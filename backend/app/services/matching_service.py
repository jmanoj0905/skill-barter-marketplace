"""
Matching Service (Updated for skill_graph + user_skills schema)
Finds compatible barter partners using semantic skill matching
"""

from typing import List, Dict, Optional
from backend.app.services.embedding_service import get_embedding_service
from backend.app.core.database import get_connection, return_connection
from psycopg2.extras import RealDictCursor
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service for finding and scoring potential barter partners
    Uses AI embeddings for semantic skill matching with normalized skill_graph
    """
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
    
    def find_matches(
        self,
        user_id: int,
        desired_skill: str,
        min_similarity: float = 0.5,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Find potential barter partners for a user
        
        Algorithm:
        1. Generate embedding for desired skill
        2. Find users offering similar skills (vector search on skill_graph)
        3. Check mutual interest (do they want what you offer?)
        4. Calculate match score (skill + trust + activity)
        5. Generate human-readable explanation
        6. Return top matches sorted by score
        
        Args:
            user_id: Current user's ID
            desired_skill: Skill the user wants to learn
            min_similarity: Minimum skill similarity threshold (0.0-1.0)
            max_results: Maximum number of matches to return
            
        Returns:
            List of match dictionaries with scores and explanations
        """
        
        # Step 1: Get current user info
        current_user = self._get_user_info(user_id)
        if not current_user:
            raise ValueError(f"User {user_id} not found")
        
        # Step 2: Generate embedding for desired skill
        desired_embedding = self.embedding_service.generate_embedding(desired_skill)
        
        # Step 3: Find users offering similar skills (vector similarity search)
        candidates = self._find_skill_candidates(
            desired_embedding,
            min_similarity,
            exclude_user_id=user_id
        )
        
        if not candidates:
            return []
        
        # Step 4: Check mutual interest and calculate scores
        matches = []
        for candidate in candidates:
            # Get candidate's full info
            candidate_info = self._get_user_info(candidate['user_id'])
            if not candidate_info:
                continue
            
            # Check if candidate wants any skill current user offers
            mutual_interest = self._check_mutual_interest(
                user_id,
                candidate['user_id']
            )
            
            # Calculate match score
            match_score = self._calculate_match_score(
                current_user=current_user,
                candidate=candidate_info,
                skill_similarity=candidate['similarity'],
                has_mutual_interest=mutual_interest is not None
            )
            
            # Generate explanation
            explanation = self._generate_explanation(
                candidate_info,
                desired_skill,
                candidate['skill_name'],
                candidate['similarity'],
                mutual_interest
            )
            
            # Build match object
            match = {
                'user_id': candidate_info['user_id'],
                'name': candidate_info['name'],
                'trust_score': candidate_info['trust_score'],
                'skills_offered': self._get_user_skills(candidate['user_id'], 'offer'),
                'skills_wanted': self._get_user_skills(candidate['user_id'], 'want'),
                'match_score': match_score,
                'skill_similarity': round(candidate['similarity'], 3),
                'has_mutual_interest': mutual_interest is not None,
                'mutual_skill': mutual_interest,
                'compatibility_reason': explanation
            }
            
            matches.append(match)
        
        # Step 5: Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Step 6: Return top matches
        return matches[:max_results]
    
    def _get_user_info(self, user_id: int) -> Optional[Dict]:
        """
        Get user's basic information and trust score
        """
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
                    COALESCE(ts.successful_barters, 0) as successful_barters,
                    COALESCE(ts.disputed_barters, 0) as disputed_barters,
                    COALESCE(ts.average_rating, 0.0) as average_rating
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
        exclude_user_id: int
    ) -> List[Dict]:
        """
        Find users offering skills similar to desired skill
        
        NEW: Queries skill_graph (canonical embeddings) joined with user_skills
        
        Returns list of candidates with their skill info and similarity scores
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Convert embedding to PostgreSQL vector format
            embedding_str = '[' + ','.join(map(str, desired_embedding)) + ']'
            
            # Vector similarity search using cosine distance
            # <=> is the cosine distance operator from pgvector
            # 1 - distance = similarity score
            #
            # NEW: JOIN user_skills → skill_graph to get canonical embeddings
            cursor.execute(
                """
                SELECT DISTINCT
                    us.user_id,
                    sg.skill_name,
                    us.proficiency_level,
                    1 - (sg.skill_embedding <=> %s::vector) as similarity
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.skill_type = 'offer'
                  AND us.user_id != %s
                  AND sg.skill_embedding IS NOT NULL
                  AND 1 - (sg.skill_embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT 20
                """,
                (embedding_str, exclude_user_id, embedding_str, min_similarity)
            )
            
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
        """
        Check if user B wants any skill that user A offers
        
        NEW: Queries through skill_graph for embeddings
        
        Returns:
            Skill name if mutual interest found, None otherwise
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get what user A offers (with embeddings from skill_graph)
            cursor.execute(
                """
                SELECT sg.skill_name, sg.skill_embedding::text as embedding
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s 
                  AND us.skill_type = 'offer' 
                  AND sg.skill_embedding IS NOT NULL
                """,
                (user_a_id,)
            )
            user_a_offers = cursor.fetchall()
            
            if not user_a_offers:
                return None
            
            # Get what user B wants (with embeddings from skill_graph)
            cursor.execute(
                """
                SELECT sg.skill_name, sg.skill_embedding::text as embedding
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s 
                  AND us.skill_type = 'want' 
                  AND sg.skill_embedding IS NOT NULL
                """,
                (user_b_id,)
            )
            user_b_wants = cursor.fetchall()
            
            if not user_b_wants:
                return None
            
            # Convert string embeddings to lists
            for skill in user_a_offers:
                skill['embedding'] = self._parse_pgvector(skill['embedding'])
            
            for skill in user_b_wants:
                skill['embedding'] = self._parse_pgvector(skill['embedding'])
            
            # Find best match between A's offers and B's wants
            best_match = None
            best_similarity = 0.0
            
            for offered in user_a_offers:
                for wanted in user_b_wants:
                    # Calculate similarity between offered and wanted skills
                    similarity = self.embedding_service.calculate_similarity_from_embeddings(
                        offered['embedding'],
                        wanted['embedding']
                    )
                    
                    if similarity >= min_similarity and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = offered['skill_name']
            
            return best_match
            
        finally:
            cursor.close()
            return_connection(conn)
    
    def _calculate_match_score(
        self,
        current_user: Dict,
        candidate: Dict,
        skill_similarity: float,
        has_mutual_interest: bool
    ) -> float:
        """
        Calculate overall match score using multiple factors
        
        FIXED: Trust component now measures candidate reliability,
               not similarity of trust levels (bug fix)
        
        Scoring formula:
        - Skill similarity: weighted at 50%
        - Trust score: weighted at 30% (FIXED: use candidate's trust directly)
        - Activity level: weighted at 20%
        - Mutual interest bonus: +10% if present
        
        Returns:
            Score between 0.0 and 1.0
        """
        # Weight factors (must sum to 1.0)
        W_SKILL = 0.50
        W_TRUST = 0.30
        W_ACTIVITY = 0.20
        
        # 1. Skill component (already calculated)
        skill_score = skill_similarity
        
        # 2. Trust compatibility component
        # FIXED: Use candidate's trust score directly as quality signal
        # Higher trust = better match (not penalize difference)
        trust_score = candidate['trust_score']
        
        # 3. Activity component
        # Prefer users with some successful barters (shows reliability)
        successful_barters = candidate.get('successful_barters', 0)
        activity_score = min(successful_barters / 5.0, 1.0)  # Caps at 5 barters
        
        # 4. Calculate weighted score
        composite_score = (
            W_SKILL * skill_score +
            W_TRUST * trust_score +
            W_ACTIVITY * activity_score
        )
        
        # 5. Boost for mutual interest
        if has_mutual_interest:
            # Perfect mutual matches get a 10% bonus
            composite_score = min(composite_score * 1.10, 1.0)
        
        return round(composite_score, 3)
    
    def _generate_explanation(
        self,
        candidate: Dict,
        desired_skill: str,
        matched_skill: str,
        similarity: float,
        mutual_skill: Optional[str]
    ) -> str:
        """
        Generate human-readable explanation of why users matched
        
        Examples:
        - "Bob teaches python programming (95% match to your search 'python'). 
           You teach graphic design which Bob wants. Trust: 0.78"
        - "Carol teaches spanish (87% match). Trust: 0.75. 
           Note: Carol doesn't want skills you offer"
        """
        name = candidate['name']
        trust = candidate['trust_score']
        
        # Part 1: Skill match explanation
        similarity_pct = int(similarity * 100)
        skill_part = f"{name} teaches {matched_skill} ({similarity_pct}% match to '{desired_skill}')"
        
        # Part 2: Mutual interest explanation
        if mutual_skill:
            mutual_part = f"You teach {mutual_skill} which {name} wants"
        else:
            mutual_part = f"{name} doesn't want skills you currently offer"
        
        # Part 3: Trust info
        trust_part = f"Trust: {trust:.2f}"
        
        # Combine
        explanation = f"{skill_part}. {mutual_part}. {trust_part}."
        
        return explanation
    
    def _get_user_skills(self, user_id: int, skill_type: str) -> List[str]:
        """
        Get list of skill names for a user
        
        NEW: Joins through skill_graph to get canonical names
        """
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
            
            results = cursor.fetchall()
            return [r['skill_name'] for r in results]
            
        finally:
            cursor.close()
            return_connection(conn)
    
    def _parse_pgvector(self, vector_str: str) -> List[float]:
        """
        Parse PostgreSQL vector string to Python list of floats
        
        PostgreSQL returns vectors as strings like: "[0.123,-0.456,0.789,...]"
        
        Args:
            vector_str: String representation of vector from PostgreSQL
            
        Returns:
            List of floats
        """
        # Remove brackets and split by comma
        vector_str = vector_str.strip()
        if vector_str.startswith('[') and vector_str.endswith(']'):
            vector_str = vector_str[1:-1]
        
        # Convert to list of floats
        return [float(x.strip()) for x in vector_str.split(',')]
    
    def get_match_statistics(self, user_id: int) -> Dict:
        """
        Get statistics about user's matching potential
        
        NEW: Updated to query skill_graph + user_skills
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Count skills offered and wanted
            cursor.execute(
                """
                SELECT 
                    COUNT(CASE WHEN us.skill_type = 'offer' THEN 1 END) as skills_offered,
                    COUNT(CASE WHEN us.skill_type = 'want' THEN 1 END) as skills_wanted,
                    COUNT(CASE WHEN sg.skill_embedding IS NOT NULL THEN 1 END) as skills_with_embeddings
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s
                """,
                (user_id,)
            )
            skill_stats = cursor.fetchone()
            
            # Count potential matches for each wanted skill
            cursor.execute(
                """
                SELECT COUNT(DISTINCT us2.user_id) as potential_partners
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
                'potential_partners': match_stats['potential_partners']
            }
            
        finally:
            cursor.close()
            return_connection(conn)


# Singleton instance
_matching_service = None

def get_matching_service() -> MatchingService:
    """
    Get the global matching service instance
    """
    global _matching_service
    if _matching_service is None:
        _matching_service = MatchingService()
    return _matching_service