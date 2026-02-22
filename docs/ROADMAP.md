# 项目路线图

> 项目整体规划 — 供 AI 把控开发节奏

---

## 项目概览

| 字段 | 值 |
|------|-----|
| **名称** | 漏洞扫描引擎 (VulnScan Engine) |
| **类型** | backend |
| **描述** | 企业级分布式漏洞扫描引擎，支持高并发、插件化、智能指纹识别、资产管理与统计追踪 |
| **技术栈** | Python + asyncio + RabbitMQ + MySQL + Redis |

---

## 目录结构

```
VulnScan-Engine/
│
├── scheduler/                    # 任务调度中心
│   ├── api_gateway/              # API Gateway
│   ├── task_manager/             # 任务管理器
│   ├── dispatcher/               # 调度器
│   ├── asset_center/             # 资产中心
│   ├── stats_center/             # 统计中心
│   ├── plugin_repo/              # 插件仓库
│   └── config_center/            # 配置中心
│
├── scanner/                      # 扫描节点
│   ├── node_manager/             # 节点管理器
│   ├── core_engine/              # 核心引擎
│   │   ├── auth_manager/         # 认证管理器
│   │   ├── fingerprint/          # 指纹识别引擎
│   │   └── vuln_detector/        # 漏洞检测引擎
│   ├── plugin_loader/            # 插件加载器
│   └── security/                 # 安全与限流模块
│
├── plugins/                      # 插件目录
│   ├── vulns/                    # 漏洞用例插件
│   └── tools/                    # 工具类插件
│
├── common/                       # 公共模块
│   ├── models/                   # 数据模型
│   ├── utils/                    # 工具函数
│   └── constants/                # 常量定义
│
├── tests/                        # 测试
│
└── docs/                         # 文档
```

---

## 模块规划

| 模块 | 路径 | 负责人 | 优先级 |
|------|------|--------|--------|
| API Gateway | `scheduler/api_gateway/**` | - | P0 |
| 任务管理器 | `scheduler/task_manager/**` | - | P0 |
| 调度器 | `scheduler/dispatcher/**` | - | P0 |
| 资产中心 | `scheduler/asset_center/**` | - | P1 |
| 统计中心 | `scheduler/stats_center/**` | - | P1 |
| 插件仓库 | `scheduler/plugin_repo/**` | - | P1 |
| 配置中心 | `scheduler/config_center/**` | - | P1 |
| 节点管理器 | `scanner/node_manager/**` | - | P0 |
| 认证管理器 | `scanner/core_engine/auth_manager/**` | - | P0 |
| 指纹识别引擎 | `scanner/core_engine/fingerprint/**` | - | P0 |
| 漏洞检测引擎 | `scanner/core_engine/vuln_detector/**` | - | P0 |
| 插件加载器 | `scanner/plugin_loader/**` | - | P1 |
| 安全与限流模块 | `scanner/security/**` | - | P1 |
| 数据模型 | `common/models/**` | - | P0 |
| 工具函数 | `common/utils/**` | - | P2 |

---

## 开发阶段

| 阶段 | 目标 | 状态 | 预计完成 |
|------|------|------|----------|
| Phase 1 | 基础架构搭建 - API Gateway、任务管理器、消息队列集成 | done | 2026-02-22 |
| Phase 2 | 扫描节点核心 - 节点管理器、协程池、心跳机制 | todo | - |
| Phase 3 | 核心引擎开发 - 认证管理、指纹识别、漏洞检测 | todo | - |
| Phase 4 | 资产与统计中心 - 资产管理、打标、统计上报 | todo | - |
| Phase 5 | 插件体系 - 插件加载器、沙箱隔离、工具类管理 | todo | - |
| Phase 6 | 安全与稳定性 - 限流、熔断、超时控制、审计日志 | todo | - |
| Phase 7 | 可观测性 - Prometheus 指标、日志收集、追踪 ID | todo | - |
| Phase 8 | 测试与优化 - 单元测试、集成测试、性能优化 | todo | - |

---

## 里程碑

| 里程碑 | 交付物 | 状态 | 日期 |
|--------|--------|------|------|
| v0.1 | 基础框架 - 调度中心 + 单节点扫描能力 | todo | - |
| v0.3 | 核心功能 - 指纹识别 + 漏洞检测 + 认证管理 | todo | - |
| v0.5 | 完整功能 - 资产中心 + 统计中心 + 插件体系 | todo | - |
| v0.8 | 稳定性 - 安全限流 + 熔断 + 审计日志 | todo | - |
| v1.0 | 正式发布 - 完整测试 + 文档 + 部署指南 | todo | - |

---

## 当前焦点

> 与 `docs/CURRENT_GOAL.md` 保持同步

| 字段 | 值 |
|------|-----|
| **阶段** | Phase 2 - 扫描节点核心 |
| **目标** | 实现扫描节点管理器、协程池、心跳机制 |
| **重点模块** | `scanner/node_manager/**`, `scanner/core_engine/**` |

---

## 风险与依赖

| 类型 | 描述 | 影响 | 状态 |
|------|------|------|------|
| 依赖 | RabbitMQ 消息队列环境 | 高 | 待准备 |
| 依赖 | MySQL 数据库环境 | 高 | 待准备 |
| 依赖 | Redis 缓存环境 | 中 | 待准备 |
| 风险 | 高并发下协程池资源耗尽 | 高 | 待解决 |
| 风险 | 插件沙箱安全性保障 | 高 | 待解决 |
| 风险 | 扫描目标被扫崩 | 中 | 待解决 |
| 风险 | 凭证安全存储与传输 | 高 | 待解决 |

---

## 核心设计要点

### 架构模式
- 主从分布式架构
- 消息队列解耦（RabbitMQ）
- 热扩容支持

### 核心能力
- **分布式部署**: 任务调度中心 + 扫描节点集群
- **高并发**: 协程池（asyncio/gevent）
- **插件化**: 漏洞用例 + 工具类插件
- **智能指纹识别**: 多层级探测（端口→服务→Web指纹）
- **资产管理**: 自动打标、去重合并
- **统计追踪**: 用例执行统计、趋势分析

### 安全机制
- 请求限流（令牌桶算法）
- 熔断机制
- 超时控制
- 沙箱隔离
- 凭证加密（AES + TLS）

---

## 备注

1. 本项目为企业内部安全评估平台的核心扫描引擎
2. 支持多登陆点认证（manager/ops/ssh）
3. 插件开发需遵循规范（见 `docs/plugin-dev-guide.md`）
4. 所有 API 需遵循 `docs/api/API.md` 中定义的契约
