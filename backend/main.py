from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.company_enrichment import CompanyEnrichmentService
from backend.services.funding_discovery import FundingDiscoveryService
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
matching_engine = MatchingEngine()

@app.get("/")
def read_root():
    return {"message": "Smart Funding Advisor API is running"}

@app.post("/api/analyze-company", response_model=List[FundingRecommendation])
async def analyze_company(company_input: CompanyInput):
    """
    Main endpoint: Analyze company and return funding recommendations
    """
    try:
        logger.info(f"Analyzing company: {company_input.company_name}")
        
        # Step 1: Enrich company data
        enriched_company = await company_service.enrich_company(company_input)
        logger.info(f"Company enriched: {enriched_company.industry}")
        
        # Step 2: Discover funding opportunities
        funding_programs = await funding_service.discover_funding()
        logger.info(f"Found {len(funding_programs)} funding programs")
        
        # Step 3: Match and rank
        recommendations = await matching_engine.match_funding(
            enriched_company, funding_programs
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error analyzing company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-company-description")
async def generate_company_description(company_input: CompanyInput) -> Dict[str, Any]:
    """
    Generate AI-powered company description and analysis
    """
    try:
        logger.info(f"Generating description for: {company_input.company_name}")
        
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
        description = await xai_service.generate_company_description(company_data)
        
        logger.info(f"Generated description with confidence: {description.get('ai_confidence', 'unknown')}")
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

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "services": "all operational"}