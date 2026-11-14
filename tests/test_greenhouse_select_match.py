from agent.greenhouse_pw import match_select_option


def test_female_not_male_substring():
    opts = ["Male", "Female", "Decline to self-identify"]
    assert match_select_option(["Female", "Woman"], opts) == "Female"
    assert match_select_option(["Male", "Man"], opts) == "Male"


def test_no_not_another_substring():
    opts = [
        "Yes",
        "No",
        "I am currently working or have worked at a SpaceXSI, SpaceX, or xAI facility for another employer",
    ]
    assert match_select_option(["No"], opts) == "No"


def test_company_website_prefers_exactish():
    opts = ["Mercer Company Website", "Company website", "LinkedIn", "Other"]
    assert match_select_option(
        ["Company website", "Company Website", "Website", "LinkedIn", "Other"],
        opts,
    ) == "Company website"


def test_short_yes_exact_only():
    opts = ["Yes", "No", "Not sure yet"]
    assert match_select_option(["Yes"], opts) == "Yes"
    # "yes" must not fuzzy-match "Not sure yet"
    assert match_select_option(["Yes"], ["Not sure yet", "Maybe"]) is None
