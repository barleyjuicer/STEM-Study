# Build and Release Guide

## Build Requirements

The build computer needs Python installed. The target computer running the portable release does not need Python.

## Build Steps

From the project root:

```powershell
.\build_release.bat
```

This calls `packaging/build_release.bat`, installs build requirements into `.venv`, runs PyInstaller, and creates:

```text
STEM_Study_Generator_Portable/
|-- STEM_Study_Generator.exe
|-- Start.bat
|-- data/
|-- exports/
|-- reports/
|-- README.txt
`-- _internal/
```

The `_internal` folder is required by PyInstaller and must remain with the executable.

## Run the Portable App

Open the release folder and double-click:

```text
Start.bat
```

The app opens locally at:

```text
http://localhost:8501
```

## Transfer to Another Computer

Copy the entire `STEM_Study_Generator_Portable` folder. Keep all files and folders together.

You may zip the folder, move it with a USB drive, or use normal file copy.

## Back Up Student Progress

Student progress is stored in:

```text
STEM_Study_Generator_Portable/data/stem_study.db
```

To back up progress, copy the entire `data` folder.

To restore progress into another portable copy, replace that copy's `data` folder with the backup.

## GitHub Safety

Do not commit:

- Real SQLite databases
- Student records
- PHI/PII
- Reports
- Exports
- Logs
- Screenshots
- Build folders
- Portable release folders
- Zip release files

Only commit source code, docs, tests, fake/sample data, and folder marker files.
