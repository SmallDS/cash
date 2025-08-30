from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Account
from database import db
from sqlalchemy import desc
from decimal import Decimal

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/', methods=['GET'])
@jwt_required()
def get_accounts():
    """获取用户账户列表"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        account_type = request.args.get('type')
        is_active = request.args.get('active')
        
        # 构建查询
        query = Account.query.filter_by(user_id=user_id)
        
        if account_type:
            query = query.filter_by(account_type=account_type)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        # 排序和分页
        query = query.order_by(desc(Account.created_at))
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        accounts = [account.to_dict() for account in pagination.items]
        
        return jsonify({
            'accounts': accounts,
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

@accounts_bp.route('/', methods=['POST'])
@jwt_required()
def create_account():
    """创建新账户"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'account_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 是必填字段'}), 400
        
        # 验证账户类型
        valid_types = ['cash', 'bank', 'credit_card', 'alipay', 'wechat', 'other']
        if data['account_type'] not in valid_types:
            return jsonify({'error': f'账户类型必须是: {", ".join(valid_types)}'}), 400
        
        # 检查账户名称是否重复
        existing_account = Account.query.filter_by(
            user_id=user_id,
            name=data['name']
        ).first()
        
        if existing_account:
            return jsonify({'error': '账户名称已存在'}), 400
        
        # 创建账户
        account = Account(
            user_id=user_id,
            name=data['name'],
            account_type=data['account_type'],
            balance=Decimal(str(data.get('balance', 0.00))),
            description=data.get('description', '')
        )
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify({
            'message': '账户创建成功',
            'account': account.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    """获取单个账户详情"""
    try:
        user_id = int(get_jwt_identity())
        
        account = Account.query.filter_by(
            id=account_id,
            user_id=user_id
        ).first()
        
        if not account:
            return jsonify({'error': '账户不存在'}), 404
        
        return jsonify({
            'account': account.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    """更新账户信息"""
    try:
        user_id = int(get_jwt_identity())
        
        account = Account.query.filter_by(
            id=account_id,
            user_id=user_id
        ).first()
        
        if not account:
            return jsonify({'error': '账户不存在'}), 404
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'name' in data:
            # 检查名称是否重复
            existing_account = Account.query.filter_by(
                user_id=user_id,
                name=data['name']
            ).filter(Account.id != account_id).first()
            
            if existing_account:
                return jsonify({'error': '账户名称已存在'}), 400
            
            account.name = data['name']
        
        if 'account_type' in data:
            valid_types = ['cash', 'bank', 'credit_card', 'alipay', 'wechat', 'other']
            if data['account_type'] not in valid_types:
                return jsonify({'error': f'账户类型必须是: {", ".join(valid_types)}'}), 400
            account.account_type = data['account_type']
        
        if 'balance' in data:
            account.balance = Decimal(str(data['balance']))
        
        if 'description' in data:
            account.description = data['description']
        
        if 'is_active' in data:
            account.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': '账户更新成功',
            'account': account.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    """删除账户"""
    try:
        user_id = get_jwt_identity()
        
        account = Account.query.filter_by(
            id=account_id,
            user_id=user_id
        ).first()
        
        if not account:
            return jsonify({'error': '账户不存在'}), 404
        
        # 检查是否有关联的支出记录
        if account.expenses:
            return jsonify({
                'error': '无法删除有支出记录的账户，请先删除相关支出记录或将账户设为非活跃状态'
            }), 400
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'message': '账户删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/types', methods=['GET'])
@jwt_required()
def get_account_types():
    """获取账户类型列表"""
    account_types = [
        {'value': 'cash', 'label': '现金'},
        {'value': 'bank', 'label': '银行卡'},
        {'value': 'credit_card', 'label': '信用卡'},
        {'value': 'alipay', 'label': '支付宝'},
        {'value': 'wechat', 'label': '微信支付'},
        {'value': 'other', 'label': '其他'}
    ]
    
    return jsonify({'account_types': account_types}), 200