from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class GrowthStage(str, Enum):
    PRE_SEED = "pre-seed"
    SEED = "seed"
    GROWTH = "growth"
    SCALE_UP = "scale-up"

class FundingPurpose(str, Enum):
    RDI = "rdi"
    INTERNATIONALIZATION = "internationalization"
    INVESTMENTS = "investments"
    EQUIPMENT = "equipment"
    WORKING_CAPITAL = "working_capital"

class CompanyInput(BaseModel):
    company_name: str = Field(..., description="Company name")
    business_id: Optional[str] = Field(None, description="Finnish Y-tunnus")
    industry: Optional[str] = Field(None, description="Industry description")
    revenue_class: Optional[str] = Field(None, description="Revenue range")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    growth_stage: Optional[GrowthStage] = Field(None, description="Company growth stage")
    funding_need_amount: Optional[int] = Field(None, description="Funding amount needed in EUR")
    funding_purpose: Optional[FundingPurpose] = Field(None, description="Purpose of funding")
    additional_info: Optional[str] = Field(None, description="Additional context")

class EnrichedCompany(BaseModel):
    # Original input
    company_name: str
    business_id: Optional[str] = None
    
    # Enriched from YTJ API
    official_name: Optional[str] = None
    nace_code: Optional[str] = None
    location: Optional[str] = None
    registration_date: Optional[str] = None
    
    # Processed/inferred
    industry: str
    industry_keywords: List[str] = []
    employee_count: Optional[int] = None
    revenue_class: Optional[str] = None
    growth_stage: Optional[GrowthStage] = None
    funding_need_amount: Optional[int] = None
    funding_purpose: Optional[FundingPurpose] = None
    
    # Additional enrichment
    website_url: Optional[str] = None
    company_description: Optional[str] = None

class FundingProgram(BaseModel):
    program_id: str
    source: str  # "business_finland", "ely", "finnvera"
    program_name: str
    description: str
    
    # Eligibility
    eligible_industries: List[str] = []
    eligible_company_sizes: List[str] = []  # "sme", "large", "startup"
    eligible_stages: List[GrowthStage] = []
    geographic_eligibility: List[str] = ["finland"]
    
    # Funding details
    min_funding: Optional[int] = None
    max_funding: Optional[int] = None
    funding_type: str  # "grant", "loan", "equity"
    
    # Application
    application_deadline: Optional[str] = None
    is_open: bool = True
    application_url: Optional[str] = None
    
    # Additional
    focus_areas: List[str] = []
    requirements: List[str] = []
    
class MatchScore(BaseModel):
    total_score: float = Field(..., ge=0, le=1, description="Overall match score 0-1")
    industry_score: float = Field(..., ge=0, le=1)
    geography_score: float = Field(..., ge=0, le=1)
    size_score: float = Field(..., ge=0, le=1)
    funding_score: float = Field(..., ge=0, le=1)
    deadline_score: float = Field(..., ge=0, le=1)
    
class FundingRecommendation(BaseModel):
    program: FundingProgram
    match_score: MatchScore
    justification: List[str] = Field(..., description="Human-readable explanation points")
    next_steps: List[str] = Field(default=[], description="Recommended actions")
    warnings: List[str] = Field(default=[], description="Potential issues")