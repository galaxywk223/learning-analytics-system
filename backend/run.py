"""
API服务器启动脚本
"""

import os
from dotenv import load_dotenv
from app import create_app, db

# 加载环境变量
load_dotenv()

# 创建应用
config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)


# CLI命令
@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    print("Database initialized.")


@app.cli.command()
def drop_db():
    """删除所有数据库表"""
    if input("Are you sure you want to drop all tables? (yes/no): ").lower() == "yes":
        db.drop_all()
        print("All tables dropped.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
