from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 创建SQLAlchemy实例
db = SQLAlchemy()

# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    code_expires_at = db.Column(db.DateTime, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(50), nullable=False, default='新用户')
    avatar = db.Column(db.String(100), default='default_avatar.png')
    bio = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 密码加密
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # 密码验证
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # 关系
    channels = db.relationship('Channel', secondary='user_channels', back_populates='users')
    messages = db.relationship('Message', back_populates='sender')

# 频道模型
class Channel(db.Model):
    __tablename__ = 'channels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, default='')
    is_private = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', secondary='user_channels', back_populates='channels')
    messages = db.relationship('Message', back_populates='channel', order_by='Message.created_at')

# 用户-频道关联表
class UserChannel(db.Model):
    __tablename__ = 'user_channels'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# 消息模型
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False, default='')
    image = db.Column(db.String(255), nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    sender = db.relationship('User', back_populates='messages')
    channel = db.relationship('Channel', back_populates='messages')
