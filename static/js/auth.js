// 登录表单提交处理
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                    remember
                }),
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // 登录成功，跳转到聊天页面
                window.location.href = '/chat';
            } else {
                // 登录失败，显示错误消息
                loginError.textContent = data.message;
                loginError.style.display = 'block';
            }
        } catch (error) {
            console.error('登录请求失败:', error);
            loginError.textContent = '登录失败，请稍后重试';
            loginError.style.display = 'block';
        }
    });
}

// 注册表单提交处理
const registerForm = document.getElementById('register-form');
const registerError = document.getElementById('register-error');
const sendCodeBtn = document.getElementById('send-code-btn');

if (registerForm) {
    // 发送验证码按钮点击事件
    if (sendCodeBtn) {
        sendCodeBtn.addEventListener('click', async () => {
            const email = document.getElementById('email').value;
            if (!email) {
                registerError.textContent = '请先输入邮箱';
                registerError.style.display = 'block';
                return;
            }
            
            // 验证邮箱格式
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                registerError.textContent = '请输入有效的邮箱地址';
                registerError.style.display = 'block';
                return;
            }
            
            try {
                // 禁用发送按钮
                sendCodeBtn.disabled = true;
                sendCodeBtn.textContent = '发送中...';
                
                const response = await fetch('/api/send_verification_code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    registerError.textContent = data.message;
                    registerError.style.display = 'block';
                    registerError.className = 'message success';
                    
                    // 倒计时60秒
                    let countdown = 60;
                    sendCodeBtn.textContent = `${countdown}秒后重试`;
                    
                    const timer = setInterval(() => {
                        countdown--;
                        sendCodeBtn.textContent = `${countdown}秒后重试`;
                        if (countdown <= 0) {
                            clearInterval(timer);
                            sendCodeBtn.disabled = false;
                            sendCodeBtn.textContent = '发送验证码';
                        }
                    }, 1000);
                } else {
                    registerError.textContent = data.message;
                    registerError.style.display = 'block';
                    registerError.className = 'error-message';
                    sendCodeBtn.disabled = false;
                    sendCodeBtn.textContent = '发送验证码';
                }
            } catch (error) {
                console.error('发送验证码失败:', error);
                registerError.textContent = '发送验证码失败，请稍后重试';
                registerError.style.display = 'block';
                sendCodeBtn.disabled = false;
                sendCodeBtn.textContent = '发送验证码';
            }
        });
    }
    
    // 注册表单提交事件
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const code = document.getElementById('code').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        // 验证密码是否一致
        if (password !== confirmPassword) {
            registerError.textContent = '两次输入的密码不一致';
            registerError.style.display = 'block';
            return;
        }
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                    email,
                    code
                }),
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // 注册成功，跳转到登录页面
                window.location.href = '/login';
            } else {
                // 注册失败，显示错误消息
                registerError.textContent = data.message;
                registerError.style.display = 'block';
            }
        } catch (error) {
            console.error('注册请求失败:', error);
            registerError.textContent = '注册失败，请稍后重试';
            registerError.style.display = 'block';
        }
    });
}
