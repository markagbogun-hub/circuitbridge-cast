@echo off
setlocal
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --noconfirm --clean --windowed --name CastwiseAudioDoctor --collect-all pyloudnorm --collect-all PySide6 --collect-all matplotlib --paths . -m castwise_audio_doctor
echo Build complete: dist\CastwiseAudioDoctor
