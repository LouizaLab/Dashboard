"""
Evaluation utilities for Phase 1: Taste Embedding Model
Similarity search, clustering, and visualization
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import List, Tuple, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns

# FAISS is optional
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Note: FAISS not installed. Using sklearn for similarity search (slower but works).")
    print("  Install FAISS for faster search: pip install faiss-cpu")


class EmbeddingEvaluator:
    """
    Evaluation utilities for product embeddings
    """
    
    def __init__(self, embeddings_path: Path, metadata_path: Path, faiss_index_path: Path = None):
        """
        Initialize evaluator
        
        Args:
            embeddings_path: Path to product_embeddings.npy
            metadata_path: Path to product_metadata.json
            faiss_index_path: Optional path to FAISS index
        """
        # Load embeddings
        self.embeddings = np.load(embeddings_path)
        print(f"Loaded {len(self.embeddings)} embeddings of dimension {self.embeddings.shape[1]}")
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        self.product_ids = self.metadata['product_ids']
        self.product_names = self.metadata['product_names']
        
        # Load FAISS index if available
        self.faiss_index = None
        if HAS_FAISS and faiss_index_path and Path(faiss_index_path).exists():
            try:
                self.faiss_index = faiss.read_index(str(faiss_index_path))
                print(f"Loaded FAISS index")
            except Exception as e:
                print(f"Warning: Could not load FAISS index: {e}")
                self.faiss_index = None
    
    def find_similar_products(self, 
                             product_id: str = None,
                             product_name: str = None,
                             embedding: np.ndarray = None,
                             top_k: int = 10,
                             use_faiss: bool = True) -> List[Tuple[str, str, float]]:
        """
        Find similar products
        
        Args:
            product_id: Product ID to find similar products for
            product_name: Product name to find similar products for
            embedding: Direct embedding vector
            top_k: Number of similar products to return
            use_faiss: Use FAISS for fast search (if available)
        
        Returns:
            List of (product_id, product_name, similarity_score) tuples
        """
        # Get query embedding
        if embedding is not None:
            query_emb = embedding
        elif product_id:
            idx = self.product_ids.index(product_id)
            query_emb = self.embeddings[idx]
        elif product_name:
            idx = self.product_names.index(product_name)
            query_emb = self.embeddings[idx]
        else:
            raise ValueError("Must provide product_id, product_name, or embedding")
        
        query_emb = query_emb.reshape(1, -1)
        
        # Normalize for cosine similarity
        query_emb_norm = query_emb / (np.linalg.norm(query_emb) + 1e-8)
        embeddings_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-8)
        
        if use_faiss and HAS_FAISS and self.faiss_index is not None:
            # Use FAISS for fast search
            try:
                faiss.normalize_L2(query_emb_norm.astype('float32'))
                similarities, indices = self.faiss_index.search(query_emb_norm.astype('float32'), top_k + 1)
                similarities = similarities[0]
                indices = indices[0]
                
                # Filter out self-match
                results = []
                for sim, idx in zip(similarities, indices):
                    if idx < len(self.product_ids):
                        results.append((
                            self.product_ids[idx],
                            self.product_names[idx],
                            float(sim)
                        ))
                return results[:top_k]
            except Exception as e:
                print(f"Warning: FAISS search failed, using sklearn: {e}")
                # Fall through to sklearn method
        
        # Use sklearn cosine similarity (always works)
            # Use sklearn cosine similarity
            similarities = cosine_similarity(query_emb_norm, embeddings_norm)[0]
            top_indices = np.argsort(similarities)[::-1][:top_k+1]
            
            results = []
            for idx in top_indices:
                if idx < len(self.product_ids):
                    # Skip self-match
                    if embedding is None and product_id and self.product_ids[idx] == product_id:
                        continue
                    if embedding is None and product_name and self.product_names[idx] == product_name:
                        continue
                    results.append((
                        self.product_ids[idx],
                        self.product_names[idx],
                        float(similarities[idx])
                    ))
            return results[:top_k]
    
    def cluster_products(self, n_clusters: int = 10, random_state: int = 42) -> Dict:
        """
        Cluster products using K-means
        
        Returns:
            Dictionary with cluster assignments and centroids
        """
        print(f"Clustering {len(self.embeddings)} products into {n_clusters} clusters...")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        cluster_labels = kmeans.fit_predict(self.embeddings)
        
        # Create cluster assignments
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append({
                'product_id': self.product_ids[idx],
                'product_name': self.product_names[idx]
            })
        
        # Convert numpy types to Python native types for JSON serialization
        return {
            'cluster_labels': [int(x) for x in cluster_labels.tolist()],
            'cluster_centroids': [[float(y) for y in x] for x in kmeans.cluster_centers_.tolist()],
            'clusters': {str(k): v for k, v in clusters.items()},  # Convert keys to strings
            'n_clusters': int(n_clusters)
        }
    
    def visualize_clusters(self, 
                          cluster_labels: np.ndarray,
                          output_path: Path = None,
                          n_samples: int = None,
                          show_names: bool = True,
                          max_names_per_cluster: int = 3):
        """
        Visualize clusters using t-SNE with beautiful styling and legend
        
        Args:
            cluster_labels: Cluster assignments
            output_path: Path to save visualization
            n_samples: Number of samples to visualize (for large datasets)
            show_names: Whether to show product names on the plot
            max_names_per_cluster: Maximum number of product names to show per cluster
        """
        embeddings = self.embeddings
        labels = cluster_labels
        product_names = self.product_names
        
        # Sample if needed
        if n_samples and len(embeddings) > n_samples:
            indices = np.random.choice(len(embeddings), n_samples, replace=False)
            embeddings = embeddings[indices]
            labels = labels[indices]
            product_names = [product_names[i] for i in indices]
        
        print("Computing t-SNE...")
        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)-1))
        embeddings_2d = tsne.fit_transform(embeddings)
        
        # Create figure with subplots: main plot + legend
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(1, 2, width_ratios=[4, 1], hspace=0.3)
        ax_main = fig.add_subplot(gs[0, 0])
        ax_legend = fig.add_subplot(gs[0, 1])
        ax_legend.axis('off')
        
        # Get unique clusters and sort them
        unique_clusters = np.unique(labels)
        unique_clusters = np.sort(unique_clusters)
        
        # Use a nice colormap
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_clusters)))
        cluster_color_map = {int(cluster_id): colors[i] for i, cluster_id in enumerate(unique_clusters)}
        
        # Plot each cluster with its color
        for cluster_id in unique_clusters:
            cluster_mask = labels == cluster_id
            cluster_points = embeddings_2d[cluster_mask]
            ax_main.scatter(
                cluster_points[:, 0], 
                cluster_points[:, 1],
                c=[cluster_color_map[int(cluster_id)]],
                label=f'Cluster {int(cluster_id)}',
                alpha=0.7,
                s=60,
                edgecolors='white',
                linewidths=0.5
            )
        
        # Style the main plot
        ax_main.set_title('Product Embeddings Clusters (t-SNE)', 
                         fontsize=18, fontweight='bold', pad=20)
        ax_main.set_xlabel('t-SNE Dimension 1', fontsize=13)
        ax_main.set_ylabel('t-SNE Dimension 2', fontsize=13)
        ax_main.grid(True, alpha=0.3, linestyle='--')
        ax_main.spines['top'].set_visible(False)
        ax_main.spines['right'].set_visible(False)
        
        # Build legend with cluster information
        legend_text = []
        legend_colors = []
        
        for cluster_id in unique_clusters:
            cluster_mask = labels == cluster_id
            cluster_names = [product_names[i] for i in range(len(product_names)) if cluster_mask[i]]
            n_products = len(cluster_names)
            
            # Get representative products
            if cluster_names:
                sample_names = cluster_names[:max_names_per_cluster]
                # Truncate long names
                sample_display = [name[:25] + '...' if len(name) > 25 else name for name in sample_names]
                sample_text = '\n'.join([f"  • {name}" for name in sample_display])
                if n_products > max_names_per_cluster:
                    sample_text += f"\n  ... and {n_products - max_names_per_cluster} more"
            else:
                sample_text = "  (empty)"
            
            # Create legend entry
            legend_entry = f"Cluster {int(cluster_id)}\n({n_products} products)\n{sample_text}"
            legend_text.append(legend_entry)
            legend_colors.append(cluster_color_map[int(cluster_id)])
        
        # Create custom legend
        legend_elements = []
        for i, (text, color) in enumerate(zip(legend_text, legend_colors)):
            legend_elements.append(
                plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=0.7, edgecolor='white', linewidth=1)
            )
        
        # Add legend to the right side
        legend = ax_legend.legend(
            legend_elements,
            legend_text,
            loc='upper left',
            fontsize=9,
            frameon=True,
            fancybox=True,
            shadow=True,
            framealpha=0.95,
            title='Clusters',
            title_fontsize=12
        )
        # Set title font weight separately
        legend.get_title().set_fontweight('bold')
        legend.get_frame().set_facecolor('#f8f9fa')
        legend.get_frame().set_edgecolor('#dee2e6')
        
        # Add cluster labels on the plot (optional, lighter)
        if show_names:
            print("Adding cluster labels to visualization...")
            for cluster_id in unique_clusters:
                cluster_mask = labels == cluster_id
                cluster_points = embeddings_2d[cluster_mask]
                
                if len(cluster_points) > 0:
                    # Find centroid
                    centroid = cluster_points.mean(axis=0)
                    
                    # Add subtle cluster number label
                    ax_main.annotate(
                        f'C{int(cluster_id)}',
                        xy=centroid,
                        fontsize=11,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        bbox=dict(
                            boxstyle='round,pad=0.4',
                            facecolor='white',
                            edgecolor=cluster_color_map[int(cluster_id)],
                            linewidth=2,
                            alpha=0.9
                        )
                    )
        
        plt.tight_layout()
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
            print(f"Saved visualization to {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def evaluate_category_separation(self, products_df: pd.DataFrame) -> Dict:
        """
        Evaluate how well embeddings separate different categories
        
        Args:
            products_df: DataFrame with product_id and category columns
        """
        # Create category mapping
        category_map = {}
        for idx, row in products_df.iterrows():
            product_id = row['product_id']
            category = row.get('category', 'Unknown')
            category_map[product_id] = category
        
        # Compute intra-category and inter-category similarities
        categories = list(set(category_map.values()))
        intra_similarities = []
        inter_similarities = []
        
        for cat in categories:
            # Get product indices for this category
            cat_indices = [i for i, pid in enumerate(self.product_ids) 
                          if category_map.get(pid) == cat]
            
            if len(cat_indices) < 2:
                continue
            
            # Intra-category similarities
            cat_embeddings = self.embeddings[cat_indices]
            cat_similarities = cosine_similarity(cat_embeddings)
            # Get upper triangle (excluding diagonal)
            triu_indices = np.triu_indices(len(cat_similarities), k=1)
            intra_similarities.extend(cat_similarities[triu_indices].tolist())
            
            # Inter-category similarities
            other_indices = [i for i in range(len(self.product_ids)) if i not in cat_indices]
            if other_indices:
                other_embeddings = self.embeddings[other_indices]
                inter_sim = cosine_similarity(cat_embeddings[:1], other_embeddings[:min(10, len(other_embeddings))])
                inter_similarities.extend(inter_sim[0].tolist())
        
        return {
            'intra_category_mean': float(np.mean(intra_similarities)),
            'intra_category_std': float(np.std(intra_similarities)),
            'inter_category_mean': float(np.mean(inter_similarities)),
            'inter_category_std': float(np.std(inter_similarities)),
            'separation_score': float(np.mean(intra_similarities) - np.mean(inter_similarities))
        }
    
    def sanity_check(self, products_df: pd.DataFrame) -> Dict:
        """
        Perform sanity checks on embeddings
        
        Examples: Coke vs Pepsi, Coffee vs Energy Drink
        """
        results = {}
        
        # Find products by name patterns
        def find_products(pattern):
            return [pid for pid, name in zip(self.product_ids, self.product_names) 
                   if pattern.lower() in name.lower()]
        
        # Test cases
        test_cases = [
            ('cola', 'cola'),
            ('coffee', 'coffee'),
            ('burger', 'burger'),
            ('chicken', 'chicken')
        ]
        
        for pattern1, pattern2 in test_cases:
            products1 = find_products(pattern1)
            products2 = find_products(pattern2)
            
            if products1 and products2:
                # Compute average similarity within group
                if len(products1) > 1:
                    indices1 = [self.product_ids.index(p) for p in products1]
                    emb1 = self.embeddings[indices1]
                    sim1 = cosine_similarity(emb1).mean()
                else:
                    sim1 = 1.0
                
                if len(products2) > 1:
                    indices2 = [self.product_ids.index(p) for p in products2]
                    emb2 = self.embeddings[indices2]
                    sim2 = cosine_similarity(emb2).mean()
                else:
                    sim2 = 1.0
                
                # Compute similarity between groups
                if products1 and products2:
                    indices1 = [self.product_ids.index(p) for p in products1[:5]]
                    indices2 = [self.product_ids.index(p) for p in products2[:5]]
                    emb1 = self.embeddings[indices1]
                    emb2 = self.embeddings[indices2]
                    sim_between = cosine_similarity(emb1, emb2).mean()
                else:
                    sim_between = 0.0
                
                results[f'{pattern1}_vs_{pattern2}'] = {
                    'within_group1': float(sim1),
                    'within_group2': float(sim2),
                    'between_groups': float(sim_between)
                }
        
        return results


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate product embeddings')
    parser.add_argument('--embeddings', type=str, default='embeddings/product_embeddings.npy',
                       help='Path to embeddings file')
    parser.add_argument('--metadata', type=str, default='embeddings/product_metadata.json',
                       help='Path to metadata file')
    parser.add_argument('--faiss_index', type=str, default='embeddings/faiss_index.bin',
                       help='Path to FAISS index')
    parser.add_argument('--products', type=str, default='data/processed/products.csv',
                       help='Path to products CSV')
    parser.add_argument('--output_dir', type=str, default='embeddings',
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = EmbeddingEvaluator(
        Path(args.embeddings),
        Path(args.metadata),
        Path(args.faiss_index) if args.faiss_index else None
    )
    
    # Load products dataframe
    products_df = pd.read_csv(args.products)
    
    # Evaluate category separation
    print("\nEvaluating category separation...")
    separation_results = evaluator.evaluate_category_separation(products_df)
    print(f"Intra-category similarity: {separation_results['intra_category_mean']:.4f}")
    print(f"Inter-category similarity: {separation_results['inter_category_mean']:.4f}")
    print(f"Separation score: {separation_results['separation_score']:.4f}")
    
    # Sanity checks
    print("\nPerforming sanity checks...")
    sanity_results = evaluator.sanity_check(products_df)
    for test_name, results in sanity_results.items():
        print(f"\n{test_name}:")
        print(f"  Within group 1: {results['within_group1']:.4f}")
        print(f"  Within group 2: {results['within_group2']:.4f}")
        print(f"  Between groups: {results['between_groups']:.4f}")
    
    # Clustering
    print("\nClustering products...")
    cluster_results = evaluator.cluster_products(n_clusters=10)
    
    # Save cluster results
    output_dir = Path(args.output_dir)
    cluster_path = output_dir / 'clusters.json'
    with open(cluster_path, 'w') as f:
        json.dump(cluster_results, f, indent=2)
    print(f"Saved cluster results to {cluster_path}")
    
    # Visualize clusters
    print("\nVisualizing clusters...")
    cluster_labels = np.array(cluster_results['cluster_labels'])
    viz_path = output_dir / 'cluster_visualization.png'
    evaluator.visualize_clusters(
        cluster_labels, 
        output_path=viz_path,
        show_names=True,
        max_names_per_cluster=3
    )
    
    # Example similarity search
    print("\nExample similarity searches:")
    if len(evaluator.product_names) > 0:
        example_product = evaluator.product_names[0]
        print(f"\nProducts similar to '{example_product}':")
        similar = evaluator.find_similar_products(product_name=example_product, top_k=5)
        if similar:
            for pid, name, sim in similar:
                print(f"  {name} (similarity: {sim:.4f})")
        else:
            print("  No similar products found")


if __name__ == '__main__':
    main()

