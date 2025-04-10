import os
from flask import Flask
from extensions import db, login_manager, init_extensions
from dotenv import load_dotenv
from datetime import datetime, timezone
from models.user import User

# 加载环境变量
load_dotenv()

def create_app():
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    init_extensions(app)
    
    # 添加上下文处理器，提供全局变量给所有模板
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}
    
    # 注册蓝图
    from routes import main_bp
    from routes.auth import auth_bp
    from routes.restaurant import restaurant_bp
    from routes.shuttle import shuttle_bp
    from routes.housing import housing_bp
    from routes.repair import repair_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(restaurant_bp, url_prefix='/restaurant')
    app.register_blueprint(shuttle_bp, url_prefix='/shuttle')
    app.register_blueprint(housing_bp, url_prefix='/housing')
    app.register_blueprint(repair_bp, url_prefix='/repair')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

def create_admin():
    # 检查是否已存在admin用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # 创建新管理员
        admin = User(
            username='admin',
            email='admin@example.com',
            password='123456',  # 直接在构造函数中提供密码
            role='admin'  # 设置为管理员角色
        )
        db.session.add(admin)
        db.session.commit()
        print("管理员账号已创建成功! 用户名: admin, 密码: 123456")
    else:
        # 已存在admin用户，确保其为管理员角色并更新密码
        admin.role = 'admin'
        admin.set_password('123456')
        db.session.commit()
        print("管理员账号已更新! 用户名: admin, 密码: 123456")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_admin()
    app.run(host='0.0.0.0', port=5000, debug=True) 