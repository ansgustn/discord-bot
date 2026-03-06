@echo off
echo 디스코드 봇과 웹 대시보드를 시작합니다...

echo.
echo [1/3] 파이썬 패키지 설치 확인 중...
pip install -r requirements.txt >nul 2>&1

echo.
echo [2/3] 웹 대시보드 서버를 백그라운드에서 실행합니다...
start /b cmd /c "python web.py"
timeout /t 2 >nul

echo.
echo [3/3] 외부 링크 터널링(Localtunnel)을 시작합니다.
echo 잠시 후 아래 팝업창(검은 화면)에 나오는 "your url is: https://..." 주소를 복사해서 사람들에게 공유하세요!
echo.
start "Web Dashboard Tunnel" cmd /k "npx localtunnel --port 5000"

echo.
echo ========================================================
echo 이제 디스코드 봇을 실행합니다!
echo 봇을 종료하려면 이 창을 닫으시거나 Ctrl + C 를 누르세요.
echo (이 창을 닫으면 봇과 웹 서버가 모두 종료됩니다.)
echo ========================================================
echo.
python main.py
