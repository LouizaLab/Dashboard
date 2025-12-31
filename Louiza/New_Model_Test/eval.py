"""
Evaluation script comparing LEM vs baselines.
"""

import torch
import numpy as np
import pandas as pd
import json
import os
from scipy.stats import entropy
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

from models.baselines import RandomBaseline, StaticPreferenceBaseline, evaluate_baseline
from models.lem import LEM
from train import ConsumerDataset, create_vocabularies
from torch.utils.data import DataLoader


def load_model(model_path: str, device: torch.device):
    """Load trained LEM model."""
    checkpoint = torch.load(model_path, map_location=device)
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
    
    return model, vocab


def evaluate_lem(model, dataloader, vocab, device):
    """Evaluate LEM model."""
    model.eval()
    
    all_predictions = []
    all_targets = []
    all_category_probs = []
    all_brand_probs = []
    all_latent_states = []
    
    idx_to_category = {v: k for k, v in vocab['category_to_idx'].items()}
    idx_to_brand = {v: k for k, v in vocab['brand_to_idx'].items()}
    
    with torch.no_grad():
        for batch in dataloader:
            category_seq = batch['category'][:, :-1].to(device)
            brand_seq = batch['brand'][:, :-1].to(device)
            time_seq = batch['time_of_day'][:, :-1].to(device)
            day_seq = batch['day_type'][:, :-1].to(device)
            promo_seq = batch['promo'][:, :-1].to(device)
            social_seq = batch['social'][:, :-1].to(device)
            
            category_target = batch['category'][:, -1].cpu().numpy()
            brand_target = batch['brand'][:, -1].cpu().numpy()
            
            output = model(
                category_seq, brand_seq,
                time_seq, day_seq, promo_seq, social_seq
            )
            
            category_logits = output['category_logits'][:, -1, :]
            brand_logits = output['brand_logits'][:, -1, :]
            latent_states = output['latent_states'][:, -1, :].cpu().numpy()
            
            category_probs = torch.softmax(category_logits, dim=-1).cpu().numpy()
            brand_probs = torch.softmax(brand_logits, dim=-1).cpu().numpy()
            
            category_pred = category_logits.argmax(dim=-1).cpu().numpy()
            brand_pred = brand_logits.argmax(dim=-1).cpu().numpy()
            
            all_predictions.append({
                'category': category_pred,
                'brand': brand_pred
            })
            all_targets.append({
                'category': category_target,
                'brand': brand_target
            })
            all_category_probs.append(category_probs)
            all_brand_probs.append(brand_probs)
            all_latent_states.append(latent_states)
    
    # Concatenate
    cat_pred = np.concatenate([p['category'] for p in all_predictions])
    brand_pred = np.concatenate([p['brand'] for p in all_predictions])
    cat_target = np.concatenate([t['category'] for t in all_targets])
    brand_target = np.concatenate([t['brand'] for t in all_targets])
    
    category_probs = np.concatenate(all_category_probs, axis=0)
    brand_probs = np.concatenate(all_brand_probs, axis=0)
    latent_states = np.concatenate(all_latent_states, axis=0)
    
    # Metrics
    category_accuracy = accuracy_score(cat_target, cat_pred)
    brand_accuracy = accuracy_score(brand_target, brand_pred)
    exact_accuracy = ((cat_pred == cat_target) & (brand_pred == brand_target)).mean()
    
    # NLL
    nll = 0.0
    for i in range(len(cat_target)):
        cat_idx = cat_target[i]
        brand_idx = brand_target[i]
        cat_prob = category_probs[i, cat_idx]
        brand_prob = brand_probs[i, brand_idx]
        nll -= np.log(max(cat_prob * brand_prob, 1e-10))
    nll = nll / len(cat_target)
    
    # Entropy
    entropies = []
    for i in range(len(category_probs)):
        cat_ent = entropy(category_probs[i], base=2)
        brand_ent = entropy(brand_probs[i], base=2)
        entropies.append(cat_ent + brand_ent)
    avg_entropy = np.mean(entropies)
    
    return {
        'accuracy': exact_accuracy,
        'category_accuracy': category_accuracy,
        'brand_accuracy': brand_accuracy,
        'nll': nll,
        'entropy': avg_entropy,
        'latent_states': latent_states,
        'predictions': {
            'category': cat_pred,
            'brand': brand_pred
        },
        'targets': {
            'category': cat_target,
            'brand': brand_target
        }
    }


def compare_states(lem_states, true_states):
    """
    Compare inferred LEM states with true hidden states.
    
    Args:
        lem_states: (n_samples, latent_dim) inferred states
        true_states: (n_samples, n_state_dims) true states
    """
    # Align dimensions using PCA
    if lem_states.shape[1] != true_states.shape[1]:
        # Project both to same dimension
        pca_lem = PCA(n_components=min(lem_states.shape[1], true_states.shape[1]))
        pca_true = PCA(n_components=min(lem_states.shape[1], true_states.shape[1]))
        
        lem_proj = pca_lem.fit_transform(lem_states)
        true_proj = pca_true.fit_transform(true_states)
        
        # Compute correlation
        correlations = []
        for i in range(min(lem_proj.shape[1], true_proj.shape[1])):
            corr = np.corrcoef(lem_proj[:, i], true_proj[:, i])[0, 1]
            correlations.append(corr)
        
        return {
            'correlations': correlations,
            'mean_correlation': np.mean(correlations),
            'lem_proj': lem_proj,
            'true_proj': true_proj
        }
    else:
        correlations = []
        for i in range(lem_states.shape[1]):
            corr = np.corrcoef(lem_states[:, i], true_states[:, i])[0, 1]
            correlations.append(corr)
        
        return {
            'correlations': correlations,
            'mean_correlation': np.mean(correlations),
            'lem_proj': lem_states,
            'true_proj': true_states
        }


def main():
    """Main evaluation."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load data
    print("Loading data...")
    events_df = pd.read_csv('data/events.csv')
    states_hidden = np.load('data/states_hidden.npy')
    
    # Load base traits (we'll regenerate them with same seed)
    # For now, we'll use a simple approximation
    np.random.seed(42)
    n_consumers = len(events_df['user_id'].unique())
    base_traits = np.random.uniform(0, 1, size=(n_consumers, 5))
    
    # Split (same as training)
    user_ids = events_df['user_id'].unique()
    np.random.seed(42)
    np.random.shuffle(user_ids)
    split_idx = int(0.8 * len(user_ids))
    val_users = set(user_ids[split_idx:])
    val_df = events_df[events_df['user_id'].isin(val_users)].copy()
    
    print(f"Evaluating on {len(val_df)} validation events")
    
    # Create vocabularies
    category_to_idx, brand_to_idx, context_to_idx = create_vocabularies(events_df)
    
    # Categories and brands for baselines
    categories = list(category_to_idx.keys())
    brands = [b for b in brand_to_idx.keys() if b != 'none']
    
    # Evaluate baselines
    print("\nEvaluating Baseline A (Random)...")
    random_baseline = RandomBaseline(categories, brands)
    random_metrics = evaluate_baseline(random_baseline, val_df)
    
    print("\nEvaluating Baseline B (Static Preference)...")
    static_baseline = StaticPreferenceBaseline(categories, brands)
    static_baseline.fit(val_df, base_traits)
    static_metrics = evaluate_baseline(static_baseline, val_df)
    
    # Evaluate LEM
    print("\nEvaluating LEM...")
    model, vocab = load_model('models/lem_best.pt', device)
    
    val_dataset = ConsumerDataset(
        val_df, category_to_idx, brand_to_idx, context_to_idx, sequence_length=10
    )
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    lem_metrics = evaluate_lem(model, val_loader, vocab, device)
    
    # State recovery analysis
    print("\nAnalyzing state recovery...")
    # Get true states for validation set
    val_user_ids = sorted(val_df['user_id'].unique())
    all_user_ids = sorted(events_df['user_id'].unique())
    val_user_indices = {uid: all_user_ids.index(uid) for uid in val_user_ids}
    
    # Extract true states for sequences in validation set
    # Match with LEM predictions by sampling from same sequences
    val_dataset = ConsumerDataset(
        val_df, category_to_idx, brand_to_idx, context_to_idx, sequence_length=10
    )
    
    true_states_list = []
    for seq_info in val_dataset.sequences[:len(lem_metrics['latent_states'])]:
        user_id = seq_info['user_id']
        end_idx = seq_info['end_idx']
        user_idx = val_user_indices[user_id]
        # Get state at the end of the sequence
        user_events = val_df[val_df['user_id'] == user_id].sort_values('timestep')
        if len(user_events) > 0 and end_idx < len(user_events):
            timestep = user_events.iloc[end_idx]['timestep']
            true_state = states_hidden[user_idx, int(timestep), :]
            true_states_list.append(true_state)
    
    if len(true_states_list) > 0 and len(true_states_list) == len(lem_metrics['latent_states']):
        true_states_sample = np.array(true_states_list)
        state_comparison = compare_states(lem_metrics['latent_states'], true_states_sample)
        print(f"Mean state correlation: {state_comparison['mean_correlation']:.4f}")
    else:
        print(f"Warning: Could not match states ({len(true_states_list)} true vs {len(lem_metrics['latent_states'])} inferred)")
        state_comparison = None
    
    # Compile results
    results = {
        'random_baseline': random_metrics,
        'static_baseline': static_metrics,
        'lem': {
            'accuracy': lem_metrics['accuracy'],
            'category_accuracy': lem_metrics['category_accuracy'],
            'brand_accuracy': lem_metrics['brand_accuracy'],
            'nll': lem_metrics['nll'],
            'entropy': lem_metrics['entropy']
        },
        'state_recovery': state_comparison['mean_correlation'] if state_comparison else None
    }
    
    # Save results
    os.makedirs('eval', exist_ok=True)
    with open('eval/metrics.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print comparison
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"\nBaseline A (Random):")
    print(f"  Accuracy: {random_metrics['accuracy']:.4f}")
    print(f"  Category Accuracy: {random_metrics['category_accuracy']:.4f}")
    print(f"  NLL: {random_metrics['nll']:.4f}")
    print(f"  Entropy: {random_metrics['entropy']:.4f}")
    
    print(f"\nBaseline B (Static Preference):")
    print(f"  Accuracy: {static_metrics['accuracy']:.4f}")
    print(f"  Category Accuracy: {static_metrics['category_accuracy']:.4f}")
    print(f"  NLL: {static_metrics['nll']:.4f}")
    print(f"  Entropy: {static_metrics['entropy']:.4f}")
    
    print(f"\nLEM (Large Emotional Model):")
    print(f"  Accuracy: {lem_metrics['accuracy']:.4f}")
    print(f"  Category Accuracy: {lem_metrics['category_accuracy']:.4f}")
    print(f"  NLL: {lem_metrics['nll']:.4f}")
    print(f"  Entropy: {lem_metrics['entropy']:.4f}")
    
    if state_comparison:
        print(f"\nState Recovery:")
        print(f"  Mean Correlation: {state_comparison['mean_correlation']:.4f}")
    
    print("\n" + "="*60)
    print("IMPROVEMENT:")
    print(f"  Accuracy: {lem_metrics['accuracy'] - static_metrics['accuracy']:.4f} "
          f"({(lem_metrics['accuracy'] / static_metrics['accuracy'] - 1) * 100:.1f}%)")
    print(f"  NLL Reduction: {static_metrics['nll'] - lem_metrics['nll']:.4f} "
          f"({(1 - lem_metrics['nll'] / static_metrics['nll']) * 100:.1f}%)")
    print(f"  Entropy Reduction: {static_metrics['entropy'] - lem_metrics['entropy']:.4f} "
          f"({(1 - lem_metrics['entropy'] / static_metrics['entropy']) * 100:.1f}%)")
    
    return results, lem_metrics, state_comparison


if __name__ == '__main__':
    main()

