@echo off
echo 디스코드 봇과 웹 대시보드를 시작합니다...

echo.
echo [1/3] 서버 실행 환경 점검 중...
pip install -r requirements.txt >nul 2>&1

echo.
echo [2/3] 웹 대시보드 서버를 백그라운드에서 실행합니다...
start "Web Dashboard Background Server" /b cmd /c "python web.py"
timeout /t 3 >nul

echo.
echo [3/3] 외부 링크 터널링(Cloudflare)을 시작합니다.
echo 잠시 후 아래 팝업창(검은 화면)에 나오는 "https://****.trycloudflare.com" 형식의 주소를 복사해서 사람들에게 공유하세요!
echo (이 주소는 보안 경고창 없이 바로 접속됩니다.)
echo.
start "Web Dashboard Tunnel" cmd /k "npx -y cloudflared --url http://127.0.0.1:5000"

echo.
echo ========================================================
echo 이제 디스코드 봇을 실행합니다!
echo 봇을 종료하려면 이 창을 닫으시거나 Ctrl + C 를 누르세요.
echo (이 창을 닫으면 봇과 터널링 서버가 모두 종료될 수 있습니다.)
echo ========================================================
echo.
python main.py
