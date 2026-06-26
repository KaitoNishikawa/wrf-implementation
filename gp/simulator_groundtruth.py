"""
Ground-truth wildfire simulator.

This module is a FAITHFUL TRANSCRIPTION of the physics, constants, and Euler
stepper in `simulation.ipynb` (repo root, read-only).  It exists ONLY to produce
the ground-truth level-set time series against which the numerical-GP prediction
is compared.

It is a deliberately SEPARATE CODE PATH from the predictor in `numerical_gp.py`:
the two modules share no forward-stepping function.  The predictor never imports
the true initial condition built here (`initial_level_set_field`) -- it sees only
the 50 sampled observation values drawn by `run_trial.py`.  Constants are shared
(the simulator is the source of truth for physics/constants), but the stepping
code is distinct so the prediction-vs-ground-truth comparison can genuinely fail.

Transcribed from simulation.ipynb cells 1-5, 8-13.  Do not edit simulation.ipynb.
"""

import numpy as np

# ----------------------------------------------------------------------------
# Grid / numerics constants (simulation.ipynb cell 2)
# ----------------------------------------------------------------------------
FIELD_SIZE = 200
DELTA_X = 82.021                # ft  (= 25.0 m); see gp/UNITS.md
VISCOSITY_COEFFICIENT = 0.4     # dimensionless (Mandel et al. value used by WRF paper)

# ----------------------------------------------------------------------------
# Rothermel fuel parameters (simulation.ipynb cell 3)
# ----------------------------------------------------------------------------
FUEL_SAV_RATIO = 3500           # fuel particle surface-area-to-volume ratio
OVENDRY_FUEL_LOADING = 0.034
FUEL_DEPTH = 1
OVENDRY_PARTICLE_DENSITY = 32
FUEL_TOTAL_MINERAL_CONTENT = 0.0555
FUEL_LOW_HEAT_CONTENT = 8000
FUEL_MOISTURE_CONTENT = 0.08
MOISTURE_OF_EXTINCTION = 0.12
FUEL_EFFECTIVE_MINERAL_CONTENT = 0.010

WIND_X = 100                    # ft/min midflame wind (cell 3, active value)
WIND_Y = 100                    # ft/min
WIND_Z = 0
WIND_MAG = np.sqrt(WIND_X ** 2 + WIND_Y ** 2 + WIND_Z ** 2)
SLOPE = 0

# Height field is zeroed in cell 7, so the slope factor vanishes.
HEIGHT_FIELD = np.zeros((FIELD_SIZE, FIELD_SIZE), dtype=float)


# ----------------------------------------------------------------------------
# Differential operators (simulation.ipynb cell 1)
# ----------------------------------------------------------------------------
def calculate_gradient(field, dx):
    grad_field_y, grad_field_x = np.gradient(field, dx)
    return grad_field_x, grad_field_y


def calculate_divergence(field_x, field_y, dx):
    _, div_field_x = np.gradient(field_x, dx)
    div_field_y, _ = np.gradient(field_y, dx)
    return div_field_x + div_field_y


# ----------------------------------------------------------------------------
# Rothermel scalar terms (simulation.ipynb cell 8)
# ----------------------------------------------------------------------------
def calculate_reaction_intensity():
    gamma_prime_max = (FUEL_SAV_RATIO ** 1.5) / (495 + 0.0594 * FUEL_SAV_RATIO ** 1.5)
    rho_b = OVENDRY_FUEL_LOADING / FUEL_DEPTH
    beta = rho_b / OVENDRY_PARTICLE_DENSITY
    beta_op = 3.348 * FUEL_SAV_RATIO ** -0.8189
    A = 1 / (4.774 * FUEL_SAV_RATIO ** 0.1 - 7.27)
    gamma_prime = gamma_prime_max * (beta / beta_op) ** A * np.exp(A * (1 - beta / beta_op))
    W_n = OVENDRY_FUEL_LOADING / (1 + FUEL_TOTAL_MINERAL_CONTENT)
    h = FUEL_LOW_HEAT_CONTENT
    M = FUEL_MOISTURE_CONTENT / MOISTURE_OF_EXTINCTION
    n_M = 1 - 2.59 * M + 5.11 * M ** 2 - 3.52 * M ** 3
    n_s = 0.174 * FUEL_EFFECTIVE_MINERAL_CONTENT ** -0.19
    return gamma_prime * W_n * h * n_M * n_s


def calculate_propagating_flux_ratio():
    rho_b = OVENDRY_FUEL_LOADING / FUEL_DEPTH
    beta = rho_b / OVENDRY_PARTICLE_DENSITY
    return (192 + 0.2595 * FUEL_SAV_RATIO) ** -1 * np.exp(
        (0.792 + 0.681 * FUEL_SAV_RATIO ** 0.5) * (beta + 0.1)
    )


def calculate_ovendry_bulk_density():
    return OVENDRY_FUEL_LOADING / FUEL_DEPTH


def calculate_effective_heating_number():
    return np.exp(-138 / FUEL_SAV_RATIO)


def calculate_heat_of_preignition():
    return 250 + 1116 * FUEL_MOISTURE_CONTENT


# ----------------------------------------------------------------------------
# Level-set-aware wind/slope coefficients (simulation.ipynb cell 9)
# ----------------------------------------------------------------------------
def get_unit_vector(x, y):
    magnitude = np.sqrt(x ** 2 + y ** 2)
    safe = np.where(magnitude > 0, magnitude, 1.0)
    ux, uy = x / safe, y / safe
    return np.where(magnitude > 0, ux, 0.0), np.where(magnitude > 0, uy, 0.0)


def calculate_wind_coefficient_level_set(grad_x, grad_y, wind_x, wind_y):
    C = 7.47 * np.exp(-0.133 * FUEL_SAV_RATIO ** 0.55)
    B = 0.02526 * FUEL_SAV_RATIO ** 0.54
    rho_b = OVENDRY_FUEL_LOADING / FUEL_DEPTH
    beta = rho_b / OVENDRY_PARTICLE_DENSITY
    beta_op = 3.348 * FUEL_SAV_RATIO ** -0.8189
    E = 0.715 * np.exp(-3.59 * 10e-4 * FUEL_SAV_RATIO)  # NOTE: simulator uses 10e-4 (=1e-3)

    nx, ny = get_unit_vector(grad_x, grad_y)
    U = wind_x * nx + wind_y * ny
    # Raising a negative number to a fractional power is undefined; clamp to 0.
    U = np.where(U >= 0, U, 0)
    return C * U ** B * (beta / beta_op) ** -E


def calculate_slope_factor_level_set(grad_x, grad_y, height_grad_x, height_grad_y):
    rho_b = OVENDRY_FUEL_LOADING / FUEL_DEPTH
    beta = rho_b / OVENDRY_PARTICLE_DENSITY
    nx, ny = get_unit_vector(grad_x, grad_y)
    slope_along_normal = height_grad_x * nx + height_grad_y * ny
    return 5.275 * beta ** -0.3 * slope_along_normal ** 2


# Precompute the scalar Rothermel terms once (they are constant in space/time).
REACTION_INTENSITY = calculate_reaction_intensity()
PROPAGATING_FLUX_RATIO = calculate_propagating_flux_ratio()
OVENDRY_BULK_DENSITY = calculate_ovendry_bulk_density()
EFFECTIVE_HEATING_NUMBER = calculate_effective_heating_number()
HEAT_OF_PREIGNITION = calculate_heat_of_preignition()


# ----------------------------------------------------------------------------
# Rate-of-spread field and Euler stepper (simulation.ipynb cell 12)
# ----------------------------------------------------------------------------
def calculate_Rf_field(level_set_field, height_field, wind_x, wind_y):
    grad_x, grad_y = calculate_gradient(level_set_field, DELTA_X)
    wind_coeff = calculate_wind_coefficient_level_set(grad_x, grad_y, wind_x, wind_y)
    hgx, hgy = calculate_gradient(height_field, DELTA_X)
    slope_factor = calculate_slope_factor_level_set(grad_x, grad_y, hgx, hgy)
    Rf_field = (
        REACTION_INTENSITY * PROPAGATING_FLUX_RATIO * (1 + wind_coeff + slope_factor)
    ) / (OVENDRY_BULK_DENSITY * EFFECTIVE_HEATING_NUMBER * HEAT_OF_PREIGNITION)
    return Rf_field


def calculate_new_level_set_field(level_set_field, Rf_field):
    grad_x, grad_y = calculate_gradient(level_set_field, DELTA_X)
    laplacian = calculate_divergence(grad_x, grad_y, DELTA_X)
    grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
    delta = -1 * Rf_field * grad_mag + VISCOSITY_COEFFICIENT * DELTA_X * laplacian
    return level_set_field + delta


def ground_truth_step(level_set_field):
    """One forward Euler step of the ground-truth simulator (Delta t = 1 min)."""
    Rf_field = calculate_Rf_field(level_set_field, HEIGHT_FIELD, WIND_X, WIND_Y)
    return calculate_new_level_set_field(level_set_field, Rf_field)


# ----------------------------------------------------------------------------
# True initial condition (simulation.ipynb cell 5)
#
# Built ONLY to (a) generate ground truth and (b) be the sampling source for the
# 50 observation VALUES.  The predictor never imports this function.
# ----------------------------------------------------------------------------
def initial_level_set_field():
    """Signed-distance level set to the square ignition (phi<0 burned, phi>0 unburned)."""
    center = FIELD_SIZE // 2
    half_side = 8
    x0, x1 = center - half_side, center + half_side
    y0, y1 = center - half_side, center + half_side

    y, x = np.mgrid[0:FIELD_SIZE, 0:FIELD_SIZE]
    dx_out = np.maximum(np.maximum(x0 - x, x - x1), 0)
    dy_out = np.maximum(np.maximum(y0 - y, y - y1), 0)
    outside = np.hypot(dx_out, dy_out)
    inside = -np.minimum(np.minimum(x - x0, x1 - x), np.minimum(y - y0, y1 - y))
    inside_region = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    return np.where(inside_region, inside, outside).astype(float)


def generate_ground_truth(n_steps=300, record_times=None):
    """Run the simulator and return {t: field} at the requested step indices.

    record_times defaults to {0, 50, 100, 150, 200, 250, 300}.
    """
    if record_times is None:
        record_times = [0, 50, 100, 150, 200, 250, 300]
    record_times = set(record_times)

    field = initial_level_set_field()
    series = {}
    for step in range(n_steps + 1):
        if step in record_times:
            series[step] = field.copy()
        if step == n_steps:
            break
        field = ground_truth_step(field)
    return series


if __name__ == "__main__":
    # Fidelity check: the scalar no-wind / full-wind rates must match gp/UNITS.md
    # (R_0 ~ 3.8 ft/min, R_f ~ 9.68 ft/min on the fully downwind side).
    R_0 = (REACTION_INTENSITY * PROPAGATING_FLUX_RATIO) / (
        OVENDRY_BULK_DENSITY * EFFECTIVE_HEATING_NUMBER * HEAT_OF_PREIGNITION
    )
    # Full-wind scalar coefficient (wind exactly along the normal, |U| = WIND_MAG).
    C = 7.47 * np.exp(-0.133 * FUEL_SAV_RATIO ** 0.55)
    B = 0.02526 * FUEL_SAV_RATIO ** 0.54
    rho_b = OVENDRY_FUEL_LOADING / FUEL_DEPTH
    beta = rho_b / OVENDRY_PARTICLE_DENSITY
    beta_op = 3.348 * FUEL_SAV_RATIO ** -0.8189
    E = 0.715 * np.exp(-3.59 * 10e-4 * FUEL_SAV_RATIO)
    wind_coeff_full = C * WIND_MAG ** B * (beta / beta_op) ** -E
    R_f_full = R_0 * (1 + wind_coeff_full)
    print(f"R_0 (no wind)      = {R_0:.4f} ft/min  (expect ~3.8)")
    print(f"R_f (full wind)    = {R_f_full:.4f} ft/min  (expect ~9.68)")

    series = generate_ground_truth()
    for t in sorted(series):
        f = series[t]
        burned = int((f < 0).sum())
        print(f"t={t:3d}  phi range [{f.min():8.2f}, {f.max():8.2f}]  burned cells={burned}")
