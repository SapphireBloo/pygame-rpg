#!/usr/bin/env bash
# Runs Chin Check Charlie on Linux. Usage:  bash run_linux.sh
# The first run sets up a private Python environment in .venv (needs internet once);
# after that it starts right away.
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 isn't installed. Install it with your package manager, e.g.:"
    echo "  sudo apt install python3 python3-venv      (Debian/Ubuntu/Mint)"
    echo "  sudo dnf install python3                   (Fedora)"
    echo "  sudo pacman -S python                      (Arch)"
    exit 1
fi

if [ ! -x .venv/bin/python ]; then
    echo "First run: setting up (about a minute)..."
    if ! python3 -m venv .venv; then
        echo "Couldn't create a Python environment. On Debian/Ubuntu/Mint run:"
        echo "  sudo apt install python3-venv"
        rm -rf .venv
        exit 1
    fi
    .venv/bin/python -m pip install --quiet --upgrade pip
    .venv/bin/python -m pip install --quiet -r requirements.txt
fi

exec .venv/bin/python main.py "$@"
