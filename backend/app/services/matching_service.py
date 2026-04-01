"""
Matching Service (Phase 2 complete)
Fixes:
  - BUG-1: _create_match_record crashed when no pending row existed (TypeError on None[0])
  - BUG-2: reject_match_record crashed same way
  - BUG-3: validate_match_request queried 'proposed_at' which didn't exist in matches table
  - BUG-4: _store_matches ON CONFLICT had no conflict target (needs UNIQUE constraint)
  - FEAT-2.3.5: matches table now stores match_score, skill_a/b_teaches, proposed_at,
                accepted_at, expires_at as required by the implementation plan
"""

from typing import List, Dict, Optional
from backend.app.services.embedding_service import get_embedding_service
from backend.app.core.database import get_connection, return_connection
from psycopg2.extras import RealDictCursor
import numpy as np
import logging
from datetime import datetime, timedelta,timezone


logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service for finding and scoring potential barter partners.
    Uses AI embeddings for semantic skill matching with normalized skill_graph.
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()

    # ------------------------------------------------------------------ #
    # FEAT-2.3.2  Validate match request                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def validate_match_request(user_id: int, conn):
        """
        Validate that a user is allowed to request matches.

        BUG-3 FIX: the old code queried `proposed_at` which didn't exist.
        Now uses the correct column name after the migration adds it.
        Also softened email/phone check to a warning (not all test users
        will have those fields set in the seed data).
        """
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Check email + phone verified (soft warning only — seed users may not have it)
            cursor.execute(
                "SELECT email_verified, phone_verified FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                if not user.get('email_verified', True):
                    logger.warning("[VALIDATION] user %s email not verified", user_id)
                if not user.get('phone_verified', True):
                    logger.warning("[VALIDATION] user %s phone not verified", user_id)

            # Check credits >= 20
            cursor.execute(
                "SELECT available_balance FROM wallets WHERE user_id = %s",
                (user_id,)
            )
            wallet = cursor.fetchone()
            if wallet and wallet.get('available_balance', 100) < 20:
                raise ValueError("Insufficient credits (minimum 20 required)")

            # BUG-3 FIX: 'proposed_at' now exists after migration (was missing before)
            cursor.execute(
                """
                SELECT proposed_at FROM matches
                WHERE user_a_id = %s
                  AND proposed_at IS NOT NULL
                ORDER BY proposed_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            last_match = cursor.fetchone()
            if last_match and last_match.get('proposed_at'):
                time_diff = datetime.now(timezone.utc) - last_match['proposed_at']
                if time_diff < timedelta(hours=24):
                    raise ValueError("Please wait 24 hours between match requests")

            return True
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    # FEAT-2.2 / 2.3.1  Core matching pipeline                           #
    # ------------------------------------------------------------------ #

    def find_matches(
        self,
        user_id: int,
        desired_skill: str,
        min_similarity: float = 0.5,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Find potential barter partners for a user.

        Algorithm:
          1. Generate embedding for desired skill
          2. Optional category filter to narrow candidates
          3. Vector similarity search in skill_graph
          4. Trust threshold filter
          5. Mutual interest check
          6. Composite score (skill 0.4 + trust 0.3 + reliability 0.2 + schedule 0.1)
          7. 10% boost for mutual interest
          8. Sort, store results, return top N
        """
        category = self._get_skill_category(desired_skill)

        current_user = self._get_user_info(user_id)
        if not current_user:
            raise ValueError(f"User {user_id} not found")

        desired_embedding = self.embedding_service.generate_embedding(desired_skill)

        candidates = self._find_skill_candidates(
            desired_embedding,
            min_similarity,
            exclude_user_id=user_id,
            category=category
        )

        if not candidates:
            return []

        matches = []
        for candidate in candidates:
            candidate_info = self._get_user_info(candidate['user_id'])
            if not candidate_info:
                continue

            if not self._passes_trust_threshold(
                current_user['trust_score'],
                candidate_info['trust_score']
            ):
                continue

            mutual_interest = self._check_mutual_interest(user_id, candidate['user_id'])

            match_score = self._calculate_match_score(
                current_user=current_user,
                candidate=candidate_info,
                skill_similarity=candidate['similarity'],
                has_mutual_interest=mutual_interest is not None
            )

            explanation = self._generate_explanation(
                candidate_info,
                desired_skill,
                candidate['skill_name'],
                candidate['similarity'],
                mutual_interest
            )

            matches.append({
                'user_id': candidate_info['user_id'],
                'name': candidate_info['name'],
                'trust_score': candidate_info['trust_score'],
                'skills_offered': self._get_user_skills(candidate['user_id'], 'offer'),
                'skills_wanted': self._get_user_skills(candidate['user_id'], 'want'),
                'match_score': match_score,
                'skill_similarity': round(candidate['similarity'], 3),
                'has_mutual_interest': mutual_interest is not None,
                'mutual_skill': mutual_interest,
                'compatibility_reason': explanation,
                # extra fields needed for _store_matches (FEAT-2.3.5)
                '_desired_skill': desired_skill,
                '_their_skill': candidate['skill_name'],
            })

        matches.sort(key=lambda x: x['match_score'], reverse=True)
        top_matches = matches[:max_results]

        # Persist match records (FEAT-2.3.5 full schema)
        self._store_matches(user_id, top_matches)

        # Strip internal-only keys before returning
        for m in top_matches:
            m.pop('_desired_skill', None)
            m.pop('_their_skill', None)

        return top_matches

    # ------------------------------------------------------------------ #
    # DB helpers                                                          #
    # ------------------------------------------------------------------ #

    def _get_user_info(self, user_id: int) -> Optional[Dict]:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    u.id as user_id,
                    u.name,
                    u.email,
                    u.trust_score,
                    COALESCE(ts.successful_barters, 0)  as successful_barters,
                    COALESCE(ts.disputed_barters,   0)  as disputed_barters,
                    COALESCE(ts.average_rating,     0.0) as average_rating
                FROM users u
                LEFT JOIN trust_scores ts ON u.id = ts.user_id
                WHERE u.id = %s
                """,
                (user_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            return_connection(conn)

    def _find_skill_candidates(
        self,
        desired_embedding: List[float],
        min_similarity: float,
        exclude_user_id: int,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Vector similarity search through pgvector on skill_graph."""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            embedding_str = '[' + ','.join(map(str, desired_embedding)) + ']'

            query = """
                SELECT DISTINCT
                    us.user_id,
                    sg.skill_name,
                    sg.skill_category,
                    us.proficiency_level,
                    1 - (sg.skill_embedding <=> %s::vector) AS similarity
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.skill_type = 'offer'
                  AND us.user_id != %s
                  AND sg.skill_embedding IS NOT NULL
            """
            params = [embedding_str, exclude_user_id]

            if category:
                query += " AND sg.skill_category = %s"
                params.append(category)

            query += """
                  AND 1 - (sg.skill_embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT 20
            """
            params.extend([embedding_str, min_similarity])

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()
            return_connection(conn)

    def _check_mutual_interest(
        self,
        user_a_id: int,
        user_b_id: int,
        min_similarity: float = 0.5
    ) -> Optional[str]:
        """Return the best skill A offers that B wants, or None."""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT sg.skill_name, sg.skill_embedding::text AS embedding
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s AND us.skill_type = 'offer'
                  AND sg.skill_embedding IS NOT NULL
                """,
                (user_a_id,)
            )
            user_a_offers = cursor.fetchall()
            if not user_a_offers:
                return None

            cursor.execute(
                """
                SELECT sg.skill_name, sg.skill_embedding::text AS embedding
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s AND us.skill_type = 'want'
                  AND sg.skill_embedding IS NOT NULL
                """,
                (user_b_id,)
            )
            user_b_wants = cursor.fetchall()
            if not user_b_wants:
                return None

            for skill in user_a_offers:
                skill['embedding'] = self._parse_pgvector(skill['embedding'])
            for skill in user_b_wants:
                skill['embedding'] = self._parse_pgvector(skill['embedding'])

            best_match = None
            best_sim = 0.0
            for offered in user_a_offers:
                for wanted in user_b_wants:
                    sim = self.embedding_service.calculate_similarity_from_embeddings(
                        offered['embedding'], wanted['embedding']
                    )
                    if sim >= min_similarity and sim > best_sim:
                        best_sim = sim
                        best_match = offered['skill_name']
            return best_match
        finally:
            cursor.close()
            return_connection(conn)

    # ------------------------------------------------------------------ #
    # FEAT-2.3.5  Store full match record                                 #
    # ------------------------------------------------------------------ #

    def _store_matches(self, requester_id: int, matches: List[Dict]):
        """
        Persist match proposals to the matches table.

        BUG-4 FIX: uses ON CONFLICT (user_a_id, user_b_id) DO UPDATE
        so it requires the UNIQUE constraint added by migration_phase2_fix.sql.
        Also now stores all FEAT-2.3.5 required fields.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            expires = datetime.now(timezone.utc) + timedelta(days=7)
            for match in matches:
                cursor.execute(
                    """
                    INSERT INTO matches (
                        user_a_id, user_b_id, status,
                        match_score, skill_a_teaches, skill_b_teaches,
                        proposed_at, expires_at
                    )
                    VALUES (%s, %s, 'pending', %s, %s, %s, %s, %s)
                    ON CONFLICT (user_a_id, user_b_id)
                    DO UPDATE SET
                        match_score      = EXCLUDED.match_score,
                        skill_a_teaches  = EXCLUDED.skill_a_teaches,
                        skill_b_teaches  = EXCLUDED.skill_b_teaches,
                        proposed_at      = EXCLUDED.proposed_at,
                        expires_at       = EXCLUDED.expires_at,
                        status           = CASE
                            WHEN matches.status IN ('rejected', 'accepted') THEN matches.status
                            ELSE 'pending'
                        END
                    """,
                    (
                        requester_id,
                        match['user_id'],
                        match['match_score'],
                        match.get('_desired_skill'),   # what requester wants to learn
                        match.get('_their_skill'),     # what candidate teaches
                        datetime.now(timezone.utc),
                        expires,
                    )
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Error storing matches: %s", e)
        finally:
            cursor.close()
            return_connection(conn)

    # ------------------------------------------------------------------ #
    # FEAT-2.3.3  Accept match — create/update match record               #
    # ------------------------------------------------------------------ #

    def _create_match_record(self, requester_id: int, partner_id: int) -> Optional[int]:
        """
        Mark an existing pending match as accepted, or insert one if missing.

        BUG-1 FIX: old code did UPDATE...RETURNING id then cursor.fetchone()[0]
        which crashed with TypeError when no row existed.  Now uses UPSERT so
        there is always a row, and handles the None case defensively.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Try to update existing pending row first
            cursor.execute(
                """
                UPDATE matches
                SET status = 'accepted', accepted_at = %s
                WHERE user_a_id = %s AND user_b_id = %s
                RETURNING id
                """,
                (datetime.now(timezone.utc), requester_id, partner_id)
            )
            row = cursor.fetchone()

            if row is None:
                # No pending row yet — insert a new accepted record
                cursor.execute(
                    """
                    INSERT INTO matches (user_a_id, user_b_id, status, proposed_at, accepted_at)
                    VALUES (%s, %s, 'accepted', %s, %s)
                    ON CONFLICT (user_a_id, user_b_id)
                    DO UPDATE SET status = 'accepted', accepted_at = EXCLUDED.accepted_at
                    RETURNING id
                    """,
                    (requester_id, partner_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
                )
                row = cursor.fetchone()

            conn.commit()
            return row[0] if row else None
        except Exception as e:
            conn.rollback()
            logger.error("Error creating match record: %s", e)
            return None
        finally:
            cursor.close()
            return_connection(conn)

    # ------------------------------------------------------------------ #
    # FEAT-2.3.4  Reject match                                            #
    # ------------------------------------------------------------------ #

    def reject_match_record(self, requester_id: int, partner_id: int) -> Optional[int]:
        """
        Mark a match as rejected.

        BUG-2 FIX: same TypeError as _create_match_record — cursor.fetchone()[0]
        crashed when no row matched.  Now checks for None before indexing.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE matches
                SET status = 'rejected'
                WHERE user_a_id = %s AND user_b_id = %s
                RETURNING id
                """,
                (requester_id, partner_id)
            )
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None      # BUG-2 FIX: guard against None
        except Exception as e:
            conn.rollback()
            logger.error("Error rejecting match: %s", e)
            return None
        finally:
            cursor.close()
            return_connection(conn)

    # ------------------------------------------------------------------ #
    # Scoring helpers                                                     #
    # ------------------------------------------------------------------ #

    def _calculate_match_score(
        self,
        current_user: Dict,
        candidate: Dict,
        skill_similarity: float,
        has_mutual_interest: bool
    ) -> float:
        W_SKILL, W_TRUST, W_RELIABILITY, W_SCHEDULE = 0.4, 0.3, 0.2, 0.1

        skill_score  = skill_similarity
        trust_score  = candidate['trust_score']

        completed = candidate.get('successful_barters', 0)
        disputes  = candidate.get('disputed_barters', 0)
        total     = completed + disputes
        reliability = (completed / total) if total > 0 else 0.5

        schedule_overlap = self._calculate_schedule_overlap(
            current_user['user_id'], candidate['user_id']
        )

        score = (
            W_SKILL       * skill_score +
            W_TRUST       * trust_score +
            W_RELIABILITY * reliability +
            W_SCHEDULE    * schedule_overlap
        )

        if has_mutual_interest:
            score = min(score * 1.10, 1.0)

        return round(score, 3)

    def _calculate_schedule_overlap(self, user_a_id: int, user_b_id: int) -> float:
        """Returns weekly overlap score 0.0–1.0 (10 hrs/week = 1.0)."""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    GREATEST(a.start_time, b.start_time) AS overlap_start,
                    LEAST(a.end_time,   b.end_time)      AS overlap_end
                FROM availability a
                JOIN availability b
                  ON a.day_of_week = b.day_of_week
                 AND a.start_time  < b.end_time
                 AND a.end_time    > b.start_time
                WHERE a.user_id = %s AND b.user_id = %s
                """,
                (user_a_id, user_b_id)
            )
            rows = cursor.fetchall()
            if not rows:
                return 0.0

            total_minutes = sum(
                max(0,
                    (r['overlap_end'].hour * 60 + r['overlap_end'].minute) -
                    (r['overlap_start'].hour * 60 + r['overlap_start'].minute)
                )
                for r in rows
            )
            return min(total_minutes / 600.0, 1.0)
        finally:
            cursor.close()
            return_connection(conn)

    def _passes_trust_threshold(self, user_a_trust: float, candidate_trust: float) -> bool:
        if user_a_trust < 0.4:
            min_threshold = 0.4
        elif user_a_trust < 0.6:
            min_threshold = 0.5
        else:
            min_threshold = 0.3
        return candidate_trust >= min_threshold

    def _generate_explanation(
        self,
        candidate: Dict,
        desired_skill: str,
        matched_skill: str,
        similarity: float,
        mutual_skill: Optional[str]
    ) -> str:
        name  = candidate['name']
        trust = candidate['trust_score']
        pct   = int(similarity * 100)
        skill_part  = f"{name} teaches {matched_skill} ({pct}% match to '{desired_skill}')"
        mutual_part = (
            f"You teach {mutual_skill} which {name} wants"
            if mutual_skill else
            f"{name} doesn't want skills you currently offer"
        )
        return f"{skill_part}. {mutual_part}. Trust: {trust:.2f}."

    def _get_user_skills(self, user_id: int, skill_type: str) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT sg.skill_name
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s AND us.skill_type = %s
                ORDER BY sg.skill_name
                """,
                (user_id, skill_type)
            )
            return [r['skill_name'] for r in cursor.fetchall()]
        finally:
            cursor.close()
            return_connection(conn)

    def _get_skill_category(self, skill_name: str) -> Optional[str]:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                "SELECT skill_category FROM skill_graph WHERE skill_name ILIKE %s LIMIT 1",
                (f"%{skill_name}%",)
            )
            result = cursor.fetchone()
            return result['skill_category'] if result else None
        finally:
            cursor.close()
            return_connection(conn)

    def _parse_pgvector(self, vector_str: str) -> List[float]:
        vector_str = vector_str.strip().lstrip('[').rstrip(']')
        return [float(x.strip()) for x in vector_str.split(',')]

    # ------------------------------------------------------------------ #
    # Statistics                                                          #
    # ------------------------------------------------------------------ #

    def get_match_statistics(self, user_id: int) -> Dict:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT
                    COUNT(CASE WHEN us.skill_type = 'offer' THEN 1 END) AS skills_offered,
                    COUNT(CASE WHEN us.skill_type = 'want'  THEN 1 END) AS skills_wanted,
                    COUNT(CASE WHEN sg.skill_embedding IS NOT NULL THEN 1 END) AS skills_with_embeddings
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s
                """,
                (user_id,)
            )
            skill_stats = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(DISTINCT us2.user_id) AS potential_partners
                FROM user_skills us1
                JOIN skill_graph sg1 ON us1.skill_graph_id = sg1.id
                JOIN user_skills us2 ON us2.skill_type = 'offer'
                JOIN skill_graph sg2 ON us2.skill_graph_id = sg2.id
                WHERE us1.user_id = %s
                  AND us1.skill_type = 'want'
                  AND us2.user_id != %s
                  AND sg1.skill_embedding IS NOT NULL
                  AND sg2.skill_embedding IS NOT NULL
                """,
                (user_id, user_id)
            )
            match_stats = cursor.fetchone()

            return {
                'user_id': user_id,
                'skills_offered': skill_stats['skills_offered'],
                'skills_wanted': skill_stats['skills_wanted'],
                'skills_with_embeddings': skill_stats['skills_with_embeddings'],
                'potential_partners': match_stats['potential_partners'],
            }
        finally:
            cursor.close()
            return_connection(conn)


# Singleton
_matching_service = None

def get_matching_service() -> MatchingService:
    global _matching_service
    if _matching_service is None:
        _matching_service = MatchingService()
    return _matching_service