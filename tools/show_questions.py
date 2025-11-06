#!/usr/bin/env python3
import json
from pathlib import Path

p = Path('data/questions.json')
if not p.exists():
    print('data/questions.json not found')
    raise SystemExit(2)

q = json.loads(p.read_text(encoding='utf-8'))
print('total', len(q))
print('---FIRST 10---')
for item in q[:10]:
    print(f"{item.get('id', '?'):3}: {item.get('question')}")
print('---LAST 10---')
for item in q[-10:]:
    print(f"{item.get('id', '?'):3}: {item.get('question')}")
