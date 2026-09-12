import os
import time
import sys

URL = "https://huggingface.co/datasets/bencorn/CICIDS2017/resolve/main/pcaps/Friday-WorkingHours.pcap"
OUT = "Friday-WorkingHours.pcap"

print(f"Starting resilient download of {URL} to {OUT}")

attempts = 0
while True:
    attempts += 1
    print(f"--- Download attempt {attempts} ---")
    ret = os.system(f'curl.exe -C - -L -o {OUT} "{URL}"')
    
    if ret == 0:
        print("Download completed successfully!")
        break
    else:
        print(f"Download interrupted (curl exit code {ret}). Retrying in 5 seconds...")
        time.sleep(5)
