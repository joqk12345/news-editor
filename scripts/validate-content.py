#!/usr/bin/env python3
"""Validate generated content metadata and index coverage."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from kb_common import CONTENT_DIR, GENERATED_BY, PROJECT_DIR, REPORTS_DIR, SUBCATEGORY_META, TAXONOMY, parse_frontmatter

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GENERATED_REPORT_TYPE = "report"
GENERATED_INDEX_TYPE = "index"
VALID_PRIORITIES = {"high", "medium", "low"}


def parse_tags(raw_tags: str) -> list[str]:
    return [tag.strip() for tag in raw_tags.strip("[]").split(",") if tag.strip()]


def expected_index_paths() -> set[Path]:
    expected = {
        CONTENT_DIR / "index.md",
        CONTENT_DIR / "taxonomy" / "index.md",
        CONTENT_DIR / "priority" / "index.md",
        CONTENT_DIR / "timeline" / "index.md",
        CONTENT_DIR / "graph" / "index.md",
    }
    for section in TAXONOMY:
        section_dir = CONTENT_DIR / section["slug"]
        expected.add(section_dir / "index.md")
        for child in section["children"]:
            expected.add(section_dir / child["slug"] / "index.md")
    return expected


def add_failure(failures: list[str], path: Path, message: str) -> None:
    failures.append(f"{path.as_posix()}: {message}")


def validate_report_page(path: Path, frontmatter: dict[str, str], failures: list[str]) -> None:
    required_keys = [
        "title",
        "description",
        "category",
        "priority",
        "priorityScore",
        "date",
        "docType",
        "sourceBucket",
        "source",
        "requestId",
    ]
    for key in required_keys:
        if not frontmatter.get(key):
            add_failure(failures, path, f"missing frontmatter key `{key}`")

    category = frontmatter.get("category", "")
    if category not in SUBCATEGORY_META:
        add_failure(failures, path, f"unknown category `{category}`")
        return

    if frontmatter.get("priority") not in VALID_PRIORITIES:
        add_failure(failures, path, f"invalid priority `{frontmatter.get('priority', '')}`")

    priority_score = frontmatter.get("priorityScore", "")
    if not priority_score.isdigit():
        add_failure(failures, path, f"invalid priorityScore `{priority_score}`")

    date = frontmatter.get("date", "")
    if date != "unknown" and not DATE_PATTERN.match(date):
        add_failure(failures, path, f"invalid date `{date}`")

    source = frontmatter.get("source", "")
    if source and not (PROJECT_DIR / source).exists():
        add_failure(failures, path, f"source file not found `{source}`")

    tags = parse_tags(frontmatter.get("tags", ""))
    section_slug, subcategory_slug = category.split("/", 1)
    for tag in [section_slug, subcategory_slug, frontmatter.get("sourceBucket", ""), frontmatter.get("docType", "")]:
        if tag and tag not in tags:
            add_failure(failures, path, f"missing required tag `{tag}`")


def validate_index_page(path: Path, failures: list[str]) -> None:
    if not path.exists():
        add_failure(failures, path, "missing generated index page")
        return

    frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
    if frontmatter.get("generatedBy") != GENERATED_BY:
        add_failure(failures, path, "missing generatedBy marker")
    if frontmatter.get("generatedType") != GENERATED_INDEX_TYPE:
        add_failure(failures, path, "missing generatedType=index marker")
    if not frontmatter.get("title"):
        add_failure(failures, path, "missing title in frontmatter")
    if not frontmatter.get("description"):
        add_failure(failures, path, "missing description in frontmatter")


def main() -> None:
    failures: list[str] = []
    report_source_paths = sorted(REPORTS_DIR.rglob("*.md"))
    generated_report_paths: list[Path] = []
    generated_index_paths: list[Path] = []

    for path in CONTENT_DIR.rglob("*.md"):
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter.get("generatedBy") != GENERATED_BY:
            continue

        generated_type = frontmatter.get("generatedType")
        if generated_type == GENERATED_REPORT_TYPE:
            generated_report_paths.append(path)
            validate_report_page(path, frontmatter, failures)
        elif generated_type == GENERATED_INDEX_TYPE:
            generated_index_paths.append(path)

    if len(generated_report_paths) != len(report_source_paths):
        failures.append(
            "generated report count mismatch: "
            f"{len(generated_report_paths)} generated pages for {len(report_source_paths)} source reports"
        )

    expected_indexes = expected_index_paths()
    actual_indexes = set(generated_index_paths)
    for path in sorted(expected_indexes):
        validate_index_page(path, failures)

    for path in sorted(actual_indexes - expected_indexes):
        add_failure(failures, path, "stale generated index page not covered by current taxonomy")

    if failures:
        print("Content validation failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)

    print(
        "Validated "
        f"{len(generated_report_paths)} generated reports and {len(actual_indexes)} generated index pages"
    )


if __name__ == "__main__":
    main()
