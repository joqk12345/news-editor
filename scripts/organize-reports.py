#!/usr/bin/env python3
"""Organize reports into a taxonomy-first VitePress content tree."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from kb_common import CONTENT_DIR, GENERATED_BY, REPORTS_DIR, SUBCATEGORY_META, format_tags, json_quote, parse_frontmatter, shorten, slugify

CATEGORY_ORDER = list(SUBCATEGORY_META.keys())
GENERATED_REPORT_TYPE = "report"

CATEGORY_RULES = {
    "operations/fetch-failures": [
        ("原文内容未获取", 10),
        ("环境异常", 8),
        ("无法获取", 8),
        ("未发布", 7),
        ("openrouter_api_key", 9),
        ("配置失败", 6),
        ("抓取异常", 8),
    ],
    "world-strategy/strategic-research": [
        ("战略研究", 8),
        ("strategic research", 8),
        ("marketstructurelens", 4),
        ("policyrisklens", 4),
        ("watchlist", 4),
        ("signal", 2),
        ("scenario", 3),
        ("战争", 5),
        ("iran", 5),
        ("hormuz", 5),
        ("出口限制", 3),
        ("政策", 2),
        ("policy", 2),
    ],
    "markets-wealth/investing-strategy": [
        ("投资", 5),
        ("定投", 5),
        ("比特币", 5),
        ("bitcoin", 5),
        ("期权", 5),
        ("options", 5),
        ("熊市", 4),
        ("capital", 2),
        ("market", 2),
        ("市场", 2),
        ("股票", 3),
        ("资产", 2),
    ],
    "markets-wealth/wealth-psychology": [
        ("财富", 4),
        ("wealth", 4),
        ("心理", 3),
        ("psychology", 3),
        ("消费", 3),
        ("借贷", 4),
        ("社交资本", 5),
        ("长期主义", 3),
        ("杠杆", 2),
        ("risk management", 2),
        ("风险偏好", 2),
    ],
    "people-life/relationships-trust": [
        ("关系", 5),
        ("信任", 5),
        ("trust", 5),
        ("善意", 4),
        ("伤害", 3),
        ("书单", 2),
        ("人际", 4),
        ("合作边界", 4),
    ],
    "people-life/family-growth": [
        ("家庭", 5),
        ("family", 5),
        ("育儿", 5),
        ("生育", 5),
        ("月子", 4),
        ("成长", 3),
        ("教育者", 3),
        ("教育心态", 3),
        ("parenting", 5),
        ("child", 3),
    ],
    "ai-software/agents-tooling": [
        ("agent", 3),
        ("代理", 3),
        ("subagent", 5),
        ("子代理", 5),
        ("claude", 4),
        ("codebase", 4),
        ("代码库", 4),
        ("编码", 2),
        ("工具", 2),
        ("workflow", 2),
        ("mcp", 2),
        ("programming language", 3),
        ("编程语言", 3),
        ("rust", 2),
        ("智能体定义问题", 5),
        ("agent definition", 5),
        ("gep", 4),
        ("技能", 2),
        ("背景代理", 4),
        ("远程控制", 3),
        ("个人ai基础设施", 3),
        ("pai", 3),
    ],
    "ai-software/models-research": [
        ("模型", 3),
        ("model", 3),
        ("芯片", 4),
        ("qwen", 4),
        ("glm", 4),
        ("dualpath", 5),
        ("推理", 3),
        ("inference", 3),
        ("i/o", 4),
        ("kv cache", 4),
        ("rdma", 4),
        ("数据中心", 4),
        ("基础设施", 2),
        ("研究", 2),
        ("research", 2),
        ("fair", 4),
        ("何恺明", 4),
        ("deepmind", 3),
        ("m5", 4),
        ("裁员", 3),
        ("layoff", 3),
        ("llvm", 3),
        ("科研", 3),
    ],
    "operations/systems-workflows": [
        ("框架", 4),
        ("framework", 4),
        ("系统", 3),
        ("workflow", 2),
        ("mercury", 4),
        ("youtube music", 4),
        ("播放器", 3),
        ("阅读体验", 3),
        ("内容应用", 3),
        ("一人公司", 4),
        ("综合报告", 3),
        ("protocol", 3),
        ("evomap", 5),
        ("mce", 5),
        ("重写", 3),
        ("rewrite", 3),
        ("task processing", 3),
        ("工作流", 3),
        ("数据导出", 4),
        ("team evaluation", 4),
        ("团队评价", 4),
        ("产品", 2),
        ("music", 2),
    ],
    "world-strategy/culture-history": [
        ("圣家堂", 6),
        ("高迪", 6),
        ("architecture", 4),
        ("文化", 3),
        ("历史", 3),
        ("history", 3),
        ("纪念", 2),
    ],
}

TAG_RULES = {
    "ai": ["ai", "模型", "model", "llm"],
    "agents": ["agent", "代理", "subagent", "子代理"],
    "tooling": ["tool", "工具", "workflow", "workflows", "codebase", "代码库"],
    "models": ["模型", "model", "qwen", "glm"],
    "infrastructure": ["基础设施", "芯片", "data center", "数据中心", "rdma", "kv cache", "i/o"],
    "research": ["研究", "research", "科研", "fair", "何恺明"],
    "strategy": ["战略", "policy", "政策", "scenario", "watchlist", "signal"],
    "investing": ["投资", "定投", "期权", "比特币", "bitcoin", "熊市", "market"],
    "wealth": ["财富", "wealth", "消费", "借贷", "杠杆"],
    "psychology": ["心理", "psychology", "偏好"],
    "family": ["家庭", "family", "育儿", "生育", "parenting"],
    "relationships": ["关系", "信任", "trust", "善意"],
    "history": ["高迪", "圣家堂", "历史", "history"],
    "operations": ["框架", "framework", "工作流", "workflow", "系统"],
    "product": ["产品", "app", "mercury", "播放器", "music"],
    "education": ["教育", "school", "导师", "educat"],
    "programming-languages": ["编程语言", "programming language", "rust", "xgo", "llvm"],
}


def detect_source_bucket(path: Path) -> str:
    relative = path.relative_to(REPORTS_DIR)
    if relative.parts[0] == "news":
        return "news"
    if relative.parts[0] == "strategic":
        return "strategic"
    return "task"


def detect_doc_type(text: str) -> str:
    markers = [
        ("strategic-report", "## 战略研究完整报告"),
        ("rewrite", "## 原文中英重写"),
        ("hn-analysis", "## Hacker News 热点分析"),
        ("link-summary", "## 链接总结"),
        ("text-summary", "## 文本总结"),
    ]
    for doc_type, marker in markers:
        if marker in text:
            return doc_type
    return "general-note"


def extract_request_id(text: str, path: Path) -> str:
    for pattern in [r"requestId:\s*([^\s]+)", r"request_id:\s*([^\s]+)"]:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    match = re.search(r"(\d{10,})", path.stem)
    return match.group(1) if match else path.stem


def extract_date(text: str, path: Path) -> str:
    match = re.search(r"生成时间\(UTC\):\s*(\d{4}-\d{2}-\d{2})T", text)
    if match:
        return match.group(1)

    match = re.search(r"/(\d{4}-\d{2}-\d{2})/", path.as_posix())
    if match:
        return match.group(1)
    return "unknown"


def extract_topic_pair(text: str) -> tuple[str, str]:
    match = re.search(r"主题（中文/English）：\s*(.+)", text)
    if match:
        value = match.group(1).strip()
        if value and value != "未提及":
            parts = [part.strip() for part in value.split(" / ", 1)]
            if len(parts) == 2:
                return parts[0], parts[1]
            return parts[0], ""

    match = re.search(r"主题（([^/()：]+?) / ([^)]+?)）：", text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    match = re.search(r"主题（([^）]+)）：", text)
    if match:
        return match.group(1).strip(), ""

    return "", ""


def extract_signal_summary(text: str) -> str:
    match = re.search(r"^\s*-\s*summary:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_title(text: str, doc_type: str, topic_zh: str, path: Path) -> str:
    if doc_type == "strategic-report":
        signal_summary = extract_signal_summary(text)
        if signal_summary:
            return shorten(signal_summary, 48)

    block_match = re.search(
        r"^## (?:文本总结|链接总结|原文中英重写|Hacker News 热点分析)\s*$([\s\S]+?)(?=^## |\Z)",
        text,
        re.MULTILINE,
    )
    if block_match:
        inner = block_match.group(1)
        heading_match = re.search(r"^#\s+(.+)$", inner, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

    for line in text.splitlines():
        if not line.startswith("# "):
            continue
        candidate = line[2:].strip()
        if "任务报告" not in candidate:
            return candidate

    if topic_zh:
        return topic_zh

    return path.stem


def extract_description(text: str, doc_type: str, title: str) -> str:
    match = re.search(r"一句话摘要：\s*(.+)", text)
    if match:
        return shorten(match.group(1).strip(), 140)

    if doc_type == "strategic-report":
        signal_summary = extract_signal_summary(text)
        if signal_summary:
            return shorten(signal_summary, 140)

    match = re.search(r"^\s*-\s*主结论：\s*(.+)$", text, re.MULTILINE)
    if match:
        return shorten(match.group(1).strip(), 140)

    return shorten(title, 140)


def classify_report(text: str, source_bucket: str, doc_type: str, title: str, topic_zh: str, topic_en: str) -> str:
    combined = "\n".join([text, title, topic_zh, topic_en, source_bucket, doc_type]).lower()

    if any(keyword in combined for keyword in ["原文内容未获取", "环境异常", "openrouter_api_key", "无法获取", "未发布"]):
        return "operations/fetch-failures"

    scores = Counter()
    for category, rules in CATEGORY_RULES.items():
        for keyword, weight in rules:
            if keyword.lower() in combined:
                scores[category] += weight

    if source_bucket == "strategic" or doc_type == "strategic-report":
        scores["world-strategy/strategic-research"] += 12

    if doc_type in {"rewrite", "hn-analysis"}:
        scores["operations/systems-workflows"] += 5

    if "投资" in combined or "bitcoin" in combined or "比特币" in combined:
        scores["markets-wealth/investing-strategy"] += 3

    if "家庭" in combined or "育儿" in combined or "trust" in combined:
        scores["people-life/family-growth"] += 1
        scores["people-life/relationships-trust"] += 1

    if not scores:
        if source_bucket == "strategic" or doc_type == "strategic-report":
            return "world-strategy/strategic-research"
        return "operations/review-queue"

    return max(scores.items(), key=lambda item: (item[1], -CATEGORY_ORDER.index(item[0])))[0]


def build_tags(text: str, category: str, source_bucket: str, doc_type: str) -> list[str]:
    combined = text.lower()
    tags = []

    def add(tag: str) -> None:
        if tag not in tags:
            tags.append(tag)

    section_slug, subcategory_slug = category.split("/", 1)
    add(section_slug)
    add(subcategory_slug)
    add(source_bucket)
    add(doc_type)

    for tag, keywords in TAG_RULES.items():
        if any(keyword.lower() in combined for keyword in keywords):
            add(tag)

    return tags[:8]


def compute_priority(text: str, category: str, doc_type: str) -> tuple[str, int]:
    combined = text.lower()
    score = 0

    score += {
        "strategic-report": 4,
        "text-summary": 3,
        "link-summary": 2,
        "hn-analysis": 2,
        "rewrite": 1,
        "general-note": 1,
    }.get(doc_type, 1)

    if "```json" in text:
        score += 2
    if "```mermaid" in text:
        score += 1
    if "概念清单" in text and "概念定义" in text:
        score += 1
    if "FAQ" in text:
        score += 1
    if "Machine Trace" in text:
        score += 1

    text_length = len(text)
    if text_length > 12000:
        score += 2
    elif text_length > 7000:
        score += 1

    reuse_terms = [
        "方法论",
        "framework",
        "框架",
        "系统",
        "机制",
        "策略",
        "综合报告",
        "完整报告",
        "基础设施",
        "工作流",
        "protocol",
    ]
    score += min(3, sum(1 for term in reuse_terms if term.lower() in combined))

    score += {
        "ai-software": 2,
        "markets-wealth": 2,
        "world-strategy": 2,
        "people-life": 1,
        "operations": 1,
    }.get(category.split("/", 1)[0], 1)

    if category == "operations/fetch-failures":
        score = min(score, 2)
    elif doc_type == "rewrite":
        score = min(score, 4)

    if score >= 13:
        return "high", score
    if score >= 9:
        return "medium", score
    return "low", score


def build_slug(title: str, topic_en: str, request_id: str) -> str:
    unique_key = re.search(r"\d{10,}", request_id)
    unique = unique_key.group(0) if unique_key else slugify(request_id, "report")
    base = slugify(topic_en or title, "report")
    return f"{base}-{unique}"


def normalize_body(text: str) -> str:
    body = re.sub(r"^#\s+.*任务报告\s*\n+", "", text, count=1)
    first_section = re.search(r"^##\s+", body, re.MULTILINE)
    if first_section:
        body = body[first_section.start():]

    lines = []
    inside_fence = False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            inside_fence = not inside_fence
            lines.append(line)
            continue

        if not inside_fence:
            match = re.match(r"^(#{1,6})(\s+.*)$", line)
            if match:
                level = min(6, len(match.group(1)) + 2)
                line = "#" * level + match.group(2)

        lines.append(line)

    return "\n".join(lines).strip()


def render_document(report: dict[str, object]) -> str:
    frontmatter = [
        "---",
        f'title: {json_quote(report["title"])}',
        f'description: {json_quote(report["description"])}',
        f'generatedBy: "{GENERATED_BY}"',
        f'generatedType: "{GENERATED_REPORT_TYPE}"',
        f"tags: {format_tags(report['tags'])}",
        f'category: "{report["category"]}"',
        f'priority: "{report["priority"]}"',
        f'priorityScore: {report["priority_score"]}',
        f'date: "{report["date"]}"',
        f'docType: "{report["doc_type"]}"',
        f'sourceBucket: "{report["source_bucket"]}"',
        f'source: "{report["source"]}"',
        f'requestId: "{report["request_id"]}"',
        "---",
        "",
        f'> {report["description"]}',
        "",
        "## 元信息",
        f'- 分类：`{report["category"]}`',
        f'- 优先级：`{report["priority"]}` (`{report["priority_score"]}`)',
        f'- 文档类型：`{report["doc_type"]}`',
        f'- 来源分组：`{report["source_bucket"]}`',
        f'- 原始文件：`{report["source"]}`',
        f'- 请求 ID：`{report["request_id"]}`',
        "",
        "## 原始内容",
        "",
        report["body"],
        "",
    ]
    return "\n".join(frontmatter)


def cleanup_generated_reports(expected_output_paths: set[Path]) -> None:
    if not CONTENT_DIR.exists():
        return

    for path in CONTENT_DIR.rglob("*.md"):
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter.get("generatedBy") != GENERATED_BY:
            continue
        if frontmatter.get("generatedType") != GENERATED_REPORT_TYPE:
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


def build_report(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    source_bucket = detect_source_bucket(path)
    doc_type = detect_doc_type(text)
    request_id = extract_request_id(text, path)
    date = extract_date(text, path)
    topic_zh, topic_en = extract_topic_pair(text)
    title = extract_title(text, doc_type, topic_zh, path)
    description = extract_description(text, doc_type, title)
    category = classify_report(text, source_bucket, doc_type, title, topic_zh, topic_en)
    priority, priority_score = compute_priority(text, category, doc_type)
    tags = build_tags("\n".join([text, title, topic_zh, topic_en, description]), category, source_bucket, doc_type)
    slug = build_slug(title, topic_en, request_id)
    section_slug, subcategory_slug = category.split("/", 1)

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "category": category,
        "priority": priority,
        "priority_score": priority_score,
        "date": date,
        "doc_type": doc_type,
        "source_bucket": source_bucket,
        "source": path.relative_to(REPORTS_DIR.parent).as_posix(),
        "request_id": request_id,
        "slug": slug,
        "body": normalize_body(text),
        "output_path": CONTENT_DIR / section_slug / subcategory_slug / f"{slug}.md",
    }


def main() -> None:
    reports = sorted(REPORTS_DIR.rglob("*.md"))
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    generated_reports = [build_report(report_path) for report_path in reports]
    cleanup_generated_reports({report["output_path"] for report in generated_reports})

    category_counter = Counter()
    priority_counter = Counter()

    for report in generated_reports:
        output_path = report["output_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_document(report), encoding="utf-8")

        category_counter[report["category"]] += 1
        priority_counter[report["priority"]] += 1
        print(f'Processed: {report["category"]}/{output_path.name}')

    prune_empty_directories(CONTENT_DIR)

    print("\nCategory distribution:")
    for category in CATEGORY_ORDER:
        if category_counter[category]:
            print(f"  {category}: {category_counter[category]}")

    print("\nPriority distribution:")
    for priority in ["high", "medium", "low"]:
        print(f"  {priority}: {priority_counter[priority]}")

    print(f"\nTotal processed: {len(reports)} files")


if __name__ == "__main__":
    main()
