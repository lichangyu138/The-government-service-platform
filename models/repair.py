from datetime import datetime
from extensions import db

class RepairCategory(db.Model):
    __tablename__ = 'repair_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与报修请求的关系
    repair_requests = db.relationship('RepairRequest', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<RepairCategory {self.name}>'

class RepairRequest(db.Model):
    __tablename__ = 'repair_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('repair_categories.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    contact_phone = db.Column(db.String(20))
    preferred_time = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    status = db.Column(db.String(20), default='pending')  # pending, assigned, in_progress, completed, canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 与报修人员的关系
    assignments = db.relationship('RepairAssignment', backref='request', lazy=True)
    
    # 与用户的关系
    user = db.relationship('User', backref=db.backref('repair_requests', lazy=True))
    
    # 与照片的关系
    photos = db.relationship('RepairPhoto', backref='request', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RepairRequest {self.id}: {self.title}>'

class RepairPhoto(db.Model):
    __tablename__ = 'repair_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RepairPhoto {self.id} for Request {self.request_id}>'

class RepairStaff(db.Model):
    __tablename__ = 'repair_staff'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    staff_number = db.Column(db.String(50), unique=True)
    specialty = db.Column(db.String(100))
    availability = db.Column(db.String(20), default='available')  # available, busy, off_duty, on_leave
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与用户的关系
    user = db.relationship('User', backref=db.backref('repair_staff', uselist=False))
    
    # 与分配任务的关系
    assignments = db.relationship('RepairAssignment', backref='staff', lazy=True)
    
    def __repr__(self):
        return f'<RepairStaff {self.staff_number}>'

class RepairAssignment(db.Model):
    __tablename__ = 'repair_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('repair_staff.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_time = db.Column(db.DateTime)
    completion_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='assigned')  # assigned, in_progress, completed, reassigned
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<RepairAssignment {self.id} for Request {self.request_id}>'

class RepairFeedback(db.Model):
    __tablename__ = 'repair_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5星评价
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    request = db.relationship('RepairRequest', backref=db.backref('feedback', uselist=False))
    user = db.relationship('User', backref=db.backref('repair_feedback', lazy=True))
    
    def __repr__(self):
        return f'<RepairFeedback {self.id} for Request {self.request_id}>' 