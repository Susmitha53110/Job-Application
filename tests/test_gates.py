from pathlib import Path

from agent import paths
from agent.salary import ingest_salary_reply_file, parse_salary_from_text, salary_from_memory, set_salary
from agent.window import check_apply_window
from agent.job_search import is_us_remote


def test_parse_salary_table_and_line():
    assert parse_salary_from_text("| Salary expectations | 135000 |") == "135000"
    assert parse_salary_from_text("Salary expectations: 120000") == "120000"
    assert parse_salary_from_text("only **NEEDS ME** here") is None


def test_salary_reply_drop_file_ingest(tmp_path, monkeypatch):
    needs = tmp_path / "needs-me"
    needs.mkdir()
    apps = tmp_path
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setattr(paths, "APPLICATIONS", apps)
    monkeypatch.setattr(paths, "STATE", mem / "STATE.md")
    monkeypatch.setattr(paths, "SETUP_STATUS", mem / "SETUP_STATUS.md")
    (mem / "STATE.md").write_text("# Runtime state\n- setup_complete: true\n", encoding="utf-8")
    reply = needs / "SALARY_REPLY.md"
    reply.write_text("135000\n", encoding="utf-8")
    assert ingest_salary_reply_file() == "135000"
    assert salary_from_memory() == "135000"
    # Reset path used by other tests via monkeypatch teardown


def test_us_remote_patterns():
    assert is_us_remote("Remote, US", "", title="Data Engineer", source="greenhouse")
    assert is_us_remote("US - Remote", "", title="Data Engineer", source="greenhouse")
    assert is_us_remote("Remote (United States)", "", title="Data Engineer", source="rippling")
    assert not is_us_remote("Remote", "Please join us on our mission", title="Engineer", source="greenhouse")
    # Jobicy remote-jobs feed often sets jobGeo=USA without "remote" in the short blob
    assert is_us_remote("USA", "", title="Senior Analytics Engineer", source="jobicy")
    assert not is_us_remote("Argentina", "", title="Data Engineer", source="jobicy")


def test_window_status_shape():
    status = check_apply_window()
    assert hasattr(status, "open")
    assert hasattr(status, "reason")


def test_ready_submits_only_window_blocked_outside():
    from agent.ready_submits import evaluate_all_ready_submits, packet_ready_except_window

    items = evaluate_all_ready_submits()
    assert len(items) >= 2
    # Outside CT window these should still be packet-ready for morning
    assert any(packet_ready_except_window(i) for i in items)


def test_morning_go_nogo_hard_pass_outside_window():
    from agent.morning_check import run_morning_check

    out = run_morning_check()
    assert "go" in out
    assert out["report_json"]
    # Salary may be missing; hard GO should still pass overnight if packets/files exist
    assert out["go"] is True, out.get("hard_failures")


def test_icims_login_url_flagged_needs_me():
    from agent.job_search import JobPosting
    from agent.process_job import process_job
    from agent.resume_parse import load_base_resume
    from agent.setup_gate import find_base_resume

    resume = load_base_resume(find_base_resume())
    job = JobPosting(
        title="Data Engineer",
        company="LoginGateCo",
        url="https://careers-example.icims.com/jobs/1/login",
        location="United States, Remote",
        description="Remote United States data engineer SQL Python Azure 3-5 years experience",
        source="test",
        posted_at="2026-11-11T12:00:00+00:00",
        apply_url="https://careers-example.icims.com/jobs/1/login",
        is_open=True,
        country_hint="US",
    )
    pkt = process_job(resume, job, dry_run=True, my_years=5, day="2026-11-11")
    assert "iCIMS" in pkt.reason
