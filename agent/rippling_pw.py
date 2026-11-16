"""Playwright helpers for Rippling ATS apply forms (BookNook / Curve-style).

Does not bypass Cloudflare/CAPTCHA. Outside-window use fill_only=True only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .window import check_apply_window


@dataclass
class RipplingSubmitResult:
    success: bool
    url: str
    needs_me: str | None
    confirmation_text: str
    proof_dir: Path | None


FAVORITE_PROJECT = (
    "At Optum I rebuilt claims ingestion on Azure Data Factory + Databricks into a "
    "Delta Lake bronze-silver-gold model with Snowflake loads via COPY INTO / MERGE. "
    "It cut new-source onboarding from ~2 weeks to ~4 days and raised scheduled pipeline "
    "success from ~97% to 99.5% — favorite because analysts could trust the silver layer "
    "and I owned the end-to-end reliability path."
)


def _click_apply(page) -> None:
    for role, name in (
        ("button", r"^Apply now$"),
        ("link", r"^Apply now$"),
        ("button", r"^Apply$"),
        ("link", r"^Apply$"),
        ("button", r"Apply for this"),
        ("link", r"Apply for this"),
    ):
        loc = page.get_by_role(role, name=re.compile(name, re.I))
        if loc.count():
            try:
                loc.first.click(timeout=3000)
                page.wait_for_timeout(1500)
                return
            except Exception:
                pass
    for sel in (
        "a:has-text('Apply now')",
        "button:has-text('Apply now')",
        "a:has-text('Apply')",
        "button:has-text('Apply')",
    ):
        loc = page.locator(sel)
        if loc.count():
            try:
                loc.first.click(timeout=3000)
                page.wait_for_timeout(1500)
                return
            except Exception:
                pass


def _following_input(page, question: str, value: str, *, which: int = 0, textarea: bool = False) -> bool:
    """Fill the Nth input/textarea after a question label (Rippling layout)."""
    try:
        loc = page.get_by_text(re.compile(question, re.I)).first
        if textarea:
            inp = loc.locator(f"xpath=following::textarea[{which + 1}]")
        else:
            inp = loc.locator(
                "xpath=following::input[not(@type='hidden') and not(@type='file') "
                f"and not(@type='radio') and not(@type='checkbox')][{which + 1}]"
            )
        if not inp.count():
            return False
        inp.first.click(timeout=2000)
        inp.first.fill("")
        inp.first.fill(value)
        return True
    except Exception:
        return False


def _select_following(page, question: str, option: str) -> bool:
    """Click the Select/Select... control after a question, then choose option."""
    try:
        loc = page.get_by_text(re.compile(question, re.I)).first
        trig = loc.locator(
            "xpath=following::*[normalize-space()='Select' or normalize-space()='Select...'][1]"
        )
        if not trig.count():
            trig = loc.locator("xpath=following::*[@role='combobox'][1]")
        trig.first.click(timeout=3000)
        page.wait_for_timeout(400)
        opt = page.locator("[role=option]").filter(has_text=re.compile(rf"^{re.escape(option)}$", re.I))
        if not opt.count():
            opt = page.get_by_text(re.compile(rf"^{re.escape(option)}$", re.I))
        if not opt.count():
            # partial match for long veteran wording
            opt = page.locator("[role=option]").filter(has_text=re.compile(option, re.I))
        opt.first.click(timeout=3000)
        page.wait_for_timeout(250)
        return True
    except Exception:
        return False


def submit_rippling_basic(
    *,
    url: str,
    resume: Path,
    proof_dir: Path,
    company: str,
    name: str = "Susmitha Chowdary",
    email: str = "dsusmitha55@gmail.com",
    phone: str | None = "9132073787",
    linkedin: str = "https://www.linkedin.com/in/susmitha-dodla-a05ab92b8",
    location: str = "Austin, TX",
    state: str = "TX",
    current_company: str = "Optum",
    favorite_project: str | None = None,
    require_window: bool = True,
    fill_only: bool = False,
) -> RipplingSubmitResult:
    if require_window and not fill_only:
        win = check_apply_window()
        if not win.open:
            return RipplingSubmitResult(False, url, win.reason, "", None)
        try:
            from .job_search import assert_url_within_max_age

            ok_age, age_detail = assert_url_within_max_age(url)
            if not ok_age:
                return RipplingSubmitResult(False, url, f"Age gate: {age_detail}", "", None)
        except Exception as e:
            return RipplingSubmitResult(False, url, f"Age gate error: {e}", "", None)

    from playwright.sync_api import sync_playwright

    proof_dir.mkdir(parents=True, exist_ok=True)
    resume = resume.resolve()
    if not resume.exists():
        return RipplingSubmitResult(False, url, f"Missing resume: {resume}", "", proof_dir)

    first, _, last = name.partition(" ")
    last = last.strip() or first
    story = favorite_project or FAVORITE_PROJECT

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 2400},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(1500)
        if "step=application" not in page.url and "/apply" not in page.url:
            _click_apply(page)
            page.wait_for_timeout(2000)

        html = page.content().lower()
        if "cf-challenge" in html or "checking your browser" in html:
            page.screenshot(path=str(proof_dir / "cloudflare.png"), full_page=True)
            browser.close()
            return RipplingSubmitResult(
                False, page.url, "Rippling Cloudflare challenge — needs you", "", proof_dir
            )

        try:
            files = page.locator("input[type=file]")
            if files.count():
                files.first.set_input_files(str(resume))
                page.wait_for_timeout(2800)
        except Exception:
            pass

        _following_input(page, r"^First name\*", first)
        _following_input(page, r"^Last name\*", last)
        _following_input(page, r"^Email\*", email)
        _following_input(page, r"^Current company$", current_company)
        if phone:
            # first following input is often country (+1 US); number is 2nd
            if not _following_input(page, r"^Phone number\*", phone, which=1):
                _following_input(page, r"^Phone number\*", phone, which=0)
        # Location often requires Places autocomplete pick (e.g. "Austin, TX, USA")
        try:
            loc_lab = page.get_by_text(re.compile(r"^Location\*", re.I)).first
            loc_inp = loc_lab.locator("xpath=following::input[not(@type='hidden')][1]")
            loc_inp.click()
            loc_inp.fill("")
            loc_inp.type(location, delay=40)
            page.wait_for_timeout(900)
            opt = page.locator("[role=option]").filter(has_text=re.compile(r"Austin", re.I))
            if opt.count():
                opt.first.click()
            else:
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
            page.wait_for_timeout(300)
        except Exception:
            _following_input(page, r"^Location\*", location)
        _following_input(page, r"^LinkedIn Link\*|^LinkedIn", linkedin)
        if not _following_input(page, r"favorite data project|favourite data project", story, textarea=True):
            _following_input(page, r"favorite data project|favourite data project", story)
        # Curve-style long-form / standing answers
        if not _following_input(
            page,
            r"data platform you built|significantly improved|What was broken",
            story,
            textarea=True,
        ):
            _following_input(page, r"data platform you built|significantly improved", story)
        try:
            from .salary import salary_from_memory

            sal = str(salary_from_memory() or "120000")
        except Exception:
            sal = "120000"
        _following_input(page, r"salary expectations|salary expectation", sal)
        _following_input(page, r"How did you hear|where did you find this job", "Company website")
        _following_input(page, r"years of related experience", "5")
        _select_following(page, r"home office.*reliable internet|reliable internet", "Yes")

        # Work auth — permanently authorized: No (F1-OPT is temporary)
        _select_following(page, r"permanently authorized to work", "No")
        _select_following(page, r"require sponsorship|sponsorship \(STEM", "No")
        _select_following(page, r"require sponsorship to work in the US", "No")

        # State of residence (BookNook TX-ok list) — type + pick option, then Tab to commit
        try:
            loc = page.get_by_text(re.compile(r"state of residence", re.I)).first
            cb = loc.locator("xpath=following::input[@role='combobox'][1]")
            if cb.count():
                cb.first.click()
                cb.first.fill("")
                cb.first.type(state, delay=60)
                page.wait_for_timeout(600)
                opt = page.locator("[role=option]").filter(
                    has_text=re.compile(rf"^{re.escape(state)}$|^{re.escape(state)}\b|Texas", re.I)
                )
                if opt.count():
                    opt.first.click()
                else:
                    page.keyboard.press("Enter")
                page.keyboard.press("Tab")
                page.wait_for_timeout(300)
            else:
                _select_following(page, r"state of residence", state)
        except Exception:
            _following_input(page, r"state of residence", state)

        # Gender — re-open and force Female (avoid wrong Select match)
        try:
            g = page.get_by_text(re.compile(r"^Gender$", re.I)).first
            trig = g.locator(
                "xpath=following::*[normalize-space()='Select' or normalize-space()='Select...' or normalize-space()='Female' or normalize-space()='Male'][1]"
            )
            trig.first.click()
            page.wait_for_timeout(350)
            page.locator("[role=option]").filter(has_text=re.compile(r"^Female$", re.I)).first.click()
            page.wait_for_timeout(200)
        except Exception:
            _select_following(page, r"^Gender$", "Female")
        # Race via typeahead option
        try:
            race = page.get_by_text(re.compile(r"identify your race", re.I)).first
            ri = race.locator("xpath=following::input[1]")
            ri.click()
            ri.fill("")
            ri.type("Asian", delay=40)
            page.wait_for_timeout(500)
            ro = page.locator("[role=option]").filter(has_text=re.compile(r"^Asian", re.I))
            if ro.count():
                ro.first.click()
            page.keyboard.press("Tab")
        except Exception:
            _following_input(page, r"identify your race", "Asian")
        _select_following(page, r"Hispanic/Latino", "No")
        if not _select_following(page, r"Veteran Status", "I am not a protected veteran"):
            _select_following(page, r"Veteran Status", "Not a veteran")

        try:
            page.get_by_text(re.compile(r"No - I do not consent", re.I)).first.click(timeout=2000)
        except Exception:
            pass
        # Race sometimes needs option click after typing
        try:
            race = page.get_by_text(re.compile(r"identify your race", re.I)).first
            race.locator("xpath=following::input[1]").click()
            race.locator("xpath=following::input[1]").fill("Asian")
            page.wait_for_timeout(400)
            opt = page.locator("[role=option]").filter(has_text=re.compile(r"^Asian", re.I))
            if opt.count():
                opt.first.click()
        except Exception:
            pass
        # Re-assert SMS No (autofill/resume parse can clear radios)
        try:
            page.get_by_text(re.compile(r"No - I do not consent", re.I)).first.click(timeout=2000)
        except Exception:
            pass

        page.screenshot(path=str(proof_dir / "filled.png"), full_page=True)
        try:
            (proof_dir / "filled_url.txt").write_text(page.url, encoding="utf-8")
            vals = page.evaluate(
                """() => Object.fromEntries([...document.querySelectorAll('input,textarea')]
                  .filter(e => !['file','radio','checkbox','hidden'].includes(e.type||''))
                  .map(e => [e.id||e.name, e.value]))"""
            )
            import json

            (proof_dir / "filled_values.json").write_text(json.dumps(vals, indent=2), encoding="utf-8")
        except Exception:
            pass

        if fill_only:
            browser.close()
            return RipplingSubmitResult(True, page.url, None, "fill_only", proof_dir)

        # Turnstile widget often injects late; also check visible verify checkbox.
        try:
            
        # TURNSTILE_CLICK_TRY: attempt checkbox / iframe click once before needs-me
        try:
            page.get_by_text(re.compile(r"verify you are human", re.I)).first.click(timeout=2000)
            page.wait_for_timeout(2500)
        except Exception:
            pass
        try:
            frame = page.frame_locator("iframe[src*='turnstile'], iframe[src*='challenges.cloudflare']").first
            frame.locator("body").click(timeout=2000)
            page.wait_for_timeout(3000)
        except Exception:
            pass
        # if still visible, fall through to needs-me

        if page.get_by_text(re.compile(r"verify you are human", re.I)).count():
                page.screenshot(path=str(proof_dir / "needs_captcha.png"), full_page=True)
                browser.close()
                return RipplingSubmitResult(
                    False, page.url, "Rippling Cloudflare Turnstile — needs you", "", proof_dir
                )
        except Exception:
            pass
        html2 = page.content().lower()
        if "recaptcha" in html2 or "hcaptcha" in html2 or "cf-turnstile" in html2 or "turnstile" in html2:
            page.screenshot(path=str(proof_dir / "needs_captcha.png"), full_page=True)
            browser.close()
            return RipplingSubmitResult(
                False, page.url, "Rippling CAPTCHA — needs you", "", proof_dir
            )

        try:
            page.get_by_role("button", name=re.compile(r"^Apply$", re.I)).first.click(timeout=5000)
        except Exception:
            try:
                page.locator("button[type=submit], input[type=submit]").first.click(timeout=5000)
            except Exception as e:
                browser.close()
                return RipplingSubmitResult(False, page.url, f"Apply click failed: {e}", "", proof_dir)

        page.wait_for_timeout(3500)
        page.screenshot(path=str(proof_dir / "after_submit.png"), full_page=True)
        body = ""
        try:
            body = page.inner_text("body")
        except Exception:
            pass
        (proof_dir / "after_submit.txt").write_text(body[:4000], encoding="utf-8")

        conf_ok = bool(
            re.search(
                r"thank you|application (has been )?submitted|successfully submitted|"
                r"we (have )?received your application|application received",
                body,
                re.I,
            )
        )
        if re.search(r"captcha|cloudflare|verify you are human", body, re.I):
            browser.close()
            return RipplingSubmitResult(
                False, page.url, "Rippling CAPTCHA/verify after Apply — needs you", body[:300], proof_dir
            )
        # Only treat explicit validation banners as errors — NOT question copy like
        # "Please select your current state of residence".
        if (
            re.search(
                r"(this field is required|field is required|required field|"
                r"please (complete|fill|fix) (all|the|this)|"
                r"fix to (continue|submit)|missing required)",
                body,
                re.I,
            )
            and not conf_ok
        ):
            browser.close()
            return RipplingSubmitResult(
                False, page.url, "Rippling validation errors after Apply — needs you", body[:300], proof_dir
            )
        # Still on apply form (Apply button visible) ⇒ not confirmed
        still_form = bool(re.search(r"^Apply$|^Apply - ", body, re.M)) or (
            "step=application" in (page.url or "") and not conf_ok
        )
        browser.close()
        if conf_ok:
            return RipplingSubmitResult(True, url, None, body[:500], proof_dir)
        if still_form:
            return RipplingSubmitResult(
                False, url, "Rippling still on application form after Apply — needs you", body[:300], proof_dir
            )
        return RipplingSubmitResult(False, url, "Submit not confirmed", body[:300], proof_dir)
