#!/usr/bin/env python3
"""
Trigger een zoekactie via GitHub Actions en haal het resultaat op.
Gebruik: python3 trigger_remote.py "beschrijving"
"""

import sys
import os
import time
import platform
from datetime import datetime, timezone, date
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_PAT = os.environ["GITHUB_PAT"]
REPO = "czvr6nbsz2-dev/ebay-search"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_PAT}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def trigger_workflow(description):
    print(f"Workflow triggeren: {description}")
    resp = requests.post(
        f"https://api.github.com/repos/{REPO}/actions/workflows/search.yml/dispatches",
        headers=HEADERS,
        json={"ref": "main", "inputs": {"description": description}},
    )
    resp.raise_for_status()
    print("Workflow gestart.\n")


def wait_for_completion(timeout=420):
    print("Wachten op voltooiing", end="", flush=True)
    start = time.time()
    time.sleep(5)
    while time.time() - start < timeout:
        resp = requests.get(
            f"https://api.github.com/repos/{REPO}/actions/runs",
            headers=HEADERS,
            params={"per_page": 1},
        )
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if runs:
            run = runs[0]
            if run["status"] == "completed":
                print(f" {run.get('conclusion')}!")
                return run.get("conclusion") == "success"
        print(".", end="", flush=True)
        time.sleep(10)
    print(" timeout!")
    return False


def get_latest_result(workflow_start_iso, description):
    resp = requests.get(
        f"https://api.github.com/repos/{REPO}/issues",
        headers=HEADERS,
        params={
            "labels": "zoekresultaten",
            "sort": "updated",
            "direction": "desc",
            "per_page": 1,
            "state": "all",
        },
    )
    resp.raise_for_status()
    issues = resp.json()
    today = date.today().isoformat()
    title = f"Zoekresultaat: {description[:80]} \u2013 {today}"

    if not issues:
        return title, None

    issue = issues[0]
    comments_resp = requests.get(
        issue["comments_url"],
        headers=HEADERS,
        params={"per_page": 100},
    )
    comments_resp.raise_for_status()
    comments = comments_resp.json()

    latest = None
    for c in comments:
        if c["created_at"] >= workflow_start_iso:
            if not latest or c["created_at"] > latest["created_at"]:
                latest = c

    if latest:
        return title, latest["body"]
    return title, issue.get("body")


def save_to_apple_notes(title, body):
    from output.apple_notes import save_to_apple_notes as _save
    _save(title, body)
    print(f"Apple Note aangemaakt: \"{title}\"")


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python3 trigger_remote.py \"beschrijving\"")
        sys.exit(1)

    description = sys.argv[1]
    workflow_start_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    trigger_workflow(description)
    success = wait_for_completion()
    if not success:
        print("Workflow mislukt. Check GitHub Actions logs.")
        sys.exit(1)

    title, body = get_latest_result(workflow_start_iso, description)
    if not body:
        print("Geen resultaten gevonden in issues/comments.")
        sys.exit(1)

    print(f"\n--- {title} ---\n")
    print(body[:2000] + ("..." if len(body) > 2000 else "") + "\n")

    if platform.system() == "Darwin":
        save_to_apple_notes(title, body)


if __name__ == "__main__":
    main()
