# Deployment

The application is a Python + Streamlit app. The repository is arranged so the Streamlit entrypoint and runtime dependency file sit at the repository root, which is the layout expected by Streamlit Community Cloud.

## Local

Use the same Python version you intend to deploy with, then install the runtime dependencies:

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

For development/testing, install `requirements-dev.txt` instead; it adds pytest and ruff on top of the runtime dependencies.

## Streamlit Community Cloud

Create the app from the repository and select:

- Repository: `AP200408/guitar-chord-generator`
- Branch: `main`
- Entrypoint: `app.py`

Community Cloud lets you choose the Python version in the deployment dialog. Its current default is Python 3.12, and Streamlit recommends developing with the same Python version used for deployment. The release CI therefore tests Python 3.12.

Keep `requirements.txt` at the repository root. Community Cloud uses the dependency file it finds according to its documented dependency-file precedence; this project intentionally keeps a single runtime dependency file and a separate development-only requirements file that is not used by the deployed app.

No external API keys or application secrets are required by the current app. Do not add `.streamlit/secrets.toml` to the repository or release ZIP.

After deployment, use the deployed app to verify the main generation flow, alternatives, filters, refinement controls, Copy/Save controls, and browser audio preview.

## Generic process host

The included `Procfile` starts Streamlit on the platform-provided `PORT`.

## Audio preview

Audio preview uses the browser's Web Audio API, so it requires a user click and a browser that supports `AudioContext`. The generated music engine itself runs entirely in Python.

## Release verification

From the repository root:

```bash
python scripts/verify_release.py
python -m compileall -q .
pytest -q
```

A GitHub Actions workflow runs the same release verification, compilation check, and full test suite on pushes to `main` and pull requests targeting `main`.
