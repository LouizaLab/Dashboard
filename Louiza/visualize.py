"""
Visualization dashboard for Phase 1 embeddings
"""

import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import json

from models import ProductEmbeddingModel, ContextEmbeddingModel, SegmentEmbeddingModel, CombinedEmbeddingModel
from data_utils import EmbeddingDataset, build_vocabularies

class EmbeddingVisualizer:
    """Visualize and analyze embeddings"""
    
    def __init__(self, model_path: str, data_dir: str = 'data'):
        """Load trained model and data"""
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.data_dir = data_dir
        
        # Load data
        self.products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
        self.contexts_df = pd.read_csv(os.path.join(data_dir, 'contexts.csv'))
        self.segments_df = pd.read_csv(os.path.join(data_dir, 'segments.csv'))
        
        # Load model
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Rebuild vocabularies
        self.vocabularies = checkpoint['vocabularies']
        
        # Recreate models
        if 'vocab_sizes' in checkpoint:
            vocab_sizes = checkpoint['vocab_sizes']
            ingredient_vocab_size = vocab_sizes['ingredient']
            tag_vocab_size = vocab_sizes['tag']
            text_vocab_size = vocab_sizes['text']
            vocab_size = max(ingredient_vocab_size, tag_vocab_size, text_vocab_size)
            
            time_of_day_vocab = vocab_sizes['time_of_day']
            location_vocab = vocab_sizes['location']
            occasion_vocab = vocab_sizes['occasion']
            age_vocab = vocab_sizes['age']
            region_vocab = vocab_sizes['region']
            psychographic_vocab = vocab_sizes['psychographic']
        else:
            # Fallback to computing from data
            ingredient_vocab_size = len(self.vocabularies['ingredient'].word_to_idx)
            tag_vocab_size = len(self.vocabularies['tag'].word_to_idx)
            text_vocab_size = len(self.vocabularies['text'].word_to_idx)
            vocab_size = max(ingredient_vocab_size, tag_vocab_size, text_vocab_size)
            
            time_of_days = sorted(self.contexts_df['time_of_day'].unique())
            locations = sorted(self.contexts_df['location'].unique())
            occasions = sorted(self.contexts_df['occasion'].unique())
            age_buckets = sorted(self.segments_df['age_bucket'].unique())
            regions = sorted(self.segments_df['region'].unique())
            psychographics = sorted(self.segments_df['psychographic'].unique())
            
            time_of_day_vocab = len(time_of_days)
            location_vocab = len(locations)
            occasion_vocab = len(occasions)
            age_vocab = len(age_buckets)
            region_vocab = len(regions)
            psychographic_vocab = len(psychographics)
        
        self.product_model = ProductEmbeddingModel(
            vocab_size=vocab_size,
            embedding_dim=64,
            hidden_dim=128,
            output_dim=128
        )
        
        self.context_model = ContextEmbeddingModel(
            time_of_day_vocab=time_of_day_vocab,
            location_vocab=location_vocab,
            occasion_vocab=occasion_vocab,
            embedding_dim=32,
            hidden_dim=64,
            output_dim=64
        )
        
        self.segment_model = SegmentEmbeddingModel(
            age_vocab=age_vocab,
            region_vocab=region_vocab,
            psychographic_vocab=psychographic_vocab,
            embedding_dim=32,
            hidden_dim=64,
            output_dim=64
        )
        
        self.product_model.load_state_dict(checkpoint['product_model_state_dict'])
        self.context_model.load_state_dict(checkpoint['context_model_state_dict'])
        self.segment_model.load_state_dict(checkpoint['segment_model_state_dict'])
        
        self.product_model.to(self.device)
        self.context_model.to(self.device)
        self.segment_model.to(self.device)
        
        self.product_model.eval()
        self.context_model.eval()
        self.segment_model.eval()
        
        # Create dataset for encoding
        intent_logs_df = pd.read_csv(os.path.join(data_dir, 'intent_logs.csv'))
        self.dataset = EmbeddingDataset(
            self.products_df, self.contexts_df, self.segments_df, intent_logs_df,
            self.vocabularies, max_ingredients=10, max_tags=8, max_text_len=50
        )
    
    def encode_all_products(self) -> np.ndarray:
        """Encode all products to embeddings"""
        embeddings = []
        product_ids = []
        
        with torch.no_grad():
            for idx in range(len(self.products_df)):
                product = self.products_df.iloc[idx]
                
                # Encode ingredients
                ingredients = product['ingredients'].split(',')
                ingredient_ids = []
                for ing in ingredients[:10]:
                    ing_id = self.vocabularies['ingredient'].word_to_idx.get(ing.strip(), 0)
                    ingredient_ids.append(ing_id)
                while len(ingredient_ids) < 10:
                    ingredient_ids.append(1)
                
                # Encode tags
                tags = product['sensory_tags'].split(',')
                tag_ids = []
                for tag in tags[:8]:
                    tag_id = self.vocabularies['tag'].word_to_idx.get(tag.strip(), 0)
                    tag_ids.append(tag_id)
                while len(tag_ids) < 8:
                    tag_ids.append(1)
                
                # Nutrition
                nutrition = torch.FloatTensor([
                    product['sugar_g'],
                    product['caffeine_mg'],
                    product['calories'],
                    product['protein_g']
                ]).unsqueeze(0).to(self.device)
                
                # Text
                text_ids = self.vocabularies['text'].encode(product['description'], 50)
                
                # Encode
                ingredient_ids_t = torch.LongTensor([ingredient_ids]).to(self.device)
                tag_ids_t = torch.LongTensor([tag_ids]).to(self.device)
                text_ids_t = torch.LongTensor([text_ids]).to(self.device)
                
                z_product = self.product_model(ingredient_ids_t, tag_ids_t, nutrition, text_ids_t)
                embeddings.append(z_product.cpu().numpy()[0])
                product_ids.append(product['product_id'])
        
        return np.array(embeddings), product_ids
    
    def visualize_product_embeddings(self, output_dir: str = 'visualizations'):
        """Create visualizations of product embeddings"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("Encoding all products...")
        embeddings, product_ids = self.encode_all_products()
        
        # Add metadata
        product_metadata = []
        for pid in product_ids:
            product = self.products_df[self.products_df['product_id'] == pid].iloc[0]
            product_metadata.append({
                'product_id': pid,
                'category': product['category'],
                'sugar': product['sugar_g'],
                'caffeine': product['caffeine_mg'],
                'price': product['price']
            })
        metadata_df = pd.DataFrame(product_metadata)
        
        # PCA for 2D visualization
        print("Computing PCA...")
        pca = PCA(n_components=2)
        embeddings_2d = pca.fit_transform(embeddings)
        
        # Combine data into DataFrame
        plot_df = metadata_df.copy()
        plot_df['PC1'] = embeddings_2d[:, 0]
        plot_df['PC2'] = embeddings_2d[:, 1]
        
        # Create scatter plot
        fig = px.scatter(
            plot_df,
            x='PC1',
            y='PC2',
            color='category',
            hover_data=['product_id', 'sugar', 'caffeine', 'price'],
            title='Product Embeddings (PCA)',
            labels={'PC1': f'PC1 ({pca.explained_variance_ratio_[0]:.2%})',
                   'PC2': f'PC2 ({pca.explained_variance_ratio_[1]:.2%})'}
        )
        fig.write_html(os.path.join(output_dir, 'product_embeddings_pca.html'))
        
        # t-SNE visualization
        print("Computing t-SNE...")
        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)-1))
        embeddings_tsne = tsne.fit_transform(embeddings)
        
        # Combine data into DataFrame for t-SNE
        plot_df_tsne = metadata_df.copy()
        plot_df_tsne['tSNE1'] = embeddings_tsne[:, 0]
        plot_df_tsne['tSNE2'] = embeddings_tsne[:, 1]
        
        fig2 = px.scatter(
            plot_df_tsne,
            x='tSNE1',
            y='tSNE2',
            color='category',
            hover_data=['product_id', 'sugar', 'caffeine', 'price'],
            title='Product Embeddings (t-SNE)'
        )
        fig2.write_html(os.path.join(output_dir, 'product_embeddings_tsne.html'))
        
        # Similarity matrix
        print("Computing similarity matrix...")
        similarity_matrix = cosine_similarity(embeddings)
        
        # Plot heatmap
        plt.figure(figsize=(12, 10))
        sns.heatmap(similarity_matrix, cmap='viridis', square=True, cbar=True)
        plt.title('Product Similarity Matrix (Cosine Similarity)')
        plt.xlabel('Product Index')
        plt.ylabel('Product Index')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'product_similarity_matrix.png'), dpi=150)
        plt.close()
        
        # Find most similar products
        print("Finding most similar products...")
        similarity_results = []
        for i, pid1 in enumerate(product_ids):
            for j, pid2 in enumerate(product_ids):
                if i < j:
                    similarity_results.append({
                        'product_1': pid1,
                        'product_2': pid2,
                        'similarity': similarity_matrix[i, j]
                    })
        
        similarity_df = pd.DataFrame(similarity_results)
        similarity_df = similarity_df.sort_values('similarity', ascending=False)
        similarity_df.to_csv(os.path.join(output_dir, 'product_similarities.csv'), index=False)
        
        print(f"Top 10 most similar product pairs:")
        print(similarity_df.head(10).to_string())
        
        return embeddings, product_ids
    
    def visualize_training_curves(self, checkpoint_path: str, output_dir: str = 'visualizations'):
        """Visualize training curves"""
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        train_losses = checkpoint['train_losses']
        val_losses = checkpoint['val_losses']
        
        os.makedirs(output_dir, exist_ok=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(train_losses))),
            y=train_losses,
            mode='lines',
            name='Train Loss',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=list(range(len(val_losses))),
            y=val_losses,
            mode='lines',
            name='Validation Loss',
            line=dict(color='red')
        ))
        fig.update_layout(
            title='Training Curves',
            xaxis_title='Epoch',
            yaxis_title='Loss',
            hovermode='x unified'
        )
        fig.write_html(os.path.join(output_dir, 'training_curves.html'))
        
        print("Training curves saved!")
    
    def analyze_embeddings(self, output_dir: str = 'visualizations'):
        """Run comprehensive embedding analysis"""
        print("\n=== Embedding Analysis ===")
        
        embeddings, product_ids = self.encode_all_products()
        
        # Statistics
        print(f"\nEmbedding Statistics:")
        print(f"  Shape: {embeddings.shape}")
        print(f"  Mean: {embeddings.mean():.4f}")
        print(f"  Std: {embeddings.std():.4f}")
        print(f"  Min: {embeddings.min():.4f}")
        print(f"  Max: {embeddings.max():.4f}")
        
        # Category analysis
        categories = self.products_df['category'].unique()
        category_embeddings = {}
        for cat in categories:
            cat_products = self.products_df[self.products_df['category'] == cat]['product_id'].tolist()
            cat_indices = [i for i, pid in enumerate(product_ids) if pid in cat_products]
            category_embeddings[cat] = embeddings[cat_indices]
            print(f"\n{cat}:")
            print(f"  Count: {len(cat_indices)}")
            print(f"  Mean embedding norm: {np.linalg.norm(category_embeddings[cat], axis=1).mean():.4f}")
        
        # Save embeddings
        embeddings_df = pd.DataFrame(embeddings, index=product_ids)
        embeddings_df.to_csv(os.path.join(output_dir, 'product_embeddings.csv'))
        print(f"\nSaved embeddings to {output_dir}/product_embeddings.csv")
        
        return embeddings, product_ids


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, default='checkpoints/best_model.pt')
    parser.add_argument('--data_dir', type=str, default='data')
    parser.add_argument('--output_dir', type=str, default='visualizations')
    
    args = parser.parse_args()
    
    visualizer = EmbeddingVisualizer(args.model_path, args.data_dir)
    
    # Run all visualizations
    visualizer.visualize_product_embeddings(args.output_dir)
    visualizer.visualize_training_curves(args.model_path, args.output_dir)
    visualizer.analyze_embeddings(args.output_dir)
    
    print("\nAll visualizations complete!")

