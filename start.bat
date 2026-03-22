@echo off
echo.
echo ==============================================
echo ⚡ Anker X1 Dev Dashboard Setup
echo ==============================================
echo.
echo 1. Installiere required Pakete (falls nicht vorhanden)...
python -m pip install -r requirements.txt
echo.
echo 2. Starte Streamlit App...
python -m streamlit run app.py
pause
