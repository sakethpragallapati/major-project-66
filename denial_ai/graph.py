"""Intake and triage as a LangGraph state graph.

load -> extract -> (cue | reason | clause | llm agents in parallel) -> supervisor.
If LangGraph is not installed the same nodes run one after another.
"""

import operator
from typing import Annotated, Optional, TypedDict

from .intake.extractor import extract_entities
from .intake.loader import clean_text, load_letter
from .schemas import AgentVote, CaseState, IntakeEntities, TriageDecision
from .triage.agents import default_agents
from .triage.supervisor import decide


class GraphState(TypedDict, total=False):
    source: Optional[str]
    raw_text: str
    entities: IntakeEntities
    votes: Annotated[list[AgentVote], operator.add]   # each agent appends its vote
    triage: TriageDecision


def _case(state):
    return CaseState(source=state.get("source"), raw_text=state.get("raw_text", ""),
                     entities=state.get("entities"))


def node_load(state):
    if state.get("raw_text"):
        return {"raw_text": clean_text(state["raw_text"])}
    return {"raw_text": load_letter(state["source"])}


def node_extract(state):
    return {"entities": extract_entities(state["raw_text"])}


def agent_node(agent):
    def run(state):
        return {"votes": [agent(_case(state))]}
    return run


def node_supervisor(state):
    return {"triage": decide(state.get("votes", []), entities=state.get("entities"))}


def build_graph(agents=None):
    agents = agents or default_agents()
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return None
    g = StateGraph(GraphState)
    g.add_node("load", node_load)
    g.add_node("extract", node_extract)
    g.add_node("supervisor", node_supervisor)
    g.add_edge(START, "load")
    g.add_edge("load", "extract")
    for a in agents:
        g.add_node(f"agent_{a.name}", agent_node(a))
        g.add_edge("extract", f"agent_{a.name}")
        g.add_edge(f"agent_{a.name}", "supervisor")
    g.add_edge("supervisor", END)
    return g.compile()


class Pipeline:
    def __init__(self, agents=None, use_langgraph=True):
        self.agents = agents or default_agents()
        self.graph = build_graph(self.agents) if use_langgraph else None

    def run(self, text=None, source=None):
        init = {"raw_text": text or "", "source": str(source) if source else None, "votes": []}
        if self.graph is not None:
            out = self.graph.invoke(init)
        else:
            out = dict(init)
            for node in (node_load, node_extract):
                out.update(node(out))
            for a in self.agents:
                out["votes"] = out["votes"] + agent_node(a)(out)["votes"]
            out.update(node_supervisor(out))
        # Votes arrive in completion order; sort them so output is stable.
        order = {a.name: i for i, a in enumerate(self.agents)}
        out["triage"].votes.sort(key=lambda v: order.get(v.agent, 99))
        return CaseState(source=out.get("source"), raw_text=out["raw_text"], entities=out["entities"],
                         votes=out["triage"].votes, triage=out["triage"])
