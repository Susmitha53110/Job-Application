"""Minimal Playwright submit helper for company iCIMS apply forms."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .window import check_apply_window


@dataclass
class IcimsSubmitResult:
    success: bool
    url: str
    needs_me: str | None
    confirmation_text: str
    proof_dir: Path | None


def submit_icims_basic(
    *,
    url: str,
    resume: Path,
    proof_dir: Path,
    company: str,
    first: str = "Susmitha",
    last: str = "Chowdary",
    email: str = "dsusmitha55@gmail.com",
    phone: str = "9132073787",
    linkedin: str = "https://www.linkedin.com/in/susmitha-dodla-a05ab92b8",
    require_window: bool = True,
) -> IcimsSubmitResult:
    if require_window:
        win = check_apply_window()
        if not win.open:
            return IcimsSubmitResult(False, url, win.reason, "", None)

    from playwright.sync_api import sync_playwright

    proof_dir.mkdir(parents=True, exist_ok=True)
    resume = resume.resolve()
    if not resume.exists():
        return IcimsSubmitResult(False, url, f"Missing resume: {resume}", "", proof_dir)

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
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(2000)

        # Enter iframe if present
        frame = page
        for f in page.frames:
            if "icims" in (f.url or "") and f != page.main_frame:
                frame = f
                break

        # Click Apply
        for name in (
            re.compile(r"^Apply( for this job)?$", re.I),
            re.compile(r"Apply Now", re.I),
            re.compile(r"Start Application", re.I),
        ):
            try:
                btn = frame.get_by_role("link", name=name)
                if btn.count():
                    btn.first.click(timeout=4000)
                    page.wait_for_timeout(2000)
                    break
                btn = frame.get_by_role("button", name=name)
                if btn.count():
                    btn.first.click(timeout=4000)
                    page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        # Refresh frame after navigation
        frame = page
        for f in page.frames:
            if "icims" in (f.url or "") and ("login" in f.url or "job" in f.url or "form" in f.url):
                frame = f

        body = ""
        try:
            body = frame.inner_text("body")
        except Exception:
            try:
                body = page.inner_text("body")
            except Exception:
                body = ""
        low = body.lower()
        if any(x in low for x in ("recaptcha", "hcaptcha", "verify you are human", "cf-turnstile")):
            page.screenshot(path=str(proof_dir / "needs_captcha.png"), full_page=True)
            browser.close()
            return IcimsSubmitResult(False, page.url, "iCIMS CAPTCHA — needs you", body[-400:], proof_dir)
        if "sign in" in low and "password" in low and "apply" not in low[:500]:
            page.screenshot(path=str(proof_dir / "needs_login.png"), full_page=True)
            browser.close()
            return IcimsSubmitResult(
                False, page.url, "iCIMS login wall — needs you", body[-400:], proof_dir
            )

        def fill_by_label(lab: str, value: str, which: int = 0) -> bool:
            try:
                loc = frame.get_by_label(re.compile(lab, re.I))
                if loc.count():
                    loc.nth(which).fill(value)
                    return True
            except Exception:
                pass
            try:
                lab_el = frame.get_by_text(re.compile(lab, re.I)).first
                inp = lab_el.locator("xpath=following::input[not(@type='hidden')][1]")
                if inp.count():
                    inp.first.fill(value)
                    return True
            except Exception:
                return False
            return False

        fill_by_label(r"First Name|First name", first)
        fill_by_label(r"Last Name|Last name", last)
        fill_by_label(r"^Email$|Email Address", email)
        fill_by_label(r"Phone|Mobile", phone)
        fill_by_label(r"LinkedIn", linkedin)
        fill_by_label(r"City", "Austin")
        fill_by_label(r"Zip|Postal", "78754")

        # Resume upload
        try:
            files = frame.locator("input[type=file]")
            if files.count():
                files.first.set_input_files(str(resume))
                page.wait_for_timeout(2000)
        except Exception:
            pass

        # Common selects
        for lab, val in (
            (r"authorized to work", "Yes"),
            (r"require sponsorship|visa sponsorship|need sponsorship", "No"),
            (r"Gender", "Female"),
            (r"Hispanic|Latino", "No"),
            (r"Veteran", "I am not a protected veteran"),
            (r"Disability", "No"),
        ):
            try:
                frame.get_by_label(re.compile(lab, re.I)).select_option(label=re.compile(val, re.I))
            except Exception:
                try:
                    el = frame.get_by_text(re.compile(lab, re.I)).first
                    el.click()
                    page.wait_for_timeout(300)
                    frame.get_by_role("option", name=re.compile(val, re.I)).first.click()
                except Exception:
                    pass

        fill_by_label(r"salary|compensation|pay expectation", "120000")
        fill_by_label(r"How did you (hear|learn)", "Company website")

        page.screenshot(path=str(proof_dir / "filled.png"), full_page=True)
        try:
            (proof_dir / "filled_url.txt").write_text(page.url, encoding="utf-8")
        except Exception:
            pass

        # Submit
        submitted = False
        for name in (
            re.compile(r"^Submit$", re.I),
            re.compile(r"Submit Application", re.I),
            re.compile(r"^Next$", re.I),
            re.compile(r"Continue", re.I),
        ):
            try:
                btn = frame.get_by_role("button", name=name)
                if btn.count():
                    btn.first.click(timeout=5000)
                    submitted = True
                    page.wait_for_timeout(3500)
                    break
            except Exception:
                continue

        page.wait_for_timeout(2000)
        try:
            body = frame.inner_text("body")
        except Exception:
            body = page.inner_text("body")
        (proof_dir / "after_submit.txt").write_text(body[:4000], encoding="utf-8")
        page.screenshot(path=str(proof_dir / "after_submit.png"), full_page=True)

        ok = bool(
            re.search(
                r"thank you|application (has been )?received|successfully submitted|"
                r"under review|we have received your application",
                body,
                re.I,
            )
        )
        if ok:
            (proof_dir / "confirmation.txt").write_text(body[:3000], encoding="utf-8")
            page.screenshot(path=str(proof_dir / "confirmation.png"), full_page=True)
            try:
                shutil.copy(
                    proof_dir / "confirmation.png",
                    f"/opt/cursor/artifacts/{company.lower().replace(' ', '_')}_confirmation.png",
                )
            except Exception:
                pass
            browser.close()
            return IcimsSubmitResult(True, page.url, None, body[:500], proof_dir)

        if re.search(r"captcha|cloudflare|verify you are human", body, re.I):
            browser.close()
            return IcimsSubmitResult(False, page.url, "iCIMS CAPTCHA — needs you", body[:300], proof_dir)

        browser.close()
        detail = "Submit not confirmed" if submitted else "Apply/Submit controls not found"
        return IcimsSubmitResult(False, page.url, detail, body[:300], proof_dir)
