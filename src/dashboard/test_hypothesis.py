"""
Test Hypothesis Page Module

This module contains the code for the Test Hypothesis page, including:
- UI components and styling
- Filter controls (demographics, establishment, etc.)
- Simulation options display
- Network graph creation function
"""

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime
import hashlib


def create_louiza_network_graph(selected_restaurants, selected_regions, selected_ages, market_view):
    """Create an interactive 3D network graph for Louiza page with filters"""
    # Fast food restaurants (filtered by selection)
    all_restaurants = [
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

    # Filter restaurants based on selection
    restaurants = (
        [r for r in all_restaurants if r in selected_restaurants]
        if selected_restaurants
        else all_restaurants
    )

    # Create network graph
    G = nx.Graph()

    # Add nodes with attributes based on filters
    for restaurant in restaurants:
        G.add_node(restaurant, region=selected_regions, age=selected_ages)

    # Add edges based on similarity and market view
    # Fast food burger chains
    burger_chains = ["McDonald's", "Burger King", "Wendy's", "Jack in the Box", "Sonic"]
    burger_chains = [r for r in burger_chains if r in restaurants]
    for i, r1 in enumerate(burger_chains):
        for r2 in burger_chains[i + 1 :]:
            weight = 0.9 if market_view == "Market Research" else 0.7
            G.add_edge(r1, r2, weight=weight)

    # Pizza chains
    pizza_chains = ["Pizza Hut", "Domino's", "Papa John's"]
    pizza_chains = [r for r in pizza_chains if r in restaurants]
    for i, r1 in enumerate(pizza_chains):
        for r2 in pizza_chains[i + 1 :]:
            weight = 0.9 if market_view == "Market Research" else 0.7
            G.add_edge(r1, r2, weight=weight)

    # Mexican fast food
    mexican_chains = ["Taco Bell", "Chipotle"]
    mexican_chains = [r for r in mexican_chains if r in restaurants]
    if len(mexican_chains) > 1:
        weight = 0.8 if market_view == "Market Research" else 0.6
        G.add_edge(mexican_chains[0], mexican_chains[1], weight=weight)

    # Coffee chains
    coffee_chains = ["Starbucks", "Dunkin'"]
    coffee_chains = [r for r in coffee_chains if r in restaurants]
    if len(coffee_chains) > 1:
        weight = 0.8 if market_view == "Market Research" else 0.6
        G.add_edge(coffee_chains[0], coffee_chains[1], weight=weight)

    # Cross-category connections (weaker)
    if "McDonald's" in restaurants and "Taco Bell" in restaurants:
        G.add_edge("McDonald's", "Taco Bell", weight=0.4)
    if "Burger King" in restaurants and "KFC" in restaurants:
        G.add_edge("Burger King", "KFC", weight=0.5)
    if "Subway" in restaurants and "Pizza Hut" in restaurants:
        G.add_edge("Subway", "Pizza Hut", weight=0.3)
    if "Chipotle" in restaurants and "Starbucks" in restaurants:
        G.add_edge("Chipotle", "Starbucks", weight=0.3)
    if "Taco Bell" in restaurants and "KFC" in restaurants:
        G.add_edge("Taco Bell", "KFC", weight=0.4)
    if "McDonald's" in restaurants and "Starbucks" in restaurants:
        G.add_edge("McDonald's", "Starbucks", weight=0.3)
    if "Subway" in restaurants and "Chipotle" in restaurants:
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
                line=dict(width=weight * 4 + 1, color=f"rgba(91, 155, 213, {0.2 + weight*0.3})"),
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
                line=dict(width=weight * 6 + 3, color=f"rgba(91, 155, 213, {0.08 + weight*0.12})"),
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
            dragmode="orbit",
            height=750,
            clickmode="event+select",
        ),
    )

    fig.update_layout(uirevision="louiza-network-graph", selectdirection="d")

    return fig


def generate_persona_response(persona, user_message):
    """Generate a response from the persona based on their characteristics"""
    name = persona["name"]
    job = persona["job"]
    interest = persona["interest"]
    age = persona["age"]
    region = persona["region"]
    income = persona["income"]
    education = persona["education"]
    gender = persona["gender"]

    user_lower = user_message.lower()

    # Contextual responses based on keywords and persona traits
    if any(word in user_lower for word in ["hello", "hi", "hey", "greetings"]):
        return f"Hi there! I'm {name}, a {age}-year-old {gender} from {region}. I work as a {job.lower()} and I'm really into {interest.lower()}. How can I help you?"

    elif any(word in user_lower for word in ["preference", "like", "favorite", "enjoy", "love"]):
        return f"As someone who works as a {job.lower()}, I tend to prefer things that are practical and efficient. I really enjoy {interest.lower()}, so anything related to that usually catches my attention. My {income} income level means I'm looking for good value, but I don't mind paying a bit more for quality."

    elif any(word in user_lower for word in ["opinion", "think", "feel", "believe", "view"]):
        return f"From my perspective as a {age}-year-old {job.lower()} in {region}, I'd say that's an interesting point. Given my {education.lower()} background, I tend to think about things from a practical angle. What specifically are you curious about?"

    elif any(
        word in user_lower
        for word in ["habit", "routine", "usually", "typically", "often", "daily"]
    ):
        return f"My daily routine as a {job.lower()} is pretty busy, but I always make time for {interest.lower()}. I usually balance work responsibilities with my personal interests. Living in {region} means I have access to some great opportunities for {interest.lower()}. Is there something specific about my routine you'd like to know?"

    elif any(
        word in user_lower for word in ["buy", "purchase", "shopping", "spend", "money", "price"]
    ):
        income_context = (
            "I'm careful with my spending"
            if "Under" in income
            else "I'm willing to invest in quality" if "Over" in income else "I look for good value"
        )
        return f"{income_context} given my {income} income level. As a {job.lower()}, I appreciate products and services that make my life easier. When it comes to {interest.lower()}, I don't mind spending a bit more if it's something I'll really use and enjoy."

    elif any(word in user_lower for word in ["work", "job", "career", "profession"]):
        return f"I work as a {job.lower()}, which keeps me pretty busy. My {education.lower()} education has been helpful in my career. I enjoy what I do, but I also value my time outside of work, especially for {interest.lower()}. What would you like to know about my work?"

    elif any(word in user_lower for word in ["location", "region", "where", "area", "city"]):
        return f"I'm from {region}, which is a great place to live. The area has a lot to offer, especially when it comes to {interest.lower()}. The local culture and opportunities here really influence my preferences and lifestyle choices."

    else:
        # Default contextual response
        return f"That's a good question! As a {age}-year-old {gender} {job.lower()} from {region}, I'd say my perspective is shaped by my experience with {interest.lower()} and my {education.lower()} background. Could you tell me more about what you're looking to understand? I'm happy to share my thoughts based on my {income} lifestyle and interests."


def generate_detailed_persona(node_id, age, gender, region, income, education):
    """Generate a detailed customer persona for a specific node"""
    # Names based on gender
    names = {
        "Male": ["Alex", "Jordan", "Michael", "David", "Chris", "Ryan", "James", "Daniel"],
        "Female": ["Sarah", "Emma", "Jessica", "Emily", "Olivia", "Sophia", "Mia", "Ava"],
        "Non-binary": ["Alex", "Jordan", "Taylor", "Casey", "Riley", "Quinn", "Avery", "Morgan"],
        "All": ["Alex", "Jordan", "Taylor", "Casey", "Riley", "Quinn", "Avery", "Morgan"],
    }

    # Jobs based on income/education
    jobs_by_income = {
        "Under $25k": ["Retail Associate", "Food Service Worker", "Delivery Driver", "Cashier"],
        "$25k-$50k": [
            "Office Assistant",
            "Customer Service Rep",
            "Sales Associate",
            "Administrative Assistant",
        ],
        "$50k-$75k": ["Marketing Coordinator", "Teacher", "Nurse", "Accountant"],
        "$75k-$100k": ["Software Developer", "Project Manager", "Financial Analyst", "Engineer"],
        "$100k-$150k": ["Senior Manager", "Consultant", "Director", "Senior Engineer"],
        "$150k-$200k": ["VP", "Senior Director", "Principal Engineer", "Executive"],
        "Over $200k": ["CEO", "CFO", "Partner", "C-Suite Executive"],
        "All": ["Professional", "Worker", "Employee", "Manager"],
    }

    # Interests based on age
    interests_by_age = {
        "18-24": ["Social media", "Gaming", "Music festivals", "Fast fashion"],
        "25-34": ["Fitness", "Travel", "Foodie culture", "Tech gadgets"],
        "35-44": ["Family activities", "Home improvement", "Investing", "Health & wellness"],
        "45-54": ["Real estate", "Retirement planning", "Golf", "Wine"],
        "55-64": ["Travel", "Grandchildren", "Gardening", "Volunteering"],
        "65+": ["Retirement", "Healthcare", "Hobbies", "Family time"],
        "All": ["Various interests", "Hobbies", "Activities"],
    }

    # Select based on node_id for consistency
    name_idx = hash(node_id) % len(names.get(gender, names["All"]))
    name = names.get(gender, names["All"])[name_idx]

    job_list = jobs_by_income.get(income, jobs_by_income["All"])
    job_idx = hash(node_id + "job") % len(job_list)
    job = job_list[job_idx]

    interest_list = interests_by_age.get(age, interests_by_age["All"])
    interest_idx = hash(node_id + "interest") % len(interest_list)
    interest = interest_list[interest_idx]

    # Build detailed persona
    gender_str = gender.lower() if gender != "All" else "person"
    age_str = f"{age}" if age != "All" else "various ages"
    region_str = region if region != "All" else "various regions"

    persona = {
        "name": name,
        "age": age_str,
        "gender": gender_str,
        "region": region_str,
        "income": income if income != "All" else "varying income",
        "education": education if education != "All" else "varying education",
        "job": job,
        "interest": interest,
    }

    return persona


def generate_customer_persona(age, gender, region, income, education):
    """Generate a customer persona description based on demographics"""
    # Format the persona string
    gender_str = gender.lower() if gender != "All" else "person"
    age_str = f"age {age}" if age != "All" else "various ages"
    region_str = f"in {region}" if region != "All" else "across regions"
    income_str = f"with {income} income" if income != "All" else "with varying income"
    education_str = (
        f"with {education} education" if education != "All" else "with varying education"
    )

    # Build persona description
    parts = [gender_str, age_str, region_str]
    if income != "All":
        parts.append(income_str)
    if education != "All":
        parts.append(education_str)

    return " ".join(parts)


def get_node_color_from_demographics(age, gender, region, income, education):
    """Generate a color based on demographics - creates unique colors for different combinations"""
    # Create a hash from demographics
    demo_string = f"{age}_{gender}_{region}_{income}_{education}"
    hash_obj = hashlib.md5(demo_string.encode())
    hash_hex = hash_obj.hexdigest()

    # Convert hash to RGB values (darker colors for better visibility on dark background)
    r = int(hash_hex[0:2], 16) % 200 + 55  # 55-255 range, but cap at 200 for darker
    g = int(hash_hex[2:4], 16) % 200 + 55
    b = int(hash_hex[4:6], 16) % 200 + 55

    # Ensure minimum brightness
    if r + g + b < 300:
        r = min(r + 50, 200)
        g = min(g + 50, 200)
        b = min(b + 50, 200)

    return f"rgb({r}, {g}, {b})"


def create_simple_network_graph(
    selected_age="All",
    selected_gender="All",
    selected_region="All",
    selected_income="All",
    selected_education="All",
):
    """Create a simple 2D network graph with demographic-based node colors and personas"""
    # Create a simple network with nodes
    G = nx.Graph()

    # Add nodes representing different customer segments/entities
    nodes = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]
    for node in nodes:
        G.add_node(node)

    # Add some connections
    edges = [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "E"),
        ("D", "F"),
        ("E", "G"),
        ("F", "H"),
        ("G", "I"),
        ("H", "J"),
        ("I", "K"),
        ("J", "L"),
        ("K", "M"),
        ("L", "N"),
        ("M", "O"),
        ("N", "A"),
        ("B", "E"),
        ("C", "F"),
        ("D", "G"),
        ("E", "H"),
        ("F", "I"),
    ]
    G.add_edges_from(edges)

    # Use spring layout
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)

    # Extract positions
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]

    # Generate node colors and personas based on demographics
    node_colors = []
    hover_texts = []
    node_personas = {}  # Store personas for each node

    # Get color for the selected demographics
    base_color = get_node_color_from_demographics(
        selected_age, selected_gender, selected_region, selected_income, selected_education
    )

    for node in G.nodes():
        # Generate detailed persona for each node
        persona = generate_detailed_persona(
            node,
            selected_age,
            selected_gender,
            selected_region,
            selected_income,
            selected_education,
        )
        node_personas[node] = persona

        # Use the same color for all nodes based on selected demographics
        node_colors.append(base_color)

        # Create detailed hover text with persona card
        # Note: Plotly hover templates support basic HTML (br, b, i, sub, sup, span)
        # Using simpler formatting that Plotly can render properly
        hover_texts.append(
            f"<b>{persona['name']}</b><br>"
            f"Age: {persona['age']} • {persona['gender'].capitalize()}<br>"
            f"Location: {persona['region']}<br>"
            f"Job: {persona['job']}<br>"
            f"Income: {persona['income']}<br>"
            f"Education: {persona['education']}<br>"
            f"Interest: {persona['interest']}<br>"
            f"<br><i>Click node to chat</i>"
        )

    # Create edge traces
    edge_traces = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=0.5, color="rgba(255, 255, 255, 0.1)"),
                hoverinfo="none",
                showlegend=False,
            )
        )

    # Create node trace with colors and hover text
    # Add customdata with node IDs for potential click handling
    node_ids = list(G.nodes())
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hovertext=hover_texts,
        hoverinfo="text",
        customdata=node_ids,  # Store node IDs for click handling
        marker=dict(
            size=14,
            color=node_colors,
            line=dict(width=2, color="rgba(255, 255, 255, 0.6)"),
            opacity=0.85,
        ),
        showlegend=False,
    )

    # Create figure
    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title="",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            clickmode="event+select",
        ),
    )

    return fig, node_personas


def render_test_hypothesis_page():
    """Render the Test Hypothesis page with all its components"""
    # Custom styling for Test Hypothesis page
    st.markdown(
        """
        <style>
        /* Test Hypothesis page specific styling */
        .louiza-container {
        background: #000000;
        }

        /* Reduce top padding to push content up */
        .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        }

        /* Remove Streamlit header spacing */
        [data-testid="stHeader"] {
        display: none !important;
        }

        /* Sidebar styling - narrow left panel - ultra condensed */
        [data-testid="column"]:first-child {
        background: #1A1A1A;
        padding: 0.5rem !important;
        border-radius: 0;
        border-right: 1px solid rgba(91, 155, 213, 0.2);
        align-self: flex-start;
        margin-top: 0 !important;
        padding-top: 0.5rem !important;
        width: 18% !important;
        min-width: 200px;
        }
        /* Reduce spacing in sidebar - tighter sections */
        [data-testid="column"]:first-child hr,
        [data-testid="column"]:first-child .stMarkdown hr {
        margin: 0.25rem 0 !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        }
        /* Reduce spacing between sections */
        [data-testid="column"]:first-child .sidebar-section-title {
        margin-top: 0.15rem !important;
        }
        [data-testid="column"]:first-child .element-container {
        margin-bottom: 0.1rem !important;
        }
        /* Make selectboxes more compact */
        [data-testid="column"]:first-child [data-testid="stSelectbox"] {
        margin-bottom: 0 !important;
        }
        [data-testid="column"]:first-child [data-testid="stSelectbox"] button {
        padding: 0.35rem 0.5rem !important;
        min-height: auto !important;
        font-size: 0.65rem !important;
        }
        [data-testid="column"]:first-child [data-testid="stSelectbox"] label {
        font-size: 0.65rem !important;
        }
        /* Make dropdown text smaller than section titles */
        [data-testid="column"]:first-child [data-testid="stSelectbox"] button span,
        [data-testid="column"]:first-child [data-baseweb="select"] button span,
        [data-testid="column"]:first-child [data-baseweb="select"] button div {
        font-size: 0.65rem !important;
        }
        [data-testid="column"]:first-child [data-testid="stSlider"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        }
        [data-testid="column"]:first-child [data-testid="stSlider"] label {
        font-size: 0.7rem !important;
        color: #888888 !important;
        }
        /* Reduce spacing after section titles */
        [data-testid="column"]:first-child .sidebar-section-title + * {
        margin-top: 0.2rem !important;
        }
        /* Hide help icons in sidebar */
        [data-testid="column"]:first-child [data-testid="stHelpIcon"],
        [data-testid="column"]:first-child button[aria-label*="help"],
        [data-testid="column"]:first-child button[title*="help"] {
        display: none !important;
        visibility: hidden !important;
        }

        /* Main content area - remove extra spacing */
        [data-testid="column"]:last-child {
        padding-left: 1.5rem;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        width: 82% !important;
        }

        /* Ensure columns start at top */
        [data-testid="column-container"] {
        align-items: flex-start !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        }

        /* Style selectboxes - minimal styling to not interfere with functionality */
        [data-testid="stSelectbox"] {
        margin-bottom: 0.5rem;
        }

        /* Style the BaseWeb select component */
        [data-baseweb="select"] {
        background-color: #1A1A1A !important;
        }

        [data-baseweb="select"] button {
        background-color: #1A1A1A !important;
        color: #E0E0E0 !important;
        border: 1px solid rgba(91, 155, 213, 0.3) !important;
        border-radius: 6px !important;
        }

        /* Style dropdown menu items */
        [data-baseweb="menu"] {
        background-color: #1A1A1A !important;
        }

        [data-baseweb="menu"] li,
        [data-baseweb="menu"] [role="option"] {
        background-color: #1A1A1A !important;
        color: #E0E0E0 !important;
        }

        [data-baseweb="menu"] li:hover,
        [data-baseweb="menu"] [role="option"]:hover {
        background-color: #2A2A2A !important;
        }

        /* Override any white backgrounds on selectboxes in main content */
        [data-testid="column"]:last-child [data-testid="stSelectbox"],
        [data-testid="column"]:last-child [data-baseweb="select"],
        [data-testid="column"]:last-child [data-baseweb="select"] button,
        [data-testid="column"]:last-child [data-baseweb="select"] button > div,
        [data-testid="column"]:last-child [data-baseweb="select"] button > span {
        background-color: #1A1A1A !important;
        background: #1A1A1A !important;
        color: #888888 !important;
        }

        /* Ensure dropdown popover is dark */
        [data-testid="column"]:last-child [data-baseweb="popover"],
        [data-testid="column"]:last-child [data-baseweb="popover"] > div {
        background-color: #1A1A1A !important;
        background: #1A1A1A !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        }

        /* Ensure dropdown menu items are dark */
        [data-testid="column"]:last-child [data-baseweb="menu"],
        [data-testid="column"]:last-child [data-baseweb="menu"] li,
        [data-testid="column"]:last-child [data-baseweb="menu"] [role="option"] {
        background-color: #1A1A1A !important;
        background: #1A1A1A !important;
        color: #888888 !important;
        }

        /* Remove box styling from network graph container */
        [data-testid="stVerticalBlock"]:has([class*="plotly"]),
        [data-testid="stVerticalBlock"]:has([data-testid="stPlotlyChart"]) {
        background: transparent !important;
        backdrop-filter: none !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        }

        </style>
    """,
        unsafe_allow_html=True,
    )

    # Create two columns: narrow left sidebar and main content
    col_sidebar, col_main = st.columns([0.18, 0.82], gap="small")

    with col_sidebar:
        st.markdown(
            """
            <style>
            .sidebar-section-title {
            color: #5B9BD5;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            }
            /* Make all non-title text in sidebar grey and smaller */
            [data-testid="stSlider"] label {
            color: #888888 !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
            }
            /* Style all sidebar section titles - grey and uppercase like reference */
            .sidebar-section-title {
            color: #888888 !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            margin-bottom: 0.3rem !important;
            margin-top: 0.2rem !important;
            }
            /* Reduce spacing between ALL dropdown boxes - extremely aggressive */
            [data-testid="column"]:first-child [data-testid="stSelectbox"],
            [data-testid="column"]:first-child .element-container:has([data-testid="stSelectbox"]),
            [data-testid="column"]:first-child [data-testid="stSelectbox"] + *,
            [data-testid="column"]:first-child .element-container:has([data-testid="stSelectbox"]) + *,
            [data-testid="column"]:first-child > div:has([data-testid="stSelectbox"]),
            [data-testid="column"]:first-child [class*="element-container"]:has([data-testid="stSelectbox"]),
            [data-testid="column"]:first-child [data-testid="stVerticalBlock"] > div:has([data-testid="stSelectbox"]),
            [data-testid="column"]:first-child [data-testid="stVerticalBlock"] > div:has([data-testid="stSelectbox"]) + div,
            [data-testid="column"]:first-child [data-testid="stVerticalBlock"] > div:has([data-testid="stSelectbox"]) ~ div {
            margin-bottom: -2.5rem !important;
            margin-top: -2.5rem !important;
            padding-bottom: 0 !important;
            padding-top: 0 !important;
            }
            /* Even more aggressive spacing reduction for demographic selectboxes */
            [data-testid="column"]:first-child [data-testid="stVerticalBlock"] > div:nth-child(n+2):nth-child(-n+7),
            [data-testid="column"]:first-child [data-testid="stVerticalBlock"] > div:nth-child(n+2):nth-child(-n+7) > *,
            [data-testid="column"]:first-child [data-testid="stVerticalBlock"] > div:nth-child(n+2):nth-child(-n+7) .element-container {
            margin-bottom: -2.6rem !important;
            margin-top: -2.6rem !important;
            padding-bottom: 0 !important;
            padding-top: 0 !important;
            }
            /* Style Market View label to match section titles */
            [data-testid="column"]:first-child [data-testid="stSelectbox"] label {
            color: #888888 !important;
            font-size: 0.7rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            }
            /* Other selectbox labels stay grey */
            [data-testid="stExpander"] [data-testid="stSelectbox"] label,
            [data-testid="column"]:first-child [data-testid="stExpander"] [data-testid="stSelectbox"] label {
            color: #888888 !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
            text-transform: none !important;
            }
            /* Style expander label to match section titles - grey uppercase */
            [data-testid="stExpander"] > label,
            [data-testid="stExpander"] > label > p,
            [data-testid="stExpander"] summary,
            [data-testid="stExpander"] summary p {
            color: #888888 !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
            }
            /* Hide keyboard arrow indicators that appear near expanders - very aggressive */
            [data-testid="stExpander"] button[aria-label*="keyboard"],
            [data-testid="stExpander"] button[title*="keyboard"],
            [data-testid="stExpander"] [class*="keyboard"],
            [data-testid="stExpander"] [class*="arrow"],
            [data-testid="stExpander"] svg[class*="keyboard"],
            [data-testid="stExpander"] svg[class*="arrow"],
            [data-testid="column"] button[aria-label*="keyboard"],
            [data-testid="column"] button[title*="keyboard"],
            [data-testid="column"] [class*="keyboard"],
            [data-testid="column"] [class*="arrow"],
            [data-testid="column"] svg[class*="keyboard"],
            [data-testid="column"] svg[class*="arrow"],
            [data-testid="column"]:first-child button[aria-label*="keyboard"],
            [data-testid="column"]:first-child button[title*="keyboard"],
            [data-testid="column"]:first-child [class*="keyboard"],
            [data-testid="column"]:first-child [class*="arrow"],
            [data-testid="column"]:first-child svg[class*="keyboard"],
            [data-testid="column"]:first-child svg[class*="arrow"],
            button[aria-label*="keyboard"],
            button[title*="keyboard"],
            [class*="keyboardArrow"],
            [class*="keyboard-arrow"],
            svg[class*="keyboard"],
            svg[class*="arrow"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            width: 0 !important;
            height: 0 !important;
            position: absolute !important;
            left: -9999px !important;
            }
            /* Ensure selectboxes inside expander still work and have proper styling */
            [data-testid="stExpander"] [data-testid="stSelectbox"],
            [data-testid="stExpander"] [data-baseweb="select"],
            [data-testid="stExpander"] [data-baseweb="popover"],
            [data-testid="stExpander"] [data-baseweb="menu"] {
            pointer-events: auto !important;
            z-index: 9999 !important;
            }
            [data-testid="stExpander"] [data-testid="stSelectbox"] label {
            color: #888888 !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
            }
            </style>
            <script>
            // Aggressively hide keyboard arrow elements
            function hideKeyboardArrows() {
            const arrows = document.querySelectorAll('button[aria-label*="keyboard"], button[title*="keyboard"], [class*="keyboard"], [class*="arrow"], svg[class*="keyboard"], svg[class*="arrow"]');
            arrows.forEach(el => {
                if (el && el.closest('[data-testid="column"]')) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    el.style.opacity = '0';
                    el.style.width = '0';
                    el.style.height = '0';
                    el.style.position = 'absolute';
                    el.style.left = '-9999px';
                }
            });
            }

            // Reduce spacing between ALL dropdown boxes - extremely aggressive
            function reduceDemographicSpacing() {
            const sidebar = document.querySelector('[data-testid="column"]:first-child');
            if (sidebar) {
                // Find all selectboxes in the sidebar
                const selectboxes = sidebar.querySelectorAll('[data-testid="stSelectbox"]');
                selectboxes.forEach((selectbox, index) => {
                    // Target all selectboxes including Market View (index 0-5)
                    if (index >= 0 && index < 6) {
                        const container = selectbox.closest('.element-container') || selectbox.parentElement;
                        if (container) {
                            container.style.marginBottom = '-2.6rem';
                            container.style.marginTop = '-2.6rem';
                            container.style.paddingBottom = '0';
                            container.style.paddingTop = '0';
                        }
                        // Also target the selectbox itself and all parent containers
                        selectbox.style.marginBottom = '-2.6rem';
                        selectbox.style.marginTop = '-2.6rem';
                        let parent = selectbox.parentElement;
                        let depth = 0;
                        while (parent && parent !== sidebar && depth < 5) {
                            parent.style.marginBottom = '-2.6rem';
                            parent.style.marginTop = '-2.6rem';
                            parent.style.paddingBottom = '0';
                            parent.style.paddingTop = '0';
                            parent = parent.parentElement;
                            depth++;
                        }
                        // Make font smaller than section titles
                        const button = selectbox.querySelector('button');
                        if (button) {
                            button.style.fontSize = '0.65rem';
                            const spans = button.querySelectorAll('span, div');
                            spans.forEach(span => {
                                span.style.fontSize = '0.65rem';
                            });
                        }
                    }
                });
                // Reduce spacing on dividers
                const dividers = sidebar.querySelectorAll('hr');
                dividers.forEach(divider => {
                    divider.style.marginTop = '0.25rem';
                    divider.style.marginBottom = '0.25rem';
                });
                // Hide help icons
                const helpIcons = sidebar.querySelectorAll('[data-testid="stHelpIcon"], button[aria-label*="help"], button[title*="help"]');
                helpIcons.forEach(icon => {
                    icon.style.display = 'none';
                    icon.style.visibility = 'hidden';
                });
            }
            }

            hideKeyboardArrows();
            reduceDemographicSpacing();
            setTimeout(() => {
            hideKeyboardArrows();
            reduceDemographicSpacing();
            }, 100);
            setTimeout(() => {
            hideKeyboardArrows();
            reduceDemographicSpacing();
            }, 500);
            const observer = new MutationObserver(() => {
            hideKeyboardArrows();
            reduceDemographicSpacing();
            });
            observer.observe(document.body, { childList: true, subtree: true });
            </script>
        """,
            unsafe_allow_html=True,
        )

        # Year slider - moved to top
        current_year = datetime.now().year
        min_year = current_year - 10
        max_year = current_year + 5

        st.markdown('<div class="sidebar-section-title">Year</div>', unsafe_allow_html=True)
        st.slider(
            "",
            min_value=min_year,
            max_value=max_year,
            value=current_year,
            step=1,
            key="louiza_year",
        )

        st.markdown('<hr style="margin: 0.25rem 0 !important;">', unsafe_allow_html=True)

        # View section - clean dropdown title
        st.markdown('<div class="sidebar-section-title">View</div>', unsafe_allow_html=True)
        market_view = st.selectbox("", ["Market Insight", "Hedge Fund"], key="louiza_market_view")

        st.markdown('<hr style="margin: 0.25rem 0 !important;">', unsafe_allow_html=True)

        # Demographics section - clean dropdown title
        st.markdown('<div class="sidebar-section-title">Demographics</div>', unsafe_allow_html=True)

        # Age filter - dropdown
        age_groups = ["All", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
        selected_age = st.selectbox("", age_groups, key="louiza_age")

        # Gender filter - dropdown
        gender_options = ["All", "Male", "Female", "Non-binary", "Prefer not to say"]
        selected_gender = st.selectbox("", gender_options, key="louiza_gender")

        # Location/Region filter - dropdown
        us_regions = [
            "All",
            "Northeast",
            "Southeast",
            "Midwest",
            "Southwest",
            "West",
            "Pacific",
            "Mountain",
            "New England",
        ]
        selected_region = st.selectbox("", us_regions, key="louiza_region")

        # Income filter - dropdown
        income_levels = [
            "All",
            "Under $25k",
            "$25k-$50k",
            "$50k-$75k",
            "$75k-$100k",
            "$100k-$150k",
            "$150k-$200k",
            "Over $200k",
        ]
        selected_income = st.selectbox("", income_levels, key="louiza_income")

        # Education filter - dropdown
        education_levels = [
            "All",
            "High School",
            "Some College",
            "Associate's",
            "Bachelor's",
            "Master's",
            "Doctorate",
            "Professional",
        ]
        selected_education = st.selectbox("", education_levels, key="louiza_education")

        st.markdown('<hr style="margin: 0.25rem 0 !important;">', unsafe_allow_html=True)

        # Establishment section - clean dropdown title
        st.markdown(
            '<div class="sidebar-section-title">Establishment</div>', unsafe_allow_html=True
        )

        fast_food_restaurants = [
            "All",
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

        st.selectbox("Fast Food Restaurant", fast_food_restaurants, key="louiza_restaurant")

    with col_main:
        # Initialize selected persona in session state
        if "selected_persona" not in st.session_state:
            st.session_state.selected_persona = None
        if "persona_chat_history" not in st.session_state:
            st.session_state.persona_chat_history = {}

        # Display network graph first with demographics
        network_fig, node_personas = create_simple_network_graph(
            selected_age=selected_age,
            selected_gender=selected_gender,
            selected_region=selected_region,
            selected_income=selected_income,
            selected_education=selected_education,
        )

        # Store personas in session state for access
        st.session_state.node_personas = node_personas

        # Display graph with click handling
        event_data = st.plotly_chart(
            network_fig,
            use_container_width=True,
            key="test_hypothesis_network_graph",
            config={"displayModeBar": False, "staticPlot": False},
            on_select="rerun",
        )

        # Handle node clicks to start chatting with personas
        if event_data and "points" in event_data and len(event_data["points"]) > 0:
            clicked_point = event_data["points"][0]
            if "pointIndex" in clicked_point:
                point_index = clicked_point["pointIndex"]
                node_list = list(node_personas.keys())
                if point_index < len(node_list):
                    selected_node = node_list[point_index]
                    st.session_state.selected_persona = node_personas[selected_node]
                    st.rerun()

        # Show persona chat if one is selected
        if st.session_state.selected_persona:
            persona = st.session_state.selected_persona
            persona_key = f"{persona['name']}_{persona['age']}_{persona['region']}"

            # Initialize chat history for this persona
            if persona_key not in st.session_state.persona_chat_history:
                st.session_state.persona_chat_history[persona_key] = []

            # Persona header with close button
            col_persona, col_close = st.columns([4, 1])
            with col_persona:
                st.markdown(
                    f"""
                    <div style="background: rgba(26, 26, 26, 0.8); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <h4 style="color: #5B9BD5; margin: 0;">Chatting with {persona['name']}</h4>
                        <p style="color: #888888; margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                            {persona['age']} • {persona['gender'].capitalize()} • {persona['region']} • {persona['job']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_close:
                if st.button("✕", key="close_persona", use_container_width=True):
                    st.session_state.selected_persona = None
                    st.rerun()

            # Display chat history
            if st.session_state.persona_chat_history[persona_key]:
                for message in st.session_state.persona_chat_history[persona_key]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            # Chat input
            user_input = st.chat_input(
                f"Ask {persona['name']} about their preferences, habits, or opinions..."
            )
            if user_input:
                # Add user message
                st.session_state.persona_chat_history[persona_key].append(
                    {"role": "user", "content": user_input}
                )

                # Generate persona response (simulated - you can enhance this with AI)
                response = generate_persona_response(persona, user_input)

                st.session_state.persona_chat_history[persona_key].append(
                    {"role": "assistant", "content": response}
                )

                st.rerun()

        # Initialize session state for selected simulation option and chat
        if "selected_simulation_option" not in st.session_state:
            st.session_state.selected_simulation_option = None
        if "simulation_chat_history" not in st.session_state:
            st.session_state.simulation_chat_history = {}

        # Centered modal below graph - conditional content based on market view
        if market_view == "Market Insight":
            # Show simulation selection screen only if no option is selected
            if not st.session_state.selected_simulation_option:
                # Market Insight view - business hypothesis categories with dropdowns
                st.markdown(
                    """
                <style>
                .simulation-modal-container {
                    background: transparent !important;
                    backdrop-filter: none !important;
                    border: none !important;
                    border-radius: 0 !important;
                    padding: 0 !important;
                    max-width: none !important;
                    width: 100%;
                    margin: 0 !important;
                    box-shadow: none !important;
                }
                .simulation-title {
                    color: #FFFFFF !important;
                    font-size: 0.95rem !important;
                    font-weight: 500 !important;
                    margin: 0 0 1.25rem 0 !important;
                    text-align: center;
                    letter-spacing: 0.3px !important;
                }
                .simulation-categories-wrapper {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 1.2rem;
                }
                .simulation-category {
                    margin-bottom: 0;
                }
                .category-title {
                    color: #888888 !important;
                    font-size: 0.7rem !important;
                    font-weight: 500 !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.5px !important;
                    margin-bottom: 0.5rem !important;
                }
                /* Style simulation dropdowns - dark background, grey text, smaller */
                .simulation-modal-container [data-testid="stSelectbox"],
                .simulation-modal-container [data-baseweb="select"] {
                    background-color: #1A1A1A !important;
                }
                .simulation-modal-container [data-baseweb="select"] button {
                    background-color: #1A1A1A !important;
                    color: #888888 !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                    border-radius: 6px !important;
                    font-size: 0.75rem !important;
                    padding: 0.4rem 0.6rem !important;
                }
                /* Target ALL possible child elements inside the button to override global E0E0E0 */
                .simulation-modal-container [data-baseweb="select"] button *,
                .simulation-modal-container [data-baseweb="select"] button span,
                .simulation-modal-container [data-baseweb="select"] button div,
                .simulation-modal-container [data-baseweb="select"] button p,
                .simulation-modal-container [data-baseweb="select"] button > *,
                .simulation-modal-container [data-baseweb="select"] button > div > *,
                .simulation-modal-container [data-baseweb="select"] button > span > * {
                    color: #888888 !important;
                    font-size: 0.75rem !important;
                }
                /* Style dropdown menu popover */
                .simulation-modal-container [data-baseweb="popover"] {
                    background-color: #1A1A1A !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                }
                .simulation-modal-container [data-baseweb="menu"] {
                    background-color: #1A1A1A !important;
                }
                .simulation-modal-container [data-baseweb="menu"] li,
                .simulation-modal-container [data-baseweb="menu"] [role="option"] {
                    background-color: #1A1A1A !important;
                    color: #888888 !important;
                    font-size: 0.75rem !important;
                }
                .simulation-modal-container [data-baseweb="menu"] li:hover,
                .simulation-modal-container [data-baseweb="menu"] [role="option"]:hover {
                    background-color: #2A2A2A !important;
                    color: #E0E0E0 !important;
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="simulation-modal-container">', unsafe_allow_html=True)
                # Add inline style tag AFTER container opens to ensure highest priority
                st.markdown(
                    """
                <style>
                /* Force simulation dropdown styling - inline for highest priority */
                .simulation-modal-container [data-baseweb="select"] button,
                .simulation-modal-container [data-baseweb="select"] button *,
                .simulation-modal-container [data-baseweb="select"] button div,
                .simulation-modal-container [data-baseweb="select"] button span,
                .simulation-modal-container [data-baseweb="select"] button div[value],
                .simulation-modal-container [data-baseweb="select"] button div[class*="st-"] {
                    color: #888888 !important;
                    font-size: 0.75rem !important;
                }
                .simulation-modal-container [data-baseweb="select"] button {
                    background-color: #1A1A1A !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                }
                </style>
                <script>
                (function() {
                    function forceStyle() {
                        const buttons = document.querySelectorAll('.simulation-modal-container [data-baseweb="select"] button');
                        buttons.forEach(function(btn) {
                            btn.style.setProperty('color', '#888888', 'important');
                            btn.style.setProperty('font-size', '0.75rem', 'important');
                            btn.style.setProperty('background-color', '#1A1A1A', 'important');
                            const all = btn.querySelectorAll('*');
                            all.forEach(function(el) {
                                el.style.setProperty('color', '#888888', 'important');
                                el.style.setProperty('font-size', '0.75rem', 'important');
                            });
                        });
                    }
                    forceStyle();
                    setInterval(forceStyle, 100);
                    new MutationObserver(forceStyle).observe(document.body, {childList: true, subtree: true});
                })();
                </script>
                """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<h3 class="simulation-title">What would you like to simulate?</h3>',
                    unsafe_allow_html=True,
                )

                # Create columns for categories
                cat_cols = st.columns(4)

                # Define categories and their options
                categories = {
                    "Product": [
                        "Menu Items",
                        "New Locations",
                        "Pricing Strategy",
                        "Product Launch",
                    ],
                    "Marketing": ["Campaigns", "Messaging", "Social Media Posts", "Advertisements"],
                    "Survey": ["Customer Feedback", "Market Research", "Satisfaction Survey"],
                    "Operations": ["Service Speed", "Drive-Thru Efficiency", "Staffing Levels"],
                    "Customer Experience": [
                        "Loyalty Programs",
                        "Ordering Experience",
                        "Delivery Options",
                    ],
                    "Pricing": ["Promotions", "Discounts", "Bundle Deals"],
                    "Location": ["Expansion", "New Markets", "Site Selection"],
                }

                # Display dropdowns for each category
                for idx, (category_name, options) in enumerate(categories.items()):
                    col_idx = idx % 4
                    with cat_cols[col_idx]:
                        st.markdown(
                            f'<div class="category-title">{category_name}</div>',
                            unsafe_allow_html=True,
                        )
                        # Add "None" as first option
                        dropdown_options = ["-- Select --"] + options
                        selected = st.selectbox(
                            "",
                            dropdown_options,
                            key=f"simulation_dropdown_{category_name}",
                            label_visibility="collapsed",
                        )

                        # Update session state when an option is selected
                        if selected != "-- Select --":
                            st.session_state.selected_simulation_option = {
                                "category": category_name,
                                "option": selected,
                            }
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Show chat agent when an option is selected
                selected_cat = st.session_state.selected_simulation_option["category"]
                selected_opt = st.session_state.selected_simulation_option["option"]

                # Initialize chat history for this option if not exists
                chat_key = f"{selected_cat}_{selected_opt}"
                if chat_key not in st.session_state.simulation_chat_history:
                    st.session_state.simulation_chat_history[chat_key] = []

                # Display chat history if there are messages
                if st.session_state.simulation_chat_history[chat_key]:
                    for message in st.session_state.simulation_chat_history[chat_key]:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                # Chat input bar
                user_input = st.chat_input(
                    "type your question or hypothesis and test it on simulated users"
                )
                if user_input:
                    # Add user message to chat history
                    st.session_state.simulation_chat_history[chat_key].append(
                        {"role": "user", "content": user_input}
                    )

                    # Here you could add AI response logic
                    # For now, just echo back
                    response = f"I understand you're asking about {selected_opt} in the {selected_cat} category. Your question: '{user_input}'"

                    st.session_state.simulation_chat_history[chat_key].append(
                        {"role": "assistant", "content": response}
                    )

                    st.rerun()
        else:
            # Hedge Fund view - similar implementation with dropdowns
            if not st.session_state.selected_simulation_option:
                st.markdown(
                    """
                    <style>
                    .simulation-modal-container {
                    background: transparent !important;
                    backdrop-filter: none !important;
                    border: none !important;
                    border-radius: 0 !important;
                    padding: 0 !important;
                    max-width: none !important;
                    width: 100%;
                    margin: 0 !important;
                    box-shadow: none !important;
                }
                .simulation-title {
                    color: #FFFFFF !important;
                    font-size: 0.95rem !important;
                    font-weight: 500 !important;
                    margin: 0 0 1.25rem 0 !important;
                    text-align: center;
                    letter-spacing: 0.3px !important;
                }
                .simulation-categories-wrapper {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 1.5rem;
                }
                .simulation-category {
                    margin-bottom: 0;
                }
                .category-title {
                    color: #888888 !important;
                    font-size: 0.7rem !important;
                    font-weight: 500 !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.5px !important;
                    margin-bottom: 0.5rem !important;
                }
                /* Style simulation dropdowns - dark background, grey text, smaller */
                .simulation-modal-container [data-testid="stSelectbox"],
                .simulation-modal-container [data-baseweb="select"] {
                    background-color: #1A1A1A !important;
                }
                .simulation-modal-container [data-baseweb="select"] button {
                    background-color: #1A1A1A !important;
                    color: #888888 !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                    border-radius: 6px !important;
                    font-size: 0.75rem !important;
                    padding: 0.4rem 0.6rem !important;
                }
                /* Target ALL possible child elements inside the button to override global E0E0E0 */
                .simulation-modal-container [data-baseweb="select"] button *,
                .simulation-modal-container [data-baseweb="select"] button span,
                .simulation-modal-container [data-baseweb="select"] button div,
                .simulation-modal-container [data-baseweb="select"] button p,
                .simulation-modal-container [data-baseweb="select"] button > *,
                .simulation-modal-container [data-baseweb="select"] button > div > *,
                .simulation-modal-container [data-baseweb="select"] button > span > * {
                    color: #888888 !important;
                    font-size: 0.75rem !important;
                }
                /* Style dropdown menu popover */
                .simulation-modal-container [data-baseweb="popover"] {
                    background-color: #1A1A1A !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                }
                .simulation-modal-container [data-baseweb="menu"] {
                    background-color: #1A1A1A !important;
                }
                .simulation-modal-container [data-baseweb="menu"] li,
                .simulation-modal-container [data-baseweb="menu"] [role="option"] {
                    background-color: #1A1A1A !important;
                    color: #888888 !important;
                    font-size: 0.75rem !important;
                }
                .simulation-modal-container [data-baseweb="menu"] li:hover,
                .simulation-modal-container [data-baseweb="menu"] [role="option"]:hover {
                    background-color: #2A2A2A !important;
                    color: #E0E0E0 !important;
                }
                </style>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="simulation-modal-container">', unsafe_allow_html=True)
                # Add inline style tag AFTER container opens to ensure highest priority
                st.markdown(
                    """
                <style>
                /* Force simulation dropdown styling - inline for highest priority */
                .simulation-modal-container [data-baseweb="select"] button,
                .simulation-modal-container [data-baseweb="select"] button *,
                .simulation-modal-container [data-baseweb="select"] button div,
                .simulation-modal-container [data-baseweb="select"] button span,
                .simulation-modal-container [data-baseweb="select"] button div[value],
                .simulation-modal-container [data-baseweb="select"] button div[class*="st-"] {
                    color: #888888 !important;
                    font-size: 0.75rem !important;
                }
                .simulation-modal-container [data-baseweb="select"] button {
                    background-color: #1A1A1A !important;
                    border: 1px solid rgba(255, 255, 255, 0.1) !important;
                }
                </style>
                <script>
                (function() {
                    function forceStyle() {
                        const buttons = document.querySelectorAll('.simulation-modal-container [data-baseweb="select"] button');
                        buttons.forEach(function(btn) {
                            btn.style.setProperty('color', '#888888', 'important');
                            btn.style.setProperty('font-size', '0.75rem', 'important');
                            btn.style.setProperty('background-color', '#1A1A1A', 'important');
                            const all = btn.querySelectorAll('*');
                            all.forEach(function(el) {
                                el.style.setProperty('color', '#888888', 'important');
                                el.style.setProperty('font-size', '0.75rem', 'important');
                            });
                        });
                    }
                    forceStyle();
                    setInterval(forceStyle, 100);
                    new MutationObserver(forceStyle).observe(document.body, {childList: true, subtree: true});
                })();
                </script>
                """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<h3 class="simulation-title">What would you like to simulate?</h3>',
                    unsafe_allow_html=True,
                )

                # Create columns for categories
                cat_cols = st.columns(3)

                # Define categories and their options for Hedge Fund view
                hedge_categories = {
                    "Survey": ["Survey"],
                    "Marketing Content": ["Article", "Website Content", "Advertisement"],
                    "Social Media Posts": [
                        "LinkedIn Post",
                        "Instagram Post",
                        "X Post",
                        "TikTok Script",
                    ],
                    "Communication": ["Email Subject Line", "Email"],
                    "Product": ["Product Proposition"],
                }

                # Display dropdowns for each category
                for idx, (category_name, options) in enumerate(hedge_categories.items()):
                    col_idx = idx % 3
                    with cat_cols[col_idx]:
                        st.markdown(
                            f'<div class="category-title">{category_name}</div>',
                            unsafe_allow_html=True,
                        )
                        # Add "None" as first option
                        dropdown_options = ["-- Select --"] + options
                        selected = st.selectbox(
                            "",
                            dropdown_options,
                            key=f"hedge_dropdown_{category_name}",
                            label_visibility="collapsed",
                        )

                        # Update session state when an option is selected
                        if selected != "-- Select --":
                            st.session_state.selected_simulation_option = {
                                "category": category_name,
                                "option": selected,
                            }
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Show chat agent when an option is selected
                selected_cat = st.session_state.selected_simulation_option["category"]
                selected_opt = st.session_state.selected_simulation_option["option"]

                # Initialize chat history for this option if not exists
                chat_key = f"{selected_cat}_{selected_opt}"
                if chat_key not in st.session_state.simulation_chat_history:
                    st.session_state.simulation_chat_history[chat_key] = []

                # Display chat history if there are messages
                if st.session_state.simulation_chat_history[chat_key]:
                    for message in st.session_state.simulation_chat_history[chat_key]:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                # Chat input bar
                user_input = st.chat_input(
                    "type your question or hypothesis and test it on simulated users"
                )
                if user_input:
                    # Add user message to chat history
                    st.session_state.simulation_chat_history[chat_key].append(
                        {"role": "user", "content": user_input}
                    )

                    # Here you could add AI response logic
                    # For now, just echo back
                    response = f"I understand you're asking about {selected_opt} in the {selected_cat} category. Your question: '{user_input}'"

                    st.session_state.simulation_chat_history[chat_key].append(
                        {"role": "assistant", "content": response}
                    )

                    st.rerun()
