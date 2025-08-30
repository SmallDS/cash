from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    reimbursements = db.relationship('Reimbursement', backref='user', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Account(db.Model):
    """账户模型"""
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # cash, bank, credit_card, alipay, wechat
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    expenses = db.relationship('Expense', backref='account', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'account_type': self.account_type,
            'balance': float(self.balance),
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Expense(db.Model):
    """支出记录模型"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # food, transport, shopping, etc.
    subcategory = db.Column(db.String(50))
    description = db.Column(db.Text)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    expense_type = db.Column(db.String(20), default='expense')  # expense, income
    tags = db.Column(db.String(200))  # 标签，逗号分隔
    receipt_url = db.Column(db.String(255))  # 收据图片URL
    is_reimbursable = db.Column(db.Boolean, default=False)
    reimbursement_id = db.Column(db.Integer, db.ForeignKey('reimbursements.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'amount': float(self.amount),
            'category': self.category,
            'subcategory': self.subcategory,
            'description': self.description,
            'expense_date': self.expense_date.isoformat() if self.expense_date else None,
            'expense_type': self.expense_type,
            'tags': self.tags.split(',') if self.tags else [],
            'receipt_url': self.receipt_url,
            'is_reimbursable': self.is_reimbursable,
            'reimbursement_id': self.reimbursement_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    """分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    value = db.Column(db.String(50), nullable=False)  # 分类值，如 'food'
    label = db.Column(db.String(100), nullable=False)  # 分类标签，如 '餐饮'
    category_type = db.Column(db.String(20), default='both')  # expense, income, both
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：同一用户的分类值不能重复
    __table_args__ = (db.UniqueConstraint('user_id', 'value', name='unique_user_category'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'label': self.label,
            'category_type': self.category_type,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Reimbursement(db.Model):
    """报销申请模型"""
    __tablename__ = 'reimbursements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid
    submit_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    approve_date = db.Column(db.Date)
    approver_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    expenses = db.relationship('Expense', backref='reimbursement', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'submit_date': self.submit_date.isoformat() if self.submit_date else None,
            'approve_date': self.approve_date.isoformat() if self.approve_date else None,
            'approver_notes': self.approver_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expense_count': len(self.expenses)
        }