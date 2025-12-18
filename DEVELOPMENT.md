# 项目开发运行说明文档

本文档旨在指导如何在本地搭建并运行项目。

## 1. 前置要求

在开始之前，请确保您的开发环境已安装以下工具：

- **Python**: 3.9+ (推荐 3.12)
- **Node.js**: 18+ (推荐 LTS 版本)
- **PostgreSQL**: 12+

## 2. 后端设置 (Backend)

后端基于 **Flask** 框架开发，代码位于 `backend/` 目录。

### 2.1 初始化虚拟环境

建议使用 `venv` 管理 Python 依赖。

```bash
cd backend
python -m venv .venv

# 激活虚拟环境
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate
```

### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

### 2.3 数据库配置

项目默认在开发环境使用 PostgreSQL，连接配置为 `postgresql://kai:123456@localhost:5432/learning_analytics_system`。
详细的数据库初始化步骤请参考 [DATABASE_SETUP.md](./DATABASE_SETUP.md)。

**初始化数据库表结构：**

```bash
# 确保在 backend 目录下且已激活虚拟环境
flask db upgrade
```

### 2.4 启动后端服务

```bash
# 设置环境变量 (Windows PowerShell)
$env:FLASK_APP="run.py"
$env:FLASK_ENV="development"

# 启动服务 (默认端口 5000)
python -m flask run --debug
```

启动成功后，API 服务将运行在 `http://127.0.0.1:5000`。

## 3. 前端设置 (Frontend)

前端基于 **Vue 3 + Vite + TypeScript** 开发，代码位于 `frontend/` 目录。

### 3.1 安装依赖

```bash
cd frontend
npm install
```

### 3.2 启动开发服务器

```bash
npm run dev
```

启动成功后，通常访问地址为 `http://localhost:5173`。

## 5. 常见任务

### 运行测试

后端包含基于 `pytest` 的单元测试和集成测试。

```bash
# 在根目录下运行 (确保已安装 dev 依赖)
# 注意：需设置 PYTHONPATH 为 backend 目录
$env:PYTHONPATH="backend"
pytest backend/tests
```

### 数据库迁移

当你修改了 `app/models.py` 中的模型后，需要生成并执行迁移脚本。

```bash
cd backend

# 生成迁移脚本
flask db migrate -m "描述你的修改"

# 应用到数据库
flask db upgrade
```
