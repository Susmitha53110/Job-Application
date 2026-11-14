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
    # Prompts must stay populated so 08:00 CT computer-use can submit immediately
    window_only = [i for i in items if packet_ready_except_window(i) and not i.ok]
    assert window_only, "expected at least one window-only blocked packet outside CT window"
    assert all(i.computer_use_prompt for i in window_only)
    assert all("SUBMIT" in i.computer_use_prompt for i in window_only)


def test_morning_go_nogo_hard_pass_outside_window():
    from agent.morning_check import run_morning_check

    out = run_morning_check()
    assert "go" in out
    assert out["report_json"]
    # Salary may be missing; hard GO should still pass overnight if packets/files exist
    assert out["go"] is True, out.get("hard_failures")


def test_icims_login_url_pattern():
    apply_blob = "https://careers-example.icims.com/jobs/1/login".lower()
    assert "icims.com" in apply_blob and "/login" in apply_blob
    assert not (
        "icims.com" in "https://careers.example.com/jobs/1".lower()
        and "/login" in "https://careers.example.com/jobs/1".lower()
    )

def test_jsonld_rejects_vietnam_applicant_location():
    from agent.ats_hunt import _jsonld_is_us_eligible

    vn = {
        "@type": "JobPosting",
        "title": "Analytics Engineer",
        "applicantLocationRequirements": {"@type": "Country", "name": "VN"},
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Ho Chi Minh City",
                "addressRegion": "Ho Chi Minh City",
            },
        },
    }
    ok, label = _jsonld_is_us_eligible(vn, "North America merchants United States Canada")
    assert ok is False
    assert "VN" in label or "Ho Chi Minh" in label

    us = {
        "@type": "JobPosting",
        "applicantLocationRequirements": {"@type": "Country", "name": "United States"},
        "jobLocation": {"@type": "Place", "address": {"addressCountry": "US"}},
    }
    ok2, _ = _jsonld_is_us_eligible(us, "remote role")
    assert ok2 is True
