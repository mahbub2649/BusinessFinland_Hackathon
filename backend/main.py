from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.company_enrichment import CompanyEnrichmentService
from backend.services.funding_discovery import FundingDiscoveryService
from backend.services.matching_engine import MatchingEngine
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

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "services": "all operational"}