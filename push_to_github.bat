@echo off
cd /d "C:\Users\777 comp service\Desktop\certificate"
echo 1. Git initsializatsiya qilinmoqda...
git init
git branch -M main
echo 2. Fayllar qoshilmoqda...
git add .
echo 3. Commit qilinmoqda...
git commit -m "MDev Certificate Telegram Bot with Render config"
echo 4. Remote sozlanmoqda...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/orifjonov-77/new.git
echo 5. GitHub ga push qilinmoqda...
git push -u origin main --force
echo.
echo ===========================================
echo Tugadi! Natijani yuqorida tekshiring.
echo ===========================================
pause
