"""
GitNova v4.4.1 — Canonical Seed Adapter

DEPRECATION NOTICE:
Manual / synthetic seeding is permanently disabled in GitNova production.
This script now executes the hardened canonical ingestion pipeline against real,
verified, open GitHub issues.
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from scripts.run_canonical_pilot_ingestion import run_pilot_ingestion

if __name__ == "__main__":
    print("🔒 [DEPRECATED SEED BYPASS REMOVED] Routing to Canonical Pilot Ingestion Gateway...")
    run_pilot_ingestion()
