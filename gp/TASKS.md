# TASKS.md

Optional checklist — not a mandatory phase gate. You may skip or reorder steps.

The hard rules these steps enforce live in CLAUDE.md (**Numerical GP requirements**, **Evaluation Protocol → Evaluation integrity**) and CONVENTIONS.md. They guard against a GP that produces great-looking metrics while doing no real work: a degenerate (zero) residual, mean-only propagation, and a "prediction" that is just the ground-truth simulator re-run from the reconstructed field. Avoid that.

## Phase 1

- [ ] Extract level-set PDE from Rothermel paper/simulator
- [ ] Verify Rothermel implementation
- [ ] Read `simulation.ipynb` for physics/constants/operators only — not for the initial-condition geometry

## Phase 2

- [ ] Create numerical GP (embed the Euler step in the GP; propagate covariance, not just the mean)
- [ ] Sample 50 fixed observations from t=0 within the central 100×100 window (indices 50 ≤ x,y < 150); document the seed
- [ ] Train on sparse observations using only the 50 observation values — no ground-truth field, parameters, or analytic form
- [ ] Verify the GP is load-bearing: non-zero residual/posterior variance; an ablation shows the result changes when the GP is removed
- [ ] Confirm predictions are produced by the GP stepper, not by re-running the ground-truth simulator

## Phase 3

- [ ] Predict t=50
- [ ] Predict t=100
- [ ] Predict t=150
- [ ] Predict t=200
- [ ] Predict t=250
- [ ] Predict t=300

## Phase 4

- [ ] Show t=0 initial field with sampled observation points overlaid
- [ ] Calculate comparison metrics
- [ ] Confirm ground truth and prediction share no forward-stepping function
- [ ] Apply any redistancing/reinitialization symmetrically (both sides or neither)
- [ ] Report t=0 reconstruction error separately from t>0 forecast error
- [ ] Generate comparison figures
- [ ] Write trial report in `gp/results/trial_NNN/report.tex` (from `gp/report_template.tex`)
- [ ] Compile `gp/results/trial_NNN/report.pdf` with `pdflatex`
- [ ] Summarize findings
- [ ] Request user feedback

## Trial report checklist (`report.tex`)

- [ ] Governing Physics (numbered equations, constants table)
- [ ] Method (prior placement, Euler embedding, block matrix / kernel structure, inference, algorithm)
- [ ] Assumptions and approximations (flagged explicitly)
- [ ] Experimental setup
- [ ] Results (metrics table, `\includegraphics` for figures)
- [ ] GP shown to be load-bearing (diagnostic or ablation), not degenerate
- [ ] Predictions come from the GP, not the simulator — stated explicitly
- [ ] Covariance propagated to t>0 (not mean-only)
- [ ] Circularity / leakage self-check documented
- [ ] Sources cited
- [ ] `report.pdf` compiles without errors
