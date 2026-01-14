"""
Node K: ReportWriter

Saves final markdown report and artifact index.
"""

from pathlib import Path
from datetime import datetime
from reasoning.state import ReasoningState
from reasoning.tools import generate_visualizations


def report_writer(state: ReasoningState) -> ReasoningState:
    """
    Write final report and generate visualizations.
    
    Saves markdown report and artifact index.
    """
    report_dir = Path("runs") / state.run_id / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate visualizations
    artifacts_dir = Path("runs") / state.run_id / state.runs[0].run_id if state.runs else None
    plots_dir = report_dir / "plots"
    
    if artifacts_dir and artifacts_dir.exists():
        try:
            generate_visualizations(
                run_id=state.run_id,
                artifacts_dir=str(artifacts_dir),
                output_dir=str(plots_dir),
                data_version=state.pins.data_version,
                personaset_path=state.pins.persona_version,
                anchoring_dir=str(Path("runs") / state.run_id / "anchoring") if state.anchoring.status == "completed" else None
            )
        except Exception as e:
            print(f"Warning: Visualization generation failed: {e}")
    
    # Generate markdown report
    report_lines = [
        "# Louiza Engine Reasoning Report",
        "",
        f"**Run ID**: {state.run_id}",
        f"**Created**: {state.created_at.isoformat()}",
        "",
        "## Request",
        "",
        f"**Prompt**: {state.request.user_prompt}",
        "",
        f"- Time Horizon: {state.request.constraints.time_horizon_weeks} weeks",
        f"- Regions: {', '.join(state.request.constraints.regions) if state.request.constraints.regions else 'All'}",
        f"- Brands: {', '.join(state.request.constraints.brands) if state.request.constraints.brands else 'All'}",
        "",
        "## Hypotheses",
        ""
    ]
    
    for hypothesis in state.hypotheses:
        report_lines.extend([
            f"### {hypothesis.hypothesis_id}",
            f"{hypothesis.statement}",
            "",
            f"- Metrics: {', '.join(hypothesis.metrics)}",
            f"- Baseline: {hypothesis.baseline}",
            f"- Treatment: {hypothesis.treatment}",
            ""
        ])
    
    report_lines.extend([
        "## Scenarios",
        ""
    ])
    
    for scenario in state.scenario_specs:
        report_lines.extend([
            f"### {scenario.scenario_id}",
            f"- Type: {scenario.kind}",
            f"- Time Horizon: {scenario.time_horizon_weeks} weeks",
            f"- Interventions: {len(scenario.interventions)}",
            ""
        ])
    
    report_lines.extend([
        "## Results Summary",
        "",
        state.final_report.summary,
        "",
        "## Scenario Comparisons",
        ""
    ])
    
    for comparison in state.analysis.scenario_comparisons:
        report_lines.extend([
            f"### {comparison['scenario_id']} vs {comparison['baseline_id']}",
            f"- Transactions Delta: {comparison['mean_transactions_delta_pct']:.2f}%",
            f"- Revenue Delta: {comparison['mean_revenue_delta_pct']:.2f}%",
            ""
        ])
    
    report_lines.extend([
        "## Provenance",
        "",
        f"- Data Version: {state.pins.data_version}",
        f"- Persona Version: {state.pins.persona_version}",
        f"- IBDE Version: {state.pins.ibde_version}",
        f"- LPM Version: {state.pins.lpm_version}",
        "",
        "## Artifacts",
        ""
    ])
    
    for run in state.runs:
        if run.status == "completed":
            report_lines.extend([
                f"### {run.run_id}",
                f"- Scenario: {run.scenario_id}",
                f"- Seed: {run.seed}",
                f"- Agents: {run.num_agents}",
                ""
            ])
    
    if state.anchoring.status == "completed":
        report_lines.extend([
            "## Anchoring",
            "",
            f"- Status: {state.anchoring.status}",
            f"- Baseline Loss: {state.anchoring.fit_summary.get('baseline_loss', 'N/A')}",
            f"- Final Loss: {state.anchoring.fit_summary.get('final_loss', 'N/A')}",
            f"- Improvement: {state.anchoring.fit_summary.get('improvement_pct', 'N/A')}%",
            ""
        ])
    
    # Write report
    report_path = report_dir / "report.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))
    
    state.final_report.markdown_path = str(report_path)
    
    return state

