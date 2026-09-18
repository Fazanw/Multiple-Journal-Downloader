import os
import platform
import subprocess
import shutil

APP_NAME = "Multi_Reference_Downloader"
MAIN_SCRIPT = "main.py"

def get_customtkinter_path():
    import customtkinter
    return os.path.dirname(customtkinter.__file__)

def build():
    os_name = platform.system()
    print(f"Detected OS: {os_name}")
    print("Starting PyInstaller Build...")
    
    ctk_path = get_customtkinter_path()
    
    # Path separator for add-data is ';' on Windows, ':' on Unix
    separator = ';' if os_name == 'Windows' else ':'
    add_data_arg = f"{ctk_path}{separator}customtkinter/"
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        f"--add-data={add_data_arg}",
        f"--add-data=github_icon.png{separator}.",
        "--icon=icon.ico",
        MAIN_SCRIPT
    ]
    
    subprocess.run(cmd, check=True)
    print("PyInstaller build completed.")
    
    # OS-Specific Packaging
    dist_dir = os.path.join("dist", APP_NAME)
    
    if os_name == 'Windows':
        print("Packaging for Windows...")
        print("Use the 'installer.iss' file with Inno Setup to create the final setup.exe wizard.")
        
    elif os_name == 'Darwin':
        print("Packaging for macOS...")
        # PyInstaller creates a .app bundle on macOS inside dist/
        app_bundle = os.path.join("dist", f"{APP_NAME}.app")
        dmg_name = os.path.join("dist", f"{APP_NAME}_macOS.dmg")
        if os.path.exists(app_bundle):
            print(f"Creating DMG image: {dmg_name}")
            # Use hdiutil to create a dmg
            try:
                subprocess.run(["hdiutil", "create", "-volname", APP_NAME, "-srcfolder", app_bundle, "-ov", "-format", "UDZO", dmg_name], check=True)
                print("macOS DMG created successfully!")
            except Exception as e:
                print(f"Failed to create DMG: {e}")
                
    elif os_name == 'Linux':
        print("Packaging for Linux...")
        tar_name = os.path.join("dist", f"{APP_NAME}_Linux.tar.gz")
        if os.path.exists(dist_dir):
            import tarfile
            print(f"Creating Tarball: {tar_name}")
            with tarfile.open(tar_name, "w:gz") as tar:
                tar.add(dist_dir, arcname=APP_NAME)
            print("Linux Tarball created successfully!")

if __name__ == "__main__":
    build()
