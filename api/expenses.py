from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Expense, Account
from database import db
from sqlalchemy import desc, and_, or_
from datetime import datetime, date
from decimal import Decimal

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/', methods=['GET'])
@jwt_required()
def get_expenses():
    """获取支出记录列表"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        expense_type = request.args.get('type')
        account_id = request.args.get('account_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        # 构建查询
        query = Expense.query.filter_by(user_id=user_id)
        
        if category:
            query = query.filter_by(category=category)
        
        if expense_type:
            query = query.filter_by(expense_type=expense_type)
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date >= start_date_obj)
            except ValueError:
                return jsonify({'error': '开始日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date <= end_date_obj)
            except ValueError:
                return jsonify({'error': '结束日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        if search:
            query = query.filter(
                or_(
                    Expense.description.contains(search),
                    Expense.category.contains(search),
                    Expense.subcategory.contains(search)
                )
            )
        
        # 排序和分页
        query = query.order_by(desc(Expense.expense_date), desc(Expense.created_at))
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        expenses = []
        for expense in pagination.items:
            expense_dict = expense.to_dict()
            # 添加账户信息
            if expense.account:
                expense_dict['account'] = {
                    'id': expense.account.id,
                    'name': expense.account.name,
                    'account_type': expense.account.account_type
                }
            expenses.append(expense_dict)
        
        return jsonify({
            'expenses': expenses,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/', methods=['POST'])
@jwt_required()
def create_expense():
    """创建支出记录"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['account_id', 'amount', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 是必填字段'}), 400
        
        # 验证账户是否存在且属于当前用户
        account = Account.query.filter_by(
            id=data['account_id'],
            user_id=user_id
        ).first()
        
        if not account:
            return jsonify({'error': '账户不存在'}), 404
        
        # 验证金额
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                return jsonify({'error': '金额必须大于0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': '金额格式错误'}), 400
        
        # 处理日期
        expense_date = date.today()
        if data.get('expense_date'):
            try:
                expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        # 创建支出记录
        expense = Expense(
            user_id=user_id,
            account_id=data['account_id'],
            amount=amount,
            category=data['category'],
            subcategory=data.get('subcategory', ''),
            description=data.get('description', ''),
            expense_date=expense_date,
            expense_type=data.get('expense_type', 'expense'),
            tags=','.join(data.get('tags', [])) if data.get('tags') else '',
            receipt_url=data.get('receipt_url', ''),
            is_reimbursable=data.get('is_reimbursable', False)
        )
        
        db.session.add(expense)
        
        # 更新账户余额
        if expense.expense_type == 'expense':
            account.balance -= amount
        else:  # income
            account.balance += amount
        
        db.session.commit()
        
        return jsonify({
            'message': '记录创建成功',
            'expense': expense.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>', methods=['GET'])
@jwt_required()
def get_expense(expense_id):
    """获取单个支出记录详情"""
    try:
        user_id = int(get_jwt_identity())
        
        expense = Expense.query.filter_by(
            id=expense_id,
            user_id=user_id
        ).first()
        
        if not expense:
            return jsonify({'error': '记录不存在'}), 404
        
        expense_dict = expense.to_dict()
        # 添加账户信息
        if expense.account:
            expense_dict['account'] = {
                'id': expense.account.id,
                'name': expense.account.name,
                'account_type': expense.account.account_type
            }
        
        return jsonify({
            'expense': expense_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """更新支出记录"""
    try:
        user_id = int(get_jwt_identity())
        
        expense = Expense.query.filter_by(
            id=expense_id,
            user_id=user_id
        ).first()
        
        if not expense:
            return jsonify({'error': '记录不存在'}), 404
        
        data = request.get_json()
        old_amount = expense.amount
        old_type = expense.expense_type
        old_account = expense.account
        
        # 更新字段
        if 'account_id' in data:
            # 验证新账户
            new_account = Account.query.filter_by(
                id=data['account_id'],
                user_id=user_id
            ).first()
            if not new_account:
                return jsonify({'error': '账户不存在'}), 404
            expense.account_id = data['account_id']
        
        if 'amount' in data:
            try:
                amount = Decimal(str(data['amount']))
                if amount <= 0:
                    return jsonify({'error': '金额必须大于0'}), 400
                expense.amount = amount
            except (ValueError, TypeError):
                return jsonify({'error': '金额格式错误'}), 400
        
        if 'category' in data:
            expense.category = data['category']
        
        if 'subcategory' in data:
            expense.subcategory = data['subcategory']
        
        if 'description' in data:
            expense.description = data['description']
        
        if 'expense_date' in data:
            try:
                expense.expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        if 'expense_type' in data:
            expense.expense_type = data['expense_type']
        
        if 'tags' in data:
            expense.tags = ','.join(data['tags']) if data['tags'] else ''
        
        if 'receipt_url' in data:
            expense.receipt_url = data['receipt_url']
        
        if 'is_reimbursable' in data:
            expense.is_reimbursable = data['is_reimbursable']
        
        # 更新账户余额
        # 先撤销原来的影响
        if old_type == 'expense':
            old_account.balance += old_amount
        else:
            old_account.balance -= old_amount
        
        # 应用新的影响
        current_account = expense.account
        if expense.expense_type == 'expense':
            current_account.balance -= expense.amount
        else:
            current_account.balance += expense.amount
        
        db.session.commit()
        
        return jsonify({
            'message': '记录更新成功',
            'expense': expense.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """删除支出记录"""
    try:
        user_id = int(get_jwt_identity())
        
        expense = Expense.query.filter_by(
            id=expense_id,
            user_id=user_id
        ).first()
        
        if not expense:
            return jsonify({'error': '记录不存在'}), 404
        
        # 恢复账户余额
        account = expense.account
        if expense.expense_type == 'expense':
            account.balance += expense.amount
        else:
            account.balance -= expense.amount
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'message': '记录删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@expenses_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """获取支出分类列表（兼容性接口，重定向到分类API）"""
    try:
        user_id = int(get_jwt_identity())
        
        # 从数据库获取用户分类
        from models import Category
        categories = Category.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).order_by(Category.sort_order, Category.label).all()
        
        # 如果用户没有分类，返回默认分类
        if not categories:
            default_categories = [
                {'value': 'food', 'label': '餐饮'},
                {'value': 'transport', 'label': '交通'},
                {'value': 'shopping', 'label': '购物'},
                {'value': 'entertainment', 'label': '娱乐'},
                {'value': 'healthcare', 'label': '医疗'},
                {'value': 'education', 'label': '教育'},
                {'value': 'housing', 'label': '住房'},
                {'value': 'utilities', 'label': '水电费'},
                {'value': 'communication', 'label': '通讯'},
                {'value': 'insurance', 'label': '保险'},
                {'value': 'investment', 'label': '投资'},
                {'value': 'salary', 'label': '工资'},
                {'value': 'bonus', 'label': '奖金'},
                {'value': 'other', 'label': '其他'}
            ]
            return jsonify({'categories': default_categories}), 200
        
        # 转换为兼容格式
        category_list = [{
            'value': cat.value,
            'label': cat.label
        } for cat in categories]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500