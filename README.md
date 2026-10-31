# air-quality-predictor
# 🌫️ Air Quality Health Alert Predictor (India)

**Author:** Gurnoor Kaur
**Tools:** Python, pandas, scikit-learn, statsmodels, Streamlit, Plotly

An end-to-end predictive analytics project that warns people a day in advance when the air in their city is going to be unhealthy. Using daily pollution readings from Indian cities, the model predicts whether **tomorrow's Air Quality Index (AQI) will be 201 or higher**, which the Central Pollution Control Board (CPCB) classes as *Poor*, *Very Poor* or *Severe*. The project covers the full workflow from raw data to a working, interactive dashboard where anyone can type in today's readings and get tomorrow's health alert.

---

## 1. Problem statement

Air pollution is one of India's biggest public-health risks. On Poor or worse days, children, older people and people with asthma or heart conditions are advised to stay indoors, wear masks and avoid outdoor exercise. AQI is usually reported for *today*, which is too late to plan around.

**Goal:** given today's pollutant readings for a city, predict whether tomorrow will be a Poor-or-worse air day.

- **Type of problem:** binary classification (with extra time-series forecasting and count modelling)
- **Target:** `1` if tomorrow's AQI ≥ 201, otherwise `0`
- **Who benefits:** citizens, schools, hospitals and city authorities who need a one-day warning
- **Ethics:** the data is public and contains no personal information. Because missing a bad-air day is more harmful than a false alarm, the model is judged on F1 and recall, not accuracy alone, and the alert threshold can be tuned in the dashboard.

## 2. Dataset

- **Source:** [Air Quality Data in India (2015 to 2020)](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india) on Kaggle, compiled from CPCB public data
- **File used:** `city_day.csv`, one row per city per day
- **Columns:** City, Date, 12 pollutants (PM2.5, PM10, NO, NO2, NOx, NH3, CO, SO2, O3, Benzene, Toluene, Xylene), AQI and AQI_Bucket

## 3. Methodology (12 stages)

The full workflow is in `AirQuality_Predictor.ipynb`, organised into the 12 stages

| Stage | What was done |
|---|---|
| 1. Problem definition and ethics | Defined the target (tomorrow's AQI ≥ 201), stakeholders and ethical points |
| 2. Data collection | Loaded `city_day.csv` (or the practice copy) and inspected shape, types and coverage |
| 3. Preprocessing | Removed duplicates. Filled short gaps in pollutant readings by interpolation within each city (up to 7 days), then with the city median. Filled only tiny AQI gaps (up to 2 days) and dropped the rest. Capped outliers at 3 × IQR per city, checked with box plots |
| 4. EDA | Mean, median, mode, variance, standard deviation and z-scores for each pollutant |
| 5. Visualisation | Bar chart, histogram, pie chart, correlation heatmap and scatter plots |
| 6. Feature engineering and selection | Created the target and new features (see below). Removed near-duplicate features (correlation above 0.95), then kept the 15 strongest with `SelectKBest` (ANOVA F-test). Scaling is done with `StandardScaler` inside each model pipeline, fitted on training data only |
| 7. Modelling | Logistic Regression, Linear Discriminant Analysis (LDA) and Quadratic Discriminant Analysis (QDA) |
| 8. Validation | Chronological train/test split (train before 1 July 2019, test after) and 5-fold `TimeSeriesSplit` cross-validation, so the model never learns from the future |
| 9. Metrics | Accuracy, precision, recall, F1, ROC AUC and confusion matrix |
| 10. Hyperparameter tuning | `GridSearchCV` and `RandomizedSearchCV` over regularisation strength (C), penalty and class weights |
| 11. Overfitting vs underfitting | Compared train and test scores for a deliberately underfit model, an overfit model and the tuned model, plus learning curves |
| 12. Conclusion | Picked the best model and saved it to `outputs/best_model.pkl` for the dashboard |

### Engineered features

| Feature | Meaning |
|---|---|
| `AQI_lag1` | Yesterday's AQI |
| `AQI_roll3`, `AQI_roll7` | Average AQI over the last 3 and 7 days |
| `AQI_change` | Today's AQI minus yesterday's (is pollution rising or falling?) |
| `PM_ratio` | PM2.5 ÷ PM10 (fine dust vs coarse dust) |
| `month_sin`, `month_cos` | Month encoded as a circle, so December sits next to January |
| `is_weekend` | 1 on Saturday and Sunday |
| `Season_*`, `City_*` | One-hot encoded season (Winter, Summer, Monsoon, Post-monsoon) and city |

### Extra models

- **SARIMA** and **Holt-Winters exponential smoothing** forecast monthly average AQI for the next 6 months
- **Poisson regression (GLM)** models the number of Poor-air days per city per month, showing how much winter, the monsoon and a city's general pollution level raise or lower the count

## 4. Results

On the real CPCB data, the **tuned Logistic Regression** model performed best:

| Metric | Score |
|---|---|
| F1 score | **0.852** |
| ROC AUC | **0.985** |

- The most important predictors were **PM2.5** and **today's AQI**, which makes sense: bad air tends to persist from one day to the next.
- Logistic Regression beat LDA and QDA while staying simple and easy to explain.
- Train and test scores were close, so the model is not overfitting.

## 5. Interactive dashboard

The Streamlit app (`app/app.py`) walks through the whole project in 16 pages with tabs and next/previous buttons, on an air-themed design (misty hills, drifting haze and AQI colours).

- **Stage pages (Problem to Verdict):** every stage above, with its tables and interactive Plotly charts
- **Results Lab:** ROC curve, precision-recall curve, threshold tuner, learning curves, calibration plot and errors by city
- **Forecast:** SARIMA and Holt-Winters forecasts and the Poisson model
- **Predict:**
  - *Today:* type in today's pollutant readings and get tomorrow's alert with its probability
  - *Replay a past day:* pick a city and date from the test period and compare the prediction with what actually happened

## 6. How to run

**Requirements:** Python 3.10 or newer

1. Clone the repository and open the folder:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```
2. Install the libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Get the data. Download `city_day.csv` from the Kaggle link above and put it in `data/`, **or** create the practice copy:
   ```bash
   python data/make_sample_data.py
   ```
4. Run the pipeline. This cleans the data, trains and tunes the models, and saves results to `outputs/`:
   ```bash
   python pipeline.py
   ```
   (Or open `AirQuality_Predictor.ipynb` in Jupyter and run all cells.)
5. Start the dashboard:
   ```bash
   streamlit run app/app.py
   ```
   It opens in your browser at `http://localhost:8501`.

## 7. Project structure

```
├── app/
│   ├── app.py                  # Streamlit dashboard
│   ├── style.py                # Dashboard theme and styling
│   └── assets/wallpaper.jpg    # Background image
├── data/
│   └── make_sample_data.py     # Creates a practice copy of city_day.csv
├── screenshots/                # Dashboard screenshots used in this README
├── AirQuality_Predictor.ipynb  # Full analysis as a Jupyter notebook
├── requirements.txt            # Python libraries
└── README.md
outputs also included

## 8. Limitations and future work

- Uses only pollutant readings; adding weather data (wind speed, temperature, humidity, rainfall) would likely improve predictions.
- Data covers 2015 to 2020 and needs retraining on newer data before real use.
- Predicts one day ahead only; multi-day forecasts would give more warning.
- Could be connected to a live CPCB data feed for automatic daily alerts.

## 9. Acknowledgements

- Dataset: Vopani (Rohan Rao), *Air Quality Data in India*, Kaggle, based on CPCB data
- Course: CSE3141 Predictive Analytics, Manipal University Jaipur
