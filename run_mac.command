#!/bin/bash
# Double-click on macOS after installing Python from python.org or Homebrew.
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
for candidate in python3.12 python3.13 python3.14 python3.15 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(not ((3, 11) <= sys.version_info[:2] <= (3, 15)))' 2>/dev/null; then
      "$candidate" run.py
      result=$?
      if [ "$result" -ne 0 ]; then read -r -p "Press Enter to close..."; fi
      exit "$result"
    fi
  fi
done
echo "Please install Python 3.12 from https://www.python.org/downloads/macos/"
echo "Then double-click run_mac.command again."
read -r -p "Press Enter to close..."
exit 1
