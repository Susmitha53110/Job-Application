from __future__ import annotations

import argparse
import json
import sys

from .ats_hunt import hunt_all
from .curve_apply import evaluate_curve_gate, write_gate_report
from .daily_apply import run_daily
from .dry_run import run_dry_run
from .morning_run import readiness_report
from .overnight_hunt import run_overnight_hunt
from .proof import require_proof_for_applied, write_proof_manifest
from .ready_submits import evaluate_all_ready_submits, packet_ready_except_window, write_ready_submits_report
from .salary import set_salary
from .setup_gate import check_setup, write_needs_me_packet
from .morning_check import run_morning_check
from .submit_handoff import build_submit_handoff
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
    sub.add_parser("overnight", help="Prepare-only overnight hunt (never submits)")
    sub.add_parser("prewarm", help="7:55 CT age-check morning queue (never submits)")
    p_q = sub.add_parser("queue-submit", help="Submit prepared morning queue (window-gated)")
    p_q.add_argument("--dry", action="store_true", help="List queue only; no submit")
    p_q.add_argument("--limit", type=int, default=None, help="Max items to attempt")
    sub.add_parser("curve-gate", help="Evaluate Curve Dental submit gate + write prompt")
    sub.add_parser("ready-submits", help="Evaluate morning ready-submit gates")
    sub.add_parser("handoff", help="Write SUBMIT_HANDOFF.json for morning computer-use")
    sub.add_parser("go-nogo", help="Morning go/no-go readiness checklist")
    p_sal = sub.add_parser("set-salary", help="Save Susmitha-provided salary expectation")
    p_sal.add_argument("amount", help="Yearly USD number, e.g. 120000")
    p_proof = sub.add_parser("proof", help="Write proof manifest for an apply attempt")
    p_proof.add_argument("--company", required=True)
    p_proof.add_argument("--role", required=True)
    p_proof.add_argument("--url", required=True)
    p_proof.add_argument("--notes", default="")
    p_proof.add_argument("--file", action="append", default=[], help="Proof file path (repeatable)")
    p_gh = sub.add_parser("gh-fill", help="Greenhouse/Ashby Playwright fill (default fill-only; --submit in-window)")
    p_gh.add_argument("--company", required=True, choices=["mongodb", "machinify", "mux"])
    p_gh.add_argument("--submit", action="store_true", help="Click Submit (requires open CT window)")
    p_gh.add_argument("--security-code", default=None, help="8-char email OTP if prompted")

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

    if args.cmd == "overnight":
        print(json.dumps(run_overnight_hunt(), indent=2))
        return 0

    if args.cmd == "prewarm":
        from .morning_prewarm import prewarm

        print(json.dumps(prewarm(), indent=2))
        return 0

    if args.cmd == "queue-submit":
        from .morning_queue_submit import submit_queue

        out = submit_queue(dry=bool(args.dry), limit=args.limit)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 3

    if args.cmd == "curve-gate":
        gate = evaluate_curve_gate()
        report = write_gate_report()
        print(json.dumps({"ok": gate.ok, "blockers": gate.blockers, "salary": gate.salary, "report": str(report)}, indent=2))
        return 0 if gate.ok else 4

    if args.cmd == "ready-submits":
        items = evaluate_all_ready_submits()
        report = write_ready_submits_report()
        print(
            json.dumps(
                {
                    "report": str(report),
                    "items": [
                        {
                            "key": i.key,
                            "company": i.company,
                            "role": i.role,
                            "ok": i.ok,
                            "needs_salary": i.needs_salary,
                            "blockers": i.blockers,
                            "url": i.url,
                            "resume": str(i.resume),
                        }
                        for i in items
                    ],
                },
                indent=2,
            )
        )
        # Outside window is expected overnight; succeed if packets are otherwise ready.
        return 0 if any(packet_ready_except_window(i) for i in items) else 4

    if args.cmd == "handoff":
        print(json.dumps(build_submit_handoff(), indent=2))
        return 0

    if args.cmd == "go-nogo":
        out = run_morning_check()
        print(json.dumps(out, indent=2))
        return 0 if out.get("go") else 2

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

    if args.cmd == "gh-fill":
        from pathlib import Path

        from .greenhouse_pw import submit_greenhouse_basic
        from . import paths

        specs = {
            "mongodb": {
                "company": "MongoDB",
                "ats": "greenhouse",
                "url": "https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433",
                "resume": paths.ROOT / "resumes" / "submit" / "Susmitha_mongodb.docx",
            },
            "machinify": {
                "company": "Machinify",
                "ats": "greenhouse",
                "url": "https://job-boards.greenhouse.io/machinifyinc/jobs/4478208009",
                "resume": paths.ROOT / "resumes" / "submit" / "Susmitha_machinify.docx",
            },
            "mux": {
                "company": "mux",
                "ats": "ashby",
                "url": "https://jobs.ashbyhq.com/mux/bf4007f4-3610-4a67-acd6-0e7a7f11dbbe",
                "resume": paths.ROOT / "resumes" / "submit" / "Susmitha_mux.docx",
            },
        }
        spec = specs[args.company]
        day = __import__("datetime").date.today().isoformat()
        proof = paths.APPLICATIONS / "applied" / day / f"{spec['company']}_Sr_fill"
        do_submit = bool(args.submit)
        if do_submit and not check_apply_window().open:
            print(json.dumps({"ok": False, "error": "Submit blocked outside CT window"}, indent=2))
            return 4
        if spec["ats"] == "ashby":
            from .ashby_pw import submit_ashby_basic

            result = submit_ashby_basic(
                url=spec["url"],
                resume=Path(spec["resume"]),
                proof_dir=proof,
                company=spec["company"],
                security_code=args.security_code,
                require_window=do_submit,
                fill_only=not do_submit,
            )
        else:
            result = submit_greenhouse_basic(
                url=spec["url"],
                resume=Path(spec["resume"]),
                proof_dir=proof,
                company=spec["company"],
                security_code=args.security_code,
                require_window=do_submit,
                fill_only=not do_submit,
            )
        print(
            json.dumps(
                {
                    "ok": result.success,
                    "url": result.url,
                    "needs_me": result.needs_me,
                    "fill_only": not do_submit,
                    "proof_dir": str(result.proof_dir) if result.proof_dir else None,
                    "snippet": (result.confirmation_text or "")[:400],
                },
                indent=2,
            )
        )
        return 0 if result.success and not result.needs_me else 2

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
