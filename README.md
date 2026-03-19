# Reports Knowledge Base

将 `reports/` 下的原始任务报告自动整理为一个可浏览的 VitePress 知识库。

## 项目作用

这个仓库的输入是真实报告文件，主要位于：

- `reports/**/*.md`
- `reports/news/**/*.md`
- `reports/strategic/**/*.md`

脚本会自动完成以下流程：

1. 扫描 `reports/` 下的 Markdown 文件
2. 提取标题、摘要、日期、请求 ID、文档类型等元数据
3. 基于规则完成分类、打标签、优先级评估
4. 生成 `content/` 下的知识库文档
5. 生成首页、分类页、优先级页、时间线、知识图谱等索引页
6. 用 VitePress 构建静态站点

## 目录说明

- `reports/`: 原始输入，知识库的事实来源
- `content/`: 生成后的知识库内容
- `scripts/organize-reports.py`: 把报告转成结构化知识文档
- `scripts/generate-index.py`: 生成首页、分类页、时间线、知识图谱等索引
- `scripts/validate-content.py`: 校验生成结果是否完整、合法
- `.vitepress/`: 站点配置与主题样式
- `.github/workflows/organize-content.yml`: 自动整理与定时任务

## 本地使用

安装依赖：

```bash
pnpm install
```

同步知识库内容：

```bash
npm run sync:content
```

本地预览：

```bash
npm run dev
```

构建静态站点：

```bash
npm run build
```

只运行校验：

```bash
npm run validate:content
```

## 自动化流程

GitHub Actions 会在以下场景自动执行整理流程：

- `reports/**/*.md` 发生变更
- `scripts/**/*.py` 发生变更
- workflow 自身变更
- 每天北京时间 `02:00` 定时执行一次

自动化流程会依次执行：

```bash
python3 scripts/organize-reports.py
python3 scripts/generate-index.py
python3 scripts/validate-content.py
```

## 生成约定

- `reports/` 是输入源
- `content/` 里的大多数页面由脚本自动生成
- 生成页面会带有 `generatedBy: "reports-pipeline"` 标记
- 已生成页面会被脚本更新或回收
- 未带生成标记的手工文件不会被整库清空
- 规则未命中的内容会进入 `operations/review-queue`

## 当前知识入口

站点当前提供这些核心入口：

- 首页
- 分类体系
- 时间轴
- 知识图谱
- 优先级总览
- 五大主题域与二级分类页

## 维护建议

- 优先修改 `reports/`，不要手工改生成后的报告页
- 如果新增分类体系，记得同时更新 `scripts/kb_common.py`
- 如果调整分类或标签规则，执行一次 `npm run sync:content`
- 提交前最好至少运行一次 `npm run validate:content`
