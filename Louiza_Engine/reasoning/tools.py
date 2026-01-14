"""
Tools for calling LPM, Anchoring, Data Engine, and Visualizations.

These are wrappers that the reasoning layer uses to interact with other layers.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from lpm.simulator import LPMSimulator
from pme.pme_runner import PMERunner
from data_engine.loaders import DataLoader
from anchoring.anchoring_runner import AnchoringRunner
from observability.plots import PlotGenerator
from common.versioning import hash_scenario_config


def load_personaset(persona_version: str) -> Any:
    """
    Load PersonaSet.
    
    Args:
        persona_version: PersonaSet version or path
        
    Returns:
        PersonaSet object
    """
    pme_runner = PMERunner(data_version="dummy")
    if Path(persona_version).exists():
        return pme_runner.load_personaset(persona_version)
    else:
        # Try with .json extension
        persona_path = Path(f"{persona_version}.json")
        if persona_path.exists():
            return pme_runner.load_personaset(str(persona_path))
        else:
            raise FileNotFoundError(f"PersonaSet not found: {persona_version}")


def run_simulation(
    scenario_spec: Dict[str, Any],
    persona_version: str,
    data_version: str,
    seed: int,
    num_agents: int,
    output_dir: str
) -> Dict[str, str]:
    """
    Run LPM simulation.
    
    Args:
        scenario_spec: Scenario specification dict
        persona_version: PersonaSet version
        data_version: Data version
        seed: Random seed
        num_agents: Number of agents
        output_dir: Output directory
        
    Returns:
        Dictionary with artifact paths
    """
    # Load PersonaSet
    personaset = load_personaset(persona_version)
    
    # Load data
    data_loader = DataLoader("data/synthetic", data_version)
    
    # Create simulator
    simulator = LPMSimulator(
        personaset=personaset,
        data_loader=data_loader,
        scenario_config=scenario_spec,
        num_agents=num_agents,
        seed=seed
    )
    
    # Run simulation
    start_week = 1
    num_weeks = scenario_spec.get("time_horizon_weeks", 12)
    
    results = simulator.run(
        start_week=start_week,
        num_weeks=num_weeks,
        output_dir=output_dir
    )
    
    return {
        "simulated_metrics_path": str(Path(output_dir) / "simulated_metrics_brand_week_region.csv"),
        "persona_contrib_path": str(Path(output_dir) / "persona_contributions.csv"),
        "run_metadata_path": str(Path(output_dir) / "run_metadata.json")
    }


def run_anchoring(
    observed_metrics_path: str,
    simulated_metrics_path: str,
    persona_contributions_path: str,
    persona_version: str,
    output_dir: str,
    train_weeks: Optional[list] = None,
    holdout_weeks: Optional[list] = None
) -> Dict[str, str]:
    """
    Run anchoring calibration.
    
    Args:
        observed_metrics_path: Path to observed metrics CSV
        simulated_metrics_path: Path to simulated metrics CSV
        persona_contributions_path: Path to persona contributions CSV
        persona_version: PersonaSet version
        output_dir: Output directory
        
    Returns:
        Dictionary with artifact paths
    """
    # Load data
    observed_metrics = pd.read_csv(observed_metrics_path)
    simulated_metrics = pd.read_csv(simulated_metrics_path)
    persona_contributions = pd.read_csv(persona_contributions_path)
    
    # Load PersonaSet
    personaset = load_personaset(persona_version)
    
    # Create anchoring runner
    runner = AnchoringRunner(
        personaset=personaset,
        observed_metrics=observed_metrics,
        simulated_metrics=simulated_metrics,
        persona_contributions=persona_contributions
    )
    
    # Run anchoring (handle case where holdout_weeks might be None or empty)
    if holdout_weeks is None or len(holdout_weeks) == 0:
        # Use default split if no holdout weeks specified
        results = runner.run(
            train_weeks=train_weeks,
            holdout_weeks=None  # Will use default split
        )
    else:
        results = runner.run(
            train_weeks=train_weeks,
            holdout_weeks=holdout_weeks
        )
    
    # Save results
    runner.save_results(results, output_dir)
    
    return {
        "patch_path": str(Path(output_dir) / "anchoring_patch.json"),
        "report_path": str(Path(output_dir) / "anchoring_report.json"),
        "diagnostics_path": str(Path(output_dir) / "anchoring_diagnostics.json"),
        "anchored_metrics_path": str(Path(output_dir) / "anchored_metrics_brand_week_region.csv")
    }


def generate_visualizations(
    run_id: str,
    artifacts_dir: str,
    output_dir: str,
    data_version: Optional[str] = None,
    personaset_path: Optional[str] = None,
    anchoring_dir: Optional[str] = None
):
    """
    Generate all visualizations.
    
    Args:
        run_id: Run ID
        artifacts_dir: Directory with simulation artifacts
        output_dir: Output directory for plots
        data_version: Optional data version
        personaset_path: Optional PersonaSet path
        anchoring_dir: Optional anchoring results directory
    """
    generator = PlotGenerator(output_dir)
    
    # Load simulation artifacts
    simulated_metrics = pd.read_csv(Path(artifacts_dir) / "simulated_metrics_brand_week_region.csv")
    persona_contributions = pd.read_csv(Path(artifacts_dir) / "persona_contributions.csv")
    
    # Generate LPM plots
    generator.plot_lpm_outcomes(simulated_metrics)
    generator.plot_persona_contributions(persona_contributions)
    
    # Generate Data Engine plots if data version provided
    if data_version:
        try:
            data_loader = DataLoader("data/synthetic", data_version)
            observed_metrics = data_loader.load_observed_metrics()
            price_schedule = data_loader.load_price_schedule()
            promo_schedule = data_loader.load_promo_schedule()
            
            generator.plot_data_engine_sanity(observed_metrics, price_schedule, promo_schedule)
            generator.plot_data_coverage(observed_metrics)
        except Exception:
            pass  # Skip if data not available
    
    # Generate PME plots if PersonaSet provided
    if personaset_path:
        try:
            generator.plot_persona_overview(personaset_path)
        except Exception:
            pass
    
    # Generate Anchoring plots if anchoring directory provided
    if anchoring_dir:
        try:
            anchored_metrics = pd.read_csv(Path(anchoring_dir) / "anchored_metrics_brand_week_region.csv")
            anchoring_report = str(Path(anchoring_dir) / "anchoring_report.json")
            
            if data_version:
                data_loader = DataLoader("data/synthetic", data_version)
                observed_metrics = data_loader.load_observed_metrics()
                generator.plot_anchoring_before_after(
                    observed_metrics,
                    simulated_metrics,
                    anchored_metrics
                )
            
            generator.plot_anchoring_error_reduction(anchoring_report)
            
            if personaset_path:
                anchoring_patch = str(Path(anchoring_dir) / "anchoring_patch.json")
                generator.plot_persona_weight_adjustments(anchoring_patch, personaset_path)
        except Exception:
            pass

