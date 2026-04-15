# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os

project_path = os.path.abspath(".")

a = Analysis(
    ['src/main.py'],
    pathex=[os.path.join(project_path, 'src')],
    binaries=[
        ('src/ffmpeg/ffmpeg.exe', 'ffmpeg'),
    ],
    datas=[                                                                                                     
        ('src/model', 'model'),
        ('src/data', 'data'),
    ],
    hiddenimports=[
        'torch',
        'whisper',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Transcritor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # ⚠️ coloque False se quiser sem terminal
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Transcritor'
)