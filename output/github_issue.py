import json
import subprocess
import tempfile
import os


def _ensure_label(label):
    result = subprocess.run(
        ["gh", "label", "list", "--json", "name"],
        capture_output=True, text=True,
    )
    existing = json.loads(result.stdout) if result.stdout.strip() else []
    if not any(l["name"] == label for l in existing):
        subprocess.run(
            ["gh", "label", "create", label, "--color", "0e8a16",
             "--description", "Zoekresultaten fotografiemateriaal"],
        )


def save_to_github_issue(title, body, labels=None):
    labels = labels or ["zoekresultaten"]
    _ensure_label(labels[0])

    result = subprocess.run(
        [
            "gh", "issue", "list",
            "--label", labels[0],
            "--state", "open",
            "--json", "number",
        ],
        capture_output=True,
        text=True,
    )
    existing = json.loads(result.stdout) if result.stdout.strip() else []

    # Schrijf body naar temp file om shell-escaping problemen te voorkomen
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(body)
        body_path = f.name

    try:
        if existing:
            issue_number = existing[0]["number"]
            subprocess.run(
                ["gh", "issue", "comment", str(issue_number),
                 "--body-file", body_path],
                check=True,
            )
            print(f"Resultaten toegevoegd aan issue #{issue_number}")
        else:
            label_args = []
            for label in labels:
                label_args.extend(["--label", label])
            subprocess.run(
                ["gh", "issue", "create", "--title", title,
                 "--body-file", body_path] + label_args,
                check=True,
            )
            print(f"Nieuw issue aangemaakt: {title}")
    finally:
        os.unlink(body_path)
