#!/usr/bin/env python
"""Silencio Raffle Verification — web viewer.

A lightweight Flask app that browses the raffle season directories,
renders the README files, and displays result / token-assignment CSVs
in a paginated table.
"""
import os
import math
import markdown
import pandas as pd
from flask import Flask, render_template, abort, request

app = Flask(__name__)
REPO = os.path.dirname(os.path.abspath(__file__))

SKIP_DIRS = {".git", "templates", "__pycache__", ".base44", "node_modules"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_seasons():
    """Return sorted list of season directory names that contain a README."""
    seasons = []
    for name in sorted(os.listdir(REPO)):
        path = os.path.join(REPO, name)
        if not os.path.isdir(path) or name.startswith(".") or name in SKIP_DIRS:
            continue
        if os.path.exists(os.path.join(path, "README.md")):
            seasons.append(name)
    return seasons


def season_title(season_dir):
    """Extract a human-friendly title from the season README."""
    readme = os.path.join(REPO, season_dir, "README.md")
    if not os.path.exists(readme):
        return season_dir
    with open(readme, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
    return season_dir


def walk_files(season_dir):
    """Walk a season directory and categorise its files."""
    base = os.path.join(REPO, season_dir)
    results, assignments, scripts, hashes, data, images = [], [], [], [], [], []
    for root, _dirs, files in os.walk(base):
        for fname in sorted(files):
            if fname.startswith(".") or fname == ".keep":
                continue
            rel = os.path.relpath(os.path.join(root, fname), base)
            ext = os.path.splitext(fname)[1].lower()
            parent = os.path.basename(root)
            if ext == ".csv" and "result" in parent.lower():
                results.append(rel)
            elif ext == ".csv" and "token_assignment" in parent.lower():
                assignments.append(rel)
            elif ext == ".csv":
                data.append(rel)
            elif ext == ".py":
                scripts.append(rel)
            elif ext == ".txt":
                hashes.append(rel)
            elif ext in (".jpg", ".png", ".jpeg"):
                images.append(rel)
    return {
        "results": sorted(results),
        "assignments": sorted(assignments),
        "scripts": sorted(scripts),
        "hashes": sorted(hashes),
        "data": sorted(data),
        "images": sorted(images),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    seasons = get_seasons()
    cards = []
    for s in seasons:
        files = walk_files(s)
        card = {
            "name": s,
            "title": season_title(s),
            "result_count": len(files["results"]),
            "has_results": len(files["results"]) > 0,
        }
        cards.append(card)
    return render_template("index.html", seasons=cards)


@app.route("/season/<season>")
def season_detail(season):
    path = os.path.join(REPO, season)
    if not os.path.isdir(path):
        abort(404)

    readme_html = ""
    readme_path = os.path.join(path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            readme_html = markdown.markdown(f.read(), extensions=["tables", "fenced_code"])

    files = walk_files(season)
    all_seasons = get_seasons()
    return render_template(
        "season.html",
        season=season,
        title=season_title(season),
        readme_html=readme_html,
        files=files,
        all_seasons=all_seasons,
    )


@app.route("/season/<season>/csv/<path:filepath>")
def view_csv(season, filepath):
    full_path = os.path.join(REPO, season, filepath)
    if not os.path.exists(full_path) or not filepath.endswith(".csv"):
        abort(404)

    page = max(1, int(request.args.get("page", 1)))
    per_page = 50
    file_size = os.path.getsize(full_path)
    truncated = False

    # For very large files, only read the first 5000 rows
    if file_size > 20_000_000:
        df = pd.read_csv(full_path, nrows=5000)
        truncated = True
        total_rows = len(df)
    else:
        df = pd.read_csv(full_path)
        total_rows = len(df)

    total_pages = max(1, math.ceil(total_rows / per_page))
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    df_page = df.iloc[start:end]

    # Convert to list of dicts for the template
    columns = df.columns.tolist()
    rows = df_page.values.tolist()

    return render_template(
        "csv_viewer.html",
        season=season,
        filepath=filepath,
        columns=columns,
        rows=rows,
        page=page,
        total_pages=total_pages,
        total_rows=total_rows,
        truncated=truncated,
        file_size_mb=round(file_size / 1_000_000, 1),
    )


@app.route("/season/<season>/file/<path:filepath>")
def view_file(season, filepath):
    full_path = os.path.join(REPO, season, filepath)
    if not os.path.exists(full_path):
        abort(404)

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".md":
        with open(full_path, encoding="utf-8") as f:
            content = markdown.markdown(f.read(), extensions=["tables", "fenced_code"])
        return render_template(
            "file_viewer.html", season=season, filepath=filepath,
            content=content, rendered=True,
        )

    # Plain text files (.py, .txt, .csv, etc.)
    try:
        with open(full_path, encoding="utf-8") as f:
            content = f.read(200_000)  # cap at 200 KB
        truncated = len(content) == 200_000
    except UnicodeDecodeError:
        content = "(Binary file — cannot display as text)"
        truncated = False

    return render_template(
        "file_viewer.html", season=season, filepath=filepath,
        content=content, rendered=False, truncated=truncated,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
