#!/usr/bin/env python3
"""Read-only setup diagnostics; never prints credentials."""
import argparse,json,platform,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--profile',choices=['sample','full'],default='sample');args=p.parse_args()
checks={'Python 3.12+':sys.version_info>=(3,12),'Recorded audio':(ROOT/'examples/audio/index.json').exists(),
        'Renderer assets':(ROOT/'vendor/DH_live/web_demo/static/js/DHLiveMini.js').exists()}
if args.profile=='full':
    checks['Apple Silicon macOS']=platform.system()=='Darwin' and platform.machine()=='arm64'
    for name,entry in json.loads((ROOT/'models.lock.json').read_text())['models'].items():
        checks['Model: '+name]=any((ROOT/entry['path']).rglob('*.safetensors')) or any((ROOT/entry['path']).rglob('*.bin')) or any((ROOT/entry['path']).rglob('*.pth'))
    for env in ['.venv','.venv-tts']:checks[env]=(ROOT/env/'bin/python').exists()
for name,ok in checks.items():print(('OK   ' if ok else 'MISS ')+name)
raise SystemExit(0 if all(checks.values()) else 1)
