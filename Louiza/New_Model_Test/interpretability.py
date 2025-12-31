"""
Interpretability analysis for LEM model.

Analyzes:
- Which latent dimensions drive indulgent behavior
- How promotions distort emotional states
- Why static models fail to capture fatigue and guilt loops
"""

import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import os

from models.lem import LEM
from train import ConsumerDataset, create_vocabularies
from torch.utils.data import DataLoader


def load_model_and_data(device):
    """Load model and validation data."""
    checkpoint = torch.load('models/lem_best.pt', map_location=device)
    vocab = checkpoint['vocab']
    
    model = LEM(
        n_categories=len(vocab['category_to_idx']),
        n_brands=len(vocab['brand_to_idx']) - 1,
        latent_dim=64,
        hidden_dim=128,
        n_layers=2
    ).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    events_df = pd.read_csv('data/events.csv')
    user_ids = events_df['user_id'].unique()
    np.random.seed(42)
    np.random.shuffle(user_ids)
    split_idx = int(0.8 * len(user_ids))
    val_users = set(user_ids[split_idx:])
    val_df = events_df[events_df['user_id'].isin(val_users)].copy()
    
    category_to_idx, brand_to_idx, context_to_idx = create_vocabularies(events_df)
    val_dataset = ConsumerDataset(
        val_df, category_to_idx, brand_to_idx, context_to_idx, sequence_length=10
    )
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    return model, vocab, val_df, val_loader, device


def analyze_indulgent_behavior(model, val_loader, vocab, device):
    """
    Analyze which latent dimensions drive indulgent behavior.
    
    Indulgent actions: fast_food, dessert
    """
    model.eval()
    
    latent_states_list = []
    categories_list = []
    
    with torch.no_grad():
        for batch in val_loader:
            category_seq = batch['category'][:, :-1].to(device)
            brand_seq = batch['brand'][:, :-1].to(device)
            time_seq = batch['time_of_day'][:, :-1].to(device)
            day_seq = batch['day_type'][:, :-1].to(device)
            promo_seq = batch['promo'][:, :-1].to(device)
            social_seq = batch['social'][:, :-1].to(device)
            
            category_target = batch['category'][:, -1].cpu().numpy()
            
            output = model(
                category_seq, brand_seq,
                time_seq, day_seq, promo_seq, social_seq
            )
            
            latent_states = output['latent_states'][:, -1, :].cpu().numpy()
            
            latent_states_list.append(latent_states)
            categories_list.append(category_target)
    
    latent_states = np.concatenate(latent_states_list, axis=0)
    categories = np.concatenate(categories_list, axis=0)
    
    # Identify indulgent actions
    idx_to_category = {v: k for k, v in vocab['category_to_idx'].items()}
    category_names = [idx_to_category[c] for c in categories]
    is_indulgent = np.array([cat in ['fast_food', 'dessert'] for cat in category_names])
    
    # Analyze correlation between latent dimensions and indulgent behavior
    correlations = []
    for dim in range(latent_states.shape[1]):
        corr = np.corrcoef(latent_states[:, dim], is_indulgent.astype(float))[0, 1]
        correlations.append(abs(corr))
    
    # Get top dimensions
    top_dims = np.argsort(correlations)[-5:][::-1]
    
    print("\n" + "="*60)
    print("INDULGENT BEHAVIOR ANALYSIS")
    print("="*60)
    print(f"\nTop 5 latent dimensions correlated with indulgent behavior:")
    for i, dim in enumerate(top_dims):
        corr = correlations[dim]
        print(f"  Dimension {dim}: correlation = {corr:.4f}")
    
    # Visualize
    fig, ax = plt.subplots(figsize=(12, 6))
    dim_indices = np.arange(len(correlations))
    colors = ['#e74c3c' if i in top_dims else '#95a5a6' for i in dim_indices]
    ax.bar(dim_indices, correlations, color=colors, alpha=0.7)
    ax.set_xlabel('Latent Dimension', fontsize=11)
    ax.set_ylabel('Absolute Correlation with Indulgent Behavior', fontsize=11)
    ax.set_title('Latent Dimensions Driving Indulgent Behavior', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/indulgent_behavior_analysis.png', dpi=300, bbox_inches='tight')
    print("\nSaved plots/indulgent_behavior_analysis.png")
    plt.close()
    
    return top_dims, correlations


def analyze_promotion_effects(model, val_df, vocab, device):
    """
    Analyze how promotions distort emotional states.
    """
    # Group by promotion exposure
    promo_groups = val_df.groupby('promo_exposure')
    
    model.eval()
    
    promo_states = {}
    
    for promo_type, group_df in promo_groups:
        if len(group_df) == 0:
            continue
        
        # Get sequences with this promotion type at last timestep
        group_df = group_df.sort_values(['user_id', 'timestep'])
        
        category_to_idx, brand_to_idx, context_to_idx = create_vocabularies(val_df)
        
        # Sample some sequences
        sample_size = min(100, len(group_df))
        sampled = group_df.groupby('user_id').tail(11).head(sample_size)
        
        if len(sampled) == 0:
            continue
        
        val_dataset = ConsumerDataset(
            sampled, category_to_idx, brand_to_idx, context_to_idx, sequence_length=10
        )
        val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
        
        latent_states_list = []
        
        with torch.no_grad():
            for batch in val_loader:
                category_seq = batch['category'][:, :-1].to(device)
                brand_seq = batch['brand'][:, :-1].to(device)
                time_seq = batch['time_of_day'][:, :-1].to(device)
                day_seq = batch['day_type'][:, :-1].to(device)
                promo_seq = batch['promo'][:, :-1].to(device)
                social_seq = batch['social'][:, :-1].to(device)
                
                output = model(
                    category_seq, brand_seq,
                    time_seq, day_seq, promo_seq, social_seq
                )
                
                latent_states = output['latent_states'][:, -1, :].cpu().numpy()
                latent_states_list.append(latent_states)
        
        if len(latent_states_list) > 0:
            promo_states[promo_type] = np.concatenate(latent_states_list, axis=0)
    
    # Compare states across promotion types
    print("\n" + "="*60)
    print("PROMOTION EFFECT ANALYSIS")
    print("="*60)
    
    if len(promo_states) > 1:
        # Compute average states
        for promo_type, states in promo_states.items():
            avg_state = states.mean(axis=0)
            print(f"\n{promo_type.upper()} (n={len(states)}):")
            print(f"  Mean latent state magnitude: {np.linalg.norm(avg_state):.4f}")
            print(f"  Mean state value: {avg_state.mean():.4f}")
        
        # Visualize
        promo_types = list(promo_states.keys())
        n_dims = promo_states[promo_types[0]].shape[1]
        
        # Use PCA to visualize
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors_map = {'none': '#95a5a6', 'discount': '#e74c3c', 'ad': '#3498db'}
        
        for promo_type in promo_types:
            states = promo_states[promo_type]
            if len(states) > 1:
                states_2d = pca.fit_transform(states)
                ax.scatter(states_2d[:, 0], states_2d[:, 1],
                          label=promo_type, alpha=0.6, s=30,
                          color=colors_map.get(promo_type, '#f39c12'))
        
        ax.set_xlabel('PC1', fontsize=11)
        ax.set_ylabel('PC2', fontsize=11)
        ax.set_title('Emotional State Distribution by Promotion Exposure', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        os.makedirs('plots', exist_ok=True)
        plt.savefig('plots/promotion_effects.png', dpi=300, bbox_inches='tight')
        print("\nSaved plots/promotion_effects.png")
        plt.close()
    
    return promo_states


def analyze_static_model_failures(events_df, states_hidden):
    """
    Analyze why static models fail to capture fatigue and guilt loops.
    """
    # Analyze temporal patterns in fatigue and guilt
    fatigue = states_hidden[:, :, 2]  # fatigue dimension
    guilt = states_hidden[:, :, 4]   # guilt dimension
    
    # Compute autocorrelation (temporal dependency)
    def autocorr(x, max_lag=10):
        """Compute autocorrelation."""
        n = len(x)
        corrs = []
        for lag in range(1, min(max_lag + 1, n)):
            if lag < n:
                corr = np.corrcoef(x[:-lag], x[lag:])[0, 1]
                corrs.append(corr if not np.isnan(corr) else 0)
        return np.array(corrs)
    
    # Compute autocorrelation for each consumer
    fatigue_autocorr = []
    guilt_autocorr = []
    
    for user_id in range(states_hidden.shape[0]):
        user_fatigue = fatigue[user_id, :]
        user_guilt = guilt[user_id, :]
        
        fatigue_ac = autocorr(user_fatigue)
        guilt_ac = autocorr(user_guilt)
        
        fatigue_autocorr.append(fatigue_ac.mean() if len(fatigue_ac) > 0 else 0)
        guilt_autocorr.append(guilt_ac.mean() if len(guilt_ac) > 0 else 0)
    
    fatigue_autocorr = np.array(fatigue_autocorr)
    guilt_autocorr = np.array(guilt_autocorr)
    
    print("\n" + "="*60)
    print("STATIC MODEL FAILURE ANALYSIS")
    print("="*60)
    print(f"\nFatigue autocorrelation (temporal dependency):")
    print(f"  Mean: {fatigue_autocorr.mean():.4f}")
    print(f"  Std: {fatigue_autocorr.std():.4f}")
    print(f"\nGuilt autocorrelation (temporal dependency):")
    print(f"  Mean: {guilt_autocorr.mean():.4f}")
    print(f"  Std: {guilt_autocorr.std():.4f}")
    print("\nHigh autocorrelation indicates strong temporal dependencies")
    print("that static models cannot capture.")
    
    # Visualize temporal patterns
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Fatigue over time (sample consumers)
    ax1 = axes[0, 0]
    sample_users = np.random.choice(states_hidden.shape[0], 10, replace=False)
    for user_id in sample_users:
        ax1.plot(fatigue[user_id, :], alpha=0.5, linewidth=1)
    ax1.plot(fatigue.mean(axis=0), label='Population Mean', linewidth=2, color='black')
    ax1.set_xlabel('Timestep', fontsize=10)
    ax1.set_ylabel('Fatigue', fontsize=10)
    ax1.set_title('Fatigue Evolution (Sample Consumers)', fontsize=11, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Guilt over time
    ax2 = axes[0, 1]
    for user_id in sample_users:
        ax2.plot(guilt[user_id, :], alpha=0.5, linewidth=1)
    ax2.plot(guilt.mean(axis=0), label='Population Mean', linewidth=2, color='black')
    ax2.set_xlabel('Timestep', fontsize=10)
    ax2.set_ylabel('Guilt', fontsize=10)
    ax2.set_title('Guilt Evolution (Sample Consumers)', fontsize=11, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # Autocorrelation distribution
    ax3 = axes[1, 0]
    ax3.hist(fatigue_autocorr, bins=30, alpha=0.7, color='#3498db', edgecolor='black')
    ax3.axvline(fatigue_autocorr.mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax3.set_xlabel('Autocorrelation', fontsize=10)
    ax3.set_ylabel('Frequency', fontsize=10)
    ax3.set_title('Fatigue Autocorrelation Distribution', fontsize=11, fontweight='bold')
    ax3.legend()
    ax3.grid(alpha=0.3)
    
    ax4 = axes[1, 1]
    ax4.hist(guilt_autocorr, bins=30, alpha=0.7, color='#e74c3c', edgecolor='black')
    ax4.axvline(guilt_autocorr.mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax4.set_xlabel('Autocorrelation', fontsize=10)
    ax4.set_ylabel('Frequency', fontsize=10)
    ax4.set_title('Guilt Autocorrelation Distribution', fontsize=11, fontweight='bold')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/static_model_failures.png', dpi=300, bbox_inches='tight')
    print("\nSaved plots/static_model_failures.png")
    plt.close()
    
    return {
        'fatigue_autocorr': fatigue_autocorr,
        'guilt_autocorr': guilt_autocorr
    }


def main():
    """Run all interpretability analyses."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load model and data
    model, vocab, val_df, val_loader, device = load_model_and_data(device)
    
    # 1. Indulgent behavior analysis
    top_dims, correlations = analyze_indulgent_behavior(model, val_loader, vocab, device)
    
    # 2. Promotion effects
    promo_states = analyze_promotion_effects(model, val_df, vocab, device)
    
    # 3. Static model failures
    events_df = pd.read_csv('data/events.csv')
    states_hidden = np.load('data/states_hidden.npy')
    failure_analysis = analyze_static_model_failures(events_df, states_hidden)
    
    print("\n" + "="*60)
    print("INTERPRETABILITY ANALYSIS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()

