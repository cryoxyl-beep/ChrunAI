# ChrunAI

**Customer churn prediction agent** — train on telecom data, score risk, find who might leave, and get retention ideas. Built for hackathons; runs locally with **Streamlit**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-Educational-lightgrey)](LICENSE)

**Topics:** `customer-churn` · `telecom` · `machine-learning` · `random-forest` · `streamlit` · `hackathon` · `retention` · `groq` · `gemini`

---

## What you get (Problem 3 checklist)

| Requirement | In this repo |
|-------------|----------------|
| Customer data processing | CSV clean + sklearn pipelines per dataset |
| Churn classification | Yes / No prediction |
| Churn probability | 0–1 score per customer |
| Risk segmentation | Low → Critical tiers |
| Feature importance | Charts in **Overview** |
| High-risk customers | **Scoring** tab (High + Critical) |
| Retention recommendations | Rules + optional **Gemini** & **Groq** LLMs |

---

## Quick start (3 steps)

```powershell
git clone https://github.com/cryoxyl-beep/ChrunAI.git
cd ChrunAI
python -m pip install -r requirements.txt
```

**Train** (once per dataset you use):

```powershell
python train.py      # IBM Telco (included in data/)
python train2.py     # Singtel — needs Kaggle CSV in data/singtel/
python train3.py     # Mnassrib BigML — data/mnassrib/
```

**Run the app:**

```powershell
streamlit run app.py
```

Open the URL shown (e.g. `http://localhost:8501`).

**Stop the app:** `Ctrl+C` in that terminal, or kill the port:

```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8501 -State Listen).OwningProcess -Force
```

---

## Datasets (3 separate models)

Each dataset has its **own** model — columns are not mixed.

| Name in app | Train command | Data path |
|-------------|---------------|-----------|
| IBM Telco | `train.py` | `data/telco_customer_churn.csv` |
| Singtel | `train2.py` | `data/singtel/Telecom Churn Data SingTel.csv` |
| Mnassrib BigML | `train3.py` | `data/mnassrib/churn-bigml-80.csv` (+ optional `churn-bigml-20.csv`) |

- [Singtel on Kaggle](https://www.kaggle.com/datasets/akhilsaichinthala/telecom-churn-data-singtel)  
- [Mnassrib on Kaggle](https://www.kaggle.com/datasets/mnassrib/telecom-churn-datasets)

After training, files land in `artifacts/<name>/` (`model.joblib`, `scored.csv`, metrics).

---

## Using the app

1. **Sidebar** — pick dataset (Telco / Singtel / Mnassrib).  
2. **Overview** — churn rate, charts, model AUC, feature importance.  
3. **Scoring & high risk** — sort/filter; download scored CSV.  
4. **Customer lookup** — one customer, risk hints, rules, **multi-LLM** retention plans.  
5. **Upload & score** — drop a CSV with the **same columns** as that dataset → instant churn scores (no retrain).

### API keys (optional, sidebar)

| Key | Used for |
|-----|----------|
| `GEMINI_API_KEY` | Gemini retention text |
| `GROQ_API_KEY` | Groq models (`openai/gpt-oss-20b`, `qwen/qwen3.6-27b`, `groq/compound-mini`) |

Rules-only mode works without any keys.

---

## How the ML works (short)

- **Algorithm:** Random Forest (100 trees) inside a sklearn **Pipeline** (impute numbers, one-hot categories).  
- **Split:** 80% train / 20% test, stratified.  
- **Risk tiers:** Low (&lt;30%) · Medium · High · Critical (≥75%).  
- **Code:** `ml_train.py` (shared) + `train.py` / `train2.py` / `train3.py`.

---

## Repo layout

```
ChrunAI/
├── app.py              # Streamlit UI
├── ml_train.py         # Train + score helpers
├── train.py / train2.py / train3.py
├── recommend.py        # Rules + Gemini + Groq
├── data/               # Raw CSVs
├── artifacts/          # Generated models & scores
└── requirements.txt
```

---

## Demo script (judges)

1. Overview → churn rate + AUC.  
2. Scoring → top **Critical** customers.  
3. Lookup → rules → **Generate AI retention plans** (Gemini + Groq).  
4. Upload tab → score a small CSV slice.

---

## Author & license

Educational / hackathon project. Dataset licenses follow IBM Telco and Kaggle sources.

**Repo:** https://github.com/cryoxyl-beep/ChrunAI
