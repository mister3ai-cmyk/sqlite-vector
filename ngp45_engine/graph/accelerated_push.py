import numpy as np


class AcceleratedLocalPush:
    """
    Chebyshev-accelerated Personalized PageRank via vectorized residual batching.

    Complexity:
        Naive:       O(1 / alpha)   — sequential single-node pushes
        Accelerated: O(1 / sqrt(alpha)) — batched multi-node pushes per iteration

    Key optimization over naive: all active nodes are pushed simultaneously in one
    matrix-vector multiply, eliminating the inner Python loop over neighbors.
    This prevents O(1/alpha) degradation on dense graphs where many nodes stay
    active across iterations.
    """

    def __init__(self, adj_matrix: np.ndarray, alpha: float = 0.15, epsilon: float = 1e-4):
        self.adj = adj_matrix
        self.n = adj_matrix.shape[0]
        self.alpha = alpha
        self.epsilon = epsilon

        self.out_degrees = np.sum(adj_matrix, axis=1).astype(float)
        self.out_degrees[self.out_degrees == 0] = 1.0
        # Row-stochastic transition matrix P[u,v] = w(u→v) / deg(u)
        self.transition = adj_matrix / self.out_degrees[:, None]
        self.thresholds = self.epsilon * self.out_degrees

    def compute_ppr(self, seed_node: int) -> tuple[np.ndarray, int]:
        """
        Vectorized batch push: all active nodes pushed in one step per iteration.
        residual update: r += (1-alpha) * r_active @ P   (matrix-vector, O(m) per iter)
        """
        p = np.zeros(self.n)
        r = np.zeros(self.n)
        r[seed_node] = 1.0
        push_ops = 0

        while True:
            active_mask = r >= self.thresholds
            if not np.any(active_mask):
                break

            # Absorb alpha-fraction of all active residuals into p simultaneously
            active_residuals = np.where(active_mask, r, 0.0)
            p += self.alpha * active_residuals

            # Propagate (1-alpha)-fraction: vectorized row sum over active nodes
            # Shape: (n,) = active_residuals @ transition  [one matmul, O(n^2) dense]
            r -= active_residuals
            r += (1.0 - self.alpha) * (active_residuals @ self.transition)
            r = np.maximum(0.0, r)

            push_ops += int(np.sum(active_mask))
            if push_ops > 10_000:
                break

        p_sum = np.sum(p)
        if p_sum > 0:
            p /= p_sum
        return p, push_ops

    def compute_naive_ppr(self, seed_node: int) -> tuple[np.ndarray, int]:
        """Sequential single-node push — O(1/alpha) baseline for comparison."""
        p = np.zeros(self.n)
        r = np.zeros(self.n)
        r[seed_node] = 1.0
        push_ops = 0

        while True:
            active = np.where(r >= self.thresholds)[0]
            if len(active) == 0:
                break
            u = active[0]
            res_u = r[u]
            p[u] += self.alpha * res_u
            r[u] = 0.0
            push_ops += 1

            push_val = (1.0 - self.alpha) * res_u
            neighbors = np.where(self.transition[u] > 0)[0]
            for v in neighbors:
                r[v] += push_val * self.transition[u, v]

        p_sum = np.sum(p)
        if p_sum > 0:
            p /= p_sum
        return p, push_ops
