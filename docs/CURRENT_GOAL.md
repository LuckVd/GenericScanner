# 当前目标

> 单一焦点：本次会话关注的核心任务

---

## 目标信息

| 字段 | 值 |
|------|-----|
| **任务** | 搭建任务调度中心基础框架 |
| **状态** | in_progress |
| **优先级** | high |
| **创建日期** | 2026-02-22 |

---

## 完成标准

- [ ] API Gateway 基础框架可运行
- [ ] 任务管理器实现任务 CRUD
- [ ] 任务持久化到 MySQL
- [ ] 与 RabbitMQ 消息队列集成
- [ ] 基础单元测试通过

---

## 关联模块

- `scheduler/api_gateway/**`
- `scheduler/task_manager/**`
- `scheduler/dispatcher/**`
- `common/models/**`

---

## 进度记录

| 时间 | 进展 |
|------|------|
| 2026-02-22 | 目标已创建，准备开始 Phase 1 开发 |
| 2026-02-22 | docs: 初始化项目配置文档（ROADMAP/API/README） |

---

## 技术要点

### API Gateway
- RESTful 接口设计
- 身份认证与权限控制
- 请求路由与负载均衡

### 任务管理器
- 任务状态机（pending → running → paused → completed → failed）
- 任务分片（按 IP 段拆分）
- 断点续扫能力

### 调度器
- 基于节点负载动态分配
- 优先级队列支持
- RabbitMQ 路由键分发

---

## 相关文档

- 详细设计文档：`docs/design/vulnscan-engine-design.md`
- API 契约：`docs/api/API.md`
