# 行政服务平台

这是一个基于Flask的行政服务平台，提供报修、班车、住宿等综合管理功能。

## 系统要求

- Python 3.8+
- Windows/Linux/MacOS

## 功能模块

1. **用户管理**: 管理员和普通用户角色区分
2. **报修管理**: 提交报修申请、处理流程跟踪、反馈评价
3. **班车管理**: 班车路线设置、预约乘坐
4. **住宿管理**: 住宿申请、合同管理

## 安装与运行

### 手动安装

1. 创建虚拟环境（推荐）:
```
python -m venv venv
venv\Scripts\activate
```

2. 安装依赖:
```
pip install -r requirements.txt
```

3. 启动应用:
```
python app.py
```

### 一键启动（Windows）

直接运行 `start.bat` 脚本，该脚本会自动:
1. 检查并创建虚拟环境
2. 安装所需的依赖
3. 启动Flask应用

## 默认账户

- 管理员: admin / 123456

## 开发说明

- 系统使用Flask框架开发
- 使用Flask-SQLAlchemy进行数据库操作
- 使用Flask-Login处理用户认证
- 使用Flask-WTF处理表单验证和CSRF保护

## 常见问题

1. **依赖安装失败**: 确保网络畅通，或尝试使用国内镜像源
   ```
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. **数据库错误**: 默认使用SQLite数据库，不需要额外配置。如需连接其他数据库，请修改.env文件中的DATABASE_URI 