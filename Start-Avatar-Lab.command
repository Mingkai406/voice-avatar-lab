#!/bin/zsh
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  echo 'Run python3 scripts/setup.py --profile full first.'
  exit 1
fi
(sleep 3; open 'http://127.0.0.1:8765') &
exec .venv/bin/python run.py
