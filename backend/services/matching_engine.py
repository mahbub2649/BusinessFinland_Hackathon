import logging
import math
from typing import List, Dict, Any
from backend.models.schemas import (
    EnrichedCompany, FundingProgram, FundingRecommendation, 
    MatchScore, GrowthStage
)

logger = logging.getLogger(__name__)

class MatchingEngine:
    """
    Core matching engine that scores and ranks funding opportunities
    """
    
    def __init__(self):
        # Scoring weights based on your priority ranking
        self.weights = {
            "industry": 0.30,      # 1st priority
            "geography": 0.25,     # 2nd priority  
            "company_size": 0.20,  # 3rd priority
            "funding_amount": 0.15, # 4th priority
            "deadline": 0.10       # 5th priority
        }
    
    async def match_funding(
        self, 
        company: EnrichedCompany, 
        funding_programs: List[FundingProgram]
    ) -> List[FundingRecommendation]:
        """
        Match company with funding programs and return ranked recommendations
        """
        logger.info(f"Matching {len(funding_programs)} programs for {company.company_name}")
        
        recommendations = []
        
        for program in funding_programs:
            try:
                # Calculate match scores
                match_score = self._calculate_match_score(company, program)
                
                # Only include if minimum threshold is met
                if match_score.total_score >= 0.3:  # 30% minimum match
                    recommendation = FundingRecommendation(
                        program=program,
                        match_score=match_score,
                        justification=self._generate_justification(company, program, match_score),
                        next_steps=self._generate_next_steps(program),
                        warnings=self._generate_warnings(company, program)
                    )
                    recommendations.append(recommendation)
                    
            except Exception as e:
                logger.error(f"Error matching program {program.program_id}: {str(e)}")
        
        # Sort by total score (highest first)
        recommendations.sort(key=lambda x: x.match_score.total_score, reverse=True)
        
        # Limit to top 10 recommendations
        top_recommendations = recommendations[:10]
        
        logger.info(f"Generated {len(top_recommendations)} recommendations")
        return top_recommendations
    
    def _calculate_match_score(
        self, 
        company: EnrichedCompany, 
        program: FundingProgram
    ) -> MatchScore:
        """
        Calculate detailed match score based on all criteria
        """
        # 1. Industry alignment (30% weight)
        industry_score = self._score_industry_match(company, program)
        
        # 2. Geographic eligibility (25% weight)
        geography_score = self._score_geography_match(company, program)
        
        # 3. Company size eligibility (20% weight)
        size_score = self._score_company_size_match(company, program)
        
        # 4. Funding amount alignment (15% weight)
        funding_score = self._score_funding_amount_match(company, program)
        
        # 5. Application deadline status (10% weight)
        deadline_score = self._score_deadline_match(program)
        
        # Calculate weighted total score
        total_score = (
            industry_score * self.weights["industry"] +
            geography_score * self.weights["geography"] +
            size_score * self.weights["company_size"] +
            funding_score * self.weights["funding_amount"] +
            deadline_score * self.weights["deadline"]
        )
        
        return MatchScore(
            total_score=round(total_score, 3),
            industry_score=round(industry_score, 3),
            geography_score=round(geography_score, 3),
            size_score=round(size_score, 3),
            funding_score=round(funding_score, 3),
            deadline_score=round(deadline_score, 3)
        )
    
    def _score_industry_match(self, company: EnrichedCompany, program: FundingProgram) -> float:
        """
        Score industry alignment (0.0 to 1.0)
        """
        if not program.eligible_industries:
            return 0.8  # No restrictions = good match
        
        company_industry = company.industry.lower() if company.industry else ""
        company_keywords = [kw.lower() for kw in company.industry_keywords]
        
        # Check direct industry matches
        for eligible_industry in program.eligible_industries:
            eligible_lower = eligible_industry.lower()
            
            # Direct match
            if eligible_lower in company_industry:
                return 1.0
            
            # Keyword match
            for keyword in company_keywords:
                if keyword in eligible_lower or eligible_lower in keyword:
                    return 0.9
        
        # Check focus areas
        for focus_area in program.focus_areas:
            focus_lower = focus_area.lower()
            if focus_lower in company_industry:
                return 0.8
            for keyword in company_keywords:
                if keyword in focus_lower:
                    return 0.7
        
        # Generic technology/innovation programs
        if any(term in program.eligible_industries for term in ["technology", "innovation", "all"]):
            return 0.6
        
        return 0.2  # Poor match
    
    def _score_geography_match(self, company: EnrichedCompany, program: FundingProgram) -> float:
        """
        Score geographic eligibility (0.0 to 1.0)
        """
        if not program.geographic_eligibility:
            return 1.0  # No restrictions
        
        # For MVP, assume all companies are Finnish
        finnish_terms = ["finland", "finnish", "suomi", "eu", "europe", "nordic"]
        
        for eligible_region in program.geographic_eligibility:
            if any(term in eligible_region.lower() for term in finnish_terms):
                return 1.0
        
        return 0.0  # Not eligible
    
    def _score_company_size_match(self, company: EnrichedCompany, program: FundingProgram) -> float:
        """
        Score company size eligibility (0.0 to 1.0)
        """
        if not program.eligible_company_sizes:
            return 1.0  # No restrictions
        
        # Determine company size category
        company_size_category = self._determine_company_size_category(company)
        
        if company_size_category in [size.lower() for size in program.eligible_company_sizes]:
            return 1.0
        
        # Partial matches
        if "all" in [size.lower() for size in program.eligible_company_sizes]:
            return 1.0
        
        if company_size_category == "startup" and "sme" in [size.lower() for size in program.eligible_company_sizes]:
            return 0.8
        
        return 0.3  # Size mismatch
    
    def _score_funding_amount_match(self, company: EnrichedCompany, program: FundingProgram) -> float:
        """
        Score funding amount alignment (0.0 to 1.0)
        """
        minamount = program.min_funding
        maxamount = program.max_funding
        x = company.funding_need_amount

        if not x:
            return 0.8  # Unknown need = neutral
        if not minamount and not maxamount:
            return 0.8  # No limits = neutral
        if minamount and x < minamount:
            # Cubic rise from 0.2 to 1.0 as x approaches minamount
            return 0.2 + 0.8 * (x / minamount) ** 3
        if maxamount and x > maxamount:
            # Exponential decay from 1.0 down to 0.2 as x exceeds maxamount
            return 0.2 + 0.8 * math.exp(-(x - maxamount) / maxamount)
        if minamount and maxamount and (x >= minamount and x <= maxamount):
            return 1.0
        # If only one bound is set and x is within or equal to it
        if minamount and x >= minamount and not maxamount:
            return 1.0
        if maxamount and x <= maxamount and not minamount:
            return 1.0
        return 0.8  # neutral
    
    def _score_deadline_match(self, program: FundingProgram) -> float:
        """
        Score application deadline status (0.0 to 1.0)
        """
        if not program.is_open:
            return 0.0  # Closed
        
        if not program.application_deadline:
            return 1.0  # Always open
        
        # For MVP, assume all open programs are good
        # In production, parse deadline and calculate urgency
        return 0.9
    
    def _determine_company_size_category(self, company: EnrichedCompany) -> str:
        """
        Determine company size category based on available data
        """
        if company.employee_count:
            if company.employee_count <= 10:
                return "startup"
            elif company.employee_count <= 250:
                return "sme"
            else:
                return "large"
        
        # Fallback to growth stage
        if company.growth_stage:
            if company.growth_stage in [GrowthStage.PRE_SEED, GrowthStage.SEED]:
                return "startup"
            elif company.growth_stage in [GrowthStage.GROWTH]:
                return "sme"
            else:
                return "large"
        
        return "sme"  # Default assumption
    
    def _generate_justification(
        self, 
        company: EnrichedCompany, 
        program: FundingProgram, 
        match_score: MatchScore
    ) -> List[str]:
        """
        Generate human-readable justification for the match
        """
        justifications = []
        
        # Industry match
        if match_score.industry_score >= 0.8:
            focus_areas_text = ", ".join(program.focus_areas) if program.focus_areas else "innovation and growth"
            justifications.append(f"Strong industry alignment: {company.industry} matches {focus_areas_text}")
        elif match_score.industry_score >= 0.6:
            justifications.append(f"Good industry fit: {company.industry} is relevant for {program.program_name}")
        
        # Size match
        if match_score.size_score >= 0.8:
            size_category = self._determine_company_size_category(company)
            justifications.append(f"Company size ({size_category}) fits eligibility criteria")
        
        # Funding match
        if match_score.funding_score >= 0.8 and company.funding_need_amount:
            justifications.append(f"Funding need (€{company.funding_need_amount:,}) within program range")

        if match_score.funding_score <= 0.3 and company.funding_need_amount:
            justifications.append(f"Funding need (€{company.funding_need_amount:,}) may not align well with program range")
        
        # Geographic
        if match_score.geography_score >= 0.8:
            justifications.append("Geographic eligibility: Finnish companies accepted")
        
        # Deadline
        if match_score.deadline_score >= 0.8:
            justifications.append("Application currently open")
        
        if not justifications:
            justifications.append("Partial match based on available criteria")
        
        return justifications
    
    def _generate_next_steps(self, program: FundingProgram) -> List[str]:
        """
        Generate recommended next steps for the funding program
        """
        steps = []
        
        if program.application_url:
            steps.append(f"Visit application portal: {program.application_url}")
        
        steps.append("Review detailed eligibility criteria")
        steps.append("Prepare required documentation")
        
        if program.funding_type == "grant":
            steps.append("Prepare project plan and budget")
        elif program.funding_type == "loan":
            steps.append("Prepare financial statements and business plan")
        
        if "co-financing" in " ".join(program.requirements).lower():
            steps.append("Arrange co-financing (own funds or other sources)")
        
        if program.application_deadline:
            steps.append(f"Submit application before deadline: {program.application_deadline}")
        else:
            steps.append("Submit application (rolling deadline)")
        
        return steps
    
    def _generate_warnings(self, company: EnrichedCompany, program: FundingProgram) -> List[str]:
        """
        Generate warnings about potential issues
        """
        warnings = []
        
        # Size warnings
        if program.eligible_company_sizes:
            company_size = self._determine_company_size_category(company)
            if company_size not in [size.lower() for size in program.eligible_company_sizes]:
                warnings.append(f"Company size ({company_size}) may not fully match eligibility criteria")
        
        # Funding amount warnings
        if company.funding_need_amount and program.max_funding:
            if company.funding_need_amount > program.max_funding:
                warnings.append(f"Funding need (€{company.funding_need_amount:,}) exceeds maximum (€{program.max_funding:,})")
        
        # Requirements warnings
        if "co-financing" in " ".join(program.requirements).lower():
            warnings.append("Co-financing required - ensure adequate own funds")
        
        if program.funding_type == "loan":
            warnings.append("Loan product - requires repayment with interest")
        
        return warnings