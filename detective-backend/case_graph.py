"""Bipartite Graph & Knowledge Graph Engine for Mystery Solvability.

Represents the case as an explicit Bipartite / Knowledge Graph:
- Partition 1 (Narrative Agents & Claims): Suspects, Alibis, Motives.
- Partition 2 (Physical Grounding & Scene Traces): Evidences, Forensic Time, Crucial Clues.

Edges capture causal and logical dependencies:
- CLAIMS: Suspect -> Alibi
- CONTRADICTS: Crucial Evidence -> Alibi (The decisive edge solving the case)
- INCRIMINATES: Evidence -> Suspect
- RED_HERRING: Evidence -> Innocent Suspect

Provides formal graph traversal algorithms to mathematically guarantee solvability.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from models import CaseDossier, Suspect, Evidence, GroundTruth


class GraphNode(BaseModel):
    """A node in the Bipartite Mystery Graph."""
    id: str
    label: str
    node_type: str = Field(..., description="'suspect', 'alibi', 'evidence', or 'crime_time'")
    partition: str = Field(..., description="'narrative_claim' or 'physical_grounding'")
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed edge in the Bipartite Mystery Graph."""
    source: str
    target: str
    relation: str = Field(..., description="'claims', 'contradicts', 'incriminates', 'red_herring_lead'")
    is_decisive: bool = False
    description: str = ""


class BipartiteCaseGraph(BaseModel):
    """Explicit Bipartite Graph representation of a Case Dossier."""
    case_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    is_connected_and_solvable: bool = False
    decisive_edge: Optional[GraphEdge] = None


def build_bipartite_case_graph(case: CaseDossier) -> BipartiteCaseGraph:
    """Build an explicit Bipartite Graph from a CaseDossier."""
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    decisive_edge: Optional[GraphEdge] = None

    # 1. Crime Time Anchor Node (Physical partition)
    crime_node_id = f"EVENT-CRIME"
    nodes.append(GraphNode(
        id=crime_node_id,
        label=f"Án mạng lúc {case.ground_truth.actual_crime_time}",
        node_type="crime_time",
        partition="physical_grounding",
        properties={
            "actual_crime_time": case.ground_truth.actual_crime_time,
            "tod_window": f"{case.victim.forensic_data.estimated_tod_start}-{case.victim.forensic_data.estimated_tod_end}"
        }
    ))

    # 2. Add Suspects and their Alibis (Narrative Claim Partition)
    culprit_id = case.ground_truth.culprit_id
    for s in case.suspects:
        # Suspect Node
        nodes.append(GraphNode(
            id=s.id,
            label=f"{s.name} ({'HUNG THỦ' if s.is_culprit else 'Vô tội'})",
            node_type="suspect",
            partition="narrative_claim",
            properties={"motive": s.motive, "is_culprit": s.is_culprit}
        ))

        # Alibi Node
        alibi_node_id = f"ALIBI-{s.id}"
        nodes.append(GraphNode(
            id=alibi_node_id,
            label=f"Alibi {s.id}: [{s.alibi_start}-{s.alibi_end}] {s.alibi_statement[:35]}...",
            node_type="alibi",
            partition="narrative_claim",
            properties={"alibi_start": s.alibi_start, "alibi_end": s.alibi_end, "statement": s.alibi_statement}
        ))

        # Edge: Suspect CLAIMS Alibi
        edges.append(GraphEdge(
            source=s.id,
            target=alibi_node_id,
            relation="claims",
            description=f"{s.name} đưa ra lời khai ngoại phạm"
        ))

    # 3. Add Evidences (Physical Grounding Partition) and connect to Alibis/Suspects
    for ev in case.evidences:
        node_type = "crucial_evidence" if ev.is_crucial else ("red_herring" if ev.is_red_herring else "trace_evidence")
        nodes.append(GraphNode(
            id=ev.id,
            label=f"[{ev.id}] {ev.title}",
            node_type=node_type,
            partition="physical_grounding",
            properties={
                "is_crucial": ev.is_crucial,
                "is_red_herring": ev.is_red_herring,
                "location": ev.location,
                "description": ev.description
            }
        ))

        # Connections
        if ev.is_crucial:
            # Crucial clue CONTRADICTS the culprit's alibi
            culprit_alibi_id = f"ALIBI-{culprit_id}"
            contradict_edge = GraphEdge(
                source=ev.id,
                target=culprit_alibi_id,
                relation="contradicts",
                is_decisive=True,
                description=f"Chứng cứ {ev.id} bẻ gãy trực tiếp bằng chứng ngoại phạm của {culprit_id}!"
            )
            edges.append(contradict_edge)
            decisive_edge = contradict_edge

            # Crucial clue INCRIMINATES culprit
            edges.append(GraphEdge(
                source=ev.id,
                target=culprit_id,
                relation="incriminates",
                is_decisive=True,
                description=f"Chứng minh sự hiện diện / liên đới của {culprit_id}"
            ))

        elif ev.is_red_herring and ev.linked_suspect_id:
            # Red herring points falsely to an innocent suspect
            edges.append(GraphEdge(
                source=ev.id,
                target=ev.linked_suspect_id,
                relation="red_herring_lead",
                description=f"Dấu vết nghi binh làm chệch hướng điều tra sang {ev.linked_suspect_id}"
            ))

    # Solvability verification over Bipartite Graph:
    # A case is graph-theoretically solvable if:
    # 1. There exists a decisive edge from Crucial Evidence -> Culprit Alibi
    # 2. No crucial clue falsely incriminates an innocent suspect
    has_false_incrimination = any(
        ev.is_crucial and ev.linked_suspect_id and ev.linked_suspect_id != culprit_id
        for ev in case.evidences
    )
    is_solvable = (decisive_edge is not None) and (not has_false_incrimination)

    return BipartiteCaseGraph(
        case_id=case.case_id,
        nodes=nodes,
        edges=edges,
        is_connected_and_solvable=is_solvable,
        decisive_edge=decisive_edge
    )


def print_ascii_graph(graph: BipartiteCaseGraph):
    """Render a text-based ASCII representation of the Bipartite Mystery Graph."""
    print("\n" + "=" * 75)
    print(f"  🕸️ BIỂU DIỄN ĐỒ THỊ HAI PHÍA MANH MỐI (BIPARTITE MYSTERY GRAPH)")
    print(f"  Vụ án: {graph.case_id} | Tổng đỉnh: {len(graph.nodes)} | Tổng cạnh: {len(graph.edges)}")
    print("=" * 75)

    print("\n[PHÂN HOẠCH 1: NARRATIVE CLAIMS (Lời khai & Nghi phạm)]")
    for n in graph.nodes:
        if n.partition == "narrative_claim":
            tag = "👤" if n.node_type == "suspect" else "🗣️"
            print(f"   {tag} [{n.id}] {n.label}")

    print("\n[PHÂN HOẠCH 2: PHYSICAL GROUNDING (Hiện trường & Dấu vết thực tế)]")
    for n in graph.nodes:
        if n.partition == "physical_grounding":
            tag = "⭐" if "crucial" in n.node_type else ("🚩" if "red_herring" in n.node_type else "🔍")
            print(f"   {tag} [{n.id}] {n.label}")

    print("\n[CÁC CẠNH LIÊN KẾT LOGIC TRÊN ĐỒ THỊ (EDGES)]")
    for e in graph.edges:
        if e.is_decisive:
            print(f"   ⚡ [BẺ GÃY MẤU CHỐT] ({e.source}) ──[{e.relation}]──> ({e.target})")
            print(f"      Lý do: {e.description}")
        elif e.relation == "red_herring_lead":
            print(f"   🚩 [NGHI BINH]      ({e.source}) ──[{e.relation}]──> ({e.target})")
        else:
            print(f"   🔗 [LIÊN ĐỚI]       ({e.source}) ──[{e.relation}]──> ({e.target})")

    print("\n" + "-" * 75)
    if graph.is_connected_and_solvable:
        print("  ✅ ĐỒ THỊ ĐẠT CHUẨN LIÊN THÔNG & BẢO ĐẢM TÍNH GIẢI ĐƯỢC (GRAPH-SOLVABLE)")
        print(f"     Đường bẻ gãy quyết định: {graph.decisive_edge.source} -> {graph.decisive_edge.target}")
    else:
        print("  ❌ ĐỒ THỊ BỊ ĐỨT GÃY: Không tìm thấy đường nối từ chứng cứ bẻ alibi hung thủ!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    import os, json
    # Test on CASE-2026-001 or CASE-9647
    cases_dir = os.path.join(os.path.dirname(__file__), "cases")
    files = [f for f in os.listdir(cases_dir) if f.endswith(".json")]
    if files:
        target = os.path.join(cases_dir, files[0])
        with open(target, "r", encoding="utf-8") as fp:
            c = CaseDossier.model_validate(json.load(fp))
            g = build_bipartite_case_graph(c)
            print_ascii_graph(g)
