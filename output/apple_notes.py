import os
import subprocess
import tempfile


def save_to_apple_notes(title, body):
    html_body = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>\n")
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html_body)
        html_path = f.name

    escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')

    script = (
        f'set htmlContent to read POSIX file "{html_path}" as «class utf8»\n'
        f'tell application "Notes"\n'
        f'    make new note with properties '
        f'{{name:"{escaped_title}", body:htmlContent}}\n'
        f"end tell"
    )

    try:
        subprocess.run(["osascript", "-e", script], check=True)
    finally:
        os.unlink(html_path)
