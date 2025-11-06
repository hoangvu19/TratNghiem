#!/usr/bin/env python3
"""
renumber_import.py
Reads import.txt, renumbers lines that start with a question number like "1. (2 points)" or "1. (0.200 point)"
and writes the corrected file back (creates a backup import.txt.bak).

Usage:
  python tools\renumber_import.py import.txt

This is safe and idempotent: runs multiple times without changing numbering after first run.
"""
import sys
import re
from pathlib import Path

def renumber(file_path: Path):
    text = file_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    qnum = 1
    pattern = re.compile(r"^(\d+)\.\s*\(.*\)\s*$")
    # We'll replace lines that start with a number-dot and parentheses on the same line,
    # or lines that start with number-dot and optional space (e.g., "1. (2 points)").
    new_lines = []
    for ln in lines:
        m = re.match(r"^(\s*)(\d+)\.(\s*\(.*\))?(\s*)$", ln)
        if m and m.group(3):
            # matched a line like '1. (2 points)'
            leading = m.group(1) or ''
            trailing = m.group(4) or ''
            new_lines.append(f"{leading}{qnum}.{m.group(3)}{trailing}")
            qnum += 1
            continue
        # Some lines are like '1. (0.200 point)' followed by text on same line; handle more general case
        m2 = re.match(r"^(\s*)(\d+)\.(\s*)(\(.*\))?(.*)$", ln)
        if m2 and m2.group(4):
            leading = m2.group(1) or ''
            rest = m2.group(4) + m2.group(5)
            new_lines.append(f"{leading}{qnum}.{rest}")
            qnum += 1
            continue
        # otherwise keep as-is
        new_lines.append(ln)
    # backup
    bak = file_path.with_suffix(file_path.suffix + '.bak')
    file_path.replace(bak)
    file_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    print(f'Renumbered {qnum-1} question headers. Backup saved to {bak}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools\\renumber_import.py import.txt')
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print('File not found:', p)
        sys.exit(1)
    renumber(p)
