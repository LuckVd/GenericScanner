# VulnScan Engine

**企业级分布式漏洞扫描引擎** — 支持高并发、插件化、智能指纹识别、资产管理与统计追踪。

---

## 目录

- [项目概述](#项目概述)
- [核心特性](#核心特性)
- [架构设计](#架构设计)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [核心模块](#核心模块)
- [插件开发](#插件开发)
- [API 文档](#api-文档)
- [部署指南](#部署指南)

---

## 项目概述

### 是什么？

VulnScan Engine 是一个企业级分布式漏洞扫描引擎，采用主从架构设计，通过消息队列解耦任务调度与扫描执行，支持热扩容和插件化扩展。

### 解决什么问题？

| 问题 | VulnScan Engine 解决方案 |
|------|-------------------------|
| 扫描任务管理混乱 | 任务调度中心统一管理，支持暂停/恢复/断点续扫 |
| 扫描节点扩展困难 | 分布式架构 + 消息队列，支持热扩容 |
| 漏洞用例难以复用 | 插件化设计，漏洞用例独立开发、热加载 |
| 目标服务识别不准 | 多层级指纹识别（端口→服务→Web指纹） |
| 资产管理分散 | 资产中心统一管理，支持自动打标 |
| 扫描效果难以追踪 | 统计中心实时收集执行数据，生成报表 |

### 核心理念

> **分布式、插件化、可观测** — 任务调度与扫描执行分离，插件热加载，全链路追踪。

---

## 核心特性

- **分布式部署** — 任务调度中心 + 扫描节点集群，通过 RabbitMQ 解耦
- **高并发扫描** — 基于 asyncio 协程池，动态调整并发数
- **插件化扩展** — 漏洞用例 + 工具类插件，支持热加载
- **智能指纹识别** — 多层级探测：端口扫描 → 服务识别 → Web 指纹
- **多登陆点认证** — 支持 manager/ops/ssh 等多入口认证
- **资产管理** — 自动发现、去重合并、标签管理
- **统计追踪** — 用例执行统计、漏洞发现比例、趋势分析
- **安全限流** — 令牌桶限流、熔断机制、超时控制

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      任务调度中心                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │API Gateway│ │任务管理器 │ │调度器    │ │资产中心  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │统计中心   │ │插件仓库   │ │配置中心  │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │ 消息队列 (RabbitMQ)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    扫描节点集群 (N个)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 节点管理器 (生命周期、协程池、心跳)                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 核心引擎 (指纹识别、漏洞检测、认证管理)                  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 插件加载器 (热加载用例、工具类)                         │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 安全与限流模块 (QPS控制、熔断)                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
VulnScan-Engine/
│
├── .claude/                      # Claude Code 配置
│   ├── PROJECT.md                # 项目配置文档
│   ├── commands/                 # 命令定义
│   └── skills/                   # 治理技能
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
├── docs/                         # 文档
│   ├── ROADMAP.md                # 项目路线图
│   ├── CURRENT_GOAL.md           # 当前目标
│   ├── api/                      # API 文档
│   └── git/                      # Git 历史
│
└── README.md                     # 项目说明
```

---

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install uv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置文件
cp config.example.yaml config.yaml

# 编辑配置（数据库、消息队列等）
vim config.yaml
```

### 3. 启动服务

```bash
# 启动调度中心
uv run python -m scheduler.main

# 启动扫描节点
uv run python -m scanner.main
```

### 4. 创建扫描任务

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例扫描",
    "targets": ["192.168.1.0/24"],
    "policy": "full"
  }'
```

---

## 核心模块

### 任务调度中心

| 模块 | 说明 |
|------|------|
| API Gateway | RESTful 接口，身份认证与权限控制 |
| 任务管理器 | 任务状态管理、分片、断点续扫 |
| 调度器 | 基于负载的任务分发，优先级队列 |
| 资产中心 | 资产发现、打标、查询 |
| 统计中心 | 用例执行统计、报表生成 |
| 插件仓库 | 插件存储、版本管理 |
| 配置中心 | 全局配置管理 |

### 扫描节点

| 模块 | 说明 |
|------|------|
| 节点管理器 | 生命周期、协程池、心跳上报 |
| 认证管理器 | 多登陆点认证、会话池 |
| 指纹识别引擎 | 端口扫描、服务识别、Web 指纹 |
| 漏洞检测引擎 | 用例加载、并发执行 |
| 插件加载器 | 热加载、沙箱隔离 |
| 安全与限流 | 令牌桶限流、熔断、超时控制 |

---

## 插件开发

### 漏洞用例结构

```python
# plugins/vulns/custom_001.py

__vuln_info__ = {
    "id": "CUSTOM-001",
    "name": "示例漏洞",
    "severity": "medium",
    "tags": ["login_required", "manager"],
    "fingerprint": {"path": "/manager", "method": "GET"}
}

class VulnCheck:
    def __init__(self, tools):
        self.tools = tools

    def verify(self, target, auth):
        """
        检测漏洞
        返回: {"vulnerable": bool, "proof": str}
        """
        session = auth.get_session("manager")
        # ... 检测逻辑
        return {"vulnerable": True, "proof": "..."}

    def cleanup(self, target, auth):
        """清理测试数据"""
        pass
```

### 工具类插件

```python
# plugins/tools/user_creator.py

class UserCreator:
    def __init__(self):
        self.cache = {}

    def create(self, target, auth):
        """创建低权限测试用户"""
        if target in self.cache:
            return self.cache[target]
        # ... 创建逻辑
        cred = self._do_create(target, auth)
        self.cache[target] = cred
        return cred
```

详细规范见：`docs/plugin-dev-guide.md`

---

## API 文档

### 任务 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/tasks` | 创建扫描任务 |
| GET | `/api/v1/tasks/{id}` | 查询任务状态 |
| POST | `/api/v1/tasks/{id}/pause` | 暂停任务 |
| POST | `/api/v1/tasks/{id}/resume` | 恢复任务 |
| DELETE | `/api/v1/tasks/{id}` | 删除任务 |

### 资产 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/assets` | 查询资产列表 |
| GET | `/api/v1/assets/{id}` | 查询资产详情 |
| POST | `/api/v1/assets/{id}/tags` | 更新资产标签 |

详细 API 文档见：`docs/api/API.md`

---

## 部署指南

### Docker 部署

```bash
# 构建镜像
docker build -t vulnscan-engine .

# 启动调度中心
docker run -d --name scheduler vulnscan-engine scheduler

# 启动扫描节点
docker run -d --name scanner-1 vulnscan-engine scanner
```

### 依赖服务

| 服务 | 用途 | 版本 |
|------|------|------|
| MySQL | 数据存储 | 8.0+ |
| RabbitMQ | 消息队列 | 3.12+ |
| Redis | 缓存 | 7.0+ |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| 异步框架 | asyncio |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy |
| 消息队列 | RabbitMQ |
| 数据库 | MySQL |
| 缓存 | Redis |

---

## License

MIT License
