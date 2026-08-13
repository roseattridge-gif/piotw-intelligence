"""Deterministically parse the retained pilot documents without LLM calls."""
from pathlib import Path
from html.parser import HTMLParser
from pypdf import PdfReader

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "footer"}: self.skip += 1
    def handle_endtag(self, tag):
        if tag in {"script", "style", "nav", "footer"} and self.skip: self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

ROOT = Path(__file__).resolve().parents[1]
for source in sorted((ROOT / "data/raw").glob("*/*")):
    target = ROOT / "data/parsed" / f"{source.parent.name}--{source.stem}.txt"
    if source.suffix.lower() == ".pdf":
        pages = []
        for number, page in enumerate(PdfReader(source).pages, 1):
            pages.append(f"\n--- PAGE {number} ---\n{page.extract_text() or ''}")
        text = "".join(pages)
    else:
        parser = TextParser(); parser.feed(source.read_text(errors="replace"))
        text = "\n".join(parser.parts)
    target.write_text(text)
    print(f"{source.relative_to(ROOT)} -> {target.relative_to(ROOT)} ({len(text):,} chars)")
