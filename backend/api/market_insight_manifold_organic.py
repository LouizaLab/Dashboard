"""
Organic Manifold Generator - Creates contiguous, patchy clusters using graph-based approach.
This produces the "continent-like" manifold visualization with clear sub-cluster boundaries.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from django.db.models import Q, Avg, Count
from .market_insight_models import (
    MarketDefinition, Brand, Product, ManifoldPoint, MarketSignal, InnovationEvent
)

try:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import HDBSCAN, KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available.")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("Warning: umap-learn not available.")

try:
    from scipy.spatial import ConvexHull
    from scipy.spatial.qhull import QhullError
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available for convex hull computation.")


class OrganicManifoldBuilder:
    """
    Builds organic, contiguous manifolds using graph-based embedding.
    Creates preference-based clusters that look like "continents" with clear boundaries.
    """
    
    def __init__(self, vertical='beauty', region='US', seed=42, n_points=900, k_clusters=18):
        self.vertical = vertical
        self.region = region
        self.seed = seed
        self.n_points = n_points
        self.k_clusters = k_clusters
        np.random.seed(seed)
        
    def generate_preference_clusters(self) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generate synthetic preference-based clusters in latent space.
        Returns: (feature_matrix, node_metadata_list)
        """
        nodes = []
        node_metadata = []
        
        # Define preference regimes (sub-markets)
        preference_regimes = self._define_preference_regimes()
        
        # Generate points for each regime
        points_per_cluster = self.n_points // len(preference_regimes)
        remaining = self.n_points % len(preference_regimes)
        
        for i, regime in enumerate(preference_regimes):
            n_points_regime = points_per_cluster + (1 if i < remaining else 0)
            
            # Generate points in this regime's latent space
            regime_points, regime_metadata = self._sample_from_regime(
                regime, n_points_regime, i
            )
            
            nodes.extend(regime_points)
            node_metadata.extend(regime_metadata)
        
        return np.array(nodes), node_metadata
    
    def _define_preference_regimes(self) -> List[Dict]:
        """Define preference-based market regimes (sub-clusters)."""
        if self.vertical == 'beauty':
            return [
                {'label': 'Clean Indie Skincare', 'category': 'Skincare', 'tier': 'premium',
                 'claims': ['clean', 'natural'], 'brand_type': 'indie', 'channel': 'Sephora',
                 'latent_center': [0.2, 0.1, 0.3, 0.4, 0.2, 0.6, 0.3, 0.4]},
                {'label': 'Clinical Derm Skincare', 'category': 'Skincare', 'tier': 'super_premium',
                 'claims': ['clinical', 'anti-aging'], 'brand_type': 'prestige', 'channel': 'DTC',
                 'latent_center': [0.7, 0.8, 0.6, 0.3, 0.5, 0.4, 0.7, 0.3]},
                {'label': 'Ultra-Luxury Fragrance', 'category': 'Fragrance', 'tier': 'ultra_luxury',
                 'claims': ['luxury', 'heritage'], 'brand_type': 'luxury', 'channel': 'Dept',
                 'latent_center': [0.9, 0.9, 0.2, 0.1, 0.1, 0.3, 0.1, 0.9]},
                {'label': 'Premium Makeup - Trend-led', 'category': 'Makeup', 'tier': 'premium',
                 'claims': ['trend', 'color'], 'brand_type': 'indie', 'channel': 'Sephora',
                 'latent_center': [0.3, 0.4, 0.8, 0.7, 0.6, 0.5, 0.4, 0.2]},
                {'label': 'Entry-Premium Skincare - Hydration', 'category': 'Skincare', 'tier': 'entry_premium',
                 'claims': ['hydration', 'barrier'], 'brand_type': 'prestige', 'channel': 'Ulta',
                 'latent_center': [0.4, 0.3, 0.4, 0.5, 0.4, 0.5, 0.3, 0.3]},
                {'label': 'Hair + Scalp Health', 'category': 'Hair', 'tier': 'premium',
                 'claims': ['scalp', 'repair'], 'brand_type': 'prestige', 'channel': 'Sephora',
                 'latent_center': [0.5, 0.5, 0.5, 0.6, 0.5, 0.4, 0.5, 0.4]},
                {'label': 'Heritage Luxury Skincare', 'category': 'Skincare', 'tier': 'ultra_luxury',
                 'claims': ['anti-aging', 'luxury'], 'brand_type': 'luxury', 'channel': 'Dept',
                 'latent_center': [0.85, 0.85, 0.3, 0.2, 0.2, 0.4, 0.2, 0.85]},
                {'label': 'Indie Clean Makeup', 'category': 'Makeup', 'tier': 'premium',
                 'claims': ['clean', 'minimal'], 'brand_type': 'indie', 'channel': 'DTC',
                 'latent_center': [0.25, 0.35, 0.75, 0.65, 0.55, 0.6, 0.35, 0.25]},
                {'label': 'Clinical Targeted Treatments', 'category': 'Skincare', 'tier': 'super_premium',
                 'claims': ['clinical', 'targeted'], 'brand_type': 'prestige', 'channel': 'DTC',
                 'latent_center': [0.75, 0.75, 0.55, 0.35, 0.45, 0.35, 0.75, 0.25]},
                {'label': 'Premium Fragrance - Modern', 'category': 'Fragrance', 'tier': 'premium',
                 'claims': ['modern', 'unisex'], 'brand_type': 'indie', 'channel': 'Sephora',
                 'latent_center': [0.6, 0.6, 0.3, 0.4, 0.3, 0.4, 0.3, 0.5]},
                {'label': 'Barrier Repair Skincare', 'category': 'Skincare', 'tier': 'premium',
                 'claims': ['barrier', 'repair'], 'brand_type': 'prestige', 'channel': 'Sephora',
                 'latent_center': [0.45, 0.4, 0.45, 0.55, 0.45, 0.5, 0.4, 0.35]},
                {'label': 'Brightening Skincare', 'category': 'Skincare', 'tier': 'premium',
                 'claims': ['brightening', 'vitamin-c'], 'brand_type': 'prestige', 'channel': 'Sephora',
                 'latent_center': [0.5, 0.45, 0.5, 0.6, 0.5, 0.55, 0.45, 0.4]},
                {'label': 'Luxury Makeup - Full Coverage', 'category': 'Makeup', 'tier': 'super_premium',
                 'claims': ['coverage', 'long-wear'], 'brand_type': 'luxury', 'channel': 'Dept',
                 'latent_center': [0.8, 0.75, 0.85, 0.8, 0.7, 0.6, 0.5, 0.6]},
                {'label': 'Indie Skincare - Sensitive Skin', 'category': 'Skincare', 'tier': 'premium',
                 'claims': ['sensitive', 'gentle'], 'brand_type': 'indie', 'channel': 'DTC',
                 'latent_center': [0.3, 0.25, 0.35, 0.45, 0.3, 0.65, 0.3, 0.3]},
                {'label': 'Premium Eye Care', 'category': 'Skincare', 'tier': 'super_premium',
                 'claims': ['anti-aging', 'eye'], 'brand_type': 'prestige', 'channel': 'Sephora',
                 'latent_center': [0.65, 0.7, 0.4, 0.4, 0.35, 0.45, 0.4, 0.5]},
                {'label': 'Heritage Fragrance - Classic', 'category': 'Fragrance', 'tier': 'ultra_luxury',
                 'claims': ['heritage', 'classic'], 'brand_type': 'luxury', 'channel': 'Dept',
                 'latent_center': [0.95, 0.95, 0.15, 0.1, 0.05, 0.25, 0.05, 0.95]},
                {'label': 'Indie Color Cosmetics', 'category': 'Makeup', 'tier': 'premium',
                 'claims': ['color', 'pigment'], 'brand_type': 'indie', 'channel': 'Sephora',
                 'latent_center': [0.35, 0.45, 0.85, 0.8, 0.7, 0.55, 0.45, 0.2]},
                {'label': 'Clinical Acne Solutions', 'category': 'Skincare', 'tier': 'premium',
                 'claims': ['acne', 'clinical'], 'brand_type': 'prestige', 'channel': 'DTC',
                 'latent_center': [0.7, 0.7, 0.6, 0.4, 0.5, 0.3, 0.7, 0.2]},
            ]
        else:
            # Food regimes
            return [
                {'label': 'Functional Protein Bars', 'category': 'Bars', 'tier': 'premium',
                 'claims': ['protein', 'functional'], 'brand_type': 'prestige', 'channel': 'Amazon',
                 'latent_center': [0.5, 0.6, 0.4, 0.5, 0.5, 0.4, 0.5, 0.3]},
                {'label': 'Clean Snack Bars', 'category': 'Bars', 'tier': 'premium',
                 'claims': ['clean', 'natural'], 'brand_type': 'indie', 'channel': 'DTC',
                 'latent_center': [0.3, 0.4, 0.3, 0.4, 0.3, 0.5, 0.3, 0.2]},
                # Add more food regimes as needed
            ]
    
    def _sample_from_regime(self, regime: Dict, n_points: int, cluster_id: int) -> Tuple[List, List]:
        """
        Sample points from a preference regime using mixture of Gaussians.
        Creates organic, contiguous regions.
        """
        center = np.array(regime['latent_center'])
        points = []
        metadata = []
        
        # Use mixture of 2-3 Gaussians per cluster for organic shape
        n_components = 2 + (cluster_id % 2)  # Vary between 2 and 3
        
        for i in range(n_points):
            # Choose which Gaussian component
            component = i % n_components
            
            # Offset from center (creates sub-structure)
            offset = np.array([
                np.sin(component * np.pi / n_components) * 0.15,
                np.cos(component * np.pi / n_components) * 0.15,
                0, 0, 0, 0, 0, 0
            ])
            
            # Sample from Gaussian with variance
            variance = 0.08 + (component * 0.02)  # Vary variance
            point = center + offset + np.random.normal(0, variance, 8)
            
            # Clip to [0, 1]
            point = np.clip(point, 0, 1)
            
            points.append(point)
            
            # Create metadata
            metadata.append({
                'cluster_id': cluster_id,
                'cluster_label': regime['label'],
                'category': regime['category'],
                'tier': regime['tier'],
                'claims': regime['claims'],
                'brand_type': regime['brand_type'],
                'channel': regime['channel'],
            })
        
        return points, metadata
    
    def build_knn_graph(self, X: np.ndarray, k: int = 15) -> np.ndarray:
        """
        Build kNN graph to connect nearby points.
        This creates the structure for contiguous clusters.
        """
        if not SKLEARN_AVAILABLE:
            return None
        
        nbrs = NearestNeighbors(n_neighbors=k, metric='euclidean')
        nbrs.fit(X)
        distances, indices = nbrs.kneighbors(X)
        
        return indices
    
    def add_bridge_edges(self, X: np.ndarray, cluster_ids: np.ndarray, 
                         n_bridges: int = 5) -> np.ndarray:
        """
        Add bridge edges between clusters to connect the global manifold.
        """
        unique_clusters = np.unique(cluster_ids[cluster_ids >= 0])
        if len(unique_clusters) < 2:
            return X
        
        # Find cluster centroids
        centroids = {}
        for cid in unique_clusters:
            mask = cluster_ids == cid
            centroids[cid] = np.mean(X[mask], axis=0)
        
        # Add small perturbations to connect clusters
        # This creates the "continent" effect
        for i in range(min(n_bridges, len(unique_clusters) - 1)):
            c1, c2 = unique_clusters[i], unique_clusters[i + 1]
            # Add a few points between clusters
            mid_point = (centroids[c1] + centroids[c2]) / 2
            X = np.vstack([X, mid_point + np.random.normal(0, 0.05, (1, X.shape[1]))])
        
        return X
    
    def embed_with_umap(self, X: np.ndarray, n_components: int = 3) -> np.ndarray:
        """
        Embed using UMAP to get the organic, patchy manifold shape.
        """
        if not UMAP_AVAILABLE:
            # Fallback to PCA
            from sklearn.decomposition import PCA
            pca = PCA(n_components=n_components, random_state=self.seed)
            return pca.fit_transform(X)
        
        # UMAP parameters tuned for organic clusters
        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=min(15, len(X) - 1),
            min_dist=0.1,  # Lower = tighter clusters
            spread=1.0,
            random_state=self.seed,
            metric='euclidean'
        )
        
        return reducer.fit_transform(X)
    
    def compute_cluster_hulls(self, coords: np.ndarray, cluster_ids: np.ndarray) -> Dict[int, np.ndarray]:
        """
        Compute convex hulls (boundaries) for each cluster.
        Returns: {cluster_id: hull_points}
        """
        hulls = {}
        
        if not SCIPY_AVAILABLE:
            return hulls
        
        unique_clusters = np.unique(cluster_ids[cluster_ids >= 0])
        
        for cid in unique_clusters:
            mask = cluster_ids == cid
            cluster_points = coords[mask]
            
            if len(cluster_points) < 3:
                continue
            
            try:
                # Use 2D coordinates for hull (x, y)
                if coords.shape[1] >= 2:
                    points_2d = cluster_points[:, :2]
                    hull = ConvexHull(points_2d)
                    hulls[cid] = points_2d[hull.vertices]
            except QhullError:
                # Skip if hull computation fails
                continue
        
        return hulls
    
    def build_organic_manifold(self, force_rebuild=False):
        """
        Main method: Build organic manifold with contiguous clusters.
        Returns: (points, hulls, cluster_info)
        """
        # Check cache
        existing_points = ManifoldPoint.objects.filter(
            vertical=self.vertical,
            region=self.region
        )
        if existing_points.exists() and not force_rebuild:
            print(f"Using cached manifold for {self.vertical}/{self.region}")
            # Return empty hulls and cluster_info for cached data
            # (These will be computed from the points if needed)
            return existing_points, {}, {}
        
        print(f"Building organic manifold for {self.vertical}/{self.region}...")
        
        # Step 1: Generate preference-based clusters in latent space
        X_latent, node_metadata = self.generate_preference_clusters()
        print(f"Generated {len(X_latent)} points in {len(set(m['cluster_id'] for m in node_metadata))} preference regimes")
        
        # Step 2: Build kNN graph (for structure)
        knn_graph = self.build_knn_graph(X_latent, k=15)
        
        # Step 3: Initial clustering in latent space
        if SKLEARN_AVAILABLE:
            # Use HDBSCAN for variable cluster sizes
            clusterer = HDBSCAN(
                min_cluster_size=max(3, len(X_latent) // 30),
                min_samples=2,
                metric='euclidean'
            )
            cluster_ids_latent = clusterer.fit_predict(X_latent)
        else:
            cluster_ids_latent = np.zeros(len(X_latent), dtype=int)
        
        # Step 4: Add bridge edges to connect clusters
        X_latent = self.add_bridge_edges(X_latent, cluster_ids_latent, n_bridges=8)
        
        # Step 5: Embed to 2D/3D using UMAP
        coords = self.embed_with_umap(X_latent, n_components=3)
        
        # Step 6: Re-cluster in embedded space for final labels
        if SKLEARN_AVAILABLE:
            clusterer_final = HDBSCAN(
                min_cluster_size=max(3, len(coords) // 25),
                min_samples=2
            )
            cluster_ids = clusterer_final.fit_predict(coords)
        else:
            # Fallback: use original cluster IDs
            cluster_ids = np.concatenate([cluster_ids_latent, 
                                          np.full(len(coords) - len(cluster_ids_latent), -1)])
        
        # Step 7: Compute cluster hulls (boundaries)
        hulls = self.compute_cluster_hulls(coords, cluster_ids)
        
        # Step 8: Generate cluster labels and drivers
        cluster_info = self._analyze_clusters(node_metadata, cluster_ids)
        
        # Step 9: Store results
        ManifoldPoint.objects.filter(vertical=self.vertical, region=self.region).delete()
        
        # Generate UUIDs for synthetic nodes
        import uuid
        import hashlib
        
        manifold_points = []
        for i, (metadata, coord, cid) in enumerate(zip(node_metadata[:len(coords)], coords[:len(node_metadata)], cluster_ids[:len(node_metadata)])):
            cluster_label = cluster_info.get(int(cid), {}).get('label', metadata.get('cluster_label', f'Cluster {cid}'))
            
            # Generate a deterministic UUID for synthetic nodes
            node_id = metadata.get('node_id')
            if node_id is None:
                # Create deterministic UUID from metadata
                id_str = f"{self.vertical}_{self.region}_{i}_{metadata.get('cluster_label', '')}"
                node_id = uuid.UUID(hashlib.md5(id_str.encode()).hexdigest()[:32])
            
            point = ManifoldPoint.objects.create(
                node_type='market',  # For now, all synthetic points are markets
                node_id=node_id,
                x=float(coord[0]),
                y=float(coord[1]),
                z=float(coord[2]) if len(coord) > 2 else 0.0,
                cluster_id=int(cid) if cid >= 0 else None,
                cluster_label=cluster_label,
                vertical=self.vertical,
                region=self.region,
            )
            manifold_points.append(point)
        
        print(f"Built organic manifold: {len(manifold_points)} points, "
              f"{len(set(cid for cid in cluster_ids if cid >= 0))} clusters")
        
        return ManifoldPoint.objects.filter(vertical=self.vertical, region=self.region), hulls, cluster_info
    
    def _analyze_clusters(self, node_metadata: List[Dict], cluster_ids: np.ndarray) -> Dict[int, Dict]:
        """
        Analyze clusters to generate labels and drivers.
        """
        cluster_groups = {}
        for i, cid in enumerate(cluster_ids):
            if cid not in cluster_groups:
                cluster_groups[cid] = []
            if i < len(node_metadata):
                cluster_groups[cid].append(node_metadata[i])
        
        cluster_info = {}
        for cid, nodes in cluster_groups.items():
            if cid < 0 or len(nodes) == 0:
                continue
            
            # Extract dominant attributes
            categories = [n.get('category', '') for n in nodes]
            tiers = [n.get('tier', '') for n in nodes]
            claims_list = [n.get('claims', []) for n in nodes]
            brand_types = [n.get('brand_type', '') for n in nodes]
            channels = [n.get('channel', '') for n in nodes]
            
            # Find most common
            top_category = max(set(categories), key=categories.count) if categories else 'Unknown'
            top_tier = max(set(tiers), key=tiers.count) if tiers else 'premium'
            top_brand_type = max(set(brand_types), key=brand_types.count) if brand_types else 'prestige'
            top_channel = max(set(channels), key=channels.count) if channels else 'Sephora'
            
            # Flatten claims
            all_claims = [c for sublist in claims_list for c in (sublist if isinstance(sublist, list) else [sublist])]
            top_claims = []
            if all_claims:
                claim_counts = {c: all_claims.count(c) for c in set(all_claims)}
                top_claims = sorted(claim_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                top_claims = [c for c, _ in top_claims]
            
            # Generate label
            label = nodes[0].get('cluster_label', f'{top_category} {top_tier.replace("_", " ").title()}')
            
            cluster_info[int(cid)] = {
                'label': label,
                'count': len(nodes),
                'drivers': {
                    'category': top_category,
                    'tier': top_tier,
                    'claims': top_claims,
                    'brand_type': top_brand_type,
                    'channel': top_channel,
                },
                'centroid': None,  # Will be computed from coordinates
            }
        
        return cluster_info
