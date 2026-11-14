"""Playwright helpers for Greenhouse job-board forms (fill + optional OTP).

Used at 08:00 CT for ready submits. Does not bypass CAPTCHA; if an 8-char
email security code is required, pass security_code or stop needs-me.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .window import check_apply_window


@dataclass
class GhSubmitResult:
    success: bool
    url: str
    needs_me: str | None
    confirmation_text: str
    proof_dir: Path | None


def _set_val(page, eid: str, val: str) -> bool:
    loc = _by_id(page, eid)
    try:
        if not loc.count():
            return False
        loc.scroll_into_view_if_needed()
        loc.click(timeout=3000)
        loc.fill("")
        loc.fill(val)
        # Also dispatch React-friendly setter in case fill was ignored
        page.evaluate(
            """(args) => {
      const el = document.getElementById(args.id);
      if (!el) return false;
      el.focus();
      const setter =
        Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value")?.set ||
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set ||
        Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
      if (setter) setter.call(el, args.val);
      else el.value = args.val;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    }""",
            {"id": eid, "val": val},
        )
        return True
    except Exception:
        return bool(
            page.evaluate(
                """(args) => {
          const el = document.getElementById(args.id);
          if (!el) return false;
          el.focus();
          const setter =
            Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), "value")?.set ||
            Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set ||
            Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
          if (setter) setter.call(el, args.val);
          else el.value = args.val;
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.dispatchEvent(new Event("change", { bubbles: true }));
          return true;
        }""",
                {"id": eid, "val": val},
            )
        )


def _close_overlays(page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(80)
    page.evaluate(
        """() => {
      document.querySelectorAll(".iti__country-list").forEach((el) => el.classList.add("iti__hide"));
    }"""
    )


def _by_id(page, eid: str):
    """Locator for any element id, including numeric Greenhouse EEO ids."""
    if not eid:
        return page.locator("html")  # empty-safe; callers check count
    return page.locator(f'[id="{eid}"]')


def _norm_option(s: str) -> str:
    """Country menus often show 'United States +1' — match on name only."""
    return re.sub(r"\s*\+\d+\s*$", "", (s or "").strip()).lower()


def match_select_option(candidates: list[str], texts: list[str]) -> str | None:
    """Pick a Greenhouse react-select option for the first matching candidate.

    Prefer exact / anchored matches. Avoid traps like male∈female and no∈another.
    """
    def _match_one(cl: str) -> str | None:
        for t in texts:
            if _norm_option(t) == cl:
                return t
        for t in texts:
            tl = _norm_option(t)
            if tl.startswith(cl + " ") or tl.startswith(cl + "(") or tl.startswith(cl + "—") or tl.startswith(cl + "-"):
                return t
        if len(cl) >= 4:
            pat = re.compile(rf"(?:^|[^a-z0-9]){re.escape(cl)}(?:[^a-z0-9]|$)")
            for t in texts:
                if pat.search(_norm_option(t)):
                    return t
        return None

    for c in candidates:
        hit = _match_one(_norm_option(c))
        if hit:
            return hit
    return None


def _pick_react(page, eid: str, candidates: list[str]) -> bool:
    if not eid:
        return False
    _close_overlays(page)
    inp = _by_id(page, eid)
    try:
        if not inp.count():
            return False
    except Exception:
        return False
    inp.scroll_into_view_if_needed()
    inp.click(timeout=5000)
    page.wait_for_timeout(200)
    # Read full menu before typing — typing can filter away matches
    # (e.g. "Company website" hides "Mercer Company Website").
    try:
        inp.fill("")
    except Exception:
        pass
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(220)
    menu = page.locator("div.select__menu").last
    texts: list[str] = []
    if menu.count():
        texts = [t.strip() for t in menu.locator("[role=option]").all_inner_texts() if t and t.strip()]

    chosen = match_select_option(candidates, texts)
    if not chosen:
        try:
            inp.fill("")
            inp.type(candidates[0], delay=15)
            page.wait_for_timeout(250)
            texts = [
                t.strip()
                for t in page.locator("div.select__menu [role=option]").all_inner_texts()
                if t and t.strip()
            ]
            chosen = match_select_option(candidates, texts)
        except Exception:
            pass
    if not chosen:
        _close_overlays(page)
        return False
    try:
        page.locator("div.select__menu").last.get_by_role("option", name=chosen, exact=True).first.click()
    except Exception:
        page.locator("div.select__menu [role=option]", has_text=chosen).first.click()
    _close_overlays(page)
    return True


def _enter_security_code(page, code: str) -> bool:
    if page.locator("#security-input-0").count() == 0:
        return False
    page.locator("#security-input-0").click()
    for i, ch in enumerate(code.strip()[:8]):
        box = page.locator(f"#security-input-{i}")
        if not box.count():
            break
        box.click()
        box.fill("")
        box.type(ch, delay=35)
        _set_val(page, f"security-input-{i}", ch)
    return True


def submit_greenhouse_basic(
    *,
    url: str,
    resume: Path,
    proof_dir: Path,
    company: str,
    first: str = "Susmitha",
    last: str = "Chowdary",
    preferred: str = "Susmitha",
    email: str = "dsusmitha55@gmail.com",
    phone: str = "9132073787",
    city: str = "Austin",
    linkedin: str = "N/A",
    sponsorship_no: bool = True,
    previously_no: bool = True,
    security_code: str | None = None,
    require_window: bool = True,
    fill_only: bool = False,
) -> GhSubmitResult:
    """Fill a common Greenhouse board form and attempt submit.

    Returns needs_me if blocked on OTP without code, captcha, or outside window.
    fill_only=True: map/fill + screenshot, never click Submit (safe outside window).
    """
    if require_window and not fill_only:
        win = check_apply_window()
        if not win.open:
            return GhSubmitResult(False, url, win.reason, "", None)
        try:
            from .job_search import assert_url_within_max_age

            ok_age, age_detail = assert_url_within_max_age(url)
            if not ok_age:
                return GhSubmitResult(False, url, f"Age gate: {age_detail}", "", None)
        except Exception as e:
            return GhSubmitResult(False, url, f"Age gate error: {e}", "", None)

    from playwright.sync_api import sync_playwright

    proof_dir.mkdir(parents=True, exist_ok=True)
    resume = resume.resolve()
    if not resume.exists():
        return GhSubmitResult(False, url, f"Missing resume: {resume}", "", proof_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_context(
            viewport={"width": 1400, "height": 2800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        ).new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(1000)
        try:
            page.get_by_text("Apply", exact=True).first.click(timeout=4000)
            page.wait_for_timeout(1000)
        except Exception:
            pass
        try:
            page.wait_for_selector("#first_name", timeout=20000)
        except Exception:
            browser.close()
            return GhSubmitResult(False, page.url, "No #first_name — form not found", "", proof_dir)

        # Upload resume first (may autofill), then overwrite with standing answers.
        if _by_id(page, "resume").count():
            page.set_input_files("#resume", str(resume))
            page.wait_for_timeout(1200)

        for eid, val in [
            ("first_name", first),
            ("last_name", last),
            ("preferred_name", preferred),
            ("email", email),
        ]:
            if _by_id(page, eid).count():
                _set_val(page, eid, val)

        if _by_id(page, "country").count():
            _pick_react(page, "country", ["United States"])
        if _by_id(page, "phone").count():
            _set_val(page, "phone", phone)
            _close_overlays(page)
        for eid in ("phone_number", "question_phone", "phone-number"):
            if _by_id(page, eid).count():
                _set_val(page, eid, phone)

        # Location (City) — Greenhouse candidate-location combobox
        if _by_id(page, "candidate-location").count():
            loc = _by_id(page, "candidate-location")
            loc.click()
            loc.fill("")
            loc.type(city, delay=25)
            page.wait_for_timeout(500)
            menu = page.locator("div.select__menu").last
            if menu.count() and menu.locator("[role=option]").count():
                # prefer Austin, TX / United States style
                opts = menu.locator("[role=option]").all_inner_texts()
                hit = next((t for t in opts if city.lower() in t.lower()), None)
                if hit:
                    menu.get_by_role("option", name=hit, exact=True).first.click()
                else:
                    menu.locator("[role=option]").first.click()
            else:
                page.keyboard.press("Enter")
            _close_overlays(page)

        # Re-assert email/name after location interactions (autofill can race)
        for eid, val in [("first_name", first), ("last_name", last), ("email", email)]:
            if _by_id(page, eid).count():
                _set_val(page, eid, val)

        # Custom questions + EEO via label map (includes numeric demographic ids)
        labels = page.evaluate(
            """() => [...document.querySelectorAll('label[id$="-label"]')].map(l => ({id: l.id.replace(/-label$/, ''), text: (l.innerText||'').trim()}))"""
        )
        for item in labels:
            low = (item.get("text") or "").lower()
            eid = item.get("id") or ""
            if not eid:
                continue
            try:
                if "preferred name" in low or "preferred first name" in low:
                    _set_val(page, eid, preferred)
                elif "linkedin" in low:
                    _set_val(page, eid, linkedin)
                elif (
                    "authorized to work" in low
                    or "legally authorized" in low
                    or "eligible to work" in low
                    or "without sponsorship" in low
                    or ("work authorization" in low and "require" not in low)
                ):
                    # Must run before sponsor branch — "authorized … without sponsorship" ≠ requiring visa
                    _pick_react(page, eid, ["Yes"])
                elif "sponsor" in low and sponsorship_no:
                    _pick_react(page, eid, ["No"])
                elif "salary" in low or "compensation expectation" in low or "pay expectation" in low:
                    from .salary import salary_from_memory

                    sal = salary_from_memory() or "120000"
                    _set_val(page, eid, str(sal))
                elif ("worked" in low and "before" in low) or "previously" in low or "interviewed" in low:
                    if previously_no:
                        _pick_react(page, eid, ["No"])
                elif "hear" in low or "learn about" in low or "how did you hear" in low or "this opportunity" in low:
                    _pick_react(
                        page,
                        eid,
                        [
                            "Mercer Company Website",
                            "MongoDB Careers Page",
                            "Company website",
                            "Company Website",
                            "Company career site",
                            "Company Website / Careers Page",
                            "Careers Page",
                            "Website",
                            "Internet search",
                            "LinkedIn",
                            "Other",
                        ],
                    )
                elif "state are you currently" in low or "state will you be based" in low or (
                    "what state" in low and "based" in low
                ):
                    _pick_react(page, eid, ["Texas", "TX"])
                elif "gender identity" in low:
                    _pick_react(page, eid, ["Woman", "Female"])
                elif low.strip().startswith("gender"):
                    _pick_react(page, eid, ["Female", "Woman"])
                elif "hispanic" in low:
                    _pick_react(page, eid, ["No"])
                    page.wait_for_timeout(400)  # race field may mount after Hispanic=No
                elif low.startswith("race") or "please identify your race" in low:
                    _pick_react(page, eid, ["Asian", "Asian (Not Hispanic or Latino)"])
                elif "veteran" in low:
                    _pick_react(page, eid, ["I am not a protected veteran"])
                elif "disability" in low:
                    _pick_react(
                        page,
                        eid,
                        ["No, I do not have a disability", "No, I don't have a disability"],
                    )
                elif "phone number" in low:
                    _set_val(page, eid, phone)
                elif "culture" in low or "careers content" in low or (
                    "alert" in low and ("receive" in low or "similar" in low)
                ):
                    _pick_react(
                        page,
                        eid,
                        [
                            "No",
                            "No thank you",
                            "No, I don't want to receive alerts",
                            "Opt out",
                            "False",
                        ],
                    )
            except Exception:
                continue

        # Second pass for race if it appeared after Hispanic
        try:
            race_lab = page.locator("label", has_text=re.compile(r"identify your race|^Race", re.I))
            if race_lab.count():
                rid = (race_lab.first.get_attribute("id") or "").replace("-label", "")
                if rid:
                    _pick_react(page, rid, ["Asian", "Asian (Not Hispanic or Latino)"])
        except Exception:
            pass

        # demographic consent checkbox (MongoDB etc.)
        consent = _by_id(page, "gdpr_demographic_data_consent_given_1")
        if consent.count():
            try:
                page.locator('label[for="gdpr_demographic_data_consent_given_1"]').click(force=True)
            except Exception:
                try:
                    consent.check(force=True)
                except Exception:
                    pass
            if not consent.is_checked():
                page.evaluate(
                    """() => {
                  const el=document.getElementById('gdpr_demographic_data_consent_given_1');
                  if(!el) return;
                  el.checked=true;
                  el.dispatchEvent(new Event('click',{bubbles:true}));
                  el.dispatchEvent(new Event('change',{bubbles:true}));
                }"""
                )
        else:
            consents = page.locator("label", has_text=re.compile(r"consent", re.I))
            for i in range(min(consents.count(), 6)):
                try:
                    consents.nth(i).click(timeout=1000)
                except Exception:
                    pass

        # Final identity overwrite (resume autofill races)
        for eid, val in [("first_name", first), ("last_name", last), ("email", email)]:
            if _by_id(page, eid).count():
                _set_val(page, eid, val)
        if _by_id(page, "country").count():
            # Re-pick country last — phone iti overlays / select races often clear it
            _pick_react(page, "country", ["United States"])
            _close_overlays(page)
        if _by_id(page, "phone").count():
            _set_val(page, "phone", phone)
            _close_overlays(page)
        # Re-assert common custom required fields that autofill may blank
        try:
            from .salary import salary_from_memory

            sal = str(salary_from_memory() or "120000")
        except Exception:
            sal = "120000"
        for item in labels:
            low = (item.get("text") or "").lower()
            eid = item.get("id") or ""
            if not eid:
                continue
            try:
                if "linkedin" in low:
                    _set_val(page, eid, linkedin)
                elif "phone number" in low:
                    _set_val(page, eid, phone)
                elif "salary" in low or "compensation expectation" in low:
                    _set_val(page, eid, sal)
                elif "state are you currently" in low or "state will you be based" in low or (
                    "what state" in low and "based" in low
                ):
                    _pick_react(page, eid, ["Texas", "TX"])
                elif "hear" in low or "this opportunity" in low:
                    _pick_react(
                        page,
                        eid,
                        [
                            "Mercer Company Website",
                            "Company website",
                            "Company Website",
                            "Website",
                            "LinkedIn",
                            "Other",
                        ],
                    )
                elif (
                    "authorized to work" in low
                    or "legally authorized" in low
                    or "without sponsorship" in low
                ):
                    _pick_react(page, eid, ["Yes"])
                elif "sponsor" in low and sponsorship_no:
                    _pick_react(page, eid, ["No"])
                elif ("worked" in low and "before" in low) or "previously" in low or "interviewed" in low:
                    if previously_no:
                        _pick_react(page, eid, ["No"])
                elif low.strip().startswith("gender") or "gender identity" in low:
                    _pick_react(page, eid, ["Female", "Woman"])
            except Exception:
                continue

        # Free-text custom questions (xAI essays, legal name, zip, current company)
        try:
            proud = (
                "Built Optum healthcare Spark/Databricks pipelines that cut reconciliation "
                "from days to hours and kept PHI quality gates green in production."
            )
            ideal = (
                "5 years Python/SQL/Spark DE; ship reliable warehouses and analytics "
                "pipelines; strong on data quality, modeling, and cross-team delivery."
            )
            for item in labels:
                low = (item.get("text") or "").lower()
                eid = item.get("id") or ""
                if not eid or not _by_id(page, eid).count():
                    continue
                tag = (page.evaluate(f"() => document.getElementById({eid!r})?.tagName || ''") or "").lower()
                if "exceptional work" in low or "most proud" in low:
                    _set_val(page, eid, proud)
                elif "ideal candidate" in low or "why are you" in low or "why do you want" in low:
                    _set_val(page, eid, ideal)
                elif "full legal name" in low and "native" not in low:
                    _set_val(page, eid, f"{first} {last}")
                elif "zip" in low or "postal" in low:
                    _set_val(page, eid, "78754")
                elif "current company" in low or "current employer" in low:
                    _set_val(page, eid, "Optum")
                elif "your location" in low and tag in {"input", "textarea"}:
                    _set_val(page, eid, "Austin, TX")
                elif low.strip() in {"website", "website url"} or low.startswith("website"):
                    pass  # optional
        except Exception:
            pass

        page.screenshot(path=str(proof_dir / "filled.png"), full_page=True)
        if fill_only:
            dom = page.evaluate(
                """() => ({
                  first: document.getElementById('first_name')?.value || null,
                  last: document.getElementById('last_name')?.value || null,
                  email: document.getElementById('email')?.value || null,
                  phone: document.getElementById('phone')?.value || null,
                  consent: document.getElementById('gdpr_demographic_data_consent_given_1')?.checked ?? null,
                  selects: [...document.querySelectorAll('.select__single-value')]
                    .map(e => (e.textContent||'').trim()).filter(Boolean),
                })"""
            )
            ok_email = (dom.get("email") or "") == email
            ok_name = (dom.get("first") or "") == first and (dom.get("last") or "") == last
            (proof_dir / "FILL_ONLY.txt").write_text(
                f"{company} fill-only dry check\n"
                f"URL: {page.url}\n"
                f"Email: {email}\n"
                f"DOM email: {dom.get('email')}\n"
                f"DOM name: {dom.get('first')} {dom.get('last')}\n"
                f"DOM phone: {dom.get('phone')}\n"
                f"DOM consent: {dom.get('consent')}\n"
                f"DOM selects: {dom.get('selects')}\n"
                f"identity_ok: {ok_email and ok_name}\n"
                f"No Submit clicked.\n"
            )
            if not (ok_email and ok_name):
                browser.close()
                return GhSubmitResult(
                    False,
                    page.url,
                    f"Fill identity mismatch DOM={dom}",
                    "fill_only",
                    proof_dir,
                )
            browser.close()
            return GhSubmitResult(True, page.url, None, "fill_only", proof_dir)

        # Detect visible reCAPTCHA before submit (cannot solve — needs-me)
        try:
            has_captcha = bool(
                page.evaluate(
                    """() => {
              const ifr=[...document.querySelectorAll('iframe')].some(f=>(f.src||'').includes('recaptcha'));
              const box=!!document.querySelector('.g-recaptcha, [data-sitekey]');
              return ifr || box;
            }"""
                )
            )
        except Exception:
            has_captcha = False
        if has_captcha and page.locator("textarea[name='g-recaptcha-response']").count():
            # Only block if captcha widget is actually rendered (not just empty textarea stub)
            try:
                vis = page.locator("iframe[src*='recaptcha']").first.is_visible(timeout=1500)
            except Exception:
                vis = False
            if vis:
                page.screenshot(path=str(proof_dir / "needs_captcha.png"), full_page=True)
                (proof_dir / "NEEDS_ME.txt").write_text(
                    f"{company}: reCAPTCHA on Greenhouse form — cannot complete autonomously.\n"
                    f"URL: {page.url}\nEmail: {email}\n"
                )
                browser.close()
                return GhSubmitResult(
                    False,
                    page.url,
                    "Greenhouse reCAPTCHA — needs you",
                    "captcha",
                    proof_dir,
                )

        btn = page.locator('button:has-text("Submit application"), button:has-text("Submit Application")')
        if btn.count():
            btn.first.click()
            page.wait_for_timeout(5000)

        body = page.inner_text("body")
        low = body.lower()
        if "verification code" in low or "security code" in low or page.locator("#security-input-0").count():
            if not security_code:
                page.screenshot(path=str(proof_dir / "needs_security_code.png"), full_page=True)
                (proof_dir / "NEEDS_ME_STATUS.txt").write_text(
                    f"{company}: Greenhouse email security code required.\n"
                    f"Email: {email}\nPaste 8-char code in chat (Gmail declined).\nURL: {page.url}\n"
                )
                browser.close()
                return GhSubmitResult(
                    False,
                    page.url,
                    "Greenhouse email security code required — paste 8-char code",
                    body[-500:],
                    proof_dir,
                )
            _enter_security_code(page, security_code)
            if btn.count():
                try:
                    btn.first.click(force=True, timeout=8000)
                except Exception:
                    page.evaluate(
                        """() => {
                  const b=[...document.querySelectorAll('button')].find(x=>/submit application/i.test(x.innerText||''));
                  if(b){b.disabled=false;b.click();}
                }"""
                    )
            page.wait_for_timeout(8000)
            body = page.inner_text("body")
            low = body.lower()
            if "incorrect security code" in low:
                browser.close()
                return GhSubmitResult(
                    False, page.url, "Incorrect security code", body[-500:], proof_dir
                )

        ok = ("/confirmation" in page.url) or any(
            x in low
            for x in [
                "thank you for applying",
                "application has been submitted",
                "successfully submitted",
                "we have received your application",
                "thanks for applying",
            ]
        )
        page.screenshot(path=str(proof_dir / ("confirmation.png" if ok else "after_submit.png")), full_page=True)
        (proof_dir / ("confirmation.txt" if ok else "after_submit.txt")).write_text(
            f"{company}\nURL: {page.url}\nEmail: {email}\n\n{body[:3000]}\n"
        )
        if ok:
            try:
                shutil.copy(proof_dir / "confirmation.png", f"/opt/cursor/artifacts/{company.lower()}_confirmation.png")
            except Exception:
                pass
        browser.close()
        return GhSubmitResult(ok, page.url, None if ok else "Submit not confirmed", body[-800:], proof_dir)
