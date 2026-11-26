"""HTTP datePosted scrape unlocks iCIMS/Velosio-style career pages."""

from __future__ import annotations

import urllib.request

from agent import job_search


class _Resp:
    def __init__(self, body: bytes):
        self._body = body

    def read(self, _n: int = -1) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_http_date_posted_scraped_before_playwright(monkeypatch):
    html = b'''
    <script type="application/ld+json">
    {"@type":"JobPosting","datePosted":"2026-11-11T17:46:00+0000","title":"Data Engineer"}
    </script>
    '''

    def fake_urlopen(req, timeout=20):  # noqa: ARG001
        return _Resp(html)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    posted = job_search.resolve_posted_at("https://careers.example.com/jobs/3162")
    assert posted == "2026-11-11T17:46:00+0000"
