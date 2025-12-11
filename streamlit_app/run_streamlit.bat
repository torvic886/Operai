@echo off
echo ========================================
echo   Iniciando Dashboard Streamlit
echo ========================================
echo.

cd streamlit_app

echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Iniciando Streamlit en http://localhost:8501
echo.

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

pause