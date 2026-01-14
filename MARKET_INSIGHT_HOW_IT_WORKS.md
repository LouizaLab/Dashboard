# How Market Insight Works

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
│  1. Opens Dashboard → Market Insight Tab                       │
│  2. Sees 2D Manifold Map (left) + Insight Workspace (right)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (Database)                         │
│  • MarketDefinition: "US Prestige Skincare | Serums"          │
│  • Brand: "Drunk Elephant", "Tatcha", etc.                     │
│  • Product: Products with claims, ingredients                  │
│  • MarketSignal: Time-series (momentum, intent, etc.)         │
│  • InnovationEvent: Launches, campaigns                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              MANIFOLD COMPUTATION (One-Time Setup)               │
│                                                                   │
│  1. For each Market/Brand/Product:                               │
│     • Build text summary: "US Beauty | Skincare | Premium..."   │
│     • Generate embedding (384-dim vector)                        │
│     • Compute features (8-dim: momentum, signals, etc.)          │
│     • Combine: 384 + 8 = 392 dimensions                          │
│                                                                   │
│  2. Project to 2D:                                               │
│     • Use UMAP to reduce 392-dim → 2D (x, y coordinates)        │
│     • Similar markets cluster together                           │
│                                                                   │
│  3. Cluster:                                                      │
│     • HDBSCAN groups similar nodes                               │
│     • Label clusters: "Skincare Premium", "Indie Brands", etc.  │
│                                                                   │
│  4. Store:                                                        │
│     • Save (x, y, cluster_id) in ManifoldPoint table            │
│     • Cache for fast retrieval                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              VISUALIZATION (Frontend - D3.js)                    │
│                                                                   │
│  GET /api/market-insight-new/manifold/                           │
│    ↓                                                              │
│  Returns: [{id, type, label, x, y, cluster_id, ...}]           │
│    ↓                                                              │
│  D3.js renders scatter plot:                                     │
│    • Each point = market/brand/product                           │
│    • Color = cluster                                             │
│    • Size = selected/pinned status                               │
│    • Filters: category, tier, momentum                           │
│    • Click → show details                                        │
│    • Shift+Click → pin for context                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              QUESTION ANSWERING (Insight Engine)                 │
│                                                                   │
│  User asks: "What categories should we prioritize?"             │
│    ↓                                                              │
│  POST /api/market-insight-new/ask/                               │
│    ↓                                                              │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ AGENT 1: EXPLORER                                        │    │
│  │ • Searches markets matching question keywords            │    │
│  │ • Retrieves relevant brands, products, signals           │    │
│  │ • Gets innovation events                                  │    │
│  │ Returns: {markets: [...], brands: [...], signals: [...]}│    │
│  └──────────────────────────────────────────────────────────┘    │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ AGENT 2: ANALYST                                          │    │
│  │ • Analyzes Case 2 template (Beauty Portfolio Strategy) │    │
│  │ • Computes category importance scores                     │    │
│  │ • Analyzes tier evolution (trade up/down)                │    │
│  │ • Examines competitor positioning                         │    │
│  │ • Identifies innovation patterns                          │    │
│  │ Returns: Structured analysis with recommendations          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ AGENT 3: CRITIC                                           │    │
│  │ • Checks evidence coverage (enough data?)               │    │
│  │ • Looks for conflicting signals                          │    │
│  │ • Flags uncertainty                                       │    │
│  │ Returns: {flags: [...], uncertainty_factors: [...]}      │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ AGENT 4: ANCHORING                                        │    │
│  │ • Attaches evidence (links to markets/brands used)       │    │
│  │ • Computes confidence score (1-5) based on:              │    │
│  │   - Evidence coverage                                     │    │
│  │   - Critic flags                                           │    │
│  │ • Computes entropy score (0-1) based on:                │    │
│  │   - Signal dispersion                                      │    │
│  │   - Uncertainty factors                                    │    │
│  │ • Generates plain-English rationale                       │    │
│  │ Returns: Final structured answer with confidence          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              ↓                                    │
│  Response JSON:                                                   │
│  {                                                               │
│    "executive_summary": ["...", "..."],                          │
│    "answers": {...},                                             │
│    "recommended_actions": {"now": [...], "next": [...]},        │
│    "confidence": {"score": 4, "entropy": 0.3, "rationale": "..."},│
│    "evidence": [{"type": "market", "id": "...", "label": "..."}]│
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESULTS DISPLAY (Frontend)                          │
│                                                                   │
│  • Executive Summary (bullets)                                  │
│  • Category Importance Analysis                                  │
│  • Recommended Actions (now/next/3-5y)                          │
│  • Confidence & Entropy bars                                    │
│  • Evidence panel (clickable links back to manifold)           │
│  • Risks & Watchouts                                             │
│  • Next Questions                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Step-by-Step: Building the Manifold

### 1. **Data Preparation**
```python
# Seed data creates:
- 30+ brands (Chanel, Dior, Drunk Elephant, etc.)
- 15-25 markets ("US Prestige Skincare | Serums | Premium")
- Products with claims, ingredients, pricing
- Time-series signals (momentum, intent, elasticity)
- Innovation events (launches, campaigns)
```

### 2. **Text Summarization**
For each market:
```
"US Prestige Skincare | Serums | Vitamin C | Premium | Sephora-heavy | momentum high | clean+clinical"
```

### 3. **Embedding Generation**
```python
# Option A: Real embedding (sentence-transformers)
embedding = model.encode(text)  # 384 dimensions

# Option B: Mock embedding (deterministic hash-based)
embedding = hash_to_vector(text)  # 384 dimensions
```

### 4. **Feature Extraction**
```python
# Market features (8 dimensions):
features = [
    intent_index,           # 0.5-0.9
    price_elasticity,        # 0.5-2.0
    trend_momentum,         # -0.2 to 0.5
    social_velocity,        # 0.1-1.0
    search_share,           # 0.05-0.3
    review_sentiment,        # 0.4-0.95
    innovation_density,     # 0.0-1.0
    heritage_share          # 0.0-1.0
]
```

### 5. **Combination**
```python
combined = np.concatenate([embedding, features])
# Result: 384 + 8 = 392 dimensions per node
```

### 6. **2D Projection**
```python
# UMAP reduces 392-dim → 2D
reducer = UMAP(n_components=2)
coords_2d = reducer.fit_transform(combined)
# Result: (x, y) coordinates for each node
```

### 7. **Clustering**
```python
# HDBSCAN finds natural clusters
clusterer = HDBSCAN(min_cluster_size=2)
cluster_labels = clusterer.fit_predict(combined)
# Result: Cluster IDs like "Skincare Premium", "Indie Brands"
```

### 8. **Storage**
```python
ManifoldPoint.objects.create(
    node_type='market',
    node_id=market.id,
    x=0.234,
    y=-0.567,
    cluster_id=3,
    cluster_label="Skincare Premium"
)
```

## Step-by-Step: Answering a Question

### Example: "What categories should we prioritize?"

**1. Explorer Agent:**
```python
# Searches for markets matching keywords
markets = MarketDefinition.objects.filter(
    vertical='beauty',
    category__icontains='Skincare'  # or 'Makeup', 'Fragrance'
)

# Gets signals
signals = MarketSignal.objects.filter(market__in=markets)

# Gets innovation events
events = InnovationEvent.objects.filter(market__in=markets)

# Returns: {markets: [...], signals: [...], events: [...]}
```

**2. Analyst Agent:**
```python
# Analyzes Case 2 template
category_importance = {}
for market in markets:
    # Get momentum from signals
    momentum = signals.filter(market=market).first().trend_momentum
    
    # Count innovation events
    event_count = events.filter(market=market).count()
    
    category_importance[market.category] = {
        'importance': 'High' if momentum > 0.3 else 'Medium',
        'growth': momentum,
        'innovation_density': event_count
    }

# Returns structured analysis
```

**3. Critic Agent:**
```python
# Checks evidence quality
evidence_count = len(markets) + len(signals)
if evidence_count < 5:
    flags.append('Limited evidence coverage')

# Checks for conflicts
momentums = [s.trend_momentum for s in signals]
if max(momentums) - min(momentums) > 0.5:
    flags.append('Conflicting momentum signals')

# Returns: {flags: [...], uncertainty_factors: [...]}
```

**4. Anchoring Agent:**
```python
# Computes confidence (1-5)
confidence_score = min(5, max(1, 1 + (evidence_count // 5)))
if flags:
    confidence_score -= len(flags)

# Computes entropy (0-1)
momentum_std = np.std(momentums)
entropy_score = min(1.0, momentum_std / 0.5)

# Attaches evidence
evidence = [
    {'type': 'market', 'id': str(m.id), 'label': m.name}
    for m in markets[:10]
]

# Returns final answer with confidence
```

## Key Concepts

### **Manifold = Market Map**
- Think of it as a "geographic map" of markets
- Similar markets cluster together (like cities on a map)
- Distance = similarity
- Clusters = market segments

### **Embeddings = Semantic Understanding**
- Text → Vector captures meaning
- "Skincare Premium" and "Face Creams Premium" → close vectors
- Enables similarity search

### **Features = Quantitative Signals**
- Momentum, intent, elasticity = market health indicators
- Innovation density = activity level
- Heritage share = competitive landscape

### **Multi-Agent = Specialized Roles**
- **Explorer**: "What data exists?"
- **Analyst**: "What does it mean?"
- **Critic**: "Is this reliable?"
- **Anchoring**: "How confident are we?"

### **Confidence & Entropy**
- **Confidence (1-5)**: How much evidence do we have?
- **Entropy (0-1)**: How uncertain are the outcomes?
- Low entropy = consistent signals = reliable
- High entropy = conflicting signals = uncertain

## Example Output

```json
{
  "title": "Market Insight: What categories should we prioritize?",
  "executive_summary": [
    "Serums and targeted treatments show highest strategic importance (45% YoY growth)",
    "Premium tier is expanding; super-premium showing trade-up momentum",
    "Indie brands driving innovation in clean claims and new formats"
  ],
  "answers": {
    "category_importance": {
      "Skincare": {"importance": "High", "growth": 0.45},
      "Makeup": {"importance": "Medium", "growth": 0.18},
      "Fragrance": {"importance": "High", "growth": 0.32}
    }
  },
  "recommended_actions": {
    "now": [
      "Prioritize Skincare serums in super-premium tier",
      "Launch targeted treatment format with clean claims"
    ],
    "next": [
      "Consider fragrance expansion in premium tier"
    ]
  },
  "confidence": {
    "score": 4,
    "entropy": 0.3,
    "rationale": "High confidence based on strong evidence coverage. Low uncertainty with consistent signals."
  },
  "evidence": [
    {"type": "market", "id": "...", "label": "US Prestige Skincare | Serums | Premium"},
    {"type": "brand", "id": "...", "label": "Drunk Elephant"}
  ]
}
```

## Why This Works

1. **Visual Exploration**: Manifold map lets consultants explore markets spatially
2. **Structured Answers**: Multi-agent system ensures thorough, reliable analysis
3. **Evidence-Based**: Every answer links back to source data
4. **Confidence Scoring**: Consultants know how reliable each insight is
5. **Case Templates**: Pre-built templates for common questions (Case 1, Case 2)
6. **Mock Mode**: Works without external APIs for demos

## Next Steps to Try

1. **Explore the Manifold**: Filter by category, click nodes, see clusters
2. **Pin Nodes**: Shift+Click to pin markets for context
3. **Ask Case 2**: Select Case 2 template, click Ask
4. **Review Evidence**: Click evidence links to see source markets
5. **Check Confidence**: Look at confidence/entropy scores

The system is designed to be **consultant-friendly**: clear, structured, evidence-backed, with confidence indicators.
