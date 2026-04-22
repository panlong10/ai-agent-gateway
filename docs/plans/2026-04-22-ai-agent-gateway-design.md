# AI Agent Gateway 设计方案

## 1. 系统概述

- **项目名称**: AI Agent Gateway
- **核心功能**: 为 AI Agent 提供统一的业务系统调用入口
- **使用场景**: 内部业务系统调用（AI Agent 调用企业内部 ERP、CRM 等系统）
- **技术栈**: Python 3.10+ / FastAPI / Pydantic / SQLite/PostgreSQL

## 2. 核心功能

| 功能 | 描述 |
|------|------|
| 路由 | 将请求路由到对应的后端业务系统 API |
| 服务注册 | 用配置文件（YAML）或代码（装饰器）注册 API 列表 |
| Agent 管理 | 管理 AI Agent 的注册、启用/禁用、配置 |
| 鉴权 | API Key 鉴权，每个 Agent 拥有独立的 Key |
| 日志审计 | 记录所有请求的日志，包含请求/响应、耗时、状态码 |
| 限流 | 全局限流（滑动窗口算法） |

## 3. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Gateway                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐  │
│  │ Router  │  │ Service  │  │  Auth   │  │ Rate Limiter │  │
│  │ 模块    │  │ Registry │  │ 中间件  │  │   中间件     │  │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └──────┬───────┘  │
│       │            │            │               │          │
│  ┌────┴────────────┴────────────┴───────────────┴────┐   │
│  │                   Core Engine                      │   │
│  │     (请求转发、熔断、重试、日志、监控)                │   │
│  └────────────────────────┬───────────────────────────┘   │
│                           │                               │
│  ┌────────────────────────┴───────────────────────────┐   │
│  │                   Database                         │   │
│  │     (SQLite/PostgreSQL: Agents, Services, Logs)     │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 4. 数据模型

### 4.1 Agent

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| name | string | Agent 名称 |
| api_key | string | 鉴权用的 API Key |
| enabled | boolean | 是否启用 |
| description | string | 描述 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.2 Service (业务 API)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| name | string | 服务名称 |
| path | string | API 路径（如 /erp/orders） |
| method | string | HTTP 方法 |
| target_url | string | 目标服务地址 |
| timeout | int | 超时时间（秒） |
| enabled | boolean | 是否启用 |
| config | json | 额外配置 |

### 4.3 RequestLog

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 主键 |
| agent_id | UUID | 关联的 Agent |
| service_id | UUID | 关联的 Service |
| path | string | 请求路径 |
| method | string | HTTP 方法 |
| request_body | text | 请求体 |
| response_body | text | 响应体 |
| status_code | int | 响应状态码 |
| duration_ms | int | 耗时（毫秒） |
| ip_address | string | 客户端 IP |
| created_at | datetime | 请求时间 |

## 5. API 设计

### 5.1 代理转发

```
POST /proxy/{service_path}
  将请求转发到注册的业务系统

Headers:
  X-API-Key: <agent_api_key>

Request:
  透传请求体

Response:
  透传业务系统响应
```

### 5.2 Agent 管理

```
POST   /admin/agents           创建 Agent
GET    /admin/agents          获取 Agent 列表
GET    /admin/agents/{id}    获取单个 Agent
PUT    /admin/agents/{id}    更新 Agent
DELETE /admin/agents/{id}    删除 Agent
```

### 5.3 Service 注册

```
POST   /admin/services        创建 Service
GET    /admin/services        获取 Service 列表
GET    /admin/services/{id}   获取单个 Service
PUT    /admin/services/{id}   更新 Service
DELETE /admin/services/{id}   删除 Service
```

### 5.4 日志查询

```
GET /admin/logs?agent_id=&service_id=&from=&to=&page=&size=
```

### 5.5 系统状态

```
GET    /health                健康检查
GET    /stats                 统计信息
```

## 6. 核心实现

### 6.1 路由层

- 使用 FastAPI 的 APIRouter
- 支持路径参数（如 `/proxy/erp/orders/{order_id}`）
- 优先级：精确匹配 > 路径参数匹配

### 6.2 服务注册

**方式一：配置文件（YAML）**

```yaml
services:
  - name: "ERP 订单服务"
    path: "/erp/orders"
    method: "POST"
    target_url: "http://erp.internal/orders"
    timeout: 30
    enabled: true
```

**方式二：代码（装饰器）**

```python
@router.service("/erp/orders", method="POST", target="http://erp.internal/orders")
async def order_handler(request: Request):
    pass
```

### 6.3 鉴权中间件

```python
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    # 验证 API Key 是否有效
    # 返回 401 如果无效
```

### 6.4 限流中间件

- 使用滑动窗口算法
- 全局限流：所有请求共享一个计数器
- 可配置：窗口大小（默认 60 秒）、最大请求数

### 6.5 日志审计

- 请求进入时生成 trace_id
- 记录完整请求/响应体
- 支持分页查询

## 7. 项目结构

```
ai-agent-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── core/
│   │   ├── engine.py          # 核心转发引擎
│   │   └── exceptions.py      # 自定义异常
│   ├── middleware/
│   │   ├── auth.py            # 鉴权中间件
│   │   ├── ratelimit.py       # 限流中间件
│   │   └── logging.py         # 日志中间件
│   ├── routers/
│   │   ├── proxy.py           # 代理转发路由
│   │   ├── admin.py           # 管理 API
│   │   └── health.py          # 健康检查
│   ├── models/
│   │   ├── agent.py           # Agent 模型
│   │   ├── service.py        # Service 模型
│   │   └── log.py            # 日志模型
│   ├── schemas/
│   │   ├── agent.py          # Agent Pydantic schemas
│   │   ├── service.py       # Service Pydantic schemas
│   │   └── log.py           # Log Pydantic schemas
│   ├── database.py          # 数据库连接
│   └── utils/
│       └── helpers.py        # 工具函数
├── configs/
│   └── services.yaml         # 服务配置文件
├── tests/
├── docs/
├── requirements.txt
├── README.md
└── main.py                  # 入口文件
```

## 8. 依赖

```
fastapi
uvicorn
pydantic
pydantic-settings
sqlalchemy
aiosqlite
pyyaml
python-multipart
httpx
python-jose
passlib
bcrypt
```

## 9. 待确认

- [ ] 是否需要支持 JWT Token？
- [ ] 是否需要按 Agent 单独限流？
- [ ] 数据库选 SQLite 还是 PostgreSQL？
- [ ] 是否需要熔断/重试机制？