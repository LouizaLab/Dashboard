"""
Behavioral Simulation Dashboard (Synthetic Data Demo)

This Streamlit dashboard visualizes the behavioral data engine with:
1. Baseline taste snapshot
2. Behavioral dynamics over time across context + segments
3. Auto-generated insight cards
4. Counterfactual what-if simulation

Data Sources:
- data/products.csv: Product metadata (ingredients, nutrition, price)
- data/segments.csv: User segment definitions
- data/contexts.csv: Context definitions (time, location, occasion)
- data/intent_logs.csv: Historical intent/preference logs
- simulations/intent_trajectories.csv: Phase 3 simulation results
- simulations/phase4_anchored.csv: Phase 4 calibrated results
- phase4_output/signals/*.csv: Generated signals (intent index, momentum, etc.)

Functions Called:
- src.dashboard.data_loader: Loads all CSV data files
- src.dashboard.metrics: Computes taste profiles and behavioral metrics
- src.dashboard.insights: Generates insight cards automatically
- src.dashboard.simulate: Runs counterfactual simulations
- models_phase3.PopulationSimulator: (if available) Full simulation engine
"""

from dashboard.test_hypothesis import render_test_hypothesis_page  # type: ignore
from dashboard.chatbot import DashboardChatbot  # type: ignore
from dashboard.simulate import run_counterfactual_simulation, compare_baseline_vs_counterfactual  # type: ignore
from dashboard.insights import generate_insights  # type: ignore
from dashboard.metrics import (  # type: ignore
    compute_taste_profile,
    compute_behavioral_dynamics,
    compute_segment_context_interaction,
)
from dashboard.data_loader import load_all_data  # type: ignore
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
from pathlib import Path
import networkx as nx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Page config
st.set_page_config(
    page_title="Behavioral Simulation Data",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for black background and Inter font
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global black background with subtle gradient */
    html, body, #root, .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #000000 100%) !important;
        background-color: #000000 !important;
        min-height: 100vh;
    }

    /* Apply Inter font to all elements */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* Smooth transitions for interactive elements */
    * {
        transition: all 0.3s ease !important;
    }

    /* Main background - multiple selectors to catch all */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #000000 !important;
    }

    /* Sidebar background */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div, [data-testid="stSidebar"] * {
        background-color: #0A0A0A !important;
    }

    /* Main content area - all containers with subtle glassmorphism */
    .main .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px !important;
    }

    .main .block-container > div,
    .element-container,
    .element-container > div,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    [data-testid="column"],
    .stColumn,
    div[data-testid="stVerticalBlock"] > div {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* Glassmorphism cards for sections */
    [data-testid="stVerticalBlock"] > div:has(h3),
    .element-container:has(h3) {
        background: rgba(10, 10, 10, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(91, 155, 213, 0.1) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        margin-bottom: 2rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }

    /* Force all divs to be transparent or black */
    div:not([class*="plotly"]):not([class*="js-plotly"]) {
        background-color: transparent !important;
    }

    /* Headers - Better blue shade for all titles */
    h1, h2, h3, h4, h5, h6 {
        color: #5B9BD5 !important;
        font-family: 'Inter', sans-serif !important;
    }

    h1 {
        font-weight: 600 !important;
    }

    h2, h4, h5, h6 {
        font-weight: 600 !important;
        color: #5B9BD5 !important;
    }

    /* Text */
    p, div, span, label, li, td, th {
        color: #E0E0E0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
    }

    [data-testid="stMetricLabel"] {
        color: #B0B0B0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Dataframes - darker grey styling for less contrast */
    .dataframe,
    table,
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] table,
    [data-testid="stDataFrame"] thead,
    [data-testid="stDataFrame"] tbody,
    [data-testid="stDataFrame"] tr,
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] table thead,
    div[data-testid="stDataFrame"] table tbody,
    div[data-testid="stDataFrame"] table tr,
    div[data-testid="stDataFrame"] table td,
    div[data-testid="stDataFrame"] table th {
        background-color: #1A1A1A !important;
        color: #E0E0E0 !important;
        border-color: #2A2A2A !important;
    }

    [data-testid="stDataFrame"] thead th,
    div[data-testid="stDataFrame"] table thead th,
    table thead th {
        background-color: #1F1F1F !important;
        color: #E0E0E0 !important;
        font-weight: 600 !important;
    }

    [data-testid="stDataFrame"] tbody tr:nth-child(even),
    div[data-testid="stDataFrame"] table tbody tr:nth-child(even),
    table tbody tr:nth-child(even) {
        background-color: #1A1A1A !important;
    }

    [data-testid="stDataFrame"] tbody tr:nth-child(odd),
    div[data-testid="stDataFrame"] table tbody tr:nth-child(odd),
    table tbody tr:nth-child(odd) {
        background-color: #151515 !important;
    }

    /* Force override Streamlit's default white background - more aggressive */
    .stDataFrame,
    .stDataFrame > div,
    .stDataFrame table,
    [class*="dataframe"],
    [class*="DataFrame"],
    div[data-testid="stDataFrame"] > div,
    div[data-testid="stDataFrame"] > div > div {
        background-color: #1A1A1A !important;
    }

    /* Target all table cells more aggressively */
    table td, table th,
    .dataframe td, .dataframe th,
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] th {
        background-color: #1A1A1A !important;
        color: #E0E0E0 !important;
    }

    table thead th,
    .dataframe thead th,
    [data-testid="stDataFrame"] thead th {
        background-color: #1F1F1F !important;
        color: #E0E0E0 !important;
    }

    /* Override any inline styles Streamlit might add */
    table[style*="background"],
    td[style*="background"],
    th[style*="background"] {
        background-color: #1A1A1A !important;
    }

    table thead th[style*="background"] {
        background-color: #1F1F1F !important;
    }

    /* Force dark background on all table elements - most aggressive */
    table, table *,
    [data-testid="stDataFrame"], [data-testid="stDataFrame"] *,
    .dataframe, .dataframe * {
        background-color: #1A1A1A !important;
        background: #1A1A1A !important;
    }

    table thead, table thead *,
    [data-testid="stDataFrame"] thead, [data-testid="stDataFrame"] thead * {
        background-color: #1F1F1F !important;
        background: #1F1F1F !important;
    }

    /* Use JavaScript to force styles if CSS doesn't work - will be added after style block */

    /* Add spacing and sectioning */
    .section-spacer {
        margin-top: 3rem;
        margin-bottom: 2rem;
    }

    .section-divider {
        border-top: 1px solid rgba(91, 155, 213, 0.2) !important;
        margin: 3rem 0 !important;
        padding-top: 2rem !important;
        display: block !important;
    }

    /* Minimalistic section headers - ensure blue color with enhanced styling */
    h3 {
        margin-top: 0 !important;
        margin-bottom: 1rem !important;
        font-size: 1.15rem !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        color: #5B9BD5 !important;
        text-shadow: 0 0 20px rgba(91, 155, 213, 0.3) !important;
    }

    /* Insight card titles (h4) - match h3 styling exactly */
    h4 {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        color: #5B9BD5 !important;
    }

    /* All markdown headers in sections use blue */
    .main h3, .main h5, .main h6,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6 {
        color: #5B9BD5 !important;
    }

    /* Ensure insight card h4 titles match section headers exactly */
    [data-testid="stMarkdownContainer"] h4 {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        color: #5B9BD5 !important;
    }

    /* Section descriptions - right under headers with minimal padding */
    h3 + p, h3 + div > p {
        color: #888888 !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
        margin-top: 0 !important;
        margin-bottom: 1.5rem !important;
        padding-top: 0 !important;
        font-weight: 400 !important;
    }

    /* Better spacing for metrics */
    [data-testid="stMetricContainer"] {
        margin-bottom: 1.5rem !important;
    }

    /* Consistent spacing throughout */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Title spacing */
    h1 {
        margin-bottom: 0.75rem !important;
        margin-top: 0 !important;
    }

    /* Subtitle spacing - unbold */
    .main .block-container > div:first-child p,
    .main .block-container p {
        margin-bottom: 1.5rem !important;
        margin-top: 0 !important;
        color: #B0B0B0 !important;
        font-weight: 400 !important;
    }

    /* Better spacing before tabs */
    .stTabs {
        margin-top: 0.5rem !important;
    }

    /* Remove bold from markdown text */
    p strong, p b, markdown strong, markdown b {
        font-weight: 400 !important;
    }

    /* Minimalistic card styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* Buttons - Enhanced 3D style */
    .stButton > button {
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.9) 0%, rgba(10, 10, 10, 0.9) 100%) !important;
        color: #5B9BD5 !important;
        border: 1px solid rgba(91, 155, 213, 0.3) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500;
        border-radius: 8px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
        min-width: 120px !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow:
            0 4px 12px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(91, 155, 213, 0.15) 0%, rgba(91, 155, 213, 0.05) 100%) !important;
        border-color: #5B9BD5 !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow:
            0 8px 24px rgba(91, 155, 213, 0.2),
            0 0 20px rgba(91, 155, 213, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }

    /* Select boxes and inputs */
    .stSelectbox label, .stSlider label, .stTextInput label,
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label {
        color: #E0E0E0 !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Selectbox dropdown */
    [data-baseweb="select"] > div,
    [data-baseweb="popover"] {
        background-color: #1A1A1A !important;
        color: #E0E0E0 !important;
    }

    /* Tabs - Enhanced Menu Style with 3D effect */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(180deg, rgba(10, 10, 10, 0.8) 0%, rgba(0, 0, 0, 0.9) 100%) !important;
        backdrop-filter: blur(10px) !important;
        border-bottom: 1px solid rgba(91, 155, 213, 0.2) !important;
        gap: 0 !important;
        padding: 0.5rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #888888 !important;
        font-family: 'Inter', sans-serif !important;
        background-color: transparent !important;
        border: none !important;
        padding: 14px 28px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #5B9BD5 !important;
        background: rgba(91, 155, 213, 0.05) !important;
        transform: translateY(-2px) !important;
    }

    .stTabs [aria-selected="true"] {
        color: #5B9BD5 !important;
        background: linear-gradient(180deg, rgba(91, 155, 213, 0.1) 0%, transparent 100%) !important;
        border-bottom: 3px solid #5B9BD5 !important;
        font-weight: 600 !important;
        text-shadow: 0 0 10px rgba(91, 155, 213, 0.5) !important;
    }

    .stTabs [data-baseweb="tab-panel"] {
        background-color: transparent !important;
        padding: 2rem 0 !important;
    }

    /* Chat input */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div {
        background-color: #1A1A1A !important;
    }

    /* Cards and containers - make transparent */
    .element-container,
    [data-testid="stVerticalBlock"] > [style*="flex"],
    [data-testid="stHorizontalBlock"] > [style*="flex"] {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* Markdown text */
    .stMarkdown, .stMarkdown * {
        color: #E0E0E0 !important;
    }

    /* Captions - unbold and less glaring */
    .stCaption, .stCaption * {
        color: #888888 !important;
        font-weight: 400 !important;
    }

    /* Info, warning, success boxes */
    [data-testid="stAlert"],
    .stAlert,
    [data-baseweb="notification"] {
        background-color: #1A1A1A !important;
        border-left: 4px solid #00D4FF !important;
        color: #E0E0E0 !important;
    }

    /* Plotly charts - ensure they have dark theme with 3D container effect */
    .js-plotly-plot,
    .plotly,
    [class*="plotly"] {
        background-color: transparent !important;
        border-radius: 16px !important;
    }

    /* Network graph container with 3D effect */
    [data-testid="stVerticalBlock"]:has([class*="plotly"]) {
        background: linear-gradient(135deg, rgba(10, 10, 10, 0.6) 0%, rgba(0, 0, 0, 0.8) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(91, 155, 213, 0.15) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        margin: 2rem 0 !important;
        box-shadow:
            0 20px 60px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(91, 155, 213, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    }

    /* Enhanced plotly container */
    div[data-testid="stPlotlyChart"] {
        background: transparent !important;
        padding: 1rem !important;
        border-radius: 12px !important;
    }

    /* Remove any white backgrounds from Streamlit widgets */
    [data-baseweb="base-input"],
    [data-baseweb="input"],
    [data-baseweb="slider"] {
        background-color: #1A1A1A !important;
    }

    /* Multi-select pills */
    [data-baseweb="tag"] {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border-color: #333333 !important;
    }

    /* Hide tooltips - but NOT selectbox dropdown menus */
    [data-baseweb="tooltip"],
    [role="tooltip"],
    .stTooltip,
    [class*="tooltip"],
    [data-testid="stTooltip"],
    div[data-baseweb="tooltip"],
    div[role="tooltip"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        position: absolute !important;
        left: -9999px !important;
    }

    /* Ensure selectbox dropdown menus are ALWAYS visible and functional */
    [data-baseweb="select"] [data-baseweb="popover"],
    [data-baseweb="popover"] [data-baseweb="menu"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        position: relative !important;
        left: auto !important;
        z-index: 9999 !important;
    }

    /* Hide title attributes tooltips */
    [title]:hover::after,
    [title]:hover::before,
    [title]::after,
    [title]::before {
        display: none !important;
        content: none !important;
    }

    /* Prevent tooltips from showing on hover - but NOT selectbox dropdowns */
    *:hover [data-baseweb="tooltip"],
    *:hover [role="tooltip"],
    *:hover .stTooltip,
    [data-baseweb="base-input"]:hover [data-baseweb="tooltip"],
    button:hover [data-baseweb="tooltip"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Remove title attribute tooltips completely */
    [title] {
        position: relative;
    }

    /* Hide Streamlit's help icon tooltips */
    [data-testid="stHelpIcon"],
    [data-testid="stHelpIcon"] + * {
        display: none !important;
    }

    /* Hide Streamlit menu and keyboard shortcut indicators - be very specific */
    /* Only target the actual Streamlit header menu, not user buttons */
    [data-testid="stHeader"] > div > div > button[aria-label*="Menu"],
    [data-testid="stHeader"] > div > div > button[title*="Menu"],
    [data-testid="stHeader"] > div > div > button[aria-label*="keyboard"],
    [data-testid="stHeader"] > div > div > button[title*="keyboard"] {
        display: none !important;
    }

    /* Ensure our Controls button is always visible */
    button[key="show_sidebar_main"],
    button[key="sidebar_toggle"] {
        display: block !important;
        visibility: visible !important;
    }

    /* Sidebar toggle functionality */
    .hide-sidebar [data-testid="stSidebar"] {
        display: none !important;
    }

    .hide-sidebar [data-testid="stSidebar"] ~ * {
        margin-left: 0 !important;
    }
    </style>
    <script>
    // Force dark background on tables - runs multiple times to catch all tables
    function styleAllTables() {
        const tables = document.querySelectorAll('table, [data-testid="stDataFrame"] table');
        tables.forEach(function(table) {
            if (table) {
                table.style.backgroundColor = '#1A1A1A';
                table.style.background = '#1A1A1A';
                const allCells = table.querySelectorAll('td, th');
                allCells.forEach(function(cell) {
                    cell.style.setProperty('background-color', '#1A1A1A', 'important');
                    cell.style.setProperty('background', '#1A1A1A', 'important');
                    cell.style.setProperty('color', '#E0E0E0', 'important');
                });
                const headers = table.querySelectorAll('thead th');
                headers.forEach(function(header) {
                    header.style.setProperty('background-color', '#1F1F1F', 'important');
                    header.style.setProperty('background', '#1F1F1F', 'important');
                    header.style.setProperty('color', '#E0E0E0', 'important');
                });
            }
        });
    }
    // Run immediately and on intervals
    styleAllTables();
    setTimeout(styleAllTables, 100);
    setTimeout(styleAllTables, 500);
    setTimeout(styleAllTables, 1000);
    // Also run when DOM changes
    const observer = new MutationObserver(styleAllTables);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """,
    unsafe_allow_html=True,
)

# Dark theme template for Plotly charts
dark_theme = {
    "layout": {
        "paper_bgcolor": "#000000",
        "plot_bgcolor": "#000000",
        "font": {"color": "#E0E0E0", "family": "Inter, sans-serif"},
        "title": {"font": {"color": "#FFFFFF", "family": "Inter, sans-serif"}},
        "xaxis": {
            "gridcolor": "#333333",
            "linecolor": "#666666",
            "zerolinecolor": "#333333",
            "title": {"font": {"color": "#E0E0E0", "family": "Inter, sans-serif"}},
            "tickfont": {"color": "#B0B0B0", "family": "Inter, sans-serif"},
        },
        "yaxis": {
            "gridcolor": "#333333",
            "linecolor": "#666666",
            "zerolinecolor": "#333333",
            "title": {"font": {"color": "#E0E0E0", "family": "Inter, sans-serif"}},
            "tickfont": {"color": "#B0B0B0", "family": "Inter, sans-serif"},
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#E0E0E0", "family": "Inter, sans-serif"},
            "bordercolor": "#333333",
        },
        "polar": {
            "bgcolor": "#000000",
            "radialaxis": {
                "gridcolor": "#333333",
                "linecolor": "#666666",
                "tickfont": {
                    "color": "#B0B0B0",
                    "family": "Inter, sans-serif",
                },
            },
            "angularaxis": {
                "gridcolor": "#333333",
                "linecolor": "#666666",
                "tickfont": {
                    "color": "#B0B0B0",
                    "family": "Inter, sans-serif",
                },
            },
        },
    }
}


def create_network_graph():
    """Create an interactive 3D network graph of fast food restaurants"""
    # Fast food restaurants
    restaurants = [
        "McDonald's",
        "Burger King",
        "Wendy's",
        "Taco Bell",
        "KFC",
        "Subway",
        "Pizza Hut",
        "Domino's",
        "Chipotle",
        "Starbucks",
        "Dunkin'",
        "Papa John's",
        "Arby's",
        "Jack in the Box",
        "Sonic",
    ]

    # Create network graph
    G = nx.Graph()

    # Add nodes
    for restaurant in restaurants:
        G.add_node(restaurant)

    # Add edges based on similarity (price range, cuisine type, market segment)
    # Fast food burger chains
    burger_chains = [
        "McDonald's",
        "Burger King",
        "Wendy's",
        "Jack in the Box",
        "Sonic",
    ]
    for i, r1 in enumerate(burger_chains):
        for r2 in burger_chains[i + 1 :]:
            G.add_edge(r1, r2, weight=0.8)

    # Pizza chains
    pizza_chains = ["Pizza Hut", "Domino's", "Papa John's"]
    for i, r1 in enumerate(pizza_chains):
        for r2 in pizza_chains[i + 1 :]:
            G.add_edge(r1, r2, weight=0.9)

    # Mexican fast food
    G.add_edge("Taco Bell", "Chipotle", weight=0.7)

    # Coffee chains
    G.add_edge("Starbucks", "Dunkin'", weight=0.8)

    # Cross-category connections (weaker)
    G.add_edge("McDonald's", "Taco Bell", weight=0.4)
    G.add_edge("Burger King", "KFC", weight=0.5)
    G.add_edge("Subway", "Pizza Hut", weight=0.3)
    G.add_edge("Chipotle", "Starbucks", weight=0.3)
    G.add_edge("Taco Bell", "KFC", weight=0.4)
    G.add_edge("McDonald's", "Starbucks", weight=0.3)
    G.add_edge("Subway", "Chipotle", weight=0.3)

    # Use 3D spring layout for positioning with more spacing
    pos = nx.spring_layout(G, k=4.0, iterations=150, seed=42, dim=3)

    # Extract node positions (x, y, z)
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_z = [pos[node][2] for node in G.nodes()]

    # Create edge traces in 3D
    edge_traces = []
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        weight = G[edge[0]][edge[1]].get("weight", 0.5)
        edge_traces.append(
            go.Scatter3d(
                x=[x0, x1, None],
                y=[y0, y1, None],
                z=[z0, z1, None],
                mode="lines",
                line=dict(
                    width=weight * 4 + 1,
                    color=f"rgba(91, 155, 213, {0.2 + weight*0.3})",
                ),
                hoverinfo="none",
                showlegend=False,
            )
        )
        # Add glow effect
        edge_traces.append(
            go.Scatter3d(
                x=[x0, x1, None],
                y=[y0, y1, None],
                z=[z0, z1, None],
                mode="lines",
                line=dict(
                    width=weight * 6 + 3,
                    color=f"rgba(91, 155, 213, {0.08 + weight*0.12})",
                ),
                hoverinfo="none",
                showlegend=False,
            )
        )

    # Create node trace in 3D without labels
    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode="markers",
        hovertext=[f"<b>{node}</b><br>Drag to rotate, scroll to zoom" for node in G.nodes()],
        hoverinfo="text",
        marker=dict(
            size=12,
            color="#5B9BD5",
            line=dict(width=2, color="rgba(255, 255, 255, 0.8)"),
            showscale=False,
            opacity=0.95,
        ),
        showlegend=False,
    )

    # Create 3D figure
    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title="",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=0),
            scene=dict(
                xaxis=dict(
                    showgrid=False,
                    showbackground=False,
                    zeroline=False,
                    showticklabels=False,
                    showaxeslabels=False,
                    range=[-2.5, 2.5],
                ),
                yaxis=dict(
                    showgrid=False,
                    showbackground=False,
                    zeroline=False,
                    showticklabels=False,
                    showaxeslabels=False,
                    range=[-2.5, 2.5],
                ),
                zaxis=dict(
                    showgrid=False,
                    showbackground=False,
                    zeroline=False,
                    showticklabels=False,
                    showaxeslabels=False,
                    range=[-2.5, 2.5],
                ),
                bgcolor="rgba(0,0,0,0)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1),
                ),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", family="Inter, sans-serif"),
            height=750,
        ),
    )

    return fig


def apply_dark_theme(fig):
    """Apply dark theme to a Plotly figure"""
    # Base layout updates
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#E0E0E0", family="Inter, sans-serif"),
        title=dict(font=dict(color="#FFFFFF", family="Inter, sans-serif")),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", family="Inter, sans-serif"),
            bordercolor="#333333",
        ),
    )

    # Update all xaxes (for subplots)
    for axis_name in fig.layout:
        if axis_name.startswith("xaxis"):
            fig.update_layout(
                {
                    axis_name: dict(
                        gridcolor="#333333",
                        linecolor="#666666",
                        zerolinecolor="#333333",
                        title=dict(font=dict(color="#E0E0E0", family="Inter, sans-serif")),
                        tickfont=dict(color="#B0B0B0", family="Inter, sans-serif"),
                    )
                }
            )
        elif axis_name.startswith("yaxis"):
            fig.update_layout(
                {
                    axis_name: dict(
                        gridcolor="#333333",
                        linecolor="#666666",
                        zerolinecolor="#333333",
                        title=dict(font=dict(color="#E0E0E0", family="Inter, sans-serif")),
                        tickfont=dict(color="#B0B0B0", family="Inter, sans-serif"),
                    )
                }
            )

    # Update annotations (subplot titles)
    if hasattr(fig.layout, "annotations") and fig.layout.annotations:
        for annotation in fig.layout.annotations:
            annotation.font.color = "#FFFFFF"
            annotation.font.family = "Inter, sans-serif"

    # Update polar charts if they exist
    if hasattr(fig.layout, "polar"):
        fig.update_layout(
            polar=dict(
                bgcolor="#000000",
                radialaxis=dict(
                    gridcolor="#333333",
                    linecolor="#666666",
                    tickfont=dict(color="#B0B0B0", family="Inter, sans-serif"),
                ),
                angularaxis=dict(
                    gridcolor="#333333",
                    linecolor="#666666",
                    tickfont=dict(color="#B0B0B0", family="Inter, sans-serif"),
                ),
            )
        )
    return fig


# Initialize session state for chatbot
if "chatbot" not in st.session_state:
    st.session_state["chatbot"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


# Cache data loading
@st.cache_data
def load_cached_data():
    """Load and cache all data"""
    return load_all_data()


# Cache simulation results
@st.cache_data
def cache_simulation(base_traj, price_mult, sugar_adj, marketing_exp):
    """Cache simulation results"""
    return run_counterfactual_simulation(
        base_traj,
        price_multiplier=price_mult,
        sugar_adjustment=sugar_adj,
        marketing_exposure=marketing_exp,
    )


# Load data
data = load_cached_data()

# Initialize sidebar visibility state FIRST - default to hidden
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = False

# Header at the top
col_title1, col_title2 = st.columns([17, 3])
with col_title1:
    st.empty()

# Sidebar toggle button in header
with col_title2:
    if not st.session_state.sidebar_visible:
        st.markdown("<br>", unsafe_allow_html=True)  # Align with title
        btn_clicked = st.button("☰ Controls", key="show_sidebar_main", use_container_width=True)
        if btn_clicked:
            st.session_state.sidebar_visible = True
            st.rerun()

# Add CSS to hide/show sidebar based on state
# Only apply hiding CSS when sidebar should be hidden
if not st.session_state.sidebar_visible:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebar"] ~ * {
            margin-left: 0 !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

# Sidebar
with st.sidebar:
    # Toggle button at the top
    toggle_text = "Hide Controls" if st.session_state.sidebar_visible else "Show Controls"
    if st.button(toggle_text, key="sidebar_toggle", use_container_width=True):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible
        st.rerun()

    if st.session_state.sidebar_visible:
        st.header("Controls")

# Create ID to name mappings - use psychographic as primary name
segment_id_to_name = {}
if not data["segments"].empty:
    for _, row in data["segments"].iterrows():
        # Use psychographic as the display name, with age/region as additional info
        psychographic = row.get("psychographic", "unknown")
        age_bucket = row.get("age_bucket", "")
        region = row.get("region", "")
        # Format: "psychographic (age, region)" or just "psychographic"
        if age_bucket and region:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket}, {region})"
        elif age_bucket:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket})"
        else:
            display_name = psychographic.title().replace("_", " ")
        segment_id_to_name[row["segment_id"]] = display_name

context_id_to_name = {}
if not data["contexts"].empty:
    for _, row in data["contexts"].iterrows():
        # Create readable context name from attributes
        context_name = f"{row.get('time_of_day', 'unknown').title()} - {row.get('location', 'unknown').title()} - {row.get('occasion', 'unknown').title()}"
        context_id_to_name[row["context_id"]] = context_name

# Segment selector - show names but use IDs internally
if not data["segments"].empty:
    # Create options with names as labels - use psychographic as primary
    segment_options = {}
    for _, row in data["segments"].iterrows():
        seg_id = row["segment_id"]
        psychographic = row.get("psychographic", "unknown")
        age_bucket = row.get("age_bucket", "")
        region = row.get("region", "")
        # Format: "psychographic (age, region)" or just "psychographic"
        if age_bucket and region:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket}, {region})"
        elif age_bucket:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket})"
        else:
            display_name = psychographic.title().replace("_", " ")
        segment_options[display_name] = seg_id

    if st.session_state.sidebar_visible:
        selected_segment_names = st.sidebar.multiselect(
            "Select Segments",
            options=list(segment_options.keys()),
            default=list(segment_options.keys())[: min(3, len(segment_options))],
        )
        # Convert selected names back to IDs
        selected_segments = [segment_options[name] for name in selected_segment_names]
    else:
        # Use defaults when sidebar is hidden
        selected_segments = list(segment_options.values())[: min(3, len(segment_options))]
else:
    selected_segments = []
    if st.session_state.sidebar_visible:
        st.sidebar.warning("No segment data available")
# Context selector - show names but use IDs internally
if not data["contexts"].empty:
    # Create options with names as labels
    context_options = {}
    for _, row in data["contexts"].iterrows():
        ctx_id = row["context_id"]
        ctx_name = context_id_to_name.get(ctx_id, ctx_id)
        context_options[ctx_name] = ctx_id

    if st.session_state.sidebar_visible:
        selected_context_names = st.sidebar.multiselect(
            "Select Contexts",
            options=list(context_options.keys()),
            default=list(context_options.keys())[: min(5, len(context_options))],
        )
        # Convert selected names back to IDs
        selected_contexts = [context_options[name] for name in selected_context_names]
    else:
        # Use defaults when sidebar is hidden
        selected_contexts = list(context_options.values())[: min(5, len(context_options))]
else:
    selected_contexts = []
    if st.session_state.sidebar_visible:
        st.sidebar.warning("No context data available")
# Time range
if st.session_state.sidebar_visible:
    time_range = st.sidebar.slider(
        "Time Range (days)", min_value=0, max_value=90, value=(0, 30), step=1
    )
else:
    time_range = (0, 30)  # Default when sidebar is hidden

# Scenario selector (placeholder)
if st.session_state.sidebar_visible:
    scenario = st.sidebar.selectbox(
        "Scenario", options=["Baseline", "Optimistic", "Pessimistic"], index=0
    )
else:
    scenario = "Baseline"  # Default when sidebar is hidden

if st.session_state.sidebar_visible:
    st.sidebar.markdown("---")
    st.sidebar.header("What-If Simulation")

    # What-if controls
    price_multiplier = st.sidebar.slider(
        "Price Multiplier",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="1.0 = baseline, 1.1 = +10% price",
    )

    sugar_adjustment = st.sidebar.slider(
        "Sugar Adjustment (g)",
        min_value=-20.0,
        max_value=20.0,
        value=0.0,
        step=1.0,
        help="Additive adjustment to sugar content",
    )

    marketing_exposure = st.sidebar.slider(
        "Marketing Exposure Multiplier",
        min_value=0.0,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help="1.0 = baseline, 2.0 = 2x marketing exposure",
    )
else:
    # Defaults when sidebar is hidden
    price_multiplier = 1.0
    sugar_adjustment = 0.0
    marketing_exposure = 1.0

if st.session_state.sidebar_visible:
    st.sidebar.markdown("---")
    st.sidebar.header("Chat with AI")
    st.sidebar.markdown("Ask questions about insights and data")

# Store mappings in session state for chatbot
if "segment_id_to_name" not in st.session_state:
    st.session_state["segment_id_to_name"] = segment_id_to_name
if "context_id_to_name" not in st.session_state:
    st.session_state["context_id_to_name"] = context_id_to_name

# Initialize chatbot if not already done
if st.session_state.get("chatbot") is None:
    try:
        # Generate insights for chatbot context
        insights_list = []
        if selected_segments and not data["trajectories"].empty:
            insights_list = generate_insights(
                data["trajectories"],
                data["intent_logs"],
                data["intent_index"],
                data["momentum"],
                selected_segments,
                selected_contexts,
                time_range,
            )

        st.session_state["chatbot"] = DashboardChatbot(
            data=data,
            insights=insights_list,
            use_openai=True,
            model="gpt-4o-mini",
        )
    except Exception as e:
        st.sidebar.warning(f"Chatbot init: {str(e)}")

# Chat interface
if st.session_state.sidebar_visible:
    chatbot = st.session_state.get("chatbot")
    if chatbot:
        # Display chat history
        chat_history = st.session_state.get("chat_history", [])
        for message in chat_history[-10:]:  # Show last 10 messages
            with st.sidebar.chat_message(message["role"]):
                st.markdown(message["content"])

        # Suggested questions
        with st.sidebar.expander("Suggested Questions"):
            suggested = chatbot.get_suggested_questions()
            for q in suggested[:5]:
                if st.button(q, key=f"suggest_{hash(q)}", use_container_width=True):
                    response = chatbot.chat(q)
                    st.session_state["chat_history"] = st.session_state.get("chat_history", [])
                    st.session_state["chat_history"].append({"role": "user", "content": q})
                    st.session_state["chat_history"].append(
                        {"role": "assistant", "content": response}
                    )
                    st.rerun()

        # User input
        user_input = st.sidebar.chat_input("Ask about insights...")
        if user_input:
            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = []
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            with st.sidebar.spinner("Thinking..."):
                response = chatbot.chat(user_input)
                st.session_state["chat_history"].append({"role": "assistant", "content": response})
            st.rerun()

        # Reset button
        if st.sidebar.button("Reset Conversation"):
            chatbot.reset_conversation()
            st.session_state["chat_history"] = []
            st.rerun()
else:
    st.sidebar.info(
        "Chatbot will be available after data loads. Set OPENAI_API_KEY environment variable to enable."
    )

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.sidebar.warning(
            "No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        )

# Main content tabs
tab_louiza, tab0, tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Test Hypothesis",
        "Network Graph",
        "Taste Snapshot",
        "Behavioral Dynamics",
        "Insights",
        "What-If Simulation",
    ]
)

# Panel: Test Hypothesis
with tab_louiza:
    render_test_hypothesis_page()

# Panel: Network Graph
with tab0:
    st.markdown("### Network Graph")
    st.markdown(
        "Interactive network visualization showing connections between fast food restaurants based on similarity in price, cuisine type, and market segment. Click and drag nodes to explore connections."
    )

    # Create and display network graph
    network_fig = create_network_graph()
    st.plotly_chart(
        network_fig,
        use_container_width=True,
        key="network_graph_tab0",
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "network_graph",
                "height": 750,
                "width": 1400,
                "scale": 2,
            },
        },
    )

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # Add information about edges with enhanced styling
    st.markdown(
        """
        <div style="
        background: rgba(10, 10, 10, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(91, 155, 213, 0.1);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        ">
    """,
        unsafe_allow_html=True,
    )

    st.markdown("### About the Connections")
    st.markdown(
        """
        **Edge weights** represent similarity between restaurants:
        - **Strong connections (thick lines)**: Similar cuisine type and market positioning
        - **Medium connections**: Related categories or overlapping customer bases
        - **Weak connections (thin lines)**: Cross-category relationships

        **Node interactions**:
        - Click on a node to see its connections highlighted
        - Pan and zoom to explore the network
        - Hover over nodes to see restaurant names
    """
    )

    st.markdown("</div>", unsafe_allow_html=True)

# Panel A: Taste Snapshot
with tab1:
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Compute taste profile
        taste_profile = compute_taste_profile(
            data["products"],
            data["segments"],
            data["intent_logs"],
            selected_segments,
        )

        if not taste_profile.empty:
            # Section 1: Overview Metrics - Clean and minimal
            st.markdown("### Overview")
            st.markdown(
                "Average intent values showing how much each segment is engaging with coffee, sugar, and price, and to what level of engagement they have (0 = low, 1 = high engagement)."
            )
            metrics_cols = st.columns(len(taste_profile))
            for idx, (_, row) in enumerate(taste_profile.iterrows()):
                with metrics_cols[idx]:
                    seg_id = row["segment_id"]
                    seg_name = segment_id_to_name.get(seg_id, seg_id)
                    st.metric(
                        label=seg_name.split("(")[0].strip(),
                        value=f"{row['avg_intent']:.3f}",
                    )

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # Section 2: Visualization
            st.markdown("### Visualization")
            st.markdown(
                "Radar chart showing how different user segments respond to sugar preference, caffeine tolerance, price sensitivity, and average intent."
            )

            # Normalize metrics for radar chart
            metrics_to_plot = [
                "avg_intent",
                "sugar_preference",
                "caffeine_tolerance",
                "price_sensitivity",
            ]
            available_metrics = [m for m in metrics_to_plot if m in taste_profile.columns]

            if available_metrics and len(available_metrics) >= 2:
                # Create radar chart
                fig = go.Figure()

                for _, row in taste_profile.iterrows():
                    values = [row[m] for m in available_metrics]
                    # Normalize to 0-1 scale for visualization
                    max_vals = taste_profile[available_metrics].max()
                    min_vals = taste_profile[available_metrics].min()
                    normalized = []
                    for m, v in zip(available_metrics, values):
                        if max_vals[m] - min_vals[m] > 1e-6:
                            norm_val = (v - min_vals[m]) / (max_vals[m] - min_vals[m])
                        else:
                            norm_val = 0.5
                        normalized.append(norm_val)

                    seg_id = row["segment_id"]
                    seg_name = segment_id_to_name.get(seg_id, seg_id)
                    fig.add_trace(
                        go.Scatterpolar(
                            r=normalized + [normalized[0]],  # Close the loop
                            theta=available_metrics + [available_metrics[0]],
                            fill="toself",
                            name=seg_name,
                        )
                    )

                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=True,
                    title="",
                    height=500,
                )
                fig = apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True, key="taste_profile_chart")
            else:
                # Fallback to bar chart
                if "avg_intent" in taste_profile.columns:
                    # Create display version with segment names
                    taste_profile_display = taste_profile.copy()
                    taste_profile_display["segment_name"] = taste_profile_display["segment_id"].map(
                        segment_id_to_name
                    )
                    fig = px.bar(
                        taste_profile_display,
                        x="segment_name",
                        y="avg_intent",
                        title="",
                    )
                fig = apply_dark_theme(fig)
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="taste_profile_bar_chart",
                )

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # Section 3: Detailed Data Table
            st.markdown("### Detailed Data")
            # Replace segment_id with segment_name for display
            taste_profile_display = taste_profile.copy()
            taste_profile_display["segment_name"] = taste_profile_display["segment_id"].map(
                segment_id_to_name
            )
            # Reorder columns to show name first
            cols = ["segment_name", "segment_id"] + [
                c for c in taste_profile_display.columns if c not in ["segment_name", "segment_id"]
            ]
            taste_profile_display = taste_profile_display[
                [c for c in cols if c in taste_profile_display.columns]
            ]
            st.dataframe(taste_profile_display, use_container_width=True, height=300)
        else:
            st.warning("No taste profile data available for selected segments")

# Panel B: Behavioral Dynamics
with tab2:
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Use Phase 4 anchored data if available, otherwise trajectories
        trajectories = (
            data["phase4_anchored"] if not data["phase4_anchored"].empty else data["trajectories"]
        )

        if trajectories.empty:
            st.warning("No trajectory data available")
        else:
            # Compute behavioral dynamics
            dynamics = compute_behavioral_dynamics(
                trajectories, selected_segments, selected_contexts, time_range
            )

            if not dynamics.empty:
                # Time series plots
                time_col = "time_step" if "time_step" in dynamics.columns else "date"

                st.markdown("### Purchase Probability")
                st.markdown("Purchase probability trends over time for selected segments.")
                # Purchase probability
                fig1 = px.line(
                    dynamics,
                    x=time_col,
                    y="purchase_probability",
                    title="",
                    labels={
                        "purchase_probability": "Purchase Probability",
                        time_col: "Time",
                    },
                )
                fig1 = apply_dark_theme(fig1)
                st.plotly_chart(
                    fig1,
                    use_container_width=True,
                    key="purchase_probability_chart",
                )

                st.markdown(
                    "<div class='section-divider'></div>",
                    unsafe_allow_html=True,
                )

                st.markdown("### Behavioral Metrics")
                st.markdown(
                    "Key behavioral indicators including repeat rate, churn rate, adoption rate, and intent value over time."
                )

                # Multiple metrics subplot
                fig2 = make_subplots(
                    rows=2,
                    cols=2,
                    subplot_titles=(
                        "Repeat Rate",
                        "Churn Rate",
                        "Adoption Rate",
                        "Intent Value",
                    ),
                    vertical_spacing=0.1,
                )

                fig2.add_trace(
                    go.Scatter(
                        x=dynamics[time_col],
                        y=dynamics["repeat_rate"],
                        name="Repeat Rate",
                    ),
                    row=1,
                    col=1,
                )
                fig2.add_trace(
                    go.Scatter(
                        x=dynamics[time_col],
                        y=dynamics["churn_rate"],
                        name="Churn Rate",
                    ),
                    row=1,
                    col=2,
                )
                fig2.add_trace(
                    go.Scatter(
                        x=dynamics[time_col],
                        y=dynamics["adoption_rate"],
                        name="Adoption Rate",
                    ),
                    row=2,
                    col=1,
                )
                fig2.add_trace(
                    go.Scatter(
                        x=dynamics[time_col],
                        y=dynamics["purchase_probability"],
                        name="Intent",
                    ),
                    row=2,
                    col=2,
                )

                fig2.update_layout(height=600, showlegend=False, title_text="")
                fig2 = apply_dark_theme(fig2)
                st.plotly_chart(
                    fig2,
                    use_container_width=True,
                    key="behavioral_metrics_chart",
                )

                st.markdown(
                    "<div class='section-divider'></div>",
                    unsafe_allow_html=True,
                )

                # Segment-context interaction
                st.markdown("### Segment-Context Interaction")
                st.markdown(
                    "Heatmap showing how different segments respond across various contexts."
                )
                interaction = compute_segment_context_interaction(
                    data["intent_logs"], trajectories, selected_segments
                )

                if not interaction.empty:
                    interaction_pivot = interaction.pivot(
                        index="segment_id",
                        columns="context_id",
                        values="intent_value",
                    )

                    fig3 = px.imshow(
                        interaction_pivot,
                        labels=dict(x="Context", y="Segment", color="Intent"),
                        title="Segment-Context Interaction Heatmap",
                    )
                    fig3 = apply_dark_theme(fig3)
                    st.plotly_chart(
                        fig3,
                        use_container_width=True,
                        key="segment_context_heatmap",
                    )
            else:
                st.warning("No dynamics data computed for selected filters")

# Panel C: Insights
with tab3:
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Generate insights
        insights = generate_insights(
            data["trajectories"],
            data["intent_logs"],
            data["intent_index"],
            data["momentum"],
            selected_segments,
            selected_contexts,
            time_range,
        )

        if insights:
            st.markdown("### Key Insights")
            st.markdown(
                "Automatically generated insights based on behavioral data and intent patterns."
            )

            # Display insight cards
            cols = st.columns(2)

            for idx, insight in enumerate(insights):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"#### {insight['title']}")
                        st.metric(label="Value", value=insight["value"])
                        # Replace segment/context IDs with names in description
                        description = insight["description"]
                        if "segment" in insight:
                            seg_id = insight["segment"]
                            seg_name = segment_id_to_name.get(seg_id, seg_id)
                            description = description.replace(seg_id, seg_name)
                        st.caption(description)
                        st.markdown("---")

            # Evidence chart for top insight
            if len(insights) > 0:
                top_insight = insights[0]
                st.subheader(f"Evidence: {top_insight['title']}")

                # Create evidence chart based on insight type
                if top_insight["type"] == "delta" and not data["intent_index"].empty:
                    intent_data = data["intent_index"]
                    # Handle both 'category' and 'product_category' column names
                    cat_col = (
                        "product_category"
                        if "product_category" in intent_data.columns
                        else "category"
                    )
                    if cat_col in intent_data.columns and top_insight.get("category"):
                        cat_data = intent_data[intent_data[cat_col] == top_insight["category"]]
                        if not cat_data.empty:
                            fig = px.line(
                                cat_data,
                                x="date",
                                y="intent_mean",
                                title=f"{top_insight['category']} Intent Over Time",
                            )
                            fig = apply_dark_theme(fig)
                            st.plotly_chart(
                                fig,
                                use_container_width=True,
                                key="insight_evidence_chart",
                            )
        else:
            st.info("No insights generated. Try adjusting filters or ensure data is available.")

# Panel D: What-If Simulation
with tab4:
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Get baseline trajectories
        baseline = (
            data["phase4_anchored"] if not data["phase4_anchored"].empty else data["trajectories"]
        )

        if baseline.empty:
            st.warning("No baseline trajectory data available")
        else:
            # Filter baseline
            baseline_filtered = baseline[baseline["segment_id"].isin(selected_segments)].copy()

            if baseline_filtered.empty:
                st.warning("No data for selected segments")
            else:
                st.markdown("### Simulation Results")
                st.markdown(
                    "Compare baseline behavior with counterfactual scenarios based on price, sugar, and marketing adjustments."
                )

                # Run counterfactual simulation
                with st.spinner("Running counterfactual simulation..."):
                    counterfactual = cache_simulation(
                        baseline_filtered,
                        price_multiplier,
                        sugar_adjustment,
                        marketing_exposure,
                    )

                # Compare baseline vs counterfactual
                comparison = compare_baseline_vs_counterfactual(baseline_filtered, counterfactual)

                if comparison:
                    st.markdown(
                        "<div class='section-divider'></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("### Comparison Metrics")
                    # Display comparison metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "Baseline Avg Intent",
                            f"{comparison['baseline']['avg_intent']:.3f}",
                        )

                    with col2:
                        st.metric(
                            "Counterfactual Avg Intent",
                            f"{comparison['counterfactual']['avg_intent']:.3f}",
                            delta=f"{comparison['deltas']['intent_delta']:+.3f}",
                        )

                    with col3:
                        st.metric(
                            "Intent Change %",
                            f"{comparison['deltas']['intent_delta_pct']:+.2f}%",
                        )

                    with col4:
                        st.metric(
                            "Total Interactions",
                            f"{comparison['counterfactual']['total_interactions']}",
                            delta=f"{comparison['deltas']['interactions_delta']:+d}",
                        )

                    st.markdown(
                        "<div class='section-divider'></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("### Baseline vs Counterfactual")

                    time_col = "time_step" if "time_step" in baseline_filtered.columns else "date"

                    if time_col in baseline_filtered.columns and time_col in counterfactual.columns:
                        baseline_ts = baseline_filtered.groupby(time_col)["intent_value"].mean()
                        cf_ts = counterfactual.groupby(time_col)["intent_value"].mean()

                        fig = go.Figure()

                        fig.add_trace(
                            go.Scatter(
                                x=baseline_ts.index,
                                y=baseline_ts.values,
                                mode="lines",
                                name="Baseline",
                                line=dict(color="blue", width=2),
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=cf_ts.index,
                                y=cf_ts.values,
                                mode="lines",
                                name="Counterfactual",
                                line=dict(color="red", width=2, dash="dash"),
                            )
                        )

                        fig.update_layout(
                            title="Intent Over Time: Baseline vs Counterfactual",
                            xaxis_title=time_col,
                            yaxis_title="Intent Value",
                            hovermode="x unified",
                        )
                        fig = apply_dark_theme(fig)

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            key="whatif_timeseries_chart",
                        )
                    else:
                        st.info("Time column not available for time series visualization")

                    st.markdown(
                        "<div class='section-divider'></div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("### Delta Summary")
                    delta_df = pd.DataFrame(
                        {
                            "Metric": [
                                "Intent Delta",
                                "Intent Delta %",
                                "Interactions Delta",
                                "Interactions Delta %",
                            ],
                            "Value": [
                                f"{comparison['deltas']['intent_delta']:+.3f}",
                                f"{comparison['deltas']['intent_delta_pct']:+.2f}%",
                                f"{comparison['deltas']['interactions_delta']:+d}",
                                f"{comparison['deltas']['interactions_delta_pct']:+.2f}%",
                            ],
                        }
                    )
                    st.dataframe(delta_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption("Behavioral Simulation Data - Synthetic Data Demo | Built with Streamlit")
