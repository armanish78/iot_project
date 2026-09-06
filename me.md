# Simulation Guide: How to Show This Project is Working

This document is your cheat sheet for presenting this project to your guide or mentor. It tells you exactly what to say and what to run to prove the system works.

## Step 0: Activate the Virtual Environment
Before running *any* Python commands below, you MUST activate the virtual environment so you have access to all the installed libraries (like `requests`, `numpy`, and `Flask`).
Run this exact command in your terminal:
```bash
source venv/bin/activate
```
*(You will know it worked when your terminal prompt starts with `(venv)`).*

## Step 1: Show the Documentation
Before running any code, open `doc.md` and `phase2.docx`. 
**What to say:** *"First, I want to show you the documentation. `doc.md` maps out every single file in this project from raw data to the Flask API. I also created `phase2.docx`, which details our exact machine learning process, how we tuned the hyper-parameters, and how we engineered our custom Hybrid Uncertainty Override to push the F1 score to 95.44%."*

## Step 2: Show the Data Preprocessing
Run this command in your terminal:
```bash
./venv/bin/python main_preprocessing.py
```
**What to say:** *"This script reads the raw 11GB datasets (N-BaIoT and UNSW-NB15). It drops irrelevant columns like IP addresses, fixes millions of missing values, normalizes the features to a 0-1 scale, and most importantly, it uses SMOTE to balance the classes so the machine learning model doesn't just guess 'Normal' every time. The clean data is saved as Numpy arrays."*

## Step 3: Show the Model Training
Run this command in your terminal:
```bash
./venv/bin/python main_training.py
```
*(Note: This might take a few minutes to run).*
**What to say:** *"Now we train the brains. We train a Random Forest to catch known attacks, and an unsupervised Isolation Forest to act as a guard dog for unknown 'zero-day' anomalies. We removed PCA and passed the top 15 raw features directly into the Isolation forest. The script tunes the hyper-parameters, saves the brains as `.pkl` files, and generates a final report."*

When it finishes, open `backend/predictions/evaluation_report.json`.
**What to say:** *"Here are the final test scores evaluated on an untouched holdout set. As you can see, our custom Hybrid Model achieved an incredibly high **95.44% F1 score** and **95.20% Precision**, vastly outperforming the individual models by eliminating false positives."*

## Step 4: Show the Live API Server
We need to prove the brains can talk to the internet.
Start the server by running:
```bash
./venv/bin/python backend/run.py
```
**What to say:** *"The models are now loaded into memory, and a Flask API is listening on port 5000."*

Leave the server running. Open a **new, second terminal window** and run a simple health check:
```bash
curl http://localhost:5000/api/health/status
```
**What to say:** *"The server is alive and responding."*

## Step 5: Show a Live Test Case
While the server is still running, you can prove that the API is actively scanning traffic by throwing a fake packet at it. Run this Python script which sends a suspicious test packet to your API:

```bash
./venv/bin/python test_api.py
```

**What to say:** *"I just ran a script to send a live, suspicious network packet to the API. As you can see printed in the terminal, it instantly ran through the models, generated a confidence score, and returned a full JSON threat analysis report."*

## Advice & Things to Keep in Mind
- **The Hybrid Pipeline is the star:** Make sure you emphasize `backend/ml_models/hybrid_pipeline.py`. It's not just a standard ML project. Explain the **RF Uncertainty Override**: If the Random Forest is highly confident (e.g. 90%), we trust it. But if the Random Forest is confused (between 50% and 70% confidence), we trigger the Isolation Forest anomaly score to break the tie. This veto system slashed our false positive rate by 69%!
- **Explainability (SHAP):** Mention `shap_explainer.py`. Explain that the system doesn't just block packets blindly; it calculates the SHAP values to explain *why* it blocked a packet (e.g., "Packet size was too large"). 
- **The Database:** Mention that every scan is logged in a SQLite database (`instance/iot_security.db`) so a system admin can view the history of attacks later.
