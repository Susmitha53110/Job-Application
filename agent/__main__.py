from __future__ import annotations

import argparse
import json
import sys

from .ats_hunt import hunt_all
from .dry_run import run_dry_run
from .setup_gate import check_setup, write_needs_me_packet
from .window import check_apply_window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Susmitha job-application agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check-setup", help="Validate Memory profile + base resume")
    p_dry = sub.add_parser("dry-run", help="Prepare 3 jobs without submitting")
    p_dry.add_argument("--limit", type=int, default=3)
    sub.add_parser("window", help="Check whether the CT apply window is open")
    sub.add_parser("hunt", help="Hunt Greenhouse/Ashby/Rippling for filter-pass jobs")

    args = parser.parse_args(argv)

    if args.cmd == "check-setup":
        result = check_setup()
        packet = write_needs_me_packet(result)
        print(json.dumps({"ok": result.ok, "blockers": result.blockers, "warnings": result.warnings, "needs_me": str(packet)}, indent=2))
        return 0 if result.ok else 2

    if args.cmd == "window":
        status = check_apply_window()
        print(json.dumps({"open": status.open, "now": status.now_local.isoformat(), "reason": status.reason}, indent=2))
        return 0 if status.open else 3

    if args.cmd == "hunt":
        jobs = hunt_all()
        print(
            json.dumps(
                [
                    {
                        "company": j.company,
                        "title": j.title,
                        "posted_at": j.posted_at,
                        "location": j.location,
                        "url": j.url,
                        "source": j.source,
                    }
                    for j in jobs
                ],
                indent=2,
            )
        )
        return 0

    if args.cmd == "dry-run":
        out = run_dry_run(limit=args.limit)
        # Compact serializable summary
        summary = {
            "ok": out.get("ok"),
            "report": out.get("report"),
            "needs_me": out.get("needs_me"),
            "jobs": [
                {
                    "company": j.company,
                    "role": j.role,
                    "url": j.url,
                    "scores": [j.score_a, j.score_b, j.score_c],
                    "status": j.status,
                    "resume_a": str(j.resume_a),
                    "catch_note": str(j.catch_note),
                    "additions": j.additions_flagged,
                }
                for j in out.get("jobs", [])
            ],
        }
        print(json.dumps(summary, indent=2))
        return 0 if out.get("ok") else 2

    return 1


if __name__ == "__main__":
    sys.exit(main())
