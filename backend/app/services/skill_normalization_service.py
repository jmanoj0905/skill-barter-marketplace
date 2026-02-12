"""
Skill Normalization Service (FEAT-1.4.5, 1.4.6)
Manages canonical skill_graph and prevents duplicate embeddings
"""

from typing import Optional, Dict, Tuple
from backend.app.services.embedding_service import get_embedding_service
from backend.app.core.database import get_connection, return_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class SkillNormalizationService:
    """
    Handles adding skills with intelligent deduplication.
    
    When user adds "python programming":
    1. Generate embedding (384-dim vector)
    2. Search skill_graph for similar skills (cosine similarity)
    3. If similarity > 0.85 → reuse existing skill_graph entry
    4. If similarity <= 0.85 → create new skill_graph entry
    5. Link user to skill via user_skills table
    
    This prevents duplicate embeddings and enables skill popularity tracking.
    """
    
    SIMILARITY_THRESHOLD = 0.85  # Min similarity to consider skills identical
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
    
    def normalize_skill_name(self, skill_name: str) -> str:
        """
        Normalize skill text (FEAT-1.4.5)
        
        Examples:
            "Python Programming" → "python programming"
            "  GUITAR  " → "guitar"
            "Web   Development" → "web development"
        """
        return self.embedding_service.normalize_skill_name(skill_name)
    
    def find_or_create_skill(
        self, 
        skill_name: str,
        category: Optional[str] = None
    ) -> int:
        """
        Find existing skill or create new one (FEAT-1.4.6)
        
        Returns:
            skill_graph_id of matched or created skill
        """
        # Step 1: Normalize input
        skill_normalized = self.normalize_skill_name(skill_name)
        
        # Step 2: Check if exact match exists (fast path)
        exact_match = self._find_exact_match(skill_normalized)
        if exact_match:
            logger.info(f"Exact match found for '{skill_name}' → skill_graph_id={exact_match}")
            return exact_match
        
        # Step 3: Generate embedding
        embedding = self.embedding_service.generate_embedding(skill_normalized)
        
        # Step 4: Search for similar skills using vector similarity
        similar_skill = self._find_similar_skill(embedding, self.SIMILARITY_THRESHOLD)
        
        if similar_skill:
            logger.info(
                f"Similar skill found: '{skill_name}' → '{similar_skill['skill_name']}' "
                f"(similarity={similar_skill['similarity']:.3f})"
            )
            return similar_skill['id']
        
        # Step 5: No match found → create new canonical skill
        new_skill_id = self._create_skill(
            skill_name=skill_name,
            skill_normalized=skill_normalized,
            embedding=embedding,
            category=category
        )
        
        logger.info(f"Created new skill: '{skill_name}' → skill_graph_id={new_skill_id}")
        return new_skill_id
    
    def add_user_skill(
        self,
        user_id: int,
        skill_name: str,
        skill_type: str,  # 'offer' or 'want'
        proficiency_level: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict:
        """
        Add a skill to a user's profile with automatic normalization
        
        Args:
            user_id: User's ID
            skill_name: Raw skill name from user input
            skill_type: 'offer' or 'want'
            proficiency_level: Optional proficiency ('beginner', 'intermediate', 'advanced', 'expert')
            category: Optional category hint for new skills
        
        Returns:
            Dict with skill_graph_id, user_skills_id, skill_name
        """
        # Validate skill_type
        if skill_type not in ('offer', 'want'):
            raise ValueError(f"skill_type must be 'offer' or 'want', got: {skill_type}")
        
        # Validate proficiency_level
        valid_proficiency = ('beginner', 'intermediate', 'advanced', 'expert', None)
        if proficiency_level not in valid_proficiency:
            raise ValueError(f"Invalid proficiency_level: {proficiency_level}")
        
        # Step 1: Find or create canonical skill
        skill_graph_id = self.find_or_create_skill(skill_name, category)
        
        # Step 2: Link user to skill (with duplicate check)
        user_skills_id = self._link_user_to_skill(
            user_id=user_id,
            skill_graph_id=skill_graph_id,
            skill_type=skill_type,
            proficiency_level=proficiency_level
        )
        
        # Step 3: Update popularity score
        self._update_popularity(skill_graph_id)
        
        return {
            'user_skills_id': user_skills_id,
            'skill_graph_id': skill_graph_id,
            'skill_name': skill_name,
            'skill_type': skill_type,
            'proficiency_level': proficiency_level
        }
    
    def remove_user_skill(self, user_id: int, user_skills_id: int) -> bool:
        """
        Remove a skill from user's profile
        
        Returns:
            True if removed, False if not found
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Verify ownership and get skill_graph_id before deleting
            cursor.execute(
                """
                SELECT skill_graph_id FROM user_skills
                WHERE id = %s AND user_id = %s
                """,
                (user_skills_id, user_id)
            )
            
            result = cursor.fetchone()
            if not result:
                return False
            
            skill_graph_id = result['skill_graph_id']
            
            # Delete user_skills entry
            cursor.execute(
                "DELETE FROM user_skills WHERE id = %s",
                (user_skills_id,)
            )
            
            conn.commit()
            
            # Update popularity score
            self._update_popularity(skill_graph_id)
            
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error removing user skill: {e}")
            raise
        finally:
            cursor.close()
            return_connection(conn)
    
    def _find_exact_match(self, skill_normalized: str) -> Optional[int]:
        """
        Check if exact normalized match exists in skill_graph
        Fast path using index on skill_normalized
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute(
                """
                SELECT id FROM skill_graph
                WHERE skill_normalized = %s
                """,
                (skill_normalized,)
            )
            
            result = cursor.fetchone()
            return result['id'] if result else None
            
        finally:
            cursor.close()
            return_connection(conn)
    
    def _find_similar_skill(
        self, 
        embedding: list, 
        threshold: float
    ) -> Optional[Dict]:
        """
        Find most similar skill in skill_graph using vector search
        
        Returns:
            Dict with id, skill_name, similarity if match found, else None
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Convert embedding to pgvector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            # Vector similarity search
            # <=> is cosine distance, 1 - distance = similarity
            cursor.execute(
                """
                SELECT 
                    id,
                    skill_name,
                    skill_normalized,
                    1 - (skill_embedding <=> %s::vector) as similarity
                FROM skill_graph
                WHERE skill_embedding IS NOT NULL
                  AND 1 - (skill_embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT 1
                """,
                (embedding_str, embedding_str, threshold)
            )
            
            return cursor.fetchone()
            
        finally:
            cursor.close()
            return_connection(conn)
    
    def _create_skill(
        self,
        skill_name: str,
        skill_normalized: str,
        embedding: list,
        category: Optional[str] = None
    ) -> int:
        """
        Create new skill in skill_graph
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Convert embedding to pgvector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            cursor.execute(
                """
                INSERT INTO skill_graph (
                    skill_name, 
                    skill_normalized, 
                    skill_embedding,
                    skill_category,
                    popularity_score
                )
                VALUES (%s, %s, %s::vector, %s, 0.0)
                RETURNING id
                """,
                (skill_name, skill_normalized, embedding_str, category)
            )
            
            result = cursor.fetchone()
            conn.commit()
            
            return result['id']
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating skill: {e}")
            raise
        finally:
            cursor.close()
            return_connection(conn)
    
    def _link_user_to_skill(
        self,
        user_id: int,
        skill_graph_id: int,
        skill_type: str,
        proficiency_level: Optional[str]
    ) -> int:
        """
        Create user_skills entry linking user to canonical skill
        Handles duplicate check (user can't add same skill twice)
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if already exists
            cursor.execute(
                """
                SELECT id FROM user_skills
                WHERE user_id = %s 
                  AND skill_graph_id = %s 
                  AND skill_type = %s
                """,
                (user_id, skill_graph_id, skill_type)
            )
            
            existing = cursor.fetchone()
            if existing:
                logger.info(f"User {user_id} already has this skill, returning existing ID")
                return existing['id']
            
            # Insert new link
            cursor.execute(
                """
                INSERT INTO user_skills (
                    user_id, 
                    skill_graph_id, 
                    skill_type, 
                    proficiency_level
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (user_id, skill_graph_id, skill_type, proficiency_level)
            )
            
            result = cursor.fetchone()
            conn.commit()
            
            return result['id']
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error linking user to skill: {e}")
            raise
        finally:
            cursor.close()
            return_connection(conn)
    
    def _update_popularity(self, skill_graph_id: int):
        """
        Update popularity score for a skill (FEAT-2.1.3)
        Score = (offer_count * 0.6) + (want_count * 0.4)
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute(
                """
                UPDATE skill_graph
                SET popularity_score = (
                    SELECT 
                        (COUNT(*) FILTER (WHERE skill_type = 'offer') * 0.6) +
                        (COUNT(*) FILTER (WHERE skill_type = 'want') * 0.4)
                    FROM user_skills
                    WHERE skill_graph_id = %s
                ),
                updated_at = NOW()
                WHERE id = %s
                """,
                (skill_graph_id, skill_graph_id)
            )
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating popularity: {e}")
            # Don't raise - this is non-critical
        finally:
            cursor.close()
            return_connection(conn)
    
    def get_user_skills(
        self, 
        user_id: int, 
        skill_type: Optional[str] = None
    ) -> list:
        """
        Get all skills for a user
        
        Args:
            user_id: User's ID
            skill_type: Optional filter ('offer' or 'want')
        
        Returns:
            List of skill dicts with skill_graph data
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            query = """
                SELECT 
                    us.id as user_skills_id,
                    us.skill_type,
                    us.proficiency_level,
                    sg.id as skill_graph_id,
                    sg.skill_name,
                    sg.skill_category,
                    sg.popularity_score
                FROM user_skills us
                JOIN skill_graph sg ON us.skill_graph_id = sg.id
                WHERE us.user_id = %s
            """
            params = [user_id]
            
            if skill_type:
                query += " AND us.skill_type = %s"
                params.append(skill_type)
            
            query += " ORDER BY sg.skill_name"
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
        finally:
            cursor.close()
            return_connection(conn)
    
    def search_skills(
        self, 
        query: str, 
        limit: int = 10
    ) -> list:
        """
        Search skills by name or semantic similarity (for autocomplete)
        
        Returns:
            List of matching skills with similarity scores
        """
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_service.generate_embedding(query)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Search by both exact match and semantic similarity
            cursor.execute(
                """
                SELECT 
                    id,
                    skill_name,
                    skill_category,
                    popularity_score,
                    1 - (skill_embedding <=> %s::vector) as similarity,
                    CASE 
                        WHEN skill_normalized LIKE %s THEN 1.0
                        ELSE 1 - (skill_embedding <=> %s::vector)
                    END as relevance_score
                FROM skill_graph
                WHERE skill_embedding IS NOT NULL
                ORDER BY relevance_score DESC, popularity_score DESC
                LIMIT %s
                """,
                (embedding_str, f'%{query.lower()}%', embedding_str, limit)
            )
            
            return cursor.fetchall()
            
        finally:
            cursor.close()
            return_connection(conn)


# Singleton instance
_skill_normalization_service = None

def get_skill_normalization_service() -> SkillNormalizationService:
    """Get the global skill normalization service instance"""
    global _skill_normalization_service
    if _skill_normalization_service is None:
        _skill_normalization_service = SkillNormalizationService()
    return _skill_normalization_service