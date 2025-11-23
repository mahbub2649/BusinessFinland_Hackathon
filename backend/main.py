from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.company_enrichment import CompanyEnrichmentService
from backend.services.funding_discovery import FundingDiscoveryService
from backend.services.xai_funding_discovery import XAIFundingDiscoveryService
from backend.services.matching_engine import MatchingEngine
from backend.services.xai_service import xai_service
from backend.models.schemas import CompanyInput, FundingRecommendation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Funding Advisor API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
company_service = CompanyEnrichmentService()
funding_service = FundingDiscoveryService()
xai_funding_service = XAIFundingDiscoveryService()  # New AI-powered discovery
matching_engine = MatchingEngine()

# Use XAI-based discovery by default (set to False to use traditional scraping)
USE_XAI_FUNDING_DISCOVERY = os.getenv("USE_XAI_FUNDING_DISCOVERY", "true").lower() == "true"
logger.info(f"Funding discovery mode: {'🤖 XAI-powered' if USE_XAI_FUNDING_DISCOVERY else '🕸️ Web scraping'}")

# Results cache - use absolute path relative to this file
RESULTS_CACHE_DIR = Path(__file__).parent / "cache" / "results"
RESULTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DURATION_HOURS = 24
logger.info(f"Results cache directory: {RESULTS_CACHE_DIR.absolute()}")

def get_cache_key(company_input: CompanyInput) -> str:
    """Generate unique cache key from company input"""
    key_data = f"{company_input.company_name}|{company_input.business_id}|{company_input.industry}|{company_input.employee_count}|{company_input.funding_need_amount}|{company_input.growth_stage}|{company_input.funding_purpose}"
    cache_key = hashlib.md5(key_data.encode()).hexdigest()
    logger.debug(f"Cache key: {cache_key} (from: {key_data})")
    return cache_key

def get_cached_results(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached analysis results if not expired"""
    cache_file = RESULTS_CACHE_DIR / f"{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cached_time = datetime.fromisoformat(data['timestamp'])
        if datetime.now() - cached_time < timedelta(hours=CACHE_DURATION_HOURS):
            logger.info(f"✓ Using cached results (age: {(datetime.now() - cached_time).total_seconds() / 3600:.1f}h)")
            return data['results']
        else:
            logger.info(f"Cache expired, removing old cache file")
            cache_file.unlink()
            return None
    except Exception as e:
        logger.error(f"Error reading cache: {e}")
        return None

def save_cached_results(cache_key: str, results: Dict[str, Any]):
    """Save analysis results to cache"""
    cache_file = RESULTS_CACHE_DIR / f"{cache_key}.json"
    
    try:
        data = {
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key,
            'results': results
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"✓ Cached results for future use")
    except Exception as e:
        logger.error(f"Error caching results: {e}")

@app.get("/")
def read_root():
    return {"message": "Smart Funding Advisor API is running"}

@app.post("/api/analyze-company", response_model=List[FundingRecommendation])
async def analyze_company(company_input: CompanyInput):
    """
    Main endpoint: Analyze company and return funding recommendations
    Uses cache to return instant results for repeated searches
    """
    try:
        logger.info(f"Analyzing company: {company_input.company_name}")
        
        # Generate cache key
        cache_key = get_cache_key(company_input)
        
        # Check cache first
        cached = get_cached_results(cache_key)
        if cached and 'recommendations' in cached:
            logger.info(f"⚡ Returning cached recommendations (instant)")
            # Convert cached dict back to FundingRecommendation objects
            from backend.models.schemas import FundingProgram, MatchScore
            recommendations = []
            for rec_data in cached['recommendations']:
                # Reconstruct FundingRecommendation from cached data
                recommendations.append(FundingRecommendation(**rec_data))
            return recommendations
        
        # Step 1: Enrich company data
        enriched_company = await company_service.enrich_company(company_input)
        logger.info(f"Company enriched: {enriched_company.industry}")
        
        # Step 2: Discover funding opportunities
        if USE_XAI_FUNDING_DISCOVERY:
            # Use XAI-powered discovery with company context
            company_dict = company_input.model_dump()
            funding_programs = await xai_funding_service.discover_funding_for_company(company_dict)
            logger.info(f"🤖 XAI discovered {len(funding_programs)} funding programs")
        else:
            # Use traditional web scraping
            funding_programs = await funding_service.discover_funding()
            logger.info(f"🕸️ Scraped {len(funding_programs)} funding programs")
        
        # Step 3: Match and rank
        recommendations = await matching_engine.match_funding(
            enriched_company, funding_programs
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        # Cache the results
        cache_data = {
            'recommendations': [rec.model_dump() for rec in recommendations]
        }
        save_cached_results(cache_key, cache_data)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error analyzing company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-company-description")
async def generate_company_description(company_input: CompanyInput) -> Dict[str, Any]:
    """
    Generate AI-powered company description and analysis
    Uses cache to return instant results for repeated searches
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Generating description for: {company_input.company_name}")
        
        # Generate cache key
        cache_key = get_cache_key(company_input)
        
        # Check cache first - use separate cache key for description to avoid conflicts
        description_cache_key = f"desc_{cache_key}"
        description_cache_file = RESULTS_CACHE_DIR / f"{description_cache_key}.json"
        
        if description_cache_file.exists():
            try:
                with open(description_cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                cached_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cached_time < timedelta(hours=CACHE_DURATION_HOURS):
                    elapsed = time.time() - start_time
                    logger.info(f"⚡ Returning cached company description (took {elapsed:.3f}s)")
                    return cached_data['description']
            except Exception as e:
                logger.error(f"Error reading description cache: {e}")
        
        # Convert CompanyInput to dict for the AI service
        company_data = {
            "company_name": company_input.company_name,
            "business_id": company_input.business_id,
            "industry": company_input.industry,
            "employee_count": company_input.employee_count,
            "funding_need_amount": company_input.funding_need_amount,
            "growth_stage": company_input.growth_stage,
            "funding_purpose": company_input.funding_purpose,
            "additional_info": company_input.additional_info
        }
        
        # Generate description using x.ai
        logger.info(f"⏱️ Calling x.ai API (this will take 3-5 seconds)...")
        description = await xai_service.generate_company_description(company_data)
        
        elapsed = time.time() - start_time
        logger.info(f"Generated description with confidence: {description.get('ai_confidence', 'unknown')} (took {elapsed:.3f}s)")
        
        # Cache the description separately
        try:
            cache_data = {
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            with open(description_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Cached description with key: {description_cache_key}")
        except Exception as e:
            logger.error(f"Error caching description: {e}")
        
        return description
        
    except Exception as e:
        logger.error(f"Error generating company description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate-description")
async def translate_description(data: Dict[str, str]) -> Dict[str, str]:
    """
    Translate Finnish funding program description to English using x.ai
    """
    try:
        finnish_text = data.get("text", "")
        if not finnish_text:
            raise HTTPException(status_code=400, detail="No text provided for translation")
        
        logger.info(f"Translating Finnish text (length: {len(finnish_text)})")
        
        # Use x.ai to translate
        translation = await xai_service.translate_finnish_to_english(finnish_text)
        
        logger.info("Translation completed successfully")
        return {"translated_text": translation}
        
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clear-cache")
def clear_cache():
    """
    Clear all cached results and descriptions
    """
    try:
        import shutil
        cleared_count = 0
        
        # Clear results cache
        if RESULTS_CACHE_DIR.exists():
            for cache_file in RESULTS_CACHE_DIR.glob("*.json"):
                cache_file.unlink()
                cleared_count += 1
        
        logger.info(f"✓ Cleared {cleared_count} cache files")
        return {
            "status": "success",
            "message": f"Cleared {cleared_count} cached files",
            "cleared_count": cleared_count
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "services": "all operational"}