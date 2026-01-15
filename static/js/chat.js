// 全局变量
let socket = null;
let currentUser = null;
let currentChannel = null;
let channels = {
    joined: [],
    public: []
};

// 初始化聊天页面
async function initChat() {
    // 检查登录状态
    await checkLoginStatus();
    
    // 初始化WebSocket连接
    initWebSocket();
    
    // 加载频道列表
    await loadJoinedChannels();
    await loadPublicChannels();
    
    // 绑定事件监听器
    bindEventListeners();
}

// 检查登录状态
async function checkLoginStatus() {
    try {
        const response = await fetch('/api/check_login', {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success' && data.is_logged_in) {
            currentUser = data.user;
            updateUserInfo();
        } else {
            // 未登录，跳转到登录页面
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        window.location.href = '/login';
    }
}

// 更新用户信息
function updateUserInfo() {
    const usernameElement = document.getElementById('current-username');
    if (usernameElement) {
        usernameElement.textContent = currentUser.nickname || currentUser.username;
    }
}

// 初始化WebSocket连接
function initWebSocket() {
    // 创建WebSocket连接
    socket = io({
        autoConnect: true,
        credentials: true
    });
    
    // 连接成功
    socket.on('connect', () => {
        console.log('WebSocket连接成功');
    });
    
    // 连接断开
    socket.on('disconnect', () => {
        console.log('WebSocket连接断开');
    });
    
    // 接收新消息
    socket.on('new_message', (message) => {
        displayMessage(message);
    });
    
    // 接收系统通知
    socket.on('system_notification', (notification) => {
        displaySystemMessage(notification);
    });
    
    // 接收频道创建通知
    socket.on('channel_created', (data) => {
        // 添加到公开频道列表
        channels.public.push(data.channel);
        renderPublicChannels();
    });
    
    // 接收错误消息
    socket.on('error', (error) => {
        console.error('WebSocket错误:', error);
        alert(error.message);
    });
}

// 加载已加入的频道
async function loadJoinedChannels() {
    try {
        const response = await fetch('/api/channels/joined', {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            channels.joined = data.channels;
            renderJoinedChannels();
        }
    } catch (error) {
        console.error('加载已加入频道失败:', error);
    }
}

// 加载公开频道
async function loadPublicChannels() {
    try {
        const response = await fetch('/api/channels/public', {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            channels.public = data.channels;
            renderPublicChannels();
        }
    } catch (error) {
        console.error('加载公开频道失败:', error);
    }
}

// 渲染已加入频道列表
function renderJoinedChannels() {
    const container = document.getElementById('joined-channels-list');
    container.innerHTML = '';
    
    if (channels.joined.length === 0) {
        container.innerHTML = '<p class="no-channels">暂无已加入的频道</p>';
        return;
    }
    
    channels.joined.forEach(channel => {
        const channelElement = createChannelElement(channel);
        container.appendChild(channelElement);
    });
}

// 渲染公开频道列表
function renderPublicChannels() {
    const container = document.getElementById('public-channels-list');
    container.innerHTML = '';
    
    if (channels.public.length === 0) {
        container.innerHTML = '<p class="no-channels">暂无公开频道</p>';
        return;
    }
    
    channels.public.forEach(channel => {
        const channelElement = createChannelElement(channel);
        container.appendChild(channelElement);
    });
}

// 创建频道元素
function createChannelElement(channel) {
    const channelDiv = document.createElement('div');
    channelDiv.className = 'channel-item';
    channelDiv.dataset.channelId = channel.id;
    
    channelDiv.innerHTML = `
        <h4>${channel.name}</h4>
        <p>${channel.description || '暂无描述'}</p>
        <span class="user-count">${channel.user_count} 人</span>
    `;
    
    // 添加点击事件
    channelDiv.addEventListener('click', () => {
        selectChannel(channel);
    });
    
    return channelDiv;
}

// 选择频道
async function selectChannel(channel) {
    // 取消之前选中的频道
    document.querySelectorAll('.channel-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 标记当前选中的频道
    document.querySelector(`[data-channel-id="${channel.id}"]`).classList.add('active');
    
    // 更新当前频道
    currentChannel = channel;
    
    // 更新频道头部信息
    updateChannelHeader();
    
    // 加载频道消息历史
    await loadChannelMessages();
    
    // 加入WebSocket房间
    socket.emit('join_channel', {
        channel_id: channel.id
    });
    
    // 启用消息输入框
    enableMessageInput();
}

// 更新频道头部信息
function updateChannelHeader() {
    document.getElementById('current-channel-name').textContent = currentChannel.name;
    document.getElementById('current-channel-description').textContent = currentChannel.description || '暂无描述';
    document.getElementById('channel-user-count').textContent = `${currentChannel.user_count} 人`;
    
    // 更新频道操作按钮
    const actionBtn = document.getElementById('channel-action-btn');
    const isJoined = channels.joined.some(ch => ch.id === currentChannel.id);
    
    if (isJoined) {
        actionBtn.textContent = '退出频道';
        actionBtn.onclick = () => leaveChannel();
    } else {
        actionBtn.textContent = '加入频道';
        actionBtn.onclick = () => joinChannel();
    }
}

// 加载频道消息历史
async function loadChannelMessages() {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '<div class="loading">加载消息中...</div>';
    
    try {
        const response = await fetch(`/api/channels/${currentChannel.id}/messages`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        messagesContainer.innerHTML = '';
        
        if (data.status === 'success') {
            data.messages.forEach(message => {
                displayMessage(message);
            });
            
            // 滚动到底部
            scrollToBottom();
        }
    } catch (error) {
        console.error('加载消息历史失败:', error);
        messagesContainer.innerHTML = '<div class="error">加载消息失败</div>';
    }
}

// 显示消息
function displayMessage(message) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    
    // 检查是否是自己发送的消息
    const isOwnMessage = message.sender_id === currentUser.id;
    
    messageDiv.className = `message-item ${isOwnMessage ? 'own' : ''}`;
    
    // 格式化时间
    const time = new Date(message.created_at).toLocaleTimeString();
    
    // 构建头像HTML
    let avatarHtml = '';
    if (message.sender_avatar) {
        // 显示实际头像图片
        avatarHtml = `<img src="/${message.sender_avatar}" alt="${message.sender_nickname}" class="message-avatar-img">`;
    } else {
        // 显示文字头像作为默认值
        avatarHtml = `<div class="message-avatar-text">${message.sender_nickname.charAt(0)}</div>`;
    }
    
    // 构建消息内容HTML
    let messageContentHtml = '';
    if (message.image) {
        // 图片消息
        messageContentHtml = `
            <div class="message-header">
                <span class="message-sender">${message.sender_nickname}</span>
                <span class="message-time">${time}</span>
            </div>
        `;
        
        if (message.content) {
            messageContentHtml += `<div class="message-text">${escapeHtml(message.content)}</div>`;
        }
        
        messageContentHtml += `<img src="/${message.image}" alt="图片消息" class="message-image">`;
    } else {
        // 文本消息
        messageContentHtml = `
            <div class="message-header">
                <span class="message-sender">${message.sender_nickname}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${escapeHtml(message.content)}</div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarHtml}</div>
        <div class="message-content">
            ${messageContentHtml}
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 显示系统消息
function displaySystemMessage(notification) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = 'system-message';
    
    // 格式化时间
    const time = new Date(notification.created_at).toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="system-message-content">
            <span>${notification.content} - ${time}</span>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// 发送消息
async function sendMessage(e) {
    e.preventDefault();
    
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    const imageInput = document.getElementById('image-input');
    
    if ((!content && !imageInput.files.length) || !currentChannel) {
        return;
    }
    
    try {
        if (imageInput.files.length > 0) {
            // 发送图片消息
            await sendImageMessage(imageInput.files[0], content);
            // 清空图片输入
            imageInput.value = '';
        } else {
            // 发送文本消息
            socket.emit('send_message', {
                channel_id: currentChannel.id,
                content: content
            });
        }
        
        // 清空文本输入框
        messageInput.value = '';
    } catch (error) {
        console.error('发送消息失败:', error);
        alert('发送消息失败');
    }
}

// 发送图片消息
async function sendImageMessage(imageFile, textContent = '') {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('channel_id', currentChannel.id);
    if (textContent) {
        formData.append('content', textContent);
    }
    
    try {
        const response = await fetch('/api/send_image_message', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const data = await response.json();
        if (data.status !== 'success') {
            throw new Error(data.message || '发送图片失败');
        }
    } catch (error) {
        console.error('发送图片消息失败:', error);
        alert('发送图片消息失败');
        throw error;
    }
}

// 加入频道
async function joinChannel() {
    if (!currentChannel) return;
    
    try {
        const response = await fetch(`/api/channels/${currentChannel.id}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 添加到已加入频道列表
            channels.joined.push(currentChannel);
            renderJoinedChannels();
            
            // 更新频道头部
            updateChannelHeader();
            
            // 刷新频道用户数量
            currentChannel.user_count += 1;
            renderPublicChannels();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('加入频道失败:', error);
        alert('加入频道失败');
    }
}

// 退出频道
async function leaveChannel() {
    if (!currentChannel) return;
    
    try {
        const response = await fetch(`/api/channels/${currentChannel.id}/leave`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 从已加入频道列表中移除
            channels.joined = channels.joined.filter(ch => ch.id !== currentChannel.id);
            renderJoinedChannels();
            
            // 刷新频道用户数量
            currentChannel.user_count -= 1;
            renderPublicChannels();
            
            // 重置当前频道
            currentChannel = null;
            resetChannelHeader();
            disableMessageInput();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('退出频道失败:', error);
        alert('退出频道失败');
    }
}

// 重置频道头部
function resetChannelHeader() {
    document.getElementById('current-channel-name').textContent = '选择一个频道开始聊天';
    document.getElementById('current-channel-description').textContent = '';
    document.getElementById('channel-user-count').textContent = '';
    document.getElementById('channel-action-btn').textContent = '';
    document.getElementById('channel-action-btn').onclick = null;
    
    // 清空消息容器
    document.getElementById('messages').innerHTML = '';
}

// 启用消息输入框
function enableMessageInput() {
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('image-btn').disabled = false;
    document.getElementById('message-input').focus();
}

// 禁用消息输入框
function disableMessageInput() {
    document.getElementById('message-input').disabled = true;
    document.getElementById('send-btn').disabled = true;
    document.getElementById('image-btn').disabled = true;
}

// 滚动到底部
function scrollToBottom() {
    const messagesContainer = document.getElementById('messages-container');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 转义HTML字符，防止XSS攻击
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 创建频道
async function createChannel(e) {
    e.preventDefault();
    
    const name = document.getElementById('channel-name').value.trim();
    const description = document.getElementById('channel-description').value.trim();
    const isPrivate = document.getElementById('channel-private').checked;
    
    if (!name) {
        alert('频道名称不能为空');
        return;
    }
    
    try {
        const response = await fetch('/api/channels', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                description,
                is_private: isPrivate
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 关闭模态框
            closeModal();
            
            // 重置表单
            document.getElementById('create-channel-form').reset();
            
            // 重新加载频道列表
            await loadJoinedChannels();
            await loadPublicChannels();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('创建频道失败:', error);
        alert('创建频道失败');
    }
}

// 显示创建频道模态框
function showCreateChannelModal() {
    const modal = document.getElementById('create-channel-modal');
    modal.classList.add('active');
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('create-channel-modal');
    modal.classList.remove('active');
}

// 搜索频道
async function searchChannels() {
    const keyword = document.getElementById('channel-search').value.trim();
    
    // 切换到公开频道标签页，因为搜索功能只搜索公开频道
    document.querySelector('.tab-btn[data-tab="public"]').click();
    
    if (!keyword) {
        // 关键词为空，重新加载公开频道
        await loadPublicChannels();
        return;
    }
    
    try {
        const response = await fetch(`/api/channels/search?q=${encodeURIComponent(keyword)}`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 显示搜索结果
            const publicChannelsList = document.getElementById('public-channels-list');
            publicChannelsList.innerHTML = '';
            
            if (data.channels.length === 0) {
                publicChannelsList.innerHTML = '<p class="no-channels">未找到匹配的频道</p>';
                return;
            }
            
            data.channels.forEach(channel => {
                const channelElement = createChannelElement(channel);
                publicChannelsList.appendChild(channelElement);
            });
        }
    } catch (error) {
        console.error('搜索频道失败:', error);
    }
}

// 登出
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 断开WebSocket连接
            if (socket) {
                socket.disconnect();
            }
            
            // 跳转到登录页面
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('登出失败:', error);
        window.location.href = '/login';
    }
}

// 绑定事件监听器
function bindEventListeners() {
    // 消息表单提交
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', sendMessage);
    }
    
    // 创建频道按钮
    const createChannelBtn = document.getElementById('create-channel-btn');
    if (createChannelBtn) {
        createChannelBtn.addEventListener('click', showCreateChannelModal);
    }
    
    // 关闭模态框按钮
    const closeModalBtn = document.getElementById('close-modal');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }
    
    // 创建频道表单提交
    const createChannelForm = document.getElementById('create-channel-form');
    if (createChannelForm) {
        createChannelForm.addEventListener('submit', createChannel);
    }
    
    // 搜索按钮
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchChannels);
    }
    
    // 搜索输入框回车事件
    const searchInput = document.getElementById('channel-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchChannels();
            }
        });
    }
    
    // 登出按钮
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // 模态框外部点击关闭
    const modal = document.getElementById('create-channel-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // 标签页切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // 切换标签页激活状态
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 切换频道列表
            const tab = btn.dataset.tab;
            document.querySelectorAll('.channel-list').forEach(list => {
                list.classList.remove('active');
            });
            document.getElementById(`${tab}-channels`).classList.add('active');
        });
    });
    
    // 图片按钮点击事件
    const imageBtn = document.getElementById('image-btn');
    if (imageBtn) {
        imageBtn.addEventListener('click', () => {
            document.getElementById('image-input').click();
        });
    }
    
    // 图片选择事件
    const imageInput = document.getElementById('image-input');
    if (imageInput) {
        imageInput.addEventListener('change', (e) => {
            // 如果选择了文件，自动聚焦到消息输入框，方便用户添加文字描述
            if (e.target.files.length > 0) {
                document.getElementById('message-input').focus();
            }
        });
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', initChat);
