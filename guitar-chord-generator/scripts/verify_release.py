"""Validate the repository is complete and safe to package for release."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "app.py",
    "README.md",
    "DEPLOYMENT.md",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    ".streamlit/config.toml",
    "generator/seeding.py",
    "Procfile",
    "Makefile",
)
REQUIRED_DIRS = ("music", "generator", "tests")
FORBIDDEN_PATH_PARTS = {
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def main() -> int:
    missing_files = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    missing_dirs = [path for path in REQUIRED_DIRS if not (ROOT / path).is_dir()]

    if missing_files or missing_dirs:
        print("Release verification failed:")
        if missing_files:
            print("Missing files:", ", ".join(missing_files))
        if missing_dirs:
            print("Missing directories:", ", ".join(missing_dirs))
        return 1

    unexpected = []
    for path in ROOT.rglob("*"):
        relative_parts = path.relative_to(ROOT).parts
        if any(part in FORBIDDEN_PATH_PARTS for part in relative_parts):
            unexpected.append(path.relative_to(ROOT))
        elif path.is_file() and path.suffix in FORBIDDEN_SUFFIXES:
            unexpected.append(path.relative_to(ROOT))

    if unexpected:
        print("Release verification failed: generated cache/bytecode files are present:")
        for path in unexpected:
            print(f" - {path}")
        return 1

    secrets_file = ROOT / ".streamlit" / "secrets.toml"
    if secrets_file.exists():
        print("Release verification failed: .streamlit/secrets.toml must not be packaged.")
        return 1

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    requirements = [line.strip() for line in requirements if line.strip() and not line.lstrip().startswith("#")]
    if not any(line.startswith("streamlit") for line in requirements):
        print("Release verification failed: requirements.txt does not declare Streamlit.")
        return 1

    if any(line.startswith("pytest") for line in requirements):
        print("Release verification failed: test-only pytest dependency is present in runtime requirements.")
        return 1

    print("Release verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
