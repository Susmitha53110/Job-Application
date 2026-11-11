from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "memory"
RESUMES_BASE = ROOT / "resumes" / "base"
RESUMES_TAILORED = ROOT / "resumes" / "tailored"
RESUMES_VERSIONS = ROOT / "resumes" / "versions"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
APPLICATIONS = ROOT / "applications"
INTERVIEW_PREP = ROOT / "interview-prep"
PROFILE = MEMORY / "PROFILE.md"
RULES = MEMORY / "RULES.md"
STATE = MEMORY / "STATE.md"
SETUP_STATUS = MEMORY / "SETUP_STATUS.md"
APPLIED_INDEX = MEMORY / "APPLIED_INDEX.md"
APPLICATIONS_CSV = LOGS / "applications.csv"
