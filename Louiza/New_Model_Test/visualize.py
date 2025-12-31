"""
Visualization script for before/after comparisons and analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from sklearn.decomposition import PCA

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def load_results():
    """Load evaluation results."""
    with open('eval/metrics.json', 'r') as f:
        results = json.load(f)
    return results


def plot_before_vs_after_accuracy(results, save_path='plots/before_vs_after_accuracy.png'):
    """Plot prediction accuracy comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    models = ['Random\nBaseline', 'Static\nPreference', 'LEM']
    accuracies = [
        results['random_baseline']['accuracy'],
        results['static_baseline']['accuracy'],
        results['lem']['accuracy']
    ]
    
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    bars = ax.bar(models, accuracies, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{acc:.3f}',
                ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Prediction Accuracy', fontsize=12, fontweight='bold')
    ax.set_title('Model Comparison: Prediction Accuracy', fontsize=14, fontweight='bold')
    ax.set_ylim([0, max(accuracies) * 1.2])
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved {save_path}")
    plt.close()


def plot_entropy_comparison(results, save_path='plots/entropy_comparison.png'):
    """Plot entropy comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    models = ['Random\nBaseline', 'Static\nPreference', 'LEM']
    entropies = [
        results['random_baseline']['entropy'],
        results['static_baseline']['entropy'],
        results['lem']['entropy']
    ]
    
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    bars = ax.bar(models, entropies, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar, ent in zip(bars, entropies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{ent:.3f}',
                ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Predictive Entropy (bits)', fontsize=12, fontweight='bold')
    ax.set_title('Model Comparison: Predictive Entropy', fontsize=14, fontweight='bold')
    ax.set_ylim([0, max(entropies) * 1.2])
    ax.grid(axis='y', alpha=0.3)
    
    # Add improvement annotation
    improvement = results['static_baseline']['entropy'] - results['lem']['entropy']
    ax.annotate(f'Reduction: {improvement:.3f} bits',
                xy=(2, results['lem']['entropy']),
                xytext=(2.3, results['lem']['entropy'] + 0.5),
                arrowprops=dict(arrowstyle='->', color='green', lw=2),
                fontsize=10, color='green', fontweight='bold')
    
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved {save_path}")
    plt.close()


def plot_state_trajectories(lem_states=None, true_states=None, save_path='plots/state_trajectories.png'):
    """Plot example consumer state trajectories."""
    # Load from evaluation if not provided
    if lem_states is None or true_states is None:
        try:
            import json
            import torch
            from eval import load_model, evaluate_lem
            from train import ConsumerDataset, create_vocabularies
            from torch.utils.data import DataLoader
            
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            events_df = pd.read_csv('data/events.csv')
            states_hidden = np.load('data/states_hidden.npy')
            
            user_ids = events_df['user_id'].unique()
            np.random.seed(42)
            np.random.shuffle(user_ids)
            split_idx = int(0.8 * len(user_ids))
            val_users = set(user_ids[split_idx:])
            val_df = events_df[events_df['user_id'].isin(val_users)].copy()
            
            category_to_idx, brand_to_idx, context_to_idx = create_vocabularies(events_df)
            val_dataset = ConsumerDataset(val_df, category_to_idx, brand_to_idx, context_to_idx, sequence_length=10)
            val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
            
            model, vocab = load_model('models/lem_best.pt', device)
            lem_metrics = evaluate_lem(model, val_loader, vocab, device)
            
            lem_states = lem_metrics['latent_states']
            
            # Get matching true states
            val_user_ids = sorted(val_df['user_id'].unique())
            all_user_ids = sorted(events_df['user_id'].unique())
            val_user_indices = {uid: all_user_ids.index(uid) for uid in val_user_ids}
            
            true_states_list = []
            for seq_info in val_dataset.sequences[:len(lem_states)]:
                user_id = seq_info['user_id']
                end_idx = seq_info['end_idx']
                user_idx = val_user_indices[user_id]
                user_events = val_df[val_df['user_id'] == user_id].sort_values('timestep')
                if len(user_events) > 0 and end_idx < len(user_events):
                    timestep = user_events.iloc[end_idx]['timestep']
                    true_state = states_hidden[user_idx, int(timestep), :]
                    true_states_list.append(true_state)
            
            if len(true_states_list) == len(lem_states):
                true_states = np.array(true_states_list)
            else:
                print("Warning: Could not match all states, using sample")
                true_states = states_hidden[:len(lem_states), -1, :] if len(lem_states) <= states_hidden.shape[0] else states_hidden[:, -1, :]
        except Exception as e:
            print(f"Could not load states: {e}")
            return
    
    # Use PCA to project to 2D for visualization
    pca = PCA(n_components=2)
    
    lem_2d = pca.fit_transform(lem_states)
    true_2d = pca.fit_transform(true_states)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # True states
    scatter1 = axes[0].scatter(true_2d[:, 0], true_2d[:, 1], c=np.arange(len(true_2d)),
                              cmap='viridis', alpha=0.6, s=20)
    axes[0].set_title('True Latent States (PCA Projection)', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('PC1', fontsize=10)
    axes[0].set_ylabel('PC2', fontsize=10)
    axes[0].grid(alpha=0.3)
    plt.colorbar(scatter1, ax=axes[0], label='Sample Index')
    
    # LEM inferred states
    scatter2 = axes[1].scatter(lem_2d[:, 0], lem_2d[:, 1], c=np.arange(len(lem_2d)),
                              cmap='viridis', alpha=0.6, s=20)
    axes[1].set_title('LEM Inferred States (PCA Projection)', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('PC1', fontsize=10)
    axes[1].set_ylabel('PC2', fontsize=10)
    axes[1].grid(alpha=0.3)
    plt.colorbar(scatter2, ax=axes[1], label='Sample Index')
    
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved {save_path}")
    plt.close()


def plot_population_state_distribution(states_hidden, save_path='plots/population_state_distribution.png'):
    """Plot population-level state distribution over time."""
    # Average states across population at each timestep
    mean_states = states_hidden.mean(axis=0)  # (n_timesteps, n_state_dims)
    std_states = states_hidden.std(axis=0)
    
    state_names = [
        'Craving Sweet', 'Craving Salty', 'Fatigue',
        'Novelty Drive', 'Guilt', 'Brand Attachment', 'Price Alertness'
    ]
    
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()
    
    timesteps = np.arange(len(mean_states))
    
    for i, (name, ax) in enumerate(zip(state_names, axes)):
        ax.plot(timesteps, mean_states[:, i], label='Mean', linewidth=2, color='#3498db')
        ax.fill_between(timesteps,
                        mean_states[:, i] - std_states[:, i],
                        mean_states[:, i] + std_states[:, i],
                        alpha=0.3, color='#3498db', label='±1 Std')
        ax.set_title(name, fontsize=11, fontweight='bold')
        ax.set_xlabel('Timestep', fontsize=9)
        ax.set_ylabel('State Value', fontsize=9)
        ax.set_ylim([0, 1])
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    
    # Remove extra subplot
    axes[7].axis('off')
    
    plt.suptitle('Population-Level State Distribution Over Time', fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved {save_path}")
    plt.close()


def plot_behavioral_regime_shifts(events_df, states_hidden, save_path='plots/behavioral_regime_shifts.png'):
    """Plot behavioral regime shifts (indulgence → fatigue → restraint)."""
    # Identify regime shifts by analyzing state patterns
    # Regime 1: Indulgence (high guilt, high fatigue, high cravings)
    # Regime 2: Fatigue (high fatigue, low cravings)
    # Regime 3: Restraint (low guilt, low cravings, high health consciousness)
    
    n_consumers = states_hidden.shape[0]
    n_timesteps = states_hidden.shape[1]
    
    # Compute regime indicators
    indulgence = (states_hidden[:, :, 0] + states_hidden[:, :, 1] + states_hidden[:, :, 4]) / 3  # cravings + guilt
    fatigue = states_hidden[:, :, 2]
    restraint = (1 - states_hidden[:, :, 0] - states_hidden[:, :, 1] + (1 - states_hidden[:, :, 4])) / 3
    
    # Average across population
    avg_indulgence = indulgence.mean(axis=0)
    avg_fatigue = fatigue.mean(axis=0)
    avg_restraint = restraint.mean(axis=0)
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    timesteps = np.arange(n_timesteps)
    
    # Plot 1: Regime indicators over time
    ax1 = axes[0]
    ax1.plot(timesteps, avg_indulgence, label='Indulgence', linewidth=2, color='#e74c3c')
    ax1.plot(timesteps, avg_fatigue, label='Fatigue', linewidth=2, color='#95a5a6')
    ax1.plot(timesteps, avg_restraint, label='Restraint', linewidth=2, color='#27ae60')
    ax1.set_xlabel('Timestep', fontsize=11)
    ax1.set_ylabel('Regime Strength', fontsize=11)
    ax1.set_title('Behavioral Regime Evolution Over Time', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)
    
    # Plot 2: Category distribution over time
    ax2 = axes[1]
    category_counts = events_df.groupby(['timestep', 'category']).size().unstack(fill_value=0)
    category_props = category_counts.div(category_counts.sum(axis=1), axis=0)
    
    colors_cat = {'fast_food': '#e74c3c', 'healthy_food': '#27ae60', 'dessert': '#f39c12', 'skip': '#95a5a6'}
    for category in category_props.columns:
        ax2.plot(category_props.index, category_props[category],
                label=category.replace('_', ' ').title(), linewidth=2, color=colors_cat.get(category, '#3498db'))
    
    ax2.set_xlabel('Timestep', fontsize=11)
    ax2.set_ylabel('Proportion of Actions', fontsize=11)
    ax2.set_title('Action Category Distribution Over Time', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3)
    ax2.set_ylim([0, 1])
    
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved {save_path}")
    plt.close()


def plot_training_history(save_path='plots/training_history.png'):
    """Plot training history."""
    try:
        with open('eval/training_history.json', 'r') as f:
            history = json.load(f)
        
        train_loss = [h['loss'] for h in history['train']]
        train_nll = [h['nll'] for h in history['train']]
        val_nll = [h['nll'] for h in history['val']]
        val_acc = [h['accuracy'] for h in history['val']]
        
        epochs = np.arange(1, len(train_loss) + 1)
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Loss
        ax1 = axes[0]
        ax1.plot(epochs, train_loss, label='Train Loss', linewidth=2, color='#3498db')
        ax1.plot(epochs, train_nll, label='Train NLL', linewidth=2, color='#2ecc71', linestyle='--')
        ax1.plot(epochs, val_nll, label='Val NLL', linewidth=2, color='#e74c3c')
        ax1.set_xlabel('Epoch', fontsize=11)
        ax1.set_ylabel('Loss', fontsize=11)
        ax1.set_title('Training History: Loss', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(alpha=0.3)
        
        # Accuracy
        ax2 = axes[1]
        ax2.plot(epochs, val_acc, label='Val Accuracy', linewidth=2, color='#27ae60')
        ax2.set_xlabel('Epoch', fontsize=11)
        ax2.set_ylabel('Accuracy', fontsize=11)
        ax2.set_title('Training History: Validation Accuracy', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        os.makedirs('plots', exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved {save_path}")
        plt.close()
    except FileNotFoundError:
        print("Training history not found, skipping...")


def main():
    """Generate all visualizations."""
    print("Generating visualizations...")
    
    # Load results
    results = load_results()
    
    # Load data for trajectory plots
    events_df = pd.read_csv('data/events.csv')
    states_hidden = np.load('data/states_hidden.npy')
    
    # Load LEM states (from evaluation)
    # We'll need to run eval first or load from saved results
    # For now, generate what we can
    
    # 1. Before vs after accuracy
    plot_before_vs_after_accuracy(results)
    
    # 2. Entropy comparison
    plot_entropy_comparison(results)
    
    # 3. State trajectories (will load from eval if available)
    try:
        plot_state_trajectories()
    except Exception as e:
        print(f"Could not generate state trajectories: {e}")
    
    # 4. Population state distribution
    plot_population_state_distribution(states_hidden)
    
    # 5. Behavioral regime shifts
    plot_behavioral_regime_shifts(events_df, states_hidden)
    
    # 6. Training history
    plot_training_history()
    
    print("\nAll visualizations generated!")


if __name__ == '__main__':
    main()

