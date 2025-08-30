// 全局变量
let currentUser = null;
let authToken = null;
let currentPage = 'login';

// API 基础配置
const API_BASE = '/api';
const ENDPOINTS = {
    auth: {
        login: `${API_BASE}/auth/login`,
        register: `${API_BASE}/auth/register`,
        profile: `${API_BASE}/auth/profile`
    },
    accounts: {
        list: `${API_BASE}/accounts/`,
        create: `${API_BASE}/accounts/`,
        types: `${API_BASE}/accounts/types`
    },
    expenses: {
        list: `${API_BASE}/expenses/`,
        create: `${API_BASE}/expenses/`,
        categories: `${API_BASE}/expenses/categories`
    },
    reimbursements: {
        list: `${API_BASE}/reimbursements/`,
        create: `${API_BASE}/reimbursements/`,
        available: `${API_BASE}/reimbursements/available-expenses`
    },
    categories: {
        list: `${API_BASE}/categories/`,
        create: `${API_BASE}/categories/`,
        initDefault: `${API_BASE}/categories/init-default`
    },
    statistics: {
        overview: `${API_BASE}/statistics/overview`,
        category: `${API_BASE}/statistics/category-analysis`,
        trend: `${API_BASE}/statistics/trend-analysis`,
        account: `${API_BASE}/statistics/account-analysis`,
        monthly: `${API_BASE}/statistics/monthly-summary`
    }
};

// 工具函数
class Utils {
    // 分类映射表
    static categoryMap = {
        'food': '餐饮',
        'transport': '交通',
        'shopping': '购物',
        'entertainment': '娱乐',
        'healthcare': '医疗',
        'education': '教育',
        'housing': '住房',
        'utilities': '水电费',
        'communication': '通讯',
        'insurance': '保险',
        'investment': '投资',
        'salary': '工资',
        'bonus': '奖金',
        'other': '其他'
    };

    // 获取分类中文名称
    static getCategoryLabel(value) {
        return this.categoryMap[value] || value;
    }

    // 格式化金额
    static formatCurrency(amount) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'CNY'
        }).format(amount);
    }

    // 格式化日期
    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN');
    }

    // 格式化日期时间
    static formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    }

    // 获取今天的日期字符串
    static getTodayString() {
        const today = new Date();
        return today.toISOString().split('T')[0];
    }

    // 防抖函数
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 显示加载状态
    static showLoading() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    // 隐藏加载状态
    static hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

// Toast 通知类
class Toast {
    static show(message, type = 'info', title = '通知') {
        const toastElement = document.getElementById('toast');
        const toastTitle = document.getElementById('toastTitle');
        const toastBody = document.getElementById('toastBody');

        // 设置内容
        toastTitle.textContent = title;
        toastBody.textContent = message;

        // 设置样式
        toastElement.className = `toast toast-${type}`;

        // 显示 Toast
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }

    static success(message, title = '成功') {
        this.show(message, 'success', title);
    }

    static error(message, title = '错误') {
        this.show(message, 'error', title);
    }

    static warning(message, title = '警告') {
        this.show(message, 'warning', title);
    }

    static info(message, title = '信息') {
        this.show(message, 'info', title);
    }
}

// API 请求类
class API {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        // 添加认证头
        if (authToken) {
            defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
        }

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, finalOptions);

            if (response.status === 401) {
                Auth.logout();
                throw new Error('登录已过期，请重新登录');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            // 显示错误信息给用户
            Toast.error(error.message || '请求失败，请稍后重试');
            throw error;
        }
    }

    static async get(url, params = {}) {
        const urlParams = new URLSearchParams(params);
        const fullUrl = urlParams.toString() ? `${url}?${urlParams}` : url;
        return this.request(fullUrl);
    }

    static async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
}

// 认证管理类
class Auth {
    static init() {
        // 从 localStorage 恢复登录状态
        const savedToken = localStorage.getItem('authToken');
        const savedUser = localStorage.getItem('currentUser');

        if (savedToken && savedUser) {
            authToken = savedToken;
            currentUser = JSON.parse(savedUser);
            this.updateUI(true);
            PageManager.showPage('dashboard');
        } else {
            this.updateUI(false);
            PageManager.showPage('login');
        }
    }

    static async login(username, password) {
        try {
            Utils.showLoading();
            const response = await API.post(ENDPOINTS.auth.login, {
                username,
                password
            });

            authToken = response.access_token;
            currentUser = response.user;

            // 保存到 localStorage
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            this.updateUI(true);
            PageManager.showPage('dashboard');
            Toast.success('登录成功');

            return response;
        } catch (error) {
            console.error('登录失败:', error);
            throw error;
        } finally {
            Utils.hideLoading();
        }
    }

    static async register(userData) {
        try {
            Utils.showLoading();
            const response = await API.post(ENDPOINTS.auth.register, userData);
            Toast.success('注册成功，请登录');
            PageManager.showPage('login');
            return response;
        } catch (error) {
            console.error('注册失败:', error);
            throw error;
        } finally {
            Utils.hideLoading();
        }
    }

    static logout() {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        this.updateUI(false);
        PageManager.showPage('login');
        Toast.info('已退出登录');
    }

    static updateUI(isLoggedIn) {
        const loginBtn = document.getElementById('loginBtn');
        const userInfo = document.getElementById('userInfo');
        const profileBtn = document.getElementById('profileBtn');
        const logoutBtnNav = document.getElementById('logoutBtnNav');
        const userName = document.getElementById('userName');
        const navbarNav = document.querySelector('.navbar-nav.me-auto');


        if (isLoggedIn && currentUser) {
            loginBtn.style.display = 'none';
            userInfo.style.display = 'block';
            profileBtn.style.display = 'block';
            logoutBtnNav.style.display = 'block';
            userName.textContent = currentUser.name;
            if (navbarNav) navbarNav.style.display = 'flex';

        } else {
            loginBtn.style.display = 'block';
            userInfo.style.display = 'none';
            profileBtn.style.display = 'none';
            logoutBtnNav.style.display = 'none';
            if (navbarNav) navbarNav.style.display = 'none';

        }
    }
}

// 页面管理类
class PageManager {
    static showPage(pageName) {
        // 检查权限：未登录用户只能访问登录和注册页面
        const publicPages = ['login', 'register'];
        if (!authToken && !publicPages.includes(pageName)) {
            Toast.warning('请先登录');
            pageName = 'login';
        }

        // 隐藏所有页面
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.style.display = 'none';
        });

        // 显示目标页面
        const targetPage = document.getElementById(`${pageName}Page`);
        if (targetPage) {
            targetPage.style.display = 'block';
            currentPage = pageName;
        }

        // 更新导航状态
        this.updateNavigation(pageName);

        // 加载页面数据
        this.loadPageData(pageName);
    }

    static updateNavigation(activePage) {
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.page === activePage) {
                link.classList.add('active');
                // 添加活跃状态动画
                link.style.animation = 'none';
                setTimeout(() => {
                    link.style.animation = 'navLinkActive 0.3s ease';
                }, 10);
            }
        });

        // 更新页面标题
        this.updatePageTitle(activePage);


    }

    static updatePageTitle(pageName) {
        const pageTitles = {
            'dashboard': '首页 - 记账报销系统',
            'accounts': '账户管理 - 记账报销系统',
            'expenses': '收支记录 - 记账报销系统',
            'reimbursements': '报销管理 - 记账报销系统',
            'statistics': '统计分析 - 记账报销系统',
            'profile': '个人信息 - 记账报销系统',
            'login': '登录 - 记账报销系统'
        };
        document.title = pageTitles[pageName] || '记账报销系统';
    }



    static async loadPageData(pageName) {
        if (!authToken && pageName !== 'login' && pageName !== 'register') {
            return;
        }

        try {
            switch (pageName) {
                case 'dashboard':
                    await Dashboard.load();
                    break;
                case 'accounts':
                    await AccountManager.load();
                    break;
                case 'expenses':
                    await ExpenseManager.load();
                    break;
                case 'reimbursements':
                    await ReimbursementManager.load();
                    break;
                case 'statistics':
                    await StatisticsManager.load();
                    break;
                case 'profile':
                    await ProfileManager.load();
                    break;
                case 'categories':
                    await CategoryManager.load();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${pageName} page:`, error);
        }
    }
}

// 仪表板类
class Dashboard {
    static async load() {
        try {
            // 加载概览数据
            const overview = await API.get(ENDPOINTS.statistics.overview, { period: 'month' });
            this.updateOverviewCards(overview);

            // 加载最近交易
            const expenses = await API.get(ENDPOINTS.expenses.list, { per_page: 5 });
            this.updateRecentTransactions(expenses.expenses);

            // 加载分类图表
            const categoryData = await API.get(ENDPOINTS.statistics.category, {
                type: 'expense',
                start_date: Utils.getTodayString().substring(0, 8) + '01' // 本月第一天
            });
            this.updateCategoryChart(categoryData.categories);

        } catch (error) {
            console.error('Dashboard load error:', error);
        }
    }

    static updateOverviewCards(data) {
        document.getElementById('totalBalance').textContent = Utils.formatCurrency(data.total_balance || 0);
        document.getElementById('monthlyIncome').textContent = Utils.formatCurrency(data.total_income || 0);
        document.getElementById('monthlyExpense').textContent = Utils.formatCurrency(data.total_expenses || 0);
        document.getElementById('pendingReimbursements').textContent = data.reimbursement_summary?.pending?.count || 0;
    }

    static updateRecentTransactions(transactions) {
        const container = document.getElementById('recentTransactions');

        if (!transactions || transactions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-receipt empty-icon"></i>
                    <div class="empty-title">暂无交易记录</div>
                    <div class="empty-description">开始记录您的第一笔交易吧</div>
                </div>
            `;
            return;
        }

        const transactionsList = transactions.map(transaction => {
            const amountClass = transaction.expense_type === 'income' ? 'amount-positive' : 'amount-negative';
            const icon = transaction.expense_type === 'income' ? 'arrow-up-circle' : 'arrow-down-circle';

            return `
                <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-${icon} me-2 ${amountClass}"></i>
                        <div>
                            <div class="fw-medium">${transaction.description || transaction.category}</div>
                            <small class="text-muted">${Utils.formatDate(transaction.expense_date)}</small>
                        </div>
                    </div>
                    <div class="${amountClass}">
                        ${transaction.expense_type === 'income' ? '+' : '-'}${Utils.formatCurrency(Math.abs(transaction.amount))}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = transactionsList;
    }

    static updateCategoryChart(categories) {
        const canvas = document.getElementById('categoryChart');
        const ctx = canvas.getContext('2d');

        // 清除之前的图表
        if (window.categoryChartInstance) {
            window.categoryChartInstance.destroy();
        }

        if (!categories || categories.length === 0) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '16px Arial';
            ctx.fillStyle = '#6c757d';
            ctx.textAlign = 'center';
            ctx.fillText('暂无数据', canvas.width / 2, canvas.height / 2);
            return;
        }

        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
        ];

        window.categoryChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categories.map(cat => cat.category),
                datasets: [{
                    data: categories.map(cat => cat.amount),
                    backgroundColor: colors.slice(0, categories.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }
}

// 账户管理类
class AccountManager {
    static async load() {
        try {
            const response = await API.get(ENDPOINTS.accounts.list);
            const accounts = response.accounts || [];
            this.updateAccountStats(accounts);
            this.updateAccountList(accounts);
            this.loadAccountOptions();
        } catch (error) {
            console.error('AccountManager.load error:', error);
        }
    }

    static updateAccountStats(accounts) {
        const totalBalance = accounts.reduce((sum, acc) => sum + parseFloat(acc.balance), 0);
        const accountCount = accounts.length;
        const activeCount = accounts.filter(acc => acc.is_active).length;

        const totalBalanceEl = document.getElementById('accountsTotalBalance');
        const accountCountEl = document.getElementById('accountsCount');
        const activeCountEl = document.getElementById('activeAccountsCount');

        if (totalBalanceEl) totalBalanceEl.textContent = Utils.formatCurrency(totalBalance);
        if (accountCountEl) accountCountEl.textContent = accountCount;
        if (activeCountEl) activeCountEl.textContent = activeCount;
    }

    static updateAccountList(accounts) {
        const container = document.getElementById('accountsList');
        if (!container) return;

        container.innerHTML = accounts.map(account => `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">${account.name}</h6>
                            <span class="badge bg-secondary">${this.getAccountTypeText(account.account_type)}</span>
                        </div>
                        <p class="card-text text-muted small">${account.description || '无描述'}</p>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="h5 mb-0 ${parseFloat(account.balance) >= 0 ? 'text-success' : 'text-danger'}">
                                ${Utils.formatCurrency(account.balance)}
                            </span>
                            <small class="text-muted">${Utils.formatDate(account.created_at)}</small>
                        </div>
                        <div class="btn-group" role="group">
                            <button class="btn btn-sm btn-outline-primary" onclick="AccountManager.editAccount(${account.id})" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="AccountManager.deleteAccount(${account.id}, '${account.name}')" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    static getAccountTypeText(type) {
        const types = {
            'cash': '现金',
            'bank_card': '银行卡',
            'credit_card': '信用卡',
            'alipay': '支付宝',
            'wechat_pay': '微信支付',
            'other': '其他'
        };
        return types[type] || type;
    }

    static async loadAccountOptions() {
        try {
            const response = await API.get(ENDPOINTS.accounts.list);
            const accounts = response.accounts || [];
            const selects = document.querySelectorAll('#expenseAccount, #editExpenseAccount, #reimbursementAccount');

            selects.forEach(select => {
                select.innerHTML = '<option value="">请选择账户</option>' +
                    accounts.map(acc => `<option value="${acc.id}">${acc.name}</option>`).join('');
            });
        } catch (error) {
            console.error('加载账户选项失败:', error);
        }
    }

    static async saveAccount(formData) {
        try {
            console.log('提交的账户数据:', formData);
            await API.post(ENDPOINTS.accounts.create, formData);
            Toast.success('账户添加成功');
            this.load();
            return true;
        } catch (error) {
            console.error('添加账户失败:', error);
            return false;
        }
    }

    static async editAccount(accountId) {
        try {
            const response = await API.get(`${ENDPOINTS.accounts.list}${accountId}`);
            const account = response.account;

            // 填充编辑表单
            document.getElementById('editAccountId').value = account.id;
            document.getElementById('editAccountName').value = account.name;
            document.getElementById('editAccountType').value = account.account_type;
            document.getElementById('editAccountBalance').value = account.balance;
            document.getElementById('editAccountDescription').value = account.description || '';

            // 显示编辑模态框
            const modal = new bootstrap.Modal(document.getElementById('editAccountModal'));
            modal.show();
        } catch (error) {
            console.error('获取账户信息失败:', error);
        }
    }

    static async updateAccount(formData) {
        try {
            const accountId = formData.get('id');
            await API.put(`${ENDPOINTS.accounts.list}${accountId}`, Object.fromEntries(formData));
            Toast.success('账户更新成功');
            this.load();
            return true;
        } catch (error) {
            console.error('更新账户失败:', error);
            return false;
        }
    }

    static async deleteAccount(accountId, accountName) {
        if (!confirm(`确定要删除账户 "${accountName}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            await API.delete(`${ENDPOINTS.accounts.list}${accountId}`);
            Toast.success('账户删除成功');
            this.load();
        } catch (error) {
            console.error('删除账户失败:', error);
        }
    }
}

// 收支记录管理类
class ExpenseManager {
    static async load(filters = {}) {
        try {
            const response = await API.get(ENDPOINTS.expenses.list, filters);
            const expenses = response.expenses || [];
            this.updateExpenseList(expenses);
            this.loadExpenseCategories();
            // 加载账户选项到下拉框
            AccountManager.loadAccountOptions();
        } catch (error) {
            console.error('加载收支记录失败:', error);
        }
    }

    static applyFilters() {
        const typeEl = document.getElementById('expenseTypeFilter');
        const categoryEl = document.getElementById('expenseCategoryFilter');
        const startDateEl = document.getElementById('expenseStartDate');
        const endDateEl = document.getElementById('expenseEndDate');
        const searchEl = document.getElementById('expenseSearch');

        const filters = {};
        if (typeEl && typeEl.value) filters.type = typeEl.value;
        if (categoryEl && categoryEl.value) filters.category = categoryEl.value;
        if (startDateEl && startDateEl.value) filters.start_date = startDateEl.value;
        if (endDateEl && endDateEl.value) filters.end_date = endDateEl.value;
        if (searchEl && searchEl.value) filters.search = searchEl.value;

        this.load(filters);
    }

    static resetFilters() {
        const typeEl = document.getElementById('expenseTypeFilter');
        const categoryEl = document.getElementById('expenseCategoryFilter');
        const startDateEl = document.getElementById('expenseStartDate');
        const endDateEl = document.getElementById('expenseEndDate');
        const searchEl = document.getElementById('expenseSearch');

        if (typeEl) typeEl.value = '';
        if (categoryEl) categoryEl.value = '';
        if (startDateEl) startDateEl.value = '';
        if (endDateEl) endDateEl.value = '';
        if (searchEl) searchEl.value = '';
        this.load();
    }

    static updateExpenseList(expenses) {
        const container = document.getElementById('expensesList');
        if (!container) return;

        container.innerHTML = expenses.map(expense => `
            <div class="col-12">
                <div class="card mb-2">
                    <div class="card-body py-2">
                        <div class="row align-items-center">
                            <div class="col-md-2">
                                <span class="${expense.expense_type === 'income' ? 'text-success' : 'text-danger'}">
                                    ${expense.expense_type === 'income' ? '+' : '-'}${Utils.formatCurrency(expense.amount)}
                                </span>
                            </div>
                            <div class="col-md-2">
                                <span class="badge ${expense.expense_type === 'income' ? 'bg-success' : 'bg-danger'}">
                                    ${Utils.getCategoryLabel(expense.category)}
                                </span>
                            </div>
                            <div class="col-md-2">
                                <small class="text-muted">${expense.account ? expense.account.name : '未知账户'}</small>
                            </div>
                            <div class="col-md-2">
                                <small class="text-muted">${Utils.formatDate(expense.expense_date)}</small>
                            </div>
                            <div class="col-md-2">
                                <small class="text-muted">${expense.description || '无描述'}</small>
                            </div>
                            <div class="col-md-2">
                                <div class="btn-group" role="group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="ExpenseManager.editExpense(${expense.id})" title="编辑">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="ExpenseManager.deleteExpense(${expense.id}, '${(expense.description || '收支记录').replace(/'/g, '\\\'')}')" title="删除">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                    ${expense.expense_type === 'expense' && !expense.is_reimbursed ?
                `<button class="btn btn-sm btn-outline-success" onclick="ExpenseManager.createReimbursement(${expense.id})" title="报销">
                                            <i class="bi bi-receipt"></i>
                                        </button>` :
                expense.is_reimbursed ? '<span class="badge bg-info ms-1">已报销</span>' : ''
            }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    static async loadExpenseCategories() {
        try {
            const response = await API.get(ENDPOINTS.expenses.categories);
            const categories = response.categories || [];
            const select = document.getElementById('expenseCategory');
            if (select) {
                select.innerHTML = '<option value="">请选择分类</option>' +
                    categories.map(cat => `<option value="${cat.value}">${cat.label}</option>`).join('');
            }
            
            // 同时更新筛选器中的分类选项
            const filterSelect = document.getElementById('expenseCategoryFilter');
            if (filterSelect) {
                filterSelect.innerHTML = '<option value="">全部分类</option>' +
                    categories.map(cat => `<option value="${cat.value}">${cat.label}</option>`).join('');
            }
        } catch (error) {
            console.error('加载分类失败:', error);
        }
    }

    static async saveExpense(formData) {
        try {
            await API.post(ENDPOINTS.expenses.create, formData);
            Toast.success('收支记录添加成功');
            this.load();
            return true;
        } catch (error) {
            console.error('添加收支记录失败:', error);
            return false;
        }
    }

    static createReimbursement(expenseId) {
        // 打开报销申请模态框并预填支出记录
        PageManager.showPage('reimbursements');
        setTimeout(() => {
            const modal = new bootstrap.Modal(document.getElementById('addReimbursementModal'));
            document.getElementById('reimbursementExpense').value = expenseId;
            modal.show();
        }, 100);
    }

    static async editExpense(expenseId) {
        try {
            const response = await API.get(`${ENDPOINTS.expenses.list}${expenseId}`);
            const expense = response.expense;

            // 填充编辑表单
            document.getElementById('editExpenseId').value = expense.id;
            document.getElementById('editExpenseType').value = expense.expense_type;
            document.getElementById('editExpenseAmount').value = expense.amount;
            document.getElementById('editExpenseCategory').value = expense.category;
            document.getElementById('editExpenseAccount').value = expense.account_id;
            document.getElementById('editExpenseDate').value = expense.expense_date;
            document.getElementById('editExpenseDescription').value = expense.description || '';

            // 更新模态框标题
            document.getElementById('editExpenseModalTitle').textContent =
                expense.expense_type === 'income' ? '编辑收入记录' : '编辑支出记录';

            // 显示编辑模态框
            const modal = new bootstrap.Modal(document.getElementById('editExpenseModal'));
            modal.show();
        } catch (error) {
            console.error('获取收支记录信息失败:', error);
        }
    }

    static async updateExpense(formData) {
        try {
            const expenseId = formData.get('id');
            await API.put(`${ENDPOINTS.expenses.list}${expenseId}`, Object.fromEntries(formData));
            Toast.success('收支记录更新成功');
            this.load();
            return true;
        } catch (error) {
            console.error('更新收支记录失败:', error);
            return false;
        }
    }

    static async deleteExpense(expenseId, description) {
        if (!confirm(`确定要删除收支记录 "${description}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            await API.delete(`${ENDPOINTS.expenses.list}${expenseId}`);
            Toast.success('收支记录删除成功');
            this.load();
        } catch (error) {
            console.error('删除收支记录失败:', error);
        }
    }
}

// 报销管理类
class ReimbursementManager {
    static async load(filters = {}) {
        try {
            const response = await API.get(ENDPOINTS.reimbursements.list, filters);
            const reimbursements = response.reimbursements || [];
            this.updateReimbursementStats(reimbursements);
            this.updateReimbursementList(reimbursements);
            this.loadAvailableExpenses();
        } catch (error) {
            console.error('ReimbursementManager.load error:', error);
        }
    }

    static applyFilters() {
        const statusEl = document.getElementById('reimbursementStatusFilter');
        const startDateEl = document.getElementById('reimbursementStartDate');
        const endDateEl = document.getElementById('reimbursementEndDate');
        const searchEl = document.getElementById('reimbursementSearch');

        const filters = {};
        if (statusEl && statusEl.value) filters.status = statusEl.value;
        if (startDateEl && startDateEl.value) filters.start_date = startDateEl.value;
        if (endDateEl && endDateEl.value) filters.end_date = endDateEl.value;
        if (searchEl && searchEl.value) filters.search = searchEl.value;

        this.load(filters);
    }

    static resetFilters() {
        const statusEl = document.getElementById('reimbursementStatusFilter');
        const startDateEl = document.getElementById('reimbursementStartDate');
        const endDateEl = document.getElementById('reimbursementEndDate');
        const searchEl = document.getElementById('reimbursementSearch');
        
        if (statusEl) statusEl.value = '';
        if (startDateEl) startDateEl.value = '';
        if (endDateEl) endDateEl.value = '';
        if (searchEl) searchEl.value = '';
        this.load();
    }

    static updateReimbursementStats(reimbursements) {
        const totalAmount = reimbursements.reduce((sum, r) => sum + parseFloat(r.total_amount), 0);
        const pendingCount = reimbursements.filter(r => r.status === 'pending').length;
        const approvedCount = reimbursements.filter(r => r.status === 'approved').length;
        const rejectedCount = reimbursements.filter(r => r.status === 'rejected').length;

        const totalAmountEl = document.getElementById('totalReimbursementAmount');
        const pendingCountEl = document.getElementById('pendingReimbursementsCount');
        const approvedCountEl = document.getElementById('approvedReimbursementsCount');
        const rejectedCountEl = document.getElementById('rejectedReimbursementsCount');

        if (totalAmountEl) totalAmountEl.textContent = Utils.formatCurrency(totalAmount);
        if (pendingCountEl) pendingCountEl.textContent = pendingCount;
        if (approvedCountEl) approvedCountEl.textContent = approvedCount;
        if (rejectedCountEl) rejectedCountEl.textContent = rejectedCount;
    }

    static updateReimbursementList(reimbursements) {
        const container = document.getElementById('reimbursementsList');
        if (!container) return;

        container.innerHTML = reimbursements.map(reimbursement => `
            <div class="col-12">
                <div class="card mb-2">
                    <div class="card-body py-2">
                        <div class="row align-items-center">
                            <div class="col-md-2">
                                <span class="text-primary">${Utils.formatCurrency(reimbursement.total_amount)}</span>
                            </div>
                            <div class="col-md-2">
                                <span class="badge ${this.getStatusBadgeClass(reimbursement.status)}">
                                    ${this.getStatusText(reimbursement.status)}
                                </span>
                            </div>
                            <div class="col-md-2">
                                <small class="text-muted">${Utils.formatDate(reimbursement.created_at)}</small>
                            </div>
                            <div class="col-md-4">
                                <small class="text-muted">${reimbursement.description || reimbursement.title}</small>
                            </div>
                            <div class="col-md-2">
                                <div class="btn-group" role="group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="ReimbursementManager.editReimbursement(${reimbursement.id})" title="编辑">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="ReimbursementManager.deleteReimbursement(${reimbursement.id}, '${reimbursement.title || reimbursement.description}')" title="删除">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                    ${reimbursement.status === 'pending' ?
                `<button class="btn btn-sm btn-success" onclick="ReimbursementManager.updateStatus(${reimbursement.id}, 'approved')" title="批准">
                                            <i class="bi bi-check"></i>
                                        </button>
                                        <button class="btn btn-sm btn-danger" onclick="ReimbursementManager.updateStatus(${reimbursement.id}, 'rejected')" title="拒绝">
                                            <i class="bi bi-x"></i>
                                        </button>` :
                ''
            }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    static getStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'rejected': 'bg-danger'
        };
        return classes[status] || 'bg-secondary';
    }

    static getStatusText(status) {
        const texts = {
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝'
        };
        return texts[status] || status;
    }

    static async loadAvailableExpenses() {
        try {
            const response = await API.get(ENDPOINTS.reimbursements.available);
            const expenses = response.expenses || [];
            const select = document.getElementById('reimbursementExpense');
            if (select) {
                select.innerHTML = '<option value="">请选择可报销的支出记录</option>' +
                    expenses.map(exp => `<option value="${exp.id}" data-amount="${exp.amount}">
                        ${exp.category} - ${Utils.formatCurrency(exp.amount)} (${Utils.formatDate(exp.expense_date)})
                    </option>`).join('');
            }
        } catch (error) {
            console.error('加载可报销支出失败:', error);
        }
    }

    static async saveReimbursement(formData) {
        try {
            await API.post(ENDPOINTS.reimbursements.create, formData);
            Toast.success('报销申请提交成功');
            this.load();
            return true;
        } catch (error) {
            console.error('提交报销申请失败:', error);
            return false;
        }
    }

    static async updateStatus(id, action) {
        try {
            const actionText = action === 'approved' ? 'approve' : 'reject';
            await API.post(`${ENDPOINTS.reimbursements.list}${id}/approve`, { action: actionText });
            Toast.success(`报销申请已${action === 'approved' ? '批准' : '拒绝'}`);
            this.load();
        } catch (error) {
            console.error('审批操作失败:', error);
        }
    }

    static async editReimbursement(reimbursementId) {
        try {
            const response = await API.get(`${ENDPOINTS.reimbursements.list}${reimbursementId}`);
            const reimbursement = response.reimbursement;

            // 填充编辑表单
            document.getElementById('editReimbursementId').value = reimbursement.id;
            document.getElementById('editReimbursementTitle').value = reimbursement.title;
            document.getElementById('editReimbursementDescription').value = reimbursement.description || '';

            // 显示编辑模态框
            const modal = new bootstrap.Modal(document.getElementById('editReimbursementModal'));
            modal.show();
        } catch (error) {
            console.error('获取报销申请信息失败:', error);
        }
    }

    static async updateReimbursement(formData) {
        try {
            const reimbursementId = formData.get('id');
            await API.put(`${ENDPOINTS.reimbursements.list}${reimbursementId}`, Object.fromEntries(formData));
            Toast.success('报销申请更新成功');
            this.load();
            return true;
        } catch (error) {
            console.error('更新报销申请失败:', error);
            return false;
        }
    }

    static async deleteReimbursement(reimbursementId, title) {
        if (!confirm(`确定要删除报销申请 "${title}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            await API.delete(`${ENDPOINTS.reimbursements.list}${reimbursementId}`);
            Toast.success('报销申请删除成功');
            this.load();
        } catch (error) {
            console.error('删除报销申请失败:', error);
        }
    }
}

// 统计分析类
class StatisticsManager {
    static async load() {
        try {
            const overview = await API.get(ENDPOINTS.statistics.overview);
            this.updateOverview(overview);

            const categoryData = await API.get(ENDPOINTS.statistics.category);
            this.updateCategoryChart(categoryData.categories || []);

            const trendData = await API.get(ENDPOINTS.statistics.trend);
            this.updateTrendChart(trendData.trend || []);

            const accountData = await API.get(ENDPOINTS.statistics.account);
            this.updateExpenseRanking(accountData.accounts || []);

            const monthlyData = await API.get(ENDPOINTS.statistics.monthly);
            this.updateMonthlySummary(monthlyData);
        } catch (error) {
            console.error('StatisticsManager.load error:', error);
            // 显示空状态
            this.updateCategoryChart([]);
            this.updateTrendChart([]);
            this.updateExpenseRanking([]);
            this.updateMonthlySummary({});
        }
    }

    static updateOverview(data) {
        const totalIncomeEl = document.getElementById('statsTotalIncome');
        const totalExpenseEl = document.getElementById('statsTotalExpense');
        const netIncomeEl = document.getElementById('statsNetIncome');
        const transactionCountEl = document.getElementById('statsTransactionCount');

        if (totalIncomeEl) totalIncomeEl.textContent = Utils.formatCurrency(data.total_income || 0);
        if (totalExpenseEl) totalExpenseEl.textContent = Utils.formatCurrency(data.total_expenses || 0);
        if (netIncomeEl) netIncomeEl.textContent = Utils.formatCurrency(data.net_income || 0);
        if (transactionCountEl) transactionCountEl.textContent = data.transaction_count || 0;
    }

    static updateCategoryChart(data) {
        // 简单的文本展示，实际项目中可以使用Chart.js等图表库
        const container = document.getElementById('expenseCategoryChart');
        if (!container) return;

        if (!data || !data.length) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-pie-chart"></i>
                    <p class="mt-2 mb-0">暂无支出分类数据</p>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map(item => `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>${item.category}</span>
                <span class="text-primary">${Utils.formatCurrency(item.amount || 0)}</span>
            </div>
        `).join('');
    }

    static updateTrendChart(data) {
        // 简单的文本展示，实际项目中可以使用Chart.js等图表库
        const container = document.getElementById('trendChart');
        if (!container) return;

        if (!data || !data.length) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-bar-chart"></i>
                    <p class="mt-2 mb-0">暂无收支趋势数据</p>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map(item => `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>${item.period}</span>
                <div>
                    <span class="text-success me-2">收入: ${Utils.formatCurrency(item.income || 0)}</span>
                    <span class="text-danger">支出: ${Utils.formatCurrency(item.expense || 0)}</span>
                </div>
            </div>
        `).join('');
    }

    static updateExpenseRanking(data) {
        const container = document.getElementById('expenseRanking');
        if (!container) return;

        if (!data || !data.length) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-list-ol"></i>
                    <p class="mt-2 mb-0">暂无账户数据</p>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map((item, index) => `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span><span class="badge bg-primary me-2">${index + 1}</span>${item.name}</span>
                <span class="text-primary">${Utils.formatCurrency(item.balance || 0)}</span>
            </div>
        `).join('');
    }

    static updateMonthlySummary(data) {
        const container = document.getElementById('monthlySummary');
        if (!container) return;

        if (!data || !data.summary) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-calendar3"></i>
                    <p class="mt-2 mb-0">暂无月度数据</p>
                </div>
            `;
            return;
        }

        const summary = data.summary;
        container.innerHTML = `
            <div class="mb-3">
                <h6 class="text-muted">${data.year || new Date().getFullYear()}年${data.month || new Date().getMonth() + 1}月汇总</h6>
            </div>
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>总收入</span>
                <span class="text-success">${Utils.formatCurrency(summary.total_income || 0)}</span>
            </div>
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>总支出</span>
                <span class="text-danger">${Utils.formatCurrency(summary.total_expense || 0)}</span>
            </div>
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-bold">净收入</span>
                <span class="fw-bold ${summary.net_income >= 0 ? 'text-success' : 'text-danger'}">${Utils.formatCurrency(summary.net_income || 0)}</span>
            </div>
        `;
    }
}

// 个人信息管理类
// 导航栏增强功能类
class NavbarEnhancer {
    static init() {
        this.initScrollEffect();
        this.initKeyboardNavigation();
        this.initMobileMenuEnhancement();
        this.initSearchShortcut();
    }

    // 滚动时导航栏效果
    static initScrollEffect() {
        let lastScrollTop = 0;
        const navbar = document.querySelector('.navbar');

        window.addEventListener('scroll', Utils.debounce(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // 向下滚动，隐藏导航栏
                navbar.style.transform = 'translateY(-100%)';
            } else {
                // 向上滚动，显示导航栏
                navbar.style.transform = 'translateY(0)';
            }

            // 添加滚动时的背景模糊效果
            if (scrollTop > 50) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }

            lastScrollTop = scrollTop;
        }, 100));
    }

    // 键盘导航支持
    static initKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Alt + 数字键快速导航
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                const keyMap = {
                    '1': 'dashboard',
                    '2': 'accounts',
                    '3': 'expenses',
                    '4': 'reimbursements',
                    '5': 'statistics'
                };

                if (keyMap[e.key] && authToken) {
                    e.preventDefault();
                    PageManager.showPage(keyMap[e.key]);
                    Toast.info(`快捷键导航到: ${this.getPageName(keyMap[e.key])}`);
                }
            }

            // Escape键关闭下拉菜单
            if (e.key === 'Escape') {
                const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
                openDropdowns.forEach(dropdown => {
                    const toggle = dropdown.previousElementSibling;
                    if (toggle) {
                        bootstrap.Dropdown.getInstance(toggle)?.hide();
                    }
                });
            }
        });
    }

    // 移动端菜单增强
    static initMobileMenuEnhancement() {
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');

        if (navbarToggler && navbarCollapse) {
            // 点击菜单项后自动关闭移动端菜单
            navbarCollapse.addEventListener('click', (e) => {
                if (e.target.closest('.nav-link') && window.innerWidth < 992) {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    }
                }
            });

            // 添加菜单打开/关闭动画
            navbarCollapse.addEventListener('show.bs.collapse', () => {
                navbarToggler.classList.add('active');
            });

            navbarCollapse.addEventListener('hide.bs.collapse', () => {
                navbarToggler.classList.remove('active');
            });
        }
    }

    // 搜索快捷键
    static initSearchShortcut() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K 打开搜索（如果有搜索功能）
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                // 这里可以添加搜索功能的触发逻辑
                Toast.info('搜索功能快捷键: Ctrl+K');
            }
        });
    }

    static getPageName(page) {
        const pageNames = {
            'dashboard': '首页',
            'accounts': '账户管理',
            'expenses': '收支记录',
            'reimbursements': '报销管理',
            'statistics': '统计分析',
            'profile': '个人信息'
        };
        return pageNames[page] || page;
    }
}

class CategoryManager {
    static async load() {
        try {
            const response = await API.get(ENDPOINTS.categories.list);
            const categories = response.categories || [];
            this.updateCategoryList(categories);
        } catch (error) {
            console.error('CategoryManager.load error:', error);
        }
    }

    static updateCategoryList(categories) {
        const categoryList = document.getElementById('categoryList');
        if (!categoryList) return;

        categoryList.innerHTML = '';
        categories.forEach(category => {
            const categoryItem = document.createElement('div');
            categoryItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            categoryItem.innerHTML = `
                <div>
                    <span class="badge ${this.getCategoryTypeBadge(category.category_type)} me-2">
                        ${this.getCategoryTypeText(category.category_type)}
                    </span>
                    <span>${category.label}</span>
                    <small class="text-muted ms-2">(${category.value})</small>
                </div>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="CategoryManager.editCategory(${category.id})" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="CategoryManager.deleteCategory(${category.id}, '${category.label}')" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            categoryList.appendChild(categoryItem);
        });
    }

    static getCategoryTypeBadge(type) {
        return type === 'expense' ? 'bg-danger' : 'bg-success';
    }

    static getCategoryTypeText(type) {
        return type === 'expense' ? '支出' : '收入';
    }

    static async saveCategory(formData) {
        try {
            await API.post(ENDPOINTS.categories.create, formData);
            Toast.success('分类保存成功');
            this.load();
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
        } catch (error) {
            Toast.error('分类保存失败: ' + error.message);
        }
    }

    static async editCategory(categoryId) {
        try {
            const response = await API.get(ENDPOINTS.categories.list);
            const categories = response.categories || [];
            const category = categories.find(c => c.id === categoryId);
            if (category) {
                document.getElementById('categoryId').value = category.id;
                document.getElementById('categoryValue').value = category.value;
                document.getElementById('categoryLabel').value = category.label;
                document.getElementById('categoryType').value = category.category_type;
                document.getElementById('categoryModalTitle').textContent = '编辑分类';
                new bootstrap.Modal(document.getElementById('categoryModal')).show();
            }
        } catch (error) {
            Toast.error('加载分类信息失败: ' + error.message);
        }
    }

    static async deleteCategory(categoryId, categoryName) {
        if (confirm(`确定要删除分类 "${categoryName}" 吗？`)) {
            try {
                await API.delete(`${ENDPOINTS.categories.list}${categoryId}`);
                Toast.success('分类删除成功');
                this.load();
            } catch (error) {
                Toast.error('分类删除失败: ' + error.message);
            }
        }
    }

    static async initDefaultCategories() {
        try {
            await API.post(ENDPOINTS.categories.initDefault);
            Toast.success('默认分类初始化成功');
            this.load();
        } catch (error) {
            Toast.error('默认分类初始化失败: ' + error.message);
        }
    }
}

class ProfileManager {
    static async load() {
        try {
            const profile = await API.get(ENDPOINTS.auth.profile);
            this.updateProfile(profile);
            this.loadUsageStats();
        } catch (error) {
            console.error('ProfileManager.load error:', error);
        }
    }

    static updateProfile(profile) {
        // 后端返回的数据结构是 {user: {...}}
        const user = profile.user || profile;
        document.getElementById('profileName').textContent = user.name || '-';
        document.getElementById('profileUsername').textContent = user.username || '-';
        document.getElementById('profileEmail').textContent = user.email || '-';
        document.getElementById('profileCreatedAt').textContent = Utils.formatDateTime(user.created_at) || '-';
    }

    static async loadUsageStats() {
        try {
            const [accounts, overview] = await Promise.all([
                API.get(ENDPOINTS.accounts.list),
                API.get(ENDPOINTS.statistics.overview)
            ]);

            const reimbursements = await API.get(ENDPOINTS.reimbursements.list);

            document.getElementById('profileAccountCount').textContent = accounts.length;
            document.getElementById('profileTransactionCount').textContent = overview.transaction_count || 0;
            document.getElementById('profileReimbursementCount').textContent = reimbursements.length;
        } catch (error) {
            console.error('加载使用统计失败:', error);
        }
    }

    static async saveProfile(formData) {
        try {
            const updatedProfile = await API.put(ENDPOINTS.auth.profile, formData);
            Toast.success('个人信息更新成功');
            // 只更新显示的个人信息，不重新加载整个页面数据
            this.updateProfile(updatedProfile);
            return true;
        } catch (error) {
            console.error('ProfileManager.saveProfile error:', error);
            return false;
        }
    }

    static async changePassword(formData) {
        try {
            await API.post(`${API_BASE}/auth/change-password`, formData);
            Toast.success('密码修改成功');
            return true;
        } catch (error) {
            console.error('ProfileManager.changePassword error:', error);
            return false;
        }
    }

    static fillEditForm(profile) {
        const form = document.getElementById('editProfileForm');
        const user = profile.user || profile;
        form.querySelector('input[name="name"]').value = user.name || '';
        form.querySelector('input[name="email"]').value = user.email || '';
    }
}

// 事件监听器
document.addEventListener('DOMContentLoaded', function () {
    // 初始化认证状态
    Auth.init();

    // 初始化导航栏交互功能
    NavbarEnhancer.init();

    // 导航链接点击事件
    document.addEventListener('click', function (e) {
        const target = e.target.closest('[data-page]');
        if (target) {
            e.preventDefault();
            const pageName = target.dataset.page;
            PageManager.showPage(pageName);
        }
    });

    // 登录表单提交
    document.getElementById('loginForm').addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            await Auth.login(username, password);
        } catch (error) {
            // 错误已在 Auth.login 中处理
        }
    });

    // 注册表单提交
    document.getElementById('registerForm').addEventListener('submit', async function (e) {
        e.preventDefault();

        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            Toast.error('两次输入的密码不一致');
            return;
        }

        const userData = {
            name: document.getElementById('registerName').value,
            username: document.getElementById('registerUsername').value,
            email: document.getElementById('registerEmail').value,
            password: password
        };

        try {
            await Auth.register(userData);
            // 清空表单
            document.getElementById('registerForm').reset();
        } catch (error) {
            // 错误已在 Auth.register 中处理
        }
    });

    // 显示注册页面
    document.getElementById('showRegister').addEventListener('click', function (e) {
        e.preventDefault();
        document.getElementById('loginPage').style.display = 'none';
        document.getElementById('registerPage').style.display = 'block';
    });

    // 显示登录页面
    document.getElementById('showLogin').addEventListener('click', function (e) {
        e.preventDefault();
        document.getElementById('registerPage').style.display = 'none';
        document.getElementById('loginPage').style.display = 'block';
    });

    // 退出登录
    document.getElementById('logoutBtn').addEventListener('click', function (e) {
        e.preventDefault();
        Auth.logout();
    });

    // 快速操作按钮
    document.addEventListener('click', function (e) {
        const target = e.target.closest('[data-action]');
        if (target) {
            const action = target.dataset.action;
            const page = target.dataset.page;

            // 根据 action 和 page 执行不同的操作
            if (action === 'add-income') {
                PageManager.showPage('expenses');
                setTimeout(() => {
                    const modal = new bootstrap.Modal(document.getElementById('addExpenseModal'));
                    document.getElementById('expenseType').value = 'income';
                    document.getElementById('expenseModalTitle').textContent = '添加收入记录';
                    // 隐藏可申请报销选项（收入不能报销）
                    document.getElementById('reimbursableOption').style.display = 'none';
                    modal.show();
                }, 100);
            } else if (action === 'add' && page === 'expenses') {
                PageManager.showPage('expenses');
                setTimeout(() => {
                    const modal = new bootstrap.Modal(document.getElementById('addExpenseModal'));
                    document.getElementById('expenseType').value = 'expense';
                    document.getElementById('expenseModalTitle').textContent = '添加支出记录';
                    // 显示可申请报销选项
                    document.getElementById('reimbursableOption').style.display = 'block';
                    modal.show();
                }, 100);
            } else if (action === 'add' && page === 'accounts') {
                PageManager.showPage('accounts');
                setTimeout(() => {
                    const modal = new bootstrap.Modal(document.getElementById('addAccountModal'));
                    modal.show();
                }, 100);
            } else if (action === 'add' && page === 'reimbursements') {
                PageManager.showPage('reimbursements');
                setTimeout(() => {
                    const modal = new bootstrap.Modal(document.getElementById('addReimbursementModal'));
                    modal.show();
                }, 100);
            } else if (page) {
                PageManager.showPage(page);
            }
        }
    });

    // 添加账户按钮
    document.getElementById('addAccountBtn')?.addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('addAccountModal'));
        modal.show();
    });

    // 添加收入按钮
    document.getElementById('addIncomeBtn')?.addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('addExpenseModal'));
        document.getElementById('expenseType').value = 'income';
        document.getElementById('expenseModalTitle').textContent = '添加收入记录';
        // 隐藏可申请报销选项（收入不能报销）
        document.getElementById('reimbursableOption').style.display = 'none';
        modal.show();
    });

    // 添加支出按钮
    document.getElementById('addExpenseBtn')?.addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('addExpenseModal'));
        document.getElementById('expenseType').value = 'expense';
        document.getElementById('expenseModalTitle').textContent = '添加支出记录';
        // 显示可申请报销选项
        document.getElementById('reimbursableOption').style.display = 'block';
        modal.show();
    });

    // 申请报销按钮
    document.getElementById('addReimbursementBtn')?.addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('addReimbursementModal'));
        modal.show();
    });

    // 保存账户
    document.getElementById('saveAccountBtn')?.addEventListener('click', async function () {
        const form = document.getElementById('addAccountForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 转换字段名以匹配后端API
        if (data.account_name) {
            data.name = data.account_name;
            delete data.account_name;
        }

        if (await AccountManager.saveAccount(data)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addAccountModal'));
            modal.hide();
            form.reset();
        }
    });

    // 更新账户
    document.getElementById('updateAccountBtn')?.addEventListener('click', async function () {
        const form = document.getElementById('editAccountForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 转换字段名以匹配后端API
        if (data.account_name) {
            data.name = data.account_name;
            delete data.account_name;
        }

        if (await AccountManager.updateAccount(formData)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editAccountModal'));
            modal.hide();
        }
    });

    // 保存收支记录
    document.getElementById('saveExpenseBtn')?.addEventListener('click', async function () {
        const form = document.getElementById('addExpenseForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 设置今天的日期如果没有选择
        if (!data.expense_date) {
            data.expense_date = Utils.getTodayString();
        }

        if (await ExpenseManager.saveExpense(data)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addExpenseModal'));
            modal.hide();
            form.reset();
        }
    });

    // 保存报销申请
    document.getElementById('saveReimbursementBtn')?.addEventListener('click', async function () {
        const form = document.getElementById('addReimbursementForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 转换字段格式以匹配后端API
        const reimbursementData = {
            title: data.title,
            expense_ids: data.expense_ids ? [parseInt(data.expense_ids)] : [],
            description: data.description || ''
        };

        // 验证必填字段
        if (!reimbursementData.title || reimbursementData.expense_ids.length === 0) {
            Toast.error('请填写完整的报销信息');
            return;
        }

        if (await ReimbursementManager.saveReimbursement(reimbursementData)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addReimbursementModal'));
            modal.hide();
            form.reset();
        }
    });

    // 更新收支记录
    document.getElementById('updateExpenseBtn')?.addEventListener('click', async function () {
        const form = document.getElementById('editExpenseForm');
        const formData = new FormData(form);

        if (await ExpenseManager.updateExpense(formData)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editExpenseModal'));
            modal.hide();
        }
    });

    // 更新报销申请
    document.getElementById('updateReimbursementBtn')?.addEventListener('click', async function () {
        const form = document.getElementById('editReimbursementForm');
        const formData = new FormData(form);

        if (await ReimbursementManager.updateReimbursement(formData)) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editReimbursementModal'));
            modal.hide();
        }
    });

    // 报销支出选择变化时自动填充金额
    document.getElementById('reimbursementExpense')?.addEventListener('change', function () {
        const selectedOption = this.options[this.selectedIndex];
        const amount = selectedOption.dataset.amount;
        const amountInput = document.querySelector('#addReimbursementForm input[name="amount"]');
        if (amountInput && amount) {
            amountInput.value = amount;
        }
    });

    // 设置默认日期为今天
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = Utils.getTodayString();
        }
    });

    // 个人信息页面事件监听器
    const editProfileBtn = document.getElementById('editProfileBtn');
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', async function () {
            try {
                const profile = await API.get(ENDPOINTS.auth.profile);
                ProfileManager.fillEditForm(profile);
                const modal = new bootstrap.Modal(document.getElementById('editProfileModal'));
                modal.show();
            } catch (error) {
                Toast.error('获取个人信息失败');
            }
        });
    }

    const changePasswordBtn = document.getElementById('changePasswordBtn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', function () {
            const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
            modal.show();
        });
    }

    const logoutAllBtn = document.getElementById('logoutAllBtn');
    if (logoutAllBtn) {
        logoutAllBtn.addEventListener('click', function () {
            if (confirm('确定要退出所有设备吗？')) {
                Auth.logout();
            }
        });
    }

    // 保存个人信息
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', async function () {
            const form = document.getElementById('editProfileForm');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);

            const success = await ProfileManager.saveProfile(data);
            if (success) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
                modal.hide();
            }
        });
    }

    // 修改密码
    const savePasswordBtn = document.getElementById('savePasswordBtn');
    if (savePasswordBtn) {
        savePasswordBtn.addEventListener('click', async function () {
            const form = document.getElementById('changePasswordForm');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);

            if (data.new_password !== data.confirm_password) {
                Toast.error('新密码和确认密码不匹配');
                return;
            }

            const success = await ProfileManager.changePassword({
                old_password: data.current_password,
                new_password: data.new_password
            });

            if (success) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('changePasswordModal'));
                modal.hide();
                form.reset();
            }
        });

        // 保存分类按钮点击事件
        const saveCategoryBtn = document.getElementById('saveCategoryBtn');
        if (saveCategoryBtn) {
            saveCategoryBtn.addEventListener('click', async function () {
                const form = document.getElementById('categoryForm');
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                
                // 如果有ID，说明是编辑，需要使用PUT请求
                if (data.id) {
                    try {
                        await API.put(`${ENDPOINTS.categories.list}${data.id}`, data);
                        Toast.success('分类更新成功');
                        CategoryManager.load();
                        bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
                    } catch (error) {
                        Toast.error('分类更新失败: ' + error.message);
                    }
                } else {
                    // 新建分类
                    await CategoryManager.saveCategory(data);
                }
            });
        }
    }

    // 收支记录筛选按钮事件
    const applyExpenseFilterBtn = document.getElementById('applyExpenseFilter');
    if (applyExpenseFilterBtn) {
        applyExpenseFilterBtn.addEventListener('click', function() {
            ExpenseManager.applyFilters();
        });
    }

    const resetExpenseFilterBtn = document.getElementById('resetExpenseFilter');
    if (resetExpenseFilterBtn) {
        resetExpenseFilterBtn.addEventListener('click', function() {
            ExpenseManager.resetFilters();
        });
    }

    // 报销记录筛选按钮事件
    const applyReimbursementFilterBtn = document.getElementById('applyReimbursementFilter');
    if (applyReimbursementFilterBtn) {
        applyReimbursementFilterBtn.addEventListener('click', function() {
            ReimbursementManager.applyFilters();
        });
    }

    const resetReimbursementFilterBtn = document.getElementById('resetReimbursementFilter');
    if (resetReimbursementFilterBtn) {
        resetReimbursementFilterBtn.addEventListener('click', function() {
            ReimbursementManager.resetFilters();
        });
    }

    // 搜索框实时筛选（防抖）
    const expenseSearchInput = document.getElementById('expenseSearch');
    if (expenseSearchInput) {
        expenseSearchInput.addEventListener('input', Utils.debounce(function() {
            ExpenseManager.applyFilters();
        }, 500));
    }

    const reimbursementSearchInput = document.getElementById('reimbursementSearch');
    if (reimbursementSearchInput) {
        reimbursementSearchInput.addEventListener('input', Utils.debounce(function() {
            ReimbursementManager.applyFilters();
        }, 500));
    }
});

// 全局错误处理
window.addEventListener('error', function (e) {
    console.error('Global error:', e.error);
    Toast.error('发生了未知错误，请刷新页面重试');
});

// 网络状态监听
window.addEventListener('online', function () {
    Toast.success('网络连接已恢复');
});

window.addEventListener('offline', function () {
    Toast.warning('网络连接已断开');
});