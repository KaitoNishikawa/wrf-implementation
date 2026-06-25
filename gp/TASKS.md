# TASKS.md

Optional checklist — not a mandatory phase gate. You may skip or reorder steps.

## Phase 1

- [ ] Extract level-set PDE from Rothermel paper/simulator
- [ ] Verify Rothermel implementation

## Phase 2

- [ ] Create numerical GP
- [ ] Train on sparse observations

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
- [ ] Sources cited
- [ ] `report.pdf` compiles without errors
