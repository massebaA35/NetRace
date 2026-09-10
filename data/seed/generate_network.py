"""
generate_network.py

Reads data/processed/entities.json (produced by generate_entities.py) and
builds a relationship graph between entities using NetworkX. It also plants
a "suspicious cluster" — a tightly connected group with unusual relationship
patterns — which the demo can highlight in the Network Explorer / Connection
Finder pages.

Usage:
    python generate_network.py --case-id case_001

Output:
    data/processed/network.json
    Shape:
    {
        "case_id": "case_001",
        "nodes": [{"id": "...", "type": "...", "label": "..."}],
        "edges": [
            {
                "source": "person_0001",
                "target": "person_0007",
                "relationship": "calls",
                "attributes": {...}
            },
            ...
        ],
        "planted_cluster": {
            "member_ids": [...],
            "description": "..."
        }
    }
"""

import argparse
import json
import random
from pathlib import Path

import networkx as nx
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "processed"
ENTITIES_FILE = PROCESSED_DIR / "entities.json"
OUTPUT_FILE = PROCESSED_DIR / "network.json"

RELATIONSHIP_TYPES = {
    ("person", "person"): ["knows", "family_of", "co_worker_of", "calls_frequently"],
    ("person", "phone"): ["owns"],
    ("person", "vehicle"): ["owns"],
    ("person", "organization"): ["works_at", "director_of", "shareholder_of"],
    ("phone", "phone"): ["calls", "sms"],
    ("organization", "organization"): ["subsidiary_of", "transacts_with"],
}


def edge_type(t1: str, t2: str) -> tuple[str, str]:
    """Normalize an unordered type pair to match RELATIONSHIP_TYPES keys."""
    key = (t1, t2)
    if key in RELATIONSHIP_TYPES:
        return key
    key_rev = (t2, t1)
    if key_rev in RELATIONSHIP_TYPES:
        return key_rev
    return None


def load_entities():
    if not ENTITIES_FILE.exists():
        raise FileNotFoundError(
            f"{ENTITIES_FILE} not found. Run generate_entities.py first."
        )
    with open(ENTITIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_baseline_graph(entities: list[dict], avg_degree: int = 3) -> nx.Graph:
    """Build a random-ish baseline social/ownership graph across all entities."""
    G = nx.Graph()
    for e in entities:
        G.add_node(e["id"], type=e["type"], label=e["label"])

    people = [e for e in entities if e["type"] == "person"]
    phones = [e for e in entities if e["type"] == "phone"]
    vehicles = [e for e in entities if e["type"] == "vehicle"]
    orgs = [e for e in entities if e["type"] == "organization"]

    # Ownership edges: person -> phone, person -> vehicle
    for phone in phones:
        owner_id = phone["attributes"]["owner_id"]
        G.add_edge(owner_id, phone["id"], relationship="owns")

    for vehicle in vehicles:
        owner_id = vehicle["attributes"]["owner_id"]
        G.add_edge(owner_id, vehicle["id"], relationship="owns")

    # Person <-> organization edges (some people work at / direct orgs)
    for person in people:
        if random.random() < 0.35 and orgs:
            org = random.choice(orgs)
            rel = random.choice(RELATIONSHIP_TYPES[("person", "organization")])
            G.add_edge(person["id"], org["id"], relationship=rel)

    # Person <-> person social graph using a scale-free-ish attachment model
    person_ids = [p["id"] for p in people]
    if len(person_ids) > 1:
        m = max(1, min(avg_degree, len(person_ids) - 1))
        ba_graph = nx.barabasi_albert_graph(len(person_ids), m, seed=42)
        for u, v in ba_graph.edges():
            rel = random.choice(RELATIONSHIP_TYPES[("person", "person")])
            G.add_edge(person_ids[u], person_ids[v], relationship=rel)

    # Phone <-> phone call edges (simple proxy for call activity between owners' phones)
    if len(phones) > 1:
        num_call_edges = len(phones) * 2
        for _ in range(num_call_edges):
            p1, p2 = random.sample(phones, 2)
            G.add_edge(p1["id"], p2["id"], relationship="calls")

    return G


def plant_suspicious_cluster(G: nx.Graph, entities: list[dict], cluster_size: int = 6) -> dict:
    """
    Pick a small set of person nodes and densely interconnect them with
    financial/communication-flavored relationships, then mark them as
    flagged. This gives the demo a clear "aha" cluster to surface via
    Connection Finder / Network Explorer.
    """
    people = [e for e in entities if e["type"] == "person"]
    if len(people) < cluster_size:
        cluster_size = len(people)

    cluster_members = random.sample(people, cluster_size)
    member_ids = [m["id"] for m in cluster_members]

    # Densely connect the cluster (near-complete graph)
    for i, a in enumerate(member_ids):
        for b in member_ids[i + 1 :]:
            if not G.has_edge(a, b):
                rel = random.choice(["transacts_with", "calls_frequently", "co_conspirator_of"])
                G.add_edge(a, b, relationship=rel, suspicious=True)
            else:
                G[a][b]["suspicious"] = True

    # Connect the cluster to a shared shell organization, if one exists
    orgs = [e for e in entities if e["type"] == "organization"]
    if orgs:
        shell_org = random.choice(orgs)
        for member_id in member_ids:
            G.add_edge(member_id, shell_org["id"], relationship="shareholder_of", suspicious=True)

    # Mark nodes as flagged
    for member_id in member_ids:
        G.nodes[member_id]["flagged"] = True

    return {
        "member_ids": member_ids,
        "description": (
            "Densely interconnected group of individuals with frequent "
            "transactions/calls and shared shareholding in a common organization — "
            "flagged for investigator review."
        ),
    }


def graph_to_json(G: nx.Graph, entities_by_id: dict, case_id: str, planted_cluster: dict) -> dict:
    nodes = []
    for node_id, data in G.nodes(data=True):
        entity = entities_by_id.get(node_id, {})
        nodes.append(
            {
                "id": node_id,
                "type": data.get("type", entity.get("type")),
                "label": data.get("label", entity.get("label")),
                "flagged": data.get("flagged", False),
            }
        )

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append(
            {
                "source": u,
                "target": v,
                "relationship": data.get("relationship", "related_to"),
                "suspicious": data.get("suspicious", False),
            }
        )

    return {
        "case_id": case_id,
        "nodes": nodes,
        "edges": edges,
        "planted_cluster": planted_cluster,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
    }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic relationship network for NetTrace")
    parser.add_argument("--case-id", type=str, default="case_001", help="Case identifier")
    parser.add_argument("--avg-degree", type=int, default=3, help="Average person-to-person connections")
    parser.add_argument("--cluster-size", type=int, default=6, help="Size of the planted suspicious cluster")
    args = parser.parse_args()

    data = load_entities()
    entities = data["entities"]
    entities_by_id = {e["id"]: e for e in entities}

    G = build_baseline_graph(entities, avg_degree=args.avg_degree)
    planted_cluster = plant_suspicious_cluster(G, entities, cluster_size=args.cluster_size)

    result = graph_to_json(G, entities_by_id, args.case_id, planted_cluster)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Built network for case '{args.case_id}'")
    print(f"  nodes={result['counts']['nodes']} edges={result['counts']['edges']}")
    print(f"  planted cluster size={len(planted_cluster['member_ids'])}")
    print(f"Wrote: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
