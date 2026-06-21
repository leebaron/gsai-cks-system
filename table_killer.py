#!/usr/bin/env python3
"""
table_killer.py — pre-flight table filter for Telegram output.
Reads stdin, strips markdown table syntax, writes to stdout.
Used as: python3 table_killer.py < message.txt
Or embedded: called before every Telegram direct message.
"""
import sys, re


def strip_tables(text: str) -> str:
    """Remove markdown table rows: lines containing | with --- separators"""
    lines = text.split("\n")
    filtered = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        # Detect table separator row: |---|---|
        if re.match(r"^[\s\|:\-]+\|[\s\|:\-]+", stripped) and "---" in stripped:
            continue  # skip separator row
        # Detect header/data row with pipe separators (table row)
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2:
            continue  # skip table row
        filtered.append(line)
    return "\n".join(filtered)


if __name__ == "__main__":
    text = sys.stdin.read()
    clean = strip_tables(text)
    sys.stdout.write(clean)
