#!/usr/bin/env python3
"""
CLI script to run reasoning workflow from natural language prompt.

Usage:
    python scripts/run_from_prompt.py "What happens if we launch a promo in US_South for 8 weeks?"
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from reasoning.state import ReasoningState, Request, Pins
from reasoning.graph import create_reasoning_graph


def main():
    parser = argparse.ArgumentParser(
        description="Run Louiza Engine reasoning workflow from prompt"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Natural language prompt describing the market question"
    )
    parser.add_argument(
        "--data-version",
        type=str,
        default=None,
        help="Data version to pin (default: auto-detect latest)"
    )
    parser.add_argument(
        "--persona-version",
        type=str,
        default="PersonaSet_v1.json",
        help="PersonaSet version to use (default: PersonaSet_v1.json)"
    )
    parser.add_argument(
        "--enable-anchoring",
        action="store_true",
        help="Enable anchoring calibration"
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=5,
        help="Maximum number of scenarios (default: 5)"
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=10,
        help="Maximum number of runs (default: 10)"
    )
    parser.add_argument(
        "--max-agents",
        type=int,
        default=10000,
        help="Maximum number of agents per run (default: 10000)"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID (default: auto-generate)"
    )
    
    args = parser.parse_args()
    
    # Generate run ID
    if args.run_id:
        run_id = args.run_id
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"reasoning_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    # Determine data version
    data_version = args.data_version
    if not data_version:
        # Try to find latest data version
        data_dir = Path("data/synthetic")
        if data_dir.exists():
            versions = sorted([d.name for d in data_dir.iterdir() if d.is_dir()])
            if versions:
                data_version = versions[-1]
            else:
                data_version = "data_2026_01_08_run01"
        else:
            data_version = "data_2026_01_08_run01"
    
    # Create initial state
    state = ReasoningState(
        request=Request(
            user_prompt=args.prompt,
            simulation_budget={
                "max_scenarios": args.max_scenarios,
                "max_runs": args.max_runs,
                "max_agents": args.max_agents
            }
        ),
        pins=Pins(
            data_version=data_version,
            persona_version=args.persona_version
        ),
        run_id=run_id
    )
    
    # Enable anchoring if requested
    if args.enable_anchoring:
        state.anchoring.enabled = True
    
    # Create and run graph
    print(f"Starting reasoning workflow...")
    print(f"Run ID: {run_id}")
    print(f"Prompt: {args.prompt}")
    print(f"Data Version: {data_version}")
    print(f"Persona Version: {args.persona_version}")
    print()
    
    try:
        graph = create_reasoning_graph()
        
        # Run graph
        initial_state = {"state": state}
        final_state = graph.invoke(initial_state)
        
        final_reasoning_state = final_state["state"]
        
        # Print summary
        print("\n" + "="*60)
        print("Reasoning Workflow Completed")
        print("="*60)
        print(f"\nRun ID: {final_reasoning_state.run_id}")
        print(f"\nHypotheses Generated: {len(final_reasoning_state.hypotheses)}")
        for h in final_reasoning_state.hypotheses:
            print(f"  - {h.hypothesis_id}: {h.statement}")
        
        print(f"\nScenarios Created: {len(final_reasoning_state.scenario_specs)}")
        for s in final_reasoning_state.scenario_specs:
            print(f"  - {s.scenario_id} ({s.kind})")
        
        print(f"\nRuns Completed: {sum(1 for r in final_reasoning_state.runs if r.status == 'completed')}")
        print(f"Runs Failed: {sum(1 for r in final_reasoning_state.runs if r.status == 'failed')}")
        
        if final_reasoning_state.anchoring.status == "completed":
            print(f"\nAnchoring: Completed")
            print(f"  Improvement: {final_reasoning_state.anchoring.fit_summary.get('improvement_pct', 'N/A')}%")
        
        if final_reasoning_state.analysis.scenario_comparisons:
            print(f"\nScenario Comparisons:")
            for comp in final_reasoning_state.analysis.scenario_comparisons:
                print(f"  - {comp['scenario_id']}: {comp['mean_transactions_delta_pct']:.2f}% transactions delta")
        
        if final_reasoning_state.final_report.markdown_path:
            print(f"\nReport: {final_reasoning_state.final_report.markdown_path}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

