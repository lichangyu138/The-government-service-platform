from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# 初始化扩展，但不与应用实例绑定
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_extensions(app):
    # 初始化数据库和登录管理器
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # 导入模型，确保它们在创建所有表之前被定义
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id)) 