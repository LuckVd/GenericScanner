# API Documentation

> VulnScan Engine API 契约文档

---

## 生命周期状态

| 状态 | 说明 | Breaking Change |
|------|------|-----------------|
| `experimental` | 实验阶段 | 允许 |
| `stable` | 稳定阶段 | 禁止（需版本升级） |
| `deprecated` | 废弃阶段 | 仅允许删除 |

---

## 接口必备字段

| 字段 | 必须 | 说明 |
|------|------|------|
| Endpoint | 是 | 例如 `GET /api/v1/tasks/{id}` |
| Method | 是 | HTTP 方法 |
| Summary | 是 | 简要说明 |
| Status | 是 | 生命周期状态 |
| Auth | 建议 | required / optional / none |

---

## Breaking Change 判定

对于 `stable` 状态的 API，以下视为 Breaking Change：

- 删除字段
- 修改字段类型
- 修改 required 属性
- 修改响应结构导致不兼容

**允许的操作：**
- 新增可选字段
- 新增不冲突的新接口

---

## API 列表

### 任务管理 API

---

### POST /api/v1/tasks

- **Summary**: 创建扫描任务
- **Status**: experimental
- **Auth**: required

**Request Body:**
```json
{
  "name": "string",
  "targets": ["192.168.1.0/24", "example.com"],
  "auth": {
    "manager": {"username": "string", "password": "string"},
    "ops": {"username": "string", "password": "string"},
    "ssh": {"username": "string", "password": "string", "port": 22}
  },
  "policy": "full|redline|smart|specified",
  "vuln_ids": ["CVE-2023-1234"],
  "priority": 5,
  "options": {
    "concurrency": 50,
    "rate_limit": 100,
    "timeout": 30,
    "break_on_high": false
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "status": "pending",
  "created_at": "timestamp"
}
```

---

### GET /api/v1/tasks

- **Summary**: 获取任务列表
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required | description |
|------|-----|------|----------|-------------|
| status | query | string | false | 过滤状态 |
| page | query | int | false | 页码 |
| size | query | int | false | 每页数量 |

**Response:**
```json
{
  "total": 100,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "status": "pending|running|paused|completed|failed",
      "progress": {"total": 100, "completed": 45},
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
}
```

---

### GET /api/v1/tasks/{id}

- **Summary**: 获取任务详情
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |

**Response:**
```json
{
  "id": "uuid",
  "name": "示例任务",
  "targets": ["192.168.1.1/24"],
  "auth": {
    "manager": {"username": "admin", "password": "***"}
  },
  "policy": "full",
  "status": "running",
  "progress": {"total": 100, "completed": 45},
  "options": {
    "concurrency": 50,
    "rate_limit": 100,
    "timeout": 30
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

### POST /api/v1/tasks/{id}/pause

- **Summary**: 暂停任务
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |

**Response:**
```json
{
  "id": "uuid",
  "status": "paused",
  "message": "Task paused successfully"
}
```

---

### POST /api/v1/tasks/{id}/resume

- **Summary**: 恢复任务
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |

**Response:**
```json
{
  "id": "uuid",
  "status": "running",
  "message": "Task resumed successfully"
}
```

---

### DELETE /api/v1/tasks/{id}

- **Summary**: 删除任务
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |

**Response:**
```json
{
  "message": "Task deleted successfully"
}
```

---

### GET /api/v1/tasks/{id}/results

- **Summary**: 获取任务扫描结果
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |
| severity | query | string | false | 过滤严重级别 |

**Response:**
```json
{
  "task_id": "uuid",
  "total_vulns": 10,
  "by_severity": {
    "critical": 2,
    "high": 3,
    "medium": 4,
    "low": 1
  },
  "results": [
    {
      "vuln_id": "CVE-2023-1234",
      "target": "192.168.1.10",
      "severity": "high",
      "vulnerable": true,
      "details": {...},
      "discovered_at": "timestamp"
    }
  ]
}
```

---

## 资产管理 API

---

### GET /api/v1/assets

- **Summary**: 获取资产列表
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required | description |
|------|-----|------|----------|-------------|
| tags | query | string | false | 按标签过滤 |
| service | query | string | false | 按服务过滤 |
| page | query | int | false | 页码 |
| size | query | int | false | 每页数量 |

**Response:**
```json
{
  "total": 500,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "uuid",
      "ip": "192.168.1.10",
      "domain": "internal.example.com",
      "ports": [80, 443, 22],
      "tags": ["internal", "manager"],
      "last_scan": "timestamp"
    }
  ]
}
```

---

### GET /api/v1/assets/{id}

- **Summary**: 获取资产详情
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |

**Response:**
```json
{
  "id": "uuid",
  "ip": "192.168.1.10",
  "domain": "internal.example.com",
  "ports": [80, 443, 22],
  "services": [
    {"port": 80, "name": "http", "banner": "nginx/1.18.0"},
    {"port": 443, "name": "https", "ssl": true}
  ],
  "fingerprints": [
    {"type": "web", "name": "nginx", "version": "1.18.0", "tags": ["webserver"]}
  ],
  "tags": ["internal", "manager", "linux"],
  "discovered_by": "task_id",
  "last_scan": "timestamp"
}
```

---

### POST /api/v1/assets/{id}/tags

- **Summary**: 更新资产标签
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required |
|------|-----|------|----------|
| id | path | string | true |

**Request Body:**
```json
{
  "add": ["tag1", "tag2"],
  "remove": ["tag3"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "tags": ["internal", "manager", "tag1", "tag2"]
}
```

---

## 统计 API

---

### GET /api/v1/stats/overview

- **Summary**: 获取统计概览
- **Status**: experimental
- **Auth**: required

**Response:**
```json
{
  "total_tasks": 100,
  "total_assets": 500,
  "total_vulns": 50,
  "by_severity": {
    "critical": 5,
    "high": 15,
    "medium": 20,
    "low": 10
  }
}
```

---

### GET /api/v1/stats/vulns

- **Summary**: 获取漏洞统计
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required | description |
|------|-----|------|----------|-------------|
| start_date | query | string | false | 开始日期 |
| end_date | query | string | false | 结束日期 |
| vuln_id | query | string | false | 漏洞ID |

**Response:**
```json
{
  "vuln_id": "CVE-2023-1234",
  "total_executions": 1000,
  "success_rate": 0.95,
  "vuln_found_rate": 0.1,
  "avg_duration": 123
}
```

---

## 节点管理 API

---

### GET /api/v1/nodes

- **Summary**: 获取扫描节点列表
- **Status**: experimental
- **Auth**: required

**Response:**
```json
{
  "nodes": [
    {
      "id": "node-001",
      "status": "online",
      "load": {"cpu": 0.5, "memory": 0.6},
      "tasks_running": 10,
      "last_heartbeat": "timestamp"
    }
  ]
}
```

---

## 插件管理 API

---

### GET /api/v1/plugins

- **Summary**: 获取插件列表
- **Status**: experimental
- **Auth**: required

**Parameters:**
| name | in | type | required | description |
|------|-----|------|----------|-------------|
| type | query | string | false | vuln / tool |

**Response:**
```json
{
  "plugins": [
    {
      "id": "CVE-2023-1234",
      "name": "Nginx越权读取",
      "severity": "high",
      "tags": ["nginx", "auth_bypass"],
      "enabled": true,
      "md5": "hash"
    }
  ]
}
```

---

### POST /api/v1/plugins/reload

- **Summary**: 重新加载插件
- **Status**: experimental
- **Auth**: required

**Response:**
```json
{
  "message": "Plugins reloaded successfully",
  "count": 50
}
```

---

## 错误响应格式

所有 API 在发生错误时返回统一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

**常见错误码：**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| TASK_NOT_FOUND | 404 | 任务不存在 |
| ASSET_NOT_FOUND | 404 | 资产不存在 |
| INVALID_PARAMETER | 400 | 参数无效 |
| UNAUTHORIZED | 401 | 未授权 |
| FORBIDDEN | 403 | 禁止访问 |
| INTERNAL_ERROR | 500 | 内部错误 |
