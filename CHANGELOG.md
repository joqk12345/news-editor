# Changelog

本文件记录仓库最近一段时间内的重要变更，优先描述用户可感知的功能、自动化和内容流水线改动，而不是逐条复述所有 commit。

## 2026-03-20

### Added

- 为普通文档页增加了 `宽栏模式` 开关，适合表格、图表、长段结构化内容的阅读；开关状态会保存在本地。
- 为 Mermaid 图增加了站点级渲染支持，不再只显示源码代码块。
- 为 Mermaid 图增加了放大、缩小、重置、最大化查看能力，便于阅读复杂结构图。
- 新增 GitHub Pages 部署 workflow，推送到 `main` 后可自动发布站点。

### Changed

- 知识图谱页改成更宽的画布布局，图谱 SVG 尺寸和节点横向间距都做了放大。
- 图谱页关闭了不必要的右侧辅助栏，优先把可视空间让给图谱本体。
- 将 Mermaid 相关经验和后续约束补充进 `AGENTS.md`，作为代理默认遵守的项目经验。

### Content Automation

- 新增并同步了最近的 `reports/news/**` 报告内容。
- 多次执行 `auto organize content`，重新生成 `content/`、时间轴、知识图谱和分类页，保持站点内容与 `reports/` 同步。

## 2026-03-19

### Added

- 建立了从 `reports/` 到 `content/` 的知识库生成流水线。
- 自动整理流程支持：
  - 分类
  - 打标签
  - 评估优先级
  - 生成知识文档
  - 生成首页、分类、优先级、时间轴、知识图谱页面
- 新增 `README.md`，说明项目定位、命令和基本使用方式。
- 新增 `AGENTS.md`，记录项目事实、工作偏好、流程约定和已踩过的坑。

### Changed

- 首页重做为知识入口页，不再是简单链接堆叠；补充了 hero、统计、入口卡片、主题域和精选区。
- 首页主标题与副标题字号做了连续收敛，整体视觉更克制。
- 知识图谱和时间轴从导航占位变成真实可浏览入口。

### Pipeline Improvements

- 分类零命中时不再静默塞进默认分类，改为进入 `operations/review-queue`。
- 生成流程不再先清空整个 `content/`，只清理带生成标记且失效的输出，避免误删手工内容。
- 增加 `scripts/validate-content.py`，对 frontmatter、分类、标签、索引完整性和 stale generated index 做校验。
- 调整 GitHub Actions 触发条件，使脚本和 workflow 变更也会触发内容整理。
- 修正定时整理任务的执行时间语义，按北京时间凌晨运行。
- 增加 `.gitignore` 规则，避免 Python `__pycache__` 被误提交。

### Maintenance

- 持续同步新增报告并自动回填到知识库目录结构中。
