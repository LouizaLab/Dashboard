"""
Market Manifold computation pipeline.
Builds 2D embeddings for markets, brands, and products using UMAP projection.
"""
import numpy as np
from typing import List, Dict, Tuple
from django.db.models import Q, Avg
from .market_insight_models import (
    MarketDefinition, Brand, Product, ManifoldPoint, MarketSignal, InnovationEvent
)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available. Using mock embeddings.")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("Warning: umap-learn not available. Using mock projection.")

try:
    from sklearn.cluster import KMeans, HDBSCAN
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using mock clustering.")


class ManifoldBuilder:
    """Builds and caches market manifolds."""
    
    def __init__(self, vertical='beauty', region='US', use_cache=True):
        self.vertical = vertical
        self.region = region
        self.use_cache = use_cache
        
        # Initialize embedding model (with fallback)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except:
                self.embedder = None
        else:
            self.embedder = None
    
    def build_text_summary(self, node_type: str, node_data: Dict) -> str:
        """Build canonical text summary for a node."""
        if node_type == 'market':
            market = node_data['object']
            # Get recent signals
            recent_signals = MarketSignal.objects.filter(market=market).order_by('-date')[:3]
            momentum = recent_signals[0].trend_momentum if recent_signals else 0.0
            
            # Get innovation density
            recent_events = InnovationEvent.objects.filter(market=market).count()
            
            # Build summary
            summary_parts = [
                f"{market.region} {market.vertical.title()}",
                market.category,
                market.sub_category or "",
                market.price_tier.replace('_', ' ') if market.price_tier else "",
            ]
            
            # Add channel info
            if market.channel_mix:
                top_channels = sorted(market.channel_mix.items(), key=lambda x: x[1], reverse=True)[:2]
                channel_str = "+".join([ch for ch, _ in top_channels])
                summary_parts.append(f"{channel_str}-heavy")
            
            # Add momentum
            if momentum > 0.2:
                summary_parts.append("momentum high")
            elif momentum < -0.1:
                summary_parts.append("momentum declining")
            
            # Add tags
            if market.tags:
                summary_parts.extend(market.tags[:3])
            
            return " | ".join([p for p in summary_parts if p])
        
        elif node_type == 'brand':
            brand = node_data['object']
            # Get product mix
            products = Product.objects.filter(brand=brand)
            categories = products.values_list('category', flat=True).distinct()
            avg_price = products.aggregate(avg=Avg('price'))['avg'] or 0
            
            summary_parts = [
                brand.name,
                brand.get_brand_type_display(),
            ]
            
            if brand.positioning_tags:
                summary_parts.extend(brand.positioning_tags[:3])
            
            if categories:
                summary_parts.append(f"products: {', '.join(categories[:2])}")
            
            return " | ".join(summary_parts)
        
        elif node_type == 'product':
            product = node_data['object']
            summary_parts = [
                product.brand.name,
                product.name,
                product.category,
                product.sub_category or "",
                product.price_tier or "",
            ]
            
            if product.claims:
                summary_parts.extend(product.claims[:2])
            
            return " | ".join([p for p in summary_parts if p])
        
        return ""
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text."""
        if self.embedder:
            return self.embedder.encode(text)
        else:
            # Mock embedding (deterministic hash-based)
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            # Generate 384-dim vector from hash
            seed = int(hash_obj.hexdigest()[:8], 16)
            np.random.seed(seed)
            return np.random.randn(384).astype(np.float32)
    
    def compute_market_features(self, market: MarketDefinition) -> np.ndarray:
        """Compute feature vector for a market. Returns fixed-size vector."""
        # Get recent signals
        recent_signals = MarketSignal.objects.filter(market=market).order_by('-date')[:1]
        if recent_signals:
            signal = recent_signals[0]
            features = [
                signal.intent_index or 0.5,
                abs(signal.price_elasticity_proxy or -1.0),
                signal.trend_momentum or 0.0,
                signal.social_velocity or 0.5,
                signal.search_share_proxy or 0.1,
                signal.review_sentiment_proxy or 0.7,
            ]
        else:
            features = [0.5, 1.0, 0.0, 0.5, 0.1, 0.7]
        
        # Innovation density
        event_count = InnovationEvent.objects.filter(market=market).count()
        features.append(min(event_count / 10.0, 1.0))  # Normalize
        
        # Competitor composition (heritage vs indie)
        if market.competitor_set:
            competitor_brands = Brand.objects.filter(id__in=market.competitor_set)
            heritage_count = competitor_brands.filter(brand_type__in=['heritage', 'luxury']).count()
            indie_count = competitor_brands.filter(brand_type='indie').count()
            total = len(competitor_brands)
            if total > 0:
                heritage_share = heritage_count / total
                features.append(heritage_share)
            else:
                features.append(0.5)
        else:
            features.append(0.5)
        
        # Pad to fixed size (8 features) to match other node types
        # This ensures all feature vectors have the same dimension
        while len(features) < 8:
            features.append(0.0)
        
        return np.array(features[:8])  # Ensure exactly 8 features
    
    def compute_brand_features(self, brand: Brand) -> np.ndarray:
        """Compute feature vector for a brand. Returns fixed-size vector (8 features)."""
        products = Product.objects.filter(brand=brand)
        
        # Product mix features
        categories = products.values_list('category', flat=True).distinct()
        category_count = len(categories)
        
        # Average tier (numeric)
        tier_map = {'entry_premium': 1, 'premium': 2, 'super_premium': 3, 'ultra_luxury': 4, 'clinical': 2.5}
        avg_tier = 0
        if products.exists():
            tiers = [tier_map.get(p.price_tier, 2) for p in products if p.price_tier]
            avg_tier = sum(tiers) / len(tiers) if tiers else 2
        
        # Channel footprint
        channels = products.values_list('channel', flat=True).distinct()
        channel_count = len(channels)
        
        features = [
            category_count / 3.0,  # Normalize
            avg_tier / 4.0,  # Normalize
            channel_count / 3.0,  # Normalize
        ]
        
        # Brand type encoding
        type_map = {'heritage': 0, 'indie': 1, 'mass': 2, 'prestige': 0.5, 'luxury': 0.25}
        features.append(type_map.get(brand.brand_type, 0.5))
        
        # Pad to fixed size (8 features) to match market features
        # Add placeholder features for signals that brands don't have
        while len(features) < 8:
            features.append(0.0)
        
        return np.array(features[:8])  # Ensure exactly 8 features
    
    def build_manifold(self, force_rebuild=False):
        """Build the manifold for markets, brands, and products."""
        # Check cache
        if self.use_cache and not force_rebuild:
            existing_points = ManifoldPoint.objects.filter(
                vertical=self.vertical,
                region=self.region
            )
            if existing_points.exists():
                print(f"Using cached manifold for {self.vertical}/{self.region}")
                return existing_points
        
        print(f"Building manifold for {self.vertical}/{self.region}...")
        
        # Collect nodes
        nodes = []
        node_data_list = []
        
        # Markets
        markets = MarketDefinition.objects.filter(vertical=self.vertical, region=self.region)
        for market in markets:
            text = self.build_text_summary('market', {'object': market})
            embedding = self.get_embedding(text)
            features = self.compute_market_features(market)
            # Combine embedding and features
            combined = np.concatenate([embedding, features])
            nodes.append(combined)
            node_data_list.append({
                'type': 'market',
                'id': market.id,
                'object': market,
                'label': market.name,
            })
        
        # Brands (only for beauty for now)
        if self.vertical == 'beauty':
            brands = Brand.objects.all()[:50]  # Limit for performance
            for brand in brands:
                text = self.build_text_summary('brand', {'object': brand})
                embedding = self.get_embedding(text)
                features = self.compute_brand_features(brand)
                combined = np.concatenate([embedding, features])
                nodes.append(combined)
                node_data_list.append({
                    'type': 'brand',
                    'id': brand.id,
                    'object': brand,
                    'label': brand.name,
                })
        
        if not nodes:
            print("No nodes found to build manifold")
            return ManifoldPoint.objects.none()
        
        # Stack into matrix
        X = np.vstack(nodes)
        
        # Normalize
        if SKLEARN_AVAILABLE:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # Project to 3D with UMAP
        if UMAP_AVAILABLE:
            reducer = umap.UMAP(n_components=3, random_state=42, n_neighbors=min(15, len(nodes)-1))
            coords_3d = reducer.fit_transform(X_scaled)
        else:
            # Mock projection (PCA-like) to 3D
            from sklearn.decomposition import PCA
            pca = PCA(n_components=3, random_state=42)
            coords_3d = pca.fit_transform(X_scaled)
        
        # Cluster
        if SKLEARN_AVAILABLE and len(nodes) >= 3:
            # Use HDBSCAN for better cluster shapes
            clusterer = HDBSCAN(min_cluster_size=max(2, len(nodes) // 10), min_samples=1)
            cluster_labels = clusterer.fit_predict(X_scaled)
        else:
            # Fallback to KMeans
            n_clusters = min(5, len(nodes) // 3) if len(nodes) >= 3 else 1
            if SKLEARN_AVAILABLE and n_clusters > 1:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(X_scaled)
            else:
                cluster_labels = np.zeros(len(nodes))
        
        # Generate cluster labels
        cluster_labels_dict = self._label_clusters(node_data_list, cluster_labels)
        
        # Store results
        ManifoldPoint.objects.filter(vertical=self.vertical, region=self.region).delete()
        
        manifold_points = []
        for i, (node_data, coord, cluster_id) in enumerate(zip(node_data_list, coords_3d, cluster_labels)):
            point = ManifoldPoint.objects.create(
                node_type=node_data['type'],
                node_id=node_data['id'],
                x=float(coord[0]),
                y=float(coord[1]),
                z=float(coord[2]),
                cluster_id=int(cluster_id) if cluster_id >= 0 else None,
                cluster_label=cluster_labels_dict.get(int(cluster_id), ''),
                vertical=self.vertical,
                region=self.region,
            )
            manifold_points.append(point)
        
        print(f"Built manifold with {len(manifold_points)} points, {len(set(cluster_labels))} clusters")
        return ManifoldPoint.objects.filter(vertical=self.vertical, region=self.region)
    
    def _label_clusters(self, node_data_list: List[Dict], cluster_labels: np.ndarray) -> Dict[int, str]:
        """Generate human-readable labels for clusters."""
        cluster_groups = {}
        for i, cluster_id in enumerate(cluster_labels):
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append(node_data_list[i])
        
        labels = {}
        for cluster_id, nodes in cluster_groups.items():
            if cluster_id < 0:
                labels[cluster_id] = 'Outlier'
                continue
            
            # Analyze cluster composition
            types = [n['type'] for n in nodes]
            type_counts = {t: types.count(t) for t in set(types)}
            
            if len(nodes) == 1:
                labels[cluster_id] = nodes[0]['label'][:30]
            else:
                # Find common themes
                if type_counts.get('market', 0) > len(nodes) * 0.7:
                    # Market cluster - check categories
                    markets = [n['object'] for n in nodes if n['type'] == 'market']
                    categories = [m.category for m in markets]
                    tiers = [m.price_tier for m in markets if m.price_tier]
                    
                    if categories:
                        top_cat = max(set(categories), key=categories.count)
                        if tiers:
                            top_tier = max(set(tiers), key=tiers.count)
                            labels[cluster_id] = f"{top_cat} {top_tier.replace('_', ' ').title()}"
                        else:
                            labels[cluster_id] = f"{top_cat} Markets"
                    else:
                        labels[cluster_id] = f"Market Cluster {cluster_id}"
                
                elif type_counts.get('brand', 0) > len(nodes) * 0.7:
                    # Brand cluster
                    brands = [n['object'] for n in nodes if n['type'] == 'brand']
                    brand_types = [b.brand_type for b in brands]
                    if brand_types:
                        top_type = max(set(brand_types), key=brand_types.count)
                        labels[cluster_id] = f"{top_type.replace('_', ' ').title()} Brands"
                    else:
                        labels[cluster_id] = f"Brand Cluster {cluster_id}"
                else:
                    labels[cluster_id] = f"Mixed Cluster {cluster_id}"
        
        return labels
