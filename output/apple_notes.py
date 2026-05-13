import os
import re
import subprocess
import tempfile


def _md_inline(text):
    def link_sub(m):
        label, url = m.group(1), m.group(2).replace("&", "&amp;")
        return f'<a href="{url}">{label}</a>'
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_sub, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def _md_to_html(md):
    lines = md.split("\n")
    out = []
    in_table = False

    def close_table():
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped:
            close_table()
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_table()
            level = len(m.group(1))
            out.append(f"<h{level}>{_md_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith(">"):
            close_table()
            out.append(f"<blockquote>{_md_inline(stripped[1:].strip())}</blockquote>")
            i += 1
            continue

        if stripped in ("---", "***"):
            close_table()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if (
                not in_table
                and i + 1 < len(lines)
                and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip())
            ):
                out.append(
                    "<table border='1' cellpadding='6' cellspacing='0' "
                    "style='border-collapse:collapse'>"
                )
                out.append("<thead><tr>")
                for c in cells:
                    out.append(f"<th>{_md_inline(c)}</th>")
                out.append("</tr></thead><tbody>")
                in_table = True
                i += 2
                continue
            if in_table:
                out.append("<tr>")
                for c in cells:
                    out.append(f"<td>{_md_inline(c)}</td>")
                out.append("</tr>")
                i += 1
                continue

        close_table()
        out.append(f"<p>{_md_inline(stripped)}</p>")
        i += 1

    close_table()
    return "\n".join(out)


def save_to_apple_notes(title, body):
    html_body = _md_to_html(body)

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
