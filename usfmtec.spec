# -*- mode: python ; coding: utf-8 -*-
block_cipher = None


a = Analysis(['scripts\\sfm\\usfmtec'],
             pathex=['C:\\Users\\IEUser\\palaso-python'],
             binaries=[('..\\AppData\\Local\\Programs\\Python\\Python38-32\\TECkit_x86.dll', '.'),
	     	       ('..\\AppData\\Local\\Programs\\Python\\Python38-32\\TECkit_Compiler_x86.dll', '.'),
	     	       ('..\\AppData\\Local\\Programs\\Python\\Python38-32\\libgcc_s_sjlj-1.dll', '.'),
		       ('..\\AppData\\Local\\Programs\\Python\\Python38-32\\libstdc++-6.dll', '.')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'asyncio', 'lib2to3', 'email'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='usfmtec',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
