from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.restaurant import Restaurant, Menu, Reservation
from datetime import datetime

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

# 餐厅列表
@restaurant_bp.route('/')
def index():
    restaurants = Restaurant.query.filter_by(status='active').all()
    return render_template('restaurant/index.html', restaurants=restaurants)

# 餐厅详情
@restaurant_bp.route('/<int:id>')
def detail(id):
    restaurant = Restaurant.query.get_or_404(id)
    menus = Menu.query.filter_by(restaurant_id=id, available=True).all()
    return render_template('restaurant/detail.html', restaurant=restaurant, menus=menus)

# 预订餐厅
@restaurant_bp.route('/<int:id>/reserve', methods=['GET', 'POST'])
@login_required
def reserve(id):
    restaurant = Restaurant.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            party_size = int(request.form.get('party_size', 1))
            notes = request.form.get('notes', '')
            
            if not date_str or not time_str:
                flash('请选择日期和时间。', 'danger')
                return render_template('restaurant/reserve.html', restaurant=restaurant)
            
            reservation_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # 创建预订
            reservation = Reservation(
                user_id=current_user.id,
                restaurant_id=id,
                reservation_time=reservation_time,
                party_size=party_size,
                notes=notes
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            flash('预订成功！', 'success')
            return redirect(url_for('restaurant.my_reservations'))
        except Exception as e:
            flash(f'预订失败：{str(e)}', 'danger')
    
    return render_template('restaurant/reserve.html', restaurant=restaurant)

# 我的预订列表
@restaurant_bp.route('/my-reservations')
@login_required
def my_reservations():
    reservations = (Reservation.query
                   .filter_by(user_id=current_user.id)
                   .order_by(Reservation.reservation_time.desc())
                   .all())
    return render_template('restaurant/my_reservations.html', reservations=reservations)

# 取消预订
@restaurant_bp.route('/cancel-reservation/<int:id>', methods=['POST'])
@login_required
def cancel_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    
    # 检查是否是当前用户的预订
    if reservation.user_id != current_user.id:
        abort(403)
    
    # 检查是否可以取消（只能取消待确认或已确认的预订）
    if reservation.status not in ['pending', 'confirmed']:
        flash('此预订无法取消。', 'danger')
        return redirect(url_for('restaurant.my_reservations'))
    
    reservation.status = 'canceled'
    db.session.commit()
    
    flash('预订已成功取消。', 'success')
    return redirect(url_for('restaurant.my_reservations'))

# ==== 管理员路由 ====

# 餐厅管理
@restaurant_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin():
        abort(403)
    
    restaurants = Restaurant.query.all()
    return render_template('restaurant/admin/index.html', restaurants=restaurants)

# 添加餐厅
@restaurant_bp.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    if not current_user.is_admin():
        abort(403)
    
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        capacity = request.form.get('capacity')
        opening_hours = request.form.get('opening_hours')
        description = request.form.get('description')
        
        if not name or not location:
            flash('餐厅名称和位置是必填项。', 'danger')
            return render_template('restaurant/admin/add_restaurant.html')
        
        new_restaurant = Restaurant(
            name=name,
            location=location,
            capacity=capacity or 0,
            opening_hours=opening_hours,
            description=description
        )
        
        db.session.add(new_restaurant)
        db.session.commit()
        
        flash('餐厅添加成功！', 'success')
        return redirect(url_for('restaurant.admin'))
    
    return render_template('restaurant/admin/add_restaurant.html')

# 编辑餐厅
@restaurant_bp.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_restaurant(id):
    if not current_user.is_admin():
        abort(403)
    
    restaurant = Restaurant.query.get_or_404(id)
    
    if request.method == 'POST':
        restaurant.name = request.form.get('name')
        restaurant.location = request.form.get('location')
        restaurant.capacity = request.form.get('capacity') or 0
        restaurant.opening_hours = request.form.get('opening_hours')
        restaurant.description = request.form.get('description')
        restaurant.status = request.form.get('status')
        
        db.session.commit()
        
        flash('餐厅信息已更新。', 'success')
        return redirect(url_for('restaurant.admin'))
    
    return render_template('restaurant/admin/edit_restaurant.html', restaurant=restaurant)

# 管理菜单
@restaurant_bp.route('/admin/menu/<int:restaurant_id>')
@login_required
def manage_menu(restaurant_id):
    if not current_user.is_admin():
        abort(403)
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menus = Menu.query.filter_by(restaurant_id=restaurant_id).all()
    
    return render_template('restaurant/admin/menu.html', restaurant=restaurant, menus=menus)

# 添加菜单项
@restaurant_bp.route('/admin/menu/<int:restaurant_id>/add', methods=['GET', 'POST'])
@login_required
def add_menu(restaurant_id):
    if not current_user.is_admin():
        abort(403)
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price')
        description = request.form.get('description')
        available = 'available' in request.form
        
        if not name or not price:
            flash('菜品名称和价格是必填项。', 'danger')
            return render_template('restaurant/admin/add_menu.html', restaurant=restaurant)
        
        try:
            price = float(price)
        except ValueError:
            flash('价格必须是有效的数字。', 'danger')
            return render_template('restaurant/admin/add_menu.html', restaurant=restaurant)
        
        new_menu = Menu(
            restaurant_id=restaurant_id,
            name=name,
            category=category,
            price=price,
            description=description,
            available=available
        )
        
        db.session.add(new_menu)
        db.session.commit()
        
        flash('菜品添加成功！', 'success')
        return redirect(url_for('restaurant.manage_menu', restaurant_id=restaurant_id))
    
    return render_template('restaurant/admin/add_menu.html', restaurant=restaurant)

# 编辑菜单项
@restaurant_bp.route('/admin/menu/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_menu(id):
    if not current_user.is_admin():
        abort(403)
    
    menu = Menu.query.get_or_404(id)
    restaurant = Restaurant.query.get_or_404(menu.restaurant_id)
    
    if request.method == 'POST':
        menu.name = request.form.get('name')
        menu.category = request.form.get('category')
        
        try:
            menu.price = float(request.form.get('price'))
        except ValueError:
            flash('价格必须是有效的数字。', 'danger')
            return render_template('restaurant/admin/edit_menu.html', menu=menu, restaurant=restaurant)
        
        menu.description = request.form.get('description')
        menu.available = 'available' in request.form
        
        db.session.commit()
        
        flash('菜品信息已更新。', 'success')
        return redirect(url_for('restaurant.manage_menu', restaurant_id=menu.restaurant_id))
    
    return render_template('restaurant/admin/edit_menu.html', menu=menu, restaurant=restaurant)

# 管理预订
@restaurant_bp.route('/admin/reservations/<int:restaurant_id>')
@login_required
def manage_reservations(restaurant_id):
    if not current_user.is_admin():
        abort(403)
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    reservations = (Reservation.query
                   .filter_by(restaurant_id=restaurant_id)
                   .order_by(Reservation.reservation_time.desc())
                   .all())
    
    return render_template('restaurant/admin/reservations.html', restaurant=restaurant, reservations=reservations)

# 更新预订状态
@restaurant_bp.route('/admin/reservations/update-status/<int:id>', methods=['POST'])
@login_required
def update_reservation_status(id):
    if not current_user.is_admin():
        abort(403)
    
    reservation = Reservation.query.get_or_404(id)
    status = request.form.get('status')
    
    if status in ['pending', 'confirmed', 'canceled', 'completed']:
        reservation.status = status
        db.session.commit()
        flash('预订状态已更新。', 'success')
    else:
        flash('无效的预订状态。', 'danger')
    
    return redirect(url_for('restaurant.manage_reservations', restaurant_id=reservation.restaurant_id)) 