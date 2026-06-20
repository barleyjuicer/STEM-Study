# STEM Study Generator

A local Streamlit app that generates and grades original practice problems for Physics II and Intro Cryptography.

The app is designed to run without cloud services. Student progress is stored in a local SQLite database under `data/`.

## Project Layout

```text
src/stem_study_generator/   Application source code
data/                       Private local SQLite databases and user progress
exports/                    Generated CSV/XLSX/PDF exports
reports/                    Generated reports
docs/                       Project documentation
packaging/                  Release build scripts
tests/                      Automated tests
sample_data/                Fake/sample data only
```

## Data Safety

Do not commit real student records, personal data, PHI/PII, databases, reports, exports, logs, screenshots, or generated release artifacts.

Private local data belongs here:

```text
data/
```

The active app database is:

```text
data/stem_study.db
```

Fake examples for tests or demos may be placed in:

```text
sample_data/
```

## Run Locally on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\run_app.bat
```

The app runs locally at:

```text
http://localhost:8501
```

## Build a Portable Windows Release

Use:

```powershell
.\build_release.bat
```

The full release process is documented in [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md).

## Development Approach

This is an AI-assisted project directed by the repository owner. Codex may help generate, reorganize, test, and document code, but project direction, acceptance decisions, and responsibility for any private data handling remain with the repository owner.

## Current Features

- Practice mode with immediate feedback
- Quiz mode with end-of-quiz review
- Physics numeric grading with tolerance
- Numeric Physics answers accepted with or without units
- Cryptography exact integer and text grading
- Worked solutions
- Confidence tracking
- Dashboard summaries
- CSV downloads from dashboard views

## Adding More Problem Generators

Generators live in:

```text
src/stem_study_generator/app.py
```

To add a generator:

1. Add the topic to `PHYSICS_TOPICS` or `CRYPTO_TOPICS`.
2. Write a `gen_*` function returning the same dictionary shape as the existing generators.
3. Add it to the `generators` mapping in `make_problem`.

Use `numeric_problem(...)` for Physics-style numeric answers, `exact_problem(...)` for exact integer answers, and `text_problem(...)` for short text answers.
