import os
import sys
import glob
import shutil
import zipfile
import urllib.request
import subprocess

PROJECT_DIR = "."
DATASETS_DIR = os.path.join(PROJECT_DIR, "data", "datasets")
NBIOT_RAW = os.path.join(DATASETS_DIR, "nbiot_raw")
UNSW_RAW = os.path.join(DATASETS_DIR, "unsw_raw")
NBIOT_DIR = os.path.join(DATASETS_DIR, "nbiot")

def main():
    print("Installing required python packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "kaggle", "patool"])
    import patoolib

    os.makedirs(DATASETS_DIR, exist_ok=True)

    print("======================================")
    print("Downloading UNSW-NB15...")
    print("======================================")
    os.makedirs(UNSW_RAW, exist_ok=True)
    subprocess.check_call([sys.executable, "-m", "kaggle", "datasets", "download", "-d", "mrwellsdavid/unsw-nb15", "-p", UNSW_RAW, "--unzip"])

    train_files = glob.glob(os.path.join(UNSW_RAW, "*training*.csv"))
    if train_files:
        shutil.copy(train_files[0], os.path.join(DATASETS_DIR, "unsw_nb15.csv"))
    else:
        all_csvs = glob.glob(os.path.join(UNSW_RAW, "*.csv"))
        if all_csvs:
            shutil.copy(all_csvs[0], os.path.join(DATASETS_DIR, "unsw_nb15.csv"))
    
    print(f"UNSW-NB15 ready at {os.path.join(DATASETS_DIR, 'unsw_nb15.csv')}")

    print("======================================")
    print("Downloading N-BaIoT (1.7GB) - This will take several minutes...")
    print("======================================")
    os.makedirs(NBIOT_RAW, exist_ok=True)
    os.makedirs(NBIOT_DIR, exist_ok=True)
    
    zip_path = os.path.join(NBIOT_RAW, "n_baiot.zip")
    if not os.path.exists(zip_path):
        urllib.request.urlretrieve("https://archive.ics.uci.edu/static/public/442/detection+of+iot+botnet+attacks+n+baiot.zip", zip_path)

    print("Unzipping main N-BaIoT archive...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(NBIOT_RAW)

    print("Extracting nested .rar files using patool...")
    for root, dirs, files in os.walk(NBIOT_RAW):
        for f in files:
            if f.endswith('.rar'):
                rar_path = os.path.join(root, f)
                print(f"Extracting {rar_path}...")
                try:
                    patoolib.extract_archive(rar_path, outdir=root)
                except Exception as e:
                    print(f"Error extracting {rar_path}: {e}")

    print("Extracting any nested .zip files...")
    for root, dirs, files in os.walk(NBIOT_RAW):
        for f in files:
            if f.endswith('.zip') and f != "n_baiot.zip":
                zpath = os.path.join(root, f)
                try:
                    with zipfile.ZipFile(zpath, 'r') as zip_ref:
                        zip_ref.extractall(root)
                except Exception as e:
                    print(f"Error extracting {zpath}: {e}")

    print("Flattening CSV files into datasets/nbiot/...")
    for root, dirs, files in os.walk(NBIOT_RAW):
        for f in files:
            if f.endswith('.csv'):
                filepath = os.path.join(root, f)
                relpath = os.path.relpath(filepath, NBIOT_RAW)
                flatname = relpath.replace(os.sep, "__").replace(" ", "_")
                shutil.copy(filepath, os.path.join(NBIOT_DIR, flatname))

    print("Cleaning up raw files...")
    shutil.rmtree(NBIOT_RAW, ignore_errors=True)
    shutil.rmtree(UNSW_RAW, ignore_errors=True)

    print("======================================")
    print("All downloads and extractions complete!")
    print("======================================")

if __name__ == "__main__":
    main()
