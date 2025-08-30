#!/usr/bin/env python3
"""
数据库迁移脚本：添加分类表
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import Category, User

def migrate_categories():
    """迁移分类表"""
    with app.app_context():
        try:
            # 创建分类表
            print("正在创建分类表...")
            db.create_all()
            print("分类表创建成功！")
            
            # 为所有现有用户初始化默认分类
            print("正在为现有用户初始化默认分类...")
            
            users = User.query.all()
            default_categories = [
                {'value': 'food', 'label': '餐饮', 'category_type': 'expense', 'sort_order': 1},
                {'value': 'transport', 'label': '交通', 'category_type': 'expense', 'sort_order': 2},
                {'value': 'shopping', 'label': '购物', 'category_type': 'expense', 'sort_order': 3},
                {'value': 'entertainment', 'label': '娱乐', 'category_type': 'expense', 'sort_order': 4},
                {'value': 'healthcare', 'label': '医疗', 'category_type': 'expense', 'sort_order': 5},
                {'value': 'education', 'label': '教育', 'category_type': 'expense', 'sort_order': 6},
                {'value': 'housing', 'label': '住房', 'category_type': 'expense', 'sort_order': 7},
                {'value': 'utilities', 'label': '水电费', 'category_type': 'expense', 'sort_order': 8},
                {'value': 'communication', 'label': '通讯', 'category_type': 'expense', 'sort_order': 9},
                {'value': 'insurance', 'label': '保险', 'category_type': 'expense', 'sort_order': 10},
                {'value': 'investment', 'label': '投资', 'category_type': 'both', 'sort_order': 11},
                {'value': 'salary', 'label': '工资', 'category_type': 'income', 'sort_order': 12},
                {'value': 'bonus', 'label': '奖金', 'category_type': 'income', 'sort_order': 13},
                {'value': 'other', 'label': '其他', 'category_type': 'both', 'sort_order': 14}
            ]
            
            for user in users:
                # 检查用户是否已有分类
                existing_count = Category.query.filter_by(user_id=user.id).count()
                if existing_count > 0:
                    print(f"用户 {user.username} 已有分类，跳过初始化")
                    continue
                
                # 为用户创建默认分类
                for cat_data in default_categories:
                    category = Category(
                        user_id=user.id,
                        value=cat_data['value'],
                        label=cat_data['label'],
                        category_type=cat_data['category_type'],
                        sort_order=cat_data['sort_order']
                    )
                    db.session.add(category)
                
                print(f"为用户 {user.username} 初始化了 {len(default_categories)} 个默认分类")
            
            db.session.commit()
            print("分类迁移完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"迁移失败: {e}")
            raise

if __name__ == '__main__':
    migrate_categories()