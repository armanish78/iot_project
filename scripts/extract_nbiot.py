import os
import glob
import subprocess
import shutil

NBIOT_RAW = "data/datasets/nbiot_raw"
NBIOT_DIR = "data/datasets/nbiot"
ZIP_PATH = os.path.join(NBIOT_RAW, "n_baiot.zip")
SEVEN_Z_PATH = r"C:\Program Files\7-Zip\7z.exe"

def run_7z(args):
    cmd = [SEVEN_Z_PATH] + args
    subprocess.check_call(cmd)

print("Extracting main archive...")
run_7z(["x", ZIP_PATH, f"-o{NBIOT_RAW}", "-y"])

print("Extracting nested RAR files...")
for root, dirs, files in os.walk(NBIOT_RAW):
    for f in files:
        if f.endswith(".rar"):
            rar_path = os.path.join(root, f)
            print(f"Extracting {rar_path}...")
            # extract RAR. -y to overwrite.
            run_7z(["x", rar_path, f"-o{root}", "-y"])

print("Flattening CSVs to", NBIOT_DIR)
os.makedirs(NBIOT_DIR, exist_ok=True)
for root, dirs, files in os.walk(NBIOT_RAW):
    for f in files:
        if f.endswith(".csv"):
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, NBIOT_RAW)
            flatname = relpath.replace(os.sep, "__").replace(" ", "_")
            dest = os.path.join(NBIOT_DIR, flatname)
            shutil.move(filepath, dest)

print("Extraction and flattening complete.")
