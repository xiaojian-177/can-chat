from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_migrate import Migrate
from models import db, User, Channel, UserChannel, Message
from datetime import datetime, timedelta
import os
import uuid
import random
from werkzeug.utils import secure_filename
from apis import send_verify_email

# 创建Flask应用
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# 配置
app.config['SECRET_KEY'] = 'can-chat-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 文件上传配置
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'img', 'avatars')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化扩展
CORS(app, supports_credentials=True)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins='*', supports_credentials=True)

# 初始化Flask-Migrate
migrate = Migrate(app, db)

# 创建数据库表
with app.app_context():
    db.create_all()

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 登录页面
@app.route('/login')
def login_page():
    return render_template('login.html')

# 注册页面
@app.route('/register')
def register_page():
    return render_template('register.html')

# 聊天页面
@app.route('/chat')
def chat_page():
    return render_template('chat.html')

# 用户资料页面
@app.route('/profile')
def profile_page():
    return render_template('profile.html')

# 辅助函数：检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# API路由 - 健康检查
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'CAN-Chat API is running'})

# API路由 - 上传头像
@app.route('/api/upload/avatar', methods=['POST'])
def upload_avatar():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    # 检查是否有文件上传
    if 'avatar' not in request.files:
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    file = request.files['avatar']
    
    # 检查文件是否为空
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': '只允许上传PNG、JPG、JPEG和GIF格式的图片'}), 400
    
    try:
        # 生成唯一的文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 更新用户头像
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 更新头像路径（保存完整的相对路径，确保前端可以正确访问）
        user.avatar = f"static/img/avatars/{unique_filename}"
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': '头像上传成功', 
            'avatar': user.avatar
        })
    except Exception as e:
        print(f"上传头像失败: {e}")
        return jsonify({'status': 'error', 'message': '上传失败，请稍后重试'}), 500

# API路由 - 发送邮箱验证码
@app.route('/api/send_verification_code', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
    
    email = data.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': '邮箱不能为空'}), 400
    
    try:
        # 检查邮箱是否已被注册
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.email_verified:
            return jsonify({'status': 'error', 'message': '该邮箱已被注册'}), 400
        
        # 生成6位数字验证码
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # 更新或创建用户的验证码信息
        if existing_user:
            existing_user.verification_code = code
            existing_user.code_expires_at = expires_at
        else:
            # 只存储验证码信息，不创建完整用户
            pass  # 完整用户将在注册时创建
        
        db.session.commit()
        
        # 发送验证码邮件
        send_verify_email(email, code)
        
        return jsonify({'status': 'success', 'message': '验证码已发送，有效期5分钟'})
    except Exception as e:
        print(f"发送验证码失败: {e}")
        return jsonify({'status': 'error', 'message': '发送验证码失败，请稍后重试'}), 500

# API路由 - 发送图片消息
@app.route('/api/send_image_message', methods=['POST'])
def send_image_message():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    # 检查是否有图片上传
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': '未选择图片'}), 400
    
    image_file = request.files['image']
    channel_id = request.form.get('channel_id')
    content = request.form.get('content', '')
    
    if not channel_id:
        return jsonify({'status': 'error', 'message': '缺少频道ID'}), 400
    
    try:
        # 检查频道是否存在
        channel = Channel.query.get(channel_id)
        if not channel:
            return jsonify({'status': 'error', 'message': '频道不存在'}), 404
        
        # 检查用户是否已加入频道
        existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
        if not existing:
            return jsonify({'status': 'error', 'message': '未加入该频道'}), 403
        
        # 保存图片
        if image_file.filename == '':
            return jsonify({'status': 'error', 'message': '未选择图片'}), 400
        
        if not allowed_file(image_file.filename):
            return jsonify({'status': 'error', 'message': '只允许上传PNG、JPG、JPEG和GIF格式的图片'}), 400
        
        # 生成唯一的文件名
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        # 保存到消息图片目录
        message_image_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'messages')
        os.makedirs(message_image_folder, exist_ok=True)
        file_path = os.path.join(message_image_folder, unique_filename)
        image_file.save(file_path)
        
        # 保存消息到数据库
        message = Message(
            content=content,
            image=f"static/img/avatars/messages/{unique_filename}",
            sender_id=user_id,
            channel_id=channel_id
        )
        db.session.add(message)
        db.session.commit()
        
        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 构建消息数据
        message_data = {
            'id': message.id,
            'type': 'message',
            'content': message.content,
            'image': message.image,
            'sender_id': message.sender_id,
            'sender_nickname': user.nickname,
            'sender_avatar': user.avatar,
            'channel_id': message.channel_id,
            'created_at': message.created_at.isoformat()
        }
        
        # 通过WebSocket广播消息
        socketio.emit('new_message', message_data, room=str(channel_id))
        
        return jsonify({'status': 'success', 'message': '图片消息发送成功', 'message_data': message_data})
    except Exception as e:
        print(f"发送图片消息失败: {e}")
        return jsonify({'status': 'error', 'message': '发送图片消息失败，请稍后重试'}), 500

# API路由 - 验证邮箱
@app.route('/api/verify_email', methods=['POST'])
def verify_email():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
    
    email = data.get('email')
    code = data.get('code')
    
    if not email or not code:
        return jsonify({'status': 'error', 'message': '邮箱和验证码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 验证验证码
    if user.verification_code != code:
        return jsonify({'status': 'error', 'message': '验证码错误'}), 400
    
    if user.code_expires_at < datetime.utcnow():
        return jsonify({'status': 'error', 'message': '验证码已过期'}), 400
    
    # 标记邮箱已验证
    user.email_verified = True
    user.verification_code = None
    user.code_expires_at = None
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '邮箱验证成功'})

# API路由 - 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    code = data.get('code')
    nickname = data.get('nickname', '新用户')
    
    if not username or not password or not email or not code:
        return jsonify({'status': 'error', 'message': '用户名、密码、邮箱和验证码不能为空'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': '该邮箱已被注册'}), 400
    
    # 创建新用户
    user = User(
        username=username,
        email=email,
        nickname=nickname
    )
    user.set_password(password)
    
    # 验证验证码
    user.verification_code = code
    user.code_expires_at = datetime.utcnow() + timedelta(minutes=5)  # 临时设置有效期，后续将验证
    db.session.add(user)
    db.session.commit()
    
    # 验证邮箱
    verify_result = verify_email_internal(user, code)
    if not verify_result['success']:
        db.session.delete(user)  # 验证失败，删除用户
        db.session.commit()
        return jsonify({'status': 'error', 'message': verify_result['message']}), 400
    
    return jsonify({'status': 'success', 'message': '注册成功', 'user_id': user.id})

# 内部函数：验证邮箱
def verify_email_internal(user, code):
    if user.verification_code != code:
        return {'success': False, 'message': '验证码错误'}
    
    if user.code_expires_at < datetime.utcnow():
        return {'success': False, 'message': '验证码已过期'}
    
    # 标记邮箱已验证
    user.email_verified = True
    user.verification_code = None
    user.code_expires_at = None
    return {'success': True, 'message': '邮箱验证成功'}

# API路由 - 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400
    
    # 验证用户
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 设置会话
    session['user_id'] = user.id
    session.permanent = remember
    
    return jsonify({'status': 'success', 'message': '登录成功', 'user': {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'bio': user.bio,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat()
    }})

# API路由 - 用户登出
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'status': 'success', 'message': '登出成功'})

# API路由 - 获取当前用户信息
@app.route('/api/user', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    return jsonify({'status': 'success', 'user': {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'bio': user.bio,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat()
    }})

# API路由 - 检查登录状态
@app.route('/api/check_login', methods=['GET'])
def check_login():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录', 'is_logged_in': False}), 401
    
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return jsonify({'status': 'error', 'message': '用户不存在', 'is_logged_in': False}), 404
    
    return jsonify({'status': 'success', 'is_logged_in': True, 'user': {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'bio': user.bio
    }})

# API路由 - 创建频道
@app.route('/api/channels', methods=['POST'])
def create_channel():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
    
    name = data.get('name')
    description = data.get('description', '')
    is_private = data.get('is_private', False)
    
    if not name:
        return jsonify({'status': 'error', 'message': '频道名称不能为空'}), 400
    
    # 创建频道
    channel = Channel(
        name=name,
        description=description,
        is_private=is_private,
        created_by=user_id
    )
    db.session.add(channel)
    
    # 先提交频道对象，生成ID
    db.session.commit()
    
    # 创建者自动加入频道
    user_channel = UserChannel(user_id=user_id, channel_id=channel.id)
    db.session.add(user_channel)
    
    db.session.commit()
    
    # 发送系统通知（通过WebSocket广播给所有连接的客户端）
    socketio.emit('channel_created', {
        'channel': {
            'id': channel.id,
            'name': channel.name,
            'description': channel.description,
            'is_private': channel.is_private,
            'created_by': channel.created_by,
            'created_at': channel.created_at.isoformat(),
            'user_count': 1
        }
    })
    
    return jsonify({'status': 'success', 'message': '频道创建成功', 'channel': {
        'id': channel.id,
        'name': channel.name,
        'description': channel.description,
        'is_private': channel.is_private,
        'created_by': channel.created_by,
        'created_at': channel.created_at.isoformat(),
        'user_count': 1
    }})

# API路由 - 获取公开频道列表
@app.route('/api/channels/public', methods=['GET'])
def get_public_channels():
    channels = Channel.query.filter_by(is_private=False).order_by(Channel.created_at.desc()).all()
    
    channel_list = []
    for channel in channels:
        # 获取频道用户数量
        user_count = UserChannel.query.filter_by(channel_id=channel.id).count()
        channel_list.append({
            'id': channel.id,
            'name': channel.name,
            'description': channel.description,
            'is_private': channel.is_private,
            'created_by': channel.created_by,
            'created_at': channel.created_at.isoformat(),
            'user_count': user_count
        })
    
    return jsonify({'status': 'success', 'channels': channel_list})

# API路由 - 搜索频道
@app.route('/api/channels/search', methods=['GET'])
def search_channels():
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({'status': 'error', 'message': '搜索关键词不能为空'}), 400
    
    channels = Channel.query.filter(
        Channel.is_private == False,
        Channel.name.like(f'%{keyword}%') | Channel.description.like(f'%{keyword}%')
    ).order_by(Channel.created_at.desc()).all()
    
    channel_list = []
    for channel in channels:
        user_count = UserChannel.query.filter_by(channel_id=channel.id).count()
        channel_list.append({
            'id': channel.id,
            'name': channel.name,
            'description': channel.description,
            'is_private': channel.is_private,
            'created_by': channel.created_by,
            'created_at': channel.created_at.isoformat(),
            'user_count': user_count
        })
    
    return jsonify({'status': 'success', 'channels': channel_list})

# API路由 - 加入频道
@app.route('/api/channels/<int:channel_id>/join', methods=['POST'])
def join_channel(channel_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    # 检查频道是否存在
    channel = Channel.query.get(channel_id)
    if not channel:
        return jsonify({'status': 'error', 'message': '频道不存在'}), 404
    
    # 检查是否已经加入频道
    existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
    if existing:
        return jsonify({'status': 'error', 'message': '已经加入该频道'}), 400
    
    # 加入频道
    user_channel = UserChannel(user_id=user_id, channel_id=channel_id)
    db.session.add(user_channel)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '成功加入频道'})

# API路由 - 退出频道
@app.route('/api/channels/<int:channel_id>/leave', methods=['POST'])
def leave_channel(channel_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    # 检查频道是否存在
    channel = Channel.query.get(channel_id)
    if not channel:
        return jsonify({'status': 'error', 'message': '频道不存在'}), 404
    
    # 检查是否是频道创建者
    if channel.created_by == user_id:
        return jsonify({'status': 'error', 'message': '创建者不能退出自己的频道'}), 400
    
    # 检查是否已经加入频道
    existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
    if not existing:
        return jsonify({'status': 'error', 'message': '未加入该频道'}), 400
    
    # 退出频道
    db.session.delete(existing)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '成功退出频道'})

# API路由 - 获取用户加入的频道
@app.route('/api/channels/joined', methods=['GET'])
def get_joined_channels():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    # 获取用户加入的频道
    user_channels = UserChannel.query.filter_by(user_id=user_id).all()
    channel_ids = [uc.channel_id for uc in user_channels]
    channels = Channel.query.filter(Channel.id.in_(channel_ids)).order_by(Channel.created_at.desc()).all()
    
    channel_list = []
    for channel in channels:
        user_count = UserChannel.query.filter_by(channel_id=channel.id).count()
        channel_list.append({
            'id': channel.id,
            'name': channel.name,
            'description': channel.description,
            'is_private': channel.is_private,
            'created_by': channel.created_by,
            'created_at': channel.created_at.isoformat(),
            'user_count': user_count
        })
    
    return jsonify({'status': 'success', 'channels': channel_list})

# API路由 - 获取频道详情
@app.route('/api/channels/<int:channel_id>', methods=['GET'])
def get_channel_detail(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return jsonify({'status': 'error', 'message': '频道不存在'}), 404
    
    # 获取频道用户数量
    user_count = UserChannel.query.filter_by(channel_id=channel.id).count()
    
    # 检查当前用户是否已加入频道
    is_joined = False
    user_id = session.get('user_id')
    if user_id:
        existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
        is_joined = existing is not None
    
    return jsonify({'status': 'success', 'channel': {
        'id': channel.id,
        'name': channel.name,
        'description': channel.description,
        'is_private': channel.is_private,
        'created_by': channel.created_by,
        'created_at': channel.created_at.isoformat(),
        'user_count': user_count,
        'is_joined': is_joined
    }})

# API路由 - 获取频道消息历史
@app.route('/api/channels/<int:channel_id>/messages', methods=['GET'])
def get_channel_messages(channel_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    # 检查用户是否已加入频道
    existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
    if not existing:
        return jsonify({'status': 'error', 'message': '未加入该频道'}), 403
    
    # 获取频道消息，按时间排序
    messages = Message.query.filter_by(channel_id=channel_id).order_by(Message.created_at.asc()).all()
    
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'content': msg.content,
            'image': msg.image,
            'sender_id': msg.sender_id,
            'sender_nickname': msg.sender.nickname,
            'sender_avatar': msg.sender.avatar,
            'channel_id': msg.channel_id,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({'status': 'success', 'messages': message_list})

# WebSocket事件 - 连接建立
@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if user_id:
        print(f'用户 {user_id} 已连接')
        # 更新用户最后登录时间
        user = User.query.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.session.commit()
    else:
        print('匿名用户已连接')

# WebSocket事件 - 连接断开
@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    if user_id:
        print(f'用户 {user_id} 已断开连接')
    else:
        print('匿名用户已断开连接')

# WebSocket事件 - 加入频道
@socketio.on('join_channel')
def handle_join_channel(data):
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '未登录'})
        return
    
    channel_id = data.get('channel_id')
    if not channel_id:
        emit('error', {'message': '缺少频道ID'})
        return
    
    # 检查用户是否已加入频道
    existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
    if not existing:
        emit('error', {'message': '未加入该频道'})
        return
    
    # 加入房间
    join_room(str(channel_id))
    
    # 获取用户信息
    user = User.query.get(user_id)
    if not user:
        emit('error', {'message': '用户不存在'})
        return
    
    # 发送系统通知
    system_message = {
        'type': 'system',
        'content': f'{user.nickname} 加入了频道',
        'channel_id': channel_id,
        'created_at': datetime.utcnow().isoformat()
    }
    emit('system_notification', system_message, room=str(channel_id))
    
    print(f'用户 {user.nickname} 加入了频道 {channel_id}')

# WebSocket事件 - 离开频道
@socketio.on('leave_channel')
def handle_leave_channel(data):
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '未登录'})
        return
    
    channel_id = data.get('channel_id')
    if not channel_id:
        emit('error', {'message': '缺少频道ID'})
        return
    
    # 离开房间
    leave_room(str(channel_id))
    
    # 获取用户信息
    user = User.query.get(user_id)
    if not user:
        emit('error', {'message': '用户不存在'})
        return
    
    # 发送系统通知
    system_message = {
        'type': 'system',
        'content': f'{user.nickname} 离开了频道',
        'channel_id': channel_id,
        'created_at': datetime.utcnow().isoformat()
    }
    emit('system_notification', system_message, room=str(channel_id))
    
    print(f'用户 {user.nickname} 离开了频道 {channel_id}')

# WebSocket事件 - 发送消息
@socketio.on('send_message')
def handle_send_message(data):
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'message': '未登录'})
        return
    
    channel_id = data.get('channel_id')
    content = data.get('content')
    
    if not channel_id or not content:
        emit('error', {'message': '缺少频道ID或消息内容'})
        return
    
    # 检查用户是否已加入频道
    existing = UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).first()
    if not existing:
        emit('error', {'message': '未加入该频道'})
        return
    
    # 保存消息到数据库
    message = Message(
        content=content,
        sender_id=user_id,
        channel_id=channel_id
    )
    db.session.add(message)
    db.session.commit()
    
    # 获取完整的消息数据
    user = User.query.get(user_id)
    if not user:
        emit('error', {'message': '用户不存在'})
        return
    
    message_data = {
        'id': message.id,
        'type': 'message',
        'content': message.content,
        'sender_id': message.sender_id,
        'sender_nickname': user.nickname,
        'sender_avatar': user.avatar,
        'channel_id': message.channel_id,
        'created_at': message.created_at.isoformat()
    }
    
    # 广播消息到频道
    emit('new_message', message_data, room=str(channel_id))
    
    print(f'用户 {user.nickname} 在频道 {channel_id} 发送了消息: {content}')

# WebSocket事件 - 新频道创建通知
@socketio.on('new_channel_created')
def handle_new_channel_created(data):
    # 这个事件主要用于前端通知，后端不需要额外处理
    pass

# API路由 - 更新个人信息
@app.route('/api/user', methods=['PUT'])
def update_user_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '缺少请求数据'}), 400
    
    # 获取用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 更新用户信息
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'bio' in data:
        user.bio = data['bio']
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '个人信息更新成功', 'user': {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'bio': user.bio,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat()
    }})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3080, debug=True)
