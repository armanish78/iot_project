#!/bin/bash
set -e

PROJECT_DIR="."
DATASETS_DIR="$PROJECT_DIR/data/datasets"

cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

echo "Installing required python packages..."
pip install --quiet kaggle patool

mkdir -p "$DATASETS_DIR"
cd "$DATASETS_DIR"

echo "======================================"
echo "Downloading UNSW-NB15..."
echo "======================================"
# Ensure Kaggle credentials are provided via environment variables or ~/.kaggle/kaggle.json
mkdir -p unsw_raw
kaggle datasets download -d mrwellsdavid/unsw-nb15 -p unsw_raw --unzip

TRAIN_FILE=$(find unsw_raw -type f -name "*training*.csv" | head -n 1)
if [ -n "$TRAIN_FILE" ]; then
    cp "$TRAIN_FILE" "unsw_nb15.csv"
else
    FIRST_CSV=$(find unsw_raw -type f -name "*.csv" | head -n 1)
    cp "$FIRST_CSV" "unsw_nb15.csv"
fi
echo "UNSW-NB15 ready at data/datasets/unsw_nb15.csv"

echo "======================================"
echo "Downloading N-BaIoT (1.7GB) - This will take several minutes..."
echo "======================================"
mkdir -p nbiot_raw
mkdir -p nbiot
wget -q -O nbiot_raw/n_baiot.zip "https://archive.ics.uci.edu/static/public/442/detection+of+iot+botnet+attacks+n+baiot.zip"

echo "Unzipping main N-BaIoT archive..."
unzip -q -o nbiot_raw/n_baiot.zip -d nbiot_raw

echo "Extracting nested .rar files using patool..."
python -c "
import os, glob
import patoolib
for root, dirs, files in os.walk('nbiot_raw'):
    for f in files:
        if f.endswith('.rar'):
            rar_path = os.path.join(root, f)
            print(f'Extracting {rar_path}...')
            try:
                patoolib.extract_archive(rar_path, outdir=root)
            except Exception as e:
                print(f'Error extracting {rar_path}: {e}')
"

echo "Extracting any nested .zip files..."
find nbiot_raw -type f -name "*.zip" ! -name "n_baiot.zip" -execdir unzip -q -o {} -d . \;

echo "Flattening CSV files into datasets/nbiot/..."
find nbiot_raw -type f -name "*.csv" | while read -r filepath; do
    relpath="${filepath#nbiot_raw/}"
    flatname="${relpath//\//__}"
    flatname="${flatname// /_}"
    cp "$filepath" "nbiot/$flatname"
done

echo "Cleaning up raw files..."
rm -rf nbiot_raw unsw_raw

echo "======================================"
echo "All downloads and extractions complete!"
echo "You can now run: source venv/bin/activate && python main_preprocessing.py"
echo "======================================"
