# /commit Command

Git 提交流程与 Skills 集成和自动更新状态文件

---

## 执行流程

### 1. Pre-commit 检查

按优先级检测并执行 lint：

- package.json 存在时执行 npm run lint 或 pnpm lint 或 yarn lint
- Makefile 存在时执行 make lint
- Python + uv 项目执行 uv run ruff check . 或 uv run flake8
- Python 项目执行 ruff check . 或 flake8

Python 环境优先级：
- 存在 uv.lock 或 .venv 时，优先使用 uv run 执行命令

Lint 失败则停止流程并输出错误

### 2. 清理临时文件

在提交前检测并删除临时文件：

需要删除的文件类型：
- 缓存文件: **/__pycache__/, **/*.pyc, .pytest_cache/
- 构建产物: **/dist/, **/build/, **/*.egg-info/
- 临时报告: **/coverage-report/, **/.coverage, **/htmlcov/
- 日志文件: **/*.log, **/logs/*.log
- 临时文件: **/*.tmp, **/*.temp, **/*.swp
- IDE 文件: **/.idea/, **/.vscode/ (可选保留)

执行步骤：
1. 扫描项目目录识别临时文件
2. 输出待删除列表供确认
3. 用户确认后删除
4. 从 Git 跟踪中移除

注意：
- 不要删除 .gitignore 中未忽略但项目需要的文件
- 保留 .env.example 等示例文件
- 保留测试数据文件如 tests/fixtures/

### 3. 调用 workspace-governor Skill

读取 .claude/PROJECT.md 执行文件保护检查

模块 Level 对应动作：
- core: 输出 Core Protection Warning 拒绝自动提交
- stable: 输出 Stability Modification Proposal 等待确认
- active: 允许继续

### 4. 调用 api-governor Skill

若变更涉及 API 相关文件执行 Breaking Change 检测

API 相关路径:
- docs/api/**
- **/routes/**
- **/api/**
- **/controllers/**
- **/endpoints/**

检测结果对应动作：
- Breaking Change: 输出 API Change Proposal 等待确认
- Non-Breaking: 允许继续并提示更新文档

### 5. 调用 goal-tracker Skill

检查当前目标进度询问用户目标是否完成

目标状态对应动作：
- in_progress: 输出目标完成询问
- completed: 提示设置新目标
- blocked: 输出阻塞原因

用户确认后：
- 完成：更新 docs/CURRENT_GOAL.md 状态为 completed 然后询问下一个目标
- 未完成：追加进度记录到 PROJECT.md 然后继续提交流程

### 6. Stage

执行 git add 添加变更文件

### 7. 生成 Commit Message

分析 git diff --cached 按 Conventional Commits 生成消息

格式：type(scope): description

Type 列表：
- feat: 新功能
- fix: Bug 修复
- refactor: 重构
- perf: 性能优化
- docs: 文档
- style: 代码风格
- test: 测试
- build: 构建
- ci: CI/CD
- chore: 杂项
- deps: 依赖
- config: 配置

Breaking Change 标记：在 type 后加感叹号或在 footer 添加 BREAKING CHANGE

Commit Message 内容要求：

body 部分必须包含从上次 commit 到本次的所有变更内容：

变更内容格式：
- 新增：列出新增的功能/文件
- 修改：列出修改的内容
- 删除：列出删除的内容
- 修复：列出修复的问题

生成步骤：
1. 执行 git log -1 --pretty=%B HEAD 获取上次 commit message
2. 执行 git diff HEAD~1..HEAD --stat 获取变更统计
3. 执行 git diff HEAD~1..HEAD 分析具体变更内容
4. 汇总所有变更生成完整的 commit message body

### 8. 执行 Commit

执行 git commit

### 9. 自动更新状态文件

提交成功后更新以下文件：

1. PROJECT.md：追加开发历史记录
2. CURRENT_GOAL.md：更新进度记录
3. ROADMAP.md：同步当前焦点

检测模块状态升级：
- 检查每个 dev 状态的模块
- 获取最近 3 次 commit 的变更文件列表
- 若模块路径无变动则输出升级建议

### 10. 更新 Git 历史记录

更新 docs/git/history.md 追加简洁摘要

创建详细日志文件于 docs/git/logs/

### 11. Push（可选）

检测远程仓库：
- 执行 git remote -v 检查是否配置了远程仓库
- 无远程仓库或无 push 权限时跳过 push 并输出提示

---

## 输出格式

Commit Successful 输出：
- Commit ID
- Commit Message
- Skills 执行结果
- 更新的文件列表
- 升级建议
- Push 状态

---

## 禁止行为

- Lint 失败仍提交
- 跳过清理临时文件步骤
- 跳过保护检查
- 跳过 API 变更检测
- 跳过目标进度检查
- 自动升级模块 Level
- 覆盖历史记录
- 忽略 Skills 输出
- 未经确认修改目标状态
- 提交不完整的 commit message
- 提交临时文件
