"""
Phase 3: Large Population Simulation
Main simulation script
"""

import torch
import pandas as pd
import numpy as np
import os
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'visualizations'))

from models_phase3 import Agent, Environment, PopulationSimulator
from models_phase2 import BehavioralDynamicEngine
from train_phase2 import load_phase1_models
from visualize import EmbeddingVisualizer

def encode_all_products_and_contexts(phase1_models, products_df, contexts_df, vocabularies, device='cpu'):
    """Pre-compute all product and context embeddings"""
    print("Encoding all products and contexts...")
    
    product_embeddings = {}
    context_embeddings = {}
    
    # Create mappings
    time_of_days = sorted(contexts_df['time_of_day'].unique())
    locations = sorted(contexts_df['location'].unique())
    occasions = sorted(contexts_df['occasion'].unique())
    time_of_day_to_idx = {td: idx for idx, td in enumerate(time_of_days)}
    location_to_idx = {loc: idx for idx, loc in enumerate(locations)}
    occasion_to_idx = {occ: idx for idx, occ in enumerate(occasions)}
    
    # Encode products
    for _, product in products_df.iterrows():
        product_id = product['product_id']
        
        # Encode ingredients
        ingredients = product['ingredients'].split(',')
        ingredient_ids = []
        for ing in ingredients[:10]:
            ing_id = vocabularies['ingredient'].word_to_idx.get(ing.strip(), 0)
            ingredient_ids.append(ing_id)
        while len(ingredient_ids) < 10:
            ingredient_ids.append(1)
        
        # Encode tags
        tags = product['sensory_tags'].split(',')
        tag_ids = []
        for tag in tags[:8]:
            tag_id = vocabularies['tag'].word_to_idx.get(tag.strip(), 0)
            tag_ids.append(tag_id)
        while len(tag_ids) < 8:
            tag_ids.append(1)
        
        # Nutrition
        nutrition = torch.FloatTensor([
            product['sugar_g'],
            product['caffeine_mg'],
            product['calories'],
            product['protein_g']
        ]).unsqueeze(0).to(device)
        
        # Text
        text_ids = vocabularies['text'].encode(product['description'], 50)
        
        # Encode
        ingredient_ids_t = torch.LongTensor([ingredient_ids]).to(device)
        tag_ids_t = torch.LongTensor([tag_ids]).to(device)
        text_ids_t = torch.LongTensor([text_ids]).to(device)
        
        with torch.no_grad():
            z_product = phase1_models['product'](
                ingredient_ids_t, tag_ids_t, nutrition, text_ids_t
            )
            product_embeddings[product_id] = z_product.cpu().numpy()[0]
    
    # Encode contexts
    for _, context in contexts_df.iterrows():
        context_id = context['context_id']
        
        time_of_day_id = time_of_day_to_idx[context['time_of_day']]
        location_id = location_to_idx[context['location']]
        occasion_id = occasion_to_idx[context['occasion']]
        price = torch.FloatTensor([[context['price_shown']]]).to(device)
        
        time_ids_t = torch.LongTensor([[time_of_day_id]]).to(device)
        location_ids_t = torch.LongTensor([[location_id]]).to(device)
        occasion_ids_t = torch.LongTensor([[occasion_id]]).to(device)
        
        with torch.no_grad():
            z_context = phase1_models['context'](
                time_ids_t, location_ids_t, occasion_ids_t, price
            )
            context_embeddings[context_id] = z_context.cpu().numpy()[0]
    
    print(f"Encoded {len(product_embeddings)} products and {len(context_embeddings)} contexts")
    return product_embeddings, context_embeddings


def encode_segments(phase1_models, segments_df, device='cpu'):
    """Encode all segments"""
    segment_embeddings = {}
    
    # Create mappings
    age_buckets = sorted(segments_df['age_bucket'].unique())
    regions = sorted(segments_df['region'].unique())
    psychographics = sorted(segments_df['psychographic'].unique())
    age_to_idx = {age: idx for idx, age in enumerate(age_buckets)}
    region_to_idx = {reg: idx for idx, reg in enumerate(regions)}
    psychographic_to_idx = {psy: idx for idx, psy in enumerate(psychographics)}
    
    for _, segment in segments_df.iterrows():
        segment_id = segment['segment_id']
        
        age_id = age_to_idx[segment['age_bucket']]
        region_id = region_to_idx[segment['region']]
        psychographic_id = psychographic_to_idx[segment['psychographic']]
        
        age_ids_t = torch.LongTensor([[age_id]]).to(device)
        region_ids_t = torch.LongTensor([[region_id]]).to(device)
        psychographic_ids_t = torch.LongTensor([[psychographic_id]]).to(device)
        
        with torch.no_grad():
            z_segment = phase1_models['segment'](
                age_ids_t, region_ids_t, psychographic_ids_t
            )
            segment_embeddings[segment_id] = z_segment.cpu().numpy()[0]
    
    return segment_embeddings


def run_simulation(n_agents: int = 10,
                  n_days: int = 30,
                  interactions_per_day: int = 1,
                  phase1_checkpoint: str = 'checkpoints/best_model.pt',
                  phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                  data_dir: str = 'data',
                  output_dir: str = 'simulations',
                  use_intent_sampling: bool = True,
                  sample_outcomes: bool = False,
                  device: str = None):
    """Run Phase 3 simulation"""
    
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Load Phase 1 models
    print("Loading Phase 1 models...")
    phase1_models, vocabularies = load_phase1_models(phase1_checkpoint, data_dir, device)
    
    # Load Phase 2 model
    print("Loading Phase 2 model...")
    checkpoint = torch.load(phase2_checkpoint, map_location=device, weights_only=False)
    phase2_model = BehavioralDynamicEngine(
        segment_dim=64,
        product_dim=128,
        context_dim=64,
        state_dim=128,
        hidden_dim=256
    )
    phase2_model.load_state_dict(checkpoint['model_state_dict'])
    phase2_model = phase2_model.to(device)
    phase2_model.eval()
    
    # Load data
    print("Loading data...")
    products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    contexts_df = pd.read_csv(os.path.join(data_dir, 'contexts.csv'))
    segments_df = pd.read_csv(os.path.join(data_dir, 'segments.csv'))
    
    # Pre-compute embeddings
    product_embeddings, context_embeddings = encode_all_products_and_contexts(
        phase1_models, products_df, contexts_df, vocabularies, device
    )
    segment_embeddings_dict = encode_segments(phase1_models, segments_df, device)
    
    # Create environment with advanced features
    print("Creating environment...")
    environment = Environment(
        products_df, contexts_df, product_embeddings, context_embeddings,
        enable_dynamic_prices=True,
        enable_new_launches=True,
        enable_macro_context=True
    )
    
    # Create simulator with advanced features
    print("Creating simulator...")
    simulator = PopulationSimulator(
        phase2_model, phase1_models, environment, device,
        enable_social_influence=True,
        state_init_noise=0.1  # Probabilistic state initialization
    )
    
    # Initialize agents with proper segment embeddings
    print(f"Initializing {n_agents} agents...")
    # Override the _encode_segment method by setting segment embeddings directly
    for agent in simulator.agents:
        if agent.segment_id in segment_embeddings_dict:
            agent.z_segment = torch.FloatTensor(segment_embeddings_dict[agent.segment_id])
            # Re-initialize state with correct segment
            with torch.no_grad():
                s_0 = phase2_model.initialize_state(
                    agent.z_segment.unsqueeze(0).to(device)
                )
                agent.s_t = s_0[0].cpu()
    
    # Actually initialize agents properly
    # Create agents manually with correct embeddings
    simulator.agents = []
    for i in range(n_agents):
        # Sample segment
        segment = segments_df.sample(1).iloc[0]
        segment_id = segment['segment_id']
        z_segment = torch.FloatTensor(segment_embeddings_dict[segment_id])
        
        # Initialize state probabilistically: s_0 ~ p(s_0 | segment)
        with torch.no_grad():
            # Base deterministic state
            s_0_base = phase2_model.initialize_state(z_segment.unsqueeze(0).to(device))
            s_0_base = s_0_base[0].cpu()
            
            # Add noise for probabilistic initialization
            noise = torch.randn_like(s_0_base) * 0.1  # 10% noise
            s_0 = s_0_base + noise
            # Renormalize
            s_0 = torch.nn.functional.normalize(s_0, p=2, dim=0)
        
        # Sample personality
        personality = {
            'novelty_bias': np.random.uniform(0.0, 1.0),
            'health_focus': np.random.uniform(0.0, 1.0),
            'exploration_rate': np.random.uniform(0.05, 0.2),
            'social_susceptibility': np.random.uniform(0.0, 0.5)
        }
        
        agent = Agent(
            agent_id=i,
            segment_id=segment_id,
            z_segment=z_segment,
            s_t=s_0,
            personality=personality
        )
        simulator.agents.append(agent)
    
    print(f"Initialized {len(simulator.agents)} agents")
    
    # Run simulation
    print("\nRunning simulation...")
    results = simulator.simulate(
        n_days=n_days,
        interactions_per_day=interactions_per_day,
        use_intent_sampling=use_intent_sampling,
        sample_outcomes=sample_outcomes
    )
    
    # Get results
    results_df = simulator.get_results_dataframe()
    stats = simulator.get_aggregate_statistics()
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    
    # Save intent trajectories
    results_df.to_csv(os.path.join(output_dir, 'intent_trajectories.csv'), index=False)
    print(f"\nSaved intent trajectories to {output_dir}/intent_trajectories.csv")
    
    # Save statistics
    with open(os.path.join(output_dir, 'simulation_stats.json'), 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"Saved statistics to {output_dir}/simulation_stats.json")
    
    # Print summary
    print("\n=== Simulation Summary ===")
    print(f"Total interactions: {stats['total_interactions']}")
    print(f"Unique agents: {stats['unique_agents']}")
    print(f"Unique products: {stats['unique_products']}")
    print(f"Mean intent: {stats['mean_intent']:.4f}")
    print(f"\nIntent by category:")
    for cat, intent in stats['intent_by_category'].items():
        print(f"  {cat}: {intent:.4f}")
    
    return simulator, results_df, stats


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_agents', type=int, default=10)
    parser.add_argument('--n_days', type=int, default=30)
    parser.add_argument('--interactions_per_day', type=int, default=1)
    parser.add_argument('--phase1_checkpoint', type=str, default='checkpoints/best_model.pt')
    parser.add_argument('--phase2_checkpoint', type=str, default='checkpoints_phase2/best_model_phase2.pt')
    parser.add_argument('--data_dir', type=str, default='data')
    parser.add_argument('--output_dir', type=str, default='simulations')
    parser.add_argument('--use_intent_sampling', action='store_true', default=True)
    parser.add_argument('--sample_outcomes', action='store_true', default=False)
    
    args = parser.parse_args()
    
    run_simulation(
        n_agents=args.n_agents,
        n_days=args.n_days,
        interactions_per_day=args.interactions_per_day,
        phase1_checkpoint=args.phase1_checkpoint,
        phase2_checkpoint=args.phase2_checkpoint,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        use_intent_sampling=args.use_intent_sampling,
        sample_outcomes=args.sample_outcomes
    )

