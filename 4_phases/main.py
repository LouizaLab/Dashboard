"""
Main entry point for 4-Phase Pipeline
Unified interface for running all phases
"""

import argparse
import os
import sys

# Add subdirectories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data_generation'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase1'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase3'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase4'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'visualizations'))

from data_generator import SyntheticDataGenerator
from train_phase1 import train_phase1
from visualize import EmbeddingVisualizer
from train_phase2 import train_phase2
from simulate_phase3 import run_simulation
from phase4_main import run_phase4

def main():
    parser = argparse.ArgumentParser(description='4-Phase Pipeline: Complete Intent Modeling System')
    parser.add_argument('--mode', type=str, required=True,
                       choices=['generate_data', 'train', 'visualize', 'all', 
                               'train_phase2', 'simulate_phase3',
                               'phase4', 'all_phases'],
                       help='Mode to run')
    parser.add_argument('--data_dir', type=str, default='data',
                       help='Directory for data files')
    parser.add_argument('--checkpoint_dir', type=str, default='checkpoints',
                       help='Directory for model checkpoints')
    parser.add_argument('--viz_dir', type=str, default='visualizations',
                       help='Directory for visualizations')
    
    # Data generation args
    parser.add_argument('--n_products', type=int, default=50,
                       help='Number of products to generate')
    parser.add_argument('--n_segments', type=int, default=5,
                       help='Number of segments to generate')
    parser.add_argument('--n_contexts', type=int, default=100,
                       help='Number of contexts to generate')
    parser.add_argument('--n_logs', type=int, default=1000,
                       help='Number of intent logs to generate')
    
    # Training args
    parser.add_argument('--batch_size', type=int, default=32,
                       help='Batch size for training')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                       help='Learning rate')
    parser.add_argument('--n_epochs', type=int, default=50,
                       help='Number of training epochs')
    
    # Phase 2 args
    parser.add_argument('--phase1_checkpoint', type=str, default='checkpoints/best_model.pt',
                       help='Path to Phase 1 checkpoint')
    parser.add_argument('--sequence_length', type=int, default=10,
                       help='Sequence length for Phase 2')
    parser.add_argument('--phase2_batch_size', type=int, default=8,
                       help='Batch size for Phase 2 training')
    parser.add_argument('--phase2_n_epochs', type=int, default=30,
                       help='Number of epochs for Phase 2')
    
    # Phase 3 args
    parser.add_argument('--phase2_checkpoint', type=str, default='checkpoints_phase2/best_model_phase2.pt',
                       help='Path to Phase 2 checkpoint')
    parser.add_argument('--n_agents', type=int, default=10,
                       help='Number of agents for Phase 3 simulation')
    parser.add_argument('--sim_days', type=int, default=30,
                       help='Number of days to simulate')
    parser.add_argument('--interactions_per_day', type=int, default=1,
                       help='Interactions per day per agent')
    parser.add_argument('--sim_output_dir', type=str, default='simulations',
                       help='Output directory for simulation results')
    
    # Phase 4 args
    parser.add_argument('--simulation_data', type=str, default=None,
                       help='Path to Phase 3 simulation data (intent_trajectories.csv)')
    parser.add_argument('--real_data_path', type=str, default=None,
                       help='Path to real intent data for Phase 4 calibration')
    parser.add_argument('--output_dir', type=str, default=None,
                       help='Output directory for Phase 4 results (alias for --phase4_output_dir)')
    parser.add_argument('--phase4_output_dir', type=str, default='phase4_output',
                       help='Output directory for Phase 4 results')
    
    args = parser.parse_args()
    
    if args.mode == 'generate_data' or args.mode == 'all':
        print("=" * 60)
        print("Generating Synthetic Data")
        print("=" * 60)
        generator = SyntheticDataGenerator(seed=42)
        data = generator.generate_all_data(
            n_products=args.n_products,
            n_segments=args.n_segments,
            n_contexts=args.n_contexts,
            n_logs=args.n_logs
        )
        generator.save_data(data, output_dir=args.data_dir)
        print("\nData generation complete!\n")
    
    if args.mode == 'train' or args.mode == 'all':
        print("=" * 60)
        print("Training Phase 1 Models")
        print("=" * 60)
        train_phase1(
            data_dir=args.data_dir,
            output_dir=args.checkpoint_dir,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            n_epochs=args.n_epochs
        )
        print("\nTraining complete!\n")
    
    if args.mode == 'visualize' or args.mode == 'all':
        print("=" * 60)
        print("Generating Visualizations")
        print("=" * 60)
        model_path = os.path.join(args.checkpoint_dir, 'best_model.pt')
        if not os.path.exists(model_path):
            print(f"Error: Model not found at {model_path}")
            print("Please train the model first.")
        else:
            visualizer = EmbeddingVisualizer(model_path, args.data_dir)
            visualizer.visualize_product_embeddings(args.viz_dir)
            visualizer.visualize_training_curves(model_path, args.viz_dir)
            visualizer.analyze_embeddings(args.viz_dir)
            print("\nVisualization complete!\n")
    
    if args.mode == 'train_phase2' or args.mode == 'all_phases':
        print("=" * 60)
        print("Training Phase 2: Behavioral Dynamic Engine")
        print("=" * 60)
        phase1_path = args.phase1_checkpoint
        if not os.path.exists(phase1_path):
            print(f"Error: Phase 1 model not found at {phase1_path}")
            print("Please train Phase 1 first.")
        else:
            train_phase2(
                phase1_checkpoint=phase1_path,
                data_dir=args.data_dir,
                output_dir='checkpoints_phase2',
                batch_size=args.phase2_batch_size,
                learning_rate=args.learning_rate,
                n_epochs=args.phase2_n_epochs,
                sequence_length=args.sequence_length
            )
            print("\nPhase 2 Training complete!\n")
    
    if args.mode == 'simulate_phase3' or args.mode == 'all_phases':
        print("=" * 60)
        print("Running Phase 3: Large Population Simulation")
        print("=" * 60)
        phase2_path = args.phase2_checkpoint
        if not os.path.exists(phase2_path):
            print(f"Error: Phase 2 model not found at {phase2_path}")
            print("Please train Phase 2 first.")
        else:
            run_simulation(
                n_agents=args.n_agents,
                n_days=args.sim_days,
                interactions_per_day=args.interactions_per_day,
                phase1_checkpoint=args.phase1_checkpoint,
                phase2_checkpoint=phase2_path,
                data_dir=args.data_dir,
                output_dir=args.sim_output_dir,
                use_intent_sampling=True,
                sample_outcomes=False
            )
            print("\nPhase 3 Simulation complete!\n")
    
    if args.mode == 'phase4' or args.mode == 'all_phases':
        print("=" * 60)
        print("Running Phase 4: Ground Truth Anchoring + Signals")
        print("=" * 60)
        
        # Determine simulation data path
        if args.simulation_data:
            sim_data_path = args.simulation_data
        else:
            sim_data_path = os.path.join(args.sim_output_dir, 'intent_trajectories.csv')
        
        if not os.path.exists(sim_data_path):
            print(f"Error: Simulation data not found at {sim_data_path}")
            print("Please run Phase 3 simulation first or provide --simulation_data path.")
        else:
            # Auto-detect real data if not provided
            real_data_path = args.real_data_path
            if not real_data_path:
                default_real_path = 'data/real_intent_data.csv'
                if os.path.exists(default_real_path):
                    real_data_path = default_real_path
                    print(f"Auto-detected real data: {real_data_path}")
            
            # Determine output directory (--output_dir takes precedence over --phase4_output_dir)
            output_dir = args.output_dir if args.output_dir else args.phase4_output_dir
            
            run_phase4(
                simulation_data_path=sim_data_path,
                real_data_path=real_data_path,
                output_dir=output_dir,
                generate_signals=True,
                calibrate=True,
                anchor=True
            )
            print("\nPhase 4 Complete!\n")
    
    if args.mode == 'all':
        print("=" * 60)
        print("Phase 1 Complete!")
        print("=" * 60)
    elif args.mode == 'all_phases':
        print("=" * 60)
        print("All Phases Complete!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("Complete!")
        print("=" * 60)

if __name__ == '__main__':
    main()
