from datetime import datetime
from extensions import db

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, default=0)
    opening_hours = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, closed, renovating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与菜单的关系
    menus = db.relationship('Menu', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Restaurant {self.name}>'

class Menu(db.Model):
    __tablename__ = 'menus'
    
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # breakfast, lunch, dinner, etc.
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Menu {self.name}>'

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    reservation_time = db.Column(db.DateTime, nullable=False)
    party_size = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, canceled, completed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    restaurant = db.relationship('Restaurant', backref=db.backref('reservations', lazy=True))
    user = db.relationship('User', backref=db.backref('reservations', lazy=True))
    
    def __repr__(self):
        return f'<Reservation {self.id} for Restaurant {self.restaurant_id}>' 