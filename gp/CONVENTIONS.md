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
- No ground-truth leakage: infer the t = 0 field only from the 50 observation values. Never hard-code, seed, or assume the true initial-condition geometry, parameters, or analytic form. Use `simulation.ipynb` for physics, constants, and operators only.
- Apply any redistancing/reinitialization symmetrically to prediction and ground truth, or to neither.
- Report t = 0 reconstruction error separately from t > 0 forecast error; include a circularity/leakage self-check before reporting.

## Reporting

- Save each trial under `gp/results/trial_NNN/`.
- Write `gp/results/trial_NNN/report.tex` as a math-forward technical note (see CLAUDE.md **Trial Documentation**); copy from `gp/report_template.tex`.
- Compile `report.pdf` with `pdflatex report.tex` in the trial directory.
- Use `\begin{equation}` for numbered equations and `\begin{bmatrix}` for block matrices.
- Define all symbols; cite sources; flag assumptions in a dedicated section.
- Keep Method, Assumptions, and Results as separate sections.
