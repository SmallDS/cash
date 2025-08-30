#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表结构和初始化数据
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Account, Expense, Reimbursement

def create_tables():
    """创建数据库表"""
    print("正在创建数据库表...")
    
    with app.app_context():
        # 删除所有表（如果存在）
        db.drop_all()
        
        # 创建所有表
        db.create_all()
        
        print("数据库表创建成功！")

def create_sample_data():
    """创建示例数据"""
    print("正在创建示例数据...")
    
    with app.app_context():
        # 创建示例用户
        demo_user = User(
            name="演示用户",
            username="demo",
            email="demo@example.com",
            password_hash=generate_password_hash("demo123")
        )
        db.session.add(demo_user)
        db.session.commit()
        
        # 创建示例账户
        accounts = [
            Account(
                user_id=demo_user.id,
                name="现金",
                account_type="cash",
                balance=1000.00,
                description="现金账户"
            ),
            Account(
                user_id=demo_user.id,
                name="工商银行储蓄卡",
                account_type="bank_card",
                balance=5000.00,
                description="工商银行储蓄卡"
            ),
            Account(
                user_id=demo_user.id,
                name="支付宝",
                account_type="alipay",
                balance=800.00,
                description="支付宝账户"
            ),
            Account(
                user_id=demo_user.id,
                name="微信钱包",
                account_type="wechat_pay",
                balance=300.00,
                description="微信钱包"
            )
        ]
        
        for account in accounts:
            db.session.add(account)
        db.session.commit()
        
        # 创建示例支出记录
        expenses = [
            # 收入记录
            Expense(
                user_id=demo_user.id,
                account_id=accounts[1].id,  # 工商银行
                amount=8000.00,
                expense_type="income",
                category="工资",
                description="2024年1月工资",
                expense_date=datetime(2024, 1, 5),
                is_reimbursable=False
            ),
            Expense(
                user_id=demo_user.id,
                account_id=accounts[2].id,  # 支付宝
                amount=500.00,
                expense_type="income",
                category="奖金",
                description="年终奖金",
                expense_date=datetime(2024, 1, 15),
                is_reimbursable=False
            ),
            
            # 支出记录
            Expense(
                user_id=demo_user.id,
                account_id=accounts[0].id,  # 现金
                amount=25.00,
                expense_type="expense",
                category="餐饮",
                description="午餐",
                expense_date=datetime(2024, 1, 10),
                is_reimbursable=True
            ),
            Expense(
                user_id=demo_user.id,
                account_id=accounts[2].id,  # 支付宝
                amount=120.00,
                expense_type="expense",
                category="交通",
                description="打车费用",
                expense_date=datetime(2024, 1, 12),
                is_reimbursable=True
            ),
            Expense(
                user_id=demo_user.id,
                account_id=accounts[1].id,  # 工商银行
                amount=299.00,
                expense_type="expense",
                category="购物",
                description="购买办公用品",
                expense_date=datetime(2024, 1, 15),
                is_reimbursable=True
            ),
            Expense(
                user_id=demo_user.id,
                account_id=accounts[3].id,  # 微信
                amount=45.00,
                expense_type="expense",
                category="餐饮",
                description="咖啡",
                expense_date=datetime(2024, 1, 16),
                is_reimbursable=False
            ),
            Expense(
                user_id=demo_user.id,
                account_id=accounts[0].id,  # 现金
                amount=80.00,
                expense_type="expense",
                category="娱乐",
                description="电影票",
                expense_date=datetime(2024, 1, 18),
                is_reimbursable=False
            ),
            Expense(
                user_id=demo_user.id,
                account_id=accounts[2].id,  # 支付宝
                amount=200.00,
                expense_type="expense",
                category="交通",
                description="高铁票",
                expense_date=datetime(2024, 1, 20),
                is_reimbursable=True
            )
        ]
        
        for expense in expenses:
            db.session.add(expense)
        db.session.commit()
        
        # 创建示例报销申请
        # 获取可报销的支出记录
        reimbursable_expenses = Expense.query.filter_by(
            user_id=demo_user.id,
            is_reimbursable=True
        ).limit(3).all()
        
        if reimbursable_expenses:
            reimbursement = Reimbursement(
                user_id=demo_user.id,
                title="1月份差旅费报销",
                description="出差相关费用报销申请",
                total_amount=sum(exp.amount for exp in reimbursable_expenses[:2]),
                status="pending"
            )
            reimbursement.expense_ids = [exp.id for exp in reimbursable_expenses[:2]]
            db.session.add(reimbursement)
            db.session.commit()
        
        print("示例数据创建成功！")
        print(f"演示账户: 用户名=demo, 密码=demo123")

def main():
    """主函数"""
    print("=" * 50)
    print("个人记账报销系统 - 数据库初始化")
    print("=" * 50)
    
    # 检查数据库文件目录
    db_dir = os.path.dirname(app.config.get('DATABASE_URL', '').replace('sqlite:///', ''))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"创建数据库目录: {db_dir}")
    
    try:
        # 创建数据库表
        create_tables()
        
        # 询问是否创建示例数据
        create_sample = input("是否创建示例数据？(y/N): ").lower().strip()
        if create_sample in ['y', 'yes', '是']:
            create_sample_data()
        
        print("\n数据库初始化完成！")
        print("\n使用说明:")
        print("1. 启动应用: python app.py")
        print("2. 访问地址: http://localhost:5000")
        if create_sample in ['y', 'yes', '是']:
            print("3. 演示账户: 用户名=demo, 密码=demo123")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()