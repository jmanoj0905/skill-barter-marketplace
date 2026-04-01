"""
Learning Path Engine — Skill Barter Marketplace
================================================
Builds a directed taxonomy graph from skill_taxonomy.json and provides
correct prerequisite / complementary / next-level recommendations.

Graph structure:
    Root domain  →  Level-1 category  →  Level-2 leaf skill
    Edges point FROM parent TO child  (parent teaches child).

Algorithm:
    Prerequisites   = ancestors of the skill   (how many levels up = expertise depth)
    Complementary   = siblings + cousins        (same parent or same grandparent)
    Next-level      = children + grandchildren  (depth depends on user level)
"""

import json
import networkx as nx
from pathlib import Path
from typing import Optional

# ── Expertise → depth mappings ────────────────────────────────────────────────
PREREQUISITE_DEPTH = {
    "beginner":      3,   # show up to 3 ancestor levels
    "intermediate":  2,
    "advanced":      1,
    "expert":        0,   # expert needs no prerequisites listed
}

NEXT_LEVEL_DEPTH = {
    "beginner":      2,   # children AND grandchildren
    "intermediate":  2,
    "advanced":      1,   # direct children only
    "expert":        1,
}

MAX_RESULTS = 5   # cap per category


class LearningPathEngine:

    def __init__(self, taxonomy_path: str = "skill_taxonomy.json"):
        with open(taxonomy_path) as f:
            self.taxonomy = json.load(f)

        self.G: nx.DiGraph = nx.DiGraph()
        self._node_meta: dict[str, dict] = {}   # skill_name → {level, category, description}
        self._build_graph()

    # ── Graph construction ────────────────────────────────────────────────────

    def _build_graph(self):
        """Recursively walk the taxonomy and add nodes + directed edges."""
        for domain_name, domain_data in self.taxonomy.items():
            self._add_node(domain_name, level=0, category=domain_name,
                           description=domain_data.get("description", ""))
            self._recurse(domain_name, domain_data.get("children", {}),
                          category=domain_name, level=1)

    def _add_node(self, name: str, level: int, category: str, description: str):
        self.G.add_node(name)
        self._node_meta[name.lower()] = {
            "canonical_name": name,
            "level": level,
            "category": category,
            "description": description,
        }

    def _recurse(self, parent: str, children: dict, category: str, level: int):
        for child_name, child_data in children.items():
            self._add_node(child_name, level=level,
                           category=category,
                           description=child_data.get("description", ""))
            self.G.add_edge(parent, child_name)          # parent → child
            self._recurse(child_name,
                          child_data.get("children", {}),
                          category=category,
                          level=level + 1)

    # ── Lookup helpers ────────────────────────────────────────────────────────

    def _find_node(self, skill: str) -> Optional[str]:
        """Case-insensitive node lookup. Returns canonical name or None."""
        key = skill.strip().lower()
        if key in self._node_meta:
            return self._node_meta[key]["canonical_name"]
        # Partial / substring match
        for stored_key, meta in self._node_meta.items():
            if key in stored_key or stored_key in key:
                return meta["canonical_name"]
        return None

    def _meta(self, node: str) -> dict:
        return self._node_meta.get(node.lower(), {})

    def _ancestors_up_to(self, node: str, max_depth: int) -> list[str]:
        """Return ancestors within max_depth hops, nearest first."""
        results = []
        visited = {node}
        frontier = [node]
        for _ in range(max_depth):
            next_frontier = []
            for n in frontier:
                for pred in self.G.predecessors(n):
                    if pred not in visited:
                        visited.add(pred)
                        results.append(pred)
                        next_frontier.append(pred)
            frontier = next_frontier
            if not frontier:
                break
        return results

    def _children_up_to(self, node: str, max_depth: int) -> list[str]:
        """Return descendants within max_depth hops, nearest first."""
        results = []
        visited = {node}
        frontier = [node]
        for _ in range(max_depth):
            next_frontier = []
            for n in frontier:
                for succ in self.G.successors(n):
                    if succ not in visited:
                        visited.add(succ)
                        results.append(succ)
                        next_frontier.append(succ)
            frontier = next_frontier
            if not frontier:
                break
        return results

    def _siblings(self, node: str) -> list[str]:
        """Return nodes that share the same parent (excluding node itself)."""
        siblings = []
        for parent in self.G.predecessors(node):
            for sibling in self.G.successors(parent):
                if sibling != node:
                    siblings.append(sibling)
        return siblings

    def _cousins(self, node: str) -> list[str]:
        """Return nodes that share the same grandparent (excluding siblings)."""
        cousins = []
        known = {node} | set(self._siblings(node))
        for parent in self.G.predecessors(node):
            for grandparent in self.G.predecessors(parent):
                for uncle in self.G.successors(grandparent):
                    if uncle != parent:
                        for cousin in self.G.successors(uncle):
                            if cousin not in known:
                                known.add(cousin)
                                cousins.append(cousin)
        return cousins

    # ── Formatting helper ─────────────────────────────────────────────────────

    def _format(self, node: str, reason: str) -> dict:
        m = self._meta(node)
        return {
            "skill_name":        node,
            "skill_category":    m.get("category"),
            "taxonomy_level":    m.get("level"),
            "description":       m.get("description", ""),
            "similarity": 1.0,
            "reason":            reason,
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def get_learning_path(self, skill: str, user_level: str = "intermediate") -> dict:
        """
        Returns a structured learning path for a given skill and user expertise.

        Parameters
        ----------
        skill      : the skill the user wants to learn (e.g. "Machine Learning")
        user_level : beginner | intermediate | advanced | expert

        Returns
        -------
        dict with keys: skill, user_level, found_as, prerequisites,
                        complementary, next_level, error (if not found)
        """
        user_level = user_level.lower().strip()
        if user_level not in PREREQUISITE_DEPTH:
            user_level = "intermediate"

        canonical = self._find_node(skill)
        if canonical is None:
            return {
                "skill":      skill,
                "user_level": user_level,
                "error":      f"Skill '{skill}' not found in taxonomy. "
                              f"Available domains: {list(self.taxonomy.keys())}",
            }

        pre_depth  = PREREQUISITE_DEPTH[user_level]
        next_depth = NEXT_LEVEL_DEPTH[user_level]

        # ── Prerequisites (ancestors) ──────────────────────────────────────
        if pre_depth == 0:
            prerequisites = []
        else:
            ancestor_nodes = self._ancestors_up_to(canonical, pre_depth)
            prerequisites = [
                self._format(n, f"Foundation you need before learning {canonical}")
                for n in ancestor_nodes[:MAX_RESULTS]
            ]

        # ── Complementary (siblings + cousins) ────────────────────────────
        sibling_nodes = self._siblings(canonical)
        cousin_nodes  = [c for c in self._cousins(canonical)
                         if c not in sibling_nodes]
        comp_nodes = sibling_nodes[:3] + cousin_nodes[:2]   # balance both
        complementary = [
            self._format(n,
                f"Sibling skill — pairs well with {canonical}"
                if n in sibling_nodes
                else f"Related skill from a neighbouring domain")
            for n in comp_nodes[:MAX_RESULTS]
        ]

        # ── Next level (children / grandchildren) ─────────────────────────
        child_nodes = self._children_up_to(canonical, next_depth)
        next_level = [
            self._format(n, f"Natural next step after mastering {canonical}")
            for n in child_nodes[:MAX_RESULTS]
        ]

        return {
            "skill":         canonical,
            "user_level":    user_level,
            "found_as":      self._meta(canonical),
            "prerequisites": prerequisites,
            "complementary": complementary,
            "next_level":    next_level,
        }

    def list_all_skills(self) -> list[str]:
        return list(self.G.nodes())

    def get_skill_info(self, skill: str) -> dict:
        canonical = self._find_node(skill)
        if not canonical:
            return {"error": f"'{skill}' not found"}
        return {
            "skill":     canonical,
            "metadata":  self._meta(canonical),
            "parents":   list(self.G.predecessors(canonical)),
            "children":  list(self.G.successors(canonical)),
            "siblings":  self._siblings(canonical),
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json as _json

    engine = LearningPathEngine(r"C:\Users\hp\OneDrive\Desktop\skill-barter-marketplace\backend\app\scripts\skill_taxonomy.json")

    test_cases = [
        ("Machine Learning",  "intermediate"),
        ("Machine Learning",  "beginner"),
        ("React",             "beginner"),
        ("Deep Learning",     "advanced"),
        ("Docker",            "intermediate"),
        ("Data Science",      "intermediate"),   # root-level domain
    ]

    for skill, level in test_cases:
        result = engine.get_learning_path(skill, level)
        print(f"\n{'='*60}")
        print(f"SKILL: {result['skill']}  |  LEVEL: {result['user_level']}")
        if "error" in result:
            print("ERROR:", result["error"])
            continue
        print(f"Found as: {result['found_as']}")
        print(f"\nPrerequisites ({len(result['prerequisites'])}):")
        for p in result['prerequisites']:
            print(f"  ← {p['skill_name']} [{p['skill_category']}] — {p['reason']}")
        print(f"\nComplementary ({len(result['complementary'])}):")
        for c in result['complementary']:
            print(f"  ↔ {c['skill_name']} [{c['skill_category']}] — {c['reason']}")
        print(f"\nNext Level ({len(result['next_level'])}):")
        for n in result['next_level']:
            print(f"  → {n['skill_name']} [{n['skill_category']}] — {n['reason']}")

# ── Singleton service instance ───────────────────────────────

_engine_instance = None

def get_learning_path_service():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = LearningPathEngine(
            r"C:\Users\hp\OneDrive\Desktop\skill-barter-marketplace\backend\app\scripts\skill_taxonomy.json"
        )
    return _engine_instance