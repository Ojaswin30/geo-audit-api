import os
import sys
import json
from urllib.parse import urlparse
import streamlit as st

# Ensure backend directory is in Python path for direct module imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from scraper import scrape_page
    from schema_recommender import get_schema_recommendation
    from model import set_gemini_api_key, is_gemini_configured
except ImportError as e:
    st.error(f"Failed to import backend modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="GEO Audit & Schema Recommender",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Dark theme accents, polished cards & badges)
st.markdown("""
<style>
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 700;
        color: #818cf8;
    }
    
    /* Card container */
    .geo-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }
    
    .geo-card-header {
        font-weight: 600;
        font-size: 1rem;
        color: #f8fafc;
        margin-bottom: 8px;
    }

    /* Badges */
    .badge-primary {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #312e81;
        color: #c7d2fe;
        border: 1px solid #4338ca;
    }
    
    .badge-success {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #064e3b;
        color: #a7f3d0;
        border: 1px solid #047857;
    }

    .badge-warning {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #78350f;
        color: #fde68a;
        border: 1px solid #b45309;
    }

    /* Header title */
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# Sample URLs for quick demonstration
SAMPLE_URLS = [
    {"name": "Stripe", "url": "https://stripe.com", "type": "Organization"},
    {"name": "Notion", "url": "https://www.notion.so", "type": "Product / App"},
    {"name": "TechCrunch", "url": "https://techcrunch.com", "type": "Article / News"},
    {"name": "Vercel", "url": "https://vercel.com", "type": "Tech Platform"},
]

# Check existing Gemini API Key from environment or secrets
current_api_key = os.getenv("GEMINI_API_KEY", "")
if not current_api_key and "GEMINI_API_KEY" in st.secrets:
    current_api_key = st.secrets["GEMINI_API_KEY"]
    set_gemini_api_key(current_api_key)

# Initialize Session State
if "target_url" not in st.session_state:
    st.session_state.target_url = "https://stripe.com"
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "is_auditing" not in st.session_state:
    st.session_state.is_auditing = False

# Sidebar Configuration & Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/search-in-browser.png", width=54)
    st.markdown("### GEO Audit Platform")
    st.caption("Generative Engine Optimization & Structured Data Engine")

    st.markdown("---")
    st.markdown("#### 🔑 LLM Engine Settings")

    api_key_input = st.text_input(
        "Gemini API Key",
        value=current_api_key,
        type="password",
        help="Enter your Google Gemini API key from https://aistudio.google.com. Falls back to deterministic rule engine if empty.",
    )

    if api_key_input != current_api_key:
        if api_key_input.strip():
            set_gemini_api_key(api_key_input.strip())
            st.success("API key updated!")
        else:
            set_gemini_api_key("")
            st.info("Operating in Rule-Based Fallback mode.")

    if is_gemini_configured():
        st.markdown(
            '<span class="badge-success">● Gemini 2.0 Flash Active</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="badge-warning">● Rule-Based Fallback Active</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### ⚡ Quick Samples")
    for sample in SAMPLE_URLS:
        if st.button(f"{sample['name']} ({sample['type']})", use_container_width=True, key=f"sample_{sample['name']}"):
            st.session_state.target_url = sample["url"]
            st.rerun()

    st.markdown("---")
    with st.expander("🏗️ Scaling Architecture (50+ Pages)"):
        st.markdown("""
        **Enterprise Crawler Roadmap:**
        - **Queue Worker Pool:** Celery + Redis distributing page fetches across worker instances.
        - **Filter Gate:** Heuristic checks classify schema type sub-millisecond; LLM is only called on content-rich key landing pages.
        - **Rate Limiting & Retries:** Circuit breakers for anti-bot blocks, dead-letter queues for transient timeouts.
        - **URL Hash Caching:** Redis TTL caching on normalized URL hashes to avoid duplicate crawls.
        """)

    with st.expander("📋 Design Decision Log"):
        st.markdown("""
        1. **Hybrid Architecture:** Keyword heuristics detect entity type deterministically; Gemini synthesizes complex metadata (`sameAs`, `founder`, `offers`).
        2. **BeautifulSoup vs Playwright:** BS4 + Requests ensures lightweight execution and zero headless browser overhead.
        3. **Graceful Degradation:** If LLM quota fails or network errors occur, rule-based JSON-LD ensures 100% API uptime.
        """)


# Main App Header
st.markdown('<div class="hero-title">GEO Audit & AI Schema Recommender</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Audit any public webpage for Generative Engine Optimization (GEO) & generate Schema.org JSON-LD graphs with Gemini 2.0 Flash.</div>',
    unsafe_allow_html=True,
)

# Input Row
col_url, col_btn = st.columns([5, 1])
with col_url:
    input_url = st.text_input(
        "Webpage URL",
        value=st.session_state.target_url,
        placeholder="https://example.com",
        label_visibility="collapsed",
    )
with col_btn:
    audit_clicked = st.button("🚀 Run Audit", type="primary", use_container_width=True)

# URL Normalization & Execution
if audit_clicked:
    if not input_url or not input_url.strip():
        st.error("Please enter a valid webpage URL.")
    else:
        normalized_url = input_url.strip()
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = "https://" + normalized_url

        st.session_state.target_url = normalized_url

        with st.status("Analyzing Webpage & Generating Schema...", expanded=True) as status:
            try:
                st.write("🌐 Fetching webpage HTML & extracting metadata...")
                scraped = scrape_page(normalized_url)

                st.write("🔍 Parsing DOM headings hierarchy & discovering social links...")
                schema_json_ld, schema_type, llm_used = get_schema_recommendation(normalized_url, scraped)

                st.write("🤖 Synthesizing Schema.org @graph entity structure...")
                st.session_state.audit_data = {
                    "url": normalized_url,
                    "title": scraped.get("title"),
                    "meta_description": scraped.get("meta_description"),
                    "headings": scraped.get("headings", []),
                    "image_url": scraped.get("image_url"),
                    "social_links": scraped.get("social_links", []),
                    "schema_type": schema_type,
                    "json_ld": schema_json_ld,
                    "llm_used": llm_used,
                    "raw_text": scraped.get("raw_text", ""),
                }
                status.update(label="Audit Completed Successfully!", state="complete", expanded=False)
            except Exception as err:
                status.update(label="Audit Failed", state="error", expanded=True)
                st.error(f"Error auditing {normalized_url}: {err}")


# Display Results
audit_result = st.session_state.audit_data
if audit_result:
    st.markdown("---")

    # Top KPI Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Detected Schema Type", audit_result["schema_type"])
    with m_col2:
        engine_label = "Gemini 2.0 Flash" if audit_result["llm_used"] else "Rule-based Fallback"
        st.metric("Generation Engine", engine_label)
    with m_col3:
        st.metric("Headings Discovered", len(audit_result["headings"]))
    with m_col4:
        st.metric("Social Links Linked", len(audit_result["social_links"]))

    # Summary Overview Card
    with st.container():
        st.markdown(
            f"""
            <div class="geo-card">
                <div class="geo-card-header">📄 Page Overview: <a href="{audit_result['url']}" target="_blank" style="color: #818cf8; text-decoration: none;">{audit_result['url']} ↗</a></div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #ffffff; margin-bottom: 6px;">{audit_result['title'] or 'No Title Found'}</div>
                <div style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">{audit_result['meta_description'] or 'No meta description found on this page.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tabs for Data Presentation
    tab_schema, tab_extracted, tab_geo = st.tabs([
        "🏷️ Schema.org JSON-LD",
        "📑 Extracted Content & Headings",
        "🚀 Generative Engine Optimization (GEO)",
    ])

    # Tab 1: Schema.org JSON-LD
    with tab_schema:
        formatted_json = json.dumps(audit_result["json_ld"], indent=2)

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            if audit_result["llm_used"]:
                st.markdown('<span class="badge-success">✨ LLM-Synthesized Multi-Entity Graph</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge-warning">⚡ Deterministic Rule Fallback Graph</span>', unsafe_allow_html=True)
        with c2:
            st.download_button(
                label="📥 Download JSON-LD",
                data=formatted_json,
                file_name="schema.jsonld",
                mime="application/ld+json",
                use_container_width=True,
            )
        with c3:
            st.link_button(
                "🧪 Google Rich Results Test",
                url=f"https://search.google.com/test/rich-results?url={audit_result['url']}",
                use_container_width=True,
            )

        st.code(formatted_json, language="json")

        # Schema Graph Nodes Breakdown
        graph_nodes = audit_result["json_ld"].get("@graph", [])
        if graph_nodes:
            with st.expander("🔍 View Dissected Graph Entities (@graph)"):
                for node in graph_nodes:
                    node_type = node.get("@type", "Unknown")
                    node_id = node.get("@id", "N/A")
                    st.markdown(f"**Entity:** `{node_type}` &nbsp;|&nbsp; **ID:** `{node_id}`")
                    st.json(node, expanded=False)

    # Tab 2: Extracted Page Data
    with tab_extracted:
        if audit_result["social_links"]:
            st.markdown("##### 🔗 Discovered Social & Authority Profiles")
            social_cols = st.columns(min(len(audit_result["social_links"]), 4))
            for i, link in enumerate(audit_result["social_links"]):
                col_idx = i % len(social_cols)
                with social_cols[col_idx]:
                    st.markdown(f"• [{link.split('//')[-1]}]({link})")
            st.markdown("---")

        st.markdown("##### 🧱 Extracted Headings Hierarchy")
        if audit_result["headings"]:
            for i, h in enumerate(audit_result["headings"]):
                tag = h.get("tag", "H")
                text = h.get("text", "")
                content = h.get("content", "No direct text block detected.")
                with st.expander(f"[{tag}] {text}", expanded=(i < 3)):
                    st.markdown(f"**Text Content:**")
                    st.caption(content)
        else:
            st.info("No H1, H2, or H3 headings detected on this webpage.")

        st.markdown("---")
        with st.expander("📄 Raw Page Text Snippet"):
            st.text_area("Snippet", value=audit_result.get("raw_text", "")[:2000], height=180, disabled=True)

    # Tab 3: GEO Scorecard & Recommendations
    with tab_geo:
        st.markdown("##### 🤖 Generative Engine Optimization (GEO) Readiness")
        st.caption("How readily can AI search engines (Perplexity, ChatGPT Search, Google AI Overviews) extract and cite entities from this page?")

        # Calculate heuristic score
        score = 0
        checks = []

        # 1. Title & Meta
        if audit_result["title"] and len(audit_result["title"]) > 10:
            score += 25
            checks.append(("✅", "Page title is clear and descriptive", "+25%"))
        else:
            checks.append(("⚠️", "Page title is missing or too short", "0%"))

        if audit_result["meta_description"] and len(audit_result["meta_description"]) > 50:
            score += 25
            checks.append(("✅", "Meta description provides solid contextual summary", "+25%"))
        else:
            checks.append(("⚠️", "Meta description is missing or brief", "0%"))

        # 2. Semantic headings
        if len(audit_result["headings"]) >= 3:
            score += 25
            checks.append(("✅", f"Strong semantic heading structure ({len(audit_result['headings'])} headings found)", "+25%"))
        else:
            checks.append(("⚠️", "Sparse heading structure (fewer than 3 headings)", "0%"))

        # 3. Entity Graph
        if audit_result["json_ld"] and "@graph" in audit_result["json_ld"]:
            score += 25
            checks.append(("✅", f"Structured JSON-LD entity graph generated ({audit_result['schema_type']})", "+25%"))
        else:
            checks.append(("⚠️", "Structured data graph not detected", "0%"))

        st.progress(score / 100)
        st.markdown(f"### AI Visibility Index: **{score}%**")

        c_chk1, c_chk2 = st.columns(2)
        with c_chk1:
            st.markdown("##### 📋 Checklist Breakdown")
            for icon, msg, pts in checks:
                st.markdown(f"{icon} **{msg}** `{pts}`")

        with c_chk2:
            st.markdown("##### 💡 Actionable GEO Improvements")
            if score == 100:
                st.success("Excellent GEO readiness! Embed the generated JSON-LD script into the `<head>` of your page to claim top search citations.")
            else:
                st.markdown("""
                - **Embed Schema Markup:** Add the generated JSON-LD block inside `<script type="application/ld+json">` in your `<head>`.
                - **Entity Disambiguation:** Link official LinkedIn, X/Twitter, or Crunchbase profiles using `sameAs` attributes.
                - **Synthesizable Headings:** Ensure `<h2>` and `<h3>` tags have direct concise explanatory paragraphs immediately below them.
                """)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #64748b; font-size: 0.8rem; padding: 12px 0;">'
    'GEO Audit Platform • Built for Villion GEO SaaS Competency Assessment • Ready for GitHub & Streamlit Cloud Deployment'
    '</div>',
    unsafe_allow_html=True,
)
