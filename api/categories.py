from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Category
from database import db
from sqlalchemy import desc

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
@jwt_required()
def get_categories():
    """获取用户的分类列表"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取查询参数
        category_type = request.args.get('type')  # expense, income, both
        
        # 构建查询
        query = Category.query.filter_by(user_id=user_id, is_active=True)
        
        if category_type and category_type != 'all':
            query = query.filter(
                (Category.category_type == category_type) | 
                (Category.category_type == 'both')
            )
        
        categories = query.order_by(Category.sort_order, Category.label).all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    """创建新分类"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['value', 'label']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 是必填字段'}), 400
        
        # 检查分类值是否已存在
        existing_category = Category.query.filter_by(
            user_id=user_id,
            value=data['value']
        ).first()
        
        if existing_category:
            return jsonify({'error': '分类值已存在'}), 400
        
        # 创建分类
        category = Category(
            user_id=user_id,
            value=data['value'],
            label=data['label'],
            category_type=data.get('category_type', 'both'),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'message': '分类创建成功',
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    """更新分类"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 查找分类
        category = Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()
        
        if not category:
            return jsonify({'error': '分类不存在'}), 404
        
        # 如果要更新分类值，检查是否与其他分类冲突
        if 'value' in data and data['value'] != category.value:
            existing_category = Category.query.filter_by(
                user_id=user_id,
                value=data['value']
            ).first()
            
            if existing_category:
                return jsonify({'error': '分类值已存在'}), 400
        
        # 更新字段
        if 'value' in data:
            category.value = data['value']
        if 'label' in data:
            category.label = data['label']
        if 'category_type' in data:
            category.category_type = data['category_type']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        if 'is_active' in data:
            category.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': '分类更新成功',
            'category': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    """删除分类"""
    try:
        user_id = int(get_jwt_identity())
        
        # 查找分类
        category = Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()
        
        if not category:
            return jsonify({'error': '分类不存在'}), 404
        
        # 检查是否有支出记录使用此分类
        from models import Expense
        expense_count = Expense.query.filter_by(
            user_id=user_id,
            category=category.value
        ).count()
        
        if expense_count > 0:
            return jsonify({
                'error': f'无法删除分类，还有 {expense_count} 条记录使用此分类'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'message': '分类删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@categories_bp.route('/init-default', methods=['POST'])
@jwt_required()
def init_default_categories():
    """初始化默认分类"""
    try:
        user_id = int(get_jwt_identity())
        
        # 检查用户是否已有分类
        existing_count = Category.query.filter_by(user_id=user_id).count()
        if existing_count > 0:
            return jsonify({'error': '用户已有分类，无需初始化'}), 400
        
        # 默认分类列表
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
        
        # 批量创建分类
        for cat_data in default_categories:
            category = Category(
                user_id=user_id,
                value=cat_data['value'],
                label=cat_data['label'],
                category_type=cat_data['category_type'],
                sort_order=cat_data['sort_order']
            )
            db.session.add(category)
        
        db.session.commit()
        
        return jsonify({
            'message': f'成功初始化 {len(default_categories)} 个默认分类'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500