"""
LangGraph workflow definition for reasoning layer.

Implements the prompt-to-simulation pipeline.

For POC, uses a simple sequential runner. Can be upgraded to LangGraph when available.
"""

from typing import TypedDict, Dict, Any
from reasoning.state import ReasoningState
from reasoning.nodes.parse_request import parse_request
from reasoning.nodes.generate_hypotheses import generate_hypotheses
from reasoning.nodes.retrieve_evidence import retrieve_evidence
from reasoning.nodes.critic_check import critic_check
from reasoning.nodes.scenario_builder import scenario_builder
from reasoning.nodes.run_planner import run_planner
from reasoning.nodes.simulation_runner import simulation_runner
from reasoning.nodes.anchoring_runner import anchoring_runner
from reasoning.nodes.comparator import comparator
from reasoning.nodes.insight_synthesizer import insight_synthesizer
from reasoning.nodes.report_writer import report_writer


class GraphState(TypedDict):
    """TypedDict wrapper for LangGraph state."""
    state: ReasoningState


class SequentialGraphRunner:
    """
    Simple sequential graph runner for POC.
    
    Executes nodes in order without LangGraph dependency.
    """
    
    def __init__(self):
        self.nodes = [
            ("parse_request", parse_request),
            ("generate_hypotheses", generate_hypotheses),
            ("retrieve_evidence", retrieve_evidence),
            ("critic_check", critic_check),
            ("scenario_builder", scenario_builder),
            ("run_planner", run_planner),
            ("simulation_runner", simulation_runner),
            ("anchoring_runner", anchoring_runner),
            ("comparator", comparator),
            ("insight_synthesizer", insight_synthesizer),
            ("report_writer", report_writer),
        ]
    
    def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute graph sequentially.
        
        Args:
            initial_state: Initial state dict with 'state' key
            
        Returns:
            Final state dict
        """
        state = initial_state["state"]
        
        for node_name, node_func in self.nodes:
            try:
                state = node_func(state)
            except Exception as e:
                print(f"Error in node {node_name}: {e}")
                raise
        
        return {"state": state}


def create_reasoning_graph():
    """
    Create reasoning workflow.
    
    For POC, returns a sequential runner. Can be upgraded to LangGraph when available.
    
    Topology:
    ParseRequest → GenerateHypotheses → RetrieveEvidence → CriticCheck
    → ScenarioBuilder → RunPlanner → SimulationRunner → AnchoringRunner
    → Comparator → InsightSynthesizer → ReportWriter
    """
    try:
        # Try to use LangGraph if available
        from langgraph.graph import StateGraph, END
        
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("parse_request", lambda state: {"state": parse_request(state["state"])})
        workflow.add_node("generate_hypotheses", lambda state: {"state": generate_hypotheses(state["state"])})
        workflow.add_node("retrieve_evidence", lambda state: {"state": retrieve_evidence(state["state"])})
        workflow.add_node("critic_check", lambda state: {"state": critic_check(state["state"])})
        workflow.add_node("scenario_builder", lambda state: {"state": scenario_builder(state["state"])})
        workflow.add_node("run_planner", lambda state: {"state": run_planner(state["state"])})
        workflow.add_node("simulation_runner", lambda state: {"state": simulation_runner(state["state"])})
        workflow.add_node("anchoring_runner", lambda state: {"state": anchoring_runner(state["state"])})
        workflow.add_node("comparator", lambda state: {"state": comparator(state["state"])})
        workflow.add_node("insight_synthesizer", lambda state: {"state": insight_synthesizer(state["state"])})
        workflow.add_node("report_writer", lambda state: {"state": report_writer(state["state"])})
        
        # Define edges
        workflow.set_entry_point("parse_request")
        workflow.add_edge("parse_request", "generate_hypotheses")
        workflow.add_edge("generate_hypotheses", "retrieve_evidence")
        workflow.add_edge("retrieve_evidence", "critic_check")
        workflow.add_edge("critic_check", "scenario_builder")
        workflow.add_edge("scenario_builder", "run_planner")
        workflow.add_edge("run_planner", "simulation_runner")
        workflow.add_edge("simulation_runner", "anchoring_runner")
        workflow.add_edge("anchoring_runner", "comparator")
        workflow.add_edge("comparator", "insight_synthesizer")
        workflow.add_edge("insight_synthesizer", "report_writer")
        workflow.add_edge("report_writer", END)
        
        return workflow.compile()
    except ImportError:
        # Fallback to sequential runner
        return SequentialGraphRunner()

