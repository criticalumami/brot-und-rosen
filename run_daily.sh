#!/bin/bash
# ============================================================
# run_daily.sh — Daily Lebanon Real Estate Scraper
# Cron entry (runs at 08:00 AM daily):
#   0 8 * * * /Users/mzrxa/Documents/antigravity/vorwärts/run_daily.sh
#
# To install the cron job, run:
#   crontab -e
# and add the line above.
# ============================================================

WORKSPACE="/Users/mzrxa/Documents/antigravity/vorwärts"
LOGFILE="$WORKSPACE/scraper.log"
PYTHON="$WORKSPACE/.venv/bin/python"
SCRIPT="$WORKSPACE/gemini-code-1783084154926.py"

echo "======================================" >> "$LOGFILE"
echo "Run started: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOGFILE"

cd "$WORKSPACE" && "$PYTHON" "$SCRIPT" >> "$LOGFILE" 2>&1

STATUS=$?
if [ $STATUS -eq 0 ]; then
  echo "Run SUCCEEDED: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOGFILE"
else
  echo "Run FAILED (exit $STATUS): $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOGFILE"
fi
echo "======================================" >> "$LOGFILE"
