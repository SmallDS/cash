# 个人记账报销系统

一个简单易用的个人记账报销管理系统，支持移动端和PC端，使用SQLite数据库存储，支持Docker部署。

## 功能特性

### 核心功能
- 📊 **记账管理** - 支持收入和支出记录，多种分类管理
- 💰 **账户管理** - 多账户支持（现金、银行卡、支付宝等）
- 📋 **报销管理** - 报销申请、审批流程管理
- 📈 **数据统计** - 收支分析、趋势图表、分类统计
- 👤 **用户管理** - 用户注册、登录、个人资料管理

### 技术特性
- 🌐 **响应式设计** - 完美适配移动端和PC端
- 🗄️ **SQLite数据库** - 轻量级、无需额外配置
- 🐳 **Docker支持** - 一键部署，环境隔离
- 🚀 **CI/CD集成** - GitHub Actions自动构建镜像
- 🔐 **安全认证** - JWT令牌认证，密码加密存储

## 技术栈

### 后端
- **Python 3.11+**
- **Flask** - Web框架
- **SQLAlchemy** - ORM数据库操作
- **Flask-JWT-Extended** - JWT认证
- **Gunicorn** - WSGI服务器

### 前端
- **HTML5/CSS3/JavaScript**
- **Bootstrap 5** - UI框架
- **Chart.js** - 图表库
- **响应式设计** - 移动端适配

### 数据库
- **SQLite** - 轻量级关系数据库

### 部署
- **Docker** - 容器化部署
- **GitHub Actions** - CI/CD自动化

## 快速开始

### 方式一：Docker部署（推荐）

1. **克隆项目**
```bash
git clone https://github.com/SmallDS/cash.git
cd cash
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，修改密钥等配置
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问应用**
打开浏览器访问：http://localhost:5000

### 方式二：本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **初始化数据库**
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

4. **启动应用**
```bash
python app.py
```

## 使用说明

### 首次使用

1. **注册账户**
   - 访问系统首页
   - 点击"注册"按钮
   - 填写用户信息完成注册

2. **登录系统**
   - 使用注册的用户名和密码登录

3. **创建账户**
   - 进入"账户管理"页面
   - 添加您的银行卡、现金等账户

### 日常使用

#### 记账功能
- **添加收入**：记录工资、奖金等收入
- **添加支出**：记录日常消费、购物等支出
- **分类管理**：按餐饮、交通、购物等分类整理

#### 报销功能
- **创建报销申请**：选择相关支出记录创建报销
- **审批管理**：审批或拒绝报销申请
- **状态跟踪**：查看报销申请的处理状态

#### 数据分析
- **收支概览**：查看总体收支情况
- **分类分析**：了解各类支出占比
- **趋势分析**：查看收支变化趋势

## API文档

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/profile` - 获取用户信息
- `PUT /api/auth/profile` - 更新用户信息

### 账户管理
- `GET /api/accounts/` - 获取账户列表
- `POST /api/accounts/` - 创建账户
- `GET /api/accounts/<id>` - 获取账户详情
- `PUT /api/accounts/<id>` - 更新账户
- `DELETE /api/accounts/<id>` - 删除账户

### 支出管理
- `GET /api/expenses/` - 获取支出列表
- `POST /api/expenses/` - 创建支出记录
- `GET /api/expenses/<id>` - 获取支出详情
- `PUT /api/expenses/<id>` - 更新支出记录
- `DELETE /api/expenses/<id>` - 删除支出记录

### 报销管理
- `GET /api/reimbursements/` - 获取报销列表
- `POST /api/reimbursements/` - 创建报销申请
- `GET /api/reimbursements/<id>` - 获取报销详情
- `PUT /api/reimbursements/<id>` - 更新报销申请
- `POST /api/reimbursements/<id>/approve` - 审批报销

### 统计分析
- `GET /api/statistics/overview` - 获取概览统计
- `GET /api/statistics/category-analysis` - 分类分析
- `GET /api/statistics/trend-analysis` - 趋势分析

## 部署配置

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Flask密钥 | 需要修改 |
| `JWT_SECRET_KEY` | JWT密钥 | 需要修改 |
| `DATABASE_URL` | 数据库连接 | `sqlite:///data/cash_system.db` |
| `FLASK_ENV` | 运行环境 | `production` |
| `PORT` | 服务端口 | `5000` |

### Docker配置

**Dockerfile特性：**
- 基于Python 3.11-slim镜像
- 多阶段构建优化镜像大小
- 非root用户运行提升安全性
- 健康检查确保服务可用性

**docker-compose.yml特性：**
- 数据持久化存储
- 自动重启策略
- 健康检查配置
- 网络隔离

### GitHub Actions CI/CD

自动化流程包括：
1. **代码检查** - 语法检查和代码质量
2. **测试运行** - 自动化测试（可扩展）
3. **镜像构建** - 多架构Docker镜像
4. **安全扫描** - 漏洞扫描
5. **镜像发布** - 推送到GitHub Container Registry

## 开发指南

### 项目结构
```
cash/
├── app.py                 # 应用入口
├── models.py              # 数据模型
├── requirements.txt       # Python依赖
├── .env                   # 环境配置
├── api/                   # API接口
│   ├── __init__.py
│   ├── auth.py           # 认证接口
│   ├── accounts.py       # 账户管理
│   ├── expenses.py       # 支出管理
│   ├── reimbursements.py # 报销管理
│   └── statistics.py     # 统计分析
├── templates/             # HTML模板
│   └── index.html
├── static/                # 静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── Dockerfile             # Docker配置
├── docker-compose.yml     # Docker编排
├── .github/workflows/     # GitHub Actions
└── README.md              # 项目文档
```

### 本地开发

1. **设置开发环境**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

2. **配置开发环境**
```bash
cp .env.example .env
# 修改 FLASK_ENV=development
```

3. **运行开发服务器**
```bash
flask run --debug
```

### 添加新功能

1. **数据模型** - 在 `models.py` 中定义新的数据表
2. **API接口** - 在 `api/` 目录下创建新的接口文件
3. **前端页面** - 在 `templates/` 和 `static/` 中添加页面和样式
4. **注册路由** - 在 `app.py` 中注册新的蓝图

## 常见问题

### Q: 如何备份数据？
A: SQLite数据库文件位于 `data/cash_system.db`，直接复制该文件即可备份。

### Q: 如何修改端口？
A: 修改 `.env` 文件中的 `PORT` 变量，或修改 `docker-compose.yml` 中的端口映射。

### Q: 如何重置密码？
A: 目前需要直接操作数据库，后续版本将添加密码重置功能。

### Q: 支持多用户吗？
A: 是的，系统支持多用户注册和使用，每个用户的数据完全隔离。

### Q: 如何升级系统？
A: 使用Docker部署时，拉取最新镜像并重启容器即可：
```bash
docker-compose pull
docker-compose up -d
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0 (2024-01-20)
- ✨ 初始版本发布
- 📊 基础记账功能
- 💰 账户管理
- 📋 报销管理
- 📈 数据统计
- 🐳 Docker支持
- 🚀 GitHub Actions CI/CD

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](../../issues)
- 发送邮件到：[smallds@example.com]

---

**感谢使用个人记账报销系统！** 🎉