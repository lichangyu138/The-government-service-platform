from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.verify_password(password):
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('登录失败，请检查用户名和密码。', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证输入
        if not username or not email or not password:
            flash('所有字段都是必填的。', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('两次输入的密码不匹配。', 'danger')
            return render_template('auth/register.html')
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已被使用。', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册。', 'danger')
            return render_template('auth/register.html')
        
        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            password=password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功！现在您可以登录了。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出。', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # 验证邮箱是否已存在
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('该邮箱已被其他用户使用。', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        current_user.email = email
        db.session.commit()
        
        flash('个人资料已更新。', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not current_user.verify_password(current_password):
            flash('当前密码不正确。', 'danger')
            return render_template('auth/change_password.html')
        
        # 验证新密码
        if new_password != confirm_password:
            flash('两次输入的新密码不匹配。', 'danger')
            return render_template('auth/change_password.html')
        
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('密码已成功更改。', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html') 