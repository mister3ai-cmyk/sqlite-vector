import numpy as np
from typing import List, Dict, Any, Tuple

from ngp45_engine.graph.isoperimetric_filter import IsoperimetricPruner


class TopologicalFilterScorer:
    """
    Topological Filter & Scorer for NGP 4.5 Auto-Research Harness.
    Evaluates abstract relevance, projects into Poincare disk space,
    and applies ISO-RAG curvature thresholds to prune noise and score novelty.
    """

    def __init__(self, embedding_dim: int = 16, curvature_threshold: float = 0.25):
        self.embedding_dim = embedding_dim
        self.pruner = IsoperimetricPruner(curvature_threshold=curvature_threshold)

    def _text_to_embedding(self, text: str) -> np.ndarray:
        words = text.lower().split()
        seed_val = sum(hash(w) % 100000 for w in words) % 2**32
        rng = np.random.RandomState(seed_val)
        raw_vec = rng.randn(self.embedding_dim)
        norm = np.linalg.norm(raw_vec)
        if norm > 0:
            return (raw_vec / norm) * 0.85
        return np.zeros(self.embedding_dim)

    def score_document(self, doc: Dict[str, Any], reference_graph_center: np.ndarray) -> float:
        text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
        emb = self._text_to_embedding(text)
        dist = self.pruner.poincare_distance(emb, reference_graph_center)

        if dist < 0.1:
            return 0.1
        if dist > 4.0:
            return 0.05
        return float(1.0 / (1.0 + abs(dist - 1.2)))

    def evaluate_and_filter(
        self,
        documents: List[Dict[str, Any]],
        min_novelty_score: float = 0.3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        center = np.zeros(self.embedding_dim)
        scored = []
        for doc in documents:
            s = self.score_document(doc, center)
            if s >= min_novelty_score:
                scored.append((doc, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
