from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.repair import (
    RepairCategory, RepairRequest, RepairPhoto, 
    RepairStaff, RepairAssignment, RepairFeedback
)
from models.user import User
from sqlalchemy import func
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Optional

repair_bp = Blueprint('repair', __name__, url_prefix='/repair')

# 设置上传文件夹
UPLOAD_FOLDER = 'admin_platform/static/uploads/repair'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 定义分类表单
class CategoryForm(FlaskForm):
    name = StringField('名称', validators=[DataRequired('分类名称不能为空'), Length(max=50)])
    description = TextAreaField('描述', validators=[Length(max=255)])

# 定义维修人员表单
class StaffForm(FlaskForm):
    user_id = SelectField('用户', validators=[DataRequired('请选择用户')], coerce=int)
    staff_number = StringField('员工编号', validators=[DataRequired('员工编号不能为空'), Length(max=50)])
    specialty = StringField('专业特长', validators=[Optional(), Length(max=100)])

# 定义编辑维修人员表单
class EditStaffForm(FlaskForm):
    specialty = StringField('专业特长', validators=[Optional(), Length(max=100)])
    availability = SelectField('当前状态', 
                              choices=[
                                  ('available', '可用'), 
                                  ('busy', '忙碌'), 
                                  ('unavailable', '不可用'),
                                  ('on_leave', '休假')
                              ],
                              validators=[DataRequired('请选择状态')])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 报修首页
@repair_bp.route('/')
def index():
    categories = RepairCategory.query.all()
    return render_template('repair/index.html', categories=categories)

# 提交报修请求
@repair_bp.route('/request', methods=['GET', 'POST'])
@login_required
def create_request():
    categories = RepairCategory.query.all()
    
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        contact_phone = request.form.get('contact_phone')
        preferred_time = request.form.get('preferred_time')
        priority = request.form.get('priority', 'normal')
        
        if not category_id or not title or not description or not location:
            flash('请填写所有必填字段。', 'danger')
            return render_template('repair/create_request.html', categories=categories)
        
        # 创建报修请求
        repair_request = RepairRequest(
            user_id=current_user.id,
            category_id=category_id,
            title=title,
            description=description,
            location=location,
            contact_phone=contact_phone,
            preferred_time=preferred_time,
            priority=priority
        )
        
        db.session.add(repair_request)
        db.session.commit()
        
        # 处理上传的照片
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            
            for photo in photos:
                if photo and photo.filename != '' and allowed_file(photo.filename):
                    # 创建上传目录
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    # 生成安全的文件名
                    filename = secure_filename(photo.filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"repair_{repair_request.id}_{timestamp}_{filename}"
                    
                    # 保存文件
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    photo.save(file_path)
                    
                    # 创建数据库记录
                    relative_path = f"uploads/repair/{filename}"
                    repair_photo = RepairPhoto(
                        request_id=repair_request.id,
                        file_path=relative_path
                    )
                    
                    db.session.add(repair_photo)
            
            db.session.commit()
        
        flash('报修请求已成功提交！', 'success')
        return redirect(url_for('repair.my_requests'))
    
    return render_template('repair/create_request.html', categories=categories)

# 我的报修请求
@repair_bp.route('/my-requests')
@login_required
def my_requests():
    requests = RepairRequest.query.filter_by(user_id=current_user.id).order_by(RepairRequest.created_at.desc()).all()
    return render_template('repair/my_requests.html', requests=requests)

# 报修请求详情
@repair_bp.route('/request/<int:id>')
@login_required
def request_detail(id):
    repair_request = RepairRequest.query.get_or_404(id)
    
    # 普通用户只能查看自己的报修请求
    if not current_user.is_admin() and repair_request.user_id != current_user.id:
        abort(403)
    
    # 获取分配信息
    assignments = RepairAssignment.query.filter_by(request_id=id).order_by(RepairAssignment.assigned_at.desc()).all()
    
    # 获取反馈信息
    feedback = RepairFeedback.query.filter_by(request_id=id).first()
    
    return render_template('repair/request_detail.html', 
                          request=repair_request, 
                          assignments=assignments,
                          feedback=feedback)

# 取消报修请求
@repair_bp.route('/cancel-request/<int:id>', methods=['POST'])
@login_required
def cancel_request(id):
    repair_request = RepairRequest.query.get_or_404(id)
    
    # 检查是否是当前用户的请求
    if repair_request.user_id != current_user.id:
        abort(403)
    
    # 只能取消待处理或已分配的请求
    if repair_request.status not in ['pending', 'assigned']:
        flash('只能取消待处理或待维修的请求。', 'danger')
        return redirect(url_for('repair.my_requests'))
    
    repair_request.status = 'canceled'
    db.session.commit()
    
    flash('报修请求已成功取消。', 'success')
    return redirect(url_for('repair.my_requests'))

# 提交反馈
@repair_bp.route('/feedback/<int:request_id>', methods=['GET', 'POST'])
@login_required
def submit_feedback(request_id):
    repair_request = RepairRequest.query.get_or_404(request_id)
    
    # 检查是否是当前用户的请求
    if repair_request.user_id != current_user.id:
        abort(403)
    
    # 只能对已完成的请求提交反馈
    if repair_request.status != 'completed':
        flash('只能对已完成的维修请求提交反馈。', 'danger')
        return redirect(url_for('repair.request_detail', id=request_id))
    
    # 检查是否已经提交过反馈
    existing_feedback = RepairFeedback.query.filter_by(request_id=request_id).first()
    if existing_feedback:
        flash('您已经提交过反馈。', 'warning')
        return redirect(url_for('repair.request_detail', id=request_id))
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError('评分必须在1-5之间')
            
            feedback = RepairFeedback(
                request_id=request_id,
                user_id=current_user.id,
                rating=rating,
                comment=comment
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            flash('感谢您的反馈！', 'success')
            return redirect(url_for('repair.request_detail', id=request_id))
        except Exception as e:
            flash(f'提交反馈失败：{str(e)}', 'danger')
    
    return render_template('repair/submit_feedback.html', request=repair_request)

# ==== 管理员路由 ====

# 报修管理
@repair_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin():
        abort(403)
    
    # 统计各状态的报修请求数量
    status_counts = {
        'pending': RepairRequest.query.filter_by(status='pending').count(),
        'assigned': RepairRequest.query.filter_by(status='assigned').count(),
        'in_progress': RepairRequest.query.filter_by(status='in_progress').count(),
        'completed': RepairRequest.query.filter_by(status='completed').count(),
        'canceled': RepairRequest.query.filter_by(status='canceled').count()
    }
    
    # 计算报修统计数据
    total_requests = sum(status_counts.values())
    completed_requests = status_counts['completed']
    
    # 计算反馈统计
    feedback_count = RepairFeedback.query.count()
    
    # 计算平均评分
    avg_rating_result = db.session.query(func.avg(RepairFeedback.rating)).scalar()
    avg_rating = avg_rating_result if avg_rating_result else 0
    
    # 计算评价率 (如果有已完成的请求)
    feedback_rate = (feedback_count / completed_requests * 100) if completed_requests > 0 else 0
    
    # 统计数据
    stats = {
        'total': total_requests,
        'pending': status_counts['pending'],
        'processing': status_counts['in_progress'] + status_counts['assigned'],
        'completed': completed_requests,
        'feedback_count': feedback_count,
        'avg_rating': avg_rating,
        'feedback_rate': round(feedback_rate, 1)
    }
    
    # 获取最近的报修请求
    recent_requests = RepairRequest.query.order_by(RepairRequest.created_at.desc()).limit(5).all()
    
    # 计算待处理和处理中的请求数量（用于显示徽章）
    pending_count = status_counts['pending']
    processing_count = status_counts['assigned'] + status_counts['in_progress']
    
    return render_template('repair/admin/index.html', 
                          status_counts=status_counts,
                          recent_requests=recent_requests,
                          stats=stats,
                          requests=recent_requests,
                          pending_count=pending_count,
                          processing_count=processing_count
                          )

# 管理报修类别
@repair_bp.route('/admin/categories')
@login_required
def manage_categories():
    if not current_user.is_admin():
        abort(403)
    
    categories = RepairCategory.query.all()
    form = CategoryForm()
    
    return render_template('repair/admin/categories.html', categories=categories, form=form)

# 添加报修类别
@repair_bp.route('/admin/categories/add', methods=['POST'])
@login_required
def add_category():
    if not current_user.is_admin():
        abort(403)
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        category = RepairCategory(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        
        flash('报修类别添加成功！', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('repair.manage_categories'))

# 编辑报修类别
@repair_bp.route('/admin/categories/edit/<int:id>', methods=['POST'])
@login_required
def edit_category(id):
    if not current_user.is_admin():
        abort(403)
    
    category = RepairCategory.query.get_or_404(id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        
        flash('报修类别已更新。', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('repair.manage_categories'))

# 删除报修类别
@repair_bp.route('/admin/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    if not current_user.is_admin():
        abort(403)
    
    category = RepairCategory.query.get_or_404(id)
    
    # 检查是否有相关联的维修请求
    if RepairRequest.query.filter_by(category_id=id).first():
        flash('无法删除此类别，因为已有报修请求使用了此类别。', 'danger')
        return redirect(url_for('repair.manage_categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('报修类别已成功删除。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除类别失败：{str(e)}', 'danger')
    
    return redirect(url_for('repair.manage_categories'))

# 管理维修人员
@repair_bp.route('/admin/staff')
@login_required
def manage_staff():
    if not current_user.is_admin():
        abort(403)
    
    staff = RepairStaff.query.all()
    return render_template('repair/admin/staff.html', staff=staff)

# 添加维修人员
@repair_bp.route('/admin/staff/add', methods=['GET', 'POST'])
@login_required
def add_staff():
    if not current_user.is_admin():
        abort(403)
    
    # 获取还不是维修人员的用户
    available_users = User.query.filter(
        ~User.id.in_(
            db.session.query(RepairStaff.user_id)
        )
    ).all()
    
    # 创建表单并设置选项
    form = StaffForm()
    form.user_id.choices = [(u.id, f"{u.username} ({u.email})") for u in available_users]
    
    if form.validate_on_submit():
        # 检查员工编号是否已存在
        existing_staff = RepairStaff.query.filter_by(staff_number=form.staff_number.data).first()
        if existing_staff:
            flash('此员工编号已被使用。', 'danger')
            return render_template('repair/admin/add_staff.html', form=form)
        
        staff = RepairStaff(
            user_id=form.user_id.data,
            staff_number=form.staff_number.data,
            specialty=form.specialty.data
        )
        
        try:
            db.session.add(staff)
            db.session.commit()
            flash('维修人员添加成功！', 'success')
            return redirect(url_for('repair.manage_staff'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败：{str(e)}', 'danger')
    
    return render_template('repair/admin/add_staff.html', form=form)

# 编辑维修人员
@repair_bp.route('/admin/staff/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_staff(id):
    if not current_user.is_admin():
        abort(403)
    
    staff = RepairStaff.query.get_or_404(id)
    form = EditStaffForm(obj=staff)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(staff)
            db.session.commit()
            
            flash('维修人员信息已更新。', 'success')
            return redirect(url_for('repair.manage_staff'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('repair/admin/edit_staff.html', staff=staff, form=form)

# 查看报修请求列表
@repair_bp.route('/admin/requests')
@login_required
def view_requests():
    if not current_user.is_admin():
        abort(403)
    
    status = request.args.get('status', 'all')
    category_id = request.args.get('category_id')
    
    query = RepairRequest.query
    
    # 处理特殊状态 'processing'（包含 'assigned' 和 'in_progress'）
    if status == 'processing':
        query = query.filter(RepairRequest.status.in_(['assigned', 'in_progress']))
    elif status != 'all':
        query = query.filter_by(status=status)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    requests = query.order_by(RepairRequest.created_at.desc()).all()
    categories = RepairCategory.query.all()
    
    # 计算各状态的数量（用于显示徽章）
    pending_count = RepairRequest.query.filter_by(status='pending').count()
    processing_count = (RepairRequest.query.filter_by(status='assigned').count() + 
                      RepairRequest.query.filter_by(status='in_progress').count())
    
    return render_template('repair/admin/requests.html', 
                          requests=requests, 
                          categories=categories,
                          current_status=status,
                          current_category=category_id,
                          pending_count=pending_count,
                          processing_count=processing_count)

# 处理报修请求
@repair_bp.route('/admin/requests/<int:id>', methods=['GET', 'POST'])
@login_required
def process_request(id):
    if not current_user.is_admin():
        abort(403)
    
    repair_request = RepairRequest.query.get_or_404(id)
    assignments = RepairAssignment.query.filter_by(request_id=id).order_by(RepairAssignment.assigned_at.desc()).all()
    
    return render_template('repair/admin/process_request.html', 
                          request=repair_request,
                          assignments=assignments)

# 分配维修人员
@repair_bp.route('/admin/assign/<int:request_id>', methods=['GET', 'POST'])
@login_required
def assign_staff(request_id):
    if not current_user.is_admin():
        abort(403)
    
    repair_request = RepairRequest.query.get_or_404(request_id)
    
    # 只能为待处理的请求分配人员
    if repair_request.status not in ['pending', 'assigned']:
        flash('只能为待处理或重新分配的请求分配维修人员。', 'danger')
        return redirect(url_for('repair.process_request', id=request_id))
    
    # 获取可用的维修人员
    available_staff = RepairStaff.query.filter_by(availability='available').all()
    
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        scheduled_time_str = request.form.get('scheduled_time')
        notes = request.form.get('notes', '')
        
        if not staff_id or not scheduled_time_str:
            flash('维修人员和计划时间是必填项。', 'danger')
            return render_template('repair/admin/assign_staff.html', 
                                  request=repair_request,
                                  staff=available_staff)
        
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, "%Y-%m-%dT%H:%M")
            
            # 创建分配记录
            assignment = RepairAssignment(
                request_id=request_id,
                staff_id=staff_id,
                scheduled_time=scheduled_time,
                notes=notes
            )
            
            db.session.add(assignment)
            
            # 更新请求状态
            repair_request.status = 'assigned'
            
            # 更新维修人员状态
            staff = RepairStaff.query.get(staff_id)
            staff.availability = 'busy'
            
            db.session.commit()
            
            flash('维修人员已成功分配！', 'success')
            return redirect(url_for('repair.process_request', id=request_id))
        except Exception as e:
            flash(f'分配失败：{str(e)}', 'danger')
    
    return render_template('repair/admin/assign_staff.html', 
                          request=repair_request,
                          staff=available_staff)

# 更新维修进度
@repair_bp.route('/admin/update-status/<int:request_id>', methods=['POST'])
@login_required
def update_request_status(request_id):
    if not current_user.is_admin():
        abort(403)
    
    repair_request = RepairRequest.query.get_or_404(request_id)
    status = request.form.get('status')
    
    if status in ['pending', 'assigned', 'in_progress', 'completed', 'canceled']:
        old_status = repair_request.status
        repair_request.status = status
        
        # 如果状态为已完成，则更新分配记录中的完成时间
        if status == 'completed':
            assignment = RepairAssignment.query.filter_by(request_id=request_id, completion_time=None).first()
            if assignment:
                assignment.completion_time = datetime.now()
                assignment.status = 'completed'
                
                # 更新维修人员状态为可用
                staff = RepairStaff.query.get(assignment.staff_id)
                staff.availability = 'available'
        
        db.session.commit()
        
        flash('报修状态已更新。', 'success')
    else:
        flash('无效的状态。', 'danger')
    
    return redirect(url_for('repair.process_request', id=request_id))

# 管理员开始维修
@repair_bp.route('/admin/start-repair/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_start_repair(id):
    if not current_user.is_admin():
        abort(403)
    
    repair_request = RepairRequest.query.get_or_404(id)
    
    if repair_request.status != 'assigned':
        flash('只能开始已分配的报修请求。', 'danger')
        return redirect(url_for('repair.admin'))
    
    if request.method == 'POST':
        repair_request.status = 'in_progress'
        repair_request.in_progress_at = datetime.utcnow()
        db.session.commit()
        
        flash('维修请求已更新为处理中状态。', 'success')
        return redirect(url_for('repair.request_detail', id=id))
    
    return render_template('repair/admin/start_repair.html', request=repair_request)

# 管理员完成维修
@repair_bp.route('/admin/complete-repair/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_complete_repair(id):
    if not current_user.is_admin():
        abort(403)
    
    repair_request = RepairRequest.query.get_or_404(id)
    
    if repair_request.status != 'in_progress':
        flash('只能完成正在处理中的报修请求。', 'danger')
        return redirect(url_for('repair.admin'))
    
    if request.method == 'POST':
        repair_request.status = 'completed'
        repair_request.completed_at = datetime.utcnow()
        db.session.commit()
        
        flash('维修请求已标记为完成。', 'success')
        return redirect(url_for('repair.request_detail', id=id))
    
    return render_template('repair/admin/complete_repair.html', request=repair_request)