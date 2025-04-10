from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.shuttle import ShuttleRoute, ShuttleSchedule, ShuttleReservation
from datetime import datetime, date
from flask_wtf import FlaskForm

shuttle_bp = Blueprint('shuttle', __name__, url_prefix='/shuttle')

# 班车路线列表
@shuttle_bp.route('/')
def index():
    routes = ShuttleRoute.query.filter_by(status='active').all()
    return render_template('shuttle/index.html', routes=routes)

# 班车路线详情
@shuttle_bp.route('/route/<int:id>')
def route_detail(id):
    route = ShuttleRoute.query.get_or_404(id)
    schedules = ShuttleSchedule.query.filter_by(route_id=id, status='active').all()
    return render_template('shuttle/route_detail.html', route=route, schedules=schedules)

# 预订班车
@shuttle_bp.route('/reserve/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def reserve(schedule_id):
    schedule = ShuttleSchedule.query.get_or_404(schedule_id)
    route = ShuttleRoute.query.get_or_404(schedule.route_id)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            reservation_date_str = request.form.get('date')
            notes = request.form.get('notes', '')
            
            if not reservation_date_str:
                flash('请选择日期。', 'danger')
                return render_template('shuttle/reserve.html', schedule=schedule, route=route, form=form)
            
            reservation_date = datetime.strptime(reservation_date_str, "%Y-%m-%d").date()
            
            # 检查预订日期是否有效（不能预订过去的日期）
            if reservation_date < date.today():
                flash('不能预订过去的日期。', 'danger')
                return render_template('shuttle/reserve.html', schedule=schedule, route=route, form=form)
            
            # 检查用户是否已经预订了同一天的同一班次
            existing_reservation = ShuttleReservation.query.filter_by(
                user_id=current_user.id,
                schedule_id=schedule_id,
                reservation_date=reservation_date,
                status='confirmed'
            ).first()
            
            if existing_reservation:
                flash('您已经预订了这个日期的这个班次。', 'danger')
                return render_template('shuttle/reserve.html', schedule=schedule, route=route, form=form)
            
            # 创建预订
            reservation = ShuttleReservation(
                user_id=current_user.id,
                schedule_id=schedule_id,
                reservation_date=reservation_date,
                notes=notes
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            flash('班车预订成功！', 'success')
            return redirect(url_for('shuttle.my_reservations'))
        except Exception as e:
            flash(f'预订失败：{str(e)}', 'danger')
    
    return render_template('shuttle/reserve.html', schedule=schedule, route=route, form=form)

# 我的班车预订
@shuttle_bp.route('/my-reservations')
@login_required
def my_reservations():
    reservations = ShuttleReservation.query.filter_by(user_id=current_user.id).order_by(ShuttleReservation.reservation_date.desc()).all()
    return render_template('shuttle/my_reservations.html', reservations=reservations)

# 取消班车预订
@shuttle_bp.route('/cancel-reservation/<int:id>', methods=['POST'])
@login_required
def cancel_reservation(id):
    reservation = ShuttleReservation.query.get_or_404(id)
    
    # 检查是否是当前用户的预订
    if reservation.user_id != current_user.id:
        abort(403)
    
    # 检查预订日期是否已过
    if reservation.reservation_date < date.today():
        flash('无法取消过去的预订。', 'danger')
        return redirect(url_for('shuttle.my_reservations'))
    
    reservation.status = 'canceled'
    db.session.commit()
    
    flash('班车预订已成功取消。', 'success')
    return redirect(url_for('shuttle.my_reservations'))

# ==== 管理员路由 ====

# 班车管理
@shuttle_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin():
        abort(403)
    
    routes = ShuttleRoute.query.all()
    return render_template('shuttle/admin/index.html', routes=routes)

# 添加班车路线
@shuttle_bp.route('/admin/route/add', methods=['GET', 'POST'])
@login_required
def add_route():
    if not current_user.is_admin():
        abort(403)
    
    # 创建一个简单的表单，用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form.get('name')
        start_location = request.form.get('start_location') 
        end_location = request.form.get('end_location')
        stops = request.form.get('stops')
        description = request.form.get('description')
        status = request.form.get('status', 'active')
        
        if not name or not start_location or not end_location:
            flash('路线名称、起点和终点是必填项。', 'danger')
            return render_template('shuttle/admin/add_route.html', form=form)
        
        new_route = ShuttleRoute(
            name=name,
            start_location=start_location,
            end_location=end_location,
            stops=stops,
            description=description,
            status=status
        )
        
        db.session.add(new_route)
        db.session.commit()
        
        flash('班车路线添加成功！', 'success')
        return redirect(url_for('shuttle.admin'))
    
    return render_template('shuttle/admin/add_route.html', form=form)

# 编辑班车路线
@shuttle_bp.route('/admin/route/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_route(id):
    if not current_user.is_admin():
        abort(403)
    
    route = ShuttleRoute.query.get_or_404(id)
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        route.name = request.form.get('name')
        route.start_location = request.form.get('start_location')
        route.end_location = request.form.get('end_location')
        route.stops = request.form.get('stops')
        route.description = request.form.get('description')
        route.status = request.form.get('status')
        
        db.session.commit()
        
        flash('班车路线信息已更新。', 'success')
        return redirect(url_for('shuttle.admin'))
    
    return render_template('shuttle/admin/edit_route.html', route=route, form=form)

# 管理班车时刻表
@shuttle_bp.route('/admin/schedule/<int:route_id>')
@login_required
def manage_schedule(route_id):
    if not current_user.is_admin():
        abort(403)
    
    route = ShuttleRoute.query.get_or_404(route_id)
    schedules = ShuttleSchedule.query.filter_by(route_id=route_id).all()
    
    return render_template('shuttle/admin/schedule.html', route=route, schedules=schedules)

# 添加班车时刻
@shuttle_bp.route('/admin/schedule/<int:route_id>/add', methods=['GET', 'POST'])
@login_required
def add_schedule(route_id):
    if not current_user.is_admin():
        abort(403)
    
    route = ShuttleRoute.query.get_or_404(route_id)
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        departure_time = request.form.get('departure_time')
        arrival_time = request.form.get('arrival_time')
        days_of_week = ','.join(request.form.getlist('days_of_week'))
        capacity = request.form.get('capacity')
        vehicle_info = request.form.get('vehicle_info')
        
        if not departure_time or not arrival_time or not days_of_week:
            flash('发车时间、到达时间和运行日期是必填项。', 'danger')
            return render_template('shuttle/admin/add_schedule.html', route=route, form=form)
        
        new_schedule = ShuttleSchedule(
            route_id=route_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            days_of_week=days_of_week,
            capacity=capacity or 0,
            vehicle_info=vehicle_info
        )
        
        db.session.add(new_schedule)
        db.session.commit()
        
        flash('班车时刻添加成功！', 'success')
        return redirect(url_for('shuttle.manage_schedule', route_id=route_id))
    
    return render_template('shuttle/admin/add_schedule.html', route=route, form=form)

# 编辑班车时刻
@shuttle_bp.route('/admin/schedule/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(id):
    if not current_user.is_admin():
        abort(403)
    
    schedule = ShuttleSchedule.query.get_or_404(id)
    route = ShuttleRoute.query.get_or_404(schedule.route_id)
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        schedule.departure_time = request.form.get('departure_time')
        schedule.arrival_time = request.form.get('arrival_time')
        schedule.days_of_week = ','.join(request.form.getlist('days_of_week'))
        schedule.capacity = request.form.get('capacity') or 0
        schedule.vehicle_info = request.form.get('vehicle_info')
        schedule.status = request.form.get('status')
        
        db.session.commit()
        
        flash('班车时刻信息已更新。', 'success')
        return redirect(url_for('shuttle.manage_schedule', route_id=route.id))
    
    return render_template('shuttle/admin/edit_schedule.html', schedule=schedule, route=route, form=form)

# 查看班车预订
@shuttle_bp.route('/admin/reservations/<int:schedule_id>')
@login_required
def view_reservations(schedule_id):
    if not current_user.is_admin():
        abort(403)
    
    schedule = ShuttleSchedule.query.get_or_404(schedule_id)
    route = ShuttleRoute.query.get_or_404(schedule.route_id)
    
    # 根据日期分组的预订
    date_str = request.args.get('date')
    
    if date_str:
        try:
            reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            reservations = ShuttleReservation.query.filter_by(
                schedule_id=schedule_id,
                reservation_date=reservation_date
            ).all()
        except ValueError:
            flash('无效的日期格式。', 'danger')
            reservations = []
    else:
        # 默认显示今天及以后的预订
        reservations = ShuttleReservation.query.filter(
            ShuttleReservation.schedule_id == schedule_id,
            ShuttleReservation.reservation_date >= date.today()
        ).order_by(ShuttleReservation.reservation_date).all()
    
    return render_template('shuttle/admin/reservations.html', 
                          schedule=schedule, 
                          route=route, 
                          reservations=reservations,
                          selected_date=date_str) 