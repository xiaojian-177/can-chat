// 全局变量
let currentUser = null;

// 初始化个人资料页面
async function initProfile() {
    // 检查登录状态并加载用户信息
    await loadUserInfo();
    
    // 绑定事件监听器
    bindEventListeners();
}

// 加载用户信息
async function loadUserInfo() {
    try {
        const response = await fetch('/api/user', {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentUser = data.user;
            fillProfileForm();
            initAvatarPreview();
        } else {
            // 未登录，跳转到登录页面
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
        window.location.href = '/login';
    }
}

// 填充个人资料表单
function fillProfileForm() {
    document.getElementById('username').value = currentUser.username;
    document.getElementById('nickname').value = currentUser.nickname;
    document.getElementById('avatar').value = currentUser.avatar || '';
    document.getElementById('bio').value = currentUser.bio || '';
}

// 初始化头像预览
function initAvatarPreview() {
    const avatarPreview = document.getElementById('avatar-preview');
    
    // 如果用户已有头像，显示预览
    if (currentUser.avatar) {
        // 确保头像路径正确
        avatarPreview.src = `/${currentUser.avatar}`;
        avatarPreview.style.display = 'block';
    } else {
        // 设置默认头像
        avatarPreview.src = '/static/img/default_avatar.png';
        avatarPreview.style.display = 'block';
    }
}

// 修复头像上传成功后更新逻辑
async function uploadAvatar() {
    const fileInput = document.getElementById('avatar-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('请先选择要上传的图片', 'error');
        return;
    }
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('avatar', file);
    
    try {
        // 显示上传中消息
        showMessage('正在上传头像...', 'success');
        
        // 发送上传请求
        const response = await fetch('/api/upload/avatar', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 上传成功，更新表单中的头像值
            document.getElementById('avatar').value = data.avatar;
            // 更新当前用户的头像
            currentUser.avatar = data.avatar;
            // 更新头像预览
            initAvatarPreview();
            // 显示成功消息
            showMessage('头像上传成功', 'success');
        } else {
            // 上传失败
            showMessage(data.message || '头像上传失败', 'error');
        }
    } catch (error) {
        console.error('上传头像失败:', error);
        showMessage('上传失败，请稍后重试', 'error');
    }
}

// 更新个人资料
async function updateProfile(e) {
    e.preventDefault();
    
    const nickname = document.getElementById('nickname').value.trim();
    const avatar = document.getElementById('avatar').value.trim();
    const bio = document.getElementById('bio').value.trim();
    
    if (!nickname) {
        showMessage('昵称不能为空', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/user', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                nickname,
                avatar,
                bio
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showMessage('个人资料更新成功', 'success');
            // 更新当前用户信息
            currentUser = data.user;
            // 更新头像预览
            initAvatarPreview();
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        console.error('更新个人资料失败:', error);
        showMessage('更新失败，请稍后重试', 'error');
    }
}

// 显示消息
function showMessage(message, type = 'success') {
    const messageElement = document.getElementById('profile-message');
    
    messageElement.textContent = message;
    messageElement.className = `message ${type === 'error' ? 'error-message' : 'message'}`;
    messageElement.style.display = 'block';
    
    // 3秒后自动隐藏
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 3000);
}

// 绑定事件监听器
function bindEventListeners() {
    // 个人资料表单提交
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', updateProfile);
    }
}

// 预览头像
function previewAvatar() {
    const fileInput = document.getElementById('avatar-file');
    const preview = document.getElementById('avatar-preview');
    
    const file = fileInput.files[0];
    if (file) {
        // 检查文件大小（16MB）
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            showMessage('文件大小超过限制，最大16MB', 'error');
            fileInput.value = '';
            return;
        }
        
        // 检查文件类型
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            showMessage('只允许上传PNG、JPG、JPEG和GIF格式的图片', 'error');
            fileInput.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
}

// 上传头像
async function uploadAvatar() {
    const fileInput = document.getElementById('avatar-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('请先选择要上传的图片', 'error');
        return;
    }
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('avatar', file);
    
    try {
        // 显示上传中消息
        showMessage('正在上传头像...', 'success');
        
        // 发送上传请求
        const response = await fetch('/api/upload/avatar', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 上传成功，更新表单中的头像值
            document.getElementById('avatar').value = data.avatar;
            // 更新当前用户的头像
            currentUser.avatar = data.avatar;
            // 更新头像预览
            initAvatarPreview();
            // 显示成功消息
            showMessage('头像上传成功', 'success');
        } else {
            // 上传失败
            showMessage(data.message || '头像上传失败', 'error');
        }
    } catch (error) {
        console.error('上传头像失败:', error);
        showMessage('上传失败，请稍后重试', 'error');
    }
}

// 绑定事件监听器
function bindEventListeners() {
    // 个人资料表单提交
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', updateProfile);
    }
    
    // 文件选择事件，预览头像
    const avatarFileInput = document.getElementById('avatar-file');
    if (avatarFileInput) {
        avatarFileInput.addEventListener('change', previewAvatar);
    }
    
    // 上传头像按钮点击事件
    const uploadAvatarBtn = document.getElementById('upload-avatar-btn');
    if (uploadAvatarBtn) {
        uploadAvatarBtn.addEventListener('click', uploadAvatar);
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initProfile);
