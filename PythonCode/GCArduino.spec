# -*- mode: python -*-

block_cipher = None


a = Analysis(['GCArduino.py'],
             pathex=['/Users/mobleyt/Documents/School My Documents/ProgrammingProjects/GC-interface/PythonCode'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=['hooks-pyinstaller'],
             runtime_hooks=['hooks-pyinstaller/pyi_rth__tkinter.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='GCArduino',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='GCArduino.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='GCArduino')
app = BUNDLE(coll,
             name='GCArduino.app',
             icon='GCArduino.icns',
             bundle_identifier=None)
