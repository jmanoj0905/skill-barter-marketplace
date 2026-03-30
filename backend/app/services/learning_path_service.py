"""
Learning Path Recommendations (FEAT-2.4.2)  –  v4  (level-hierarchy)

Root cause of all previous failures:
  1. popularity_score = 0 for all CSV-imported skills (not linked to users),
     so every popularity-based condition evaluates to 0 < 0 → False.
     next_level was ALWAYS empty as a result.
  2. Cosine similarity is symmetric — sim(NLP, ML) == sim(ML, NLP) — so it
     cannot determine learning direction by itself.
  3. co-taught signal is empty with only ~7 seed users.

Solution:
  Encode a SKILL_LEVELS dictionary that assigns each known skill a conceptual
  depth level 1–5.  Given the query skill's level Q:
    prerequisites   → level <  Q        (more foundational)
    complementary   → level == Q ± 1    (same-tier peers)
    next_level      → level >  Q        (more specialised / advanced)

  For any skill NOT in the dictionary, fall back to semantic similarity bands
  relative to the query (asymmetric similarity is still useful for unknown skills
  when combined with the known-level context).

  This mirrors how real learning platforms (Coursera, Khan Academy) work:
  they encode domain knowledge rather than derive it from user activity.
"""

from typing import List, Dict, Optional, Set, Tuple
from backend.app.services.embedding_service import get_embedding_service
from backend.app.core.database import get_connection, return_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Domain knowledge: skill → conceptual depth level 1–5               #
# 1 = most foundational / widely-known                               #
# 5 = most specialised / advanced                                     #
# ------------------------------------------------------------------ #

SKILL_LEVELS: Dict[str, int] = {
    # ── Level 1: Pure foundations ──────────────────────────────────
    "mathematics": 1,
    "statistics": 1,
    "linear algebra": 1,
    "calculus": 1,
    "probability": 1,
    "discrete mathematics": 1,
    "logic": 1,
    "python": 1,
    "java": 1,
    "javascript": 1,
    "c++": 1,
    "c programming": 1,
    "ruby": 1,
    "sql": 1,
    "html": 1,
    "css": 1,
    "excel": 1,
    "git": 1,

    # ── Level 2: Core applied skills ───────────────────────────────
    "data analysis": 2,
    "statistical analysis": 2,
    "data visualization": 2,
    "database design": 2,
    "algorithms": 2,
    "data structures": 2,
    "object oriented programming": 2,
    "functional programming": 2,
    "rest api": 2,
    "linux": 2,
    "networking": 2,
    "photography": 2,
    "graphic design": 2,
    "music theory": 2,
    "translation": 2,

    # ── Level 3: Intermediate specialisations ──────────────────────
    "machine learning": 3,
    "data science": 3,
    "web development": 3,
    "react": 3,
    "angular": 3,
    "vue": 3,
    "django": 3,
    "flask": 3,
    "node.js": 3,
    "nodejs": 3,
    "software engineering": 3,
    "cloud computing": 3,
    "devops": 3,
    "docker": 3,
    "kubernetes": 3,
    "big data": 3,
    "data mining": 3,
    "data warehousing": 3,
    "feature engineering": 3,
    "business intelligence": 3,
    "cybersecurity": 3,
    "blockchain": 3,
    "mobile development": 3,
    "ios development": 3,
    "android development": 3,
    "ui/ux design": 3,
    "product management": 3,

    # ── Level 4: Advanced specialisations ──────────────────────────
    "deep learning": 4,
    "neural networks": 4,
    "computer vision": 4,
    "natural language processing": 4,
    "nlp": 4,
    "reinforcement learning": 4,
    "data engineering": 4,
    "graph databases": 4,
    "distributed systems": 4,
    "system design": 4,
    "microservices": 4,
    "elasticsearch": 4,
    "kafka": 4,
    "spark": 4,
    "tensorflow": 4,
    "pytorch": 4,
    "opencv": 4,
    "penetration testing": 4,
    "ethical hacking": 4,

    # ── Level 5: Highly specialised / cutting-edge ─────────────────
    "generative ai": 5,
    "large language models": 5,
    "mlops": 5,
    "text classification": 5,
    "face recognition": 5,
    "object detection": 5,
    "speech recognition": 5,
    "transformer models": 5,
    "diffusion models": 5,
    "federated learning": 5,
    "quantum computing": 5,
}


def _level_of(skill_name: str) -> Optional[int]:
    """Return the level for a skill, trying progressively looser matches."""
    key = skill_name.lower().strip()
    if key in SKILL_LEVELS:
        return SKILL_LEVELS[key]
    # Try partial match (handles "Python Programming" → matches "python")
    for known, lvl in SKILL_LEVELS.items():
        if known in key or key in known:
            return lvl
    return None


class LearningPathService:

    def __init__(self):
        self.embedding_service = get_embedding_service()

    # ------------------------------------------------------------------ #
    # Public entry point                                                   #
    # ------------------------------------------------------------------ #

    def get_learning_path(
        self,
        skill_name: str,
        user_level: Optional[str] = None
    ) -> Dict:
        normalized  = skill_name.lower().strip()
        emb         = self.embedding_service.generate_embedding(normalized)
        emb_str     = '[' + ','.join(map(str, emb)) + ']'
        query_level = _level_of(skill_name)

        candidates  = self._fetch_related(normalized, emb_str)

        pre, comp, nxt = self._classify(
            skill_name, query_level, user_level, candidates
        )

        return {
            "skill":         skill_name,
            "user_level":    user_level,
            "prerequisites": pre,
            "complementary": comp,
            "next_level":    nxt,
        }

    # ------------------------------------------------------------------ #
    # DB: related skills                                                   #
    # ------------------------------------------------------------------ #

    def _fetch_related(
        self, skill_normalized: str, emb_str: str, limit: int = 30
    ) -> List[Dict]:
        conn   = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    sg.skill_name,
                    sg.skill_category,
                    COALESCE(sg.popularity_score, 0) AS popularity_score,
                    1 - (sg.skill_embedding <=> %s::vector) AS similarity
                FROM skill_graph sg
                WHERE sg.skill_embedding IS NOT NULL
                  AND LOWER(sg.skill_normalized) != %s
                  AND 1 - (sg.skill_embedding <=> %s::vector) >= 0.25
                ORDER BY similarity DESC
                LIMIT %s
                """,
                (emb_str, skill_normalized, emb_str, limit)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error("_fetch_related: %s", e)
            return []
        finally:
            cursor.close()
            return_connection(conn)

    # ------------------------------------------------------------------ #
    # Classification                                                       #
    # ------------------------------------------------------------------ #

    def _classify(
        self,
        skill_name: str,
        query_level: Optional[int],
        user_level: Optional[str],
        candidates: List[Dict],
    ) -> Tuple[List, List, List]:
        """
        Assign each candidate to prerequisites / complementary / next_level.

        Primary strategy (query_level is known):
          candidate_level < query_level  → prerequisite
          candidate_level = query_level  → complementary   (must have sim >= 0.40)
          candidate_level > query_level  → next_level

        Fallback (query_level unknown, or candidate level unknown):
          Use similarity bands as a secondary signal:
            sim >= 0.50  → complementary
            sim  0.28–0.49  → prerequisite (by default, since we can't tell direction)
          Anything classified as fallback-prerequisite that is also in the
          "higher similarity" zone for next_level gets re-scored.

        user_level adjustments:
          expert    → fewer prerequisites shown (they already know the basics)
          beginner  → more prerequisites, fewer next_level in response
        """
        pre:  List[Dict] = []
        comp: List[Dict] = []
        nxt:  List[Dict] = []
        used: Set[str]   = set()

        # How many items to show per bucket based on user's stated level
        limits = self._bucket_limits(user_level)

        # ── Pass 1: level-hierarchy classification (most reliable) ──
        for r in candidates:
            name  = r['skill_name']
            sim   = r['similarity']
            c_lvl = _level_of(name)

            if name in used or sim >= 0.80:   # skip near-duplicates
                continue

            if query_level is not None and c_lvl is not None:
                entry = self._make_entry(name, r, sim)

                if c_lvl < query_level and len(pre) < limits['pre']:
                    pre.append({**entry, "reason": self._pre_reason(name, skill_name)})
                    used.add(name)

                elif c_lvl == query_level and sim >= 0.40 and len(comp) < limits['comp']:
                    comp.append({**entry, "reason": self._comp_reason(name, skill_name)})
                    used.add(name)

                elif c_lvl > query_level and len(nxt) < limits['nxt']:
                    nxt.append({**entry, "reason": self._nxt_reason(name, skill_name)})
                    used.add(name)

        # ── Pass 2: fallback for unknown-level candidates ────────────
        # Only runs for candidates not yet classified
        for r in candidates:
            name = r['skill_name']
            sim  = r['similarity']

            if name in used or sim >= 0.80:
                continue

            # If one of our buckets still needs filling, use similarity bands
            entry = self._make_entry(name, r, sim)

            if sim >= 0.50 and len(comp) < limits['comp']:
                comp.append({**entry, "reason": self._comp_reason(name, skill_name)})
                used.add(name)

            elif 0.28 <= sim < 0.50:
                # Decide pre vs nxt based on whether next_level still needs filling
                # and we have a query level to reason about
                if len(nxt) < limits['nxt'] and query_level is not None and query_level >= 3:
                    # For mid/advanced skills the fallback lower-band is likely next-level
                    nxt.append({**entry, "reason": self._nxt_reason(name, skill_name)})
                    used.add(name)
                elif len(pre) < limits['pre']:
                    pre.append({**entry, "reason": self._pre_reason(name, skill_name)})
                    used.add(name)

        # ── Pass 3: guarantee no empty bucket ────────────────────────
        all_unused = [r for r in candidates
                      if r['skill_name'] not in used and r['similarity'] < 0.80]

        if not comp:
            for r in sorted(all_unused, key=lambda x: -x['similarity']):
                if len(comp) < limits['comp']:
                    comp.append({**self._make_entry(r['skill_name'], r, r['similarity']),
                                  "reason": f"Semantically related to {skill_name}"})
                    used.add(r['skill_name'])

        if not nxt:
            for r in all_unused:
                if r['skill_name'] not in used and len(nxt) < limits['nxt']:
                    nxt.append({**self._make_entry(r['skill_name'], r, r['similarity']),
                                 "reason": self._nxt_reason(r['skill_name'], skill_name)})
                    used.add(r['skill_name'])

        if not pre:
            for r in sorted(all_unused, key=lambda x: x['similarity']):
                if r['skill_name'] not in used and len(pre) < limits['pre']:
                    pre.append({**self._make_entry(r['skill_name'], r, r['similarity']),
                                 "reason": self._pre_reason(r['skill_name'], skill_name)})
                    used.add(r['skill_name'])

        # ── Sort each bucket pedagogically ───────────────────────────
        # prerequisites: lowest level first (most foundational)
        pre.sort(key=lambda x: (_level_of(x['skill_name']) or 99, -x['similarity']))
        # complementary: highest similarity first
        comp.sort(key=lambda x: -x['similarity'])
        # next_level: lowest next-level first (gradual progression)
        nxt.sort(key=lambda x: (_level_of(x['skill_name']) or 0, -x['similarity']))

        return pre, comp, nxt

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _bucket_limits(user_level: Optional[str]) -> Dict[str, int]:
        """How many items to return per bucket based on user's level."""
        defaults = {"pre": 3, "comp": 3, "nxt": 3}
        if user_level == "expert":
            defaults["pre"] = 1    # experts need fewer prerequisites
            defaults["nxt"] = 3
        elif user_level == "beginner":
            defaults["pre"] = 3
            defaults["nxt"] = 2    # don't overwhelm beginners with advanced topics
        return defaults

    @staticmethod
    def _make_entry(name: str, row: Dict, sim: float) -> Dict:
        return {
            "skill_name":     name,
            "skill_category": row.get('skill_category'),
            "similarity":     round(sim, 3),
        }

    @staticmethod
    def _pre_reason(candidate: str, query: str) -> str:
        return f"A foundational skill to master before learning {query}"

    @staticmethod
    def _comp_reason(candidate: str, query: str) -> str:
        return f"Complements {query} — commonly learned together"

    @staticmethod
    def _nxt_reason(candidate: str, query: str) -> str:
        return f"A natural progression after mastering {query}"


# Singleton
_learning_path_service = None

def get_learning_path_service() -> LearningPathService:
    global _learning_path_service
    if _learning_path_service is None:
        _learning_path_service = LearningPathService()
    return _learning_path_service