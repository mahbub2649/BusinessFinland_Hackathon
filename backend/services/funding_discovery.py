import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import hashlib
from pathlib import Path

from backend.models.schemas import FundingProgram, GrowthStage

logger = logging.getLogger(__name__)

# Global rate limiter manager (singleton pattern)
class GlobalRateLimiterManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.limiters = {}
        return cls._instance
    
    def get_limiter(self, domain: str, calls_per_minute: int = 6) -> 'RateLimiter':
        """Get or create rate limiter for domain"""
        if domain not in self.limiters:
            self.limiters[domain] = RateLimiter(calls_per_minute)
            logger.info(f"Created global rate limiter for {domain}: {calls_per_minute} calls/min")
        return self.limiters[domain]

# Global instance
_global_rate_manager = GlobalRateLimiterManager()

class RateLimiter:
    """Rate limiter to prevent overwhelming target websites"""
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.min_delay = 60 / calls_per_minute
    
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        
        # Remove old calls (older than 1 minute)
        self.calls = [call_time for call_time in self.calls 
                     if (now - call_time).total_seconds() < 60]
        
        # Check if we've hit the limit
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds...")
                await asyncio.sleep(sleep_time)
        
        # Add minimum delay between requests
        if self.calls:
            last_call = self.calls[-1]
            time_since_last = (now - last_call).total_seconds()
            if time_since_last < self.min_delay:
                wait_time = self.min_delay - time_since_last
                logger.debug(f"Throttling request, waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
        
        self.calls.append(datetime.now())

class CacheManager:
    """Simple file-based cache for scraping results"""
    def __init__(self, cache_dir: str = "cache", cache_duration_minutes: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
    
    def _get_cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[str]:
        """Get cached content if not expired"""
        cache_file = self.cache_dir / f"{self._get_cache_key(url)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cached_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cached_time < self.cache_duration:
                logger.info(f"Using cached content for {url}")
                return data['content']
            else:
                logger.info(f"Cache expired for {url}")
                cache_file.unlink()
                return None
        except Exception as e:
            logger.error(f"Error reading cache for {url}: {e}")
            return None
    
    def set(self, url: str, content: str):
        """Cache content"""
        cache_file = self.cache_dir / f"{self._get_cache_key(url)}.json"
        
        try:
            data = {
                'url': url,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached content for {url}")
        except Exception as e:
            logger.error(f"Error caching {url}: {e}")

class FundingDiscoveryService:
    """Enhanced service with global rate limiting, caching, and better error handling"""
    
    def __init__(self):
        # Use global rate limiters for coordination across services
        self.rate_manager = _global_rate_manager
        
        self.cache = CacheManager(cache_duration_minutes=30)
        
        self.sources = {
            "business_finland": BusinessFinlandScraper(self.rate_manager, self.cache),
            "ely": ELYScraper(self.rate_manager),
            "finnvera": FinnveraScraper(self.rate_manager)
        }
    
    async def discover_funding(self) -> List[FundingProgram]:
        """Discover funding opportunities with serialized rate limiting"""
        logger.info("Starting funding discovery with global rate limiting...")
        all_programs = []
        
        # Run scrapers sequentially to respect global rate limits
        for source_name, scraper in self.sources.items():
            try:
                logger.info(f"Starting {source_name} scraping...")
                start_time = asyncio.get_event_loop().time()
                
                programs = await scraper.scrape()
                
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Completed {source_name}: {len(programs)} programs in {elapsed:.2f}s")
                all_programs.extend(programs)
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {str(e)}")
        
        logger.info(f"Total funding programs discovered: {len(all_programs)}")
        return all_programs

class BusinessFinlandScraper:
    """Enhanced Business Finland scraper with global rate limiting and caching"""
    
    def __init__(self, rate_manager: GlobalRateLimiterManager, cache: CacheManager):
        self.base_url = "https://www.businessfinland.fi"
        self.rate_manager = rate_manager
        self.cache = cache
        self.funding_pages = [
            # English pages
            "/en/for-finnish-customers/services/funding",
            "/en/for-finnish-customers/services/funding/research-and-development-funding",
            # Finnish pages
            "/fi/suomalaisille-asiakkaille/palvelut/rahoitus",
            "/fi/suomalaisille-asiakkaille/palvelut/rahoitus/tutkimus-ja-kehitystoiminnan-rahoitus"
        ]
        
        # Enhanced headers to appear more like a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _get_rate_limiter(self, url: str) -> RateLimiter:
        """Get global rate limiter for domain"""
        if "businessfinland.fi" in url:
            return self.rate_manager.get_limiter("businessfinland.fi", calls_per_minute=6)
        return self.rate_manager.get_limiter("default", calls_per_minute=10)
    
    async def scrape(self) -> List[FundingProgram]:
        """Scrape Business Finland with rate limiting and caching"""
        logger.info("Starting Business Finland scraping with rate limiting...")
        programs = []
        
        async with httpx.AsyncClient(
            timeout=15.0, 
            follow_redirects=True,
            headers=self.headers,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=1)
        ) as client:
            for page_url in self.funding_pages:
                try:
                    full_url = self.base_url + page_url
                    
                    # Check cache first
                    cached_content = self.cache.get(full_url)
                    if cached_content:
                        page_programs = self._parse_funding_page(cached_content, full_url)
                        programs.extend(page_programs)
                        continue
                    
                    # Apply rate limiting
                    rate_limiter = self._get_rate_limiter(full_url)
                    await rate_limiter.acquire()
                    
                    logger.info(f"Fetching: {full_url}")
                    response = await client.get(full_url)
                    
                    if response.status_code == 200:
                        # Cache the content
                        self.cache.set(full_url, response.text)
                        
                        page_programs = self._parse_funding_page(response.text, full_url)
                        programs.extend(page_programs)
                        logger.info(f"Successfully scraped {full_url}")
                    else:
                        logger.warning(f"HTTP {response.status_code} for {full_url}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout scraping {page_url}")
                except httpx.ConnectError:
                    logger.error(f"Connection error for {page_url}")
                except Exception as e:
                    logger.error(f"Error scraping Business Finland page {page_url}: {str(e)}")
        
        # Always include fallback programs
        fallback_programs = self._get_fallback_programs()
        programs.extend(fallback_programs)
        
        logger.info(f"Business Finland scraping complete: {len(programs)} programs")
        return programs
    
    def _parse_funding_page(self, html_content: str, source_url: str) -> List[FundingProgram]:
        """Parse Business Finland funding page HTML with better error handling"""
        programs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for funding program sections with multiple selectors
            program_sections = (
                soup.find_all(['div', 'section'], class_=re.compile(r'program|funding|service')) +
                soup.find_all(['article', 'div'], class_=re.compile(r'card|item|entry')) +
                soup.find_all('div', attrs={'data-component': re.compile(r'funding|program')})
            )
            
            for section in program_sections[:5]:  # Limit to prevent too many results
                program = self._extract_program_info(section, source_url)
                if program:
                    programs.append(program)
                    
        except Exception as e:
            logger.error(f"Error parsing Business Finland page: {str(e)}")
        
        return programs
    
    def _extract_program_info(self, section, source_url: str) -> Optional[FundingProgram]:
        """Extract program information from HTML section with validation"""
        try:
            # Try multiple selectors for titles
            title_elem = (
                section.find(['h1', 'h2', 'h3', 'h4']) or 
                section.find(['div', 'span'], class_=re.compile(r'title|heading|name'))
            )
            
            if not title_elem:
                return None
                
            program_name = title_elem.get_text(strip=True)
            if len(program_name) < 5 or len(program_name) > 200:  # Validate length
                return None
            
            # Extract description
            desc_selectors = ['p', 'div.description', 'div.summary', '.lead']
            description = "No description available"
            
            for selector in desc_selectors:
                desc_elem = section.find(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if len(desc_text) > 20:  # Meaningful description
                        description = desc_text
                        break
            
            # Create program with enhanced metadata
            return FundingProgram(
                program_id=f"bf_{hashlib.md5(program_name.encode()).hexdigest()[:8]}",
                source="business_finland",
                program_name=program_name,
                description=description[:500] + "..." if len(description) > 500 else description,
                eligible_industries=["technology", "innovation", "research", "development"],
                eligible_company_sizes=["sme", "large", "startup"],
                eligible_stages=[GrowthStage.SEED, GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                min_funding=50000,
                max_funding=5000000,
                funding_type="grant",
                is_open=True,
                application_url=source_url,
                focus_areas=self._extract_keywords(description),
                requirements=["Finnish company", "Innovation project", "Eligible activities"]
            )
            
        except Exception as e:
            logger.error(f"Error extracting program info: {str(e)}")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from description"""
        keywords = []
        text_lower = text.lower()
        
        keyword_map = {
            'innovation': ['innovation', 'innovative', 'new technology'],
            'research': ['research', 'r&d', 'development'],
            'digitalization': ['digital', 'digitalization', 'technology'],
            'sustainability': ['sustainable', 'green', 'environment'],
            'internationalization': ['international', 'export', 'global']
        }
        
        for category, terms in keyword_map.items():
            if any(term in text_lower for term in terms):
                keywords.append(category)
        
        return keywords[:3]  # Limit to top 3
    
    def _get_fallback_programs(self) -> List[FundingProgram]:
        """Enhanced fallback programs with more realistic data"""
        return [
            FundingProgram(
                program_id="bf_innovation_funding_2024",
                source="business_finland",
                program_name="Innovation Funding for Growth Companies",
                description="Support for companies developing new products, services or business models with significant market potential. Focus on breakthrough innovations and digital transformation.",
                eligible_industries=["technology", "cleantech", "healthcare", "manufacturing", "services"],
                eligible_company_sizes=["sme", "large"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                min_funding=100000,
                max_funding=2000000,
                funding_type="grant",
                is_open=True,
                application_deadline="2025-12-31",
                application_url="https://www.businessfinland.fi/en/for-finnish-customers/services/funding",
                focus_areas=["innovation", "product development", "digitalization", "growth"],
                requirements=["Finnish company", "Innovation project", "Co-financing 50%", "Market potential"]
            ),
            FundingProgram(
                program_id="bf_research_funding_2024",
                source="business_finland",
                program_name="Research and Development Funding",
                description="Funding for ambitious research and development projects that create new knowledge, capabilities and innovations with commercial potential.",
                eligible_industries=["technology", "biotechnology", "cleantech", "advanced materials"],
                eligible_company_sizes=["sme", "startup"],
                eligible_stages=[GrowthStage.SEED, GrowthStage.GROWTH],
                min_funding=50000,
                max_funding=1000000,
                funding_type="grant",
                is_open=True,
                application_deadline="2025-11-30",
                application_url="https://www.businessfinland.fi/en/for-finnish-customers/services/funding/research-and-development-funding",
                focus_areas=["research", "development", "innovation", "technology"],
                requirements=["R&D project", "Finnish company", "Research plan", "Competent team"]
            )
        ]

class ELYScraper:
    """ELY Centre scraper with rate limiting and Finnish language support"""
    
    def __init__(self, rate_manager: GlobalRateLimiterManager):
        self.rate_manager = rate_manager
        self.base_url = "https://www.ely-keskus.fi"
        self.cache = CacheManager(cache_duration_minutes=30)
        self.funding_pages = [
            "/yritysrahoitus",
            "/aloittavan-yrittajan-toimintaohjelma",
            "/pk-yrityksen-kehittamisavustus"
        ]
        
        # Headers for Finnish sites
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def scrape(self) -> List[FundingProgram]:
        logger.info("ELY Centre scraping with Finnish language support...")
        programs = []
        
        async with httpx.AsyncClient(
            timeout=15.0, 
            follow_redirects=True,
            headers=self.headers,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=1)
        ) as client:
            for page_url in self.funding_pages:
                try:
                    full_url = self.base_url + page_url
                    
                    # Check cache first
                    cached_content = self.cache.get(full_url)
                    if cached_content:
                        page_programs = self._parse_ely_page(cached_content, full_url)
                        programs.extend(page_programs)
                        continue
                    
                    # Apply rate limiting
                    rate_limiter = self.rate_manager.get_limiter("ely-keskus.fi", calls_per_minute=8)
                    await rate_limiter.acquire()
                    
                    logger.info(f"Fetching ELY page: {full_url}")
                    response = await client.get(full_url)
                    
                    if response.status_code == 200:
                        # Cache the content
                        self.cache.set(full_url, response.text)
                        
                        page_programs = self._parse_ely_page(response.text, full_url)
                        programs.extend(page_programs)
                        logger.info(f"Successfully scraped {full_url}")
                    else:
                        logger.warning(f"HTTP {response.status_code} for {full_url}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout scraping {page_url}")
                except httpx.ConnectError:
                    logger.error(f"Connection error for {page_url}")
                except Exception as e:
                    logger.error(f"Error scraping ELY page {page_url}: {str(e)}")
        
        # Add fallback programs
        fallback_programs = self._get_ely_fallback_programs()
        programs.extend(fallback_programs)
        
        logger.info(f"ELY Centre scraping complete: {len(programs)} programs")
        return programs
    
    def _parse_ely_page(self, html_content: str, source_url: str) -> List[FundingProgram]:
        """Parse ELY Centre page for Finnish funding programs"""
        programs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for funding program sections with Finnish selectors
            program_sections = (
                soup.find_all(['div', 'section'], class_=re.compile(r'avustus|rahoitus|tuki|ohjelma')) +
                soup.find_all(['article', 'div'], class_=re.compile(r'card|item|entry|content')) +
                soup.find_all('div', attrs={'data-component': re.compile(r'funding|program|rahoitus')})
            )
            
            for section in program_sections[:5]:  # Limit to prevent too many results
                program = self._extract_ely_program_info(section, source_url)
                if program:
                    programs.append(program)
                    
        except Exception as e:
            logger.error(f"Error parsing ELY page: {str(e)}")
        
        return programs
    
    def _extract_ely_program_info(self, section, source_url: str) -> Optional[FundingProgram]:
        """Extract Finnish program information from HTML section"""
        try:
            # Try multiple selectors for titles (Finnish content)
            title_elem = (
                section.find(['h1', 'h2', 'h3', 'h4']) or 
                section.find(['div', 'span'], class_=re.compile(r'title|heading|name|otsikko'))
            )
            
            if not title_elem:
                return None
                
            program_name = title_elem.get_text(strip=True)
            if len(program_name) < 5 or len(program_name) > 200:  # Validate length
                return None
            
            # Skip if it's just navigation or generic text
            skip_terms = ['etusivu', 'menu', 'navigation', 'footer', 'header', 'cookie', 
                         'tietoa meistä', 'about us', 'yhteystiedot', 'contact', 'uutiset',
                         'ajankohtaista', 'haku', 'search', 'kirjaudu', 'login']
            if any(term in program_name.lower() for term in skip_terms):
                return None
            
            # Extract description
            desc_selectors = ['p', 'div.description', 'div.summary', '.lead', '.kuvaus']
            description = "Lisätietoja saatavilla ELY-keskuksesta"  # Finnish fallback
            
            for selector in desc_selectors:
                desc_elem = section.find(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if len(desc_text) > 20:  # Meaningful description
                        description = desc_text
                        break
            
            # Create program with enhanced metadata for Finnish programs
            return FundingProgram(
                program_id=f"ely_{hashlib.md5(program_name.encode()).hexdigest()[:8]}",
                source="ely",
                program_name=program_name,
                description=description[:500] + "..." if len(description) > 500 else description,
                eligible_industries=self._extract_finnish_industries(program_name + " " + description),
                eligible_company_sizes=["startup", "sme"],
                eligible_stages=[GrowthStage.PRE_SEED, GrowthStage.SEED, GrowthStage.GROWTH],
                min_funding=5000,
                max_funding=500000,
                funding_type="grant",
                is_open=True,
                application_url=source_url,
                focus_areas=self._extract_finnish_keywords(program_name + " " + description),
                requirements=["Suomalainen yritys", "Yrittäjyysohjelma", "Liiketoimintasuunnitelma"]
            )
            
        except Exception as e:
            logger.error(f"Error extracting ELY program info: {str(e)}")
            return None
    
    def _extract_finnish_industries(self, text: str) -> List[str]:
        """Extract relevant industries from Finnish text"""
        industries = []
        text_lower = text.lower()
        
        industry_map = {
            'teknologia': ['technology', 'tech'],
            'valmistus': ['manufacturing'],
            'palvelu': ['services'],
            'kauppa': ['trade'],
            'teollisuus': ['manufacturing', 'industrial'],
            'ict': ['technology', 'software'],
            'cleantech': ['cleantech', 'environmental'],
            'bio': ['biotechnology'],
            'elintarvike': ['food'],
            'matkailu': ['tourism']
        }
        
        for finnish_term, english_terms in industry_map.items():
            if finnish_term in text_lower:
                industries.extend(english_terms)
        
        # If no specific industries found, assume general business
        if not industries:
            industries = ["all"]
            
        return list(set(industries))  # Remove duplicates
    
    def _extract_finnish_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from Finnish description"""
        keywords = []
        text_lower = text.lower()
        
        keyword_map = {
            'aloittava': ['startup', 'entrepreneurship'],
            'kehittäminen': ['development', 'growth'],
            'innovaatio': ['innovation'],
            'tutkimus': ['research'],
            'kansainvälistyminen': ['internationalization'],
            'investointi': ['investment'],
            'työllisyys': ['employment'],
            'yrittäjyys': ['entrepreneurship'],
            'pk-yritys': ['sme'],
            'rahoitus': ['funding']
        }
        
        for finnish_term, english_terms in keyword_map.items():
            if finnish_term in text_lower:
                keywords.extend(english_terms)
        
        return list(set(keywords[:5]))  # Limit to top 5, remove duplicates
    
    def _get_ely_fallback_programs(self) -> List[FundingProgram]:
        """Enhanced ELY fallback programs with Finnish funding options"""
        return [
            FundingProgram(
                program_id="ely_startup_grant_2024",
                source="ely",
                program_name="Aloittavan yrittäjän toimintaohjelma",
                description="Taloudellinen tuki työttömälle henkilölle uuden yrityksen perustamiseen. Kattaa yrittäjän toimeentulon yritystoiminnan käynnistymisvaiheessa.",
                eligible_industries=["all"],
                eligible_company_sizes=["startup"],
                eligible_stages=[GrowthStage.PRE_SEED, GrowthStage.SEED],
                min_funding=5000,
                max_funding=35000,
                funding_type="grant",
                is_open=True,
                application_deadline="2025-12-31",
                application_url="https://www.ely-keskus.fi/yritysrahoitus",
                focus_areas=["entrepreneurship", "startup", "business development"],
                requirements=["Työtön henkilö", "Elinkelpoiset liikeideät", "Liiketoimintasuunnitelma", "Suomen asukas"]
            ),
            FundingProgram(
                program_id="ely_development_grant_2024",
                source="ely",
                program_name="PK-yrityksen kehittämisavustus",
                description="Tuki pienille ja keskisuurille yrityksille liiketoiminnan kehittämiseen, kilpailukyvyn parantamiseen ja kasvupotentiaalin vahvistamiseen strategisten investointien kautta.",
                eligible_industries=["manufacturing", "services", "technology", "trade"],
                eligible_company_sizes=["sme"],
                eligible_stages=[GrowthStage.GROWTH],
                min_funding=10000,
                max_funding=500000,
                funding_type="grant",
                is_open=True,
                application_url="https://www.ely-keskus.fi/yritysrahoitus",
                focus_areas=["business development", "competitiveness", "growth", "productivity"],
                requirements=["PK-yrityksen kriteerit", "Kehittämishanke", "Omarahoitus 50%", "Suomalainen yritys"]
            ),
            FundingProgram(
                program_id="ely_environmental_grant_2024",
                source="ely",
                program_name="Ympäristö- ja energiarahoitus",
                description="Rahoitusta ympäristöystävällisten ja energiatehokkaiden ratkaisujen kehittämiseen ja käyttöönottoon.",
                eligible_industries=["cleantech", "environmental", "energy"],
                eligible_company_sizes=["sme", "startup"],
                eligible_stages=[GrowthStage.SEED, GrowthStage.GROWTH],
                min_funding=15000,
                max_funding=300000,
                funding_type="grant",
                is_open=True,
                application_url="https://www.ely-keskus.fi/yritysrahoitus",
                focus_areas=["environmental", "sustainability", "energy efficiency", "cleantech"],
                requirements=["Ympäristöhyöty", "Energiatehokkuus", "Omarahoitus", "Suomalainen yritys"]
            )
        ]

class FinnveraScraper:
    """Finnvera scraper with rate limiting and Finnish language support"""
    
    def __init__(self, rate_manager: GlobalRateLimiterManager):
        self.rate_manager = rate_manager
        self.base_url = "https://www.finnvera.fi"
        self.cache = CacheManager(cache_duration_minutes=30)
        self.funding_pages = [
            "/rahoitus",
            "/rahoitus/lainat",
            "/rahoitus/takaukset",
            "/rahoitus/pk-yritykset"
        ]
        
        # Headers for Finnish sites
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def scrape(self) -> List[FundingProgram]:
        logger.info("Finnvera scraping with Finnish language support...")
        programs = []
        
        async with httpx.AsyncClient(
            timeout=15.0, 
            follow_redirects=True,
            headers=self.headers,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=1)
        ) as client:
            for page_url in self.funding_pages:
                try:
                    full_url = self.base_url + page_url
                    
                    # Check cache first
                    cached_content = self.cache.get(full_url)
                    if cached_content:
                        page_programs = self._parse_finnvera_page(cached_content, full_url)
                        programs.extend(page_programs)
                        continue
                    
                    # Apply rate limiting
                    rate_limiter = self.rate_manager.get_limiter("finnvera.fi", calls_per_minute=8)
                    await rate_limiter.acquire()
                    
                    logger.info(f"Fetching Finnvera page: {full_url}")
                    response = await client.get(full_url)
                    
                    if response.status_code == 200:
                        # Cache the content
                        self.cache.set(full_url, response.text)
                        
                        page_programs = self._parse_finnvera_page(response.text, full_url)
                        programs.extend(page_programs)
                        logger.info(f"Successfully scraped {full_url}")
                    else:
                        logger.warning(f"HTTP {response.status_code} for {full_url}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout scraping {page_url}")
                except httpx.ConnectError:
                    logger.error(f"Connection error for {page_url}")
                except Exception as e:
                    logger.error(f"Error scraping Finnvera page {page_url}: {str(e)}")
        
        # Add fallback programs
        fallback_programs = self._get_finnvera_fallback_programs()
        programs.extend(fallback_programs)
        
        logger.info(f"Finnvera scraping complete: {len(programs)} programs")
        return programs
    
    def _parse_finnvera_page(self, html_content: str, source_url: str) -> List[FundingProgram]:
        """Parse Finnvera page for Finnish funding programs"""
        programs = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for funding program sections with Finnish selectors
            program_sections = (
                soup.find_all(['div', 'section'], class_=re.compile(r'laina|takaus|rahoitus|tuote')) +
                soup.find_all(['article', 'div'], class_=re.compile(r'card|item|entry|product')) +
                soup.find_all('div', attrs={'data-component': re.compile(r'funding|loan|rahoitus')})
            )
            
            for section in program_sections[:5]:  # Limit to prevent too many results
                program = self._extract_finnvera_program_info(section, source_url)
                if program:
                    programs.append(program)
                    
        except Exception as e:
            logger.error(f"Error parsing Finnvera page: {str(e)}")
        
        return programs
    
    def _extract_finnvera_program_info(self, section, source_url: str) -> Optional[FundingProgram]:
        """Extract Finnish Finnvera program information from HTML section"""
        try:
            # Try multiple selectors for titles (Finnish content)
            title_elem = (
                section.find(['h1', 'h2', 'h3', 'h4']) or 
                section.find(['div', 'span'], class_=re.compile(r'title|heading|name|otsikko'))
            )
            
            if not title_elem:
                return None
                
            program_name = title_elem.get_text(strip=True)
            if len(program_name) < 5 or len(program_name) > 200:  # Validate length
                return None
            
            # Skip navigation and generic content
            skip_terms = ['etusivu', 'menu', 'navigation', 'footer', 'header', 'cookie', 'yhteystiedot']
            if any(term in program_name.lower() for term in skip_terms):
                return None
            
            # Extract description
            desc_selectors = ['p', 'div.description', 'div.summary', '.lead', '.kuvaus']
            description = "Lisätietoja Finnverasta"
            
            for selector in desc_selectors:
                desc_elem = section.find(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if len(desc_text) > 20:
                        description = desc_text
                        break
            
            # Determine funding type from program name
            funding_type = "loan"
            if "takaus" in program_name.lower():
                funding_type = "guarantee"
            elif "avustus" in program_name.lower():
                funding_type = "grant"
            
            return FundingProgram(
                program_id=f"finnvera_{hashlib.md5(program_name.encode()).hexdigest()[:8]}",
                source="finnvera",
                program_name=program_name,
                description=description[:500] + "..." if len(description) > 500 else description,
                eligible_industries=["all"],
                eligible_company_sizes=["sme", "startup"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                min_funding=20000,
                max_funding=10000000,
                funding_type=funding_type,
                is_open=True,
                application_url=source_url,
                focus_areas=self._extract_finnish_keywords(program_name + " " + description),
                requirements=["Suomalainen yritys", "Vakuudet", "Liiketoimintasuunnitelma"]
            )
            
        except Exception as e:
            logger.error(f"Error extracting Finnvera program info: {str(e)}")
            return None
    
    def _extract_finnish_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from Finnish description"""
        keywords = []
        text_lower = text.lower()
        
        keyword_map = {
            'kasvu': ['growth'],
            'investointi': ['investment'],
            'kehittäminen': ['development'],
            'kansainvälistyminen': ['internationalization'],
            'käyttöpääoma': ['working capital'],
            'laina': ['loan'],
            'takaus': ['guarantee'],
            'pk-yritys': ['sme'],
            'startup': ['startup'],
            'yrittäjyys': ['entrepreneurship']
        }
        
        for finnish_term, english_terms in keyword_map.items():
            if finnish_term in text_lower:
                keywords.extend(english_terms)
        
        return list(set(keywords[:5]))
    
    def _get_finnvera_fallback_programs(self) -> List[FundingProgram]:
        """Enhanced Finnvera fallback programs with Finnish funding options"""
        return [
            FundingProgram(
                program_id="finnvera_growth_loan_2024",
                source="finnvera",
                program_name="Finnvera Kasvulaina",
                description="Lainaa pk-yrityksille, kun perinteinen pankkirahoitus ei riitä. Tukee yrityksen kasvua, investointeja ja käyttöpääomatarpeita edullisin ehdoin.",
                eligible_industries=["all"],
                eligible_company_sizes=["sme"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                min_funding=50000,
                max_funding=10000000,
                funding_type="loan",
                is_open=True,
                application_url="https://www.finnvera.fi/rahoitus/lainat",
                focus_areas=["growth", "investments", "working capital", "expansion"],
                requirements=["PK-yrityksen kriteerit", "Elinkelpoinen liiketoimintamalli", "Vakuudet", "Takaisinmaksukyky"]
            ),
            FundingProgram(
                program_id="finnvera_guarantee_2024",
                source="finnvera",
                program_name="Finnvera Lainavakuus",
                description="Takauksia pankilainojen vakuudeksi pk-yrityksille, kun vakuudet eivät riitä. Vähentää pankin riskiä ja parantaa pääsyä perinteiseen rahoitukseen.",
                eligible_industries=["all"],
                eligible_company_sizes=["sme"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                min_funding=20000,
                max_funding=5000000,
                funding_type="guarantee",
                is_open=True,
                application_url="https://www.finnvera.fi/rahoitus/takaukset",
                focus_areas=["loan security", "risk mitigation", "bank financing", "growth"],
                requirements=["PK-yrityksen kriteerit", "Pankkilainahakemus", "Riittämättömät vakuudet", "Suomalainen yritys"]
            ),
            FundingProgram(
                program_id="finnvera_export_financing_2024",
                source="finnvera",
                program_name="Vientiluotto",
                description="Rahoitusratkaisuja vientitoimintaan ja kansainvälistymiseen. Tukee suomalaisten yritysten menestystä kansainvälisillä markkinoilla.",
                eligible_industries=["all"],
                eligible_company_sizes=["sme", "large"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                min_funding=100000,
                max_funding=50000000,
                funding_type="loan",
                is_open=True,
                application_url="https://www.finnvera.fi/rahoitus",
                focus_areas=["export", "internationalization", "foreign markets", "growth"],
                requirements=["Vientitoiminta", "Suomalainen yritys", "Vakuudet", "Kansainvälistymissuunnitelma"]
            )
        ]