# Dashboard App

Sprint 1 dashboard app implementation area.

The current scaffold uses Streamlit and mock data. It keeps data loading separate so a future CSV, DB, or Gold Layer source can be mapped into the internal dashboard schema.

## Run Locally

```powershell
cd apps/dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Data Loading

- If `data/sample_access_drift.csv` exists, the app reads that CSV.
- If the CSV is missing, `src/mock_data.py` generates temporary mock rows.
- Pages show `Using mock data` when mock rows are active.
- Final source column mapping should be added in `src/data_loader.py`.
