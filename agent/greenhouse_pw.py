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
    page.wait_for_timeout(180)
    try:
        inp.fill("")
        inp.type(candidates[0], delay=15)
    except Exception:
        pass
    page.wait_for_timeout(280)
    menu = page.locator("div.select__menu").last
    texts = []
    if menu.count():
        texts = [t for t in menu.locator("[role=option]").all_inner_texts() if "+" not in t]
    chosen = None
    for c in candidates:
        for t in texts:
            if t.strip().lower() == c.lower() or c.lower() in t.strip().lower():
                chosen = t.strip()
                break
        if chosen:
            break
    if not chosen:
        opts = page.locator("div.select__menu [role=option]")
        for i in range(min(opts.count(), 40)):
            t = opts.nth(i).inner_text().strip()
            if any(c.lower() in t.lower() for c in candidates):
                opts.nth(i).click()
                _close_overlays(page)
                return True
        _close_overlays(page)
        return False
    menu.get_by_role("option", name=chosen, exact=True).first.click()
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

        if _by_id(page, "resume").count():
            page.set_input_files("#resume", str(resume))

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
                elif "sponsor" in low and sponsorship_no:
                    _pick_react(page, eid, ["No"])
                elif ("worked" in low and "before" in low) or "previously" in low:
                    if previously_no:
                        _pick_react(page, eid, ["No"])
                elif "hear" in low or "learn about" in low:
                    _pick_react(
                        page,
                        eid,
                        [
                            "MongoDB Careers Page",
                            "Company website",
                            "Company Website",
                            "Company career site",
                            "LinkedIn",
                            "Other",
                        ],
                    )
                elif "gender identity" in low:
                    _pick_react(page, eid, ["Woman", "Female"])
                elif low.strip().startswith("gender"):
                    _pick_react(page, eid, ["Female", "Woman"])
                elif "hispanic" in low:
                    _pick_react(page, eid, ["No"])
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
            except Exception:
                continue

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

        page.screenshot(path=str(proof_dir / "filled.png"), full_page=True)
        if fill_only:
            (proof_dir / "FILL_ONLY.txt").write_text(
                f"{company} fill-only dry check\nURL: {page.url}\nEmail: {email}\nNo Submit clicked.\n"
            )
            browser.close()
            return GhSubmitResult(True, page.url, None, "fill_only", proof_dir)

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
