#!/usr/bin/env python3
"""Generate VitePress index pages for the taxonomy-first content tree."""

from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
from pathlib import Path

from kb_common import CONTENT_DIR, GENERATED_BY, SECTION_META, SUBCATEGORY_META, TAXONOMY, content_link, escape_cell, json_quote, parse_frontmatter

STRUCTURAL_TAGS = {
    section["slug"]
    for section in TAXONOMY
} | {
    child["slug"]
    for section in TAXONOMY
    for child in section["children"]
} | {
    "news",
    "task",
    "strategic",
    "text-summary",
    "link-summary",
    "rewrite",
    "general-note",
    "strategic-report",
    "hn-analysis",
}
GRAPH_EXCLUDED_TAGS = {"ai"}
GENERATED_INDEX_TYPE = "index"

GRAPH_COLORS = {
    "section_fill": "#dbeafe",
    "section_stroke": "#2563eb",
    "subcategory_fill": "#ccfbf1",
    "subcategory_stroke": "#0f766e",
    "document_fill": "#ffedd5",
    "document_stroke": "#ea580c",
    "tag_fill": "#fee2e2",
    "tag_stroke": "#dc2626",
    "edge_section": "#93c5fd",
    "edge_document": "#fdba74",
    "edge_tag": "#fca5a5",
    "text": "#0f172a",
    "subtext": "#475569",
}


def parse_tags(raw_tags: str) -> list[str]:
    return [tag.strip() for tag in raw_tags.strip("[]").split(",") if tag.strip()]


def wrap_generated_page(title: str, description: str, body: str, extra_frontmatter: list[str] | None = None) -> str:
    frontmatter = [
        "---",
        f"title: {json_quote(title)}",
        f"description: {json_quote(description)}",
        f'generatedBy: "{GENERATED_BY}"',
        f'generatedType: "{GENERATED_INDEX_TYPE}"',
    ]
    if extra_frontmatter:
        frontmatter.extend(extra_frontmatter)
    frontmatter.extend(["---", "", body.strip(), ""])
    return "\n".join(frontmatter)


def parse_document(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    relative = path.relative_to(CONTENT_DIR)
    category = frontmatter.get("category", "")
    section_slug, subcategory_slug = ("", "")
    section_title = ""
    subcategory_title = ""
    if "/" in category:
        section_slug, subcategory_slug = category.split("/", 1)
        section_title = str(SECTION_META.get(section_slug, {}).get("title", section_slug))
        subcategory_title = str(SUBCATEGORY_META.get(category, {}).get("title", subcategory_slug))

    return {
        "path": path,
        "relative": relative,
        "title": frontmatter.get("title", path.stem),
        "description": frontmatter.get("description", ""),
        "tags": parse_tags(frontmatter.get("tags", "")),
        "category": category,
        "section_slug": section_slug,
        "subcategory_slug": subcategory_slug,
        "section_title": section_title,
        "subcategory_title": subcategory_title,
        "priority": frontmatter.get("priority", "low"),
        "priority_score": int(frontmatter.get("priorityScore", "0")),
        "date": frontmatter.get("date", "unknown"),
        "doc_type": frontmatter.get("docType", "general-note"),
        "source_bucket": frontmatter.get("sourceBucket", "task"),
        "url": content_link(path),
    }


def sort_documents(documents: list[dict[str, object]]) -> list[dict[str, object]]:
    priority_rank = {"high": 3, "medium": 2, "low": 1}
    return sorted(
        documents,
        key=lambda doc: (
            priority_rank.get(str(doc["priority"]), 0),
            int(doc["priority_score"]),
            str(doc["date"]),
            str(doc["title"]),
        ),
        reverse=True,
    )


def sort_documents_by_date(documents: list[dict[str, object]]) -> list[dict[str, object]]:
    priority_rank = {"high": 3, "medium": 2, "low": 1}
    return sorted(
        documents,
        key=lambda doc: (
            "" if str(doc["date"]) == "unknown" else str(doc["date"]),
            priority_rank.get(str(doc["priority"]), 0),
            int(doc["priority_score"]),
            str(doc["title"]),
        ),
        reverse=True,
    )


def render_table(documents: list[dict[str, object]], relative_prefix: str = ".") -> list[str]:
    lines = [
        "| 标题 | 日期 | 优先级 | 标签 |",
        "|------|------|--------|------|",
    ]
    for document in documents:
        target = document["relative"].with_suffix("").as_posix()
        if relative_prefix == ".":
            link = "./" + Path(target).name
        else:
            link = document["url"]
        tags = ", ".join(document["tags"][:4]) if document["tags"] else "-"
        lines.append(
            f'| [{escape_cell(str(document["title"]))}]({link}) | {document["date"]} | '
            f'{document["priority"]} | {escape_cell(tags)} |'
        )
    return lines


def render_chip_row(chips: list[str], indent: str = "") -> list[str]:
    if not chips:
        return []
    return [
        f'{indent}<div class="kb-chip-row">',
        *[f'{indent}  <span class="kb-chip">{escape(chip)}</span>' for chip in chips],
        f"{indent}</div>",
    ]


def category_label(document: dict[str, object]) -> str:
    if document["section_title"] and document["subcategory_title"]:
        return f'{document["section_title"]} / {document["subcategory_title"]}'
    return str(document["category"])


def semantic_tags(document: dict[str, object]) -> list[str]:
    return [str(tag) for tag in document["tags"] if str(tag) not in STRUCTURAL_TAGS]


def humanize_tag(tag: str) -> str:
    return tag.replace("-", " ")


def graph_tags_for_document(document: dict[str, object], selected_tags: set[str]) -> list[str]:
    tags = [
        humanize_tag(tag)
        for tag in semantic_tags(document)
        if tag not in GRAPH_EXCLUDED_TAGS and tag in selected_tags
    ]
    if tags:
        return tags[:3]
    return [humanize_tag(tag) for tag in semantic_tags(document) if tag not in GRAPH_EXCLUDED_TAGS][:3]


def select_home_highlights(documents: list[dict[str, object]], limit: int = 6) -> list[dict[str, object]]:
    ordered = sort_documents_by_date(documents)
    selected = []
    selected_urls = set()
    seen_sections = set()

    for document in ordered:
        section_slug = str(document["section_slug"])
        document_url = str(document["url"])
        if not section_slug or section_slug in seen_sections or document_url in selected_urls:
            continue
        selected.append(document)
        selected_urls.add(document_url)
        seen_sections.add(section_slug)
        if len(selected) >= limit:
            return selected

    for document in ordered:
        document_url = str(document["url"])
        if document_url in selected_urls:
            continue
        selected.append(document)
        selected_urls.add(document_url)
        if len(selected) >= limit:
            break

    return selected


def build_home_page(documents: list[dict[str, object]]) -> str:
    ordered_by_date = sort_documents_by_date(documents)
    known_dates = [str(document["date"]) for document in ordered_by_date if str(document["date"]) != "unknown"]
    latest_date = known_dates[0] if known_dates else "unknown"
    earliest_date = known_dates[-1] if known_dates else "unknown"
    high_priority_count = sum(1 for document in documents if str(document["priority"]) == "high")
    medium_priority_count = sum(1 for document in documents if str(document["priority"]) == "medium")
    latest_highlights = select_home_highlights(documents, limit=6)

    entry_cards = [
        {
            "eyebrow": "Structure",
            "title": "分类体系",
            "description": "从一级主题域和二级分类切入，先建立整体认知框架。",
            "link": "/taxonomy/",
        },
        {
            "eyebrow": "Chronology",
            "title": "时间轴",
            "description": "按日期回看新近内容，适合跟踪素材流入节奏。",
            "link": "/timeline/",
        },
        {
            "eyebrow": "Connections",
            "title": "知识图谱",
            "description": "从主题标签和代表性文档之间的连接关系开始探索。",
            "link": "/graph/",
        },
        {
            "eyebrow": "Prioritization",
            "title": "优先级",
            "description": "直接查看高价值文档和当前最值得先读的部分。",
            "link": "/priority/",
        },
    ]

    section_cards = []
    for section in TAXONOMY:
        section_slug = section["slug"]
        section_docs = [document for document in documents if str(document["section_slug"]) == section_slug]
        section_latest = sort_documents_by_date(section_docs)[0] if section_docs else None
        section_cards.extend(
            [
                f'    <a class="kb-home-section-card" href="/{section_slug}/">',
                f'      <p class="kb-home-card-eyebrow">{escape(section["title"])}</p>',
                f'      <h3>{escape(section["description"])}</h3>',
                "      <div class=\"kb-home-card-meta\">",
                f'        <span>{len(section_docs)} 篇文档</span>',
                f'        <span>{len(section["children"])} 个子分类</span>',
                (
                    f'        <span>最近更新 {escape(str(section_latest["date"]))}</span>'
                    if section_latest
                    else "        <span>暂无内容</span>"
                ),
                "      </div>",
                (
                    f'      <p class="kb-home-card-note">代表文档：{escape(str(section_latest["title"]))}</p>'
                    if section_latest
                    else "      <p class=\"kb-home-card-note\">等待内容同步。</p>"
                ),
                "    </a>",
            ]
        )

    highlight_cards = []
    for document in latest_highlights:
        highlight_cards.extend(
            [
                f'    <a class="kb-home-highlight-card" href="{escape(str(document["url"]), quote=True)}">',
                f'      <p class="kb-home-card-eyebrow">{escape(category_label(document))}</p>',
                f'      <h3>{escape(str(document["title"]))}</h3>',
                f'      <p>{escape(str(document["description"]))}</p>',
                "      <div class=\"kb-home-card-meta\">",
                f'        <span>{escape(str(document["date"]))}</span>',
                f'        <span>{escape(str(document["priority"]))} / {int(document["priority_score"])}</span>',
                f'        <span>{escape(str(document["source_bucket"]))}</span>',
                "      </div>",
                "    </a>",
            ]
        )

    return "\n".join(
        [
            "---",
            "title: 知识库首页",
            "description: reports 素材库的自动整理结果",
            f'generatedBy: "{GENERATED_BY}"',
            f'generatedType: "{GENERATED_INDEX_TYPE}"',
            "layout: home",
            "",
            "hero:",
            '  name: "Reports Knowledge Base"',
            '  text: "把零散报告压成可导航的知识地图"',
            '  tagline: "从 reports 自动抽取、归类、排序，把时间线、主题域和重点文档组织成一个可以直接浏览的研究入口。"',
            "  actions:",
            "    - theme: brand",
            "      text: 浏览分类地图",
            "      link: /taxonomy/",
            "    - theme: alt",
            "      text: 进入时间轴",
            "      link: /timeline/",
            "---",
            "",
            '<div class="kb-home-shell">',
            '  <section class="kb-home-stats">',
            '    <article class="kb-home-stat">',
            '      <p class="kb-home-stat-label">文档规模</p>',
            f'      <strong>{len(documents)}</strong>',
            '      <span>已整理入库的可浏览文档</span>',
            "    </article>",
            '    <article class="kb-home-stat">',
            '      <p class="kb-home-stat-label">优先级</p>',
            f'      <strong>{high_priority_count}</strong>',
            f'      <span>高优先级，另有 {medium_priority_count} 篇中优先级</span>',
            "    </article>",
            '    <article class="kb-home-stat">',
            '      <p class="kb-home-stat-label">时间跨度</p>',
            f'      <strong>{escape(latest_date)}</strong>',
            f'      <span>最早可追溯至 {escape(earliest_date)}</span>',
            "    </article>",
            '    <article class="kb-home-stat">',
            '      <p class="kb-home-stat-label">主题域</p>',
            f'      <strong>{len(TAXONOMY)}</strong>',
            '      <span>覆盖 AI、市场、生活、战略与系统</span>',
            "    </article>",
            "  </section>",
            "",
            '  <section class="kb-home-block">',
            '    <div class="kb-home-heading">',
            '      <p class="kb-home-eyebrow">Browse Paths</p>',
            "      <h2>先从哪种入口开始</h2>",
            "      <p>如果你还不确定怎么浏览，这四个入口分别对应结构、时间、连接关系和优先级。</p>",
            "    </div>",
            '    <div class="kb-home-entry-grid">',
            *[
                line
                for card in entry_cards
                for line in [
                    f'      <a class="kb-home-entry-card" href="{card["link"]}">',
                    f'        <p class="kb-home-card-eyebrow">{escape(card["eyebrow"])}</p>',
                    f'        <h3>{escape(card["title"])}</h3>',
                    f'        <p>{escape(card["description"])}</p>',
                    "      </a>",
                ]
            ],
            "    </div>",
            "  </section>",
            "",
            '  <section class="kb-home-block">',
            '    <div class="kb-home-heading">',
            '      <p class="kb-home-eyebrow">Topic Domains</p>',
            "      <h2>五大主题域</h2>",
            "      <p>每个主题域都包含自己的子分类和代表性文档，适合按领域沉浸式阅读。</p>",
            "    </div>",
            '    <div class="kb-home-section-grid">',
            *section_cards,
            "    </div>",
            "  </section>",
            "",
            '  <section class="kb-home-block">',
            '    <div class="kb-home-heading">',
            '      <p class="kb-home-eyebrow">Latest Highlights</p>',
            "      <h2>最新重点文档</h2>",
            "      <p>优先展示最近进入知识库、且权重较高的文档，适合先扫一遍当前热点。</p>",
            "    </div>",
            '    <div class="kb-home-highlight-grid">',
            *highlight_cards,
            "    </div>",
            "  </section>",
            "</div>",
            "",
        ]
    )


def build_taxonomy_page(section_counts: Counter, category_counts: Counter) -> str:
    lines = [
        "# 分类体系",
        "",
        "本页记录 `reports/` 素材库的自动分类结果。当前分类优先按主题域组织，而不是按原始来源目录组织。",
        "",
        "## 一级分类",
        "",
    ]

    for section in TAXONOMY:
        lines.append(
            f'- [{section["title"]}](/{section["slug"]}/)：{section["description"]} 共 {section_counts[section["slug"]]} 篇。'
        )

    lines.extend(["", "## 二级分类", ""])

    for category, meta in SUBCATEGORY_META.items():
        lines.append(
            f'- [{meta["section_title"]} / {meta["title"]}](/{meta["section_slug"]}/{meta["slug"]}/)：'
            f'{meta["description"]} 共 {category_counts[category]} 篇。'
        )

    return wrap_generated_page(
        "分类体系",
        "按主题域和子分类查看 reports 素材库的自动整理结果。",
        "\n".join(lines),
    )


def build_priority_page(documents: list[dict[str, object]]) -> str:
    priority_counter = Counter(str(document["priority"]) for document in documents)
    top_documents = sort_documents(documents)[:20]
    lines = [
        "# 优先级总览",
        "",
        f'- 高优先级：{priority_counter["high"]} 篇',
        f'- 中优先级：{priority_counter["medium"]} 篇',
        f'- 低优先级：{priority_counter["low"]} 篇',
        "",
        "## Top 20",
        "",
        "| 排名 | 标题 | 分类 | 日期 | 优先级 |",
        "|------|------|------|------|--------|",
    ]

    for index, document in enumerate(top_documents, start=1):
        lines.append(
            f'| {index} | [{escape_cell(str(document["title"]))}]({document["url"]}) | '
            f'`{document["category"]}` | {document["date"]} | '
            f'{document["priority"]} ({document["priority_score"]}) |'
        )

    return wrap_generated_page(
        "优先级总览",
        "按优先级查看知识库中最值得优先阅读的文档。",
        "\n".join(lines),
    )


def build_timeline_page(documents: list[dict[str, object]]) -> str:
    ordered = sort_documents_by_date(documents)
    known_dates = [str(document["date"]) for document in ordered if str(document["date"]) != "unknown"]
    date_counter = Counter(str(document["date"]) for document in ordered if str(document["date"]) != "unknown")
    high_priority_count = sum(1 for document in documents if str(document["priority"]) == "high")
    latest_date = known_dates[0] if known_dates else "unknown"
    earliest_date = known_dates[-1] if known_dates else "unknown"

    lines = [
        "# 时间轴",
        "",
        "按日期串联全部整理文档，方便从最近更新倒查到更早素材，并快速看到每篇文档所属主题与优先级。",
        "",
        *render_chip_row(
            [
                f"共 {len(documents)} 篇文档",
                f"覆盖 {len(date_counter)} 个日期",
                f"高优先级 {high_priority_count} 篇",
                f"时间范围 {earliest_date} 至 {latest_date}",
            ]
        ),
        "",
        "## 按时间查看",
        "",
        '<div class="kb-timeline">',
    ]

    for document in ordered:
        chips = [
            category_label(document),
            f'{document["priority"]} / {document["priority_score"]}',
            str(document["source_bucket"]),
        ]
        chips.extend(humanize_tag(tag) for tag in semantic_tags(document)[:3])
        lines.extend(
            [
                '  <div class="kb-timeline-item">',
                f'    <div class="kb-timeline-date">{escape(str(document["date"]))}</div>',
                '    <div class="kb-timeline-card">',
                (
                    '      <div class="kb-timeline-title">'
                    f'<a href="{escape(str(document["url"]), quote=True)}">{escape(str(document["title"]))}</a>'
                    "</div>"
                ),
                f'      <p>{escape(str(document["description"]))}</p>',
                *render_chip_row(chips, "      "),
                "    </div>",
                "  </div>",
            ]
        )

    lines.extend(
        [
            "</div>",
            "",
            "## 最近重点文档",
            "",
            *[
                f'- [{document["title"]}]({document["url"]})：{document["date"]}，{category_label(document)}。'
                for document in sort_documents(documents)[:10]
            ],
            "",
        ]
    )

    return wrap_generated_page(
        "时间轴",
        "按日期串联知识库文档，追踪内容进入知识库的时间顺序。",
        "\n".join(lines),
    )


def select_featured_documents(documents: list[dict[str, object]], limit: int = 12) -> list[dict[str, object]]:
    ordered = sort_documents(documents)
    grouped = defaultdict(list)
    for document in ordered:
        grouped[str(document["category"])].append(document)

    selected = []
    selected_urls = set()

    for category in SUBCATEGORY_META:
        if len(selected) >= limit:
            break
        if not grouped[category]:
            continue
        document = grouped[category][0]
        selected.append(document)
        selected_urls.add(str(document["url"]))

    for document in ordered:
        if len(selected) >= limit:
            break
        document_url = str(document["url"])
        if document_url in selected_urls:
            continue
        selected.append(document)
        selected_urls.add(document_url)

    return selected


def select_graph_tags(documents: list[dict[str, object]], limit: int = 10) -> list[str]:
    tag_counter = Counter()
    per_document_tags: dict[str, list[str]] = {}

    for document in documents:
        document_tags = semantic_tags(document)
        per_document_tags[str(document["url"])] = document_tags
        tag_counter.update(document_tags)

    dominance_limit = max(2, int(len(documents) * 0.75))
    ordered_tags = [
        tag
        for tag, count in tag_counter.most_common()
        if tag not in GRAPH_EXCLUDED_TAGS and count < dominance_limit
    ]
    if not ordered_tags:
        ordered_tags = [tag for tag, _count in tag_counter.most_common() if tag not in GRAPH_EXCLUDED_TAGS]

    selected = ordered_tags[:limit]
    covered_documents = {
        str(document["url"])
        for document in documents
        if any(tag in selected for tag in per_document_tags[str(document["url"])])
    }

    if len(selected) >= limit:
        return selected[:limit]

    for document in documents:
        document_url = str(document["url"])
        if document_url in covered_documents:
            continue
        for tag in per_document_tags[document_url]:
            if tag in GRAPH_EXCLUDED_TAGS:
                continue
            if tag not in selected:
                selected.append(tag)
                covered_documents.add(document_url)
                break
        if len(selected) >= limit:
            break

    return selected[:limit]


def distribute_nodes(
    items: list[dict[str, object]],
    x: int,
    width: int,
    top: int,
    bottom: int,
    height: int,
) -> list[dict[str, object]]:
    if not items:
        return []

    available = bottom - top
    if len(items) == 1:
        start_y = top + (available - height) / 2
        gap = 0
    else:
        gap = max(12, (available - len(items) * height) / (len(items) - 1))
        total_height = len(items) * height + (len(items) - 1) * gap
        start_y = top + max(0, (available - total_height) / 2)

    nodes = []
    for index, item in enumerate(items):
        nodes.append(
            {
                **item,
                "x": x,
                "y": start_y + index * (height + gap),
                "width": width,
                "height": height,
            }
        )
    return nodes


def svg_curve(x1: float, y1: float, x2: float, y2: float, color: str, width: float, opacity: float = 0.8) -> str:
    control_offset = max(60.0, (x2 - x1) / 2.5)
    return (
        f'<path d="M {x1:.1f} {y1:.1f} C {x1 + control_offset:.1f} {y1:.1f}, '
        f'{x2 - control_offset:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="{width:.1f}" opacity="{opacity:.2f}" />'
    )


def truncate_label(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def svg_node(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    stroke: str,
    label: str,
    subtitle: str,
    href: str | None = None,
) -> str:
    label_x = x + 16
    label_y = y + 24
    subtitle_y = y + 40
    parts = []
    wrapper_start = f'<a href="{escape(href, quote=True)}">' if href else "<g>"
    wrapper_end = "</a>" if href else "</g>"
    parts.append(wrapper_start)
    parts.append(f"<title>{escape(label)}</title>")
    parts.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="16" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2" />'
    )
    parts.append(
        f'<text x="{label_x:.1f}" y="{label_y:.1f}" font-size="14" font-weight="700" fill="{GRAPH_COLORS["text"]}">'
        f"{escape(label)}</text>"
    )
    parts.append(
        f'<text x="{label_x:.1f}" y="{subtitle_y:.1f}" font-size="11.5" fill="{GRAPH_COLORS["subtext"]}">'
        f"{escape(subtitle)}</text>"
    )
    parts.append(wrapper_end)
    return "".join(parts)


def build_graph_svg(documents: list[dict[str, object]]) -> str:
    section_counts = Counter(str(document["section_slug"]) for document in documents if document["section_slug"])
    category_counts = Counter(str(document["category"]) for document in documents if document["category"])
    featured_documents = select_featured_documents(documents, limit=12)
    selected_tags = select_graph_tags(featured_documents, limit=10)
    selected_tag_set = set(selected_tags)
    tag_counts = Counter(tag for document in featured_documents for tag in semantic_tags(document))
    graph_width = 1460
    graph_height = 980

    section_nodes = distribute_nodes(
        [
            {
                "key": section["slug"],
                "label": section["title"],
                "subtitle": f'{section_counts[section["slug"]]} 篇文档',
            }
            for section in TAXONOMY
        ],
        x=60,
        width=220,
        top=48,
        bottom=940,
        height=58,
    )

    subcategory_nodes = distribute_nodes(
        [
            {
                "key": category,
                "label": meta["title"],
                "subtitle": f'{category_counts[category]} 篇文档',
            }
            for category, meta in SUBCATEGORY_META.items()
        ],
        x=360,
        width=260,
        top=48,
        bottom=940,
        height=58,
    )

    document_nodes = distribute_nodes(
        [
            {
                "key": str(document["url"]),
                "label": truncate_label(str(document["title"]), 24),
                "subtitle": f'{document["priority"]} / {document["date"]}',
                "href": str(document["url"]),
            }
            for document in featured_documents
        ],
        x=760,
        width=320,
        top=48,
        bottom=940,
        height=58,
    )

    tag_nodes = distribute_nodes(
        [
            {
                "key": tag,
                "label": truncate_label(humanize_tag(tag), 22),
                "subtitle": f'{tag_counts[tag]} 篇重点文档',
            }
            for tag in selected_tags
        ],
        x=1200,
        width=220,
        top=48,
        bottom=940,
        height=58,
    )

    section_lookup = {str(node["key"]): node for node in section_nodes}
    subcategory_lookup = {str(node["key"]): node for node in subcategory_nodes}
    document_lookup = {str(node["key"]): node for node in document_nodes}
    tag_lookup = {str(node["key"]): node for node in tag_nodes}

    edges = []
    for category, meta in SUBCATEGORY_META.items():
        section_node = section_lookup[meta["section_slug"]]
        subcategory_node = subcategory_lookup[category]
        edges.append(
            svg_curve(
                float(section_node["x"]) + float(section_node["width"]),
                float(section_node["y"]) + float(section_node["height"]) / 2,
                float(subcategory_node["x"]),
                float(subcategory_node["y"]) + float(subcategory_node["height"]) / 2,
                GRAPH_COLORS["edge_section"],
                1.6 + category_counts[category] / 10,
                0.65,
            )
        )

    for document in featured_documents:
        subcategory_node = subcategory_lookup[str(document["category"])]
        document_node = document_lookup[str(document["url"])]
        edges.append(
            svg_curve(
                float(subcategory_node["x"]) + float(subcategory_node["width"]),
                float(subcategory_node["y"]) + float(subcategory_node["height"]) / 2,
                float(document_node["x"]),
                float(document_node["y"]) + float(document_node["height"]) / 2,
                GRAPH_COLORS["edge_document"],
                2.0,
                0.7,
            )
        )

        document_tags = [tag for tag in semantic_tags(document) if tag in selected_tag_set][:2]
        for tag in document_tags:
            tag_node = tag_lookup[tag]
            edges.append(
                svg_curve(
                    float(document_node["x"]) + float(document_node["width"]),
                    float(document_node["y"]) + float(document_node["height"]) / 2,
                    float(tag_node["x"]),
                    float(tag_node["y"]) + float(tag_node["height"]) / 2,
                    GRAPH_COLORS["edge_tag"],
                    1.4 + tag_counts[tag] / 6,
                    0.75,
                )
            )

    node_parts = []
    node_parts.extend(
        svg_node(
            x=float(node["x"]),
            y=float(node["y"]),
            width=float(node["width"]),
            height=float(node["height"]),
            fill=GRAPH_COLORS["section_fill"],
            stroke=GRAPH_COLORS["section_stroke"],
            label=str(node["label"]),
            subtitle=str(node["subtitle"]),
        )
        for node in section_nodes
    )
    node_parts.extend(
        svg_node(
            x=float(node["x"]),
            y=float(node["y"]),
            width=float(node["width"]),
            height=float(node["height"]),
            fill=GRAPH_COLORS["subcategory_fill"],
            stroke=GRAPH_COLORS["subcategory_stroke"],
            label=str(node["label"]),
            subtitle=str(node["subtitle"]),
        )
        for node in subcategory_nodes
    )
    node_parts.extend(
        svg_node(
            x=float(node["x"]),
            y=float(node["y"]),
            width=float(node["width"]),
            height=float(node["height"]),
            fill=GRAPH_COLORS["document_fill"],
            stroke=GRAPH_COLORS["document_stroke"],
            label=str(node["label"]),
            subtitle=str(node["subtitle"]),
            href=str(node["href"]),
        )
        for node in document_nodes
    )
    node_parts.extend(
        svg_node(
            x=float(node["x"]),
            y=float(node["y"]),
            width=float(node["width"]),
            height=float(node["height"]),
            fill=GRAPH_COLORS["tag_fill"],
            stroke=GRAPH_COLORS["tag_stroke"],
            label=str(node["label"]),
            subtitle=str(node["subtitle"]),
        )
        for node in tag_nodes
    )

    return "\n".join(
        [
            f'<svg viewBox="0 0 {graph_width} {graph_height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="kb-graph-title">',
            '  <title id="kb-graph-title">知识库知识图谱</title>',
            '  <text x="60" y="24" font-size="12" fill="#64748b">一级分类</text>',
            '  <text x="360" y="24" font-size="12" fill="#64748b">二级分类</text>',
            '  <text x="760" y="24" font-size="12" fill="#64748b">重点文档</text>',
            '  <text x="1200" y="24" font-size="12" fill="#64748b">主题标签</text>',
            *[f"  {edge}" for edge in edges],
            *[f"  {node}" for node in node_parts],
            "</svg>",
        ]
    )


def build_graph_page(documents: list[dict[str, object]]) -> str:
    section_counts = Counter(str(document["section_slug"]) for document in documents if document["section_slug"])
    category_counts = Counter(str(document["category"]) for document in documents if document["category"])
    featured_documents = select_featured_documents(documents, limit=12)
    selected_tags = select_graph_tags(featured_documents, limit=10)
    selected_tag_set = set(selected_tags)
    graph_tag_counts = Counter(
        tag
        for document in featured_documents
        for tag in semantic_tags(document)
        if tag in selected_tag_set
    )
    busiest_section = max(section_counts.items(), key=lambda item: (item[1], item[0])) if section_counts else None
    busiest_category = max(category_counts.items(), key=lambda item: (item[1], item[0])) if category_counts else None
    busiest_tag = max(graph_tag_counts.items(), key=lambda item: (item[1], item[0])) if graph_tag_counts else None

    lines = [
        "# 知识图谱",
        "",
        "把分类结构、重点文档和高频主题标签放到同一张图里，便于从主题域快速跳到代表性材料，再顺着标签回看相关脉络。",
        "",
        *render_chip_row(
            [
                f"共 {len(documents)} 篇文档",
                f"展示 {len(featured_documents)} 篇重点文档",
                f"{len(selected_tags)} 个高频主题标签",
            ]
        ),
        "",
        "## 图例",
        "",
        '<div class="kb-graph-legend">',
        f'  <div class="kb-graph-legend-item"><span class="kb-graph-swatch" style="background:{GRAPH_COLORS["section_stroke"]}"></span><span>一级分类</span></div>',
        f'  <div class="kb-graph-legend-item"><span class="kb-graph-swatch" style="background:{GRAPH_COLORS["subcategory_stroke"]}"></span><span>二级分类</span></div>',
        f'  <div class="kb-graph-legend-item"><span class="kb-graph-swatch" style="background:{GRAPH_COLORS["document_stroke"]}"></span><span>重点文档</span></div>',
        f'  <div class="kb-graph-legend-item"><span class="kb-graph-swatch" style="background:{GRAPH_COLORS["tag_stroke"]}"></span><span>主题标签</span></div>',
        "</div>",
        "",
        "## 图谱",
        "",
        '<div class="kb-graph-shell">',
        build_graph_svg(documents),
        "</div>",
        "",
        "## 关键连接",
        "",
        (
            f'- 最活跃一级分类：`{str(SECTION_META[busiest_section[0]]["title"])}`，共 {busiest_section[1]} 篇文档。'
            if busiest_section
            else "- 最活跃一级分类：暂无文档。"
        ),
        (
            f'- 最密集二级分类：`{SUBCATEGORY_META[busiest_category[0]]["section_title"]} / '
            f'{SUBCATEGORY_META[busiest_category[0]]["title"]}`，共 {busiest_category[1]} 篇文档。'
            if busiest_category
            else "- 最密集二级分类：暂无文档。"
        ),
        (
            f'- 图谱中最密集的主题标签：`{humanize_tag(busiest_tag[0])}`，连接 {busiest_tag[1]} 篇重点文档。'
            if busiest_tag
            else "- 图谱中暂无可稳定提取的主题标签。"
        ),
        "",
        "## 重点文档入口",
        "",
        *[
            (
                f'- [{document["title"]}]({document["url"]})：'
                f'{category_label(document)}，{document["date"]}，'
                f'标签 {", ".join(graph_tags_for_document(document, selected_tag_set)) or str(document["doc_type"])}。'
            )
            for document in featured_documents
        ],
        "",
    ]

    return wrap_generated_page(
        "知识图谱",
        "用静态图谱查看主题域、子分类、重点文档和主题标签之间的连接关系。",
        "\n".join(lines),
        extra_frontmatter=[
            'pageClass: "kb-graph-page"',
            "aside: false",
            "outline: false",
        ],
    )


def build_section_page(section: dict[str, object], documents: list[dict[str, object]], category_counts: Counter) -> str:
    lines = [
        f'# {section["title"]}',
        "",
        section["description"],
        "",
        "## 子分类",
        "",
    ]

    for child in section["children"]:
        category = f'{section["slug"]}/{child["slug"]}'
        lines.append(
            f'- [{child["title"]}](./{child["slug"]}/)：{child["description"]} 共 {category_counts[category]} 篇。'
        )

    lines.extend(["", "## 最近更新", ""])
    section_docs = sort_documents(documents)[:8]
    lines.extend(f'- [{document["title"]}]({document["url"]})' for document in section_docs)
    return wrap_generated_page(
        str(section["title"]),
        str(section["description"]),
        "\n".join(lines),
    )


def build_subcategory_page(meta: dict[str, str], documents: list[dict[str, object]]) -> str:
    lines = [
        f'# {meta["title"]}',
        "",
        meta["description"],
        "",
        f'上级分类：[ {meta["section_title"]} ](/{meta["section_slug"]}/)',
        "",
        f"共 {len(documents)} 篇文档。",
        "",
        "## 文档列表",
        "",
        *render_table(documents),
        "",
    ]
    return wrap_generated_page(
        str(meta["title"]),
        str(meta["description"]),
        "\n".join(lines),
    )


def cleanup_generated_indexes(expected_output_paths: set[Path]) -> None:
    if not CONTENT_DIR.exists():
        return

    for path in CONTENT_DIR.rglob("*.md"):
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter.get("generatedBy") != GENERATED_BY:
            continue
        if frontmatter.get("generatedType") != GENERATED_INDEX_TYPE:
            continue
        if path not in expected_output_paths:
            path.unlink()


def prune_empty_directories(root: Path) -> None:
    if not root.exists():
        return

    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not path.is_dir():
            continue
        try:
            path.rmdir()
        except OSError:
            continue


def main() -> None:
    documents = []
    for path in CONTENT_DIR.rglob("*.md"):
        if path.name == "index.md":
            continue
        documents.append(parse_document(path))

    documents = sort_documents(documents)
    section_groups = defaultdict(list)
    category_groups = defaultdict(list)
    section_counts = Counter()
    category_counts = Counter()

    for document in documents:
        category = str(document["category"])
        if not category:
            continue
        section_slug, _subcategory_slug = category.split("/", 1)
        section_groups[section_slug].append(document)
        category_groups[category].append(document)
        section_counts[section_slug] += 1
        category_counts[category] += 1

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    expected_output_paths = {
        CONTENT_DIR / "index.md",
        CONTENT_DIR / "taxonomy" / "index.md",
        CONTENT_DIR / "priority" / "index.md",
        CONTENT_DIR / "timeline" / "index.md",
        CONTENT_DIR / "graph" / "index.md",
    }
    for section in TAXONOMY:
        section_dir = CONTENT_DIR / section["slug"]
        expected_output_paths.add(section_dir / "index.md")
        for child in section["children"]:
            expected_output_paths.add(section_dir / child["slug"] / "index.md")

    cleanup_generated_indexes(expected_output_paths)
    (CONTENT_DIR / "index.md").write_text(build_home_page(documents), encoding="utf-8")

    taxonomy_dir = CONTENT_DIR / "taxonomy"
    taxonomy_dir.mkdir(parents=True, exist_ok=True)
    (taxonomy_dir / "index.md").write_text(
        build_taxonomy_page(section_counts, category_counts),
        encoding="utf-8",
    )

    priority_dir = CONTENT_DIR / "priority"
    priority_dir.mkdir(parents=True, exist_ok=True)
    (priority_dir / "index.md").write_text(build_priority_page(documents), encoding="utf-8")

    timeline_dir = CONTENT_DIR / "timeline"
    timeline_dir.mkdir(parents=True, exist_ok=True)
    (timeline_dir / "index.md").write_text(build_timeline_page(documents), encoding="utf-8")

    graph_dir = CONTENT_DIR / "graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "index.md").write_text(build_graph_page(documents), encoding="utf-8")

    for section in TAXONOMY:
        section_dir = CONTENT_DIR / section["slug"]
        section_dir.mkdir(parents=True, exist_ok=True)
        (section_dir / "index.md").write_text(
            build_section_page(section, section_groups[section["slug"]], category_counts),
            encoding="utf-8",
        )

        for child in section["children"]:
            category = f'{section["slug"]}/{child["slug"]}'
            subcategory_dir = section_dir / child["slug"]
            subcategory_dir.mkdir(parents=True, exist_ok=True)
            (subcategory_dir / "index.md").write_text(
                build_subcategory_page(SUBCATEGORY_META[category], category_groups[category]),
                encoding="utf-8",
            )

    prune_empty_directories(CONTENT_DIR)
    print(f"Generated home, taxonomy, priority, timeline, graph, and section indexes for {len(documents)} documents")


if __name__ == "__main__":
    main()
