import numpy as np


class TryptophanNetworkSim:
    """
    Non-Hermitian effective Hamiltonian for UV bio-photon transport (280/350 nm)
    in tryptophan protein networks.

    H_eff = H_0 - iW
      H_0: Hermitian site-energy + dipole-dipole coupling matrix
      W:   uniform decay matrix (gamma_0 per site)

    Superradiance condition: exists eigenvalue λ s.t. Im(λ) > gamma_0
    Superradiance ratio:     SR = max(-Im(λ)) / gamma_0   (>1 → superradiant)
    """

    def __init__(self, num_sites: int = 16, gamma_0: float = 0.00273):
        self.num_sites = num_sites
        self.gamma_0 = gamma_0

    def build_hamiltonian(self, disorder_sigma: float = 0.0) -> np.ndarray:
        np.random.seed(42)
        H0 = np.zeros((self.num_sites, self.num_sites), dtype=complex)

        # Site energies with optional static disorder
        site_energies = 4.43 + np.random.normal(0, disorder_sigma, self.num_sites)
        np.fill_diagonal(H0, site_energies)

        # Dipole-dipole coupling: J_ij = 0.015 / r_ij^3  [eV], r in nm
        for i in range(self.num_sites):
            for j in range(i + 1, self.num_sites):
                r_ij = abs(i - j) * 0.8
                coupling = 0.015 / (r_ij ** 3)
                H0[i, j] = coupling
                H0[j, i] = coupling

        # Uniform non-Hermitian decay: W_ij = gamma_0 for all i,j
        W = np.ones((self.num_sites, self.num_sites), dtype=complex) * self.gamma_0
        return H0 - 1j * W

    def compute_superradiance(
        self, H_eff: np.ndarray
    ) -> tuple[float, int, float, float]:
        """
        Returns:
            max_imag:           max(-Im(λ)) across all eigenmodes  [eV]
            superradiant_count: number of modes with -Im(λ) > gamma_0
            norm_diff:          ||H_eff - H_eff†|| (non-Hermiticity measure)
            sr_ratio:           max_imag / gamma_0  (Dicke superradiance ratio)
        """
        eigvals = np.linalg.eigvals(H_eff)
        imag_parts = -np.imag(eigvals)

        max_imag = float(np.max(imag_parts))
        superradiant_count = int(np.sum(imag_parts > self.gamma_0 * 1.01))
        norm_diff = float(np.linalg.norm(H_eff - np.conj(H_eff.T)))
        sr_ratio = max_imag / self.gamma_0

        return max_imag, superradiant_count, norm_diff, sr_ratio

    def disorder_stability_sweep(
        self, sigmas: list[float] | None = None
    ) -> list[dict]:
        """
        Validates superradiance persistence across static disorder levels.
        Boundary condition: SR ratio > 1.0 for all sigma up to 0.15 eV.

        Returns list of dicts: {sigma, sr_ratio, superradiant_count, stable}
        """
        if sigmas is None:
            sigmas = [0.0, 0.03, 0.05, 0.08, 0.10, 0.12, 0.15]

        results = []
        for sigma in sigmas:
            H_eff = self.build_hamiltonian(disorder_sigma=sigma)
            max_imag, count, _, sr_ratio = self.compute_superradiance(H_eff)
            results.append({
                "sigma": sigma,
                "sr_ratio": sr_ratio,
                "superradiant_count": count,
                "stable": sr_ratio > 1.0,
            })
        return results
