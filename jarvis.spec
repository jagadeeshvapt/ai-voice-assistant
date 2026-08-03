# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for JARVIS v5.0 Production 100/100 - Offline+Online + Full Access

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('data', 'data'),
        ('models', 'models'),
        ('jarvis', 'jarvis'),
    ],
    hiddenimports=[
        'jarvis.core.orchestrator',
        'jarvis.audio.speech_to_text',
        'jarvis.audio.text_to_speech',
        'jarvis.language.tanglish_normalizer',
        'jarvis.language.intent_parser',
        'jarvis.language.local_llm',
        'jarvis.language.human_personality',
        'jarvis.language.empathy_engine',
        'jarvis.language.claude_level_intelligence',
        'jarvis.security.permissions',
        'jarvis.security.pin',
        'jarvis.memory.database',
        'jarvis.memory.self_learning',
        'jarvis.tools.registry',
        'yaml',
        'bcrypt',
        'psutil',
        'pyttsx3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
