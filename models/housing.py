from datetime import datetime
from extensions import db

class Housing(db.Model):
    __tablename__ = 'housing'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # apartment, dormitory, house, etc.
    area = db.Column(db.Float)  # 面积，单位平方米
    floor = db.Column(db.Integer)
    rooms = db.Column(db.Integer)  # 房间数
    price = db.Column(db.Float, nullable=False)
    deposit = db.Column(db.Float)
    is_furnished = db.Column(db.Boolean, default=False)
    facilities = db.Column(db.Text)  # 设施，以逗号分隔
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 房屋照片关系
    photos = db.relationship('HousingPhoto', backref='housing', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Housing {self.name}>'

class HousingPhoto(db.Model):
    __tablename__ = 'housing_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    housing_id = db.Column(db.Integer, db.ForeignKey('housing.id', ondelete='CASCADE'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HousingPhoto {self.id} for Housing {self.housing_id}>'

class HousingApplication(db.Model):
    __tablename__ = 'housing_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    housing_id = db.Column(db.Integer, db.ForeignKey('housing.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    occupants = db.Column(db.Integer, default=1)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, canceled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    housing = db.relationship('Housing', backref=db.backref('applications', lazy=True))
    user = db.relationship('User', backref=db.backref('housing_applications', lazy=True))
    
    def __repr__(self):
        return f'<HousingApplication {self.id} for Housing {self.housing_id}>'

class HousingContract(db.Model):
    __tablename__ = 'housing_contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('housing_applications.id'), nullable=False)
    contract_number = db.Column(db.String(50), unique=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    monthly_payment = db.Column(db.Float, nullable=False)
    payment_day = db.Column(db.Integer, default=1)  # 每月几号付款
    status = db.Column(db.String(20), default='active')  # active, terminated, expired
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    application = db.relationship('HousingApplication', backref=db.backref('contract', uselist=False))
    
    def __repr__(self):
        return f'<HousingContract {self.contract_number}>' 