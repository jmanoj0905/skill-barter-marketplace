"""
Matching Service
Finds compatible barter partners using semantic skill matching and multi-factor scoring
"""

from typing import List, Dict, Optional, Tuple
from app.services.embedding_service import get_embedding_service
from app.core.database import get_connection, return_connection
from psycopg2.extras import RealDictCursor
import numpy as np


class MatchingService:
    """
    Service for finding and scoring potential barter partners
    Uses AI embeddings for semantic skill matching
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
        2. Find users offering similar skills (vector search)
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
                'skills_offered': self._get_user_skills(candidate['user_id'], 'offered'),
                'skills_wanted': self._get_user_skills(candidate['user_id'], 'desired'),
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
        Uses PostgreSQL pgvector for fast similarity search
        
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
            cursor.execute(
                """
                SELECT DISTINCT
                    s.user_id,
                    s.skill_name,
                    s.proficiency_level,
                    1 - (s.embedding <=> %s::vector) as similarity
                FROM skills s
                WHERE s.skill_type = 'offered'
                  AND s.user_id != %s
                  AND s.embedding IS NOT NULL
                  AND 1 - (s.embedding <=> %s::vector) >= %s
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
        
        Returns:
            Skill name if mutual interest found, None otherwise
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get what user A offers
            cursor.execute(
                """
                SELECT skill_name, embedding::text as embedding
                FROM skills
                WHERE user_id = %s AND skill_type = 'offered' AND embedding IS NOT NULL
                """,
                (user_a_id,)
            )
            user_a_offers = cursor.fetchall()
            
            if not user_a_offers:
                return None
            
            # Get what user B wants
            cursor.execute(
                """
                SELECT skill_name, embedding::text as embedding
                FROM skills
                WHERE user_id = %s AND skill_type = 'desired' AND embedding IS NOT NULL
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
        
        Scoring formula:
        - Base score: 0.95 if mutual interest, 0.70 if one-sided
        - Skill similarity: weighted at 50%
        - Trust compatibility: weighted at 30%
        - Activity level: weighted at 20%
        
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
        # Penalize large trust score differences
        # Users with similar trust levels should match better
        trust_diff = abs(current_user['trust_score'] - candidate['trust_score'])
        trust_score = 1.0 - (trust_diff * 0.5)  # Max penalty is 0.5
        trust_score = max(0.0, min(1.0, trust_score))  # Clamp to [0, 1]
        
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
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute(
                """
                SELECT skill_name
                FROM skills
                WHERE user_id = %s AND skill_type = %s
                ORDER BY skill_name
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
        Useful for debugging and analytics
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Count skills offered and wanted
            cursor.execute(
                """
                SELECT 
                    COUNT(CASE WHEN skill_type = 'offered' THEN 1 END) as skills_offered,
                    COUNT(CASE WHEN skill_type = 'desired' THEN 1 END) as skills_wanted,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as skills_with_embeddings
                FROM skills
                WHERE user_id = %s
                """,
                (user_id,)
            )
            skill_stats = cursor.fetchone()
            
            # Count potential matches for each wanted skill
            cursor.execute(
                """
                SELECT COUNT(DISTINCT s2.user_id) as potential_partners
                FROM skills s1
                JOIN skills s2 ON s1.skill_type = 'desired' AND s2.skill_type = 'offered'
                WHERE s1.user_id = %s
                  AND s2.user_id != %s
                  AND s1.embedding IS NOT NULL
                  AND s2.embedding IS NOT NULL
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