# Run Options Dashboard Locally (Quick Guide)

This small guide describes the minimal steps to run `prod/dashboard_options.py` locally on Windows and avoid common encoding and data path issues.

1) Copy options data from the running container to your repo (recommended)

PowerShell / CMD (run from repository root `c:\n8n-local-stack`):
```
# Copy the container's options data into a local folder
docker cp n8n_data_architect:/data/options_data .\data\options_data

# Verify files exist locally
ls .\data\options_data | Select-Object -First 10
```

2) Create and activate a Python virtual environment

PowerShell:
```
python -m venv .venv_dashboard
.\.venv_dashboard\Scripts\Activate.ps1
```

3) Install required packages

Either use an existing `requirements.txt` or run:
```
pip install streamlit pandas plotly yfinance numpy
```

4) Ensure Python uses UTF-8 for I/O in the session

PowerShell (temporary for this shell session):
```
$env:PYTHONUTF8='1'; chcp 65001 | Out-Null
```

5) Run the Streamlit app locally

PowerShell (choose an available port; 8503 used here):
```
streamlit run prod\dashboard_options.py --server.port 8503
```

6) If you see `FileNotFoundError: '/data/options_data'`
- Create the local folder `data\options_data` (see step 1) or edit the top of `prod/dashboard_options.py` to set `OPTIONS_DATA_DIR = './data/options_data'`.

7) Fixing `??` emoji/encoding artifacts
- If files in `prod/` show `??` where emojis should be, the safest approach is to copy the original files out of the container (they were written as UTF-8) with `docker cp`, then replace the corrupted local copies.

Example: copy the canonical dashboard file from container:
```
docker cp n8n_data_architect:/data/scripts/dashboard_sentiment_clean.py .\prod\dashboard_sentiment_clean.py
```

8) Convert all `prod/*.py` to UTF-8 (no code changes)

PowerShell command (will re-save files as UTF-8 without modifying logic):
```
Get-ChildItem -Path .\prod -Filter *.py -Recurse | ForEach-Object { (Get-Content -Raw $_.FullName) | Set-Content -LiteralPath $_.FullName -Encoding UTF8 }
```

9) Tests
- Run the options dashboard tests (inside the container is recommended if using container data):
```
# inside container
docker exec -it n8n_data_architect sh -c "python3 /data/scripts/test_options_dashboard.py"

# locally (after copying data)
pytest prod/test_options_dashboard.py
```

10) Quick troubleshooting
- Port already in use: choose another port with `--server.port`.
- Streamlit shows blank/empty charts: confirm `./data/options_data` contains CSV/JSON files (calls/puts) for a few tickers.
- Encoding issues persist: prefer to re-copy files from container using `docker cp`.

If you want, I can:
- (A) update `prod/dashboard_options.py` to fall back to a local path automatically if `/data/options_data` is missing, and
- (B) convert all `prod/*.py` to UTF-8 now (no logic changes),
Just tell me which action to perform next.
