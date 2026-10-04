# Silencio Raffle Verification — Base44 Dev Environment

## What this repo is

A Python data-verification repository for Silencio raffle seasons (beta-airdrop + seasons 1–7).
Each subdirectory contains a `raffle_airdrop.py` (or `beta_airdrop.py`) script, CSV input data,
token-assignment CSVs, and result CSVs. There is **no web application** in the original repo.

## What was added for the preview

A lightweight Flask web viewer (`app.py`, `templates/`, `requirements-web.txt`) that browses
the season directories, renders READMEs as HTML, and displays result/token CSVs in paginated tables.
This is the only thing served on port 3000.

## Running

```
docker compose -f docker-compose.base44.yml up -d --build
```

- Base image: `python:3.11-slim` (plain runtime, source bind-mounted at `/app`)
- Installs `requirements-web.txt` on startup, then runs `python app.py` (Flask dev server on 0.0.0.0:3000)
- No external services, no databases, no secrets needed
- Healthcheck: `GET /` via Python urllib

## Verification

- `curl http://localhost:3000/` → home page listing all seasons
- Navigate to `/season/beta-airdrop` → README + file browser
- Click a result CSV → paginated table view
- Large CSVs (>20 MB, e.g. `participating_users.csv`) are capped at 5,000 rows

## Running the original verification scripts (optional)

Each season has its own `requirements.txt` (pinned to old pandas/numpy). To run a script:
```
cd raffle-season-1
pip install -r requirements.txt
python raffle_airdrop.py
```
This is not part of the web preview.
