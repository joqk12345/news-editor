# AGENTS.md

本文件面向进入本仓库工作的 AI coding agents，记录项目事实、工作流程、用户偏好和已经验证过的经验。

## 1. 项目定位

这个仓库用于把 `reports/` 下的原始 Markdown 报告自动整理为一个可浏览的 VitePress 知识库。

核心输入：

- `reports/**/*.md`
- `reports/news/**/*.md`
- `reports/strategic/**/*.md`

核心输出：

- `content/**/*.md`
- `content/index.md`
- `content/taxonomy/index.md`
- `content/priority/index.md`
- `content/timeline/index.md`
- `content/graph/index.md`

站点框架：

- VitePress
- 配置在 `.vitepress/`

## 2. 当前流水线

### 报告整理

脚本：

- `scripts/organize-reports.py`

负责：

1. 扫描 `reports/`
2. 提取标题、摘要、日期、请求 ID、文档类型
3. 分类
4. 打标签
5. 评估优先级
6. 生成结构化知识文档到 `content/`

### 索引生成

脚本：

- `scripts/generate-index.py`

负责生成：

- 首页
- 分类体系
- 优先级总览
- 时间轴
- 知识图谱
- 一级分类页
- 二级分类页

### 内容校验

脚本：

- `scripts/validate-content.py`

负责校验：

- 生成报告数量是否和 `reports/` 一致
- frontmatter 是否完整
- 分类是否合法
- 必需标签是否存在
- 索引页是否完整
- 是否存在 stale generated index

## 3. 常用命令

安装依赖：

```bash
pnpm install
```

同步内容：

```bash
npm run sync:content
```

说明：

- 该命令会执行整理、生成索引、校验
- 该命令更新的是 `content/` 源文件
- 它不会自动重建 `.vitepress/dist`

本地预览：

```bash
npm run dev
```

构建站点：

```bash
npm run build
```

只执行校验：

```bash
npm run validate:content
```

## 4. 自动化

GitHub Actions:

- `.github/workflows/organize-content.yml`

自动触发条件：

- `reports/**/*.md` 发生变更
- `scripts/**/*.py` 发生变更
- `package.json` 发生变更
- workflow 自身发生变更
- 每天北京时间 `02:00`

自动执行顺序：

```bash
python3 scripts/organize-reports.py
python3 scripts/generate-index.py
python3 scripts/validate-content.py
```

## 5. 生成文件约定

### 生成报告页

生成报告页 frontmatter 包含：

- `generatedBy: "reports-pipeline"`
- `generatedType: "report"`

### 生成索引页

生成索引页 frontmatter 包含：

- `generatedBy: "reports-pipeline"`
- `generatedType: "index"`

### 清理策略

不要再直接删除整个 `content/`。

当前策略是：

- 只回收带生成标记、但不再属于当前输出集合的文件
- 未带生成标记的手工内容不应被无脑删除

## 6. 分类与待归类策略

如果分类规则没有明显命中：

- 不要静默塞进默认分类
- 应进入 `operations/review-queue`

这是显式人工复核桶，用来避免误分类伪装成“自动化成功”。

## 7. 用户偏好

本仓库用户的偏好已经比较明确，后续代理应默认遵守：

1. 偏好直接执行，不要空谈方案。
2. 回答要简洁、直接、少废话。
3. 如果是代码或站点问题，优先动手改并验证。
4. 做 review 时，要明确指出真实风险，不要只讲概览。
5. 做完修改后，尽量把验证也一并跑完。
6. 如果用户说 “acp”，理解为：
   - `git add`
   - `git commit`
   - `git push`
7. 提交前要注意不要把缓存垃圾带进仓库，尤其是：
   - `scripts/__pycache__/`

## 8. UI 与内容呈现偏好

用户已经对首页风格给出过明确反馈：

1. 首页不能太丑，不能只是默认 VitePress 模板。
2. 首页需要更像知识入口，而不是简单链接列表。
3. 首页 hero 文案字号不能过大。
4. `Reports Knowledge Base`
   和
   `把零散报告压成可导航的知识地图`
   都需要保持克制，不要做成夸张大标题。
5. 时间轴和知识图谱是重要入口，不能只是导航占位。

如果继续改首页，默认方向应该是：

- 信息层次清晰
- 视觉更精致
- 但整体克制，不浮夸

## 9. 已验证的经验

这些不是理论，而是已经在当前仓库里踩过的坑：

1. `npm run sync:content` 后如果用户说“我没看到更新”，先检查他是不是在看旧的静态站点。
   原因：
   - `sync:content` 更新的是 `content/`
   - `npm run build` 才会刷新 `.vitepress/dist`

2. 并行读取文件时，容易读到旧产物，尤其是在刚运行完生成脚本后。
   做法：
   - 如果怀疑结果不对，重新读取目标文件
   - 不要只依赖先前并行读取的缓存结果

3. Python `__pycache__` 很容易被误提交。
   做法：
   - `.gitignore` 里要有 `scripts/__pycache__`
   - 提交前看一眼 `git status --short`

4. 知识图谱逻辑不能假定一定存在可用语义标签。
   当前代码已经做了降级处理。
   后续不要再把这类“空集合直接 max()”的问题引回去。

5. review 不能只看“能不能跑”，还要看：
   - 是否支持定时扫描
   - 是否存在静默误分类
   - 是否会误删内容
   - 是否有校验护栏

## 10. 后续代理的默认工作方式

在这个仓库里工作时，推荐默认顺序：

1. 先看 `reports/`、`scripts/`、`content/`
2. 修改脚本或配置
3. 跑：

```bash
npm run sync:content
```

4. 再跑：

```bash
npm run build
```

5. 如果用户要求提交，再执行 ACP

## 11. 如果继续演进，优先级最高的方向

后续值得继续做的事情：

1. 为分类增加“低置信度进入待归类”的机制，而不是只处理零命中。
2. 为脚本增加更明确的测试集，而不只是校验产物。
3. 为知识图谱加入更稳定的主题抽样策略。
4. 进一步优化首页，但保持文字尺寸克制。
