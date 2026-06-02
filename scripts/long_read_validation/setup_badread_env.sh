#!/usr/bin/env bash
set -euo pipefail

BADREAD_VENV="${BADREAD_VENV:-$HOME/.venvs/bactscout-badread}"

mkdir -p "$(dirname "$BADREAD_VENV")"
python3 -m venv "$BADREAD_VENV"
if [[ -x "$BADREAD_VENV/bin/badread" ]]; then
	echo "Badread already available in $BADREAD_VENV"
	exit 0
fi

"$BADREAD_VENV/bin/pip" install --upgrade pip setuptools wheel
"$BADREAD_VENV/bin/pip" install git+https://github.com/rrwick/Badread.git

echo "Badread installed in $BADREAD_VENV"