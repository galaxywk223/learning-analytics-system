# 本地开发与配置说明

本文档覆盖本项目本地开发所需的全部配置，包括后端环境变量、数据库创建、迁移、前端配置、启动方式、测试命令和常见问题。

## 1. 项目结构

- `backend/`：Flask API、数据库模型、迁移脚本、测试
- `frontend/`：Vue 3 + Vite + TypeScript 前端
- `.env.example`：后端环境变量示例

## 2. 环境要求

- Python 3.10+，推荐 3.11 或 3.12
- Node.js 18+
- PostgreSQL 12+

## 3. 配置文件约定

本项目本地开发主要会用到两类配置文件：

- 根目录 `.env`：后端使用，基于根目录的 `.env.example` 复制得到
- `frontend/.env.development`：前端开发环境使用

数据库结构不再通过单独的 `schema.sql` 导入，统一以 `backend/migrations/` 中的 Flask-Migrate 迁移脚本为准。

## 4. 后端配置与启动

### 4.1 创建后端环境变量

在项目根目录执行：

```powershell
Copy-Item .env.example .env
```

根目录 `.env` 中开发环境最重要的配置项如下：

| 变量名 | 是否必填 | 说明 |
| --- | --- | --- |
| `FLASK_ENV` | 是 | 本地开发请设为 `development` |
| `SECRET_KEY` | 是 | Flask 会话与应用安全配置 |
| `JWT_SECRET_KEY` | 建议 | JWT 签名密钥，不填时会退回 `SECRET_KEY` |
| `DEV_DATABASE_URL` | 建议 | 开发环境数据库连接串 |
| `UPLOAD_FOLDER` | 否 | 上传文件目录，默认是 `backend/uploads` |
| `MAX_UPLOAD_SIZE_MB` | 否 | 上传大小限制，默认 `64` |
| `CORS_ORIGINS` | 否 | 允许访问后端的前端域名，多个值用逗号分隔 |
| `LOG_LEVEL` | 否 | 日志级别，默认 `INFO` |
| `QWEN_API_KEY` | 可选 | 启用 AI 助手时使用 |
| `QWEN_MODEL` | 否 | 默认 `qwen-plus-2025-07-28` |
| `QWEN_BASE_URL` | 否 | 默认 DashScope OpenAI 兼容地址 |
| `AI_ENABLE_FALLBACK` | 否 | AI 降级开关，默认开启 |
| `AI_MAX_RETRIES` | 否 | AI 重试次数，默认 `2` |
| `AI_RETRY_BACKOFF` | 否 | AI 重试退避系数，默认 `1.25` |
| `SENTRY_DSN` | 可选 | 错误监控 |
| `SENTRY_TRACES_SAMPLE_RATE` | 否 | Sentry 性能采样率 |

开发环境数据库连接读取 `DEV_DATABASE_URL`。如果不填写，后端会默认尝试连接：

```text
postgresql://postgres:123456@localhost:5432/learning_analytics_system
```

### 4.2 创建 Python 虚拟环境并安装依赖

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 PowerShell 禁止执行脚本，可先执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### 4.3 创建 PostgreSQL 数据库

迁移命令会创建表，但不会替你创建数据库本身。你需要先在 PostgreSQL 中准备一个空数据库。

如果你直接使用默认连接串，可执行：

```powershell
psql -U postgres -h localhost -c "CREATE DATABASE learning_analytics_system;"
```

如果你要使用自定义用户和数据库，请先创建它们，再把连接串写入根目录 `.env`：

```text
DEV_DATABASE_URL=postgresql://your_user:your_password@localhost:5432/your_database
```

### 4.4 初始化数据库表结构

项目数据库结构以迁移脚本为准，初始化时直接执行：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
flask --app run.py db upgrade
```

执行成功后，所有当前版本所需表结构都会自动创建。

### 4.5 启动后端

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python run.py
```

默认监听地址：

- `http://127.0.0.1:5000`
- 健康检查：`http://127.0.0.1:5000/health`
- API 根路径：`http://127.0.0.1:5000/api`

## 5. 前端配置与启动

### 5.1 配置前端接口地址

开发环境默认配置文件是 `frontend/.env.development`。本地开发建议保留为：

```text
VITE_API_BASE_URL=http://127.0.0.1:5000
```

这里填写的是后端服务根地址，不要额外拼接 `/api`，因为前端请求代码会自己追加接口路径。

如果你想固定前端开发端口，也可以在启动前设置：

```powershell
$env:VITE_PORT="5173"
```

未设置时，Vite 会自动选择空闲端口。

### 5.2 安装依赖并启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端启动后，终端会显示实际访问地址。项目默认绑定 `127.0.0.1`，常见地址类似：

- `http://127.0.0.1:5173`

## 6. 一次完整的本地启动流程

```powershell
# 1. 根目录创建后端环境变量文件
Copy-Item .env.example .env

# 2. 安装并启动后端
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app run.py db upgrade
python run.py

# 3. 新开一个终端，启动前端
cd frontend
npm install
npm run dev
```

## 7. 常用开发命令

### 7.1 后端测试

在项目根目录执行：

```powershell
$env:PYTHONPATH="backend"
pytest backend/tests
```

### 7.2 生成数据库迁移

当你修改 `backend/app/models/` 下的模型后，先生成迁移，再升级数据库：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
flask --app run.py db migrate -m "describe your change"
flask --app run.py db upgrade
```

### 7.3 回滚最近一次迁移

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
flask --app run.py db downgrade
```

### 7.4 前端检查与构建

```powershell
cd frontend
npm run type-check
npm run lint
npm run build
```

## 8. 常见问题

### 8.1 数据库连不上

优先检查以下几项：

- PostgreSQL 服务是否已启动
- `DEV_DATABASE_URL` 中的主机、端口、用户名、密码、数据库名是否正确
- 目标数据库是否已经创建

### 8.2 前端请求 404 或接口地址不对

通常是 `VITE_API_BASE_URL` 配错了。开发环境推荐使用：

```text
VITE_API_BASE_URL=http://127.0.0.1:5000
```

不要写成 `http://127.0.0.1:5000/api`，否则前端会拼出重复路径。

### 8.3 跨域失败

检查根目录 `.env` 中的 `CORS_ORIGINS` 是否包含你的前端访问地址，例如：

```text
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### 8.4 上传目录异常

如果附件上传或导入导出报错，检查根目录 `.env` 中的 `UPLOAD_FOLDER`。相对路径会自动解析到 `backend/` 目录下，开发环境可直接使用：

```text
UPLOAD_FOLDER=uploads
```

### 8.5 数据库密码包含中文或特殊字符

连接串里建议优先使用 URL 编码后的密码。项目已经对 PostgreSQL 连接串做了兼容处理，但仍建议你尽量避免手动输入带空格或未转义的特殊字符。
