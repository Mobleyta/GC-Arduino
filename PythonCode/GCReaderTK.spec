# -*- mode: python -*-

block_cipher = None


a = Analysis(['GCReaderTK.py'],
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
          name='GCReaderTK',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='GCReaderTK')
app = BUNDLE(coll,
             name='GCReaderTK.app',
             icon=None,
             bundle_identifier=None)
