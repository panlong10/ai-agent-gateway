# AI Agent Gateway

AI Agent 业务系统调用网关 - 为 AI Agent 提供统一的业务系统调用入口。opencode 开发。

## 功能特性

| 功能 | 描述 |
|------|------|
| 路由转发 | 将请求路由到对应的业务系统 API |
| 服务注册 | 支持配置文件或 API 注册业务服务 |
| Agent 管理 | 管理 AI Agent 的注册、启用/禁用 |
| API 鉴权 | API Key 鉴权，每个 Agent 拥有独立的 Key |
| 日志审计 | 记录所有请求的日志（请求/响应、耗时、状态码） |
| 限流 | 全局限流，防止恶意请求 |
| **自然语言 API** | **LLM 驱动的自然语言意图解析** |
| **多提供商 LLM** | **支持 OpenAI/Anthropic/OpenRouter** |
| **意图注册** | **自然语言意图到 API 的映射** |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Gateway                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐ │
│  │ 路由    │  │ 服务注册 │  │ 意图注册 │  │ LLM配置  │ │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └────┬────┘ │
│       │            │            │            │            │       │
│  ┌────┴────────────┴────────────┴─────────────┴────┐  │
│  │              核心转发引擎                    │  │
│  │     (请求转发、意图解析、日志、监控)             │  │
│  └────────────────────────┬───────────────────────┘  │
│                          │                           │
│  ┌──────────────────────┴───────────────────────┐  │
│  │               SQLite 数据库                   │  │
│  │  (Agents, Services, Logs, Intents, LLMConfigs) │  │
│  └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
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

## 使用示例：自然语言调用 ERP

### 完整示例：创建客户

```bash
# 1. 创建 Agent（使用 sale_agent_token 作为标识）
curl -X POST "http://localhost:8001/admin/agents" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "销售Agent", "api_key": "sale_agent_token", "description": "负责客户管理"}'

# 2. 注册业务服务（ERP API）
curl -X POST "http://localhost:8001/admin/services" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "客户管理服务",
    "path": "/agent/customer/create",
    "method": "POST",
    "target_url": "http://local.unimeserp.com/api",
    "timeout": 30
  }'

# 3. 配置 LLM（OpenRouter 免费模型）
curl -X POST "http://localhost:8001/admin/llm-configs" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenRouter",
    "provider": "openai",
    "api_key": "sk-or-v1-xxx",
    "model": "tencent/hy3-preview:free",
    "base_url": "https://openrouter.ai"
  }'

# 4. 注册意图（将"创建客户"映射到服务）
curl -X POST "http://localhost:8001/admin/intents" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "create_customer",
    "description": "创建客户",
    "pattern": "创建客户",
    "service_id": "服务ID（上面返回的）"
  }'

# 5. 自然语言调用（创建客户）
curl -X POST "http://localhost:8001/nlp/agent" \
  -H "X-API-Key: sale_agent_token" \
  -H "Content-Type: application/json" \
  -d '{"query": "创建一个客户名为测试客户bynlp"}'

# 返回: {"code":201,"message":"创建成功","data":{"customer_id":16,...}}
```

### 单独使用 NLP Parse

```bash
# 解析意图（不调用后端）
curl -X POST "http://localhost:8001/nlp/parse" \
  -H "X-API-Key: admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "创建一个客户名为张三的客户"}'

# 返回: {"intent_name":"create_customer","params":{"客户名":"张三"}}
```

### 传统代理调用

```bash
curl -X POST "http://localhost:8001/proxy/agent/customer/create" \
  -H "X-API-Key: sale_agent_token" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试客户", "link": "王五", "phone": "13700137000", "pay_method": 0}'
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
| POST | `/admin/intents` | 创建意图 |
| GET | `/admin/intents` | 获取意图列表 |
| GET | `/admin/intents/{id}` | 获取单个意图 |
| PUT | `/admin/intents/{id}` | 更新意图 |
| DELETE | `/admin/intents/{id}` | 删除意图 |
| POST | `/admin/llm-configs` | 创建 LLM 配置 |
| GET | `/admin/llm-configs` | 获取 LLM 配置列表 |
| GET | `/admin/llm-configs/{id}` | 获取单个 LLM 配置 |
| PUT | `/admin/llm-configs/{id}` | 更新 LLM 配置 |
| DELETE | `/admin/llm-configs/{id}` | 删除 LLM 配置 |
| GET | `/admin/logs` | 查询日志 |
| GET | `/admin/stats` | 统计信息 |

### 代理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| * | `/proxy/{path}` | 代理转发 |
| POST | `/nlp/agent` | 自然语言调用 |
| POST | `/nlp/parse` | 解析意图 |

### 系统接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | 根路径 |

## 配置文件

### 服务配置（YAML）

在 `configs/services.yaml` ��定义服务：

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
│   ├── config.py           # 配置管理
│   ├── database.py        # 数据库模型
│   ├── core/
│   │   └── engine.py    # 核心转发引擎
│   ├── middleware/
│   │   ├── auth.py      # 鉴权中间件
│   │   ├── ratelimit.py # 限流中间件
│   │   └── logging.py   # 日志中间件
│   ├── routers/
│   │   ├── proxy.py    # 代理转发路由
│   │   ├── nlp.py     # 自然语言路由
│   │   ├── admin.py    # 管理 API
│   │   └── health.py  # 健康检查
│   ├── models/        # 数据模型
│   ├── schemas/      # Pydantic schemas
│   └── services/     # LLM 服务
├── configs/
│   └── services.yaml  # 服务配置
├── requirements.txt
└── main.py          # 入口文件
```

## 差异化价值

| 传统 API Gateway | AI Agent Gateway |
|---------------|---------------|
| OAuth/JWT 认证 | **API Key + 自然语言** |
| 全局限流 | **Agent 级别限流（待实现）** |
| 协议转换 | **LLM 驱动的智能转换** |
| 静态配置 | **动态 + 意图映射** |
| 面向开发者 | **面向 AI Agent** |

## 测试结果

- [x] 健康检查
- [x] 创建客户 NLP 意图解析
- [x] 代理转发到 ERP
- [x] 客户创建成功

## 待实现功能

- [ ] 多租户/组织支持
- [ ] 插件/扩展机制
- [ ] Agent 服务权限控制
- [ ] Agent 级别限流
- [ ] 熔断/重试
- [ ] 完整 RBAC