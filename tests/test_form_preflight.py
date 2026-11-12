from agent.form_preflight import MULTIYEAR_NO_SPONSOR, _scan_label, preflight_greenhouse


def test_multiyear_no_sponsor_regex():
    q = "Are you located in and able to work in the US without visa sponsorship for the next 5 years?"
    assert MULTIYEAR_NO_SPONSOR.search(q)
    blockers, _ = _scan_label(q, required=True)
    assert blockers and "multi-year no-sponsorship" in blockers[0]


def test_standard_sponsorship_question_not_multiyear_trap():
    q = "Do you require sponsorship to work in the country listed for employment now or in the future?"
    assert not MULTIYEAR_NO_SPONSOR.search(q)
    blockers, _ = _scan_label(q, required=True)
    assert blockers == []


def test_betterhelp_preflight_blocks_live():
    pf = preflight_greenhouse("betterhelpcom", 5475004008)
    assert not pf.ok
    assert any("multi-year no-sponsorship" in b for b in pf.blockers)


def test_life360_preflight_allows_standard_sponsorship():
    pf = preflight_greenhouse("life360", 8935286002)
    assert pf.ok, pf.blockers
    assert any("sponsorship" in q.lower() for q in pf.questions)
