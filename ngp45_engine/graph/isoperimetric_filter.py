import numpy as np


class IsoperimetricPruner:
    """
    ISO-RAG: Isoperimetric pruning via Jaccard curvature on the Poincare disk model.
    Edges with Jaccard(u,v) < threshold are removed as trans-cluster noise.
    """

    def __init__(self, curvature_threshold: float = 0.2):
        self.threshold = curvature_threshold

    def prune_graph(self, adj_matrix: np.ndarray) -> np.ndarray:
        n = adj_matrix.shape[0]
        pruned = adj_matrix.copy().astype(float)
        degrees = np.sum(adj_matrix, axis=1)

        for i in range(n):
            for j in range(i + 1, n):
                if adj_matrix[i, j] > 0:
                    common = np.sum(np.logical_and(adj_matrix[i] > 0, adj_matrix[j] > 0))
                    union = degrees[i] + degrees[j] - common
                    jaccard = common / union if union > 0 else 0.0
                    if jaccard < self.threshold:
                        pruned[i, j] = 0.0
                        pruned[j, i] = 0.0
        return pruned

    @staticmethod
    def poincare_distance(u: np.ndarray, v: np.ndarray, eps: float = 1e-6) -> float:
        """
        Hyperbolic geodesic distance in the Poincare unit disk model:
            d_H(u, v) = arccosh(1 + 2 * ||u-v||^2 / ((1 - ||u||^2)(1 - ||v||^2)))

        Inputs are clamped to |x| < 1 - eps to avoid singularity at the boundary.
        """
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)
        # Clamp to stay strictly inside the unit disk
        if norm_u >= 1.0:
            u = u / norm_u * (1.0 - eps)
            norm_u = 1.0 - eps
        if norm_v >= 1.0:
            v = v / norm_v * (1.0 - eps)
            norm_v = 1.0 - eps

        num = 2.0 * np.sum((u - v) ** 2)
        denom = (1.0 - norm_u ** 2) * (1.0 - norm_v ** 2)
        arg = 1.0 + num / max(denom, eps)
        return float(np.arccosh(max(1.0, arg)))

    @staticmethod
    def clustering_coefficient(adj_matrix: np.ndarray) -> float:
        n = adj_matrix.shape[0]
        total_cc = 0.0
        valid_nodes = 0

        for i in range(n):
            neighbors = np.where(adj_matrix[i] > 0)[0]
            k = len(neighbors)
            if k < 2:
                continue
            subgraph = adj_matrix[np.ix_(neighbors, neighbors)]
            links = np.sum(subgraph > 0) / 2.0
            total_cc += (2.0 * links) / (k * (k - 1))
            valid_nodes += 1

        return total_cc / valid_nodes if valid_nodes > 0 else 0.0
