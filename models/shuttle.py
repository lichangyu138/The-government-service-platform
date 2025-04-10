from datetime import datetime
from extensions import db

class ShuttleRoute(db.Model):
    __tablename__ = 'shuttle_routes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_location = db.Column(db.String(200), nullable=False)
    end_location = db.Column(db.String(200), nullable=False)
    stops = db.Column(db.Text)  # 存储中间站点，以逗号分隔
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与班车时刻表的关系
    schedules = db.relationship('ShuttleSchedule', backref='route', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ShuttleRoute {self.name}>'

class ShuttleSchedule(db.Model):
    __tablename__ = 'shuttle_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('shuttle_routes.id', ondelete='CASCADE'), nullable=False)
    departure_time = db.Column(db.String(10), nullable=False)  # 格式: HH:MM
    arrival_time = db.Column(db.String(10), nullable=False)  # 格式: HH:MM
    days_of_week = db.Column(db.String(20), nullable=False)  # 例如：1,2,3,4,5 表示周一至周五
    capacity = db.Column(db.Integer, default=0)
    vehicle_info = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, canceled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShuttleSchedule {self.id} for Route {self.route_id}>'

class ShuttleReservation(db.Model):
    __tablename__ = 'shuttle_reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('shuttle_schedules.id'), nullable=False)
    reservation_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, canceled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    schedule = db.relationship('ShuttleSchedule', backref=db.backref('reservations', lazy=True))
    user = db.relationship('User', backref=db.backref('shuttle_reservations', lazy=True))
    
    def __repr__(self):
        return f'<ShuttleReservation {self.id} for Schedule {self.schedule_id}>' 