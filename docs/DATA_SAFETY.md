# Data Safety Notes

This repository should be safe to publish on GitHub only when private generated files are excluded.

Private data locations:

- `data/` for SQLite databases and student progress
- `exports/` for generated CSV/XLSX/PDF files
- `reports/` for generated reports

Do not commit:

- Real user databases
- Student records
- PHI/PII
- Reports
- Exports
- Logs
- Screenshots
- Build outputs
- Portable release folders

Use `sample_data/` only for fake data that is safe to share publicly.
