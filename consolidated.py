import numpy as np
import matplotlib.pyplot as plt

field_size = 200
delta_x = 82.021
viscosity_coefficient = 0.4

fuel_particle_surface_area_to_volume_ratio = 3500
ovendry_fuel_loading = 0.034
fuel_depth = 1
ovendry_particle_density = 32
fuel_particle_total_mineral_content = 0.0555
fuel_particle_low_heat_content = 8000
fuel_particle_moisture_content = 0.08
moisture_content_of_extinction = 0.12
fuel_particle_effective_mineral_content = 0.010
# wind_X_velo_at_midflame_height = 984.3
wind_X_velo_at_midflame_height = 20
wind_Y_velo_at_midflame_height = 0
wind_Z_velo_at_midflame_height = 0
wind_velo_magnitude_at_midflame_height = np.sqrt(wind_X_velo_at_midflame_height ** 2 + wind_Y_velo_at_midflame_height ** 2 + wind_Z_velo_at_midflame_height ** 2)
slope = 0

height_field = np.full((field_size, field_size), 0, dtype=float)
velo_x_field = np.full((field_size, field_size), 5, dtype=float)
velo_y_field = np.full((field_size, field_size), 0, dtype=float)

# φ < 0: burned; φ > 0: unburned; φ = 0: fire front (signed distance to square)
center = field_size // 2
half_side = 8
x0, x1 = center - half_side, center + half_side
y0, y1 = center - half_side, center + half_side

y, x = np.mgrid[0:field_size, 0:field_size]
dx_out = np.maximum(np.maximum(x0 - x, x - x1), 0)
dy_out = np.maximum(np.maximum(y0 - y, y - y1), 0)
outside = np.hypot(dx_out, dy_out)
inside = -np.minimum(np.minimum(x - x0, x1 - x), np.minimum(y - y0, y1 - y))
inside_region = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
level_set_field = np.where(inside_region, inside, outside).astype(float)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(level_set_field, cmap="RdBu_r", origin="lower")
ax.contour(level_set_field, levels=[0], colors="k", linewidths=1.5)
ax.set_title("Initial level set φ")
ax.set_xlabel("x (cell index)")
ax.set_ylabel("y (cell index)")
fig.colorbar(im, ax=ax, label="φ")
plt.show()

def calculate_gradient(field, dx):
    grad_field_y, grad_field_x = np.gradient(field, dx)
    return grad_field_x, grad_field_y

def calculate_divergence(field_x, field_y, dx):
    garbage, div_field_x = np.gradient(field_x, dx)
    div_field_y, garbage = np.gradient(field_y, dx)

    return div_field_x + div_field_y

def calculate_reaction_intensity():
    gamma_prime_max = (fuel_particle_surface_area_to_volume_ratio ** 1.5) / (495 + 0.0594 * fuel_particle_surface_area_to_volume_ratio ** 1.5)
    rho_b = ovendry_fuel_loading / fuel_depth
    beta = rho_b / ovendry_particle_density
    beta_op = 3.348 * fuel_particle_surface_area_to_volume_ratio ** -0.8189
    A = 1 / (4.774 * fuel_particle_surface_area_to_volume_ratio ** 0.1 - 7.27)
    gamma_prime = gamma_prime_max * (beta / beta_op) ** A * np.exp(A * (1 - beta / beta_op))

    W_n = ovendry_fuel_loading / (1 + fuel_particle_total_mineral_content)

    h = fuel_particle_low_heat_content

    n_M = 1 - 2.59 * (fuel_particle_moisture_content / moisture_content_of_extinction) + 5.11 * (fuel_particle_moisture_content / moisture_content_of_extinction) ** 2 - 3.52 * (fuel_particle_moisture_content / moisture_content_of_extinction) ** 3

    n_s = 0.174 * fuel_particle_effective_mineral_content ** -0.19

    return gamma_prime * W_n * h * n_M * n_s

def calculate_propagating_flux_ratio():
    rho_b = ovendry_fuel_loading / fuel_depth
    beta = rho_b / ovendry_particle_density

    return (192 + 0.2595 * fuel_particle_surface_area_to_volume_ratio) ** -1 * np.exp((0.792 + 0.681 * fuel_particle_surface_area_to_volume_ratio ** 0.5) * (beta + 0.1))

def calculate_wind_coefficient():
    C = 7.47 * np.exp(-0.133 * fuel_particle_surface_area_to_volume_ratio ** 0.55)

    B = 0.02526 * fuel_particle_surface_area_to_volume_ratio ** 0.54

    rho_b = ovendry_fuel_loading / fuel_depth
    beta = rho_b / ovendry_particle_density

    beta_op = 3.348 * fuel_particle_surface_area_to_volume_ratio ** -0.8189

    E = 0.715 * np.exp(-3.59 * 10e-4 * fuel_particle_surface_area_to_volume_ratio)

    return C * wind_velo_magnitude_at_midflame_height ** B * (beta / beta_op) ** -E

def calculate_slope_factor():
    rho_b = ovendry_fuel_loading / fuel_depth
    beta = rho_b / ovendry_particle_density

    return 5.275 * beta ** -0.3 * np.tan(slope) ** 2

def calculate_ovendry_bulk_density():
    return ovendry_fuel_loading / fuel_depth

def calculate_effective_heating_number():
    return np.exp(-138 / fuel_particle_surface_area_to_volume_ratio)

def calculate_heat_of_preignition():
    return 250 + 1116 * fuel_particle_moisture_content

def get_unit_vector(x, y):
    magnitude = np.sqrt(x ** 2 + y ** 2)
    safe = np.where(magnitude > 0, magnitude, 1.0)
    ux, uy = x / safe, y / safe
    return np.where(magnitude > 0, ux, 0.0), np.where(magnitude > 0, uy, 0.0)

def calculate_wind_coefficient_level_set(level_set_gradient_x, level_set_gradient_y, wind_x, wind_y):
    C = 7.47 * np.exp(-0.133 * fuel_particle_surface_area_to_volume_ratio ** 0.55)

    B = 0.02526 * fuel_particle_surface_area_to_volume_ratio ** 0.54

    rho_b = ovendry_fuel_loading / fuel_depth
    beta = rho_b / ovendry_particle_density

    beta_op = 3.348 * fuel_particle_surface_area_to_volume_ratio ** -0.8189

    E = 0.715 * np.exp(-3.59 * 10e-4 * fuel_particle_surface_area_to_volume_ratio)

    level_set_gradient_x, level_set_gradient_y = get_unit_vector(level_set_gradient_x, level_set_gradient_y)
    U = wind_x * level_set_gradient_x + wind_y * level_set_gradient_y

    U = np.where(U > 0, U, 0)

    return C * U ** B * (beta / beta_op) ** -E

def calculate_slope_factor_level_set(level_set_gradient_x, level_set_gradient_y, height_gradient_x, height_gradient_y):
    rho_b = ovendry_fuel_loading / fuel_depth
    beta = rho_b / ovendry_particle_density

    level_set_gradient_x, level_set_gradient_y = get_unit_vector(level_set_gradient_x, level_set_gradient_y)
    slope_along_normal = height_gradient_x * level_set_gradient_x + height_gradient_y * level_set_gradient_y

    return 5.275 * beta ** -0.3 * slope_along_normal ** 2

reaction_intensity = calculate_reaction_intensity()
propagating_flux_ratio = calculate_propagating_flux_ratio()
ovendry_bulk_density = calculate_ovendry_bulk_density()
effective_heating_number = calculate_effective_heating_number()
heat_of_preignition = calculate_heat_of_preignition()

def calculate_Rf_field(level_set_field, height_field, wind_x, wind_y):
    level_set_gradient_x, level_set_gradient_y = calculate_gradient(level_set_field, delta_x)
    wind_coefficient_level_set = calculate_wind_coefficient_level_set(level_set_gradient_x, level_set_gradient_y, wind_x, wind_y)

    height_gradient_x, height_gradient_y = calculate_gradient(height_field, delta_x)
    slope_factor_level_set = calculate_slope_factor_level_set(level_set_gradient_x, level_set_gradient_y, height_gradient_x, height_gradient_y)

    Rf_field = (reaction_intensity * propagating_flux_ratio * (1 + wind_coefficient_level_set + slope_factor_level_set)) / (ovendry_bulk_density * effective_heating_number * heat_of_preignition)

    return Rf_field

def calculate_new_level_set_field(level_set_field, Rf_field):
    level_set_gradient_x, level_set_gradient_y = calculate_gradient(level_set_field, delta_x)
    laplacian_level_set = calculate_divergence(level_set_gradient_x, level_set_gradient_y, delta_x)
    gradient_magnitude_level_set = np.sqrt(level_set_gradient_x ** 2 + level_set_gradient_y ** 2)
    
    level_set_field_delta = -1 * Rf_field * gradient_magnitude_level_set + viscosity_coefficient * delta_x * laplacian_level_set
    new_level_set_field = level_set_field + level_set_field_delta

    return new_level_set_field

level_set_time_series = []

for i in range(100):
    level_set_time_series.append(level_set_field)
    Rf_field = calculate_Rf_field(level_set_field, height_field, wind_X_velo_at_midflame_height, wind_Y_velo_at_midflame_height)
    level_set_field = calculate_new_level_set_field(level_set_field, Rf_field)

level_set_time_series = np.array(level_set_time_series)

from matplotlib.animation import FuncAnimation
from IPython.display import HTML

n_frames = len(level_set_time_series)
vmin, vmax = level_set_time_series.min(), level_set_time_series.max()

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(level_set_time_series[0], vmin=vmin, vmax=vmax, cmap="RdBu_r", origin="lower")
fire_front = [ax.contour(level_set_time_series[0], levels=[0], colors="k", linewidths=1)]
ax.set_title("Level set — step 0")
ax.set_xlabel("x")
ax.set_ylabel("y")
fig.colorbar(im, ax=ax, label="φ")

def update(frame):
    field = level_set_time_series[frame]
    im.set_array(field)
    ax.set_title(f"Level set — step {frame} / {n_frames - 1}")
    if fire_front[0] is not None:
        fire_front[0].remove()
    if field.min() <= 0 <= field.max():
        fire_front[0] = ax.contour(field, levels=[0], colors="k", linewidths=1)
    else:
        fire_front[0] = None
    return [im]

anim = FuncAnimation(fig, update, frames=n_frames, interval=80, blit=False)
plt.close(fig)
HTML(anim.to_jshtml())