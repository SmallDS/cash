from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Reimbursement, Expense
from database import db
from sqlalchemy import desc, and_
from datetime import datetime, date

reimbursements_bp = Blueprint('reimbursements', __name__)

@reimbursements_bp.route('/', methods=['GET'])
@jwt_required()
def get_reimbursements():
    """获取报销申请列表"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        # 构建查询
        query = Reimbursement.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Reimbursement.submit_date >= start_date_obj)
            except ValueError:
                return jsonify({'error': '开始日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Reimbursement.submit_date <= end_date_obj)
            except ValueError:
                return jsonify({'error': '结束日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        if search:
            query = query.filter(
                Reimbursement.title.contains(search) |
                Reimbursement.description.contains(search)
            )
        
        # 排序和分页
        query = query.order_by(desc(Reimbursement.created_at))
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        reimbursements = [reimbursement.to_dict() for reimbursement in pagination.items]
        
        return jsonify({
            'reimbursements': reimbursements,
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

@reimbursements_bp.route('/', methods=['POST'])
@jwt_required()
def create_reimbursement():
    """创建报销申请"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'expense_ids']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 是必填字段'}), 400
        
        expense_ids = data['expense_ids']
        if not isinstance(expense_ids, list) or len(expense_ids) == 0:
            return jsonify({'error': '必须选择至少一个支出记录'}), 400
        
        # 验证支出记录是否存在且属于当前用户
        expenses = Expense.query.filter(
            and_(
                Expense.id.in_(expense_ids),
                Expense.user_id == user_id,
                Expense.is_reimbursable == True,
                Expense.reimbursement_id.is_(None)  # 未被其他报销申请关联
            )
        ).all()
        
        if len(expenses) != len(expense_ids):
            return jsonify({'error': '部分支出记录不存在、不可报销或已被其他报销申请关联'}), 400
        
        # 计算总金额
        total_amount = sum(expense.amount for expense in expenses)
        
        # 处理提交日期
        submit_date = date.today()
        if data.get('submit_date'):
            try:
                submit_date = datetime.strptime(data['submit_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        # 创建报销申请
        reimbursement = Reimbursement(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            total_amount=total_amount,
            submit_date=submit_date
        )
        
        db.session.add(reimbursement)
        db.session.flush()  # 获取ID
        
        # 关联支出记录
        for expense in expenses:
            expense.reimbursement_id = reimbursement.id
        
        db.session.commit()
        
        return jsonify({
            'message': '报销申请创建成功',
            'reimbursement': reimbursement.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/<int:reimbursement_id>', methods=['GET'])
@jwt_required()
def get_reimbursement(reimbursement_id):
    """获取单个报销申请详情"""
    try:
        user_id = int(get_jwt_identity())
        
        reimbursement = Reimbursement.query.filter_by(
            id=reimbursement_id,
            user_id=user_id
        ).first()
        
        if not reimbursement:
            return jsonify({'error': '报销申请不存在'}), 404
        
        reimbursement_dict = reimbursement.to_dict()
        
        # 添加关联的支出记录
        expenses = [expense.to_dict() for expense in reimbursement.expenses]
        reimbursement_dict['expenses'] = expenses
        
        return jsonify({
            'reimbursement': reimbursement_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/<int:reimbursement_id>', methods=['PUT'])
@jwt_required()
def update_reimbursement(reimbursement_id):
    """更新报销申请"""
    try:
        user_id = int(get_jwt_identity())
        
        reimbursement = Reimbursement.query.filter_by(
            id=reimbursement_id,
            user_id=user_id
        ).first()
        
        if not reimbursement:
            return jsonify({'error': '报销申请不存在'}), 404
        
        # 只有待审核状态的申请可以修改
        if reimbursement.status != 'pending':
            return jsonify({'error': '只有待审核的申请可以修改'}), 400
        
        data = request.get_json()
        
        # 更新基本信息
        if 'title' in data:
            reimbursement.title = data['title']
        
        if 'description' in data:
            reimbursement.description = data['description']
        
        if 'submit_date' in data:
            try:
                reimbursement.submit_date = datetime.strptime(data['submit_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD'}), 400
        
        # 更新关联的支出记录
        if 'expense_ids' in data:
            expense_ids = data['expense_ids']
            if not isinstance(expense_ids, list) or len(expense_ids) == 0:
                return jsonify({'error': '必须选择至少一个支出记录'}), 400
            
            # 清除原有关联
            for expense in reimbursement.expenses:
                expense.reimbursement_id = None
            
            # 验证新的支出记录
            expenses = Expense.query.filter(
                and_(
                    Expense.id.in_(expense_ids),
                    Expense.user_id == user_id,
                    Expense.is_reimbursable == True,
                    Expense.reimbursement_id.is_(None)
                )
            ).all()
            
            if len(expenses) != len(expense_ids):
                return jsonify({'error': '部分支出记录不存在、不可报销或已被其他报销申请关联'}), 400
            
            # 建立新关联
            for expense in expenses:
                expense.reimbursement_id = reimbursement.id
            
            # 重新计算总金额
            reimbursement.total_amount = sum(expense.amount for expense in expenses)
        
        db.session.commit()
        
        return jsonify({
            'message': '报销申请更新成功',
            'reimbursement': reimbursement.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/<int:reimbursement_id>', methods=['DELETE'])
@jwt_required()
def delete_reimbursement(reimbursement_id):
    """删除报销申请"""
    try:
        user_id = int(get_jwt_identity())
        
        reimbursement = Reimbursement.query.filter_by(
            id=reimbursement_id,
            user_id=user_id
        ).first()
        
        if not reimbursement:
            return jsonify({'error': '报销申请不存在'}), 404
        
        # 只有待审核状态的申请可以删除
        if reimbursement.status != 'pending':
            return jsonify({'error': '只有待审核的申请可以删除'}), 400
        
        # 清除关联的支出记录
        for expense in reimbursement.expenses:
            expense.reimbursement_id = None
        
        db.session.delete(reimbursement)
        db.session.commit()
        
        return jsonify({'message': '报销申请删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/<int:reimbursement_id>/approve', methods=['POST'])
@jwt_required()
def approve_reimbursement(reimbursement_id):
    """审批报销申请"""
    try:
        user_id = int(get_jwt_identity())
        
        reimbursement = Reimbursement.query.filter_by(
            id=reimbursement_id,
            user_id=user_id
        ).first()
        
        if not reimbursement:
            return jsonify({'error': '报销申请不存在'}), 404
        
        if reimbursement.status != 'pending':
            return jsonify({'error': '只有待审核的申请可以审批'}), 400
        
        data = request.get_json()
        action = data.get('action')  # approve, reject
        notes = data.get('notes', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': '审批动作必须是 approve 或 reject'}), 400
        
        reimbursement.status = 'approved' if action == 'approve' else 'rejected'
        reimbursement.approve_date = date.today()
        reimbursement.approver_notes = notes
        
        db.session.commit()
        
        return jsonify({
            'message': f'报销申请已{"通过" if action == "approve" else "拒绝"}',
            'reimbursement': reimbursement.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/<int:reimbursement_id>/pay', methods=['POST'])
@jwt_required()
def pay_reimbursement(reimbursement_id):
    """标记报销申请为已支付"""
    try:
        user_id = int(get_jwt_identity())
        
        reimbursement = Reimbursement.query.filter_by(
            id=reimbursement_id,
            user_id=user_id
        ).first()
        
        if not reimbursement:
            return jsonify({'error': '报销申请不存在'}), 404
        
        if reimbursement.status != 'approved':
            return jsonify({'error': '只有已通过的申请可以标记为已支付'}), 400
        
        reimbursement.status = 'paid'
        db.session.commit()
        
        return jsonify({
            'message': '报销申请已标记为已支付',
            'reimbursement': reimbursement.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/available-expenses', methods=['GET'])
@jwt_required()
def get_available_expenses():
    """获取可用于报销的支出记录"""
    try:
        user_id = int(get_jwt_identity())
        
        expenses = Expense.query.filter(
            and_(
                Expense.user_id == user_id,
                Expense.is_reimbursable == True,
                Expense.reimbursement_id.is_(None)
            )
        ).order_by(desc(Expense.expense_date)).all()
        
        expenses_data = []
        for expense in expenses:
            expense_dict = expense.to_dict()
            # 添加账户信息
            if expense.account:
                expense_dict['account'] = {
                    'id': expense.account.id,
                    'name': expense.account.name,
                    'account_type': expense.account.account_type
                }
            expenses_data.append(expense_dict)
        
        return jsonify({
            'expenses': expenses_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reimbursements_bp.route('/status-options', methods=['GET'])
@jwt_required()
def get_status_options():
    """获取报销状态选项"""
    status_options = [
        {'value': 'pending', 'label': '待审核'},
        {'value': 'approved', 'label': '已通过'},
        {'value': 'rejected', 'label': '已拒绝'},
        {'value': 'paid', 'label': '已支付'}
    ]
    
    return jsonify({'status_options': status_options}), 200