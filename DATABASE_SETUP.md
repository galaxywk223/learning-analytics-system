# 数据库配置说明文档

本文档详细说明了后端服务的数据库环境要求、配置方法及初始化步骤。

## 1. 环境要求

- **数据库类型**: PostgreSQL
- **版本要求**: PostgreSQL 12+
- **操作系统**: Windows (WSL2), Linux, macOS

## 2. 默认配置信息

在开发环境 (`DevelopmentConfig`) 下，系统默认使用以下连接信息。您可以直接使用此配置，或通过环境变量覆盖。

| 配置项                 | 默认值                      | 说明                 |
| :--------------------- | :-------------------------- | :------------------- |
| **主机 (Host)**        | `localhost`                 | 数据库服务器地址     |
| **端口 (Port)**        | `5432`                      | 默认 PostgreSQL 端口 |
| **用户名 (User)**      | `kai`                       | 数据库用户名         |
| **密码 (Password)**    | `123456`                    | 数据库密码           |
| **数据库名 (DB Name)** | `learning_analytics_system` | 业务数据库名称       |

**默认连接字符串 (URI):**

```
postgresql://kai:123456@localhost:5432/learning_analytics_system
```

## 3. 配置修改 (环境变量)

项目支持通过环境变量动态修改数据库连接，无需修改代码。

### 开发环境 (Development)

设置 `DEV_DATABASE_URL` 环境变量覆盖默认 PostgreSQL 连接：

```bash
# Linux / macOS / WSL
export DEV_DATABASE_URL="postgresql://username:password@localhost:5432/your_db_name"

# Windows PowerShell
$env:DEV_DATABASE_URL="postgresql://username:password@localhost:5432/your_db_name"
```

## 4. 数据库初始化 (Setup)

### 步骤 1: 安装与启动 PostgreSQL

确保 PostgreSQL 服务已安装并正在运行。

```bash
# Ubuntu / WSL
sudo service postgresql start
```

### 步骤 2: 创建用户与数据库

使用 `psql` 命令行工具创建默认的用户和数据库：

```bash
# 登录默认 postgres 用户
sudo -u postgres psql

# 在 psql 终端中执行 SQL:
CREATE USER kai WITH PASSWORD '123456';
CREATE DATABASE learning_analytics_system OWNER kai;
\q
```

### 步骤 3: 导入表结构 (Schema)

如果您已拥有导出的 `schema.sql` 文件，可以直接导入结构：

```bash
psql -h localhost -U kai -d learning_analytics_system -f schema.sql
```

或者，使用 Flask-Migrate 进行迁移初始化（推荐用于从零构建）：

```bash
# 在 backend 目录下
flask db upgrade
```

## 5. 生成数据库结构文件 (可选)

若需导出当前的数据库结构（不含数据），可使用 `pg_dump` 工具：

```bash
pg_dump -s -h localhost -p 5432 -U kai -d learning_analytics_system > schema.sql
```

## 6. 常见问题

- **连接拒绝 (Connection Refused)**: 请检查 PostgreSQL 服务是否启动 (`sudo service postgresql status`)，以及端口 5432 是否被占用。
- **认证失败 (Authentication Failed)**: 请检查 `config.py` 中的密码是否与数据库实际密码匹配。
- **WSL 连接问题**: 若在 WSL 中运行代码连接 Windows 安装的 Postgres，请使用 Windows 的 IP 地址而非 `localhost`。推荐直接在 WSL 内部安装 Postgres。
