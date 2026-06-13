https://github.com/PinW/whisper-key-local

Local faster-whisper speech-to-text app with global hotkeys for Windows 10+ and macOS.

- **Start here:** `state_manager.py` is the hub — it coordinates all components and the recording→transcription→delivery workflow.

@docs/platform-abstraction.md

## Components

Most filenames are self-describing (`audio_recorder.py`, `clipboard_manager.py`, …). The non-obvious bits:

| Component | File | Notes |
|-----------|------|-------|
| State coordination | `state_manager.py` | Orchestrates everything — the entry point for understanding flow |
| Speech recognition | `whisper_engine.py` | faster-whisper transcription (pure STT; output transforms live elsewhere) |
| Text post-processing | `text_postprocessor.py` | Corrections + trailing-period strip, applied by state_manager after STT |
| Model management | `model_registry.py` | Whisper model registry & cache detection |
| Voice activity detection | `voice_activity_detection.py` | ten-vad continuous monitoring & silence detection |
| Configuration | `config_manager.py` | YAML via **ruamel.yaml** (preserves user comments on save) |
| Streaming | `streaming_manager.py` | Experimental real-time STT via sherpa-onnx |
| Platform abstraction | `platform/` | OS-specific implementations (see contract above) |

Cross-platform tech decisions (can't be guessed from filenames):
- **Hotkeys:** global-hotkeys (Win) / NSEvent (Mac)
- **Paste:** ctypes SendInput (Win) / Quartz (Mac)
- **Single instance:** win32event (Win) / fcntl (Mac)
- **Tray:** pystray + Pillow

## Conventions

- Test app startup: `/test-from-wsl` (launch only, no interaction)
- Ask user for real test before committing
- Prefer elegant code that is modular and consistent
- Use explicit variable/function names
- **AVOID COMMENTS** IF AT ALL POSSIBLE! DO NOT WRITE DOCSTRINGS!
- **No backward compatibility** - Break old formats freely