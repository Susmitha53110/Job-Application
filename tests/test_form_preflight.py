from agent.form_preflight import MULTIYEAR_NO_SPONSOR, _scan_label, preflight_greenhouse


def test_multiyear_no_sponsor_regex():
    q = "Are you located in and able to work in the US without visa sponsorship for the next 5 years?"
    assert MULTIYEAR_NO_SPONSOR.search(q)
    blockers, warnings = _scan_label(q, required=True)
    # Standing Memory: sponsorship No → answer Yes; warn only, do not hard-block.
    assert blockers == []
    assert warnings and "Multi-year no-sponsorship Q" in warnings[0]


def test_standard_sponsorship_question_not_multiyear_trap():
    q = "Do you require sponsorship to work in the country listed for employment now or in the future?"
    assert not MULTIYEAR_NO_SPONSOR.search(q)
    blockers, _ = _scan_label(q, required=True)
    assert blockers == []


def test_betterhelp_preflight_allows_with_standing_sponsorship_no():
    pf = preflight_greenhouse("betterhelpcom", 5475004008)
    assert pf.ok, pf.blockers
    assert any("Multi-year no-sponsorship Q" in w for w in pf.warnings)


def test_life360_preflight_allows_standard_sponsorship():
    pf = preflight_greenhouse("life360", 8935286002)
    assert pf.ok, pf.blockers
    assert any("sponsorship" in q.lower() for q in pf.questions)
