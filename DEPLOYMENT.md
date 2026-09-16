# Deployment

The application is a Python + Streamlit app.

## Local

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

Use `app.py` as the entrypoint and keep `requirements.txt` at the repository root.
No external API keys are required by the current application.

## Generic process host

The included `Procfile` starts Streamlit on the platform-provided `PORT`.

## Notes

Audio preview uses the browser's Web Audio API, so it requires a user click
and a browser that supports `AudioContext`. The generated music engine itself
runs entirely in Python.
