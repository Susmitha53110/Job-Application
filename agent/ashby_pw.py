"""Playwright helpers for Ashby application forms (fill + optional submit)."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .window import check_apply_window


@dataclass
class AshbySubmitResult:
    success: bool
    url: str
    needs_me: str | None
    confirmation_text: str
    proof_dir: Path | None


def submit_ashby_basic(
    *,
    url: str,
    resume: Path,
    proof_dir: Path,
    company: str,
    name: str = "Susmitha Chowdary",
    email: str = "dsusmitha55@gmail.com",
    phone: str | None = "9132073787",
    linkedin: str = "N/A",
    why_fit: str | None = None,
    spell_twelve: bool = True,
    security_code: str | None = None,
    require_window: bool = True,
    fill_only: bool = False,
) -> AshbySubmitResult:
    if require_window and not fill_only:
        win = check_apply_window()
        if not win.open:
            return AshbySubmitResult(False, url, win.reason, "", None)

    from playwright.sync_api import sync_playwright

    proof_dir.mkdir(parents=True, exist_ok=True)
    resume = resume.resolve()
    if not resume.exists():
        return AshbySubmitResult(False, url, f"Missing resume: {resume}", "", proof_dir)

    why_fit = why_fit or (
        "I build reliable Python/SQL/Spark data platforms and want to apply that "
        "experience to product analytics and data systems at scale."
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_context(
            viewport={"width": 1280, "height": 2400},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        ).new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(1200)
        for txt in ("Apply", "Apply for this Job", "Submit Application"):
            loc = page.get_by_role("button", name=txt)
            if loc.count():
                try:
                    loc.first.click(timeout=3000)
                    page.wait_for_timeout(1000)
                    break
                except Exception:
                    pass

        def fill_label(pattern: str, value: str) -> None:
            try:
                page.get_by_label(re.compile(pattern, re.I)).first.fill(value, timeout=3000)
            except Exception:
                pass

        def click_yes_no(question_snippet: str, answer: str) -> None:
            """Ashby often uses Yes/No buttons under a question heading."""
            try:
                q = page.get_by_text(re.compile(question_snippet, re.I)).first
                root = q.locator("xpath=ancestor::*[self::div or self::fieldset][1]")
                root.get_by_role("button", name=answer).first.click(timeout=3000)
            except Exception:
                try:
                    # fallback: nearest buttons after the text
                    page.get_by_text(re.compile(question_snippet, re.I)).first.locator(
                        "xpath=following::button[normalize-space()='%s'][1]" % answer
                    ).click(timeout=3000)
                except Exception:
                    pass

        # Resume first (autofill), then overwrite standing answers
        try:
            page.set_input_files("input[type=file]", str(resume))
            page.wait_for_timeout(2000)
        except Exception:
            pass

        fill_label(r"^Name$", name)
        fill_label(r"^Email$", email)
        if phone:
            fill_label(r"Phone", phone)
        fill_label(r"LinkedIn", linkedin)
        fill_label(r"Why does|good fit|interests you about this", why_fit)
        fill_label(r"How did you hear", "Company website")
        fill_label(r"favourite game|favorite game", "Portal — elegant puzzle design and clean systems thinking.")
        fill_label(r"Something we should know", "Open to a 6-month contract; Austin TX; F1-OPT authorized, no sponsorship needed.")
        fill_label(r"previously employed or contracted", "No")
        fill_label(r"non-compete|non-solicitation|confidentiality agreement", "No")
        click_yes_no(r"eligible to work in the US|authorized to work at the location", "Yes")
        click_yes_no(r"require (visa )?sponsorship", "No")
        click_yes_no(r"18 years of age", "Yes")
        if spell_twelve:
            fill_label(r"Spell the number", "twelve")
        # Terms checkbox
        try:
            page.get_by_text(re.compile(r"I have read and agree", re.I)).first.click(timeout=2000)
        except Exception:
            try:
                page.locator('input[type=checkbox]').last.check(force=True, timeout=2000)
            except Exception:
                pass
        # EEO radios
        try:
            page.get_by_text("Female", exact=True).first.click(timeout=2000)
        except Exception:
            pass
        try:
            page.get_by_text("Asian (Not Hispanic or Latino)", exact=True).first.click(timeout=2000)
        except Exception:
            try:
                page.get_by_text("Asian", exact=True).first.click(timeout=2000)
            except Exception:
                pass
        try:
            page.get_by_text("I am not a protected veteran", exact=True).first.click(timeout=2000)
        except Exception:
            pass
        # Re-assert identity after autofill races
        fill_label(r"^Name$", name)
        fill_label(r"^Email$", email)
        try:
            page.locator("#_systemfield_email, input[type=email]").first.fill(email, timeout=3000)
        except Exception:
            pass
        try:
            page.locator("#_systemfield_name").first.fill(name, timeout=3000)
        except Exception:
            pass

        page.screenshot(path=str(proof_dir / "filled.png"), full_page=True)
        if fill_only:
            dom = page.evaluate(
                """() => ({
                  name: document.getElementById('_systemfield_name')?.value
                    || document.querySelector('input[name="_systemfield_name"]')?.value || null,
                  email: document.getElementById('_systemfield_email')?.value
                    || document.querySelector('input[type=email]')?.value || null,
                })"""
            )
            ok = (dom.get("email") or "") == email and (dom.get("name") or "") == name
            (proof_dir / "FILL_ONLY.txt").write_text(
                f"{company} Ashby fill-only\n"
                f"URL: {page.url}\n"
                f"Email: {email}\n"
                f"DOM name: {dom.get('name')}\n"
                f"DOM email: {dom.get('email')}\n"
                f"identity_ok: {ok}\n"
                f"No Submit.\n"
            )
            if not ok:
                browser.close()
                return AshbySubmitResult(
                    False, page.url, f"Fill identity mismatch DOM={dom}", "fill_only", proof_dir
                )
            browser.close()
            return AshbySubmitResult(True, page.url, None, "fill_only", proof_dir)

        # CAPTCHA gate (cannot solve)
        try:
            captcha_vis = page.locator("iframe[src*='recaptcha'], iframe[title*='recaptcha']").first.is_visible(
                timeout=1500
            )
        except Exception:
            captcha_vis = False
        if captcha_vis or "select all images" in (page.inner_text("body").lower()):
            page.screenshot(path=str(proof_dir / "needs_captcha.png"), full_page=True)
            (proof_dir / "NEEDS_ME.txt").write_text(
                f"{company}: Ashby reCAPTCHA — cannot complete autonomously.\nURL: {page.url}\nEmail: {email}\n",
                encoding="utf-8",
            )
            browser.close()
            return AshbySubmitResult(
                False, page.url, "Ashby reCAPTCHA — needs you", "captcha", proof_dir
            )

        # submit
        btn = page.get_by_role("button", name=re.compile(r"Submit", re.I))
        if btn.count():
            btn.first.click()
            page.wait_for_timeout(6000)
        body = page.inner_text("body")
        low = body.lower()
        if "verification code" in low or "security code" in low:
            if not security_code:
                page.screenshot(path=str(proof_dir / "needs_security_code.png"), full_page=True)
                browser.close()
                return AshbySubmitResult(
                    False,
                    page.url,
                    "Email/security verification required — paste code (Gmail declined)",
                    body[-500:],
                    proof_dir,
                )
        ok = any(
            x in low
            for x in [
                "thank you",
                "application has been submitted",
                "successfully submitted",
                "we have received",
                "thanks for applying",
            ]
        )
        page.screenshot(
            path=str(proof_dir / ("confirmation.png" if ok else "after_submit.png")),
            full_page=True,
        )
        (proof_dir / ("confirmation.txt" if ok else "after_submit.txt")).write_text(
            f"{company}\nURL: {page.url}\nEmail: {email}\n\n{body[:3000]}\n"
        )
        if ok:
            try:
                shutil.copy(
                    proof_dir / "confirmation.png",
                    f"/opt/cursor/artifacts/{company.lower()}_confirmation.png",
                )
            except Exception:
                pass
        browser.close()
        return AshbySubmitResult(ok, page.url, None if ok else "Submit not confirmed", body[-800:], proof_dir)
