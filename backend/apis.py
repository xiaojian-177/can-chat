import requests
import json
with open('api-config.json', 'r') as f:
    config = json.load(f)
def send_verify_email(email, code):
    r = requests.post('https://api.sendcloud.net/apiv2/mail/send', data={
    'apiUser': config['apiUser'],
    'apiKey': config['apiKey'],
    'from': 'CAN_CHAT-Verify@qq.com',
    'to': email,
    'subject': 'Verifiy your email address',
    'html': '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CAN_CHAT - Email</title>
        <meta name="x-apple-disable-message-reformatting">
        <!-- 邮箱客户端兼容meta -->
        <style type="text/css">
            /* 全局重置 适配所有邮箱 */
            body { margin: 0; padding: 0; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; background-color: #f5f7fa; }
            table { border-collapse: collapse; mso-table-lspace: 0; mso-table-rspace: 0; }
            td { border-collapse: collapse; }
            img { border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }
            p { margin: 0; padding: 0; }
            /* 响应式适配 */
            @media only screen and (max-width: 600px) {
            .email-container { width: 100% !important; padding: 15px !important; }
            .verify-card { padding: 20px 15px !important; }
            .code-box { padding: 12px 0 !important; font-size: 24px !important; letter-spacing: 8px !important; }
            }
        </style>
        </head>
        <body style="margin: 0; padding: 20px 0; background-color: #f5f7fa; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333333;">
        <!-- 主容器 - 居中+自适应 -->
        <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#f5f7fa">
            <tbody>
            <tr>
                <td align="center">
                <!-- 邮件内容主体 -->
                <table class="email-container" width="560" border="0" cellspacing="0" cellpadding="0" bgcolor="#ffffff" style="border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06); border: 1px solid #ebeef5;">
                    <tbody>
                    <!-- 头部LOGO+标题区 -->
                    <tr>
                        <td style="padding: 30px 35px 20px; text-align: center; border-bottom: 1px solid #f0f2f5;">
                        <h1 style="margin: 0; font-size: 22px; font-weight: 600; color: #165DFF;">CAN_CHAT 邮箱验证</h1>
                        <p style="margin: 8px 0 0; font-size: 14px; color: #666666;">感谢你注册 CAN_CHAT，完成验证即可开启聊天之旅</p>
                        </td>
                    </tr>

                    <!-- 核心验证码区 -->
                    <tr>
                        <td class="verify-card" style="padding: 30px 35px; text-align: center;">
                        <p style="margin: 0; font-size: 15px; color: #333333; line-height: 1.6;">尊敬的用户，你正在进行邮箱验证，本次验证码为：</p>
                        <!-- 验证码高亮卡片 - 重中之重 -->
                        <p class="code-box" style="margin: 20px auto; padding: 15px 0; width: 90%; background-color: #f0f7ff; border-radius: 12px; font-size: 28px; font-weight: 700; color: #165DFF; letter-spacing: 12px; font-family: 'Courier New', monospace;">'''+ code +'''</p>
                        <!-- 重要提示 -->
                        <p style="margin: 0; font-size: 13px; color: #999999; line-height: 1.6;">验证码有效期为 <strong style="color: #ff4d4f; font-weight: 500;">5分钟</strong>，请尽快完成验证</p>
                        </td>
                    </tr>

                    <!-- 安全提醒+说明区 -->
                    <tr>
                        <td style="padding: 0 35px 30px; border-top: 1px solid #f0f2f5;">
                        <p style="margin: 25px 0 8px; font-size: 14px; color: #666666; line-height: 1.6;">💡 安全提示：</p>
                        <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #888888; line-height: 1.8;">
                            <li>此验证码仅用于 CAN_CHAT 邮箱验证，请勿泄露给任何人</li>
                            <li>如非本人操作，请忽略此邮件，你的账号安全不会受到影响</li>
                            <li>验证码过期后，请重新发起验证申请</li>
                        </ul>
                        <p style="margin: 20px 0 0; font-size: 12px; color: #cccccc; text-align: center;">© 2026 CAN_CHAT 版权所有 | 本邮件由系统自动发送，请勿直接回复</p>
                        </td>
                    </tr>
                    </tbody>
                </table>
                </td>
            </tr>
            </tbody>
        </table>
        </body>
        </html>
        '''
    })