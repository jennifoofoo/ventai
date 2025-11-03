# Market Mapper - startup discovery app
import streamlit as st
import sys
from pathlib import Path

# Import path setup
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.research_agent import ResearchAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.enrichment_agent import EnrichmentAgent
from src.utils import save_results
from src.visualize import create_category_bar_chart, create_country_pie_chart
from src.config import FEEDS_BY_TOPIC

# Page setup
st.set_page_config(page_title="Market Mapper", page_icon="🧭", layout="wide")

# Header
st.title("🧭 Market Mapper – Multi-Agent Startup Discovery")
st.markdown("Discover and analyze startups using RSS feeds and OpenVC datasets")

# Session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_df' not in st.session_state:
    st.session_state.analysis_df = None
if 'insights_summary' not in st.session_state:
    st.session_state.insights_summary = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📊 Feed Category")
    feed_category = st.selectbox(
        "Select RSS feed category",
        options=list(FEEDS_BY_TOPIC.keys()),
        index=0
    )
    st.caption(f"Will fetch from {len(FEEDS_BY_TOPIC[feed_category])} feeds")
    
    st.subheader("📊 Data Sources")
    include_openvc = st.checkbox("Include OpenVC dataset", value=True)
    enable_enrichment = st.checkbox("Enrich from Websites", value=False)
    
    st.markdown("---")
    
    st.subheader("🔧 Processing")
    max_entries_per_feed = st.slider("Max entries per RSS feed", 10, 50, 30)
    n_clusters = st.slider("Number of clusters", 3, 10, 6)
    model_name = st.text_input("Ollama model", value="mistral")
    
    st.markdown("---")
    st.markdown("### ℹ️ Requirements")
    st.markdown("""
    - Ollama must be installed and running
    - Model 'mistral' must be pulled
    - Run: `ollama serve` in terminal
    """)

# Main input
topic = st.text_input("Enter a topic to research", placeholder="e.g., AI for SMEs Europe", key="topic_input")

col1, col2 = st.columns([1, 4])
with col1:
    run_button = st.button("🚀 Run Market Mapping", type="primary", use_container_width=True)

status_container = st.container()
results_container = st.container()

if run_button and topic:
    # Clear previous results
    st.session_state.results = None
    st.session_state.analysis_df = None
    st.session_state.insights_summary = None
    
    # Initialize status placeholders
    with status_container:
        st.header("📊 Agent Progress")
        
        research_status = st.empty()
        extraction_status = st.empty()
        enrichment_status = st.empty()
        analysis_status = st.empty()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Status callback functions
    research_messages = []
    extraction_messages = []
    enrichment_messages = []
    analysis_messages = []
    
    def research_callback(msg):
        research_messages.append(msg)
        research_status.text_area("ResearchAgent", "\n".join(research_messages[-8:]), height=120, disabled=True)
    
    def extraction_callback(msg):
        extraction_messages.append(msg)
        extraction_status.text_area("ExtractionAgent", "\n".join(extraction_messages[-8:]), height=120, disabled=True)
    
    def enrichment_callback(msg):
        enrichment_messages.append(msg)
        enrichment_status.text_area("EnrichmentAgent", "\n".join(enrichment_messages[-8:]), height=120, disabled=True)
    
    def analysis_callback(msg):
        analysis_messages.append(msg)
        analysis_status.text_area("AnalysisAgent", "\n".join(analysis_messages[-8:]), height=120, disabled=True)
    
    try:
        # Step 1: Research
        progress_bar.progress(10)
        status_text.text(f"🔍 Phase 1/4: Fetching data from '{feed_category}' feeds...")
        
        research_agent = ResearchAgent(max_entries_per_feed=max_entries_per_feed)
        research_agent.set_status_callback(research_callback)
        articles = research_agent.fetch_all_sources(
            feed_category=feed_category,
            include_openvc=include_openvc
        )
        
        if not articles:
            st.error("❌ No data found from sources. Please check your internet connection or try a different category.")
            st.stop()
        
        rss_count = sum(1 for a in articles if a.get('source') != 'OpenVC')
        openvc_count = sum(1 for a in articles if a.get('source') == 'OpenVC')
        research_callback(f"🔍 ResearchAgent: Loaded {len(FEEDS_BY_TOPIC[feed_category])} feeds for '{feed_category}'")
        research_callback(f"📰 Collected {rss_count} articles + {openvc_count} OpenVC entries")
        
        # Step 2: Extraction
        progress_bar.progress(40)
        status_text.text("🤖 Phase 2/4: Extracting startup information with Ollama...")
        
        extraction_agent = ExtractionAgent(model=model_name)
        extraction_agent.set_status_callback(extraction_callback)
        startups = extraction_agent.extract_startups(articles, topic)
        
        if not startups:
            st.warning("⚠️ No startups extracted. The data may not contain relevant startup information.")
            st.stop()
        
        extraction_callback(f"🧠 ExtractionAgent: Identified {len(startups)} startups via Ollama")
        
        # Step 3: Enrichment (optional)
        if enable_enrichment:
            progress_bar.progress(70)
            status_text.text("🌐 Phase 3/4: Enriching startup data from websites...")
            
            enrichment_agent = EnrichmentAgent()
            enrichment_agent.set_status_callback(enrichment_callback)
            startups = enrichment_agent.enrich_startups(startups)
        else:
            progress_bar.progress(70)
            enrichment_status.text_area("EnrichmentAgent", "⏭️ Skipped (disabled)", height=120, disabled=True)
        
        # Step 4: Analysis
        progress_bar.progress(80)
        status_text.text("📊 Phase 4/4: Analyzing and clustering...")
        
        analysis_agent = AnalysisAgent(n_clusters=n_clusters)
        analysis_agent.set_status_callback(analysis_callback)
        df = analysis_agent.analyze(startups)
        
        # Generate insights summary
        insights_summary = analysis_agent.generate_insights_summary()
        
        # Save results
        output_path = save_results(startups, topic)
        
        # Update session state
        st.session_state.results = startups
        st.session_state.analysis_df = df
        st.session_state.insights_summary = insights_summary
        
        # Complete
        progress_bar.progress(100)
        n_clusters_found = df['cluster'].nunique() if 'cluster' in df.columns else 0
        analysis_callback(f"📊 AnalysisAgent: Clustered into {n_clusters_found} categories")
        status_text.success(f"✅ Report ready! Found {len(startups)} startups from {len(articles)} data points.")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

# Display results
if st.session_state.results and st.session_state.analysis_df is not None:
    with results_container:
        st.markdown("---")
        st.header("📈 Results")
        
        df = st.session_state.analysis_df
        
        # Insights Summary
        if st.session_state.insights_summary:
            st.info(f"💡 **Insights**: {st.session_state.insights_summary}")
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Startups", len(df))
        with col2:
            st.metric("Unique Countries", df['country'].nunique() if 'country' in df.columns else 0)
        with col3:
            st.metric("Categories", df['category'].nunique() if 'category' in df.columns else 0)
        with col4:
            st.metric("Clusters", df['cluster'].nunique() if 'cluster' in df.columns else 0)
        
        # Data table
        st.subheader("📋 Startup Data")
        display_cols = ['name', 'description', 'country', 'category']
        if 'cluster' in df.columns:
            display_cols.append('cluster')
        
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols], use_container_width=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            category_chart = create_category_bar_chart(df)
            if category_chart:
                st.plotly_chart(category_chart, use_container_width=True)
            else:
                st.info("No category data available for chart")
        
        with col2:
            country_chart = create_country_pie_chart(df)
            if country_chart:
                st.plotly_chart(country_chart, use_container_width=True)
            else:
                st.info("No country data available for chart")
        
        # Download button
        st.markdown("---")
        import json
        json_str = json.dumps(st.session_state.results, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"startups_{topic.replace(' ', '_')[:50]}.json",
            mime="application/json"
        )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Powered by Ollama (local LLM) + Python Agents • "
    "Built with Streamlit"
    "</div>",
    unsafe_allow_html=True
)
