"""
XAI-powered funding discovery service that uses Grok's web search to find funding opportunities.
This replaces traditional web scraping with AI-powered search and analysis.
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import time

from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

from backend.models.schemas import FundingProgram, GrowthStage

logger = logging.getLogger(__name__)


class XAIFundingDiscoveryService:
    """AI-powered funding discovery using xAI Grok with web search"""
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable not set")
        
        self.client = Client(api_key=self.api_key)
        logger.info("✅ XAI Funding Discovery Service initialized")
    
    async def discover_funding_for_company(self, company_data: Dict[str, Any]) -> List[FundingProgram]:
        """
        Use xAI with web search to discover relevant funding opportunities for a company
        
        Args:
            company_data: Dictionary containing company information from the form
            
        Returns:
            List of FundingProgram objects
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🤖 Discovering funding opportunities for {company_data.get('company_name')} using xAI... (attempt {attempt + 1}/{max_retries})")
                
                prompt = self._build_funding_discovery_prompt(company_data)
                
                # Create chat with web search tool
                chat = self.client.chat.create(
                    model="grok-4-1-fast-non-reasoning",
                    tools=[web_search()]
                )
                
                chat.append(user(prompt))
                
                # Stream the response and collect tool calls
                full_response = ""
                for response, chunk in chat.stream():
                    # Log web searches as they happen
                    for tool_call in chunk.tool_calls:
                        logger.info(f"🔍 {tool_call.function.name}: {tool_call.function.arguments}")
                    
                    if chunk.content:
                        full_response += chunk.content
                
                logger.info(f"✅ Received AI response ({len(full_response)} chars)")
                logger.debug(f"AI Response preview: {full_response[:500]}...")
                
                # Parse the AI response into FundingProgram objects
                funding_programs = self._parse_funding_response(full_response, company_data)
                
                logger.info(f"📊 Discovered {len(funding_programs)} funding programs")
                return funding_programs
                
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries} attempts failed. Error: {e}", exc_info=True)
                    # Return fallback programs if all retries fail
                    return self._get_fallback_programs()
    
    def _build_funding_discovery_prompt(self, company_data: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for funding discovery"""
        
        # Format funding amount
        funding_amount = company_data.get('funding_need_amount', 'N/A')
        if isinstance(funding_amount, (int, float)):
            funding_str = f"€{funding_amount:,}"
        else:
            funding_str = str(funding_amount)
        
        return f"""You are a Finnish business funding expert. Search the web for current funding opportunities that match this company's profile.

COMPANY PROFILE:
- Name: {company_data.get('company_name', 'N/A')}
- Business ID: {company_data.get('business_id', 'N/A')}
- Industry: {company_data.get('industry', 'N/A')}
- Number of Employees: {company_data.get('employee_count', 'N/A')}
- Growth Stage: {company_data.get('growth_stage', 'N/A')}
- Location: {company_data.get('location', 'Finland')}
- Funding Need: {funding_str}
- Funding Purpose: {company_data.get('funding_purpose', 'N/A')}
- Additional Context: {company_data.get('additional_info', 'N/A')}

TASK:
Search for current (2024-2025) Finnish funding opportunities from these sources:
1. Business Finland (businessfinland.fi) - Innovation, R&D, growth funding
2. ELY-keskus (ely-keskus.fi) - Startup grants, SME development funding
3. Finnvera (finnvera.fi) - Loans, guarantees, export financing
4. Tekes/EURA - Regional development funding
5. Any other relevant Finnish or EU funding programs

For EACH funding program you find, provide:

```json
{{
  "program_name": "Exact name of the program",
  "source": "business_finland|ely|finnvera|other",
  "description": "Detailed description of what the program funds (2-3 sentences)",
  "funding_type": "grant|loan|guarantee|equity",
  "min_funding": 10000,
  "max_funding": 5000000,
  "eligible_industries": ["technology", "manufacturing", "services"],
  "eligible_company_sizes": ["startup", "sme", "large"],
  "eligible_stages": ["pre_seed", "seed", "growth", "scale_up"],
  "requirements": ["Specific requirement 1", "Specific requirement 2"],
  "application_url": "https://exact-url-to-apply",
  "application_deadline": "2025-12-31 or ongoing",
  "focus_areas": ["innovation", "sustainability", "export"],
  "is_open": true,
  "match_reasoning": "Why this program is relevant for this specific company"
}}
```

IMPORTANT INSTRUCTIONS:
- Search for REAL, CURRENT programs (2024-2025)
- Find at least 6-10 relevant programs
- Include EXACT application URLs from official websites
- Focus on programs that match the company's industry, size, and funding needs
- Include both grants and loans
- Prioritize programs with highest relevance
- For eligible_stages, ONLY use: "pre_seed", "seed", "growth", "scale_up" (NO "mature" or other values)
- Return ONLY valid JSON array of programs, no other text
- Use actual data from websites, not generic descriptions

Return format (valid JSON array):
[
  {{
    "program_name": "Example Program Name",
    "source": "business_finland",
    "description": "Program description",
    "funding_type": "grant",
    "min_funding": 50000,
    "max_funding": 1000000,
    "eligible_industries": ["technology"],
    "eligible_company_sizes": ["sme"],
    "eligible_stages": ["growth"],
    "requirements": ["Requirement 1"],
    "application_url": "https://example.fi",
    "application_deadline": "2025-12-31",
    "focus_areas": ["innovation"],
    "is_open": true,
    "match_reasoning": "Why relevant"
  }}
]
"""
    
    def _parse_funding_response(self, ai_response: str, company_data: Dict[str, Any]) -> List[FundingProgram]:
        """Parse AI response into FundingProgram objects"""
        programs = []
        
        try:
            # Try to extract JSON from response
            # Look for JSON array pattern
            import re
            
            # Log the response for debugging
            logger.debug(f"Parsing AI response: {ai_response[:1000]}...")
            
            json_match = re.search(r'\[[\s\S]*\]', ai_response)
            
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"Found JSON: {json_str[:500]}...")
                
                programs_data = json.loads(json_str)
                
                logger.info(f"📝 Parsing {len(programs_data)} programs from AI response")
                
                for idx, prog_data in enumerate(programs_data):
                    try:
                        # Map stage strings to GrowthStage enum
                        stages = []
                        for stage_str in prog_data.get('eligible_stages', []):
                            stage_map = {
                                'pre_seed': GrowthStage.PRE_SEED,
                                'pre-seed': GrowthStage.PRE_SEED,
                                'seed': GrowthStage.SEED,
                                'growth': GrowthStage.GROWTH,
                                'scale_up': GrowthStage.SCALE_UP,
                                'scale-up': GrowthStage.SCALE_UP,
                                'scaleup': GrowthStage.SCALE_UP,
                                # Map 'mature' to 'scale_up' as fallback
                                'mature': GrowthStage.SCALE_UP,
                                'established': GrowthStage.SCALE_UP
                            }
                            stage_lower = stage_str.lower().replace('_', '-')
                            if stage_lower in stage_map:
                                stages.append(stage_map[stage_lower])
                            else:
                                logger.warning(f"Unknown stage '{stage_str}', using GROWTH as default")
                                stages.append(GrowthStage.GROWTH)
                        
                        # Create FundingProgram object
                        program = FundingProgram(
                            program_id=f"xai_{prog_data.get('source', 'unknown')}_{idx}_{datetime.now().strftime('%Y%m%d')}",
                            source=prog_data.get('source', 'unknown'),
                            program_name=prog_data.get('program_name', 'Unknown Program'),
                            description=prog_data.get('description', ''),
                            funding_type=prog_data.get('funding_type', 'grant'),
                            min_funding=prog_data.get('min_funding', 0),
                            max_funding=prog_data.get('max_funding', 0),
                            eligible_industries=prog_data.get('eligible_industries', []),
                            eligible_company_sizes=prog_data.get('eligible_company_sizes', []),
                            eligible_stages=stages if stages else [GrowthStage.GROWTH],
                            requirements=prog_data.get('requirements', []),
                            application_url=prog_data.get('application_url', ''),
                            application_deadline=prog_data.get('application_deadline'),
                            focus_areas=prog_data.get('focus_areas', []),
                            is_open=prog_data.get('is_open', True),
                            match_reasoning=prog_data.get('match_reasoning', '')
                        )
                        
                        programs.append(program)
                        logger.info(f"  ✅ {program.program_name} ({program.source})")
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️ Failed to parse program {idx}: {e}")
                        continue
            
            else:
                logger.warning("⚠️ No JSON array found in AI response")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
        except Exception as e:
            logger.error(f"❌ Error parsing AI response: {e}")
        
        # If no programs parsed, return fallback
        if not programs:
            logger.warning("⚠️ No programs parsed from AI, using fallback")
            return self._get_fallback_programs()
        
        return programs
    
    def _get_fallback_programs(self) -> List[FundingProgram]:
        """Fallback programs if AI discovery fails"""
        logger.info("📦 Using fallback funding programs")
        
        return [
            FundingProgram(
                program_id="fallback_bf_innovation_2024",
                source="business_finland",
                program_name="Business Finland Innovation Funding",
                description="Funding for companies developing innovative products, services, or business models with significant growth and export potential.",
                funding_type="grant",
                min_funding=100000,
                max_funding=2000000,
                eligible_industries=["technology", "cleantech", "healthcare", "manufacturing"],
                eligible_company_sizes=["sme", "large"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                requirements=["Innovation project", "Co-financing", "Growth potential"],
                application_url="https://www.businessfinland.fi/en/for-finnish-customers/services/funding",
                is_open=True,
                focus_areas=["innovation", "growth", "internationalization"]
            ),
            FundingProgram(
                program_id="fallback_ely_startup_2024",
                source="ely",
                program_name="Starttiraha - Startup Grant",
                description="Financial support for unemployed individuals starting a new business. Covers entrepreneur's living expenses during the startup phase.",
                funding_type="grant",
                min_funding=5000,
                max_funding=35000,
                eligible_industries=["all"],
                eligible_company_sizes=["startup"],
                eligible_stages=[GrowthStage.PRE_SEED, GrowthStage.SEED],
                requirements=["Unemployed", "Business plan", "Finnish resident"],
                application_url="https://www.ely-keskus.fi/yritysrahoitus",
                is_open=True,
                focus_areas=["entrepreneurship", "startup"]
            ),
            FundingProgram(
                program_id="fallback_finnvera_loan_2024",
                source="finnvera",
                program_name="Finnvera Growth Loan",
                description="Loans for SMEs when traditional bank financing is not sufficient. Supports growth, investments, and working capital needs.",
                funding_type="loan",
                min_funding=50000,
                max_funding=10000000,
                eligible_industries=["all"],
                eligible_company_sizes=["sme"],
                eligible_stages=[GrowthStage.GROWTH, GrowthStage.SCALE_UP],
                requirements=["SME criteria", "Viable business model", "Collateral"],
                application_url="https://www.finnvera.fi/en/finnvera/financing",
                is_open=True,
                focus_areas=["growth", "working capital", "investments"]
            )
        ]
