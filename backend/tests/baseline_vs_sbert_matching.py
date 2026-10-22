"""
Baseline vs SBERT Semantic Matching — Comparison Script
=========================================================
For: Matching Agent module demo slide (Skill Barter Marketplace)

What this does
---------------
Runs the SAME set of skill-pair test cases through two matchers:
  1. BASELINE  — naive exact-string / keyword matching (what most
                 non-AI barter apps use)
  2. YOUR MODEL — sentence-transformers (all-MiniLM-L6-v2) cosine
                 similarity, i.e. the exact function used in
                 backend/app/services/embedding_service.py

It prints a side-by-side table and a summary accuracy score you can
paste directly into your "Demonstration & Result" slide.

How to run
-----------
    pip install sentence-transformers scikit-learn --break-system-packages
    python baseline_vs_sbert_matching.py

Takes ~15-30 seconds (model download only happens once, then cached).
"""

from sentence_transformers import SentenceTransformer
import numpy as np

# --------------------------------------------------------------------- #
# Test set: (skill_a, skill_b, should_they_match, description)
# Mirrors the real matching scenarios your barter platform must handle.
# --------------------------------------------------------------------- #
TEST_CASES = [
    # Paraphrase / informal-vs-formal (SHOULD match)
    ("Python", "Python Programming", True, "Informal vs formal name"),
    ("ML", "Machine Learning", True, "Common abbreviation"),
    ("Web Dev", "Web Development", True, "Informal vs formal name"),
    ("JS", "JavaScript", True, "Common abbreviation"),
    ("Guitar", "Guitar Playing", True, "Trivial paraphrase"),

    # Synonymous skill phrasing (SHOULD match)
    ("Frontend Programming", "Web Development", True, "Related synonym phrasing"),
    ("Neural Networks", "Deep Learning", True, "Closely related ML subfields"),
    ("AI", "Machine Learning", True, "Broad-to-specific relation"),

    # Clearly unrelated (should NOT match)
    ("Graphic Design", "Python", False, "Unrelated domains"),
    ("Guitar", "Cooking", False, "Unrelated domains"),
    ("Cybersecurity", "Photography", False, "Unrelated domains"),
    ("Data Science", "Guitar", False, "Unrelated domains"),
]

SIMILARITY_THRESHOLD = 0.55   # same ballpark as matching_service.py min_similarity default (0.5)


def keyword_baseline_match(a: str, b: str) -> bool:
    """
    Naive baseline: what a non-AI barter platform typically does —
    case-insensitive exact match or substring containment.
    """
    a_norm, b_norm = a.strip().lower(), b.strip().lower()
    return a_norm == b_norm or a_norm in b_norm or b_norm in a_norm


def main():
    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded.\n")

    rows = []
    baseline_correct = 0
    sbert_correct = 0

    for skill_a, skill_b, expected, desc in TEST_CASES:
        # --- Baseline ---
        baseline_pred = keyword_baseline_match(skill_a, skill_b)

        # --- SBERT (same logic as embedding_service.calculate_similarity) ---
        emb_a = model.encode(skill_a.lower().strip())
        emb_b = model.encode(skill_b.lower().strip())
        sim = float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b)))
        sbert_pred = sim >= SIMILARITY_THRESHOLD

        baseline_ok = (baseline_pred == expected)
        sbert_ok = (sbert_pred == expected)
        baseline_correct += baseline_ok
        sbert_correct += sbert_ok

        rows.append({
            "pair": f"{skill_a} vs {skill_b}",
            "desc": desc,
            "expected": expected,
            "baseline_pred": baseline_pred,
            "baseline_ok": baseline_ok,
            "sbert_sim": round(sim, 3),
            "sbert_pred": sbert_pred,
            "sbert_ok": sbert_ok,
        })

    # ---- Print table ----
    print(f"{'Skill Pair':38} {'Expected':9} {'Baseline':10} {'SBERT sim':10} {'SBERT':8}")
    print("-" * 85)
    for r in rows:
        print(f"{r['pair']:38} {str(r['expected']):9} "
              f"{('MATCH' if r['baseline_pred'] else 'no match'):10} "
              f"{r['sbert_sim']:<10} "
              f"{('MATCH' if r['sbert_pred'] else 'no match'):8}"
              f"  {'✓' if r['sbert_ok'] else '✗ (baseline ✓' if r['baseline_ok'] else '✗'}")

    n = len(TEST_CASES)
    print("\n" + "=" * 85)
    print(f"BASELINE (keyword/exact match) accuracy : {baseline_correct}/{n} = {baseline_correct/n*100:.1f}%")
    print(f"SBERT (semantic embedding)   accuracy   : {sbert_correct}/{n} = {sbert_correct/n*100:.1f}%")
    print("=" * 85)
    print(f"\nImprovement over baseline: +{(sbert_correct - baseline_correct)/n*100:.1f} percentage points")


if __name__ == "__main__":
    main()
