"""
rag_engine.py
-----------
TF-IDF based duplicate detection for user's email batch only.
NOT for cross-comparison with base dataset — only within user's submitted emails.

Tries to use sklearn for efficiency, falls back to pure Python cosine similarity.
"""

from typing import List, Tuple, Set, Dict, Any
from collections import Counter
import math


class RAGEngine:
    """
    Builds a TF-IDF index over user's opportunity emails to detect near-duplicates.
    Useful for filtering out forwarded/resent versions of the same opportunity.
    """
    
    def __init__(self):
        """Initialize empty RAG engine. Index is built fresh for each user batch."""
        self.vectorizer = None
        self.matrix = None
        self.emails = []
        self.use_sklearn = False
        self.tfidf_vectors = []
        self.vocab = {}
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on whitespace/punctuation, filter stops."""
        import re
        stops = {'the', 'a', 'an', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been', 
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                 'should', 'may', 'might', 'must', 'can', 'in', 'of', 'to', 'for', 'from', 'at', 'by'}
        
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return [t for t in tokens if t not in stops and len(t) > 2]
    
    def _compute_tfidf(self, docs: List[str]) -> Tuple[List[Dict[str, float]], Dict[str, int]]:
        """
        Compute TF-IDF vectors for documents (pure Python, no sklearn).
        Returns (vectors, vocab)
        """
        # Build vocabulary and document term frequencies
        all_tokens = []
        doc_tokens = []
        
        for doc in docs:
            tokens = self._simple_tokenize(doc)
            doc_tokens.append(tokens)
            all_tokens.extend(tokens)
        
        # Build vocab (map term -> id)
        vocab = {term: idx for idx, term in enumerate(sorted(set(all_tokens)))}
        n_docs = len(docs)
        
        # Compute IDF for each term
        idf = {}
        for term in vocab:
            doc_count = sum(1 for tokens in doc_tokens if term in tokens)
            idf[term] = math.log(n_docs / (1 + doc_count))
        
        # Compute TF-IDF vectors
        vectors = []
        for tokens in doc_tokens:
            vec = {}
            tf = Counter(tokens)
            doc_len = len(tokens)
            
            for term in vocab:
                if term in tf:
                    tf_val = tf[term] / max(doc_len, 1)
                    vec[term] = tf_val * idf[term]
            
            vectors.append(vec)
        
        return vectors, vocab
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Compute cosine similarity between two TF-IDF vectors."""
        # Dot product
        dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in set(vec1) | set(vec2))
        
        # Magnitude
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def build_index(self, emails: List[Dict[str, Any]]) -> None:
        """
        Build a TF-IDF index over the user's opportunity emails.
        Uses sklearn if available, falls back to pure Python implementation.
        
        Args:
            emails: List of email dicts with 'subject', 'body', etc.
                   (should be only "opportunity" labeled emails)
        """
        self.emails = emails
        
        if len(emails) < 2:
            # Nothing to compare against
            return
        
        # Create documents: subject + first 500 chars of body
        docs = [
            f"{e.get('subject', '')} {e.get('body', '')[:500]}"
            for e in emails
        ]
        
        # Try to use sklearn first
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=300,
                min_df=1,
                max_df=0.95
            )
            self.matrix = self.vectorizer.fit_transform(docs)
            self.use_sklearn = True
        except ImportError:
            # Fall back to pure Python TF-IDF
            self.tfidf_vectors, self.vocab = self._compute_tfidf(docs)
            self.use_sklearn = False
    
    def find_duplicates(self, threshold: float = 0.70) -> List[Tuple[int, int, float]]:
        """
        Find email pairs with high similarity within the user's batch.
        
        Args:
            threshold: Cosine similarity threshold (0.0-1.0). 
                      Default 0.70 means 70% similar.
        
        Returns:
            List of (idx_a, idx_b, similarity_score) tuples where idx_a < idx_b
            and similarity_score >= threshold.
        """
        if not self.emails or len(self.emails) < 2:
            return []
        
        duplicates = []
        n = len(self.emails)
        
        if self.use_sklearn:
            # Use sklearn cosine similarity
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                sim_matrix = cosine_similarity(self.matrix)
                
                for i in range(n):
                    for j in range(i + 1, n):
                        score = float(sim_matrix[i][j])
                        if score >= threshold:
                            duplicates.append((i, j, round(score, 3)))
            except Exception:
                # Fall back to pure Python
                for i in range(n):
                    for j in range(i + 1, n):
                        score = self._cosine_similarity(self.tfidf_vectors[i], self.tfidf_vectors[j])
                        if score >= threshold:
                            duplicates.append((i, j, round(score, 3)))
        else:
            # Use pure Python cosine similarity
            for i in range(n):
                for j in range(i + 1, n):
                    score = self._cosine_similarity(self.tfidf_vectors[i], self.tfidf_vectors[j])
                    if score >= threshold:
                        duplicates.append((i, j, round(score, 3)))
        
        return duplicates
    
    def get_duplicate_ids(self, threshold: float = 0.70) -> Set[int]:
        """
        Get indices of emails that are duplicates within the batch.
        Keeps the first occurrence, marks later ones as duplicates.
        
        Args:
            threshold: Cosine similarity threshold.
        
        Returns:
            Set of email indices (within the batch) that are duplicates.
        """
        pairs = self.find_duplicates(threshold)
        duplicate_indices = set()
        
        for i, j, score in pairs:
            # Keep lower index (first occurrence), mark higher as duplicate
            duplicate_indices.add(j)
        
        return duplicate_indices
    
    def get_duplicate_groups(self, threshold: float = 0.70) -> List[List[int]]:
        """
        Get groups of duplicate emails (for UI display).
        
        Args:
            threshold: Cosine similarity threshold.
        
        Returns:
            List of lists, where each inner list is a group of duplicate indices.
        """
        pairs = self.find_duplicates(threshold)
        
        # Build connected components
        groups = []
        assigned = set()
        
        for i, j, score in pairs:
            if i not in assigned and j not in assigned:
                groups.append([i, j])
                assigned.add(i)
                assigned.add(j)
            elif i in assigned:
                for group in groups:
                    if i in group:
                        if j not in group:
                            group.append(j)
                        assigned.add(j)
                        break
            elif j in assigned:
                for group in groups:
                    if j in group:
                        if i not in group:
                            group.append(i)
                        assigned.add(i)
                        break
        
        return groups
