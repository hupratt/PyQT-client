@echo off
pyinstaller --noconfirm --onefile --log-level=INFO ui.py
echo "copy the freshly created .exe file from the /dist folder into this folder ./"
@pause
