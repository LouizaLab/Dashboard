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

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dashboard.data_loader import load_all_data, DATA_DIR
from dashboard.metrics import (
    compute_taste_profile,
    compute_behavioral_dynamics,
    compute_segment_context_interaction
)
from dashboard.insights import generate_insights
from dashboard.simulate import run_counterfactual_simulation, compare_baseline_vs_counterfactual
from dashboard.chatbot import DashboardChatbot

# Page config
st.set_page_config(
    page_title="Behavioral Simulation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for chatbot
if 'chatbot' not in st.session_state:
    st.session_state['chatbot'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

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
        marketing_exposure=marketing_exp
    )

# Load data
data = load_cached_data()

# Header
st.title("📊 Behavioral Simulation Dashboard")
st.markdown("**Synthetic Data Demo** - Visualizing behavioral intent modeling across segments, contexts, and time")

# Sidebar
st.sidebar.header("Controls")

# Create ID to name mappings - use psychographic as primary name
segment_id_to_name = {}
if not data['segments'].empty:
    for _, row in data['segments'].iterrows():
        # Use psychographic as the display name, with age/region as additional info
        psychographic = row.get('psychographic', 'unknown')
        age_bucket = row.get('age_bucket', '')
        region = row.get('region', '')
        # Format: "psychographic (age, region)" or just "psychographic"
        if age_bucket and region:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket}, {region})"
        elif age_bucket:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket})"
        else:
            display_name = psychographic.title().replace('_', ' ')
        segment_id_to_name[row['segment_id']] = display_name

context_id_to_name = {}
if not data['contexts'].empty:
    for _, row in data['contexts'].iterrows():
        # Create readable context name from attributes
        context_name = f"{row.get('time_of_day', 'unknown').title()} - {row.get('location', 'unknown').title()} - {row.get('occasion', 'unknown').title()}"
        context_id_to_name[row['context_id']] = context_name

# Segment selector - show names but use IDs internally
if not data['segments'].empty:
    # Create options with names as labels - use psychographic as primary
    segment_options = {}
    for _, row in data['segments'].iterrows():
        seg_id = row['segment_id']
        psychographic = row.get('psychographic', 'unknown')
        age_bucket = row.get('age_bucket', '')
        region = row.get('region', '')
        # Format: "psychographic (age, region)" or just "psychographic"
        if age_bucket and region:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket}, {region})"
        elif age_bucket:
            display_name = f"{psychographic.title().replace('_', ' ')} ({age_bucket})"
        else:
            display_name = psychographic.title().replace('_', ' ')
        segment_options[display_name] = seg_id
    
    selected_segment_names = st.sidebar.multiselect(
        "Select Segments",
        options=list(segment_options.keys()),
        default=list(segment_options.keys())[:min(3, len(segment_options))]
    )
    # Convert selected names back to IDs
    selected_segments = [segment_options[name] for name in selected_segment_names]
else:
    selected_segments = []
    st.sidebar.warning("No segment data available")

# Context selector - show names but use IDs internally
if not data['contexts'].empty:
    # Create options with names as labels
    context_options = {}
    for _, row in data['contexts'].iterrows():
        ctx_id = row['context_id']
        ctx_name = context_id_to_name.get(ctx_id, ctx_id)
        context_options[ctx_name] = ctx_id
    
    selected_context_names = st.sidebar.multiselect(
        "Select Contexts",
        options=list(context_options.keys()),
        default=list(context_options.keys())[:min(5, len(context_options))]
    )
    # Convert selected names back to IDs
    selected_contexts = [context_options[name] for name in selected_context_names]
else:
    selected_contexts = []
    st.sidebar.warning("No context data available")

# Time range
time_range = st.sidebar.slider(
    "Time Range (days)",
    min_value=0,
    max_value=90,
    value=(0, 30),
    step=1
)

# Scenario selector (placeholder)
scenario = st.sidebar.selectbox(
    "Scenario",
    options=["Baseline", "Optimistic", "Pessimistic"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.header("What-If Simulation")

# What-if controls
price_multiplier = st.sidebar.slider(
    "Price Multiplier",
    min_value=0.5,
    max_value=2.0,
    value=1.0,
    step=0.1,
    help="1.0 = baseline, 1.1 = +10% price"
)

sugar_adjustment = st.sidebar.slider(
    "Sugar Adjustment (g)",
    min_value=-20.0,
    max_value=20.0,
    value=0.0,
    step=1.0,
    help="Additive adjustment to sugar content"
)

marketing_exposure = st.sidebar.slider(
    "Marketing Exposure Multiplier",
    min_value=0.0,
    max_value=3.0,
    value=1.0,
    step=0.1,
    help="1.0 = baseline, 2.0 = 2x marketing exposure"
)

st.sidebar.markdown("---")
st.sidebar.header("💬 Chat with AI")
st.sidebar.markdown("Ask questions about insights and data")

# Store mappings in session state for chatbot
if 'segment_id_to_name' not in st.session_state:
    st.session_state['segment_id_to_name'] = segment_id_to_name
if 'context_id_to_name' not in st.session_state:
    st.session_state['context_id_to_name'] = context_id_to_name

# Initialize chatbot if not already done
if st.session_state.get('chatbot') is None:
    try:
        # Generate insights for chatbot context
        insights_list = []
        if selected_segments and not data['trajectories'].empty:
            insights_list = generate_insights(
                data['trajectories'],
                data['intent_logs'],
                data['intent_index'],
                data['momentum'],
                selected_segments,
                selected_contexts,
                time_range
            )
        
        st.session_state['chatbot'] = DashboardChatbot(
            data=data,
            insights=insights_list,
            use_openai=True,
            model="gpt-4o-mini"
        )
    except Exception as e:
        st.sidebar.warning(f"Chatbot init: {str(e)}")

# Chat interface
chatbot = st.session_state.get('chatbot')
if chatbot:
    # Display chat history
    chat_history = st.session_state.get('chat_history', [])
    for message in chat_history[-10:]:  # Show last 10 messages
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Suggested questions
    with st.sidebar.expander("💡 Suggested Questions"):
        suggested = chatbot.get_suggested_questions()
        for q in suggested[:5]:
            if st.button(q, key=f"suggest_{hash(q)}", use_container_width=True):
                # Add to chat
                response = chatbot.chat(q)
                st.session_state['chat_history'] = st.session_state.get('chat_history', [])
                st.session_state['chat_history'].append({"role": "user", "content": q})
                st.session_state['chat_history'].append({"role": "assistant", "content": response})
                st.rerun()
    
    # User input
    user_input = st.sidebar.chat_input("Ask about insights...")
    
    if user_input:
        # Add user message
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []
        st.session_state['chat_history'].append({"role": "user", "content": user_input})
        
        # Get chatbot response
        with st.sidebar.spinner("Thinking..."):
            response = chatbot.chat(user_input)
            st.session_state['chat_history'].append({"role": "assistant", "content": response})
        
        st.rerun()
    
    # Reset button
    if st.sidebar.button("🔄 Reset Conversation"):
        chatbot.reset_conversation()
        st.session_state['chat_history'] = []
        st.rerun()
else:
    st.sidebar.info("💡 Chatbot will be available after data loads. Set OPENAI_API_KEY environment variable to enable.")
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        st.sidebar.warning("⚠️ No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Taste Snapshot",
    "📈 Behavioral Dynamics",
    "💡 Insights",
    "🔮 What-If Simulation"
])

# Panel A: Taste Snapshot
with tab1:
    st.header("Baseline Taste & Preference Profile")
    
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Compute taste profile
        taste_profile = compute_taste_profile(
            data['products'],
            data['segments'],
            data['intent_logs'],
            selected_segments
        )
        
        if not taste_profile.empty:
            # Radar chart for taste preferences
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Normalize metrics for radar chart
                metrics_to_plot = ['avg_intent', 'sugar_preference', 'caffeine_tolerance', 'price_sensitivity']
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
                        
                        seg_id = row['segment_id']
                        seg_name = segment_id_to_name.get(seg_id, seg_id)
                        fig.add_trace(go.Scatterpolar(
                            r=normalized + [normalized[0]],  # Close the loop
                            theta=available_metrics + [available_metrics[0]],
                            fill='toself',
                            name=seg_name
                        ))
                    
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        showlegend=True,
                        title="Taste Profile Radar Chart"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Fallback to bar chart
                    if 'avg_intent' in taste_profile.columns:
                        # Create display version with segment names
                        taste_profile_display = taste_profile.copy()
                        taste_profile_display['segment_name'] = taste_profile_display['segment_id'].map(segment_id_to_name)
                        fig = px.bar(
                            taste_profile_display,
                            x='segment_name',
                            y='avg_intent',
                            title='Average Intent by Segment'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Metrics summary
                st.subheader("Key Metrics")
                for _, row in taste_profile.iterrows():
                    seg_id = row['segment_id']
                    seg_name = segment_id_to_name.get(seg_id, seg_id)
                    st.metric(
                        label=f"{seg_name} - Avg Intent",
                        value=f"{row['avg_intent']:.3f}"
                    )
                    if 'top_category' in row and pd.notna(row['top_category']):
                        st.caption(f"Top Category: {row['top_category']}")
            
            # Detailed table
            st.subheader("Detailed Profile")
            # Replace segment_id with segment_name for display
            taste_profile_display = taste_profile.copy()
            taste_profile_display['segment_name'] = taste_profile_display['segment_id'].map(segment_id_to_name)
            # Reorder columns to show name first
            cols = ['segment_name', 'segment_id'] + [c for c in taste_profile_display.columns if c not in ['segment_name', 'segment_id']]
            taste_profile_display = taste_profile_display[[c for c in cols if c in taste_profile_display.columns]]
            st.dataframe(taste_profile_display, use_container_width=True)
        else:
            st.warning("No taste profile data available for selected segments")

# Panel B: Behavioral Dynamics
with tab2:
    st.header("Behavioral Dynamics Over Time")
    
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Use Phase 4 anchored data if available, otherwise trajectories
        trajectories = data['phase4_anchored'] if not data['phase4_anchored'].empty else data['trajectories']
        
        if trajectories.empty:
            st.warning("No trajectory data available")
        else:
            # Compute behavioral dynamics
            dynamics = compute_behavioral_dynamics(
                trajectories,
                selected_segments,
                selected_contexts,
                time_range
            )
            
            if not dynamics.empty:
                # Time series plots
                time_col = 'time_step' if 'time_step' in dynamics.columns else 'date'
                
                # Purchase probability
                fig1 = px.line(
                    dynamics,
                    x=time_col,
                    y='purchase_probability',
                    title='Purchase Probability Over Time',
                    labels={'purchase_probability': 'Purchase Probability', time_col: 'Time'}
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # Multiple metrics subplot
                fig2 = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Repeat Rate', 'Churn Rate', 'Adoption Rate', 'Intent Value'),
                    vertical_spacing=0.1
                )
                
                fig2.add_trace(
                    go.Scatter(x=dynamics[time_col], y=dynamics['repeat_rate'], name='Repeat Rate'),
                    row=1, col=1
                )
                fig2.add_trace(
                    go.Scatter(x=dynamics[time_col], y=dynamics['churn_rate'], name='Churn Rate'),
                    row=1, col=2
                )
                fig2.add_trace(
                    go.Scatter(x=dynamics[time_col], y=dynamics['adoption_rate'], name='Adoption Rate'),
                    row=2, col=1
                )
                fig2.add_trace(
                    go.Scatter(x=dynamics[time_col], y=dynamics['purchase_probability'], name='Intent'),
                    row=2, col=2
                )
                
                fig2.update_layout(height=600, showlegend=False, title_text="Behavioral Metrics Over Time")
                st.plotly_chart(fig2, use_container_width=True)
                
                # Segment-context interaction
                st.subheader("Segment-Context Interaction")
                interaction = compute_segment_context_interaction(
                    data['intent_logs'],
                    trajectories,
                    selected_segments
                )
                
                if not interaction.empty:
                    interaction_pivot = interaction.pivot(
                        index='segment_id',
                        columns='context_id',
                        values='intent_value'
                    )
                    
                    fig3 = px.imshow(
                        interaction_pivot,
                        labels=dict(x="Context", y="Segment", color="Intent"),
                        title="Segment-Context Interaction Heatmap"
                    )
                    st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("No dynamics data computed for selected filters")

# Panel C: Insights
with tab3:
    st.header("Auto-Generated Insights")
    
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Generate insights
        insights = generate_insights(
            data['trajectories'],
            data['intent_logs'],
            data['intent_index'],
            data['momentum'],
            selected_segments,
            selected_contexts,
            time_range
        )
        
        if insights:
            # Display insight cards
            cols = st.columns(2)
            
            for idx, insight in enumerate(insights):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"### {insight['title']}")
                        st.metric(
                            label="Value",
                            value=insight['value']
                        )
                        # Replace segment/context IDs with names in description
                        description = insight['description']
                        if 'segment' in insight:
                            seg_id = insight['segment']
                            seg_name = segment_id_to_name.get(seg_id, seg_id)
                            description = description.replace(seg_id, seg_name)
                        st.caption(description)
                        st.markdown("---")
            
            # Evidence chart for top insight
            if len(insights) > 0:
                top_insight = insights[0]
                st.subheader(f"Evidence: {top_insight['title']}")
                
                # Create evidence chart based on insight type
                if top_insight['type'] == 'delta' and not data['intent_index'].empty:
                    intent_data = data['intent_index']
                    # Handle both 'category' and 'product_category' column names
                    cat_col = 'product_category' if 'product_category' in intent_data.columns else 'category'
                    if cat_col in intent_data.columns and top_insight.get('category'):
                        cat_data = intent_data[intent_data[cat_col] == top_insight['category']]
                        if not cat_data.empty:
                            fig = px.line(
                                cat_data,
                                x='date',
                                y='intent_mean',
                                title=f"{top_insight['category']} Intent Over Time"
                            )
                            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No insights generated. Try adjusting filters or ensure data is available.")

# Panel D: What-If Simulation
with tab4:
    st.header("Counterfactual What-If Simulation")
    
    if not selected_segments:
        st.warning("Please select at least one segment in the sidebar")
    else:
        # Get baseline trajectories
        baseline = data['phase4_anchored'] if not data['phase4_anchored'].empty else data['trajectories']
        
        if baseline.empty:
            st.warning("No baseline trajectory data available")
        else:
            # Filter baseline
            baseline_filtered = baseline[
                baseline['segment_id'].isin(selected_segments)
            ].copy()
            
            if baseline_filtered.empty:
                st.warning("No data for selected segments")
            else:
                # Run counterfactual simulation
                with st.spinner("Running counterfactual simulation..."):
                    counterfactual = cache_simulation(
                        baseline_filtered,
                        price_multiplier,
                        sugar_adjustment,
                        marketing_exposure
                    )
                
                # Compare baseline vs counterfactual
                comparison = compare_baseline_vs_counterfactual(
                    baseline_filtered,
                    counterfactual
                )
                
                if comparison:
                    # Display comparison metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Baseline Avg Intent",
                            f"{comparison['baseline']['avg_intent']:.3f}"
                        )
                    
                    with col2:
                        st.metric(
                            "Counterfactual Avg Intent",
                            f"{comparison['counterfactual']['avg_intent']:.3f}",
                            delta=f"{comparison['deltas']['intent_delta']:+.3f}"
                        )
                    
                    with col3:
                        st.metric(
                            "Intent Change %",
                            f"{comparison['deltas']['intent_delta_pct']:+.2f}%"
                        )
                    
                    with col4:
                        st.metric(
                            "Total Interactions",
                            f"{comparison['counterfactual']['total_interactions']}",
                            delta=f"{comparison['deltas']['interactions_delta']:+d}"
                        )
                    
                    # Overlay chart
                    st.subheader("Baseline vs Counterfactual")
                    
                    time_col = 'time_step' if 'time_step' in baseline_filtered.columns else 'date'
                    
                    if time_col in baseline_filtered.columns and time_col in counterfactual.columns:
                        baseline_ts = baseline_filtered.groupby(time_col)['intent_value'].mean()
                        cf_ts = counterfactual.groupby(time_col)['intent_value'].mean()
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=baseline_ts.index,
                            y=baseline_ts.values,
                            mode='lines',
                            name='Baseline',
                            line=dict(color='blue', width=2)
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=cf_ts.index,
                            y=cf_ts.values,
                            mode='lines',
                            name='Counterfactual',
                            line=dict(color='red', width=2, dash='dash')
                        ))
                        
                        fig.update_layout(
                            title="Intent Over Time: Baseline vs Counterfactual",
                            xaxis_title=time_col,
                            yaxis_title="Intent Value",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Time column not available for time series visualization")
                    
                    # Delta summary
                    st.subheader("Delta Summary")
                    delta_df = pd.DataFrame({
                        'Metric': ['Intent Delta', 'Intent Delta %', 'Interactions Delta', 'Interactions Delta %'],
                        'Value': [
                            f"{comparison['deltas']['intent_delta']:+.3f}",
                            f"{comparison['deltas']['intent_delta_pct']:+.2f}%",
                            f"{comparison['deltas']['interactions_delta']:+d}",
                            f"{comparison['deltas']['interactions_delta_pct']:+.2f}%"
                        ]
                    })
                    st.dataframe(delta_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption("Behavioral Simulation Dashboard - Synthetic Data Demo | Built with Streamlit")

