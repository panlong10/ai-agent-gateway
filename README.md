# AI Agent Gateway

AI Agent 业务系统调用网关 - 为 AI Agent 提供统一的业务系统调用入口。

## 功能特性

| 功能 | 描述 |
|------|------|
| 路由转发 | 将请求路由到对应的业务系统 API |
| 服务注册 | 支持配置文件或 API 注册业务服务 |
| Agent 管理 | 管理 AI Agent 的注册、启用/禁用 |
| API 鉴权 | API Key 鉴权，每个 Agent 拥有独立的 Key |
| 日志审计 | 记录所有请求的日志（请求/响应、耗时、状态码） |
| 限流 | 全局限流，防止恶意请求 |

## 系统架构

```
┌──────────────────────────────────────────────────┐
│              AI Agent Gateway                     │
├──────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌────────────┐     │
│  │ 路由    │  │ 服务注册  │  │ Agent管理 │     │
│  └────┬────┘  └────┬─────┘  └────┬────┘     │
│       │            │             │           │
│  ┌────┴────────────┴─────────────┴────┐       │
│  │           核心转发引擎              │       │
│  └────────────────┬────────────────┘       │
│                   │                           │
│  ┌───────────────┴───────────────────┐        │
│  │        SQLite 数据库            │        │
│  └───────────────────────────────┘        │
└──────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python3 main.py
```

服务启动在 `http://localhost:8001`

### 3. 检查服务状态

```bash
curl http://localhost:8001/health
# 返回: {"status":"ok","version":"1.0.0"}
```

## 使用示例：创建客户

### 步骤 1：创建 Agent

```bash
curl -X POST "http://localhost:8001/admin/agents" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "销售Agent",
    "api_key": "sale_agent_token",
    "description": "负责客户管理的Agent"
  }'
```

**参数说明：**
- `name`: Agent 名称
- `api_key`: Agent 的鉴权 Key（后续调用时使用）
- `description`: 可选，描述

**返回示例：**
```json
{
  "name": "销售Agent",
  "api_key": "sale_agent_token",
  "id": "xxx",
  "enabled": true
}
```

### 步骤 2：注册业务服务

```bash
curl -X POST "http://localhost:8001/admin/services" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "创建客户服务",
    "path": "/agent/customer/create",
    "method": "POST",
    "target_url": "http://your-erp-server.com/api",
    "timeout": 30
  }'
```

**参数说明：**
- `path`: Gateway 路由路径（相对于 `/proxy`）
- `method`: HTTP 方法
- `target_url`: 业务系统地址
- `timeout`: 超时时间（秒）

### 步骤 3：通过 Gateway 调用

```bash
curl -X POST "http://localhost:8001/proxy/agent/customer/create" \
  -H "X-API-Key: sale_agent_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试客户",
    "link": "王五",
    "phone": "13700137000",
    "pay_method": 0,
    "other": "测试备注"
  }'
```

**Header 说明：**
- `X-API-Key`: Agent 的 API Key（步骤1创建的）

**返回示例：**
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "customer_id": 1,
    "customer_name": "测试客户",
    "link": "王五",
    "phone": "13700137000",
    "pay_method": 0
  }
}
```

## API 接口文档

### 管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/admin/agents` | 创建 Agent |
| GET | `/admin/agents` | 获取 Agent 列表 |
| GET | `/admin/agents/{id}` | 获取单个 Agent |
| PUT | `/admin/agents/{id}` | 更新 Agent |
| DELETE | `/admin/agents/{id}` | 删除 Agent |
| POST | `/admin/services` | 创建服务 |
| GET | `/admin/services` | 获取服务列表 |
| GET | `/admin/services/{id}` | 获取单个服务 |
| PUT | `/admin/services/{id}` | 更新服务 |
| DELETE | `/admin/services/{id}` | 删除服务 |
| GET | `/admin/logs` | 查询日志 |
| GET | `/admin/stats` | 统计信息 |

### 代理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| * | `/proxy/{path}` | 代理转发 |

### 系统接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | 根路径 |

## 配置文件

### 服务配置（YAML）

在 `configs/services.yaml` 中定义服务：

```yaml
services:
  - name: "ERP订单服务"
    path: "/erp/orders"
    method: "POST"
    target_url: "http://erp-server:3000/api"
    timeout: 30
    enabled: true
```

### 环境配置（.env）

```env
APP_NAME=AI Agent Gateway
DEBUG=false

DATABASE_URL=sqlite+aiosqlite:///./gateway.db

RATE_LIMIT_WINDOW=60
RATE_LIMIT_MAX_REQUESTS=100

ADMIN_API_KEY=admin-secret-key
```

## 默认配置

- 端口: 8001
- 管理员 Key: `admin-secret-key`
- 限流: 60秒内最多 100 次请求

## 项目结构

```
ai-agent-gateway/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py          # 配置管理
│   ├── database.py       # 数据库模型
│   ├── core/           # 核心引擎
│   ├── middleware/     # 中间件（鉴权、限流）
│   ├── routers/       # 路由
│   ├── models/        # 数据模型
│   └── schemas/       # Pydantic schemas
├── configs/
│   └── services.yaml   # 服务配置
├── requirements.txt
└── main.py
```