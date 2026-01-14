# Organic Manifold Implementation

## Overview

The Market Manifold visualization has been upgraded to use an **organic, graph-based approach** that creates contiguous, patchy clusters resembling a "continent-like" market landscape. This replaces the previous scattered/random point distribution with structured preference-based sub-markets.

## Key Features

### 1. **Organic Cluster Generation**
- Uses **graph-based embedding** (kNN graph + UMAP) to create contiguous regions
- **Preference regimes** define sub-markets (e.g., "Clean Indie Skincare", "Clinical Derm Skincare")
- Each cluster is generated using **mixture of Gaussians** for organic shapes
- **Bridge edges** connect clusters to form one continuous market landscape

### 2. **Cluster Boundaries**
- **Convex hulls** computed for each cluster (visual boundaries)
- Displayed as dashed lines in the 3D visualization
- Helps visualize cluster separation and overlap

### 3. **Preference-Based Labeling**
- Clusters labeled based on dominant attributes:
  - Category (Skincare, Makeup, Fragrance)
  - Price tier (Premium, Super-Premium, Ultra-Luxury)
  - Claims (clean, clinical, anti-aging, etc.)
  - Brand type (indie, heritage, luxury)
  - Channel (Sephora, DTC, Dept Store)

### 4. **Enhanced UI**
- **Cluster filter dropdown** to isolate specific sub-markets
- **Cluster legend** showing all clusters with counts and drivers
- **Hover tooltips** display cluster drivers (claims, channel, etc.)
- **Cluster boundaries** rendered as semi-transparent dashed lines

## Architecture

### Backend Components

#### `market_insight_manifold_organic.py`
- `OrganicManifoldBuilder`: Main class for building organic manifolds
- `generate_preference_clusters()`: Creates synthetic preference regimes
- `build_knn_graph()`: Builds kNN graph for structure
- `embed_with_umap()`: Projects to 2D/3D using UMAP
- `compute_cluster_hulls()`: Computes convex hulls for boundaries
- `_analyze_clusters()`: Generates cluster labels and drivers

#### API Endpoint
- `GET /api/market-insight-new/manifold/?vertical=beauty&region=US&organic=true`
- Returns:
  ```json
  {
    "points": [...],
    "clusters": [
      {
        "cluster_id": 0,
        "label": "Clean Indie Skincare",
        "count": 50,
        "drivers": {
          "category": "Skincare",
          "tier": "premium",
          "claims": ["clean", "natural"],
          "brand_type": "indie",
          "channel": "Sephora"
        }
      }
    ],
    "hulls": {
      "0": [[x1, y1], [x2, y2], ...]
    }
  }
  ```

### Frontend Components

#### `MarketManifold3D.jsx`
- Displays 3D scatter plot with cluster boundaries
- Cluster filter dropdown
- Cluster legend with drivers
- Enhanced hover tooltips

## Usage

### Rebuild Manifold

```bash
# Using organic builder (default)
python3 manage.py rebuild_market_manifold --vertical beauty --region US --organic

# With custom parameters
python3 manage.py rebuild_market_manifold \
  --vertical beauty \
  --region US \
  --organic \
  --n-points 900 \
  --k-clusters 18 \
  --seed 42

# Using legacy builder
python3 manage.py rebuild_market_manifold --vertical beauty --region US
```

### API Usage

```javascript
// Fetch manifold with clusters and hulls
const response = await fetch(
  'http://localhost:8000/api/market-insight-new/manifold/?vertical=beauty&region=US&organic=true'
);
const data = await response.json();

// Access clusters
data.clusters.forEach(cluster => {
  console.log(cluster.label, cluster.count, cluster.drivers);
});

// Access hull boundaries
Object.entries(data.hulls).forEach(([clusterId, hullPoints]) => {
  console.log(`Cluster ${clusterId} boundary:`, hullPoints);
});
```

## Preference Regimes (Beauty)

The system generates 18 preference-based clusters:

1. **Clean Indie Skincare** - Premium, clean claims, indie brands, Sephora
2. **Clinical Derm Skincare** - Super-premium, clinical claims, prestige brands, DTC
3. **Ultra-Luxury Fragrance** - Ultra-luxury, heritage claims, luxury brands, Dept Store
4. **Premium Makeup - Trend-led** - Premium, trend claims, indie brands, Sephora
5. **Entry-Premium Skincare - Hydration** - Entry-premium, hydration claims, prestige brands, Ulta
6. **Hair + Scalp Health** - Premium, scalp repair claims, prestige brands, Sephora
7. **Heritage Luxury Skincare** - Ultra-luxury, anti-aging claims, luxury brands, Dept Store
8. **Indie Clean Makeup** - Premium, clean minimal claims, indie brands, DTC
9. **Clinical Targeted Treatments** - Super-premium, clinical targeted claims, prestige brands, DTC
10. **Premium Fragrance - Modern** - Premium, modern unisex claims, indie brands, Sephora
11. **Barrier Repair Skincare** - Premium, barrier repair claims, prestige brands, Sephora
12. **Brightening Skincare** - Premium, brightening vitamin-c claims, prestige brands, Sephora
13. **Luxury Makeup - Full Coverage** - Super-premium, coverage long-wear claims, luxury brands, Dept Store
14. **Indie Skincare - Sensitive Skin** - Premium, sensitive gentle claims, indie brands, DTC
15. **Premium Eye Care** - Super-premium, anti-aging eye claims, prestige brands, Sephora
16. **Heritage Fragrance - Classic** - Ultra-luxury, heritage classic claims, luxury brands, Dept Store
17. **Indie Color Cosmetics** - Premium, color pigment claims, indie brands, Sephora
18. **Clinical Acne Solutions** - Premium, acne clinical claims, prestige brands, DTC

## Technical Details

### Graph-Based Embedding Process

1. **Generate preference clusters** in 8D latent space
   - Each regime has a center point
   - Points sampled using mixture of Gaussians
   - Creates organic, contiguous regions

2. **Build kNN graph** (k=15)
   - Connects nearby points
   - Creates structure for clustering

3. **Add bridge edges**
   - Connects clusters to form one continuous manifold
   - Creates "continent" effect

4. **Embed with UMAP**
   - Projects 8D → 3D
   - Preserves local structure
   - Creates patchy, organic shapes

5. **Re-cluster in embedded space**
   - HDBSCAN for variable cluster sizes
   - Final cluster assignments

6. **Compute hulls**
   - Convex hull for each cluster
   - Visual boundaries

### Parameters

- `n_points`: Number of points to generate (default: 900)
- `k_clusters`: Target number of clusters (default: 18)
- `seed`: Random seed for reproducibility (default: 42)
- `n_neighbors`: kNN graph parameter (default: 15)
- `min_dist`: UMAP minimum distance (default: 0.1) - lower = tighter clusters
- `spread`: UMAP spread (default: 1.0)

## Visual Result

The manifold now displays:
- **Contiguous clusters** that look like "continents" or "islands"
- **Clear boundaries** between preference regimes
- **Variable cluster sizes** (some large mainstream segments, some niche pockets)
- **Organic shapes** rather than uniform blobs
- **One connected market landscape** with distinct sub-regions

## Future Enhancements

1. **Concave hulls** (alpha shapes) for more accurate boundaries
2. **Interactive cluster highlighting** (click cluster to highlight all points)
3. **Cluster overlap visualization** (show overlapping regions)
4. **Animated cluster evolution** (show how clusters change over time)
5. **Real data integration** (replace synthetic with actual market data)
