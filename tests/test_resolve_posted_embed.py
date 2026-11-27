from agent.job_search import resolve_posted_at


def test_greenhouse_embed_for_token_resolves_mongodb():
    posted = resolve_posted_at(
        "https://job-boards.greenhouse.io/embed/job_app?for=mongodb&token=8352433"
    )
    assert posted
    assert posted.startswith("2026-11-05")


def test_greenhouse_embed_abnormal():
    posted = resolve_posted_at(
        "https://job-boards.greenhouse.io/embed/job_app?for=abnormalsecurity&token=8196352003"
    )
    assert posted
    assert "2026-11-12" in posted
