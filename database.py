#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置模块
独立的数据库配置，避免循环导入
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 在应用上下文中创建表
    with app.app_context():
        db.create_all()