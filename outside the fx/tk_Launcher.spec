# tk_Launcher.spec
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Ensure project root is on the search path
pathex = [os.path.abspath('.')]

hidden = set()
hidden.update(['MetaTrader5', 'tkinter', 'pytz', 'scipy.signal', 'bs4', 'idna.idnadata', 'soupsieve'])
# Important: include all runtime-imported modules from your package and dateutil
hidden.update(collect_submodules('day_trading_bot'))
hidden.update(collect_submodules('dateutil'))

a = Analysis(
    ['day_trading_bot/tk_launcher.py'],
    pathex=pathex,
    binaries=[],
    datas=[
        # Bundle dashboard script so open_dashboard() can run it from MEIPASS
        ('day_trading_bot/streamlit_app.py', 'day_trading_bot'),
        # Optional data folders your bot uses
        ('day_trading_bot/data', 'day_trading_bot/data'),
        ('day_trading_bot/logs', 'day_trading_bot/logs'),
        ('day_trading_bot/reports', 'day_trading_bot/reports'),
    ],
    hiddenimports=list(hidden),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ForexBotLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # GUI app
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ForexBotLauncher'
)
