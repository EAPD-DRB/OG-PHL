## Workflow

- Read-only actions don't need prior approval — status, log, branch listing, file reads, drafting.
- Mutating actions need a plan and explicit approval before running — file edits, commits, pushes, branch/ref/worktree deletion, rebases, merges.

## Project: OG-PHL

OG-PHL is a Philippines country calibration of the OG-Core overlapping-generations model of demographics and fiscal policy.

## Environment

- Conda environment: `ogphl-dev`
- Run all Python, `pip`, and `pytest` commands inside `ogphl-dev` (either `conda activate ogphl-dev` for a session, or `conda run -n ogphl-dev <cmd>` per-command). This keeps the Python version and dependency set aligned with CI.

## Python formatting

- Sequence: edit → black → test → stage → commit → push.
- Format command (matches CI's black version): `conda run -n ogphl-dev python -m black <files>`
- Run only on `.py` files; black fails on non-Python files.
- Re-run tests after formatting — black can change line breaks that affect string literals and assertions.
- CI lints all `.py` files in the repo. If `main` has formatting drift, format the drifted files too and include them in the same commit.

## Testing

- Default suite (matches CI, skips the long example run): `conda run -n ogphl-dev python -m pytest -m 'not local' -q`
- Targeted (fast): `conda run -n ogphl-dev python -m pytest tests/test_income.py tests/test_input_output.py tests/test_macro_params.py -q`
- Full example run (slow, ~35 min – 2 hr): `conda run -n ogphl-dev python examples/run_og_phl.py`

## Repo conventions

- The packaged JSON default parameters are the standard baseline input for offline/default runs.
- Calibration or data-source changes (macro parameters, demographics, earnings, industry I/O) should be validated with targeted tests and, where feasible, the relevant example flow.
