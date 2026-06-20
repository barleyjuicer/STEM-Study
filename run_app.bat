@echo off
cd /d "%~dp0"
python -m streamlit run src\stem_study_generator\app.py --server.address localhost --server.port 8501
pause
