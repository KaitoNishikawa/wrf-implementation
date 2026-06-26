"""
Physics-informed numerical Gaussian Process for wildfire-spread prediction.

This is the PREDICTOR.  It is a separate code path from
`simulator_groundtruth.py`: it shares no forward-stepping function with the
simulator, and it never reads the true initial field -- it sees only the 50
sampled observation values handed to `fit_initial_gp`.

Pipeline
--------
1.  Prior at t = 0 (general, no ignition-geometry prior):
        phi^0(x) ~ GP(  m_poly(x),  k_RBF(x, x') )
    realised as a Bayesian linear model with feature map
        Phi(x) = [ 1, u, v, u^2, v^2, uv ,  z_1(x), ..., z_M(x) ]
    where the polynomial block is a generic low-order trend (universal-kriging
    mean -- it does NOT encode the square / signed-distance ignition family) and
    z_j are random Fourier features approximating a stationary RBF kernel.

2.  Sparse conditioning: condition the weights on the 50 observation VALUES via
    exact Bayesian-linear-regression posterior  w ~ N(mu_w, Sigma_w).

3.  Numerical-GP time stepping (the Euler discretisation embedded in the GP):
    advance an ensemble of posterior draws of phi^0 through the embedded
    Rothermel level-set operator.  The ensemble carries the GP covariance to
    every evaluation time (Monte-Carlo push-forward of the joint Numerical-GP
    distribution through the operator -- no mean-only collapse).

Constants are taken from the simulator (it is the source of truth for physics);
the stepping code below is independently written.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Physics constants (values from simulation.ipynb; independently re-encoded)
# ---------------------------------------------------------------------------
FIELD_SIZE = 200
DELTA_X = 82.021
VISCOSITY_COEFFICIENT = 0.4

FUEL_SAV_RATIO = 3500
OVENDRY_FUEL_LOADING = 0.034
FUEL_DEPTH = 1
OVENDRY_PARTICLE_DENSITY = 32
FUEL_TOTAL_MINERAL_CONTENT = 0.0555
FUEL_LOW_HEAT_CONTENT = 8000
FUEL_MOISTURE_CONTENT = 0.08
MOISTURE_OF_EXTINCTION = 0.12
FUEL_EFFECTIVE_MINERAL_CONTENT = 0.010

WIND_X = 100
WIND_Y = 100


def _rothermel_scalars():
    """Spatially-constant Rothermel terms (independent re-encoding of cell 8)."""
    sav = FUEL_SAV_RATIO
    gamma_prime_max = (sav ** 1.5) / (495 + 0.0594 * sav ** 1.5)
    rho_b = OVENDRY_FUEL_LOADING / FUEL_DEPTH
    beta = rho_b / OVENDRY_PARTICLE_DENSITY
    beta_op = 3.348 * sav ** -0.8189
    A = 1 / (4.774 * sav ** 0.1 - 7.27)
    gamma_prime = gamma_prime_max * (beta / beta_op) ** A * np.exp(A * (1 - beta / beta_op))
    W_n = OVENDRY_FUEL_LOADING / (1 + FUEL_TOTAL_MINERAL_CONTENT)
    Mr = FUEL_MOISTURE_CONTENT / MOISTURE_OF_EXTINCTION
    n_M = 1 - 2.59 * Mr + 5.11 * Mr ** 2 - 3.52 * Mr ** 3
    n_s = 0.174 * FUEL_EFFECTIVE_MINERAL_CONTENT ** -0.19
    reaction_intensity = gamma_prime * W_n * FUEL_LOW_HEAT_CONTENT * n_M * n_s

    propagating_flux_ratio = (192 + 0.2595 * sav) ** -1 * np.exp(
        (0.792 + 0.681 * sav ** 0.5) * (beta + 0.1)
    )
    ovendry_bulk_density = rho_b
    effective_heating_number = np.exp(-138 / sav)
    heat_of_preignition = 250 + 1116 * FUEL_MOISTURE_CONTENT

    # Constant prefactor R such that R_f = R * (1 + wind_coeff)   (slope = 0).
    R_prefactor = (reaction_intensity * propagating_flux_ratio) / (
        ovendry_bulk_density * effective_heating_number * heat_of_preignition
    )

    # Wind-coefficient constants (cell 9).
    C = 7.47 * np.exp(-0.133 * sav ** 0.55)
    B = 0.02526 * sav ** 0.54
    E = 0.715 * np.exp(-3.59 * 10e-4 * sav)
    wind_beta_term = (beta / beta_op) ** -E
    return R_prefactor, C, B, wind_beta_term


_R_PREFACTOR, _WIND_C, _WIND_B, _WIND_BETA_TERM = _rothermel_scalars()


# ---------------------------------------------------------------------------
# Embedded numerical-GP operator (the predictor's forward stepper).
# Batched over a leading ensemble axis; gradients on the last two axes (y, x).
# Mathematically equivalent to the simulator's Rothermel level-set Euler step,
# but a deliberately separate implementation (no shared function).
# ---------------------------------------------------------------------------
def _grad_x(field):
    return np.gradient(field, DELTA_X, axis=-1)


def _grad_y(field):
    return np.gradient(field, DELTA_X, axis=-2)


def embedded_levelset_step(phi, wind_x=WIND_X, wind_y=WIND_Y):
    """One forward-Euler step of the embedded Rothermel level-set operator.

    phi : array (..., Y, X).   Returns phi^{n+1} of the same shape.
        phi^{n+1} = phi^n + [ -R_f |grad phi| + nu*dx*lap(phi) ]      (Delta t = 1)
    with R_f = R_prefactor * (1 + wind_coeff(normal . wind)).
    """
    gx = _grad_x(phi)
    gy = _grad_y(phi)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2)

    # Outward unit normal (phi increases toward unburned); 0 where gradient is 0.
    safe = np.where(grad_mag > 0, grad_mag, 1.0)
    nx = np.where(grad_mag > 0, gx / safe, 0.0)
    ny = np.where(grad_mag > 0, gy / safe, 0.0)

    U = wind_x * nx + wind_y * ny
    U = np.where(U >= 0, U, 0.0)                 # clamp: no fractional power of negatives
    wind_coeff = _WIND_C * U ** _WIND_B * _WIND_BETA_TERM
    Rf = _R_PREFACTOR * (1 + wind_coeff)

    # Laplacian = div(grad) using the same centered scheme as the gradient.
    lap = _grad_x(gx) + _grad_y(gy)

    delta = -Rf * grad_mag + VISCOSITY_COEFFICIENT * DELTA_X * lap
    return phi + delta


def rollout(initial_fields, n_steps, record_times):
    """Step an ensemble of initial fields with the embedded operator.

    initial_fields : (N, Y, X) ensemble of posterior draws of phi^0.
    Returns {t: ensemble (N, Y, X)} at the requested step indices.
    """
    record_times = set(record_times)
    phi = np.asarray(initial_fields, dtype=float).copy()
    out = {}
    for step in range(n_steps + 1):
        if step in record_times:
            out[step] = phi.copy()
        if step == n_steps:
            break
        phi = embedded_levelset_step(phi)
    return out


# ---------------------------------------------------------------------------
# GP prior / sparse inference (Bayesian linear model: poly trend + RBF RFF)
# ---------------------------------------------------------------------------
def _poly_features(coords):
    """Generic quadratic trend basis [1, u, v, u^2, v^2, uv].

    coords : (P, 2) array of (x, y) cell indices.  Normalised by the public
    domain half-width (100 cells) -- this is the grid centre, NOT the (unknown)
    fire location.  A quadratic bowl cannot represent the square ignition front;
    the front geometry is supplied entirely by the RBF residual conditioned on
    data.
    """
    u = (coords[:, 0] - 100.0) / 100.0
    v = (coords[:, 1] - 100.0) / 100.0
    return np.stack([np.ones_like(u), u, v, u ** 2, v ** 2, u * v], axis=1)


def _rff_features(coords, omega, b, sigma_f):
    """Random Fourier features approximating a stationary RBF kernel of the
    given signal std sigma_f.  coords : (P, 2);  omega : (M, 2);  b : (M,)."""
    M = omega.shape[0]
    proj = coords @ omega.T + b[None, :]          # (P, M)
    return np.sqrt(2.0 / M) * sigma_f * np.cos(proj)


def _rbf_log_marglik(coords, y, lengthscale, sigma_f, sigma_n):
    """Exact RBF-GP log marginal likelihood (for hyperparameter selection)."""
    d2 = np.sum((coords[:, None, :] - coords[None, :, :]) ** 2, axis=-1)
    K = sigma_f ** 2 * np.exp(-0.5 * d2 / lengthscale ** 2)
    K = K + sigma_n ** 2 * np.eye(len(y))
    L = np.linalg.cholesky(K)
    alpha = np.linalg.solve(L.T, np.linalg.solve(L, y))
    return (
        -0.5 * y @ alpha
        - np.sum(np.log(np.diag(L)))
        - 0.5 * len(y) * np.log(2 * np.pi)
    )


def select_lengthscale(coords, values, candidates, sigma_f, sigma_n):
    """Pick the RBF lengthscale (in cells) that maximises the exact-GP marginal
    likelihood of the residual after the quadratic trend.  Uses ONLY the 50
    observation values -- no ground-truth leakage."""
    P = _poly_features(coords)
    trend, *_ = np.linalg.lstsq(P, values, rcond=None)
    residual = values - P @ trend
    scores = {ell: _rbf_log_marglik(coords, residual, ell, sigma_f, sigma_n)
              for ell in candidates}
    best = max(scores, key=scores.get)
    return best, scores


class InitialFieldGP:
    """GP posterior over phi^0 inferred from the 50 sparse observation values."""

    def __init__(self, lengthscale, sigma_f, sigma_n, n_features=512,
                 poly_prior_std=1e3, seed=0):
        self.lengthscale = lengthscale
        self.sigma_f = sigma_f
        self.sigma_n = sigma_n
        self.M = n_features
        self.poly_prior_std = poly_prior_std
        rng = np.random.default_rng(seed)
        # RFF for an RBF kernel: omega ~ N(0, ell^-2 I), b ~ U[0, 2pi].
        self.omega = rng.normal(0.0, 1.0 / lengthscale, size=(n_features, 2))
        self.b = rng.uniform(0.0, 2 * np.pi, size=n_features)
        self._rng = rng

    def _features(self, coords):
        return np.concatenate(
            [_poly_features(coords), _rff_features(coords, self.omega, self.b, self.sigma_f)],
            axis=1,
        )

    def fit(self, coords, values):
        """Condition the weight posterior on the observations (coords, values)."""
        Phi = self._features(coords)                     # (P, 6 + M)
        n_poly = 6
        # Prior precision: near-flat on the polynomial trend, unit on RFF weights
        # (the RBF signal variance is folded into the features).
        prior_prec = np.ones(Phi.shape[1])
        prior_prec[:n_poly] = 1.0 / self.poly_prior_std ** 2
        A = (Phi.T @ Phi) / self.sigma_n ** 2 + np.diag(prior_prec)
        self._chol_A = np.linalg.cholesky(A)
        rhs = (Phi.T @ values) / self.sigma_n ** 2
        self.mu_w = np.linalg.solve(self._chol_A.T, np.linalg.solve(self._chol_A, rhs))
        self._fitted = True
        return self

    def _field_from_weights(self, grid_coords, W):
        """W : (n_w,) or (n_w, N).  Returns field(s) reshaped to the grid."""
        Phi = self._features(grid_coords)
        F = Phi @ W
        side = FIELD_SIZE
        if F.ndim == 1:
            return F.reshape(side, side)
        return F.T.reshape(-1, side, side)               # (N, Y, X)

    def posterior_mean_field(self, grid_coords):
        return self._field_from_weights(grid_coords, self.mu_w)

    def posterior_mean_only_weights(self):
        return self.mu_w

    def sample_initial_fields(self, grid_coords, n_samples):
        """Draw n_samples posterior fields phi^0.

        w_s = mu_w + R^{-T} eta,  eta ~ N(0, I),  with A = R R^T (Cov = A^{-1})."""
        n_w = self.mu_w.shape[0]
        eta = self._rng.standard_normal(size=(n_w, n_samples))
        W = self.mu_w[:, None] + np.linalg.solve(self._chol_A.T, eta)
        return self._field_from_weights(grid_coords, W)

    def trend_only_field(self, grid_coords):
        """Quadratic-trend-only reconstruction (RBF residual ablated)."""
        w = self.mu_w.copy()
        w[6:] = 0.0
        return self._field_from_weights(grid_coords, w)


def grid_coordinates():
    """(FIELD_SIZE^2, 2) array of (x, y) cell indices matching field[y, x]."""
    yy, xx = np.mgrid[0:FIELD_SIZE, 0:FIELD_SIZE]
    return np.stack([xx.ravel(), yy.ravel()], axis=1).astype(float)
