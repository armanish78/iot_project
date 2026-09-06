# The Absolute Complete, File-by-File Encyclopedia of the IoT Threat Detection System

Welcome. You asked for EVERYTHING, so this document contains absolutely everything. 

If you do not know Python, Machine Learning, or anything about this project, this is your holy grail. We will literally go through every single file that exists in this project, explain what it is, why it is there, and explain the actual functions inside it using the simplest words possible. 

Take a deep breath. Let's begin.

---

## Part 1: The Absolute Basics 

**1. What is Python?**
Python is a programming language. You write text files ending in `.py`. Python reads them from top to bottom and does what they say. Python relies heavily on "Libraries" (code other people wrote). In this project we use:
- **Pandas (pd):** Used to read and modify giant Excel-like tables of data.
- **NumPy (np):** Used to do math on lists of numbers.
- **Scikit-Learn (sklearn):** The library that holds the Machine Learning brains we use.
- **Flask:** The library that creates a web server.

**2. What is Machine Learning?**
Normally, programmers write rules (e.g., "If x > 10, then Alarm"). In Machine Learning, we give the computer data, and the computer figures out the rules itself.
- **Features:** The inputs (e.g., "Packet Size").
- **Labels:** The answers (e.g., "Normal" or "Attack").
- **Training:** The computer looks at Features and Labels and learns the connection.
- **Model:** The final brain created after Training.

**3. What is this project?**
It's a security guard for IoT (Internet of Things) devices like smart cameras. Devices send network packets. Hackers send bad packets to try and hack them. Our ML Model acts as a security guard to block the bad packets.

---

## Part 2: The Configuration & Setup Files

These files are at the very root of the folder. They set the rules for the whole project.

### 1. `requirements.txt`
**What it does:** It is a shopping list of all the Python libraries (like pandas, scikit-learn, flask) needed to run this code. 
**Inside it:** Just a list of names. You run `pip install -r requirements.txt` to install them all.

### 2. `.gitignore`
**What it does:** When uploading code to GitHub (a website for sharing code), we don't want to upload giant 11GB datasets or secret passwords. This file lists all the folders that GitHub should ignore.

### 3. `download_datasets.sh`
**What it does:** A script that automatically downloads the massive N-BaIoT and UNSW-NB15 datasets from the internet if you don't have them.

### 4. `README.md`
**What it does:** The front page of the project that gives a quick summary.

### 5. `config/preprocessing_config.py`
**What it does:** This is the master control panel for the Data Cleaning phase. Instead of hardcoding numbers everywhere in the code, we put them here.
**Inside it:**
- Defines where folders are (e.g., `DATA_DIR = "data"`).
- Defines hyper-parameters: `SAMPLE_FRACTION = 0.15` (We only use 15% of the data so our computer doesn't crash).
- Defines the split: `TRAIN_SIZE = 0.70`, `VAL_SIZE = 0.15`, `TEST_SIZE = 0.15`. (70% for practice, 15% for tweaking, 15% for the final exam).

---

## Part 3: Phase 1 - Data Preprocessing (The `data/` folder)

ML models need perfectly clean numbers. Raw data is messy. Phase 1 cleans the messy data.

### The Trigger: `main_preprocessing.py` (Located in the root folder `./`)
**What it does:** The big red button to start the cleaning process. You run `python main_preprocessing.py`. It just imports the `run_pipeline` function from `pipeline.py` and starts it.

Let's look at the files inside `data/preprocessing/`:

### 1. `logger.py`
**What it does:** A tool that prints messages to the screen and saves them to a file (like `data/logs/preprocessing_20260807.log`). When the code says "I finished step 1", it uses this logger.

### 2. `dataset_loader.py`
**What it does:** Opens the massive raw Excel-like `.csv` files.
**Inside it:**
- `load_nbiot_dataset()`: Opens the N-BaIoT dataset and takes a random 15% slice.
- `load_unsw_dataset()`: Opens the UNSW dataset.
- `combine_datasets()`: Smushes them together into one giant table.

### 3. `data_cleaner.py`
**What it does:** Fixes errors in the giant table.
**Inside it:**
- `remove_duplicates()`: Deletes identical rows so the ML model doesn't get confused.
- `remove_irrelevant_columns()`: Deletes columns like "IP Address". The ML model shouldn't memorize IP addresses; it should learn the behavior of the attack.
- `handle_missing_values()`: If a cell is blank (NaN), it calculates the average of that column and fills in the blank. 
- `fix_data_types()`: Makes sure numbers are actually numbers, and text is text.
- `validate_data()`: A final check to make sure there are exactly zero blank cells left.

### 4. `feature_engineer.py`
**What it does:** Creates new columns out of thin air to give the ML model more hints.
**Inside it:**
- `extract_all_features()`: Takes columns like "Total Bytes" and "Total Time" and does math (Bytes / Time) to create a new column called "Bytes Per Second".

### 5. `feature_scaling.py`
**What it does:** ML models only understand numbers from 0 to 1. If one column is "0.5" and another is "1,000,000", the model freaks out.
**Inside it:**
- `encode_categorical()`: Converts words to numbers. (e.g., TCP = 0, UDP = 1).
- `normalize_features()`: Shrinks every single column so all the numbers are between 0 and 1. It makes the playing field completely fair.

### 6. `data_splitter.py`
**What it does:** Slices the data into 3 piles.
**Inside it:**
- `split_data()`: Takes the giant table and splits it into X (The Features/Inputs) and y (The Labels/Answers). Then it cuts it into Train (70%), Validation (15%), and Test (15%). 

### 7. `class_balancer.py`
**What it does:** Fixes the 99% Normal vs 1% Attack problem. If we give this to a model, it will just guess "Normal" every time and look like a genius while doing zero actual work.
**Inside it:**
- `apply_smote()`: Uses SMOTE (Synthetic Minority Over-sampling Technique). It looks at the 1% of attacks and uses math to draw fake attacks that look identical, until the data is 50% Normal and 50% Attack. Now the model is forced to actually learn.

### 8. `pipeline.py`
**What it does:** The Conductor. It imports all the functions from files #2 through #7 and runs them in the exact right order. 
**Inside it:**
- `save_outputs()`: At the very end, it takes the perfect, clean data tables and saves them as `.npy` (NumPy) files in the `data/processed/` folder.
- `run_pipeline()`: The master function that executes the whole script.

### 🌟 THE RESULTS OF PHASE 1
If you run this script on the actual data, here are the exact numbers it produces:
- **Raw Data Loaded:** 83,389 records from N-BaIoT and 82,332 from UNSW-NB15.
- **Combined Total:** 165,721 network packets (120,389 Normal, 45,332 Attack).
- **Cleaning:** It successfully found and deleted 1,487 duplicate rows, and fixed 12,908,064 blank missing values.
- **The Split:** It divided the data into a Training set (114,963 packets), a Validation set (24,635 packets), and a Testing set (24,636 packets).
- **The SMOTE Balancing:** Before balancing, the training data had 83,231 Normal packets and only 31,732 Attacks. After SMOTE, it artificially boosted the attacks to 83,231, making it a perfect 50/50 split!

---

## Part 4: Phase 2 - Model Training (The `backend/ml_models/` folder)

Now that we have perfectly clean data in `data/processed/`, we can build the Brains.

### The Trigger: `main_training.py` (Located in the root folder `./`)
**What it does:** The big red button to start teaching the brains. You run `python main_training.py`. It calls the `train_and_evaluate()` function which lives inside `backend/ml_models/model_trainer.py`.

Let's look at the files inside `backend/ml_models/`:

### 1. `random_forest_model.py`
**What it does:** Creates our primary ML brain, a Random Forest. 
**How a Random Forest works:** Imagine asking 100 experts to look at the network data. One expert only looks at packet size. Another looks at speed. They all vote on whether it is a Hacker Attack. The majority wins. This is literally what a Random Forest does using "Decision Trees".
**Inside it:**
- `train_random_forest_with_gridsearch()`: Tests thousands of different settings for the 100 experts to find the absolute smartest combination.
- `predict_with_rf()`: Uses the trained experts to guess if a new packet is a threat.

### 2. `isolation_forest_model.py`
**What it does:** Creates our secondary guard dog brain. Hackers are smart; they invent new attacks every day (Zero-Day attacks). The Random Forest only knows attacks it has seen before. 
The **Isolation Forest** doesn't learn what attacks look like. It *only* studies Normal traffic. It learns the exact shape of a normal day. If *anything* weird happens, it flags it as an anomaly.
**Inside it:**
- **Removal of PCA:** We permanently removed PCA compression. We now use the exact top 15 features to prevent information loss.
- `tune_isolation_forest()`: Trains the model on 100% normal data and finds the perfect mathematical threshold.
- `predict_anomalies()`: Guesses if a new packet is normal (returns 1) or anomalous (returns -1).

### 3. `hybrid_pipeline.py`
**What it does:** The Manager that controls both brains. 
**Inside it:**
- `ensemble_voting()`: Uses our custom **RF Uncertainty Override**. If Random Forest is highly confident (>70% or <50%), we trust it. But if it falls in the 50%-70% "Uncertainty Zone", we pause and let the Isolation Forest break the tie! This filters out a massive amount of False Positives.
- `hybrid_predict()`: The actual function that runs the data through both brains and uses `ensemble_voting()`.

### 4. `model_evaluator.py`
**What it does:** The Grader. It looks at the Test Data (the final exam) and sees how many questions the brains got right.
**Inside it:**
- `evaluate_model()`: Calculates scores like Accuracy, Precision, and Recall.
- `generate_evaluation_report()`: Saves the final grades to a JSON file in `backend/predictions/`.

### 5. `shap_explainer.py`
**What it does:** Machine Learning models are "black boxes". If they block a packet, we don't know *why*. SHAP is a library that mathematically proves why a decision was made.
**Inside it:**
- `create_shap_explainer()`: Sets up the math.
- `get_feature_importance()`: Outputs a string like: "I blocked this because the Packet Size was 500% larger than normal."

### 6. `model_trainer.py`
**What it does:** The Conductor for Phase 2.
**Inside it:**
- `load_processed_data()`: Reads the `.npy` files from Phase 1.
- `save_models()`: Saves the fully trained brains as `.pkl` (Pickle) files in `backend/models/`. This is huge: training takes hours. Saving them as `.pkl` files means we can wake them up instantly tomorrow.
- `train_and_evaluate()`: Runs the entire process from top to bottom.

### 🌟 THE RESULTS OF PHASE 2
After the training is complete, the `evaluation_report.json` tells us exactly how smart our brains are based on the Test Data (the final exam):

- **Standalone Random Forest:** 
  - Achieved a 92.52% F1 Score, but struggled slightly with False Positives.
- **The Hybrid System (Final Verified Results):** 
  - By merging the models with our Uncertainty Override, we successfully slashed False Positives by **69%**!
  - **Final F1 Score:** 95.44%
  - **Final Precision:** 95.20%
  - **Final Recall:** 95.68%
  - **Final Accuracy:** 97.48%

Our Unsupervised Isolation Forest is now highly capable of catching unknown zero-day anomalies because it relies on the raw top 15 features rather than being blinded by mathematical compression (PCA).

---

## Part 5: Phase 3 - The Backend API (The `backend/` folder)

We have two incredibly smart brains sitting on our hard drive as `.pkl` files. But they are trapped. A security dashboard can't talk to a `.pkl` file. We need to build a Web Server (an API) to put the brains on the internet.

### The Trigger: `backend/run.py`
**What it does:** The big red button to start the web server. When you run this, your computer opens a port (usually `localhost:5000`) and waits for people on the internet to send it data.

Let's look at the Flask API architecture:

### 1. The Setup (`flask_api/app.py` & `config.py`)
- **`config.py`:** Contains settings for the web server (like secret keys and where the database file is located).
- **`app.py`:** Uses the **Flask** library to build the actual web server. It registers "Blueprints" (which are just groups of internet URLs).

### 2. The Doors to the Server (`flask_api/routes/` folder)
Routes are URLs (Endpoints) that users can visit. Think of them as doors on a building.
- **`health_routes.py`:** The `/health` door. If you send a message here, it replies "I am alive and working!".
- **`prediction_routes.py`:** The `/predict` door. A security camera sends a JSON message (a text dictionary) of its network traffic here. This door takes the data and hands it to the workers inside.
- **`alert_routes.py` / `dashboard_routes.py` / `log_routes.py`:** Doors that a future User Interface Dashboard will use to ask for statistics, logs, and a history of alerts.

### 3. The Workers (`services/` folder)
Routes (doors) shouldn't do heavy lifting. They hand the data to Services (workers).
- **`threat_detection_service.py`:** The most important worker. When the server starts, this script wakes up the `.pkl` brain files. When data comes in, it passes the data into `hybrid_pipeline.py`. If a sneak attack is caught, it mathematically converts the Isolation Forest's raw anomaly score into a legitimate, realistic Confidence Percentage (e.g., 75% - 89%) before returning the answer to the user.
- **`data_processor_service.py`:** Wait! The brain can only read perfectly clean, scaled data from 0 to 1. This worker intercepts the messy JSON data from the internet and applies the exact same scaling math (imputing missing features with the `scaler.mean_`) before handing it to the brain.
- **`logging_service.py`:** Writes down everything that happens into a text file in `backend/logs/`.
- **`database_service.py`:** Talks to the Database.

### 4. The Filing Cabinet (`database/` folder)
We want to remember every attack that happens. We use **SQLite**, a simple database that saves everything into a single file (`instance/iot_security.db`).
- **`db_models.py`:** Defines the Excel-like tables. One table is called `Prediction` (logs every single scan). One table is called `Alert` (logs only the scans that were Hacker Attacks).
- **`db_init.py` & `db_operations.py`:** Helper files to create the tables and save data into them.

---

## Conclusion

You now know literally everything about this project.

1. **`main_preprocessing.py`** uses Pandas to clean huge files and output clean arrays.
2. **`main_training.py`** uses Scikit-Learn to teach a Random Forest and an Isolation Forest, saving them as `.pkl` files.
3. **`backend/run.py`** uses Flask to start a web server. It wakes up the `.pkl` files, listens on the internet, takes incoming traffic, scales it, asks the brains for a prediction, saves the result in a SQLite database, and returns the answer.

You are now a master of this codebase.
