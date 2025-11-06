#!/usr/bin/env python3
"""Rebuild data/questions.json from import.txt by splitting on numbered headers.

Usage: python tools/rebuild_questions.py path/to/import.txt

This script looks for lines starting with a numbered header like "1. ..." and
treats each such header as the start of a new question. It extracts choices
(A. B. C. D.) and looks for an Answer line if present. The output is a JSON
array with one object per question.
"""
import re
import json
import sys
from pathlib import Path


def load_lines(path: Path):
    text = path.read_text(encoding="utf-8")
    # Normalize Windows line endings and keep as list
    return text.splitlines()


def is_header(line: str):
    return re.match(r"^\s*(\d+)\.\s*", line) is not None


def parse_blocks(lines):
    header_re = re.compile(r"^\s*(\d+)\.\s*(.*)")
    blocks = []  # list of (num, header_rest, block_lines)
    cur_num = None
    cur_header = None
    cur_lines = []

    for i, line in enumerate(lines):
        m = header_re.match(line)
        if m:
            # start new block
            if cur_num is not None:
                blocks.append((cur_num, cur_header, cur_lines))
            cur_num = int(m.group(1))
            cur_header = m.group(2).strip()
            cur_lines = []
        else:
            # append line to current block if any
            if cur_num is not None:
                cur_lines.append(line.rstrip())
            else:
                # skip lines before first header
                continue

    if cur_num is not None:
        blocks.append((cur_num, cur_header, cur_lines))

    return blocks


def parse_block_to_question(num, header, lines):
    # capture optional leading '*' which marks the correct choice in the source
    choice_re = re.compile(r"^\s*(\*?)\s*([A-Da-d])\.\s*(.*)")
    # accept common answer-labeling lines (Answer: B) as fallback
    answer_re = re.compile(r"^\s*(?:Answer|Ans|Correct|Key|Đáp án)\s*[:\-]?\s*([A-Da-d])", re.I)

    choices = []
    question_lines = []
    answer_letter = None

    for line in lines:
        cm = choice_re.match(line)
        if cm:
            star = cm.group(1)
            label = cm.group(2)
            text = cm.group(3)
            choices.append(text.strip())
            # if the source marks the correct choice with a leading '*', prefer that
            if star and not answer_letter:
                answer_letter = label.upper()
            continue

        am = answer_re.match(line)
        if am:
            answer_letter = am.group(1).upper()
            continue

        # otherwise this is a question body line
        question_lines.append(line)

    # Build question text: include header and the text lines
    qtext_parts = [header] if header else []
    if question_lines:
        # join with spaces to preserve sentence breaks
        qtext_parts.append(" ".join([l.strip() for l in question_lines if l.strip()]))
    question_text = " ".join(qtext_parts).strip()

    qobj = {
        "id": num,
        "question": question_text,
        "type": "mcq" if choices else "short",
        "choices": choices,
        "answer": None,
    }

    # convert detected answer letter (A-D) to zero-based index and set answer if valid
    if answer_letter and choices:
        idx = ord(answer_letter.upper()) - ord('A')
        if 0 <= idx < len(choices):
            qobj["answer"] = idx

    return qobj


def rebuild(input_path: Path, out_path: Path):
    lines = load_lines(input_path)
    blocks = parse_blocks(lines)
    questions = []
    for num, header, blines in blocks:
        q = parse_block_to_question(num, header, blines)
        questions.append(q)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {out_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/rebuild_questions.py path/to/import.txt")
        sys.exit(2)
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(2)
    out_path = Path("data/questions.json")
    rebuild(input_path, out_path)


if __name__ == "__main__":
    main()
