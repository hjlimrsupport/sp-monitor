
import streamlit as st
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import time

# Import refactored modules
import crawler
import monitor
import smart_monitor
import summarizer
import cleanup

# --- Page Configuration ---
st.set_page_config(
    page_title="Splashtop.jp Analyzer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(255, 255, 255) 0%, rgb(240, 245, 255) 90%);
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #0045ff, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .card {
        background-color: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid rgba(0, 69, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 69, 255, 0.3);
    }
    
    .status-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-new { background-color: #e6ffed; color: #22863a; }
    .status-changed { background-color: #fffbdd; color: #735c0f; }
    .status-stable { background-color: #f6f8fa; color: #24292e; }
    .status-deleted { background-color: #ffeef0; color: #cb2431; }
    .status-error { background-color: #fff0f0; color: #d73a49; }
</style>
""", unsafe_allow_html=True)

# --- File Paths ---
STRUCTURE_FILE = Path("site_structure.json")
STATE_FILE = Path("site_state.json")
SUMMARY_FILE = Path("site_summary.json")
REPORT_META_FILE = Path("site_report_meta.json")

def load_json(path):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- Sidebar ---
st.sidebar.title("Splashtop JP 🚀")
st.sidebar.markdown("Web Monitoring Suite")

menu = st.sidebar.selectbox(
    "Navigation",
    ["📊 Dashboard", "🕸️ Crawler", "🔍 Monitor", "🛠️ Tools"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("Service State")
if STRUCTURE_FILE.exists():
    st.sidebar.success(f"Structure: {len(load_json(STRUCTURE_FILE))} URLs")
else:
    st.sidebar.warning("Structure: Missing")

if STATE_FILE.exists():
    st.sidebar.success("State: Available")
else:
    st.sidebar.info("State: Not initialized")

# --- Dashboard ---
if menu == "📊 Dashboard":
    st.markdown('<h1 class="main-header">Insights Dashboard</h1>', unsafe_allow_html=True)
    
    report_meta = load_json(REPORT_META_FILE)
    
    if report_meta:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Monitored", report_meta.get("curr_count", 0), 
                      delta=report_meta.get("curr_count", 0) - report_meta.get("prev_count", 0))
        with c2:
            st.metric("Last Scan", datetime.fromisoformat(report_meta.get("curr_time", "2000-01-01")).strftime("%m/%d %H:%M"))
        with c3:
            st.metric("Structure Total", len(load_json(STRUCTURE_FILE)))

    st.markdown("### 📋 Latest Scan Results")
    summary_data = load_json(SUMMARY_FILE)
    
    if summary_data:
        # Filter for only interesting things by default
        df = pd.DataFrame(summary_data)
        
        status_filter = st.multiselect(
            "Filter Status",
            options=["new", "changed", "stable", "deleted", "error"],
            default=["new", "changed", "deleted", "error"]
        )
        
        filtered_df = df[df["status"].isin(status_filter)] if not df.empty else df
        
        if not filtered_df.empty:
            # Custom display logic
            for _, row in filtered_df.iterrows():
                with st.expander(f"{row['status'].upper()} | {row['title']}", expanded=(row['status'] in ['new', 'changed'])):
                    st.markdown(f"**URL:** [{row['url']}]({row['url']})")
                    st.markdown(f"**Description:** {row['description']}")
                    st.caption(f"Last checked: {row['last_checked']}")
        else:
            st.info("Everything looks stable! Adjust filters to see all pages.")
            
        if st.checkbox("Show full table"):
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found. Please run the Crawler and then the Monitor.")

# --- Crawler ---
elif menu == "🕸️ Crawler":
    st.markdown('<h1 class="main-header">Website Crawler</h1>', unsafe_allow_html=True)
    st.info("Maps the site structure to define the monitoring scope.")
    
    col_l, col_r = st.columns([1, 1])
    with col_l:
        base_url = st.text_input("Start URL", "https://www.splashtop.co.jp/")
        max_depth = st.slider("Crawl Depth", 0, 5, 2)
        
    if st.button("Start Mapping", type="primary", use_container_width=True):
        with st.status("🛠️ Mapping structure...", expanded=True) as s:
            st.write("Initializing...")
            results = crawler.start_crawl(base_url, max_depth)
            s.update(label="✅ Mapping Complete!", state="complete")
        st.balloons()
        st.success(f"Discovered {len(results)} pages.")
        st.rerun()

    if STRUCTURE_FILE.exists():
        st.markdown("### 🗺️ Current Map")
        struct = load_json(STRUCTURE_FILE)
        df_struct = pd.DataFrame(list(struct.items()), columns=["URL", "Depth"])
        st.dataframe(df_struct, use_container_width=True)

# --- Monitor ---
elif menu == "🔍 Monitor":
    st.markdown('<h1 class="main-header">Content Monitor</h1>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="card">
            <h4>Ready to check for updates?</h4>
            <p>The Smart Monitor will analyze dynamic pages (News, Blog, etc.) for any content changes.</p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")
    
    if st.button("🚀 Run Site-wide Check", type="primary", use_container_width=True):
        with st.status("🔍 Checking content hashes...", expanded=True) as s:
            smart_monitor.run_targeted_monitor()
            s.update(label="✅ Monitoring Complete!", state="complete")
        st.success("Analysis report generated.")
        time.sleep(1)
        st.rerun()

    if st.button("🔄 Quick Sync (Metadata Only)"):
        with st.status("Fetching metadata..."):
            summarizer.generate_summary()
        st.success("Metadata synced.")

# --- Tools ---
elif menu == "🛠️ Tools":
    st.markdown('<h1 class="main-header">System Utilities</h1>', unsafe_allow_html=True)
    
    st.markdown("### 🧹 Maintenance")
    if st.button("Normalize & Cleanup JSON Files"):
        cleanup.run_cleanup()
        st.success("Files cleaned and normalized.")

    st.markdown("### 🧨 Risk Zone")
    if st.button("Clear All Data"):
        for f in [STRUCTURE_FILE, STATE_FILE, SUMMARY_FILE, REPORT_META_FILE]:
            if f.exists():
                f.unlink()
        st.warning("All monitoring data has been wiped.")
        st.rerun()

    st.markdown("### ℹ️ About")
    st.write("Built with Streamlit for high-performance web monitoring.")
