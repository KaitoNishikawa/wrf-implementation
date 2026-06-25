# Units mapping for `simulation.ipynb`

The ground-truth simulator (`simulation.ipynb`, repo root) reproduces the uniform-velocity
case of **Section 3** of Muñoz-Esparza et al. (2018), *An Accurate Fire-Spread Algorithm in
the WRF Model Using the Level-Set Method* (`gp/docs/`). Section 3 uses a 5 km × 5 km domain
at 25 m resolution, which fixes the grid as 200 × 200.

The simulator feeds **Rothermel (1972)'s raw imperial formula**, so the rate of spread comes
out in **ft/min**, not the m/s the WRF paper uses. The Euler step has `Δt ≡ 1` implicit (no
`Δt` factor in `calculate_new_level_set_field`), so the only self-consistent reading is
**Δt = 1 minute**. GP trials must treat steps as minutes, not seconds.

## Canonical quantities

| Quantity | Symbol / variable | Value | Units | Notes |
|---|---|---|---|---|
| Grid size | `field_size` | 200 × 200 | cells | 5 km / 25 m = 200 |
| Grid spacing | `delta_x` | 82.021 | ft (= 25.0 m) | `82.021 ft = 25.0 m` exactly |
| Domain extent | — | 5000 × 5000 | ft? no → 5 km × 5 km | matches paper Section 3 |
| Time step | implicit `Δt` | 1 | **minute** | no `Δt` term in code ⇒ `Δt = 1` |
| Steps in loop | `range(300)` | 300 | minutes (= 5 h) | sampled every 5 ⇒ frames at 0,5,…,295 min |
| Eval times (t=50…300) | — | 50,100,…,300 | **minutes** | per CLAUDE.md Evaluation Protocol |
| Rate of spread | `Rf_field`, `R_0`, `R_f` | ~3.8 (no wind), ~9.7 (full) | **ft/min** | Rothermel imperial constants |
| Midflame wind | `wind_X/Y_velo_at_midflame_height` | (100, 100) → mag 141 | **ft/min** | = 0.72 m/s |
| Level-set field | `level_set_field` (φ) | signed distance | **grid-index units** (NOT ft) | see caveat below |
| Viscosity coeff | `viscosity_coefficient` (ε) | 0.4 | dimensionless | Mandel et al. value cited by paper |

## Why Δt = 1 means one minute

The level-set front normal speed is `F = R_f` (the φ scaling cancels in `F = φ_t / |∇φ|`).
With `R_f` in ft/min and the implicit `Δt = 1`, the front advances `R_f` ft per step, i.e.
`R_f` ft/min — so each step is one minute. Per-step front advance ≈ 9.68 ft (CFL
`R_f·Δt/Δx ≈ 0.12`, comfortably stable for Euler).

If a trial instead treated a step as 1 **second**, R would have to be ft/s, but it is ft/min —
a 60× error in spread rate. **Always: 1 step = 1 min.**

## Caveats / deviations from the paper (relevant to GP fidelity)

- **φ is in grid-index units, not feet.** The initial signed distance (`simulation.ipynb`
  CELL 5) is built from raw `mgrid` index differences, while `|∇φ|` is taken with the physical
  `delta_x`. This cancels for front *speed*, but if you read φ as a physical distance (e.g. a
  contour-distance metric or a GP prior on φ in feet) you must remember φ is in index units.
- **No reinitialization.** The paper reinitializes φ to a signed-distance function (its Eq. 3);
  the simulator does not. So `|∇φ|` drifts from 1 over time. Any redistancing in a GP trial must
  be applied symmetrically to prediction and ground truth, or to neither (CLAUDE.md).
- **Euler vs ERK3 / centered vs WENO5.** The paper uses WENO5 + 3rd-order ERK; the simulator
  uses `np.gradient` (centered) + forward Euler. Euler is mandated by CLAUDE.md.
- **Wind strength.** The paper's Section 3 uniform case is 5 m/s (= 984.3 ft/min, the
  commented-out value). The active `(100, 100)` ft/min ≈ 0.72 m/s is ~7× weaker.

## Sources

- `simulation.ipynb` — constants, operators, Euler update (source of truth).
- Muñoz-Esparza et al. (2018), Section 2.1–2.3, Section 3 — `gp/docs/`.
- Rothermel (1972), p. 32 (R in ft/min) — `gp/docs/A_Mathematical_Model_for_Predicting_Fire.pdf`.
