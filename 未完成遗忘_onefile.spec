# -*- mode: python ; coding: utf-8 -*-
# 单文件（onefile）版本：产出一个独立 exe，运行时会自解压到临时目录 _MEIPASS。
# 资源(assets)经 __file__ 相对定位可命中 _MEIPASS/assets；
# 用户数据(PROJECT_DIR)在 frozen 时取 exe 同目录，持久化安全。

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['PyQt5.QtSvg', 'PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='未完成遗忘',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon_std.ico'],
)
