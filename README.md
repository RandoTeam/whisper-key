<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-success.svg?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/Platform-Windows%2011-blue.svg?style=for-the-badge&logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/Python-3.10+-yellow.svg?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge" alt="License" />

  <br><br>
  <h1>🎤 Whisper Key / Beautiful STT Overlay</h1>
  <p><strong>A premium, lightning-fast Speech-To-Text floating widget for Windows.</strong></p>
  <p><i>Стильный, молниеносный виджет диктовки (Голос-в-Текст) для Windows с анимациями уровня Apple Siri.</i></p>
</div>

<hr>

## 🌟 About The Project / О проекте

**Whisper Key** is a beautiful, global overlay application that brings Apple-like dictation to Windows. Simply hold a hotkey (`Ctrl + Win`), speak naturally, and watch as your voice is instantly transcribed and pasted into any active application. Powered by `faster-whisper` and completely offline for total privacy.

**Whisper Key** — это премиальный глобальный виджет, который переносит удобство диктовки Apple на Windows. Просто зажмите горячую клавишу (`Ctrl + Win`), говорите естественным языком, и ваш текст будет моментально расшифрован и вставлен в любое активное окно. Работает на базе `faster-whisper`, полностью локально и без интернета для защиты вашей приватности.

![Screenshot Placeholder](https://placehold.co/800x400/121214/f4f4f5?text=Siri+Wave+Oscillograph+Screenshot+Here)

---

## ✨ Features / Ключевые возможности

- 🚀 **Lightning Fast:** Uses `faster-whisper` and CTranslate2 for ultra-fast, near real-time transcription on your GPU.
- 🎨 **Beautiful iOS-like UI:** Features a stunning 60-FPS mathematically accurate Siri wave (oscillograph) built with Electron and HTML5 Canvas. Glassmorphic transparency seamlessly blends with Windows 11.
- 🌍 **Multi-language Support:** Excellent transcription for Russian (`zipformer.small.ru` & `large-v3-turbo`) and English.
- ⌨️ **Global Hotkeys:** Works anywhere in Windows. Press `Ctrl + Win` to speak, release to paste.
- 🔒 **100% Offline:** All AI models run locally on your machine. Your voice is never sent to the cloud.

---

## 🛠 Tech Stack / Технологии

* **Backend Engine:** Python, `faster-whisper`, `CTranslate2`, `pyaudio`
* **Frontend GUI:** Electron, HTML5 Canvas API (60-FPS rendering)
* **IPC (Inter-Process Communication):** High-performance Local TCP Sockets
* **AI Model:** `large-v3-turbo` (Default) / `zipformer.small.ru`

---

## 📥 Installation / Установка

### Prerequisites / Требования
* Windows 10 or Windows 11 (Recommended for blur effects)
* Node.js (for Electron UI)
* Python 3.10+ 
* Optional but highly recommended: NVIDIA GPU with CUDA for instant transcription

### Setup / Настройка

1. **Clone the repo / Скачайте репозиторий:**
   ```bash
   git clone https://github.com/RandoTeam/whisper-key.git
   cd whisper-key
   ```

2. **Install Python dependencies / Установите зависимости Python:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the App / Запустите приложение:**
   ```bash
   # You can run it directly using our launcher
   python -m src.whisper_key.main
   ```
   *(Note: The Electron GUI dependencies will be automatically installed via `npx` on the first run! / Зависимости для графического интерфейса скачаются автоматически при первом запуске).*

---

## ⚙️ How It Works / Как это работает

1. **Start the app:** The background service will load the AI model into memory.
2. **Press `Ctrl + Win`:** A beautiful translucent capsule will smoothly slide in from the bottom of your screen.
3. **Speak:** The neon Siri-wave will react dynamically to your voice in real-time.
4. **Release `Ctrl + Win`:** The app will finalize the transcription and instantly type the text into your currently active window (e.g. Word, Telegram, Browser).

---

## 📜 License / Лицензия

Distributed under the **MIT License**. See `LICENSE` for more information.

*This project utilizes `faster-whisper` by SYSTRAN and the original `Whisper` model by OpenAI, both of which are open-source under the MIT License.*

<br>
<div align="center">
  <i>Crafted with passion for beautiful UI and AI technology.</i>
</div>
