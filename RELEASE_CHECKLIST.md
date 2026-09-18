# Release Checklist

This checklist is the final verification gate for the Guitar Chord Generator release.

## Automated checks

Run from the repository root:

```bash
python scripts/verify_release.py
python -m compileall -q .
pytest -q
```

The release verifier checks required application/deployment files, required source directories, absence of Python bytecode and test caches, absence of `.streamlit/secrets.toml`, and separation of test-only dependencies from runtime requirements.

## Package checks

Before sharing a ZIP:

- Package the repository root folder and its application files.
- Do not include `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.pyc`, `.pyo`, or `.streamlit/secrets.toml`.
- Keep `app.py`, `requirements.txt`, and `.streamlit/config.toml` at the repository root.
- Re-run the complete test suite after extracting the ZIP into a clean directory.

## Streamlit Community Cloud checks

The current application is prepared for Streamlit Community Cloud with:

- Entrypoint: `app.py`
- Runtime dependency file: `requirements.txt`
- Streamlit configuration: `.streamlit/config.toml`
- Seed / Reproducibility controls are available in the sidebar
- No application secrets required
- Python 3.12 is the tested deployment target for the release CI configuration

After deployment, verify that the app opens, the sidebar controls render, Generate/Regenerate/Randomize work, refinement actions work, copy/save controls render, and browser audio preview responds to a user click.

## Release state

The application scope remains the guitar chord/chord-progression generator. The final seed feature adds reproducibility controls without changing the underlying harmonic generation algorithm.
