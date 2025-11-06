#!/usr/bin/env python3
"""
merge_import.py
Simple importer: reads a text file with questions (import.txt) and appends parsed questions to data/questions.json.

Format suggestions:
- MCQ: first line = question
  next lines: A. choice, B. choice, C. choice, D. choice (mark correct with a leading * or add a line 'Answer: B')
- Short: first line = question
  next line: ShortAnswer: <answer text>

Usage:
  python tools\merge_import.py import.txt

Outputs: overwrites data/questions.json with appended items and prints summary.
"""
import sys
import json
import re
from pathlib import Path

def parse_lines(lines):
    i = 0
    out = []
    idbase = 0
    while i < len(lines):
        qline = lines[i].strip()
        i += 1
        if not qline:
            continue
        choices = []
        answer_index = None
        short_answer = ''
        # collect following lines until next blank or next question guessed (we rely on format)
        while i < len(lines) and lines[i].strip():
            ln = lines[i].strip()
            i += 1
            # choice like '*B. text' or 'B. text' or 'A. text'
            m = re.match(r"^\*?([A-Da-d])\.\s*(.*)$", ln)
            if m:
                label = m.group(1).upper()
                text = m.group(2).strip()
                idx = ord(label) - 65
                choices.append(text)
                if ln.startswith('*'):
                    answer_index = idx
                continue
            # Answer: B or Answer: 2 or ShortAnswer:
            am = re.match(r"^(Answer|Đáp án)\s*[:\-]?\s*([A-Da-d0-9]+)$", ln)
            if am:
                v = am.group(2).upper()
                if re.match(r"^[A-D]$", v):
                    answer_index = ord(v) - 65
                elif re.match(r"^[0-9]+$", v):
                    answer_index = int(v) - 1
                continue
            sm = re.match(r"^(ShortAnswer:|Đáp án ngắn:)\s*(.*)$", ln, re.I)
            if sm:
                short_answer = sm.group(2).strip()
                continue
            # fallback: if line doesn't match, but starts with A./B./..., try to split by letter labels
            m2 = re.match(r"^([A-Da-d])\.\s*(.*)$", ln)
            if m2:
                choices.append(m2.group(2).strip())
                continue
            # otherwise treat as continuation of short answer
            if short_answer:
                short_answer += ' ' + ln
            else:
                # if no choices yet and line doesn't look like a choice, treat as short answer
                short_answer = ln

        # build question object
        q = {}
        q['question'] = qline
        if choices:
            q['type'] = 'mcq'
            q['choices'] = choices
            q['answer'] = answer_index if answer_index is not None else None
            q['shortAnswer'] = short_answer or None
        else:
            q['type'] = 'short'
            q['shortAnswer'] = short_answer or ''
        out.append(q)
    return out

def main():
    if len(sys.argv) < 2:
        print('Usage: python tools\\merge_import.py import.txt')
        sys.exit(1)
    import_path = Path(sys.argv[1])
    if not import_path.exists():
        print('Import file not found:', import_path)
        sys.exit(1)
    text = import_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    parsed = parse_lines(lines)
    if not parsed:
        print('No questions parsed from import file.')
        sys.exit(0)

    data_path = Path('data') / 'questions.json'
    if data_path.exists():
        existing = json.loads(data_path.read_text(encoding='utf-8'))
    else:
        existing = []

    start_id = max([q.get('id',0) for q in existing], default=0) + 1
    for idx,p in enumerate(parsed):
        p['id'] = start_id + idx
        existing.append(p)

    data_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Appended {len(parsed)} questions. Total now: {len(existing)}. Written to {data_path}')

if __name__ == '__main__':
    main()
