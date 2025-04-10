from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.housing import Housing, HousingPhoto, HousingApplication, HousingContract
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm

housing_bp = Blueprint('housing', __name__, url_prefix='/housing')

# 设置上传文件夹
UPLOAD_FOLDER = 'admin_platform/static/uploads/housing'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 房源列表
@housing_bp.route('/')
def index():
    housing_list = Housing.query.filter_by(status='available').all()
    return render_template('housing/index.html', housing_list=housing_list)

# 房源详情
@housing_bp.route('/<int:id>')
def detail(id):
    housing = Housing.query.get_or_404(id)
    return render_template('housing/detail.html', housing=housing)

# 申请租房
@housing_bp.route('/<int:id>/apply', methods=['GET', 'POST'])
@login_required
def apply(id):
    housing = Housing.query.get_or_404(id)
    
    # 检查房源是否可用
    if housing.status != 'available':
        flash('该房源目前不可申请。', 'danger')
        return redirect(url_for('housing.detail', id=id))
    
    # 检查用户是否已有待处理的申请
    existing_application = HousingApplication.query.filter_by(
        user_id=current_user.id,
        housing_id=id,
        status='pending'
    ).first()
    
    if existing_application:
        flash('您已经申请了这个房源，请等待审核。', 'danger')
        return redirect(url_for('housing.my_applications'))
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        occupants = request.form.get('occupants', 1)
        purpose = request.form.get('purpose', '')
        
        if not start_date_str:
            flash('开始日期是必填项。', 'danger')
            return render_template('housing/apply.html', housing=housing, form=form)
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            
            # 验证开始日期
            if start_date < date.today():
                flash('开始日期不能是过去的日期。', 'danger')
                return render_template('housing/apply.html', housing=housing, form=form)
            
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                # 验证结束日期
                if end_date <= start_date:
                    flash('结束日期必须晚于开始日期。', 'danger')
                    return render_template('housing/apply.html', housing=housing, form=form)
            
            # 创建申请
            application = HousingApplication(
                user_id=current_user.id,
                housing_id=id,
                start_date=start_date,
                end_date=end_date,
                occupants=occupants,
                purpose=purpose
            )
            
            db.session.add(application)
            db.session.commit()
            
            flash('租房申请已提交！', 'success')
            return redirect(url_for('housing.my_applications'))
        except Exception as e:
            flash(f'申请失败：{str(e)}', 'danger')
    
    return render_template('housing/apply.html', housing=housing, form=form)

# 我的租房申请
@housing_bp.route('/my-applications')
@login_required
def my_applications():
    applications = HousingApplication.query.filter_by(user_id=current_user.id).order_by(HousingApplication.created_at.desc()).all()
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    return render_template('housing/my_applications.html', applications=applications, form=form)

# 查看我的合同
@housing_bp.route('/my-contracts')
@login_required
def my_contracts():
    contracts = HousingContract.query.join(HousingApplication).filter(HousingApplication.user_id == current_user.id).all()
    return render_template('housing/my_contracts.html', contracts=contracts)

# 取消申请
@housing_bp.route('/cancel-application/<int:id>', methods=['POST'])
@login_required
def cancel_application(id):
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if not form.validate_on_submit():
        flash('验证失败，无法处理此请求。', 'danger')
        return redirect(url_for('housing.my_applications'))
    
    application = HousingApplication.query.get_or_404(id)
    
    # 检查是否是当前用户的申请
    if application.user_id != current_user.id:
        abort(403)
    
    # 只能取消待处理的申请
    if application.status != 'pending':
        flash('只能取消待处理的申请。', 'danger')
        return redirect(url_for('housing.my_applications'))
    
    application.status = 'canceled'
    db.session.commit()
    
    flash('租房申请已成功取消。', 'success')
    return redirect(url_for('housing.my_applications'))

# ==== 管理员路由 ====

# 房源管理
@housing_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin():
        abort(403)
    
    housing_list = Housing.query.all()
    return render_template('housing/admin/index.html', housing_list=housing_list)

# 添加房源
@housing_bp.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_housing():
    if not current_user.is_admin():
        abort(403)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form.get('name')
        address = request.form.get('address')
        housing_type = request.form.get('type')
        area = request.form.get('area')
        floor = request.form.get('floor')
        rooms = request.form.get('rooms')
        price = request.form.get('price')
        deposit = request.form.get('deposit')
        is_furnished = 'is_furnished' in request.form
        facilities = request.form.get('facilities')
        description = request.form.get('description')
        
        if not name or not address or not price:
            flash('房源名称、地址和价格是必填项。', 'danger')
            return render_template('housing/admin/add_housing.html', form=form)
        
        try:
            price = float(price)
            deposit = float(deposit) if deposit else None
            area = float(area) if area else None
            floor = int(floor) if floor else None
            rooms = int(rooms) if rooms else None
            
            new_housing = Housing(
                name=name,
                address=address,
                type=housing_type,
                area=area,
                floor=floor,
                rooms=rooms,
                price=price,
                deposit=deposit,
                is_furnished=is_furnished,
                facilities=facilities,
                description=description
            )
            
            db.session.add(new_housing)
            db.session.commit()
            
            flash('房源添加成功！', 'success')
            return redirect(url_for('housing.admin'))
        except Exception as e:
            flash(f'添加失败：{str(e)}', 'danger')
    
    return render_template('housing/admin/add_housing.html', form=form)

# 编辑房源
@housing_bp.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_housing(id):
    if not current_user.is_admin():
        abort(403)
    
    housing = Housing.query.get_or_404(id)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        housing.name = request.form.get('name')
        housing.address = request.form.get('address')
        housing.type = request.form.get('type')
        
        try:
            housing.area = float(request.form.get('area')) if request.form.get('area') else None
            housing.floor = int(request.form.get('floor')) if request.form.get('floor') else None
            housing.rooms = int(request.form.get('rooms')) if request.form.get('rooms') else None
            housing.price = float(request.form.get('price'))
            housing.deposit = float(request.form.get('deposit')) if request.form.get('deposit') else None
        except ValueError:
            flash('请确保数值字段输入正确。', 'danger')
            return render_template('housing/admin/edit_housing.html', housing=housing, form=form)
        
        housing.is_furnished = 'is_furnished' in request.form
        housing.facilities = request.form.get('facilities')
        housing.description = request.form.get('description')
        housing.status = request.form.get('status')
        
        db.session.commit()
        
        flash('房源信息已更新。', 'success')
        return redirect(url_for('housing.admin'))
    
    return render_template('housing/admin/edit_housing.html', housing=housing, form=form)

# 管理房源照片
@housing_bp.route('/admin/photos/<int:housing_id>')
@login_required
def manage_photos(housing_id):
    if not current_user.is_admin():
        abort(403)
    
    housing = Housing.query.get_or_404(housing_id)
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    return render_template('housing/admin/photos.html', housing=housing, form=form)

# 添加房源照片
@housing_bp.route('/admin/photos/<int:housing_id>/add', methods=['GET', 'POST'])
@login_required
def add_photo(housing_id):
    if not current_user.is_admin():
        abort(403)
    
    housing = Housing.query.get_or_404(housing_id)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        description = request.form.get('description', '')
        
        # 检查是否有文件
        if 'photo' not in request.files:
            flash('未找到文件。', 'danger')
            return render_template('housing/admin/add_photo.html', housing=housing, form=form)
        
        file = request.files['photo']
        
        # 检查文件名是否为空
        if file.filename == '':
            flash('未选择文件。', 'danger')
            return render_template('housing/admin/add_photo.html', housing=housing, form=form)
        
        if file and allowed_file(file.filename):
            # 创建上传目录
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{housing_id}_{timestamp}_{filename}"
            
            # 保存文件
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # 创建数据库记录
            relative_path = f"uploads/housing/{filename}"
            photo = HousingPhoto(
                housing_id=housing_id,
                file_path=relative_path,
                description=description
            )
            
            db.session.add(photo)
            db.session.commit()
            
            flash('照片上传成功！', 'success')
            return redirect(url_for('housing.manage_photos', housing_id=housing_id))
        else:
            flash('不允许的文件类型。', 'danger')
    
    return render_template('housing/admin/add_photo.html', housing=housing, form=form)

# 删除房源照片
@housing_bp.route('/admin/photos/delete/<int:id>', methods=['POST'])
@login_required
def delete_photo(id):
    if not current_user.is_admin():
        abort(403)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if form.validate_on_submit():
        photo = HousingPhoto.query.get_or_404(id)
        housing_id = photo.housing_id
        
        # 删除文件
        try:
            file_path = os.path.join('admin_platform/static', photo.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            flash(f'删除文件时出错：{str(e)}', 'warning')
        
        # 删除数据库记录
        db.session.delete(photo)
        db.session.commit()
        
        flash('照片已删除。', 'success')
        return redirect(url_for('housing.manage_photos', housing_id=housing_id))
    
    flash('验证失败，无法删除照片。', 'danger')
    return redirect(url_for('housing.admin'))

# 管理租房申请
@housing_bp.route('/admin/applications')
@login_required
def manage_applications():
    if not current_user.is_admin():
        abort(403)
    
    status = request.args.get('status', 'pending')
    applications = HousingApplication.query.filter_by(status=status).order_by(HousingApplication.created_at.desc()).all()
    
    return render_template('housing/admin/applications.html', applications=applications, current_status=status)

# 处理租房申请
@housing_bp.route('/admin/applications/<int:id>', methods=['GET', 'POST'])
@login_required
def process_application(id):
    if not current_user.is_admin():
        abort(403)
    
    application = HousingApplication.query.get_or_404(id)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if status in ['approved', 'rejected']:
            application.status = status
            application.notes = notes
            
            # 如果批准了申请，将房源状态更新为已占用
            if status == 'approved':
                housing = Housing.query.get(application.housing_id)
                housing.status = 'occupied'
                
                # 创建合同
                contract_number = f"HC-{date.today().strftime('%Y%m%d')}-{application.id}"
                contract = HousingContract(
                    application_id=application.id,
                    contract_number=contract_number,
                    start_date=application.start_date,
                    end_date=application.end_date or application.start_date.replace(year=application.start_date.year + 1),
                    monthly_payment=application.housing.price,
                    payment_day=1
                )
                
                db.session.add(contract)
            
            db.session.commit()
            
            flash('申请已处理。', 'success')
            return redirect(url_for('housing.manage_applications'))
    
    return render_template('housing/admin/process_application.html', application=application, form=form)

# 管理租房合同
@housing_bp.route('/admin/contracts')
@login_required
def manage_contracts():
    if not current_user.is_admin():
        abort(403)
    
    status = request.args.get('status', 'active')
    contracts = HousingContract.query.filter_by(status=status).all()
    
    return render_template('housing/admin/contracts.html', contracts=contracts, current_status=status)

# 编辑租房合同
@housing_bp.route('/admin/contracts/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_contract(id):
    if not current_user.is_admin():
        abort(403)
    
    contract = HousingContract.query.get_or_404(id)
    
    # 创建表单对象用于CSRF保护
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            monthly_payment = request.form.get('monthly_payment')
            payment_day = request.form.get('payment_day')
            status = request.form.get('status')
            notes = request.form.get('notes')
            
            contract.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            contract.end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            contract.monthly_payment = float(monthly_payment)
            contract.payment_day = int(payment_day)
            contract.status = status
            contract.notes = notes
            
            # 如果合同状态变为终止或过期，更新房源状态为可用
            if status in ['terminated', 'expired']:
                application = HousingApplication.query.get(contract.application_id)
                housing = Housing.query.get(application.housing_id)
                housing.status = 'available'
            
            db.session.commit()
            
            flash('合同信息已更新。', 'success')
            return redirect(url_for('housing.manage_contracts'))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('housing/admin/edit_contract.html', contract=contract, form=form) 