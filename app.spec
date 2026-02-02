# -*- mode: python ; coding: utf-8 -*-
import streamlit
import streamlit_option_menu
import os

# This pulls the 'static' folder from D:\call-log-management\call-log-management-main\.venv\Lib\site-packages\streamlit
st_static_path = os.path.join(os.path.dirname(streamlit.__file__), "static")
som_path = os.path.join(os.path.dirname(streamlit_option_menu.__file__), "frontend", "dist")

from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# This tells PyInstaller to grab the version and package info for streamlit
datas_metadata = copy_metadata('streamlit')

# Bundle all necessary folders and files
added_files = [
    ('.streamlit', '.streamlit'),
    (st_static_path, "streamlit/static"),  # <--- Essential for fixing the 404
    (som_path, "streamlit_option_menu/frontend/dist"), # <--- ADD THIS LINE
    ('favicon.ico', '.'),
    ('views', 'views'),
    ('utils', 'utils'),
    ('storage', 'storage'),
    ('style.css', '.'),
    ('app.py', '.'),
] + datas_metadata # <--- Append the metadata here

added_binaries = [
    ('bin/mongodump.exe', 'bin'),
    ('bin/mongorestore.exe', 'bin'),
]

a = Analysis(
    ['run_app.py'],  # Use the wrapper script as entry point
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',          # <--- ADD THIS
        'tkinter.messagebox',           # <--- ADD THIS (if you use popups)
        '_tkinter',
        'streamlit',
        'streamlit.runtime.scriptrunner.magic_funcs', # <--- ADD THIS LINE
        'pymongo',
        'dotenv',                  # <--- ADD THIS LINE
        'pandas',
        'streamlit_option_menu',
        'altair',
        'openpyxl',
        'email',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'email.mime.image',
        'smtplib', # Usually needed if you're sending emails
        'ssl',     # Usually needed for secure email connections
        'pyarrow',
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
    [],  # <--- Remove a.binaries, a.zipfiles, a.datas from here
    exclude_binaries=True, # <--- Add this
    name='CallLog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, 
    icon='favicon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CallLogManagementSystem', # This will be the name of your folder
)