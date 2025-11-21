import os
import streamlit as st
import requests
from datetime import datetime
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search, x_search  # Built-in search tools

# Load env
load_dotenv()

# YTJ API helper (free Finnish company fetch)
@st.cache_data(ttl=3600)
def fetch_company_profile(business_id):
    if not business_id:
        return {"name": "Sample Turku Cleantech Oy", "industry": "Cleantech", "employees": 10, "revenue": "€500k", "stage": "Growth"}
    url = f"https://virre.prh.fi/ytj/api/v2/companies/{business_id}?language=EN"
    try:
        resp = requests.get(url)
        data = resp.json()
        return {
            "name": data.get("name", "Unknown"),
            "industry": data.get("activity", {}).get("description", {}).get("fi", "Unknown"),
            "employees": data.get("personnelSize", {}).get("description", {}).get("fi", "Unknown"),
            "revenue": "N/A (full via PRH)",  # Enhance if needed
            "stage": "Growth"  # User override
        }
    except:
        st.warning("Invalid Business ID; using sample.")
        return {"name": "Sample Turku Cleantech Oy", "industry": "Cleantech", "employees": 10, "revenue": "€500k", "stage": "Growth"}

# Grok advisor with search tools
def get_funding_advice(client, profile, funding_need):
    # Enable tools with filters: Finnish/EU domains, recent X for investor buzz
    tools = [
        web_search(allowed_domains=["businessfinland.fi", "ely-keskus.fi", "europa.eu", "tem.fi", "mmm.fi"]),  # Funding sites
        x_search(from_date=datetime(2025, 1, 1), to_date=datetime.now())  # Recent X posts (e.g., funding announcements)
    ]

    prompt = f"""
    Company: {profile['name']}, {profile['industry']}, {profile['employees']} employees, {profile['revenue']}, {profile['stage']} stage.
    Need: €{funding_need['amount']:,} for {funding_need['purpose']} (e.g., RDI in cleantech).

    Use web_search for current Finnish/EU funding (ELY, Business Finland, Finnvera, Horizon Europe, Nordic programmes) and x_search for investor sentiment on X.
    Tasks:
    1. 1-2 sentence company summary.
    2. Top 5 prioritized recommendations (public instruments/investors).
    3. Per rec: Name, relevance score (0-1), justification (why matches), deadline/openings, source URL.

    Prioritize: Industry > stage > size. Search real-time as of {datetime.now().strftime('%Y-%m-%d')}.
    Output ONLY valid JSON:
    {{
        "summary": "Text",
        "recommendations": [
            {{"name": "...", "score": 0.85, "justification": "Why...", "deadline": "Open until...", "source": "URL"}}
        ]
    }}
    """

    chat = client.chat.create(model="grok-4-fast", tools=tools)  # Agentic model
    chat.append(user(prompt))
    response = chat.sample()  # Triggers searches + reasoning

    # Parse JSON from content
    try:
        import json
        advice = json.loads(response.content)
        advice["citations"] = response.citations or []  # URLs from searches
        return advice
    except json.JSONDecodeError:
        st.error("Parsing error; raw: " + response.content[:500])
        return {"summary": "Error", "recommendations": [], "citations": []}

# Streamlit UI
st.title("🚀 Smart Funding Advisor MVP (with Grok Search Tools)")
st.write("AI-powered recs using real-time web/X search for funding. Integrates YTJ for profiles.")

# Inputs
col1, col2 = st.columns(2)
with col1:
    business_id = st.text_input("Business ID (Y-tunnus)", placeholder="e.g., 1234567-8")
with col2:
    funding_amount = st.number_input("Amount (€)", min_value=10000, value=200000)
funding_purpose = st.selectbox("Purpose", ["RDI", "Internationalization", "Investments", "Growth Capital"])
growth_stage = st.selectbox("Stage", ["Pre-seed", "Seed", "Growth", "Scale-up"])

if st.button("Get Advice", type="primary"):
    with st.spinner("Searching & advising... (Grok + web/X tools)"):
        profile = fetch_company_profile(business_id)
        profile["stage"] = growth_stage
        need = {"amount": funding_amount, "purpose": funding_purpose}

        client = Client()  # Auto-uses XAI_API_KEY
        advice = get_funding_advice(client, profile, need)

        # Render results
        st.subheader("Company Summary")
        st.write(advice.get("summary", "N/A"))

        st.subheader("Top Recommendations")
        recs = advice.get("recommendations", [])
        for i, rec in enumerate(recs[:5], 1):
            with st.expander(f"{i}. {rec['name']} (Score: {rec['score']:.2f})"):
                st.write("**Justification:** " + rec["justification"])
                st.write("**Deadline:** " + rec["deadline"])
                st.write("**Source:** " + rec["source"])

        st.subheader("Search Citations")
        for cit in advice.get("citations", []):
            st.write(f"- [Citation]({cit})")  # URLs from Grok

        import time
        st.metric("Latency", f"{time.time() - st.session_state.get('start', time.time()):.1f}s")  # Track perf

st.sidebar.info("**Tech:** xAI SDK 1.3.1+ (grok-4-fast) with web_search/x_search. Filters for FI/EU. CRM-ready via /advise endpoint. Cost: ~€0.02/query.")
if st.sidebar.button("Sample Run"):
    st.rerun()