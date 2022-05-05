#!/usr/bin/env python3
import os.path
import subprocess
import sys
import tempfile
import urllib.request
import glob

DLL_NAME = "ucrtbase.dll"
EXE_NAME = "vc_redist.x64.exe"
VC_REDIST_URL = f"https://download.microsoft.com/download/0/6/4/064F84EA-D1DB-4EAA-9A5C-CC2F0FF6A638/{EXE_NAME}"

STEAMAPPS_LOCATIONS = list(map(os.path.expanduser, [
    "~/.steam/debian-installation/steamapps",  # Ubuntu package 'steam-installer'
    "~/.local/share/Steam/steamapps",  # Location I got from another script on "the internet"
]))

SYSTEM32_LOCATIONS = [
    "compatdata/*/pfx/drive_c/windows/system32/",
]


class Cwd(object):
    """Sets the cwd within the context"""
    def __init__(self, path: str):
        self.path = path
        self.origin = os.getcwd()

    def __enter__(self):
        os.chdir(self.path)

    def __exit__(self, *args):
        os.chdir(self.origin)


def check_cabextract():
    try:
        subprocess.run(["cabextract", "--version"], check=True)
    except FileNotFoundError:
        print("Could not execute 'cabextract. Is it installed?'", file=sys.stderr)
        sys.exit(1)


def find_system32s():
    for steam_location in STEAMAPPS_LOCATIONS:
        for system32_location in SYSTEM32_LOCATIONS:
            yield from glob.glob(os.path.join(steam_location, system32_location))

def find_ucrtbase_dll_symlinks():
    for system32_location in find_system32s():
        path = os.path.join(system32_location, DLL_NAME)
        if os.path.exists(path) and os.path.islink(path):
            yield path

def find_missing_ucrtbase_dll():
    for system32_location in find_system32s():
        path = os.path.join(system32_location, DLL_NAME)
        if (not os.path.exists(path)) or os.path.islink(path):
            yield path
        else:
            print(f">>> Already installed: {path}")


def install_dlls():
    dlls = list(find_missing_ucrtbase_dll())
    if dlls:
        dll = get_dll()
        for missing_lib in find_missing_ucrtbase_dll():
            new = missing_lib + ".new"
            with open(new, "wb") as fp:
                print(f">>> Writing {missing_lib}..")
                fp.write(dll)
            os.rename(new, missing_lib)


def get_dll():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with Cwd(tmp_dir):
            print(f">>> Downloading {VC_REDIST_URL}..")
            urllib.request.urlretrieve(VC_REDIST_URL, EXE_NAME)
            print(f">>> Extracting {EXE_NAME}..")
            subprocess.run(["cabextract", EXE_NAME, "--filter", "a10"], check=True, stdout=subprocess.PIPE)
            print(f">>> Extracting {DLL_NAME}..")
            subprocess.run(["cabextract", "a10", "--filter", DLL_NAME], check=True, stdout=subprocess.PIPE)
            return open(DLL_NAME, "rb").read()

if __name__ == '__main__':
    check_cabextract()
    install_dlls()
