#!/usr/bin/env python3
"""
Trigger een zoekactie via GitHub Actions en haal het resultaat op.
Gebruik: python3 trigger_remote.py "Nikkor 35mm f/2 AI"

Resultaat verschijnt als GitHub Issue (leesbaar op telefoon).
Op Mac wordt het ook in Apple Notes gezet.
"""

import sys
import os
import time
import json
import platform
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


def wait_for_completion(timeout=180):
    print("Wachten op voltooiing", end="", flush=True)
    start = time.time()

    # Geef GitHub even om de run aan te maken
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
            status = run["status"]
            conclusion = run.get("conclusion")

            if status == "completed":
                print(f" {conclusion}!")
                return conclusion == "success"

        print(".", end="", flush=True)
        time.sleep(10)

    print(" timeout!")
    return False


def get_latest_issue():
    resp = requests.get(
        f"https://api.github.com/repos/{REPO}/issues",
        headers=HEADERS,
        params={"labels": "zoekresultaten", "sort": "created", "direction": "desc", "per_page": 1},
    )
    resp.raise_for_status()
    issues = resp.json()

    if issues:
        return issues[0]["title"], issues[0]["body"]
    return None, None


def save_to_apple_notes(title, body):
    from output.apple_notes import save_to_apple_notes as _save
    _save(title, body)
    print(f"Apple Note aangemaakt: \"{title}\"")


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python3 trigger_remote.py \"beschrijving\"")
        sys.exit(1)

    description = sys.argv[1]

    trigger_workflow(description)
    success = wait_for_completion()

    if not success:
        print("Workflow mislukt. Check GitHub Actions logs.")
        sys.exit(1)

    title, body = get_latest_issue()

    if not body:
        print("Geen resultaten gevonden in issues.")
        sys.exit(1)

    print(f"\n--- {title} ---\n")
    print(body[:500] + "...\n")

    # Op Mac: ook Apple Note aanmaken
    if platform.system() == "Darwin":
        save_to_apple_notes(title, body)


if __name__ == "__main__":
    main()
