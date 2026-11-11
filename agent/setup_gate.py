from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


PLACEHOLDER_RE = re.compile(r"\[[A-Z0-9 /,_%.\-]+\]")


@dataclass
class GateResult:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_needs_me(self) -> str:
        lines = ["# needs me — setup incomplete", "", "Do these before any dry run or apply:", ""]
        for i, b in enumerate(self.blockers, 1):
            lines.append(f"{i}. {b}")
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"- {w}")
        return "\n".join(lines) + "\n"


def _field_values(profile_text: str) -> list[str]:
    values: list[str] = []
    for line in profile_text.splitlines():
        if ":" not in line:
            continue
        if line.strip().startswith(">"):
            continue
        _, _, rest = line.partition(":")
        values.append(rest.strip())
    return values


def find_base_resume() -> Path | None:
    if not paths.RESUMES_BASE.exists():
        return None
    candidates = []
    for p in paths.RESUMES_BASE.iterdir():
        if not p.is_file():
            continue
        if p.name.startswith("PUT_BASE_RESUME"):
            continue
        if p.name.startswith("."):
            continue
        if p.suffix.lower() in {".docx", ".md", ".txt", ".pdf"}:
            candidates.append(p)
    if not candidates:
        return None
    # Prefer docx, then md
    # Prefer structured .md twin for parsing when present; .docx remains canonical file on disk.
    candidates.sort(key=lambda p: {".md": 0, ".docx": 1, ".txt": 2, ".pdf": 3}.get(p.suffix.lower(), 9))
    return candidates[0]


def check_setup() -> GateResult:
    blockers: list[str] = []
    warnings: list[str] = []

    if not paths.PROFILE.exists():
        blockers.append("Create memory/PROFILE.md with your filled profile.")
        return GateResult(False, blockers, warnings)

    text = paths.PROFILE.read_text(encoding="utf-8")
    if "SETUP INCOMPLETE" in text:
        blockers.append("Remove SETUP INCOMPLETE from memory/PROFILE.md after filling all fields.")

    values = _field_values(text)
    placeholder_hits = [v for v in values if PLACEHOLDER_RE.search(v)]
    if placeholder_hits:
        blockers.append(
            "Fill every bracketed placeholder in memory/PROFILE.md "
            f"({len(placeholder_hits)} still look incomplete)."
        )

    # Required identity keys present and non-empty
    required_labels = [
        "Full name",
        "Application email",
        "Phone",
        "Location",
        "Current/most recent role + years",
        "Education",
        "Roles",
        "Location preference",
        "Seniority / years range",
        "Work authorization",
        "Daily window",
    ]
    lower = text.lower()
    for label in required_labels:
        if label.lower() not in lower:
            blockers.append(f"Missing profile section/label: {label}")

    resume = find_base_resume()
    if resume is None:
        blockers.append(
            "Add your base resume to resumes/base/ (.docx preferred, or .md/.txt). "
            "That file is the only source of truth."
        )
    elif resume.suffix.lower() == ".pdf":
        warnings.append(
            f"Base resume is PDF ({resume.name}). Prefer .docx or .md for reliable text extraction."
        )

    # Schedule placeholders
    if "[START TIME]" in text or "[END TIME]" in text or "[TIME ZONE]" in text:
        blockers.append("Set Daily window START, END, and TIME ZONE in memory/PROFILE.md.")

    # Work auth still placeholder-like
    if "always ask me" in text.lower():
        warnings.append(
            "Work authorization is 'always ask me' — every application will go to needs me for that field."
        )

    return GateResult(ok=not blockers, blockers=blockers, warnings=warnings)


def write_needs_me_packet(result: GateResult) -> Path:
    out_dir = paths.APPLICATIONS / "needs-me"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "SETUP.md"
    out.write_text(result.as_needs_me(), encoding="utf-8")
    return out
