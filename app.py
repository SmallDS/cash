from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime
import os
from dotenv import load_dotenv
from database import db, init_db

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///cash_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))

# 初始化扩展
init_db(app)
jwt = JWTManager(app)
CORS(app)

# 路由
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': os.getenv('APP_VERSION', '1.0.0')
    })

# 导入API路由
from api.auth import auth_bp
from api.accounts import accounts_bp
from api.expenses import expenses_bp
from api.reimbursements import reimbursements_bp
from api.statistics import statistics_bp
from api.categories import categories_bp

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
app.register_blueprint(reimbursements_bp, url_prefix='/api/reimbursements')
app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
app.register_blueprint(categories_bp, url_prefix='/api/categories')

# 模型已在database.py中初始化

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)