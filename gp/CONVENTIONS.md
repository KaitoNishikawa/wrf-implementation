- Prefer correctness over speed.
- Keep implementations focused and auditable; avoid unnecessary abstractions.
- Avoid introducing frameworks.
- Avoid refactoring unrelated code.
- Use deterministic seeds.
- Explain mathematical assumptions in comments.

## Numerical GP integrity (hard rules — see CLAUDE.md for full statements)

- The GP must produce the predictions: predictions at t > 0 come from the Euler step embedded in the GP, never from re-running the ground-truth simulator. Ground truth and prediction share no forward-stepping function.
- Propagate covariance, not just the posterior mean. A mean-only rollout is not a valid trial on its own.
- The GP must be load-bearing: if the residual or posterior variance collapses to ~zero, that is a failure, not a result. Prove the GP does work with a diagnostic or ablation.
- No ground-truth leakage: infer the t = 0 field only from the 50 observation values, sampled from a fixed central 100×100 window of the grid (indices 50 ≤ x,y < 150; see CLAUDE.md). Never hard-code, seed, or assume the true initial-condition geometry, parameters, or analytic form. Use `simulation.ipynb` for physics, constants, and operators only.
- Apply any redistancing/reinitialization symmetrically to prediction and ground truth, or to neither.
- Report t = 0 reconstruction error separately from t > 0 forecast error; include a circularity/leakage self-check before reporting.

## Units (see `gp/UNITS.md`)

- **Δt = 1 step = 1 minute** (not seconds): R is in ft/min from Rothermel's imperial formula, and the Euler step has no explicit Δt.
- `delta_x = 82.021 ft = 25 m`; grid 200×200 = 5 km × 5 km (paper Section 3).
- `R_f` in ft/min; wind in ft/min; `level_set_field` φ in **grid-index units**, not feet.

## Reporting

- Save each trial under `gp/results/trial_NNN/`.
- Write `gp/results/trial_NNN/report.tex` as a math-forward technical note (see CLAUDE.md **Trial Documentation**); copy from `gp/report_template.tex`.
- Compile `report.pdf` with `pdflatex report.tex` in the trial directory.
- Use `\begin{equation}` for numbered equations and `\begin{bmatrix}` for block matrices.
- Define all symbols; cite sources; flag assumptions in a dedicated section.
- Keep Method, Assumptions, and Results as separate sections.
- **Explicit construction (mandatory; a write-up standard, not a prescribed
  method).** Do not stop at an abstract operator-on-covariance statement
  (`K_n = J K J^\top`). Whatever encoding you choose, show how your embedded physics
  produces the covariance term by term, in the §5-appendix style of the Numerical
  GP paper: write your operator(s) out with all coefficients shown (if you
  approximate a nonlinear operator, state and justify the approximation you chose —
  your call), the discrete stepping operator(s), the resulting covariance / kernel
  objects, and a dedicated **Appendix** with their full term-by-term expansion plus
  closed-form expressions for any kernel-derived quantities (verify these). If the
  covariance is computed by a realization that differs from the written
  construction, state the
  correspondence and order of agreement. The encoding is each trial's own choice;
  only the explicitness is mandated.
