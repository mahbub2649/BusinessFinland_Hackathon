import os
import json
import streamlit as st
import requests
from datetime import datetime
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search, x_search  # Built-in search tools

# Load env
load_dotenv()

PRH_API_URL = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies"
DEFAULT_PROFILE = {
    "name": "Sample Turku Cleantech Oy",
    "industry": "Cleantech",
    "employees": "10",
    "revenue": "~€0.5M",
    "stage": "Growth",
    "business_id": "1234567-8",
    "address": "Turku, Finland",
}


def _get_name(names):
    for name in names or []:
        if name.get("type") == "1":  # official name
            return name.get("name")
    return (names or [{}])[0].get("name", "Unknown")


def _get_description(entries, lang_code="3"):
    for entry in entries or []:
        if entry.get("languageCode") == lang_code:
            return entry.get("description")
    return None


def _format_address(addresses):
    if not addresses:
        return "Unknown"
    primary = addresses[0]
    city_entry = (primary.get("postOffices") or [{}])[0]
    city = city_entry.get("city", "")
    street = primary.get("street", "")
    number = primary.get("buildingNumber", "")
    parts = [part for part in [street, number, city] if part]
    return ", ".join(parts) or "Unknown"

# YTJ API helper (free Finnish company fetch)
@st.cache_data(ttl=3600)
def fetch_company_profile(business_id):
    if not business_id:
        return DEFAULT_PROFILE.copy(), {}

    try:
        resp = requests.get(PRH_API_URL, params={"businessId": business_id}, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        st.warning(f"PRH lookup failed ({exc}); using sample data.")
        return DEFAULT_PROFILE.copy(), {}

    companies = payload.get("companies") or []
    if not companies:
        st.warning("No company matched that Business ID; using sample data.")
        return DEFAULT_PROFILE.copy(), {}

    company = companies[0]
    main_line = company.get("mainBusinessLine", {})
    profile = {
        "name": _get_name(company.get("names")) or DEFAULT_PROFILE["name"],
        "industry": _get_description(main_line.get("descriptions")) or DEFAULT_PROFILE["industry"],
        "employees": "",
        "revenue": "",
        "stage": "",
        "business_id": company.get("businessId", {}).get("value", business_id),
        "address": _format_address(company.get("addresses")),
        "business_line_code": main_line.get("type"),
        "company_form": _get_description((company.get("companyForms") or [{}])[0].get("descriptions"), lang_code="3"),
    }
    return profile, company


def enrich_profile_with_ai(client, profile, company_record):
    missing = [field for field in ("employees", "revenue", "stage") if not profile.get(field)]
    if not missing:
        return profile

    snapshot = {
        "businessId": company_record.get("businessId", {}).get("value"),
        "mainBusinessLine": company_record.get("mainBusinessLine"),
        "status": company_record.get("status"),
        "registeredEntries": company_record.get("registeredEntries"),
        "companyForms": company_record.get("companyForms"),
        "names": company_record.get("names"),
        "addresses": company_record.get("addresses"),
    }
    prompt = f"""
    You are an analyst enriching Finnish Trade Register data. Using the JSON below, estimate the company's headcount range, annual revenue range in EUR, and growth stage (choose from Pre-seed, Seed, Growth, Scale-up, Mature).
    Prefer well-justified, conservative estimates. If information is absent, infer from industry, age, and registrations.
    JSON source:\n```json\n{json.dumps(snapshot)}\n```
    Return JSON with keys employees (string), revenue (string), stage (string from allowed set).
    """

    chat = client.chat.create(model="grok-4-1-fast-reasoning")
    chat.append(user(prompt))
    response = chat.sample()
    try:
        ai_data = json.loads(response.content)
        for key in ("employees", "revenue", "stage"):
            if not profile.get(key) and isinstance(ai_data.get(key), str):
                profile[key] = ai_data[key]
    except (json.JSONDecodeError, TypeError):
        st.warning("AI enrichment failed; using defaults for missing fields.")
    return profile

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
growth_stage = st.selectbox("Stage (override)", ["Auto (AI)", "Pre-seed", "Seed", "Growth", "Scale-up", "Mature"])

if st.button("Get Advice", type="primary"):
    with st.spinner("Searching & advising... (Grok + web/X tools)"):
        profile, company_record = fetch_company_profile(business_id)
        client = Client()  # Auto-uses XAI_API_KEY

        if company_record:
            profile = enrich_profile_with_ai(client, profile, company_record)

        if growth_stage != "Auto (AI)":
            profile["stage"] = growth_stage

        profile["employees"] = profile.get("employees") or "Unknown"
        profile["revenue"] = profile.get("revenue") or "Unknown"
        profile["stage"] = profile.get("stage") or "Growth"

        need = {"amount": funding_amount, "purpose": funding_purpose}

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