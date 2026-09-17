# ChrunAI — Customer Churn Prediction Agent

Predict telco customer churn, segment risk, explain drivers, and suggest retention actions. Built for a hackathon-style demo: **train once**, **score everyone**, **explore in Streamlit**.

**Dataset:** IBM Telco Customer Churn (`data/telco_customer_churn.csv`, ~7,043 customers).

---

## What it does

| Capability | How |
|------------|-----|
| **Data processing** | Clean `TotalCharges`, encode categoricals, impute numerics |
| **Churn classification** | Binary label: Stay (`No`) vs Churn (`Yes`) |
| **Churn probability** | `predict_proba` per customer (0–1) |
| **Risk segmentation** | Low / Medium / High / Critical from probability thresholds |
| **Feature importance** | Global Random Forest importances in Overview |
| **High-risk customers** | Filter and sort by probability in the app |
| **Retention recommendations** | Rule-based actions + optional **Gemini** polish on lookup |

---

## Tech stack

| Layer | Tools |
|-------|--------|
| **ML** | Python, pandas, scikit-learn, joblib |
| **Model** | `RandomForestClassifier` (100 trees, `random_state=42`) |
| **UI** | Streamlit |
| **LLM** | Google Gemini (`gemini-3.6-flash`) via `google-generativeai` |

---

## Machine learning pipeline

### 1. Cleaning (`train.py`)

- Drop `customerID` from features (used only for lookup).
- `TotalCharges`: coerce to numeric; missing values filled with `tenure × MonthlyCharges`, then median if still missing.
- Target: `Churn` → `1` if `Yes`, else `0`.

### 2. Features

- **Numeric:** `SeniorCitizen`, `tenure`, `MonthlyCharges`, `TotalCharges`
- **Categorical:** gender, contract, payment method, internet/add-ons, etc. (15 columns)

### 3. Preprocessing + model (single `sklearn` `Pipeline`)

```
ColumnTransformer
  ├── Numeric  → SimpleImputer (median)
  └── Categorical → OneHotEncoder (handle_unknown=ignore)
        ↓
RandomForestClassifier(n_estimators=100)
```

### 4. Training

- **Split:** 80% train / 20% test, stratified on churn.
- **No live retraining in the app** — run `train.py` locally, then load artifacts in Streamlit.

### 5. Holdout metrics (example run)

| Metric | Value |
|--------|-------|
| Accuracy | ~0.79 |
| ROC-AUC | ~0.82 |
| Dataset churn rate | ~26.5% |

### 6. Risk tiers (probability `p`)

| Tier | Condition |
|------|-----------|
| Low | p < 0.30 |
| Medium | 0.30 ≤ p < 0.55 |
| High | 0.55 ≤ p < 0.75 |
| Critical | p ≥ 0.75 |

After training, **every row** in the dataset is scored and saved to `scored_customers.csv` (probability, prediction, tier).

### 7. Artifacts

| File | Purpose |
|------|---------|
| `model.joblib` | Full fitted pipeline |
| `scored_customers.csv` | All customers + scores (app reads this) |
| `metrics.json` | Holdout accuracy, AUC, confusion matrix |
| `feature_importance.json` | Top encoded features for charts |

These generated files are gitignored; recreate them with `python train.py`.

---

## Retention logic (`recommend.py`)

**Rules (always on):** e.g. month-to-month contract → loyalty offer; electronic check → auto-pay incentive; short tenure → onboarding call; fiber without security/support → bundle; high monthly charges → plan review.

**Gemini (optional):** On Customer lookup, **Generate recommendation** sends customer context + rule list to Gemini for a short bullet retention plan. If the API fails or no key is set, the UI shows rules only.

**Per-customer “why”:** Heuristic hints (contract, payment, tenure, add-ons, charges) — no SHAP, tuned for speed and reliability.

---

## Streamlit app (`app.py`)

Three tabs:

1. **Overview** — churn rate, charts (contract / tenure), global feature importance, model AUC.
2. **Scoring & high risk** — full scored table; toggle High + Critical; download CSV.
3. **Customer lookup** — pick `customerID`, see probability, tier, hints, rules, Gemini button.

---

## Quick start

```bash
git clone https://github.com/cryoxyl-beep/ChrunAI.git
cd ChrunAI
python -m pip install -r requirements.txt
python train.py
streamlit run app.py
```

Open **http://localhost:8501** (or the port Streamlit prints).

**Gemini (optional):** set `GEMINI_API_KEY` in the environment or paste the key in the sidebar.

---

## Project layout

```
ChrunAI/
├── data/telco_customer_churn.csv
├── train.py           # Train model + write artifacts
├── recommend.py       # Rules + Gemini helper
├── app.py             # Streamlit UI
├── requirements.txt
└── README.md
```

---

## Demo flow (judges)

1. Overview → churn rate + contract/tenure insight + AUC.
2. Scoring & high risk → top Critical customers by probability.
3. Customer lookup → rehearsed ID → rules → **Generate recommendation**.
4. Download scored CSV for ops handoff.

---

## License

Hackathon / educational use. Telco dataset is the public IBM Telco Customer Churn dataset.
