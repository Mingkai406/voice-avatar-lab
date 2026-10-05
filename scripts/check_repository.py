#!/usr/bin/env python3
"""Check the public source tree, local Markdown links and accidental large/private files."""
import re,subprocess
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','.venv-tts','.bootstrap','.hf-cache','.uv-cache','models','vendor','runtime','__pycache__','qa-local'}
files=[]
def walk(folder):
    for p in folder.iterdir():
        if p.name in SKIP:continue
        if p.is_symlink():continue
        if p.is_dir():walk(p)
        elif p.name not in ['.DS_Store'] and not (p.parent==ROOT/'public' and (p.name.startswith('lp-') or p.name.startswith('source-'))):files.append(p)
walk(ROOT);errors=[]
for p in files:
    rel=p.relative_to(ROOT)
    if p.name=='.env' or (p.name.startswith('.env.') and p.name!='.env.example'):errors.append(f'Private config present: {rel}')
    if p.stat().st_size>5*1024*1024:errors.append(f'Oversized public file: {rel}')
    if p.suffix not in ['.py','.md','.js','.html','.css','.json','.yml','.toml','.txt']:continue
    text=p.read_text()
    if re.search(r'gh[pousr]_[A-Za-z0-9]{24,}',text):errors.append(f'Possible credential: {rel}')
    if '/Us'+'ers/' in text or '/home/'+'mingkai' in text:errors.append(f'Private absolute path: {rel}')
    if p.suffix=='.md':
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if re.match(r'\w+://|mailto:|#',target):continue
            target=unquote(target.split('#')[0])
            if target and not (p.parent/target).exists():errors.append(f'Broken local link in {rel}: {target}')
if errors:raise SystemExit('\n'.join(errors))
print(f'Public-source checks passed ({len(files)} files).')
