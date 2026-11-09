"""Generate the static legal pages from source/<lang>/<doc>.md.

Usage: python tools/build.py   (requires: pip install markdown)
"""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["en", "ru"]
DOCS = ["privacy-policy", "terms-of-use", "support"]
DOC_NAMES = {
	"en": {"privacy-policy": "Privacy Policy", "terms-of-use": "Terms of Use", "support": "Support"},
	"ru": {"privacy-policy": "Политика конфиденциальности", "terms-of-use": "Условия использования", "support": "Поддержка"},
}
SITE_NAME = "Hedgehog"

PAGE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{site} | {title}</title>
<meta name="description" content="{site} | {title}">
<link rel="preconnect" href="https://fonts.gstatic.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&amp;subset=latin,cyrillic&amp;display=swap">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<nav class="topbar">
<span class="docs">{doc_links}</span>
<span class="langs">{lang_links}</span>
</nav>
<main class="doc">
{body}
</main>
</body>
</html>
"""


def preprocess(text: str) -> str:
	text = text.lstrip("﻿")
	text = text.replace("https\\://", "https://")
	# A lone backslash is an empty line: treat it as a paragraph break.
	text = re.sub(r"^\\[ \t]*$", "", text, flags=re.M)
	# The title is written as ***Title*** on the first line.
	text = re.sub(r"\A\s*\*\*\*(.+?)\*\*\*[ \t]*\\?[ \t]*$", r"# \1", text, flags=re.M)
	# A line that is entirely bold is a section heading: "1." / "Section 1" -> h2, sub-sections -> h3.
	def heading(m):
		title = m.group(1).strip()
		level = "##" if re.match(r"(\d+\.\s|Section\s|Раздел\s)", title) else "###"
		return f"\n{level} {title}\n"
	text = re.sub(r"^\*\*([^*\n]+)\*\*[ \t]*\\?[ \t]*$", heading, text, flags=re.M)
	# A trailing backslash is a hard line break.
	text = re.sub(r"\\[ \t]*$", "<br>", text, flags=re.M)
	return text


def title_of(text: str) -> str:
	first = next(line for line in text.splitlines() if line.strip())
	return first.strip("#* \t")


def render(lang: str, doc: str) -> str:
	src = preprocess((ROOT / "source" / lang / f"{doc}.md").read_text(encoding="utf-8"))
	body = markdown.markdown(src, extensions=["tables", "sane_lists"], output_format="html")
	body = re.sub(r"(<br>\s*)+</p>", "</p>", body)
	body = re.sub(r"(?<![\"'>:/\w])([\w.+-]+@[\w-]+\.[a-z]{2,})(?![^<]*</a>)", r'<a href="mailto:\1">\1</a>', body)
	body = re.sub(r"(?<![\"'>])(https://[^\s<]+)(?![^<]*</a>)", r'<a href="\1">\1</a>', body)
	doc_links = " · ".join(
		f'<a href="{d}.html"{" class=\"active\"" if d == doc else ""}>{html.escape(DOC_NAMES[lang][d])}</a>'
		for d in DOCS
	)
	lang_links = " | ".join(
		f'<a href="../{l}/{doc}.html" hreflang="{l}"{" class=\"active\"" if l == lang else ""}>{l.upper()}</a>'
		for l in LANGS
	)
	return PAGE.format(
		lang=lang, site=SITE_NAME, title=html.escape(title_of(src)),
		doc_links=doc_links, lang_links=lang_links, body=body,
	)


def main():
	for lang in LANGS:
		for doc in DOCS:
			out = ROOT / lang / f"{doc}.html"
			out.parent.mkdir(exist_ok=True)
			out.write_text(render(lang, doc), encoding="utf-8", newline="\n")
			print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
	main()
