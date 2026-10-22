"""
Learning Path Module — Comparison Script
=========================================
Compares two approaches to generating skill-learning recommendations:

  1. FLAT SEMANTIC SIMILARITY  — same approach as the Matching module:
     embed the target skill, rank all other skills by cosine similarity,
     return the top-K. No notion of "direction" (prerequisite vs next-step)
     or relationship type.

  2. TAXONOMY GRAPH (your Learning Path Engine) — uses the directed
     skill_taxonomy.json graph to correctly separate:
       - prerequisites   (ancestors)
       - complementary   (siblings / cousins)
       - next-level      (children)

Produces ONE combined figure with two panels:
  Left  : your taxonomy graph, categorized and color-coded around
          the target skill
  Right : flat similarity top-K, single color, un-categorized —
          visually demonstrating the "everything looks the same" problem

Usage:
    pip install sentence-transformers networkx matplotlib --break-system-packages
    python learning_path_comparison.py
"""

import json
import os
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import textwrap
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

# Resolve taxonomy path relative to THIS script's own folder,
# so it works no matter which directory you run the script from.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_PATH = os.path.join(_SCRIPT_DIR, "skill_taxonomy.json")

if not os.path.exists(TAXONOMY_PATH):
    raise FileNotFoundError(
        f"Could not find skill_taxonomy.json next to this script.\n"
        f"Looked at: {TAXONOMY_PATH}\n"
        f"Fix: make sure skill_taxonomy.json is in the same folder as this script, "
        f"or edit TAXONOMY_PATH above to point directly at it."
    )

print(f"Using taxonomy file: {TAXONOMY_PATH}")
TARGET_SKILL = "Python Programming"
USER_LEVEL = "intermediate"
TOP_K_FLAT = 8

PREREQUISITE_DEPTH = {"beginner": 3, "intermediate": 2, "advanced": 1, "expert": 0}
NEXT_LEVEL_DEPTH = {"beginner": 2, "intermediate": 2, "advanced": 1, "expert": 1}
MAX_RESULTS = 5


# --------------------------------------------------------------------- #
# 1. Build the taxonomy graph (same logic as learning_path_engine.py)
# --------------------------------------------------------------------- #
class LearningPathEngine:
    def __init__(self, taxonomy_path):
        with open(taxonomy_path) as f:
            self.taxonomy = json.load(f)
        self.G = nx.DiGraph()
        self._node_meta = {}
        self._build_graph()

    def _add_node(self, name, level, category):
        self.G.add_node(name)
        self._node_meta[name.lower()] = {"canonical_name": name, "level": level, "category": category}

    def _recurse(self, parent, children, category, level):
        for child_name, child_data in children.items():
            self._add_node(child_name, level, category)
            self.G.add_edge(parent, child_name)
            self._recurse(child_name, child_data.get("children", {}), category, level + 1)

    def _build_graph(self):
        for domain_name, domain_data in self.taxonomy.items():
            self._add_node(domain_name, 0, domain_name)
            self._recurse(domain_name, domain_data.get("children", {}), domain_name, 1)

    def _find_node(self, skill):
        key = skill.strip().lower()
        if key in self._node_meta:
            return self._node_meta[key]["canonical_name"]
        for k, meta in self._node_meta.items():
            if key in k or k in key:
                return meta["canonical_name"]
        return None

    def _ancestors_up_to(self, node, max_depth):
        results, visited, frontier = [], {node}, [node]
        for _ in range(max_depth):
            nxt = []
            for n in frontier:
                for pred in self.G.predecessors(n):
                    if pred not in visited:
                        visited.add(pred); results.append(pred); nxt.append(pred)
            frontier = nxt
            if not frontier: break
        return results

    def _children_up_to(self, node, max_depth):
        results, visited, frontier = [], {node}, [node]
        for _ in range(max_depth):
            nxt = []
            for n in frontier:
                for succ in self.G.successors(n):
                    if succ not in visited:
                        visited.add(succ); results.append(succ); nxt.append(succ)
            frontier = nxt
            if not frontier: break
        return results

    def _siblings(self, node):
        out = []
        for parent in self.G.predecessors(node):
            for sib in self.G.successors(parent):
                if sib != node:
                    out.append(sib)
        return out

    def get_categorized(self, skill, user_level="intermediate"):
        canonical = self._find_node(skill)
        pre_depth = PREREQUISITE_DEPTH[user_level]
        next_depth = NEXT_LEVEL_DEPTH[user_level]
        prerequisites = self._ancestors_up_to(canonical, pre_depth)[:MAX_RESULTS] if pre_depth else []
        complementary = self._siblings(canonical)[:MAX_RESULTS]
        next_level = self._children_up_to(canonical, next_depth)[:MAX_RESULTS]
        return canonical, prerequisites, complementary, next_level


# --------------------------------------------------------------------- #
# 2. Run taxonomy graph approach
# --------------------------------------------------------------------- #
engine = LearningPathEngine(TAXONOMY_PATH)
canonical, prerequisites, complementary, next_level = engine.get_categorized(TARGET_SKILL, USER_LEVEL)

print(f"Target skill: {canonical}")
print(f"Prerequisites: {prerequisites}")
print(f"Complementary: {complementary}")
print(f"Next level: {next_level}")

# --------------------------------------------------------------------- #
# 3. Run flat semantic similarity approach (same method as Matching module)
# --------------------------------------------------------------------- #
all_skills = list(engine.G.nodes())
all_skills = [s for s in all_skills if s != canonical]

USING_SBERT = False
if SBERT_AVAILABLE:
    try:
        print("\nLoading sentence-transformers model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        target_emb = model.encode(canonical.lower())
        all_embs = model.encode([s.lower() for s in all_skills])
        sims = np.dot(all_embs, target_emb) / (
            np.linalg.norm(all_embs, axis=1) * np.linalg.norm(target_emb)
        )
        USING_SBERT = True
    except Exception as e:
        print(f"\n[!] Could not load SBERT model ({e}).")
        print("[!] Falling back to a character n-gram similarity proxy for THIS PREVIEW ONLY.")
        print("[!] On your machine (with internet / cached model), this block will run with real SBERT automatically.\n")

if not USING_SBERT:
    # Offline fallback: character-trigram Jaccard-style similarity.
    # NOT what your real model uses — purely so this script produces a
    # preview chart in network-restricted environments. On your machine,
    # SBERT loads fine (as your baseline_vs_sbert_matching.py already proved)
    # and this block is skipped automatically.
    def trigrams(s):
        s = s.lower()
        return set(s[i:i+3] for i in range(len(s) - 2)) or {s}

    target_grams = trigrams(canonical)
    sims = []
    for s in all_skills:
        g = trigrams(s)
        inter = len(target_grams & g)
        union = len(target_grams | g)
        sims.append(inter / union if union else 0.0)
    sims = np.array(sims)
ranked = sorted(zip(all_skills, sims), key=lambda x: x[1], reverse=True)[:TOP_K_FLAT]

print("\nFlat similarity top-K (no relationship type):")
for skill, sim in ranked:
    true_relation = (
        "prerequisite" if skill in prerequisites else
        "complementary" if skill in complementary else
        "next-level" if skill in next_level else
        "NOT in taxonomy neighborhood"
    )
    print(f"  {skill:30s} sim={sim:.3f}   [actual relation: {true_relation}]")

# --------------------------------------------------------------------- #
# 4. Visualization — two-panel figure
# --------------------------------------------------------------------- #
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

# ---- Left panel: taxonomy graph, categorized ----
sub_nodes = [canonical] + prerequisites + complementary + next_level
subG = nx.DiGraph()
for n in sub_nodes:
    subG.add_node(n)
for p in prerequisites:
    subG.add_edge(p, canonical)
for c in complementary:
    subG.add_edge(canonical, c)  # drawn as related, not directional in reality
for n in next_level:
    subG.add_edge(canonical, n)

pos = {}
pos[canonical] = (0, 0)
for i, p in enumerate(prerequisites):
    pos[p] = (-1.6, (i - (len(prerequisites)-1)/2) * 1.0)
for i, c in enumerate(complementary):
    pos[c] = (0, 1.4 + i * 0.9)
for i, nl in enumerate(next_level):
    pos[nl] = (1.6, (i - (len(next_level)-1)/2) * 1.0)

node_colors = []
for n in subG.nodes():
    if n == canonical:
        node_colors.append("#2563eb")
    elif n in prerequisites:
        node_colors.append("#f59e0b")
    elif n in complementary:
        node_colors.append("#8b5cf6")
    else:
        node_colors.append("#22c55e")

nx.draw_networkx_edges(subG, pos, ax=ax1, edge_color="#94a3b8", arrows=True,
                        arrowsize=15, connectionstyle="arc3,rad=0.05", width=1.3)

nx.draw_networkx_nodes(
    subG,
    pos,
    ax=ax1,
    node_color=node_colors,
    node_size=2200,          # slightly larger circles
    edgecolors="white",
    linewidths=1.5,
)

# Wrapped labels so they fit inside the circles
for node, (x, y) in pos.items():
    ax1.text(
        x,
        y,
        textwrap.fill(node, width=11),  # wraps long names into multiple lines
        ha="center",
        va="center",
        fontsize=7,
        fontweight="bold",
        color="white",
        linespacing=0.9,
    )

ax1.set_title(f"Taxonomy Graph (Yours)\nCategorized recommendations for '{canonical}'",
              fontsize=12, fontweight="bold")
ax1.axis("off")
legend_elems = [
    Patch(facecolor="#2563eb", label="Target skill"),
    Patch(facecolor="#f59e0b", label="Prerequisite"),
    Patch(facecolor="#8b5cf6", label="Complementary"),
    Patch(facecolor="#22c55e", label="Next level"),
]
ax1.legend(handles=legend_elems, loc="lower center", bbox_to_anchor=(0.5, -0.12),
           ncol=2, frameon=False, fontsize=9)

# ---- Right panel: flat similarity ranking ----
skills_r = [s for s, _ in ranked][::-1]
sims_r = [s for _, s in ranked][::-1]

def relation_of(skill):
    if skill in prerequisites: return "#f59e0b"
    if skill in complementary: return "#8b5cf6"
    if skill in next_level: return "#22c55e"
    return "#94a3b8"  # grey = not even in taxonomy neighborhood, similarity alone surfaced it

colors_r = [relation_of(s) for s in skills_r]

bars = ax2.barh(range(len(skills_r)), sims_r, color=colors_r, height=0.6)
ax2.set_yticks(range(len(skills_r)))
ax2.set_yticklabels(skills_r, fontsize=9)
ax2.set_xlabel("Cosine similarity to target skill", fontsize=10)
ax2.set_title(f"Flat Semantic Similarity (Baseline)\nTop-{TOP_K_FLAT} by similarity alone — same color regardless of relation",
              fontsize=12, fontweight="bold")
ax2.spines[["top", "right"]].set_visible(False)
ax2.xaxis.grid(True, linestyle="--", alpha=0.4)
ax2.set_axisbelow(True)

for i, (bar, sim) in enumerate(zip(bars, sims_r)):
    ax2.text(sim + 0.01, i, f"{sim:.3f}", va="center", fontsize=8)

legend_elems2 = [
    Patch(facecolor="#f59e0b", label="Actually a prerequisite"),
    Patch(facecolor="#8b5cf6", label="Actually complementary"),
    Patch(facecolor="#22c55e", label="Actually next-level"),
    Patch(facecolor="#94a3b8", label="Not in taxonomy neighborhood"),
]
ax2.legend(handles=legend_elems2, loc="lower right", frameon=False, fontsize=8)

fig.suptitle("Learning Path Recommendations: Taxonomy Graph vs Flat Semantic Similarity",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
output_path = os.path.join(_SCRIPT_DIR, "learning_path_comparison.png")
plt.savefig(output_path, dpi=200, bbox_inches="tight")
print(f"Saved: {output_path}")
print("\nSaved: learning_path_comparison.png")
