"""Source extraction for the Godot documentation knowledge index."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable

from .schema import entity_id, member_id, source_id, tokenize, topic_id

ROLE_RE = re.compile(r":(?P<role>[A-Za-z0-9_-]+):`(?P<body>[^`]+)`")
LABEL_RE = re.compile(r"^\s*\.\. _(?P<label>[^\s:]+):\s*$")
TOCTREE_RE = re.compile(r"^(?P<indent>\s*)\.\. toctree::")
DIRECTIVE_RE = re.compile(r"^\s*\.\.\s+(?P<name>[A-Za-z0-9_-]+)::(?:\s+(?P<arg>.*))?$")
CODE_DIRECTIVE_RE = re.compile(
    r"^\s*\.\.\s+(?P<name>code-block|code)::(?:\s+(?P<language>[^ ]+))?\s*$"
)
HEADING_RE = re.compile(r"^\s*(?P<char>[=\-~^\"'+`#*])(?P=char){2,}\s*$")
XML_SOURCE_RE = re.compile(r"^\.\. XML source:\s*(?P<source>\S+)", re.MULTILINE)
INHERITS_RE = re.compile(r"^\*\*(?P<kind>Inherits|Inherited By):\*\*\s*(?P<body>.*)$")

SECTION_LEVELS = {
    "=": 1,
    "-": 2,
    "~": 3,
    "^": 4,
    '"': 5,
    "'": 6,
    "`": 7,
    "#": 8,
    "*": 9,
}

MEMBER_KINDS = (
    "private_method",
    "virtual_method",
    "theme_item",
    "theme_constant",
    "theme_style",
    "theme_color",
    "theme_font",
    "theme_icon",
    "annotation",
    "constructor",
    "operator",
    "property",
    "constant",
    "signal",
    "method",
    "enum",
)

STOP_WORDS = {
    "about",
    "also",
    "and",
    "are",
    "based",
    "can",
    "do",
    "for",
    "from",
    "godot",
    "how",
    "in",
    "into",
    "is",
    "it",
    "more",
    "not",
    "of",
    "once",
    "only",
    "that",
    "the",
    "their",
    "this",
    "to",
    "using",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
}


@dataclass
class Section:
    title: str
    level: int
    line_start: int
    line_end: int
    heading_path: list[str]
    text: str


@dataclass
class ParsedPage:
    path: str
    kind: str
    text: str
    lines: list[str]
    sha256: str
    title: str
    headings: list[dict] = field(default_factory=list)
    labels: list[dict] = field(default_factory=list)
    toctree_entries: list[dict] = field(default_factory=list)
    refs: list[dict] = field(default_factory=list)
    code_blocks: list[dict] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)

    @property
    def source_id(self) -> str:
        return source_id(self.path)

    @property
    def topic_id(self) -> str:
        return topic_id(self.path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_page(root: Path, path: Path) -> ParsedPage:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    relative = path.relative_to(root).as_posix()
    kind = "entity" if relative.startswith("classes/") and relative != "classes/index.rst" else "topic"
    return parse_page(relative, kind, text, hashlib.sha256(raw).hexdigest())


def discover_pages(root: Path) -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    for path in sorted(root.rglob("*.rst")):
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        if any(part in {"_build", "_tools"} for part in relative_parts):
            continue
        pages.append(read_page(root, path))
    return pages


def parse_page(path: str, kind: str, text: str, content_hash: str | None = None) -> ParsedPage:
    lines = text.splitlines()
    headings = parse_headings(lines)
    labels = parse_labels(lines) + parse_toctree_names(lines)
    labels.sort(key=lambda item: item["line"])
    code_blocks = parse_code_blocks(lines)
    refs = parse_references(lines, code_blocks)
    sections = parse_sections(lines, headings)
    title = headings[0]["title"] if headings else Path(path).stem
    return ParsedPage(
        path=PurePosixPath(path).as_posix(),
        kind=kind,
        text=text,
        lines=lines,
        sha256=content_hash or sha256_text(text),
        title=title,
        headings=headings,
        labels=labels,
        toctree_entries=parse_toctrees(lines),
        refs=refs,
        code_blocks=code_blocks,
        sections=sections,
    )


def parse_headings(lines: list[str]) -> list[dict]:
    headings: list[dict] = []
    for index in range(len(lines) - 1):
        title = lines[index].strip()
        match = HEADING_RE.match(lines[index + 1])
        if not title or not match or len(lines[index + 1].strip()) < len(title):
            continue
        char = match.group("char")
        headings.append(
            {
                "title": clean_inline(title),
                "level": SECTION_LEVELS.get(char, 9),
                "line": index + 1,
                "underline": char,
            }
        )
    return headings


def parse_labels(lines: list[str]) -> list[dict]:
    labels: list[dict] = []
    for index, line in enumerate(lines):
        match = LABEL_RE.match(line)
        if match:
            labels.append({"label": match.group("label"), "line": index + 1})
    return labels


def parse_toctrees(lines: list[str]) -> list[dict]:
    entries: list[dict] = []
    for index, line in enumerate(lines):
        match = TOCTREE_RE.match(line)
        if not match:
            continue
        base_indent = len(match.group("indent").expandtabs(8))
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= base_indent:
                break
            stripped = candidate.strip()
            if stripped and not stripped.startswith(":") and not stripped.startswith(".."):
                display, target = split_link_target(stripped)
                entries.append(
                    {
                        "target": target,
                        "display": display,
                        "line": cursor + 1,
                    }
                )
            cursor += 1
    return entries


def parse_toctree_names(lines: list[str]) -> list[dict]:
    labels: list[dict] = []
    for index, line in enumerate(lines):
        match = TOCTREE_RE.match(line)
        if not match:
            continue
        base_indent = len(match.group("indent").expandtabs(8))
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= base_indent:
                break
            option = re.match(r"^\s*:name:\s*(?P<name>\S+)\s*$", candidate)
            if option:
                labels.append({"label": option.group("name"), "line": cursor + 1, "kind": "toctree"})
            cursor += 1
    return labels


def parse_code_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    index = 0
    while index < len(lines):
        match = CODE_DIRECTIVE_RE.match(lines[index])
        if match:
            start = index + 1
            end = find_indented_end(lines, index)
            blocks.append(
                {
                    "kind": "code",
                    "language": match.group("language") or "text",
                    "line_start": start + 1,
                    "line_end": end,
                }
            )
            index = end
            continue
        stripped = lines[index].rstrip()
        if stripped.endswith("::") and not stripped.lstrip().startswith(".."):
            end = find_indented_end(lines, index)
            if end > index + 1:
                blocks.append(
                    {
                        "kind": "literal",
                        "language": "text",
                        "line_start": index + 2,
                        "line_end": end,
                    }
                )
                index = end
                continue
        index += 1
    return blocks


def find_indented_end(lines: list[str], directive_index: int) -> int:
    cursor = directive_index + 1
    while cursor < len(lines):
        line = lines[cursor]
        if line.strip() and not line[:1].isspace():
            break
        cursor += 1
    return cursor


def parse_references(lines: list[str], code_blocks: list[dict]) -> list[dict]:
    references: list[dict] = []
    code_ranges = {(block["line_start"] - 1, block["line_end"]) for block in code_blocks}
    for index, line in enumerate(lines):
        if any(start <= index < end for start, end in code_ranges):
            continue
        for match in ROLE_RE.finditer(line):
            display, target = split_link_target(match.group("body"))
            references.append(
                {
                    "role": match.group("role"),
                    "display": clean_inline(display),
                    "target": target,
                    "line": index + 1,
                }
            )
    return references


def parse_sections(lines: list[str], headings: list[dict]) -> list[Section]:
    if not headings:
        text = "\n".join(lines).strip()
        return [Section("", 1, 1, len(lines), [], text)] if text else []

    sections: list[Section] = []
    for index, heading in enumerate(headings):
        end = len(lines)
        for following in headings[index + 1 :]:
            if following["level"] <= heading["level"]:
                end = following["line"] - 1
                break
        next_heading_line = heading["line"]
        if index + 1 < len(headings):
            next_heading_line = headings[index + 1]["line"]
        raw_start = heading["line"] + 1
        raw_end = next_heading_line - 1
        text = "\n".join(lines[raw_start:raw_end]).strip()
        path = build_heading_path(headings, index)
        sections.append(
            Section(
                title=heading["title"],
                level=heading["level"],
                line_start=heading["line"],
                line_end=end,
                heading_path=path,
                text=text,
            )
        )

    first_heading = headings[0]["line"] - 1
    preamble = "\n".join(lines[:first_heading]).strip()
    if preamble:
        sections.insert(0, Section("", 1, 1, first_heading, [], preamble))
    return sections


def build_heading_path(headings: list[dict], current_index: int) -> list[str]:
    current = headings[current_index]
    path: list[str] = []
    for heading in headings[: current_index + 1]:
        while len(path) >= heading["level"]:
            path.pop()
        path.append(heading["title"])
    while len(path) > current["level"]:
        path.pop()
    return path


def split_link_target(value: str) -> tuple[str, str]:
    value = value.strip()
    if value.endswith(">") and "<" in value:
        display, target = value.rsplit("<", 1)
        return display.strip(), target[:-1].strip()
    return value, value


def clean_inline(value: str) -> str:
    def replace_role(match: re.Match[str]) -> str:
        display, _ = split_link_target(match.group("body"))
        return display

    value = ROLE_RE.sub(replace_role, value)
    value = re.sub(r"``([^`]+)``", r"\1", value)
    value = re.sub(r"`([^`]+)`_", r"\1", value)
    value = re.sub(r"\|([^|]+)\|", r"\1", value)
    value = re.sub(r"\\([^\s])", r"\1", value)
    value = value.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", value).strip()


def plain_text(value: str) -> str:
    output: list[str] = []
    for raw_line in value.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if output and output[-1] != "":
                output.append("")
            continue
        if stripped.startswith(".. ") or stripped.startswith(":") and not stripped.startswith("::"):
            continue
        if re.match(r"^[+|=-]{3,}$", stripped):
            continue
        cleaned = clean_inline(stripped)
        cleaned = cleaned.strip("| ")
        if cleaned:
            output.append(cleaned)
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output)


def first_paragraph(lines: Iterable[str], max_length: int = 700) -> str:
    paragraph: list[str] = []
    started = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith(".. ") or stripped.startswith(":") or stripped.startswith("+"):
            continue
        if stripped.startswith("**Inherits:") or stripped.startswith("**Inherited By:"):
            continue
        if re.match(r"^[+|=-]{3,}$", stripped):
            continue
        started = True
        paragraph.append(clean_inline(stripped))
    summary = re.sub(r"\s+", " ", " ".join(paragraph)).strip()
    return summary[: max_length - 1].rstrip() + "..." if len(summary) > max_length else summary


def page_summary(page: ParsedPage) -> str:
    start = 0
    if page.headings:
        start = page.headings[0]["line"]
    return first_paragraph(page.lines[start:])


def page_keywords(page: ParsedPage) -> list[str]:
    candidates = [page.title]
    candidates.extend(heading["title"] for heading in page.headings)
    candidates.extend(label["label"] for label in page.labels)
    terms = {
        token
        for candidate in candidates
        for token in tokenize(candidate)
        if token not in STOP_WORDS
    }
    return sorted(terms)


def section_chunks(page: ParsedPage, max_length: int = 6000) -> list[dict]:
    chunks: list[dict] = []
    ordinal = 0
    for section in page.sections:
        content = plain_text(section.text)
        if not content:
            continue
        paragraphs = content.split("\n\n")
        current: list[str] = []
        current_length = 0
        part = 0
        for paragraph in paragraphs:
            if current and current_length + len(paragraph) + 2 > max_length:
                chunks.append(
                    {
                        "heading_path": section.heading_path,
                        "line_start": section.line_start,
                        "line_end": section.line_end,
                        "part": part,
                        "text": "\n\n".join(current),
                    }
                )
                ordinal += 1
                current = []
                current_length = 0
                part += 1
            current.append(paragraph)
            current_length += len(paragraph) + 2
        if current:
            chunks.append(
                {
                    "heading_path": section.heading_path,
                    "line_start": section.line_start,
                    "line_end": section.line_end,
                    "part": part,
                    "text": "\n\n".join(current),
                }
            )
            ordinal += 1
    return chunks


def class_name_from_page(page: ParsedPage) -> tuple[str, str]:
    labels = [label["label"] for label in page.labels]
    for label in labels:
        if label.startswith("class_") and label.count("_") == 1:
            return label[len("class_") :], label
    return page.title, "class_" + page.title


def class_member_label(label: str, class_label: str) -> tuple[str, str] | None:
    prefix = class_label + "_"
    if not label.startswith(prefix):
        return None
    suffix = label[len(prefix) :]
    for kind in sorted(MEMBER_KINDS, key=len, reverse=True):
        marker = kind + "_"
        if suffix.startswith(marker):
            name = suffix[len(marker) :]
            if name:
                return kind, name
    return None


def class_enum_label(label: str, class_name: str) -> tuple[str, str] | None:
    prefix = "enum_" + class_name + "_"
    if label.startswith(prefix):
        name = label[len(prefix) :]
        if name:
            return "enum", name
    return None


def line_after_label(page: ParsedPage, label_line: int) -> list[str]:
    start = label_line
    end = len(page.lines)
    for label in page.labels:
        if label["line"] > label_line:
            end = label["line"] - 1
            break
    return page.lines[start:end]


def member_signature(page: ParsedPage, label_line: int) -> str:
    for line in line_after_label(page, label_line)[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("..") or stripped == "----":
            continue
        return clean_inline(stripped)[:600]
    return ""


def member_description(page: ParsedPage, label_line: int) -> str:
    lines = line_after_label(page, label_line)[1:]
    signature_seen = False
    body: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".. _"):
            break
        if stripped.startswith(".. rst-class::") or stripped == "----":
            continue
        if not signature_seen and stripped:
            signature_seen = True
            continue
        body.append(line)
    return plain_text("\n".join(body))[:1600]


def parse_class_entities(page: ParsedPage) -> tuple[dict, list[dict]]:
    class_name, class_label = class_name_from_page(page)
    class_entity = {
        "id": entity_id(class_name),
        "kind": "class",
        "name": class_name,
        "title": page.title,
        "source_path": page.path,
        "source_hash": page.sha256,
        "labels": [class_label],
        "summary": page_summary(page),
        "inherits": [],
        "inherited_by": [],
        "members": [],
        "xml_source": next(
            (match.group("source") for match in XML_SOURCE_RE.finditer(page.text)),
            None,
        ),
    }
    for line in page.lines:
        match = INHERITS_RE.match(line.strip())
        if not match:
            continue
        refs = [
            target
            for reference in parse_references([match.group("body")], [])
            if (target := reference["target"]).startswith("class_")
        ]
        names = [target[len("class_") :] for target in refs]
        class_entity["inherits" if match.group("kind") == "Inherits" else "inherited_by"] = names

    line_by_label = {item["label"]: item["line"] for item in page.labels}
    members: list[dict] = []
    seen: set[str] = set()
    for label, label_line in line_by_label.items():
        member = class_member_label(label, class_label)
        if member is None:
            member = class_enum_label(label, class_name)
        if member is None:
            continue
        kind, name = member
        identifier = member_id(class_name, kind, name)
        if identifier in seen:
            continue
        seen.add(identifier)
        record = {
            "id": identifier,
            "kind": kind,
            "name": name,
            "owner": entity_id(class_name),
            "source_path": page.path,
            "source_hash": page.sha256,
            "label": label,
            "signature": member_signature(page, label_line),
            "description": member_description(page, label_line),
        }
        members.append(record)
        class_entity["members"].append(identifier)
    members.sort(key=lambda item: item["id"])
    class_entity["members"].sort()
    return class_entity, members


__all__ = [
    "ParsedPage",
    "Section",
    "class_member_label",
    "discover_pages",
    "entity_id",
    "first_paragraph",
    "page_keywords",
    "page_summary",
    "parse_class_entities",
    "parse_page",
    "plain_text",
    "section_chunks",
    "sha256_text",
    "split_link_target",
    "tokenize",
]
