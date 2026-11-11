from __future__ import annotations

import argparse
import json
import sys

from .ats_hunt import hunt_all
from .curve_apply import evaluate_curve_gate, write_gate_report
from .daily_apply import run_daily
from .dry_run import run_dry_run
from .morning_run import readiness_report
from .proof import require_proof_for_applied, write_proof_manifest
from .salary import set_salary
from .setup_gate import check_setup, write_needs_me_packet
from .watchlist import poll_watchlist, write_watchlist_report
from .window import check_apply_window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Susmitha job-application agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check-setup", help="Validate Memory profile + base resume")
    p_dry = sub.add_parser("dry-run", help="Prepare 3 jobs without submitting")
    p_dry.add_argument("--limit", type=int, default=3)
    sub.add_parser("window", help="Check whether the CT apply window is open")
    sub.add_parser("hunt", help="Hunt Greenhouse/Ashby/Rippling for filter-pass jobs")
    sub.add_parser("watchlist", help="Poll target-company ATS watchlist for mid-level hits")
    sub.add_parser("ready", help="Write morning readiness report (window/salary/queue)")
    p_daily = sub.add_parser("daily", help="Run daily hunt/readiness/report cycle")
    p_daily.add_argument("--dry", action="store_true", help="Force prepare-only (no submit guidance)")
    sub.add_parser("curve-gate", help="Evaluate Curve Dental submit gate + write prompt")
    p_sal = sub.add_parser("set-salary", help="Save Susmitha-provided salary expectation")
    p_sal.add_argument("amount", help="Yearly USD number, e.g. 120000")
    p_proof = sub.add_parser("proof", help="Write proof manifest for an apply attempt")
    p_proof.add_argument("--company", required=True)
    p_proof.add_argument("--role", required=True)
    p_proof.add_argument("--url", required=True)
    p_proof.add_argument("--notes", default="")
    p_proof.add_argument("--file", action="append", default=[], help="Proof file path (repeatable)")

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

    if args.cmd == "watchlist":
        jobs = poll_watchlist()
        report = write_watchlist_report(jobs)
        print(
            json.dumps(
                {
                    "count": len(jobs),
                    "report": str(report),
                    "jobs": [
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
                },
                indent=2,
            )
        )
        return 0

    if args.cmd == "ready":
        print(json.dumps(readiness_report(), indent=2))
        return 0

    if args.cmd == "daily":
        # Outside window always prepare-only; --dry forces prepare-only even in-window
        window = check_apply_window()
        force_dry = bool(args.dry) or (not window.open)
        print(json.dumps(run_daily(dry=force_dry), indent=2))
        return 0

    if args.cmd == "curve-gate":
        gate = evaluate_curve_gate()
        report = write_gate_report()
        print(json.dumps({"ok": gate.ok, "blockers": gate.blockers, "salary": gate.salary, "report": str(report)}, indent=2))
        return 0 if gate.ok else 4

    if args.cmd == "set-salary":
        try:
            out = set_salary(args.amount)
        except ValueError as e:
            print(json.dumps({"ok": False, "error": str(e)}, indent=2))
            return 2
        print(json.dumps({"ok": True, **out}, indent=2))
        return 0

    if args.cmd == "proof":
        status = require_proof_for_applied(args.file)
        path = write_proof_manifest(
            company=args.company,
            role=args.role,
            url=args.url,
            status=status,
            notes=args.notes,
            proof_files=args.file,
        )
        print(json.dumps({"status": status, "manifest": str(path), "proof_files": args.file}, indent=2))
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
