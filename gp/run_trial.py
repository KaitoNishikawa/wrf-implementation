"""
Trial 001 driver: physics-informed numerical-GP wildfire-spread prediction.

Pipeline
--------
* Ground truth  : simulator_groundtruth.generate_ground_truth() (simulator path)
* Observations  : 50 cells from the central 100x100 window, fixed seed
* Inference     : numerical_gp.InitialFieldGP  (50 values only)
* Prediction    : ensemble of posterior phi^0 draws stepped by the embedded
                  numerical-GP operator (numerical_gp.rollout) -- NOT the simulator
* Evaluation    : field RMSE + fire-front contour distance at t = 50..300,
                  variance + ablation load-bearing diagnostics, leakage self-check

All outputs are written under gp/results/trial_001/.
"""

import os
import sys
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simulator_groundtruth as sim
import numerical_gp as ngp

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 42
N_OBS = 50
OBS_LO, OBS_HI = 50, 150            # central 100x100 window (inclusive lo, exclusive hi)
N_STEPS = 300
EVAL_TIMES = [50, 100, 150, 200, 250, 300]
RECORD_TIMES = [0] + EVAL_TIMES
N_ENSEMBLE = 128
N_FEATURES = 512
SIGMA_N = 0.1                       # obs jitter (phi units); observations are near-exact
LENGTHSCALE_CANDIDATES = [8, 10, 12, 14, 16, 18, 20, 24]
DELTA_X = sim.DELTA_X               # ft per cell
FT_PER_M = 1.0 / 0.3048

OUTDIR = os.path.join(HERE, "results", "trial_001")
os.makedirs(OUTDIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# Metric helpers
# --------------------------------------------------------------------------- #
def rmse(a, b, mask=None):
    if mask is None:
        return float(np.sqrt(np.mean((a - b) ** 2)))
    return float(np.sqrt(np.mean((a[mask] - b[mask]) ** 2)))


def mae(a, b, mask=None):
    if mask is None:
        return float(np.mean(np.abs(a - b)))
    return float(np.mean(np.abs(a[mask] - b[mask])))


def front_points(field):
    """Zero-level-set vertices (x=col, y=row cell coords) via matplotlib contour."""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cs = ax.contour(field, levels=[0])
    segs = cs.allsegs[0] if cs.allsegs else []
    plt.close(fig)
    if not segs:
        return np.empty((0, 2))
    return np.vstack(segs)


def _directed_distances(A, B):
    """For each point in A, distance to nearest point in B (cell units)."""
    d = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1))
    return d.min(axis=1)


def front_distance(pred_field, gt_field):
    """Symmetric mean and Hausdorff fire-front distance (in cells).

    Returns (nan, nan) if either field has no zero-level-set contour (e.g. the
    ablation IC, which has no fire front at all)."""
    P = front_points(pred_field)
    G = front_points(gt_field)
    if len(P) == 0 or len(G) == 0:
        return float("nan"), float("nan")
    dPG = _directed_distances(P, G)
    dGP = _directed_distances(G, P)
    mean_sym = 0.5 * (dPG.mean() + dGP.mean())
    hausdorff = max(dPG.max(), dGP.max())
    return float(mean_sym), float(hausdorff)


# --------------------------------------------------------------------------- #
# 1. Ground truth (simulator code path)
# --------------------------------------------------------------------------- #
print("[1] Generating ground truth from simulator ...")
gt = sim.generate_ground_truth(n_steps=N_STEPS, record_times=RECORD_TIMES)
phi0_true = gt[0]

# --------------------------------------------------------------------------- #
# 2. Sample 50 observations from the central window (fixed seed)
# --------------------------------------------------------------------------- #
print("[2] Sampling 50 observations (seed=%d, window [%d,%d)) ..." % (SEED, OBS_LO, OBS_HI))
rng = np.random.default_rng(SEED)
xs = rng.integers(OBS_LO, OBS_HI, size=N_OBS)
ys = rng.integers(OBS_LO, OBS_HI, size=N_OBS)
obs_coords = np.stack([xs, ys], axis=1).astype(float)     # (x, y)
obs_values = phi0_true[ys, xs].astype(float)              # the ONLY ground-truth info the GP sees

# --------------------------------------------------------------------------- #
# 3. Hyperparameters + GP inference of phi^0 from the 50 values
# --------------------------------------------------------------------------- #
print("[3] Selecting lengthscale and conditioning the GP ...")
sigma_f = float(np.std(obs_values))
best_ell, ell_scores = ngp.select_lengthscale(
    obs_coords, obs_values, LENGTHSCALE_CANDIDATES, sigma_f=sigma_f, sigma_n=SIGMA_N
)
print("    sigma_f=%.3f  chosen lengthscale=%d cells" % (sigma_f, best_ell))

gp = ngp.InitialFieldGP(lengthscale=best_ell, sigma_f=sigma_f, sigma_n=SIGMA_N,
                        n_features=N_FEATURES, seed=SEED)
gp.fit(obs_coords, obs_values)

grid = ngp.grid_coordinates()
m0 = gp.posterior_mean_field(grid)
ens0 = gp.sample_initial_fields(grid, N_ENSEMBLE)
std0 = ens0.std(axis=0)

# --------------------------------------------------------------------------- #
# 4. Numerical-GP ensemble rollout (predictor code path -- NOT the simulator)
# --------------------------------------------------------------------------- #
print("[4] Rolling out %d-member ensemble through embedded operator ..." % N_ENSEMBLE)
pred = ngp.rollout(ens0, n_steps=N_STEPS, record_times=RECORD_TIMES)
pred_mean = {t: pred[t].mean(axis=0) for t in RECORD_TIMES}
pred_std = {t: pred[t].std(axis=0) for t in RECORD_TIMES}

# Ablation: roll out the quadratic-trend-only IC (RBF residual / GP removed).
print("[5] Ablation: trend-only (GP residual removed) rollout ...")
trend0 = gp.trend_only_field(grid)
abl = ngp.rollout(trend0[None, :, :], n_steps=N_STEPS, record_times=RECORD_TIMES)
abl_mean = {t: abl[t][0] for t in RECORD_TIMES}

# --------------------------------------------------------------------------- #
# 5. Masks / metrics
# --------------------------------------------------------------------------- #
window = np.zeros_like(phi0_true, dtype=bool)
window[OBS_LO:OBS_HI, OBS_LO:OBS_HI] = True

def front_band(gt_field, w=4.0):
    return np.abs(gt_field) <= w        # cells near the true fire front

print("[6] Computing metrics ...")
# t=0 reconstruction error (reported separately from forecast error).
recon = {
    "rmse_full": rmse(m0, phi0_true),
    "rmse_window": rmse(m0, phi0_true, window),
    "mae_window": mae(m0, phi0_true, window),
}
fd_mean0, fd_haus0 = front_distance(m0, phi0_true)
recon["front_mean_cells"] = fd_mean0
recon["front_haus_cells"] = fd_haus0

# Does the GP-ablated (trend-only) IC even have a fire front?
abl_has_front = len(front_points(trend0)) > 0
print("    trend-only IC: min phi = %.3f, has zero-level-set front = %s"
      % (trend0.min(), abl_has_front))

rows = []
for t in EVAL_TIMES:
    band = front_band(gt[t])
    fd_mean, fd_haus = front_distance(pred_mean[t], gt[t])
    abl_fd_mean, _ = front_distance(abl_mean[t], gt[t])
    rows.append({
        "t": t,
        "rmse_full": rmse(pred_mean[t], gt[t]),
        "rmse_window": rmse(pred_mean[t], gt[t], window),
        "mae_window": mae(pred_mean[t], gt[t], window),
        "front_mean_cells": fd_mean,
        "front_mean_ft": fd_mean * DELTA_X,
        "front_mean_m": fd_mean * DELTA_X / FT_PER_M,
        "front_haus_cells": fd_haus,
        "pred_std_band": float(pred_std[t][band].mean()),   # front-localised uncertainty
        "pred_std_window": float(pred_std[t][window].mean()),
        "abl_rmse_window": rmse(abl_mean[t], gt[t], window),   # ablation: GP removed
        "abl_front_mean_cells": abl_fd_mean,
        "gt_burned": int((gt[t] < 0).sum()),
        "pred_burned": int((pred_mean[t] < 0).sum()),
        "abl_burned": int((abl_mean[t] < 0).sum()),
    })

# --------------------------------------------------------------------------- #
# 6. Write metrics CSV + leakage/circularity self-check
# --------------------------------------------------------------------------- #
with open(os.path.join(OUTDIR, "metrics.csv"), "w", newline="") as f:
    w = csv.writer(f)
    cols = ["t", "rmse_full", "rmse_window", "mae_window",
            "front_mean_cells", "front_mean_ft", "front_mean_m", "front_haus_cells",
            "pred_std_band", "pred_std_window",
            "abl_rmse_window", "abl_burned", "gt_burned", "pred_burned"]
    w.writerow(cols)
    for r in rows:
        w.writerow([r[k] for k in cols])

band0 = front_band(gt[EVAL_TIMES[-1]])
selfcheck = []
selfcheck.append("(a) Predictions come from the GP stepper, not the simulator:")
selfcheck.append("    ground-truth stepper = %s.%s" % (sim.__name__, sim.ground_truth_step.__name__))
selfcheck.append("    predictor stepper    = %s.%s" % (ngp.__name__, ngp.embedded_levelset_step.__name__))
selfcheck.append("    distinct functions   = %s" % (sim.ground_truth_step is not ngp.embedded_levelset_step))
selfcheck.append("(b) Inference used only the %d observation values; the GP never reads phi0_true." % N_OBS)
selfcheck.append("    obs value range = [%.3f, %.3f]" % (obs_values.min(), obs_values.max()))
selfcheck.append("(c) GP is non-degenerate:")
selfcheck.append("    t=0 ensemble std in front band   = %.4f (cells of phi)" % std0[front_band(gt[0])].mean())
selfcheck.append("    t=300 ensemble std in front band = %.4f" % pred_std[EVAL_TIMES[-1]][band0].mean())
selfcheck.append("    t=0 reconstruction window RMSE   = %.4f (> 0: front genuinely inferred, not leaked)" % recon["rmse_window"])
spurious = int((m0[~window] < 0).sum())
selfcheck.append("    spurious burned cells outside window = %d" % spurious)
with open(os.path.join(OUTDIR, "self_check.txt"), "w") as f:
    f.write("\n".join(selfcheck) + "\n")
print("\n".join(selfcheck))

# --------------------------------------------------------------------------- #
# 7. Figures
# --------------------------------------------------------------------------- #
print("[7] Rendering figures ...")
ZOOM = (40, 160)
PHI_VMIN, PHI_VMAX = -10, 70


def style_field(ax, field, title, vmin=PHI_VMIN, vmax=PHI_VMAX, cmap="RdBu_r"):
    im = ax.imshow(field, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xlim(*ZOOM); ax.set_ylim(*ZOOM)
    ax.set_title(title, fontsize=10)
    return im


# --- Figure: t=0 reconstruction with observations -------------------------- #
fig, axs = plt.subplots(1, 4, figsize=(18, 4.6))
im = style_field(axs[0], phi0_true, "True $\\phi^0$ + 50 obs")
axs[0].scatter(xs, ys, s=14, c="k", edgecolors="w", linewidths=0.5)
fig.colorbar(im, ax=axs[0], fraction=0.046)
im = style_field(axs[1], m0, "GP posterior mean $\\phi^0$")
axs[1].contour(m0, levels=[0], colors="k", linewidths=1.2)
fig.colorbar(im, ax=axs[1], fraction=0.046)
im = style_field(axs[2], std0, "GP posterior std $\\phi^0$", vmin=0, vmax=8, cmap="viridis")
fig.colorbar(im, ax=axs[2], fraction=0.046)
im = style_field(axs[3], np.abs(m0 - phi0_true), "|recon error|", vmin=0, vmax=12, cmap="magma")
fig.colorbar(im, ax=axs[3], fraction=0.046)
for a in axs:
    a.set_xlabel("x"); a.set_ylabel("y")
fig.suptitle("t = 0 reconstruction (window RMSE = %.2f, front mean dist = %.2f cells)"
             % (recon["rmse_window"], recon["front_mean_cells"]))
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "t0_reconstruction.png"), dpi=120)
plt.close(fig)

# --- Per-eval-time comparison panels --------------------------------------- #
for r in rows:
    t = r["t"]
    fig, axs = plt.subplots(1, 4, figsize=(18, 4.6))
    im = style_field(axs[0], pred_mean[t], "Prediction (ensemble mean) t=%d" % t)
    axs[0].contour(pred_mean[t], levels=[0], colors="r", linewidths=1.2)
    fig.colorbar(im, ax=axs[0], fraction=0.046)
    im = style_field(axs[1], gt[t], "Ground truth t=%d" % t)
    axs[1].contour(gt[t], levels=[0], colors="k", linewidths=1.2)
    fig.colorbar(im, ax=axs[1], fraction=0.046)
    im = style_field(axs[2], np.abs(pred_mean[t] - gt[t]), "|error| (RMSE_win=%.2f)" % r["rmse_window"],
                     vmin=0, vmax=12, cmap="magma")
    fig.colorbar(im, ax=axs[2], fraction=0.046)
    im = style_field(axs[3], pred_std[t], "predictive std (band=%.2f)" % r["pred_std_band"],
                     vmin=0, vmax=8, cmap="viridis")
    axs[3].contour(gt[t], levels=[0], colors="w", linewidths=0.8)
    fig.colorbar(im, ax=axs[3], fraction=0.046)
    for a in axs:
        a.set_xlabel("x"); a.set_ylabel("y")
    fig.suptitle("t = %d : front mean dist = %.2f cells (%.0f ft)" %
                 (t, r["front_mean_cells"], r["front_mean_ft"]))
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "comparison_t%03d.png" % t), dpi=120)
    plt.close(fig)

# --- Front-evolution overlay (pred vs GT, all times) + ensemble spread ------ #
fig, ax = plt.subplots(figsize=(7.5, 7))
colors = plt.cm.viridis(np.linspace(0, 1, len(RECORD_TIMES)))
for c, t in zip(colors, RECORD_TIMES):
    ax.contour(gt[t], levels=[0], colors=[c], linewidths=2.0, linestyles="solid")
    ax.contour(pred_mean[t], levels=[0], colors=[c], linewidths=1.4, linestyles="dashed")
# ensemble spread of the front at the final time (thin grey members)
for k in range(min(40, N_ENSEMBLE)):
    ax.contour(pred[EVAL_TIMES[-1]][k], levels=[0], colors="0.7", linewidths=0.3, alpha=0.5)
ax.set_xlim(*ZOOM); ax.set_ylim(*ZOOM)
ax.set_title("Fire front evolution: GT (solid) vs prediction (dashed)\n"
             "colour = time 0..300; grey = ensemble members at t=300")
ax.set_xlabel("x"); ax.set_ylabel("y")
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "front_evolution.png"), dpi=120)
plt.close(fig)

# --- Load-bearing diagnostics: variance growth + ablation ------------------- #
fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
ts = [0] + EVAL_TIMES
band_std = [std0[front_band(gt[0])].mean()] + [r["pred_std_band"] for r in rows]
axs[0].plot(ts, band_std, "o-", color="C0")
axs[0].set_xlabel("t (min)"); axs[0].set_ylabel("ensemble std at front band (cells of $\\phi$)")
axs[0].set_title("Predictive uncertainty propagated to t>0\n(non-trivial => GP is load-bearing)")
axs[0].grid(alpha=0.3)

axs[1].plot(EVAL_TIMES, [r["rmse_window"] for r in rows], "o-", label="full GP")
axs[1].plot(EVAL_TIMES, [r["abl_rmse_window"] for r in rows], "s--",
            label="ablation: trend-only IC (GP residual removed)")
axs[1].set_xlabel("t (min)"); axs[1].set_ylabel("field RMSE in window ($\\phi$)")
axs[1].set_title("Ablation: removing the GP residual degrades the forecast\n"
                 "(trend-only IC has no fire front at all)")
axs[1].legend(); axs[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "diagnostics.png"), dpi=120)
plt.close(fig)

# --------------------------------------------------------------------------- #
# 8. Console summary
# --------------------------------------------------------------------------- #
print("\n=== t=0 reconstruction (separate from forecast error) ===")
print("  window RMSE = %.3f | full RMSE = %.3f | front mean = %.2f cells (%.0f ft)"
      % (recon["rmse_window"], recon["rmse_full"], recon["front_mean_cells"],
         recon["front_mean_cells"] * DELTA_X))
print("\n=== Forecast metrics (full GP) vs ablation (GP removed) ===")
print("  t   RMSE_win  front_mean[cells/ft]  haus  std_band | abl_RMSE_win  burned(gt/pred/abl)")
for r in rows:
    print("  %3d  %7.3f  %6.2f /%6.0f   %5.2f  %7.4f |  %8.3f    %5d/%5d/%5d"
          % (r["t"], r["rmse_window"], r["front_mean_cells"], r["front_mean_ft"],
             r["front_haus_cells"], r["pred_std_band"],
             r["abl_rmse_window"], r["gt_burned"], r["pred_burned"], r["abl_burned"]))
print("\nAblation IC has fire front: %s (trend-only min phi = %.2f)" % (abl_has_front, trend0.min()))
print("Saved outputs to", OUTDIR)
