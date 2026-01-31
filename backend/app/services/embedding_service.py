"""
Skill Embedding Service
Converts skill text to 384-dimensional vectors using sentence-transformers
Enables semantic similarity matching
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple
import time

class SkillEmbeddingService:
    """
    Service for generating and comparing skill embeddings
    Uses pre-trained 'all-MiniLM-L6-v2' model (66MB, fast inference)
    """
    
    def __init__(self):
        """
        Initialize the embedding model
        This downloads the model on first run (~66MB)
        Subsequent runs load from cache
        """
        print("Loading sentence-transformer model...")
        start_time = time.time()
        
        # Load pre-trained model
        # all-MiniLM-L6-v2: 384 dimensions, fast, good quality
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        load_time = time.time() - start_time
        print(f"✓ Model loaded in {load_time:.2f} seconds")
        
    def normalize_skill_name(self, skill_name: str) -> str:
        """
        Normalize skill text for consistent embeddings
        
        Examples:
            "Python Programming" -> "python programming"
            "  GUITAR  " -> "guitar"
        
        Args:
            skill_name: Raw skill text
            
        Returns:
            Normalized skill text
        """
        if not skill_name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = skill_name.lower().strip()
        
        # Remove extra spaces between words
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def generate_embedding(self, skill_name: str) -> List[float]:
        """
        Generate 384-dimensional embedding vector for a skill
        
        This is the CORE AI FUNCTION - converts text to numbers
        
        Args:
            skill_name: Skill text (e.g., "Python Programming")
            
        Returns:
            List of 384 floats representing the skill semantically
            
        Example:
            >>> service = SkillEmbeddingService()
            >>> embedding = service.generate_embedding("Python Programming")
            >>> len(embedding)
            384
            >>> embedding[:3]
            [0.123, -0.456, 0.789]
        """
        # Normalize input
        normalized = self.normalize_skill_name(skill_name)
        
        if not normalized:
            raise ValueError("Skill name cannot be empty")
        
        # Generate embedding using transformer model
        # This runs the neural network to encode meaning
        embedding = self.model.encode(normalized)
        
        # Convert numpy array to Python list for JSON serialization
        return embedding.tolist()
    
    def generate_embeddings_batch(self, skill_names: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple skills at once
        More efficient than calling generate_embedding() in a loop
        
        Args:
            skill_names: List of skill texts
            
        Returns:
            List of embedding vectors
        """
        # Normalize all skills
        normalized = [self.normalize_skill_name(name) for name in skill_names]
        
        # Batch encoding is faster than one-by-one
        embeddings = self.model.encode(normalized)
        
        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]
    
    def calculate_similarity(self, skill1: str, skill2: str) -> float:
        """
        Calculate semantic similarity between two skills
        
        Uses cosine similarity: measures angle between vectors
        - 1.0 = identical meaning
        - 0.0 = completely unrelated
        - Higher = more similar
        
        Args:
            skill1: First skill name
            skill2: Second skill name
            
        Returns:
            Similarity score between 0.0 and 1.0
            
        Examples:
            >>> service.calculate_similarity("Python", "Python Programming")
            0.92  # Very similar
            
            >>> service.calculate_similarity("Guitar", "Music Theory")
            0.65  # Somewhat related
            
            >>> service.calculate_similarity("Guitar", "Cooking")
            0.23  # Not related
        """
        # Generate embeddings
        emb1 = self.model.encode(self.normalize_skill_name(skill1))
        emb2 = self.model.encode(self.normalize_skill_name(skill2))
        
        # Calculate cosine similarity
        # Formula: dot(A, B) / (||A|| * ||B||)
        similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        
        # Return as Python float (not numpy float)
        return float(similarity)
    
    def calculate_similarity_from_embeddings(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Calculate similarity when you already have embeddings
        Faster than calculate_similarity() since no encoding needed
        
        Args:
            embedding1: First skill's embedding vector
            embedding2: Second skill's embedding vector
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        
        return float(similarity)
    
    def find_most_similar(
        self, 
        query_skill: str, 
        candidate_skills: List[Dict[str, any]], 
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Find most similar skills from a list of candidates
        Useful for matching and autocomplete
        
        Args:
            query_skill: The skill to match against
            candidate_skills: List of dicts with 'name' and 'embedding' keys
            top_k: Number of top matches to return
            
        Returns:
            List of (skill_dict, similarity_score) tuples, sorted by similarity
            
        Example:
            >>> candidates = [
            ...     {"name": "Python", "embedding": [...]},
            ...     {"name": "JavaScript", "embedding": [...]},
            ...     {"name": "Guitar", "embedding": [...]}
            ... ]
            >>> results = service.find_most_similar("Python Programming", candidates, top_k=2)
            >>> for skill, score in results:
            ...     print(f"{skill['name']}: {score:.2f}")
            Python: 0.92
            JavaScript: 0.65
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query_skill)
        
        # Calculate similarity with each candidate
        similarities = []
        for candidate in candidate_skills:
            if 'embedding' not in candidate or candidate['embedding'] is None:
                continue  # Skip if no embedding
                
            similarity = self.calculate_similarity_from_embeddings(
                query_embedding,
                candidate['embedding']
            )
            
            similarities.append((candidate, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K
        return similarities[:top_k]


# Singleton instance (load model once, reuse everywhere)
_embedding_service = None

def get_embedding_service() -> SkillEmbeddingService:
    """
    Get the global embedding service instance
    Loads model only once for efficiency
    
    Usage:
        service = get_embedding_service()
        embedding = service.generate_embedding("Python")
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = SkillEmbeddingService()
    return _embedding_service