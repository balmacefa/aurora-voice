# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['../main.py'],
    pathex=['.'], # current directory (packaging/) and parent (CWD)
    binaries=[],
    datas=[],
    hiddenimports=[
        'winrt.windows.media.speechrecognition',
        'winrt.windows.globalization',
        'winrt.windows.foundation',
        'winrt.runtime',
        'keyboard',
        'pystray',
        'PIL', # For Pillow
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
    [],
    exclude_binaries=True,
    name='Aurora',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None, # No icon found in the repo
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Aurora', # onedir
)