import os
from typing import Dict, Any
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

# Load environment variables
load_dotenv()

class XAIService:
    """Service for interacting with x.ai API with agentic search for company analysis"""
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.client = Client(api_key=self.api_key)
        
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable not set")
    
    async def generate_company_description(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive company description using x.ai with web search
        
        Args:
            company_data: Dictionary containing company information
            
        Returns:
            Dictionary with generated description and analysis
        """
        try:
            # Create chat with web search tool enabled
            chat = self.client.chat.create(
                model="grok-4-fast",
                tools=[
                    web_search(
                        allowed_domains=[
                            "businessfinland.fi", 
                            "finnvera.fi", 
                            "ely-keskus.fi",
                            "linkedin.com",
                            "prh.fi"  # Finnish business register
                        ]
                    )
                ]
            )
            
            prompt = self._build_enhanced_analysis_prompt(company_data)
            chat.append(user(prompt))
            
            # Stream the response to get real-time tool calls
            full_response = ""
            citations = []
            
            for response, chunk in chat.stream():
                # Log tool calls as they happen
                for tool_call in chunk.tool_calls:
                    print(f"🔍 Searching: {tool_call.function.name} with {tool_call.function.arguments}")
                
                if chunk.content:
                    full_response += chunk.content
                
                # Collect citations
                if hasattr(response, 'citations') and response.citations:
                    citations = response.citations
            
            # Parse the AI response with citations
            return self._parse_enhanced_response(full_response, company_data, citations)
                    
        except Exception as e:
            print(f"Error with x.ai search: {e}")
            # Fallback to basic analysis if search fails
            return await self._basic_analysis_fallback(company_data)
    
    def _build_enhanced_analysis_prompt(self, company_data: Dict[str, Any]) -> str:
        """Build an enhanced prompt that leverages web search"""
        
        # Format funding amount safely
        funding_amount = company_data.get('funding_need_amount', 'N/A')
        if isinstance(funding_amount, (int, float)):
            funding_str = f"€{funding_amount:,}"
        else:
            funding_str = str(funding_amount)
        
        return f"""
I need a CONCISE business analysis for a Finnish company seeking funding. Keep it brief and actionable.

Company Information:
- Name: {company_data.get('company_name', 'N/A')}
- Business ID: {company_data.get('business_id', 'N/A')} 
- Industry: {company_data.get('industry', 'N/A')}
- Employees: {company_data.get('employee_count', 'N/A')}
- Funding Need: {funding_str}
- Growth Stage: {company_data.get('growth_stage', 'N/A')}
- Funding Purpose: {company_data.get('funding_purpose', 'N/A')}
- Additional Info: {company_data.get('additional_info', 'N/A')}

Please search for information about this company and provide a JSON response with:
{{
    "company_description": "2-3 sentence summary of the company and its business model",
    "market_size": {{"value": "€X.XB", "description": "Global/EU market size for this industry"}},
    "company_website": "https://company-website.fi or null if not found",
    "hashtags": ["#environmentaltech", "#carboncapture", "#cleantech"],
    "ai_confidence": "high/medium/low"
}}

Keep it concise and focus on the most important information for funding decisions.
"""
    
    async def _basic_analysis_fallback(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to basic analysis without web search if needed"""
        try:
            # Create chat without search tools
            chat = self.client.chat.create(model="grok-4-fast")
            
            prompt = f"""
Analyze this Finnish company for funding readiness:

Company: {company_data.get('company_name')} 
Industry: {company_data.get('industry')}
Employees: {company_data.get('employee_count')}
Growth Stage: {company_data.get('growth_stage')}

Provide JSON analysis:
{{
    "business_summary": "Professional company overview",
    "market_position": "Market analysis",
    "growth_potential": "Growth assessment", 
    "funding_readiness": "Funding evaluation",
    "key_strengths": ["strength1", "strength2"],
    "potential_challenges": ["challenge1", "challenge2"],
    "industry_insights": "Industry analysis",
    "ai_confidence": "medium"
}}
"""
            
            chat.append(user(prompt))
            
            full_response = ""
            for response, chunk in chat.stream():
                if chunk.content:
                    full_response += chunk.content
            
            return self._parse_enhanced_response(full_response, company_data, [])
            
        except Exception as e:
            print(f"Fallback analysis failed: {e}")
            return self._final_fallback_description(company_data)
    
    def _parse_enhanced_response(self, ai_content: str, company_data: Dict[str, Any], citations: list) -> Dict[str, Any]:
        """Parse enhanced AI response with citations"""
        try:
            # Extract JSON from response
            if "```json" in ai_content:
                json_start = ai_content.find("```json") + 7
                json_end = ai_content.find("```", json_start)
                json_str = ai_content[json_start:json_end].strip()
            elif "{" in ai_content and "}" in ai_content:
                json_start = ai_content.find("{")
                json_end = ai_content.rfind("}") + 1
                json_str = ai_content[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            import json
            parsed_data = json.loads(json_str)
            
            # Convert citations to serializable format
            serializable_citations = []
            if citations:
                for citation in citations:
                    if hasattr(citation, 'url'):
                        serializable_citations.append(str(citation.url))
                    elif isinstance(citation, str):
                        serializable_citations.append(citation)
                    else:
                        serializable_citations.append(str(citation))
            
            # Add citations and metadata
            result = {
                "company_description": parsed_data.get("company_description", "Finnish company seeking funding for growth and innovation."),
                "market_size": parsed_data.get("market_size", {"value": "€XB", "description": "Market analysis pending"}),
                "company_website": parsed_data.get("company_website"),
                "hashtags": parsed_data.get("hashtags", ["#technology", "#innovation", "#finland"]),
                "ai_confidence": parsed_data.get("ai_confidence", "medium"),
                "generated_by": "x.ai with web search",
                "company_name": company_data.get("company_name", ""),
                "citations": serializable_citations,
                "research_enhanced": len(serializable_citations) > 0
            }
            
            return result
            
        except Exception as e:
            print(f"Error parsing enhanced response: {e}")
            return self._final_fallback_description(company_data)
    
    def _final_fallback_description(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Final fallback when all AI methods fail"""
        funding_amount = company_data.get('funding_need_amount')
        company_name = company_data.get('company_name', 'This company')
        industry = company_data.get('industry', 'technology')
        employee_count = company_data.get('employee_count', 'several')
        
        if isinstance(funding_amount, (int, float)):
            summary = f"{company_name} operates in the {industry} sector with {employee_count} employees, seeking €{funding_amount:,} in funding."
        else:
            summary = f"{company_name} operates in the {industry} sector with {employee_count} employees."
        
        return {
            "company_description": summary,
            "market_size": {"value": "€XB", "description": "Market analysis pending"},
            "company_website": None,
            "hashtags": [f"#{industry.lower().replace(' ', '').replace('-', '')}", "#technology", "#finland"],
            "ai_confidence": "low",
            "generated_by": "fallback system",
            "company_name": company_name,
            "citations": [],
            "research_enhanced": False
        }


# Global instance
xai_service = XAIService()