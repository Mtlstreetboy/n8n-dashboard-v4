<!-- Copilot / AI agent instructions for contributors and automated agents -->
# Copilot Instructions

Purpose: short guidance for AI assistants and contributors working on this repository. Keep production behavior unchanged unless explicitly approved by a human reviewer.

Key principles for automated agents
- **Preserve Production**: Do not change files under `prod/` that are currently deployed without explicit approval. If you propose a change, open a PR and run the test suite.
- **Run Tests First**: Before changing dashboard logic, run `pytest prod/test_options_dashboard.py` (in-container or locally after copying data).
- **Avoid Encoding Damage**: Never transfer file contents using PowerShell piping such as `Get-Content ... | docker exec ...` (this can convert UTF-8 emojis into `??`). Use `docker cp` or edit files directly in the container or in a UTF-8 aware editor.

Repository layout (quick)
- `prod/` : Production scripts and dashboards (Streamlit apps, collectors, engines).
- `docs/` : Documentation and quick run guides.
- `/data/...` : Runtime data inside the Docker container (mapped to container filesystem).

Important paths (container vs host)
- Container options data: `/data/options_data`
- Container scripts path: `/data/scripts` (when running inside the `n8n_data_architect` container)
- Host repository root (example): `c:\n8n-local-stack`

Common commands

- Start stack (development):
```
docker-compose up -d
```

- Copy options data from container to host (preferred over piping):
```
docker cp n8n_data_architect:/data/options_data ./data/options_data
```

- Run options dashboard inside the container (mapped ports):
```
docker exec -it n8n_data_architect sh -c "streamlit run /data/scripts/dashboard_options.py --server.port 8501"
```

- Run Streamlit locally (Windows PowerShell):
```
python -m venv .venv_dashboard
.\.venv_dashboard\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONUTF8='1'; chcp 65001 | Out-Null
streamlit run prod\dashboard_options.py --server.port 8503
```

Encoding & emoji: troubleshooting
- Problem: PowerShell piping (Get-Content | docker exec) re-encodes text and turns emojis into `??`.
- Fix: always use `docker cp` to copy original files out of the container, or open files with an editor that preserves UTF-8.
- To re-save repository Python files as UTF-8 on Windows PowerShell (no logic change):
```
Get-ChildItem -Path .\prod -Filter *.py -Recurse | ForEach-Object { (Get-Content -Raw $_.FullName) | Set-Content -LiteralPath $_.FullName -Encoding UTF8 }
```

Local-run notes
- If you run the Streamlit app locally and you get `FileNotFoundError: '/data/options_data'`, copy container data to `./data/options_data` or update the `OPTIONS_DATA_DIR` constant at the top of the Streamlit script to point to a local path.

Agent behaviour checklist before making code edits
1. Confirm whether the change affects production visuals or data flow.
2. If it does, open a PR and run tests inside the container.
3. If the change is purely maintenance (encoding, formatting), keep diffs minimal and avoid touching visualization parameters.

Contact / Reviewer
- If unsure, request review from the repo owner / Senior Data Architect before merging.

Date: 2025-12-10
