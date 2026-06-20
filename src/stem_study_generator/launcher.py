import os
import sys
from pathlib import Path

from streamlit.web import cli as streamlit_cli


def executable_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundled_app_path():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")).resolve() / "stem_study_generator" / "app.py"
    return Path(__file__).resolve().parent / "app.py"


def main():
    root = executable_dir()
    os.environ["STEM_STUDY_PORTABLE_DIR"] = str(root)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "false")

    (root / "data").mkdir(exist_ok=True)
    (root / "exports").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)

    sys.argv = [
        "streamlit",
        "run",
        str(bundled_app_path()),
        "--server.address",
        "localhost",
        "--server.port",
        "8501",
        "--global.developmentMode",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]
    streamlit_cli.main()


if __name__ == "__main__":
    main()
