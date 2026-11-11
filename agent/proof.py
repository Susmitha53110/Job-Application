from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import paths


def applied_dir(company: str, role: str, day: str | None = None) -> Path:
    day = day or date.today().isoformat()
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in f"{company}_{role}").strip().replace(" ", "_")
    out = paths.APPLICATIONS / "applied" / day / safe[:120]
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_proof_manifest(
    *,
    company: str,
    role: str,
    url: str,
    status: str,
    notes: str,
    proof_files: list[str] | None = None,
    day: str | None = None,
) -> Path:
    """Record proof metadata. status must be applied|unconfirmed|needs me."""
    day = day or date.today().isoformat()
    folder = applied_dir(company, role, day=day) if status in {"applied", "unconfirmed"} else (
        paths.APPLICATIONS / "needs-me" / day
    )
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "company": company,
        "role": role,
        "url": url,
        "status": status,
        "notes": notes,
        "proof_files": proof_files or [],
        "day": day,
    }
    path = folder / "PROOF.json" if status in {"applied", "unconfirmed"} else folder / f"PROOF_{company}_{role}.json".replace(" ", "_")
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def require_proof_for_applied(proof_files: list[str] | None) -> str:
    """Return 'applied' only when at least one proof file path exists on disk."""
    files = proof_files or []
    existing = [p for p in files if Path(p).exists()]
    if existing:
        return "applied"
    return "unconfirmed"
