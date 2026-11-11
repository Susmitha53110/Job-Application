from agent.salary import parse_salary_from_text
from agent.window import check_apply_window
from agent.job_search import is_us_remote


def test_parse_salary_table_and_line():
    assert parse_salary_from_text("| Salary expectations | 135000 |") == "135000"
    assert parse_salary_from_text("Salary expectations: 120000") == "120000"
    assert parse_salary_from_text("only **NEEDS ME** here") is None


def test_us_remote_patterns():
    assert is_us_remote("Remote, US", "", title="Data Engineer", source="greenhouse")
    assert is_us_remote("US - Remote", "", title="Data Engineer", source="greenhouse")
    assert is_us_remote("Remote (United States)", "", title="Data Engineer", source="rippling")
    assert not is_us_remote("Remote", "Please join us on our mission", title="Engineer", source="greenhouse")


def test_window_status_shape():
    status = check_apply_window()
    assert hasattr(status, "open")
    assert hasattr(status, "reason")
