from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Account, Expense, Reimbursement
from database import db
from sqlalchemy import func, and_, extract
from datetime import datetime, date, timedelta
from collections import defaultdict

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取总览统计数据"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取时间范围参数
        period = request.args.get('period', 'month')  # month, year, all
        
        # 计算时间范围
        today = date.today()
        if period == 'month':
            start_date = today.replace(day=1)
        elif period == 'year':
            start_date = today.replace(month=1, day=1)
        else:  # all
            start_date = None
        
        # 构建基础查询
        expense_query = Expense.query.filter_by(user_id=user_id)
        if start_date:
            expense_query = expense_query.filter(Expense.expense_date >= start_date)
        
        # 总支出
        total_expenses = expense_query.filter_by(expense_type='expense').with_entities(
            func.sum(Expense.amount)
        ).scalar() or 0
        
        # 总收入
        total_income = expense_query.filter_by(expense_type='income').with_entities(
            func.sum(Expense.amount)
        ).scalar() or 0
        
        # 净收入
        net_income = total_income - total_expenses
        
        # 账户总余额
        total_balance = Account.query.filter_by(
            user_id=user_id,
            is_active=True
        ).with_entities(
            func.sum(Account.balance)
        ).scalar() or 0
        
        # 交易笔数
        transaction_count = expense_query.count()
        
        # 报销统计
        reimbursement_stats = db.session.query(
            Reimbursement.status,
            func.count(Reimbursement.id).label('count'),
            func.sum(Reimbursement.total_amount).label('amount')
        ).filter_by(user_id=user_id).group_by(Reimbursement.status).all()
        
        reimbursement_summary = {
            'pending': {'count': 0, 'amount': 0},
            'approved': {'count': 0, 'amount': 0},
            'rejected': {'count': 0, 'amount': 0},
            'paid': {'count': 0, 'amount': 0}
        }
        
        for status, count, amount in reimbursement_stats:
            reimbursement_summary[status] = {
                'count': count,
                'amount': float(amount or 0)
            }
        
        return jsonify({
            'period': period,
            'total_expenses': float(total_expenses),
            'total_income': float(total_income),
            'net_income': float(net_income),
            'total_balance': float(total_balance),
            'transaction_count': transaction_count,
            'reimbursement_summary': reimbursement_summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistics_bp.route('/category-analysis', methods=['GET'])
@jwt_required()
def get_category_analysis():
    """获取分类分析数据"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取时间范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        expense_type = request.args.get('type', 'expense')
        
        # 构建查询
        query = Expense.query.filter_by(
            user_id=user_id,
            expense_type=expense_type
        )
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date >= start_date_obj)
            except ValueError:
                return jsonify({'error': '开始日期格式错误'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Expense.expense_date <= end_date_obj)
            except ValueError:
                return jsonify({'error': '结束日期格式错误'}), 400
        
        # 按分类统计
        category_stats = query.with_entities(
            Expense.category,
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).group_by(Expense.category).order_by(
            func.sum(Expense.amount).desc()
        ).all()
        
        categories = []
        total_amount = 0
        
        for category, amount, count in category_stats:
            amount_float = float(amount)
            total_amount += amount_float
            categories.append({
                'category': category,
                'amount': amount_float,
                'count': count,
                'percentage': 0  # 稍后计算
            })
        
        # 计算百分比
        for category_data in categories:
            if total_amount > 0:
                category_data['percentage'] = round(
                    (category_data['amount'] / total_amount) * 100, 2
                )
        
        return jsonify({
            'categories': categories,
            'total_amount': total_amount,
            'expense_type': expense_type
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistics_bp.route('/trend-analysis', methods=['GET'])
@jwt_required()
def get_trend_analysis():
    """获取趋势分析数据"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取查询参数
        period = request.args.get('period', 'month')  # day, month, year
        months = int(request.args.get('months', 12))  # 显示多少个月的数据
        
        # 计算时间范围
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        # 构建查询
        query = Expense.query.filter(
            and_(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        )
        
        if period == 'day':
            # 按天统计
            trend_data = query.with_entities(
                Expense.expense_date,
                Expense.expense_type,
                func.sum(Expense.amount).label('amount')
            ).group_by(
                Expense.expense_date,
                Expense.expense_type
            ).order_by(Expense.expense_date).all()
        elif period == 'month':
            # 按月统计
            trend_data = query.with_entities(
                extract('year', Expense.expense_date).label('year'),
                extract('month', Expense.expense_date).label('month'),
                Expense.expense_type,
                func.sum(Expense.amount).label('amount')
            ).group_by(
                extract('year', Expense.expense_date),
                extract('month', Expense.expense_date),
                Expense.expense_type
            ).order_by('year', 'month').all()
        else:  # year
            # 按年统计
            trend_data = query.with_entities(
                extract('year', Expense.expense_date).label('year'),
                Expense.expense_type,
                func.sum(Expense.amount).label('amount')
            ).group_by(
                extract('year', Expense.expense_date),
                Expense.expense_type
            ).order_by('year').all()
        
        # 处理数据
        trend_dict = defaultdict(lambda: {'income': 0, 'expense': 0})
        
        for row in trend_data:
            if period == 'day':
                key = row[0].isoformat()
                expense_type = row[1]
                amount = float(row[2])
            elif period == 'month':
                key = f"{int(row[0])}-{int(row[1]):02d}"
                expense_type = row[2]
                amount = float(row[3])
            else:  # year
                key = str(int(row[0]))
                expense_type = row[1]
                amount = float(row[2])
            
            trend_dict[key][expense_type] = amount
        
        # 转换为列表格式
        trend_list = []
        for key in sorted(trend_dict.keys()):
            data = trend_dict[key]
            trend_list.append({
                'period': key,
                'income': data['income'],
                'expense': data['expense'],
                'net': data['income'] - data['expense']
            })
        
        return jsonify({
            'trend': trend_list,
            'period_type': period
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistics_bp.route('/account-analysis', methods=['GET'])
@jwt_required()
def get_account_analysis():
    """获取账户分析数据"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取所有活跃账户
        accounts = Account.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        account_data = []
        total_balance = 0
        
        for account in accounts:
            balance = float(account.balance)
            total_balance += balance
            
            # 获取该账户的交易统计
            expense_count = Expense.query.filter_by(
                user_id=user_id,
                account_id=account.id
            ).count()
            
            account_data.append({
                'id': account.id,
                'name': account.name,
                'account_type': account.account_type,
                'balance': balance,
                'transaction_count': expense_count,
                'percentage': 0  # 稍后计算
            })
        
        # 计算百分比
        for account in account_data:
            if total_balance != 0:
                account['percentage'] = round(
                    (account['balance'] / total_balance) * 100, 2
                )
        
        # 按余额排序
        account_data.sort(key=lambda x: x['balance'], reverse=True)
        
        return jsonify({
            'accounts': account_data,
            'total_balance': total_balance
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@statistics_bp.route('/monthly-summary', methods=['GET'])
@jwt_required()
def get_monthly_summary():
    """获取月度汇总数据"""
    try:
        user_id = int(get_jwt_identity())
        
        # 获取参数
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
        
        # 计算月份的开始和结束日期
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # 基础查询
        base_query = Expense.query.filter(
            and_(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date <= end_date
            )
        )
        
        # 收入支出统计
        income_total = base_query.filter_by(expense_type='income').with_entities(
            func.sum(Expense.amount)
        ).scalar() or 0
        
        expense_total = base_query.filter_by(expense_type='expense').with_entities(
            func.sum(Expense.amount)
        ).scalar() or 0
        
        # 按分类统计支出
        category_expenses = base_query.filter_by(expense_type='expense').with_entities(
            Expense.category,
            func.sum(Expense.amount).label('amount')
        ).group_by(Expense.category).order_by(
            func.sum(Expense.amount).desc()
        ).all()
        
        # 按日统计
        daily_stats = base_query.with_entities(
            Expense.expense_date,
            Expense.expense_type,
            func.sum(Expense.amount).label('amount')
        ).group_by(
            Expense.expense_date,
            Expense.expense_type
        ).order_by(Expense.expense_date).all()
        
        # 处理每日数据
        daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})
        for expense_date, expense_type, amount in daily_stats:
            daily_data[expense_date.isoformat()][expense_type] = float(amount)
        
        daily_list = []
        for day_str in sorted(daily_data.keys()):
            data = daily_data[day_str]
            daily_list.append({
                'date': day_str,
                'income': data['income'],
                'expense': data['expense'],
                'net': data['income'] - data['expense']
            })
        
        return jsonify({
            'year': year,
            'month': month,
            'summary': {
                'total_income': float(income_total),
                'total_expense': float(expense_total),
                'net_income': float(income_total - expense_total)
            },
            'category_expenses': [
                {'category': cat, 'amount': float(amount)}
                for cat, amount in category_expenses
            ],
            'daily_data': daily_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500