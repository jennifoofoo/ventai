# VentAI - AI-powered venture intelligence app
import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

# Import path setup
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.research_agent import ResearchAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.enrichment_agent import EnrichmentAgent
from src.agents.trend_agent import TrendAgent
from src.utils import save_results
from src.visualize import create_category_bar_chart, create_country_pie_chart
from src.config import FEEDS_BY_TOPIC

# Page setup
st.set_page_config(page_title="VentAI", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for modern styling
st.markdown("""
<style>
    .hero-section {
        text-align: center;
        padding: 4em 2em 3em 2em;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        margin-bottom: 3em;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 3.5em;
        font-weight: bold;
        margin-bottom: 0.3em;
    }
    .hero-subtitle {
        font-size: 1.3em;
        opacity: 0.95;
        margin-bottom: 2em;
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    /* Wide layout for main content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_df' not in st.session_state:
    st.session_state.analysis_df = None
if 'insights_summary' not in st.session_state:
    st.session_state.insights_summary = None
if 'topic' not in st.session_state:
    st.session_state.topic = ""
if 'scan_completed' not in st.session_state:
    st.session_state.scan_completed = False
if 'should_run_scan' not in st.session_state:
    st.session_state.should_run_scan = False
if 'config_values' not in st.session_state:
    st.session_state.config_values = {}
if 'trend_data' not in st.session_state:
    st.session_state.trend_data = None
if 'trend_keywords' not in st.session_state:
    st.session_state.trend_keywords = ""

# Sidebar - Complete Control Center
with st.sidebar:
    st.markdown("### 🧠 VentAI")
    st.markdown("---")
    
    # Status indicator
    if st.session_state.should_run_scan and not st.session_state.scan_completed:
        st.warning("🔄 Running VentAI...")
    elif st.session_state.scan_completed:
        st.success("✅ VentAI Ready")
    else:
        st.info("🔍 Ready for research")
    
    st.markdown("---")
    
    # 🧩 Configuration Section
    st.markdown("### 🧩 Configuration")
    
    # Get saved category or default
    saved_category = st.session_state.config_values.get('feed_category', list(FEEDS_BY_TOPIC.keys())[0])
    category_index = list(FEEDS_BY_TOPIC.keys()).index(saved_category) if saved_category in FEEDS_BY_TOPIC else 0
    
    # Disable sidebar during processing
    sidebar_disabled = st.session_state.should_run_scan and not st.session_state.scan_completed
    
    feed_category = st.selectbox(
        "RSS Feed Category:",
        options=list(FEEDS_BY_TOPIC.keys()),
        index=category_index,
        help="Choose which category of RSS feeds to fetch",
        disabled=sidebar_disabled
    )
    st.caption(f"📡 {len(FEEDS_BY_TOPIC[feed_category])} feeds selected")
    
    st.markdown("---")
    
    # 📊 Data Sources Section
    st.markdown("### 📊 Data Sources")
    
    include_openvc = st.checkbox(
        "Include OpenVC dataset", 
        value=st.session_state.config_values.get('include_openvc', True),
        disabled=sidebar_disabled
    )
    enable_enrichment = st.checkbox(
        "Enrich from Websites", 
        value=st.session_state.config_values.get('enable_enrichment', False),
        disabled=sidebar_disabled,
        help="Scrape company websites for additional details"
    )
    
    st.markdown("---")
    
    # ⚙️ Processing Options Section
    st.markdown("### ⚙️ Processing Options")
    
    max_entries_per_feed = st.slider(
        "Max entries per RSS feed", 
        10, 50, 
        st.session_state.config_values.get('max_entries_per_feed', 30),
        disabled=sidebar_disabled
    )
    
    n_clusters = st.slider(
        "Number of clusters", 
        3, 10, 
        st.session_state.config_values.get('n_clusters', 6),
        disabled=sidebar_disabled,
        help="Clustering granularity for analysis"
    )
    
    model_name = st.text_input(
        "Ollama model", 
        value=st.session_state.config_values.get('model_name', 'mistral'),
        disabled=sidebar_disabled,
        help="Local LLM model name"
    )
    
    st.markdown("---")
    
    # 🔍 Advanced Settings (optional placeholder)
    with st.expander("🔍 Advanced Settings"):
        st.caption("Advanced options coming soon")
        # Placeholder for future advanced settings
    
    st.markdown("---")
    
    # Store config values in session state
    st.session_state.config_values = {
        'feed_category': feed_category,
        'include_openvc': include_openvc,
        'enable_enrichment': enable_enrichment,
        'max_entries_per_feed': max_entries_per_feed,
        'n_clusters': n_clusters,
        'model_name': model_name
    }
    
    # About section at bottom
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("""
    AI-powered venture intelligence engine.
    
    Uses local LLM (Ollama) to analyze startup ecosystems.
    """)
    
    st.markdown("### 📋 Requirements")
    st.caption("""
    - Ollama installed
    - Model 'mistral' pulled
    - Run: `ollama serve`
    """)

# Hero Section - Simple and Prominent
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🧠 VentAI</div>
    <div class="hero-subtitle">AI-Powered Venture Intelligence</div>
    <p style="font-size: 1em; opacity: 0.85; margin-bottom: 2em;">Discover and analyze venture trends across global startup ecosystems</p>
</div>
""", unsafe_allow_html=True)

# Topic Input and Run Button - Centered in Hero Area
col1, col2, col3 = st.columns([1.5, 3, 1.5])
with col2:
    topic_input = st.text_input(
        "Enter your research topic:",
        placeholder="e.g., AI in Manufacturing Europe",
        key="topic_input_hero",
        label_visibility="collapsed",
        value=st.session_state.get('topic', '')
    )
    
    # Run button - centered below input
    run_research = st.button("🚀 Run Research", type="primary", use_container_width=True)

# Trigger scan
if run_research and topic_input:
    st.session_state.topic = topic_input
    st.session_state.scan_completed = False
    st.session_state.should_run_scan = True
    st.rerun()

# Tabs - Only show after research has started
if st.session_state.should_run_scan or st.session_state.scan_completed or st.session_state.results:
    tab_config, tab_analysis, tab_trends = st.tabs(["⚙️ Configuration", "📊 Analysis", "📈 Trend Radar"])
    
    # Configuration Tab - Now just shows saved settings
    with tab_config:
        st.header("⚙️ Current Configuration")
        st.info("💡 All configuration options are available in the sidebar. Adjust settings there before running research.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Sources")
            config = st.session_state.config_values
            st.write(f"**Feed Category:** {config.get('feed_category', 'N/A')}")
            st.write(f"**OpenVC Dataset:** {'✅ Enabled' if config.get('include_openvc', False) else '❌ Disabled'}")
            st.write(f"**Website Enrichment:** {'✅ Enabled' if config.get('enable_enrichment', False) else '❌ Disabled'}")
        
        with col2:
            st.subheader("⚙️ Processing Options")
            st.write(f"**Max entries per feed:** {config.get('max_entries_per_feed', 'N/A')}")
            st.write(f"**Number of clusters:** {config.get('n_clusters', 'N/A')}")
            st.write(f"**Ollama model:** {config.get('model_name', 'N/A')}")
        
        st.markdown("---")
        st.markdown("### 💡 Usage")
        st.markdown("""
        1. Configure settings in the **sidebar** (left)
        2. Enter topic in the **hero section** above
        3. Click **"🚀 Run Research"**
        4. View results in **Analysis** tab
        """)

# Analysis Tab
if st.session_state.should_run_scan or st.session_state.scan_completed or st.session_state.results:
    with tab_analysis:
        # Check if we should run research
        current_topic = st.session_state.get('topic', "")
        
        if current_topic and st.session_state.should_run_scan and not st.session_state.scan_completed:
            # Run the research workflow
            with st.container():
                st.header("📊 Running Intelligence Scan")
                
                research_status = st.empty()
                extraction_status = st.empty()
                enrichment_status = st.empty()
                analysis_status = st.empty()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Status callbacks
                research_messages = []
                extraction_messages = []
                enrichment_messages = []
                analysis_messages = []
                
                def research_callback(msg):
                    research_messages.append(msg)
                    research_status.text_area("ResearchAgent", "\n".join(research_messages[-5:]), height=100, disabled=True, label_visibility="collapsed")
                
                def extraction_callback(msg):
                    extraction_messages.append(msg)
                    extraction_status.text_area("ExtractionAgent", "\n".join(extraction_messages[-5:]), height=100, disabled=True, label_visibility="collapsed")
                
                def enrichment_callback(msg):
                    enrichment_messages.append(msg)
                    enrichment_status.text_area("EnrichmentAgent", "\n".join(enrichment_messages[-5:]), height=100, disabled=True, label_visibility="collapsed")
                
                def analysis_callback(msg):
                    analysis_messages.append(msg)
                    analysis_status.text_area("AnalysisAgent", "\n".join(analysis_messages[-5:]), height=100, disabled=True, label_visibility="collapsed")
                
                try:
                    # Get config from session state
                    config_values = st.session_state.get('config_values', {})
                    config_category = config_values.get('feed_category', list(FEEDS_BY_TOPIC.keys())[0])
                    config_openvc = config_values.get('include_openvc', True)
                    config_enrichment = config_values.get('enable_enrichment', False)
                    config_max_entries = config_values.get('max_entries_per_feed', 30)
                    config_clusters = config_values.get('n_clusters', 6)
                    config_model = config_values.get('model_name', 'mistral')
                    
                    # Step 1: Research
                    progress_bar.progress(10)
                    status_text.text("🔍 VentAI: Starting venture intelligence workflow...")
                    
                    research_agent = ResearchAgent(max_entries_per_feed=config_max_entries)
                    research_agent.set_status_callback(research_callback)
                    articles = research_agent.fetch_all_sources(
                        feed_category=config_category,
                        include_openvc=config_openvc
                    )
                    
                    if not articles:
                        st.error("❌ No data found from sources. Please check your internet connection.")
                        st.stop()
                    
                    rss_count = sum(1 for a in articles if a.get('source') != 'OpenVC')
                    openvc_count = sum(1 for a in articles if a.get('source') == 'OpenVC')
                    research_callback(f"🔍 VentAI: Fetched {rss_count} articles from {len(FEEDS_BY_TOPIC[config_category])} feeds")
                    
                    # Step 2: Extraction
                    progress_bar.progress(40)
                    status_text.text("🧠 VentAI: Extracting startup intelligence with Ollama...")
                    
                    extraction_agent = ExtractionAgent(model=config_model)
                    extraction_agent.set_status_callback(extraction_callback)
                    startups = extraction_agent.extract_startups(articles, current_topic)
                    
                    if not startups:
                        st.warning("⚠️ No startups extracted. The data may not contain relevant startup information.")
                        st.stop()
                    
                    extraction_callback(f"🧠 VentAI: Identified {len(startups)} startups via Ollama")
                    
                    # Step 3: Enrichment (optional)
                    if config_enrichment:
                        progress_bar.progress(70)
                        status_text.text("🌐 VentAI: Enriching venture data from websites...")
                        
                        enrichment_agent = EnrichmentAgent()
                        enrichment_agent.set_status_callback(enrichment_callback)
                        startups = enrichment_agent.enrich_startups(startups)
                    else:
                        progress_bar.progress(70)
                        enrichment_status.text_area("EnrichmentAgent", "⏭️ Skipped (disabled)", height=100, disabled=True, label_visibility="collapsed")
                    
                    # Step 4: Analysis
                    progress_bar.progress(80)
                    status_text.text("📊 VentAI: Clustering and analyzing venture data...")
                    
                    analysis_agent = AnalysisAgent(n_clusters=config_clusters)
                    analysis_agent.set_status_callback(analysis_callback)
                    df = analysis_agent.analyze(startups)
                    
                    # Generate insights summary
                    insights_summary = analysis_agent.generate_insights_summary()
                    
                    # Save results
                    output_path = save_results(startups, current_topic)
                    
                    # Update session state
                    st.session_state.results = startups
                    st.session_state.analysis_df = df
                    st.session_state.insights_summary = insights_summary
                    st.session_state.scan_completed = True
                    st.session_state.should_run_scan = False
                    
                    # Complete
                    progress_bar.progress(100)
                    n_clusters_found = df['cluster'].nunique() if 'cluster' in df.columns else 0
                    analysis_callback(f"📊 VentAI: Clustered into {n_clusters_found} categories")
                    status_text.success(f"✅ VentAI Intelligence Report Ready!")
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)
        
        # Display results if available
        if st.session_state.results and st.session_state.analysis_df is not None:
            df = st.session_state.analysis_df.copy()
            
            # Insights Summary
            if st.session_state.insights_summary:
                st.info(f"💡 **Insights**: {st.session_state.insights_summary}")
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Startups Extracted", len(df))
            with col2:
                st.metric("Countries Covered", df['country'].nunique() if 'country' in df.columns else 0)
            with col3:
                st.metric("Categories", df['category'].nunique() if 'category' in df.columns else 0)
            with col4:
                st.metric("Clusters", df['cluster'].nunique() if 'cluster' in df.columns else 0)
            
            # Filters
            st.subheader("🔍 Filters")
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                if 'country' in df.columns and len(df['country'].dropna().unique()) > 0:
                    available_countries = sorted(df['country'].dropna().unique())
                    country_filter = st.multiselect(
                        "Filter by Country:",
                        options=available_countries,
                        default=[]
                    )
                else:
                    country_filter = []
            
            with filter_col2:
                if 'category' in df.columns and len(df['category'].dropna().unique()) > 0:
                    available_categories = sorted(df['category'].dropna().unique())
                    category_filter = st.multiselect(
                        "Filter by Category:",
                        options=available_categories,
                        default=[]
                    )
                else:
                    category_filter = []
            
            # Apply filters
            filtered_df = df.copy()
            if country_filter:
                filtered_df = filtered_df[filtered_df['country'].isin(country_filter)]
            if category_filter:
                filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
            
            # Data table
            st.subheader("📋 Startup Data")
            display_cols = ['name', 'description', 'country', 'category']
            if 'cluster' in filtered_df.columns:
                display_cols.append('cluster')
            
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            st.dataframe(filtered_df[available_cols], width='stretch', height=400)
            
            # Charts
            st.subheader("📊 Visualizations")
            chart_tab1, chart_tab2 = st.tabs(["Category Distribution", "Country Breakdown"])
            
            with chart_tab1:
                category_chart = create_category_bar_chart(filtered_df)
                if category_chart:
                    st.plotly_chart(category_chart, width='stretch')
                else:
                    st.info("No category data available")
            
            with chart_tab2:
                country_chart = create_country_pie_chart(filtered_df)
                if country_chart:
                    st.plotly_chart(country_chart, width='stretch')
                else:
                    st.info("No country data available")
            
            # Export
            st.subheader("💾 Export Data")
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Export as CSV",
                    data=csv_data,
                    file_name=f"ventai_results_{current_topic.replace(' ', '_')[:30]}.csv",
                    mime="text/csv",
                    width='stretch'
                )
            
            with export_col2:
                json_data = filtered_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📦 Export as JSON",
                    data=json_data,
                    file_name=f"ventai_results_{current_topic.replace(' ', '_')[:30]}.json",
                    mime="application/json",
                    width='stretch'
                )
        else:
            # Empty state
            st.info("👆 Enter a research topic in the hero section above and click 'Run Research' to start analysis.")
else:
    # Empty state before research
    st.markdown("---")
    st.info("""
    👆 **Get Started:**
    1. Configure your settings in the **sidebar** (left)
    2. Enter a research topic in the **hero section** above
    3. Click **"🚀 Run Research"** to start analysis
    """)

# Trend Radar Tab
if st.session_state.should_run_scan or st.session_state.scan_completed or st.session_state.results:
    with tab_trends:
        st.header("📈 VentAI Trend Radar")
        st.caption("Analyze emerging topics from Google Trends, GitHub, and Reddit.")
        
        # Trend keywords input
        col_input, col_button = st.columns([3, 1])
        with col_input:
            trend_keywords = st.text_input(
                "Enter up to 5 keywords to analyze (comma-separated):",
                value=st.session_state.trend_keywords,
                placeholder="e.g., AI, climate tech, robotics, fintech, SaaS",
                key="trend_keywords_input"
            )
        with col_button:
            run_trend_analysis = st.button("🔍 Run Trend Analysis", type="primary", width='stretch')
        
        # Store keywords in session state
        if trend_keywords:
            st.session_state.trend_keywords = trend_keywords
        
        # Run trend analysis
        if run_trend_analysis and trend_keywords:
            keywords_list = [k.strip() for k in trend_keywords.split(",") if k.strip()]
            if keywords_list:
                with st.spinner("📈 Analyzing trends from multiple sources..."):
                    # Status callback
                    status_container = st.empty()
                    trend_messages = []
                    
                    def trend_callback(msg):
                        trend_messages.append(msg)
                        status_container.text_area(
                            "Trend Analysis Status",
                            "\n".join(trend_messages[-10:]),
                            height=150,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    
                    # Run TrendAgent
                    try:
                        agent = TrendAgent(keywords_list, status_callback=trend_callback)
                        df = agent.run()
                        
                        if not df.empty:
                            st.session_state.trend_data = df
                            st.success(f"✅ Fetched {len(df)} trend data points from multiple sources.")
                        else:
                            st.warning("⚠️ No trend data collected. Please try different keywords.")
                    except Exception as e:
                        st.error(f"❌ Error running trend analysis: {str(e)}")
        
        # Display trend data if available
        if st.session_state.trend_data is not None and not st.session_state.trend_data.empty:
            df = st.session_state.trend_data.copy()
            
            # Google Trends visualization
            google_df = df[df["source"] == "Google Trends"]
            if not google_df.empty:
                st.markdown("---")
                st.subheader("📊 Google Trends Interest (Last 3 Months)")
                
                # Pivot for line chart
                try:
                    google_pivot = google_df.pivot_table(
                        index='date',
                        columns='keyword',
                        values='interest',
                        aggfunc='mean'
                    ).fillna(0)
                    
                    st.line_chart(google_pivot)
                    
                    # Summary stats
                    col1, col2 = st.columns(2)
                    with col1:
                        avg_interest = google_df.groupby('keyword')['interest'].mean().sort_values(ascending=False)
                        st.metric("Average Interest", f"{avg_interest.max():.1f}", 
                                 f"Highest: {avg_interest.idxmax()}")
                    with col2:
                        recent_interest = google_df[google_df['date'] >= google_df['date'].max() - pd.Timedelta(days=7)]
                        if not recent_interest.empty:
                            recent_avg = recent_interest.groupby('keyword')['interest'].mean().sort_values(ascending=False)
                            st.metric("Recent Trend (7d)", f"{recent_avg.max():.1f}" if not recent_avg.empty else "N/A",
                                     f"Highest: {recent_avg.idxmax()}" if not recent_avg.empty else "")
                except Exception as e:
                    st.warning(f"Could not create Google Trends chart: {str(e)}")
            
            # GitHub repositories
            github_df = df[df["source"] == "GitHub"]
            if not github_df.empty:
                st.markdown("---")
                st.subheader("💻 GitHub Repositories")
                
                # Top repositories by stars
                top_repos = github_df.nlargest(10, 'stars')[['keyword', 'repo', 'stars', 'created', 'url']]
                
                for idx, row in top_repos.iterrows():
                    with st.expander(f"⭐ {row['repo']} ({row['stars']} stars) - {row['keyword']}"):
                        st.write(f"**Created:** {row['created']}")
                        st.write(f"**URL:** {row['url']}")
                
                # Summary by keyword
                github_summary = github_df.groupby('keyword').agg({
                    'stars': 'sum',
                    'repo': 'count'
                }).rename(columns={'repo': 'repositories'}).sort_values('stars', ascending=False)
                
                st.dataframe(github_summary, width='stretch')
            
            # Reddit activity
            reddit_df = df[df["source"] == "Reddit"]
            if not reddit_df.empty:
                st.markdown("---")
                st.subheader("🗞️ Reddit Mentions (Last 90 Days)")
                
                # Count mentions by keyword
                mentions = reddit_df.groupby('keyword').size().reset_index(name='mentions')
                mentions = mentions.sort_values('mentions', ascending=False)
                
                st.bar_chart(mentions.set_index('keyword'))
                
                # Top posts
                top_posts = reddit_df.nlargest(10, 'score')[['keyword', 'title', 'score', 'subreddit', 'created']]
                
                st.markdown("**Top Reddit Posts:**")
                for idx, row in top_posts.iterrows():
                    st.write(f"**{row['title']}** (r/{row['subreddit']}) - {row['score']} upvotes")
                    st.caption(f"Keyword: {row['keyword']} | {row['created'].strftime('%Y-%m-%d') if hasattr(row['created'], 'strftime') else row['created']}")
            
            # Combined summary
            st.markdown("---")
            st.subheader("📊 Trend Summary")
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                total_points = len(df)
                st.metric("Total Data Points", total_points)
            
            with summary_col2:
                sources = df['source'].nunique()
                st.metric("Data Sources", sources)
            
            with summary_col3:
                keywords_tracked = df['keyword'].nunique()
                st.metric("Keywords Tracked", keywords_tracked)
            
            # Export option
            st.markdown("---")
            st.subheader("💾 Export Trend Data")
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f"ventai_trends_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width='stretch'
            )
        
        else:
            # Empty state
            if not run_trend_analysis:
                st.info("👆 Enter keywords above and click 'Run Trend Analysis' to see trend insights.")
            
            # Show analysis summary if available
            if st.session_state.results and st.session_state.analysis_df is not None:
                st.markdown("---")
                st.markdown("### 💡 Tip: Extract Keywords from Your Analysis")
                df = st.session_state.analysis_df
                
                if 'category' in df.columns:
                    top_categories = df['category'].value_counts().head(5)
                    suggested_keywords = ", ".join(top_categories.index.tolist())
                    st.code(f"Suggested keywords: {suggested_keywords}")
                    st.caption("Copy these keywords to analyze trends for your startup categories.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1em;'>"
    "🧠 VentAI – Discover. Analyze. Predict. • "
    "Powered by Ollama (local LLM) + Python Agents"
    "</div>",
    unsafe_allow_html=True
)
