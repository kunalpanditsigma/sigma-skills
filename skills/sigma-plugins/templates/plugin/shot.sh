#!/bin/bash
# shot.sh <out.png> <width> <height> [hash]
# Screenshot the local test page headlessly. Fine for a local file; for a live
# Sigma embed use a real-time wait instead (virtual time budgets hang there).
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$C" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=4000 \
  --window-size="$2,$3" --screenshot="$1" "file://$PWD/test/index.html#$4" >/dev/null 2>&1
echo "$1"
