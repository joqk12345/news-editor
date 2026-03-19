#!/usr/bin/env python3
"""Common utilities for generating the VitePress knowledge base."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
REPORTS_DIR = PROJECT_DIR / "reports"
CONTENT_DIR = PROJECT_DIR / "content"
GENERATED_BY = "reports-pipeline"

TAXONOMY = [
    {
        "slug": "ai-software",
        "title": "AI 与软件",
        "description": "聚焦 AI 代理、模型系统、研究方法与软件工具链。",
        "children": [
            {
                "slug": "agents-tooling",
                "title": "代理与工具",
                "description": "AI 代理、编码助手、开发工作流与工具使用经验。",
            },
            {
                "slug": "models-research",
                "title": "模型与研究",
                "description": "模型发布、推理基础设施、研究范式与科研方法。",
            },
        ],
    },
    {
        "slug": "markets-wealth",
        "title": "市场与财富",
        "description": "聚焦投资判断、资产配置、财富观念与行为偏差。",
        "children": [
            {
                "slug": "investing-strategy",
                "title": "投资策略",
                "description": "投资方法、市场分析、资本配置与可执行策略。",
            },
            {
                "slug": "wealth-psychology",
                "title": "财富心理",
                "description": "财富感知、消费偏差、风险偏好与借贷决策。",
            },
        ],
    },
    {
        "slug": "people-life",
        "title": "人与生活",
        "description": "聚焦关系、家庭、成长、教育与自我管理。",
        "children": [
            {
                "slug": "relationships-trust",
                "title": "关系与信任",
                "description": "人际关系、信任修复、合作边界与相处方法。",
            },
            {
                "slug": "family-growth",
                "title": "家庭与成长",
                "description": "育儿、生育、成长转变、教育心态与家庭经验。",
            },
        ],
    },
    {
        "slug": "world-strategy",
        "title": "世界与战略",
        "description": "聚焦战略研究、政策冲击、地缘事件与文化历史素材。",
        "children": [
            {
                "slug": "strategic-research",
                "title": "战略研究",
                "description": "情景推演、政策风险、市场结构与地缘分析。",
            },
            {
                "slug": "culture-history",
                "title": "文化与历史",
                "description": "文化事件、历史语境与跨领域观察。",
            },
        ],
    },
    {
        "slug": "operations",
        "title": "流程与系统",
        "description": "聚焦流程产物、系统框架、工作流设计与抓取异常。",
        "children": [
            {
                "slug": "systems-workflows",
                "title": "系统与工作流",
                "description": "框架设计、产品机制、流程重写与系统化实践。",
            },
            {
                "slug": "fetch-failures",
                "title": "抓取异常",
                "description": "原文缺失、环境异常、配置失败等低价值产物。",
            },
            {
                "slug": "review-queue",
                "title": "待归类",
                "description": "规则未命中或需要人工复核的内容，避免静默误分类。",
            },
        ],
    },
]

SECTION_META = {section["slug"]: section for section in TAXONOMY}
SUBCATEGORY_META = {
    f'{section["slug"]}/{child["slug"]}': {
        "section_slug": section["slug"],
        "section_title": section["title"],
        "section_description": section["description"],
        "slug": child["slug"],
        "title": child["title"],
        "description": child["description"],
    }
    for section in TAXONOMY
    for child in section["children"]
}


def slugify(value: str, fallback: str = "report") -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or fallback


def json_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def format_tags(tags: list[str]) -> str:
    return "[" + ", ".join(tags) + "]"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}

    frontmatter = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def shorten(text: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def escape_cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ").strip()


def content_link(path: Path) -> str:
    relative = path.relative_to(CONTENT_DIR)
    if path.name == "index.md":
        if relative.parent == Path("."):
            return "/"
        return "/" + relative.parent.as_posix() + "/"
    return "/" + relative.with_suffix("").as_posix()
