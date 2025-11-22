import httpx
import logging
from typing import Optional
from backend.models.schemas import CompanyInput, EnrichedCompany, GrowthStage

logger = logging.getLogger(__name__)

class CompanyEnrichmentService:
    """
    Service for enriching company data using YTJ API and web scraping
    """
    
    def __init__(self):
        self.ytj_base_url = "https://avoindata.prh.fi/bis/v1"
    
    async def enrich_company(self, company_input: CompanyInput) -> EnrichedCompany:
        """
        Enrich company data with additional insights and validation
        All form fields are required, so we only add value-added enrichment
        """
        logger.info(f"Enriching company: {company_input.company_name}")
        
        # Start with complete input data (all fields required by user)
        enriched = EnrichedCompany(
            company_name=company_input.company_name,
            business_id=company_input.business_id,
            industry=company_input.industry,
            employee_count=company_input.employee_count,
            revenue_class=company_input.revenue_class,
            growth_stage=company_input.growth_stage,
            funding_need_amount=company_input.funding_need_amount,
            funding_purpose=company_input.funding_purpose
        )
        
        try:
            # Optional: Validate Finnish companies via YTJ API
            if company_input.business_id:
                ytj_data = await self._fetch_ytj_data(company_input.company_name, company_input.business_id)
                if ytj_data:
                    logger.info(f"YTJ validation successful for {company_input.company_name}")
            
            # Add value-added enrichment (industry keywords for better AI matching)
            enriched.industry_keywords = self._extract_industry_keywords(enriched.industry)
            
        except Exception as e:
            logger.error(f"Error during enrichment: {str(e)}")
            # Continue with user-provided data
        
        return enriched
    
    async def _enhance_with_intelligent_defaults(self, enriched: EnrichedCompany) -> EnrichedCompany:
        """
        Add minimal fallback enrichment when YTJ API fails
        """
        # Only provide minimal fallbacks, don't force values
        logger.info(f"Applying minimal fallback enrichment for: {enriched.company_name}")
        return enriched
    
    async def _fetch_ytj_data(self, company_name: str, business_id: Optional[str] = None) -> Optional[dict]:
        """
        Fetch company data from Finnish YTJ (PRH) API
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if business_id:
                    # Search by business ID (most accurate)
                    url = f"{self.ytj_base_url}/{business_id}"
                else:
                    # Search by company name
                    url = f"{self.ytj_base_url}?totalResults=false&maxResults=1&name={company_name}"
                
                logger.info(f"Fetching YTJ data from: {url}")
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully fetched YTJ data")
                    return data
                else:
                    logger.warning(f"YTJ API returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching YTJ data: {str(e)}")
            return None
    
    def _merge_ytj_data(self, enriched: EnrichedCompany, ytj_data: dict) -> EnrichedCompany:
        """
        Merge YTJ API data with enriched company data
        """
        try:
            # Handle both single company and search results format
            company_data = ytj_data
            if 'results' in ytj_data and ytj_data['results']:
                company_data = ytj_data['results'][0]
            
            # Update with YTJ data
            if 'name' in company_data:
                enriched.official_name = company_data['name']
            
            if 'businessId' in company_data:
                enriched.business_id = company_data['businessId']
            
            if 'registrationDate' in company_data:
                enriched.registration_date = company_data['registrationDate']
            
            # Extract industry from business lines
            if 'businessLines' in company_data:
                business_lines = company_data['businessLines']
                if business_lines and len(business_lines) > 0:
                    primary_line = business_lines[0]
                    if 'name' in primary_line:
                        enriched.industry = primary_line['name']
                    if 'code' in primary_line:
                        enriched.nace_code = primary_line['code']
            
            # Extract location
            if 'addresses' in company_data:
                addresses = company_data['addresses']
                for addr in addresses:
                    if addr.get('type') == 'postal':
                        enriched.location = addr.get('city', '')
                        break
            
            logger.info("Successfully merged YTJ data")
            
        except Exception as e:
            logger.error(f"Error merging YTJ data: {str(e)}")
        
        return enriched
    
    async def _infer_missing_data(self, enriched: EnrichedCompany) -> EnrichedCompany:
        """
        Infer missing data using heuristics and AI
        """
        try:
            # Generate industry keywords
            if enriched.industry and enriched.industry != "Unknown":
                enriched.industry_keywords = self._extract_industry_keywords(enriched.industry)
            
            # Infer company size if missing and have revenue
            if not enriched.employee_count and enriched.revenue_class:
                enriched.employee_count = self._infer_employee_count(enriched.revenue_class)
            
            # Infer revenue class only if have employee count
            if not enriched.revenue_class and enriched.employee_count:
                if enriched.employee_count >= 500:
                    enriched.revenue_class = "> 50M EUR"
                elif enriched.employee_count >= 100:
                    enriched.revenue_class = "10-50M EUR"
                elif enriched.employee_count >= 20:
                    enriched.revenue_class = "2-10M EUR"
                else:
                    enriched.revenue_class = "< 2M EUR"
                logger.info(f"Inferred revenue class: {enriched.revenue_class} based on {enriched.employee_count} employees")
            
            # Infer growth stage based on available data
            if not enriched.growth_stage:
                enriched.growth_stage = self._infer_growth_stage(enriched)
            
        except Exception as e:
            logger.error(f"Error inferring missing data: {str(e)}")
        
        return enriched
    
    def _extract_industry_keywords(self, industry: str) -> list:
        """
        Extract relevant keywords from industry description
        """
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        industry_lower = industry.lower()
        
        # Technology keywords
        tech_keywords = ['software', 'tech', 'digital', 'ai', 'data', 'cloud', 'saas']
        for keyword in tech_keywords:
            if keyword in industry_lower:
                keywords.append(keyword)
        
        # Environmental keywords
        env_keywords = ['clean', 'green', 'sustainable', 'energy', 'environmental', 'carbon']
        for keyword in env_keywords:
            if keyword in industry_lower:
                keywords.append('cleantech')
                break
        
        # Manufacturing keywords
        mfg_keywords = ['manufacturing', 'production', 'industrial']
        for keyword in mfg_keywords:
            if keyword in industry_lower:
                keywords.append('manufacturing')
                break
        
        return keywords
    
    def _infer_employee_count(self, revenue_class: str) -> Optional[int]:
        """
        Infer approximate employee count from revenue class
        """
        revenue_lower = revenue_class.lower()
        
        if 'micro' in revenue_lower or '<10k' in revenue_lower:
            return 5
        elif 'small' in revenue_lower or '10k-2m' in revenue_lower:
            return 25
        elif 'medium' in revenue_lower or '2m-10m' in revenue_lower:
            return 100
        elif 'large' in revenue_lower or '>10m' in revenue_lower:
            return 500
        
        return None
    
    def _infer_growth_stage(self, company: EnrichedCompany) -> Optional[GrowthStage]:
        """
        Infer growth stage based on available company data
        """
        # Simple heuristics - could be enhanced
        if company.employee_count:
            if company.employee_count <= 10:
                return GrowthStage.SEED
            elif company.employee_count <= 50:
                return GrowthStage.GROWTH
            else:
                return GrowthStage.SCALE_UP
        
        if company.funding_need_amount:
            if company.funding_need_amount <= 100000:
                return GrowthStage.SEED
            elif company.funding_need_amount <= 2000000:
                return GrowthStage.GROWTH
            else:
                return GrowthStage.SCALE_UP
        
        return GrowthStage.GROWTH  # Default assumption