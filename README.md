# 萤火集 · 学习分析与智能规划系统

轻量、开箱即用的学习记录、统计分析与智能规划（AI）平台。前后端完全分离，支持本地与服务器部署。

---

## 特色功能

- 记录学习时长与任务，分类/子分类管理
- 可视化统计（趋势、分类占比、条形图下钻）
- 倒计时、成就时刻、待办管理
- 智能规划助手（基于真实数据输出分析与下一步规划，含历史追溯）

## 技术栈

- 前端：Vue 3 + TypeScript + Vite + Element Plus
- 后端：Flask + SQLAlchemy + Flask‑Migrate + PostgreSQL

## 平台建议（强烈推荐 Linux/WSL2）

- 更少的权限/路径问题与更强的脚本兼容性
- PostgreSQL 安装与服务管理更顺滑
- 构建与依赖解析速度更稳

> Windows 完全可用，但若遇到权限与路径大小写等问题，建议使用 WSL2（Ubuntu）环境。

---

## 前置要求

- Python 3.12+
- Node.js 18+（建议 20/22）
- PostgreSQL 14+（建议 17）

检查版本：

```bash
python --version
node --version
psql --version
```

---

## 一、后端（Flask）

### 1. 克隆仓库

```bash
git clone https://github.com/galaxywk223/learning-analytics-system.git
cd learning-analytics-system
```

### 2. 创建虚拟环境并安装依赖

- Linux/macOS（bash）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Windows（PowerShell）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 创建数据库

- Linux（以本机 postgres 超级用户为例）

```bash
sudo -u postgres createuser -P mlogger   # 按提示设置密码
sudo -u postgres createdb -O mlogger mlogger
```

- Windows（psql 交互）

```powershell
psql -U postgres -h localhost
-- 进入后执行：
CREATE USER mlogger WITH PASSWORD 'mlogger123';
CREATE DATABASE mlogger OWNER mlogger;
\q
```

### 4. 配置环境变量（.env）

在 `backend` 目录新建 `.env`：

```dotenv
# 开发库连接（DevelopmentConfig 读取 DEV_DATABASE_URL）
DEV_DATABASE_URL=postgresql+psycopg2://mlogger:mlogger123@localhost:5432/mlogger

# 生产库连接（生产模式使用）
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/prod

# 安全与跨域
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret-key
CORS_ORIGINS=http://localhost:5173

# 智能规划（可选）
GEMINI_API_KEY=your_google_api_key
# GEMINI_MODEL=gemini-2.5-flash
AI_ENABLE_FALLBACK=1       # 模型不可用时返回基于真实数据的模板分析/规划
AI_MAX_RETRIES=2
AI_RETRY_BACKOFF=1.25
```

### 5. 迁移并启动

- Linux/macOS（bash）

```bash
# 指定 Flask App（工厂模式）
export FLASK_APP=run.py
export FLASK_ENV=development
flask db upgrade
python run.py
```

- Windows（PowerShell）

```powershell
$env:FLASK_APP='run.py'
$env:FLASK_ENV='development'
flask db upgrade
python .\run.py
```

后端启动地址：<http://localhost:5000>

> 若 PostgreSQL 服务未启动：Linux 使用 `systemctl start postgresql`；Windows 使用 `net start postgresql-x64-17`（版本号按实际安装）。

---

## 二、前端（Vue 3）

### 1. 安装依赖并启动

- Linux/macOS（bash）

```bash
cd ../frontend
npm install
# API 地址配置
printf "VITE_API_BASE_URL=http://localhost:5000\n" > .env
npm run dev
```

- Windows（PowerShell）

```powershell
cd ..\frontend
npm install
# API 地址配置
"VITE_API_BASE_URL=http://localhost:5000" | Out-File -Encoding utf8 .env
npm run dev
```

前端启动地址：<http://localhost:5173>

### 2. 构建生产包

- Linux/macOS

```bash
npm run build
```

- Windows

```powershell
npm run build
```

---

## 三、智能规划（AI）说明

- 后端会聚合日/周/月/阶段的真实学习数据，再调用 Gemini 生成中文分析与规划。
- 如果网络/证书问题导致模型不可用，后端会返回“基于真实数据的模板结果”（可在 `.env` 通过 `AI_ENABLE_FALLBACK=0` 关闭）。
- 常见 SSL 错误（如 `SSL: UNEXPECTED_EOF_WHILE_READING`）通常是网络抖动或代理导致；系统已做自动重试与兜底。

---

## 常见问题（Linux 与 Windows 对照）

- 端口被占用
  - Linux: `lsof -i:5000 | awk 'NR>1{print $2}' | xargs -r kill -9`
  - Windows: `netstat -ano | findstr :5000` + `taskkill /PID <PID> /F`
- 虚拟环境激活失败
  - Windows PowerShell 需执行（管理员）：`Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
- PostgreSQL 无法连接
  - 确认服务已启动；连接串使用 `postgresql+psycopg2://user:pass@host:port/db`
- CORS 报错
  - 将前端地址加入后端 `.env` 的 `CORS_ORIGINS`，使用逗号分隔多个来源
- Gemini 报错/超时
  - 检查 `GEMINI_API_KEY`；必要时设置 `HTTP(S)_PROXY`；或者暂时依赖兜底模板结果

---

## 目录结构（简要）

- `backend/` Flask 应用（`run.py`、`app/`、`migrations/`）
- `frontend/` Vue 前端
- `scripts/` 部署脚本

## 许可证

本项目采用 MIT License，详见 `LICENSE`。

> 建议优先在 Linux/WSL2 环境开发与部署；若你只在 Windows 上开发，推荐使用 PowerShell 并按本文 Windows 命令执行。
