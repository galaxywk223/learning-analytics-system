# 萤火集 - 运行指南

> 萤火集是一套前后端分离的学习记录与分析系统，小组成员请按照以下步骤在本地运行项目。

## 📋 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus
- **后端**: Flask + PostgreSQL

## 🚀 快速开始

### 前置要求（必装软件）

确保你的电脑已安装以下软件：

- **Visual Studio Code** (推荐的开发工具)
- Python 3.12+
- Node.js 22+
- PostgreSQL 17+

**查看已安装版本：**

```cmd
python --version
node --version
psql --version
code --version
```

---

## 💻 VS Code 开发环境配置

本项目推荐使用 **Visual Studio Code** 进行开发，以下是推荐的配置：

### 安装 VS Code

1. 访问 [Visual Studio Code 官网](https://code.visualstudio.com/) 下载安装
2. 安装后，在命令行运行 `code --version` 验证安装成功

### 推荐安装的扩展

**Python 开发必备：**

- `Python` - Python 语言支持
- `Pylance` - Python 代码智能提示
- `Python Debugger` - Python 调试工具

**前端开发必备：**

- `Vue - Official` (Volar) - Vue 3 语言支持
- `TypeScript Vue Plugin (Volar)` - Vue 中的 TypeScript 支持
- `ESLint` - JavaScript/TypeScript 代码规范检查
- `Prettier - Code formatter` - 代码格式化工具

**通用工具：**

- `GitLens` - Git 可视化增强
- `Path Intellisense` - 路径自动补全
- `Auto Rename Tag` - 自动重命名标签
- `Error Lens` - 行内错误提示

### 在 VS Code 中打开项目

```cmd
# 克隆项目后，用 VS Code 打开
cd learning-analytics-system
code .
```

### VS Code 集成终端使用

1. 打开 VS Code 后，按 `` Ctrl+` `` 打开集成终端
2. 推荐同时打开多个终端：
   - **终端 1**：运行后端（Flask）
   - **终端 2**：运行前端（Vue）
3. 在终端右上角点击 `+` 号可以创建新终端

**提示：** 本项目所有的命令行操作都可以在 VS Code 的集成终端中完成，无需切换到其他终端窗口。

---

## 🧭 本地运行步骤

### 步骤一：启动后端服务

1. 进入后端目录并创建虚拟环境

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
```

2. 安装依赖

```cmd
pip install -r requirements.txt
```

3. 配置数据库（PostgreSQL）

```cmd
# 创建数据库（在 psql 中执行）
psql -U postgres
```

然后在 PostgreSQL 命令行中执行：

```sql
CREATE DATABASE mlogger;
CREATE USER mlogger WITH PASSWORD 'mlogger123';
GRANT ALL PRIVILEGES ON DATABASE mlogger TO mlogger;
\q
```

4. 在 `backend` 目录创建 `.env` 文件

```env
DATABASE_URL=postgresql+psycopg2://mlogger:mlogger123@localhost:5432/mlogger
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret-key
CORS_ORIGINS=http://localhost:5173
```

5. 初始化数据库并运行

```cmd
flask db upgrade
python run.py
```

✅ 后端启动成功：<http://localhost:5000>

### 步骤二：启动前端服务

1. 打开新终端，进入前端目录

```cmd
cd frontend
```

2. 安装依赖

```cmd
npm install
```

3. 在 `frontend` 目录创建 `.env` 文件

```env
VITE_API_BASE_URL=http://localhost:5000
```

4. 运行前端

```cmd
npm run dev
```

✅ 前端启动成功：<http://localhost:5173>

---

## 🔄 Git 协作流程

### 初次设置：Fork 项目

1. **Fork 项目到你的账号**

   - 访问：`https://github.com/galaxywk223/learning-analytics-system`
   - 点击右上角 `Fork` 按钮

2. **克隆到本地**

```cmd
git clone https://github.com/你的用户名/learning-analytics-system.git
cd learning-analytics-system
```

3. **关联原项目**

```cmd
git remote add upstream https://github.com/galaxywk223/learning-analytics-system.git
```

### 开发工作流程

1. **同步最新代码**（每次开发前必做）

```cmd
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

2. **创建功能分支**

```cmd
git checkout -b feature/你的功能名
```

3. **提交代码**

```cmd
git status                              # 查看修改
git add .                               # 添加所有修改
git commit -m "描述你的修改"              # 提交
git push origin feature/你的功能名       # 推送到你的 Fork
```

4. **提交 Pull Request**
   - 访问你 Fork 的项目页面
   - 点击 `Compare & pull request`
   - 填写 PR 说明（改了什么、为什么改）
   - 提交后等待审核合并

### Git 常用命令参考

```cmd
git branch                    # 查看分支
git checkout 分支名           # 切换分支
git log --oneline            # 查看提交历史
git checkout -- 文件名        # 撤销修改
git remote -v                # 查看远程仓库
```

---

## ⚠️ 常见问题解决

### 1. 虚拟环境激活失败

**现象**：PowerShell 提示无法运行脚本

**解决**：以管理员身份运行 PowerShell，执行：

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. 依赖安装太慢

**解决方法**：

```cmd
# 前端：使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# Python：升级 pip
python -m pip install --upgrade pip
```

### 3. 端口被占用

**解决方法**：

```cmd
# 查看哪个进程占用了端口
netstat -ano | findstr :5000
netstat -ano | findstr :5173

# 结束进程（记下进程ID后执行，需要管理员权限）
taskkill /PID <进程ID> /F
```

### 4. 数据库连接失败

**解决方法**：

```cmd
# 启动 PostgreSQL 服务（管理员权限）
net start postgresql-x64-17

# 或者手动启动
# 按 Win+R，输入 services.msc
# 找到 PostgreSQL 服务，点击启动
```

---

**✅ 运行成功后，就可以开始写代码了！遇到问题记得在群里讨论。**

---

## 🤖 智能规划功能
- 在 `.env` 或系统环境变量中配置 `GEMINI_API_KEY`（必填）和可选的 `GEMINI_MODEL`。
- 部署或更新后执行 `./scripts/migrate.sh` 应用最新数据库迁移。
- 后台将聚合日/周/月/阶段的学习数据，再调用 Gemini 生成中文分析与规划，前端支持历史记录查询。
