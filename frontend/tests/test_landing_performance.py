"""Run after npm run build: keep the landing page's font download under 300 KB."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


class Stylesheets(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.paths = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.paths.append(attrs["href"])


class LandingPerformanceTests(unittest.TestCase):
    def test_landing_fonts_fit_download_budget(self):
        output = Path(__file__).resolve().parents[1] / "out"
        styles = Stylesheets((output / "index.html").read_text())
        fonts = set()
        for path in styles.paths:
            stylesheet = output / path.lstrip("/")
            for url in re.findall(r"url\([\"']?([^\)\"']+\.woff2)[\"']?\)", stylesheet.read_text()):
                fonts.add(output / url.lstrip("/") if url.startswith("/") else (stylesheet.parent / url).resolve())
        self.assertEqual(len(fonts), 4, "Expected three body weights and the display font")
        self.assertLess(sum(font.stat().st_size for font in fonts), 300_000,
                        "Keep landing fonts subsetted; the original files cost 1.2 MB")


if __name__ == "__main__":
    unittest.main()
