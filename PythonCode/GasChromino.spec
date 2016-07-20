# -*- mode: python -*-

block_cipher = None

added_files = [
			 ('../Instructions.pdf', '.'),
			 ('../README', '.'),
			 ('../LICENSE.md', '.'),
			 ('../ArduinoCode','ArduinoCode'),
			 ('../Circuitry','Circuitry'),
			 ('../Example Data Sets', 'Example Data Sets'),
			 ('GasChromino.cfg','.'),
			 ('GCSetupDir/gcSetup','.'),
			 ('GCSetupDir/Info','.')
			 ]
a = Analysis(['GasChromino.py'],
			 pathex=['~/Documents/School\ My\ Documents/ProgrammingProjects/GC-Interface/PythonCode'],
             binaries=None,
             datas=added_files,
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
          name='GasChromino',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='GasChromino.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='GasChromino')
app = BUNDLE(coll,
             name='GasChromino.app',
             icon='GasChromino.icns',
             bundle_identifier=None)
