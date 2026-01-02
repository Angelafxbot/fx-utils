# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    [os.path.join('day_trading_bot', 'main.py')],
    pathex=[os.path.abspath('.')],  # ✅ ensures correct base path
    binaries=[],
    datas=[
        ('day_trading_bot/data/*', 'day_trading_bot/data'),
        ('day_trading_bot/logs/*', 'day_trading_bot/logs'),
        ('day_trading_bot/reports/*', 'day_trading_bot/reports'),
    ],
    hiddenimports=[
        'MetaTrader5',
        'pytz',
        'tkinter',
        'bs4',
        'scipy.signal',
        'numpy',
        'idna.idnadata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # ← or False if no terminal needed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
