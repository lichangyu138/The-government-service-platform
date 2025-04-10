from flask import Blueprint, render_template
from flask_login import current_user

# 主页蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """网站主页"""
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    """用户仪表板"""
    return render_template('dashboard.html') 