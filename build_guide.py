#!/usr/bin/env python3

"""
build_guide.py --- regenerates the ShowPy study guide PDF from its sources

Run from the repository root:

    uv run python build_guide.py

Steps: run every tutorial example and capture its output, draw the figures, run every exercise
check against the answers (must pass) and the empty stubs (must fail), execute every `>>>`
snippet of every chapter and compare it with the text, then render Markdown to HTML and print
it to PDF. The PDF always shows the outputs of this run, so it cannot drift from the code.
`--update-snippets` rewrites the stored snippet outputs in the chapters instead of failing.

Contains:
    Block: holds one executed snippet: statements, outputs and pictures
    run_examples(): runs each tutorial example and stores its output next to it
    make_figures(): runs the figure script
    check_exercises(): runs every exercise check against answers and stubs
    execute_chapter(): runs every pycon block of a chapter and returns the results
    render_chapter(): turns one chapter's Markdown into numbered HTML
    build_pdf(): assembles the title page, contents and chapters and prints the PDF
    main(): runs the whole build
"""

import argparse
import contextlib
import html
import io
import os
import re
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

GUIDE = Path(__file__).resolve().parent
REPO = GUIDE
CHAPTERS = GUIDE / "chapters"
EXAMPLES = GUIDE / "examples"
EXERCISES = GUIDE / "exercises"
OUTPUTS = EXAMPLES / "output"
FIGURE_SCRIPT = GUIDE / "figures" / "make_figures.py"
CHECK_RUNNER = EXERCISES / "run_all_checks.py"
PDF_PATH = GUIDE / "showpy-guide.pdf"
TITLE = "ShowPy"
SUBTITLE = "How the Python choreography library works, from first principles"
EDITION = "2026-11-18"
SUBPROCESS_TIMEOUT_S = 900
PYCON_BLOCK = re.compile(r"^```pycon\n(.*?)^```\n", re.DOTALL | re.MULTILINE)
INCLUDE = re.compile(r"^\{\{(code|output|check): ([\w./-]+)\}\}$", re.MULTILINE)
PLACEHOLDER = re.compile(r"<p>GUIDEBLOCK(\d+)</p>")
HEADING = re.compile(r"<h([123])>(.*?)</h\1>", re.DOTALL)
FIGURE = re.compile(r'<p><img alt="(.*?)" src="(.*?)" ?/?></p>', re.DOTALL)
TAG = re.compile(r"<[^>]+>")
QUIET_BOX = '<div class="output quiet"><div class="outlabel">No printed output</div></div>'
UNNUMBERED_PREFIXES = ("00-", "99-")
APPENDIX_PREFIX = "99-"


@dataclass
class Block:
    """Holds one executed snippet.

    Attributes:
        steps: (statement lines, output lines, raised) per statement, in order.
        pictures: (path, caption) of pictures the snippet drew.
    """

    steps: list[tuple[list[str], list[str], bool]] = field(default_factory=list)
    pictures: list[tuple[Path, str]] = field(default_factory=list)

    def text(self) -> str:
        """Returns the block as doctest-style text, as stored in the chapter."""
        lines: list[str] = []
        for statement, output, _ in self.steps:
            lines += [(">>> " if i == 0 else "... ") + s for i, s in enumerate(statement)]
            lines += output
        return "\n".join(line.rstrip() for line in lines) + "\n"


@dataclass
class TocEntry:
    """Holds one contents line.

    Attributes:
        level: 1 for a chapter, 2 for a section.
        number: Printed number such as `4` or `4.2`; empty for front and back matter.
        title: Heading text without tags.
        anchor: ID of the heading element.
    """

    level: int
    number: str
    title: str
    anchor: str


@dataclass
class Numbering:
    """Tracks chapter, section and figure numbers across the whole guide.

    Attributes:
        chapter: Current chapter number.
        counters: Section and subsection counters inside the chapter.
        figure: Figure counter inside the chapter.
        label: Prefix of figure numbers: the chapter number, or `A` in the appendix.
        toc: Contents entries collected so far.
    """

    chapter: int = 0
    counters: list[int] = field(default_factory=lambda: [0, 0])
    figure: int = 0
    label: str = ""
    toc: list[TocEntry] = field(default_factory=list)


def _run(args: list[str], what: str) -> str:
    done = subprocess.run(
        args, cwd=REPO, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_S, check=False
    )
    if done.returncode != 0:
        sys.exit(f"E: {what} failed\n{done.stdout}\n{done.stderr}")
    return done.stdout


def run_examples() -> None:
    """Runs each tutorial example in order and writes its stdout to examples/output."""
    OUTPUTS.mkdir(exist_ok=True)
    for script in sorted(EXAMPLES.glob("t*.py")):
        output = _run([sys.executable, str(script)], f"example {script.name}")
        (OUTPUTS / f"{script.stem}.txt").write_text(output)
        print(f"Ran {script.name}")


def make_figures() -> None:
    """Runs the figure script, which writes PNG files into figures/."""
    _run([sys.executable, str(FIGURE_SCRIPT)], "figure script")
    print("Drew figures")


def check_exercises() -> None:
    """Runs every exercise check: answers must pass and untouched stubs must fail."""
    print(_run([sys.executable, str(CHECK_RUNNER)], "exercise checks").strip().splitlines()[-1])


def _statements(body: str) -> list[list[str]]:
    statements: list[list[str]] = []
    for line in body.splitlines():
        if line.startswith(">>> ") or line == ">>>":
            statements.append([line[4:]])
        elif line.startswith("... ") or line == "...":
            statements[-1].append(line[4:])
    return statements


def _echo(text: str) -> list[str]:
    return [line.rstrip() or "<BLANKLINE>" for line in text.rstrip("\n").splitlines()]


def _execute(body: str, namespace: dict[str, object], prefix: str) -> Block:
    from guide_draw import sketch

    sketch.start(prefix)
    block = Block()
    for statement in _statements(body):
        printed = io.StringIO()
        raised = False
        try:
            code = compile("\n".join(statement) + "\n", "<guide>", "single")
            with contextlib.redirect_stdout(printed):
                exec(code, namespace)
            output = _echo(printed.getvalue()) if printed.getvalue() else []
        except Exception as error:
            last = traceback.format_exception_only(type(error), error)[-1].rstrip("\n")
            output = ["Traceback (most recent call last):", "  ...", last]
            raised = True
        block.steps.append((statement, output, raised))
    block.pictures = sketch.collect()
    return block


def execute_chapter(path: Path, update: bool) -> list[Block]:
    """Runs every pycon block of a chapter in one namespace, in order.

    Stored outputs must equal the fresh ones; with `update` the chapter is rewritten instead.
    """
    namespace: dict[str, object] = {"__name__": "__guide__"}
    text = path.read_text()
    blocks: list[Block] = []
    stale: list[int] = []
    cwd = Path.cwd()
    os.chdir(REPO)
    try:
        for index, match in enumerate(PYCON_BLOCK.finditer(text)):
            block = _execute(match.group(1), namespace, f"{path.stem}-{index + 1}")
            if block.text() != match.group(1):
                stale.append(index + 1)
            blocks.append(block)
    finally:
        os.chdir(cwd)
    if stale and update:
        fresh = iter(blocks)
        path.write_text(PYCON_BLOCK.sub(lambda m: f"```pycon\n{next(fresh).text()}```\n", text))
        print(f"Updated {path.name}: snippets {stale}")
    elif stale:
        sys.exit(f"E: {path.name} snippets {stale} differ from a fresh run; use --update-snippets")
    print(f"Ran {path.name}: {len(blocks)} snippets")
    return blocks


def _highlight(source: str, lexer: str) -> str:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name

    return highlight(source, get_lexer_by_name(lexer), HtmlFormatter(cssclass="code"))


def _output_box(lines: list[str], raised: bool) -> str:
    text = "\n".join("" if line == "<BLANKLINE>" else line for line in lines)
    kind, label = ("output error", "What happened (exception)") if raised else ("output", "Output")
    return (
        f'<div class="{kind}"><div class="outlabel">{label}</div>'
        f"<pre>{html.escape(text)}</pre></div>"
    )


def _block_html(block: Block) -> str:
    parts: list[str] = []
    code: list[str] = []
    for statement, output, raised in block.steps:
        code += statement
        if output:
            parts.append(_highlight("\n".join(code), "python"))
            parts.append(_output_box(output, raised))
            code = []
    if code:
        parts.append(_highlight("\n".join(code), "python"))
        parts.append(QUIET_BOX)
    return f'<div class="snippet">{"".join(parts)}</div>'


def _check_output(name: str) -> str:
    script = EXERCISES / f"check_{name}.py"
    return _run([sys.executable, str(script), "--answers"], f"check {name}").rstrip("\n")


def _include(match: re.Match[str], boxes: list[str]) -> str:
    kind, name = match.groups()
    if kind == "code":
        source = (GUIDE / name).read_text().rstrip("\n")
        return f"```python\n{source}\n```"
    output = (
        (OUTPUTS / f"{name}.txt").read_text().rstrip("\n")
        if kind == "output"
        else _check_output(name)
    )
    boxes.append(_output_box(output.splitlines(), raised=False))
    return f"GUIDEBLOCK{len(boxes) - 1}"


def _plain_heading(numbering: Numbering, match: re.Match[str]) -> str:
    level, inner = int(match.group(1)), match.group(2)
    anchor = f"u-{len(numbering.toc)}-{level}"
    if level == 1:
        numbering.toc.append(TocEntry(1, "", TAG.sub("", inner), anchor))
        return f'<h1 id="{anchor}"><span class="chaptitle">{inner}</span></h1>'
    if level == 2:
        numbering.toc.append(TocEntry(2, "", TAG.sub("", inner), anchor))
    return f'<h{level} id="{anchor}">{inner}</h{level}>'


def _number_heading(numbering: Numbering, match: re.Match[str]) -> str:
    level, inner = int(match.group(1)), match.group(2)
    if level == 1:
        numbering.chapter += 1
        numbering.counters = [0, 0]
        numbering.figure = 0
        numbering.label = str(numbering.chapter)
        number = str(numbering.chapter)
    else:
        numbering.counters[level - 2] += 1
        if level == 2:
            numbering.counters[1] = 0
        number = ".".join(map(str, [numbering.chapter, *numbering.counters[: level - 1]]))
    anchor = f"s-{number.replace('.', '-')}"
    if level <= 2:
        numbering.toc.append(TocEntry(level, number, TAG.sub("", inner), anchor))
    if level == 1:
        return (
            f'<h1 id="{anchor}"><span class="chapno">Chapter {number}</span>'
            f'<span class="chaptitle">{inner}</span></h1>'
        )
    return f'<h{level} id="{anchor}"><span class="secno">{number}</span> {inner}</h{level}>'


def _figure(numbering: Numbering, match: re.Match[str]) -> str:
    numbering.figure += 1
    caption, src = match.groups()
    label = f"Figure {numbering.label}.{numbering.figure}"
    return (
        f'<figure><img src="{src}" alt="{label}"/>'
        f"<figcaption><b>{label}.</b> {caption}</figcaption></figure>"
    )


def _with_placeholders(text: str, blocks: list[Block], boxes: list[str]) -> str:
    fresh = iter(blocks)

    def swap(_: re.Match[str]) -> str:
        block = next(fresh)
        boxes.append(_block_html(block))
        pictures = "".join(
            f"\n![{caption}]({path.relative_to(GUIDE).as_posix()})\n"
            for path, caption in block.pictures
        )
        return f"\nGUIDEBLOCK{len(boxes) - 1}\n{pictures}\n"

    return PYCON_BLOCK.sub(swap, text)


def render_chapter(path: Path, blocks: list[Block], numbering: Numbering) -> str:
    """Expands includes and snippets, converts Markdown to HTML, numbers headings and figures.

    Files whose name starts with `00-` (front matter) or `99-` (appendix) are not numbered.
    """
    import markdown

    boxes: list[str] = []
    text = _with_placeholders(path.read_text(), blocks, boxes)
    text = INCLUDE.sub(lambda m: _include(m, boxes), text)
    body = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "codehilite", "sane_lists", "attr_list"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "code"}},
    )
    body = PLACEHOLDER.sub(lambda m: boxes[int(m.group(1))], body)
    numbered = not path.name.startswith(UNNUMBERED_PREFIXES)
    if path.name.startswith(APPENDIX_PREFIX):
        numbering.label, numbering.figure = "A", 0
    heading = _number_heading if numbered else _plain_heading
    body = HEADING.sub(lambda m: heading(numbering, m), body)
    body = FIGURE.sub(lambda m: _figure(numbering, m), body)
    return f'<section class="chapter">{body}</section>'


def _toc(numbering: Numbering) -> str:
    items = [
        f'<li class="toc{e.level}"><a href="#{e.anchor}"><span class="tocno">{e.number}</span>'
        f"{html.escape(e.title)}</a></li>"
        for e in numbering.toc
    ]
    return (
        f'<section class="toc"><h2 class="tochead">Contents</h2><ul>{"".join(items)}</ul></section>'
    )


def _title_page() -> str:
    return (
        '<section class="titlepage">'
        f'<p class="kicker">Study guide</p><h1 class="title">{html.escape(TITLE)}</h1>'
        f'<p class="subtitle">{html.escape(SUBTITLE)}</p>'
        f'<p class="edition">Edition {EDITION}</p></section>'
    )


def build_pdf(chapters: list[tuple[Path, list[Block]]]) -> int:
    """Renders every chapter, prints the PDF and returns its page count."""
    from pygments.formatters import HtmlFormatter
    from weasyprint import CSS, HTML

    numbering = Numbering()
    bodies = [render_chapter(path, blocks, numbering) for path, blocks in chapters]
    style = (GUIDE / "guide.css").read_text()
    formatter = HtmlFormatter(style="friendly")
    # types-Pygments leaves Formatter.get_style_defs unannotated.
    code_style: str = formatter.get_style_defs(".code")  # type: ignore[no-untyped-call]
    document = (
        f"<!doctype html><html><head><meta charset='utf-8'><title>{TITLE}</title></head>"
        f"<body>{_title_page()}{_toc(numbering)}{''.join(bodies)}</body></html>"
    )
    rendered = HTML(string=document, base_url=str(GUIDE)).render(
        stylesheets=[CSS(string=style), CSS(string=code_style)]
    )
    rendered.write_pdf(PDF_PATH)
    return len(rendered.pages)


def main() -> None:
    """Runs examples, figures, exercise checks and snippets, then writes the PDF."""
    parser = argparse.ArgumentParser(description="Builds the ShowPy study guide PDF.")
    parser.add_argument("--update-snippets", action="store_true", help="rewrite snippet output")
    parser.add_argument("--skip-examples", action="store_true", help="reuse example output")
    parser.add_argument("--skip-figures", action="store_true", help="reuse drawn figures")
    parser.add_argument("--skip-exercises", action="store_true", help="skip exercise checks")
    parser.add_argument("--only", default="", help="run only chapters whose name has this text")
    parser.add_argument("--no-pdf", action="store_true", help="stop before printing the PDF")
    args = parser.parse_args()
    sys.path[:0] = [str(GUIDE), str(EXAMPLES), str(EXERCISES)]
    if not args.skip_examples:
        run_examples()
    if not args.skip_figures:
        make_figures()
    if not args.skip_exercises:
        check_exercises()
    chapters = [
        (path, execute_chapter(path, args.update_snippets))
        for path in sorted(CHAPTERS.glob("*.md"))
        if args.only in path.name
    ]
    if args.no_pdf:
        return
    pages = build_pdf(chapters)
    print(f"Wrote {PDF_PATH.relative_to(REPO)} ({pages} pages)")


if __name__ == "__main__":
    main()
