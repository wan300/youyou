# youyou - 使用说明与环境变量配置

本项目用来周期性查询商品价格并在价格低于设定阈值时通过邮件发送通知。为保护隐私与安全，所有敏感信息（邮箱账号、授权码、API Token 等）应保存在项目根目录的 `.env` 文件中。此 README 说明如何配置环境变量、安装依赖、验证配置及执行脚本。

## 目录
- 功能简介
- 前提条件
- 安装依赖
- 配置环境变量（.env）
- 验证 env 加载（安全检查）
- 测试邮件发送（可选，谨慎）
- 运行脚本
- 常见问题与排查
- 安全建议

## 功能简介
脚本 `get.py` 会：
- 向指定接口发送 POST 请求获取商品数据
- 自动从响应中提取第一个带 `price` 字段的商品
- 当价格低于阈值时，通过 SMTP 发邮件通知

敏感配置（邮件账号、授权码、接口 token 等）已移入 `.env` 以便安全管理。

## 前提条件
- Python 3.7+
- 可访问互联网（用于请求接口与 SMTP 发信）

## 安装依赖
建议使用虚拟环境（venv/conda），在项目根目录运行：

```powershell
pip install -r .\requirements.txt
```

`requirements.txt` 包含：
- requests
- python-dotenv

## 配置环境变量（.env）
1. 复制示例文件：

```powershell
copy .env.example .env
notepad .env
```

2. 在 `.env` 中设置实际值（示例变量）：

- SENDER_EMAIL：发件邮箱（例如 QQ 邮箱）
- RECEIVER_EMAIL：接收通知的邮箱
- EMAIL_PASSWORD：SMTP 授权码（注意：不是登录密码，QQ 邮箱需在设置中开启并生成授权码）
- AUTHORIZATION：调用接口所需的 Authorization Token（如脚本原来包含的）
- DEVICE_ID：设备 ID（如原请求头）
- DEVICE_UK：设备 UK
- UK：请求头中的 uk 字段

示例（不要把真实值提交到远程仓库）：

```
SENDER_EMAIL=your_sender@qq.com
RECEIVER_EMAIL=recipient@example.com
EMAIL_PASSWORD=your_smtp_authorization_code
AUTHORIZATION=eyJ... (token)
DEVICE_ID=xxxx-xxxx-xxxx
DEVICE_UK=xxxxx
UK=xxxxx
```

> 注意：项目根目录下已包含 `.gitignore`，会忽略 `.env`，请确保不要把真实 `.env` 提交到版本控制系统。

## 验证 env 加载（安全检查）
在填好 `.env` 后，可运行下面命令验证脚本能正确加载这些变量（只打印是否设置，不会显示秘密内容）：

```powershell
python -c "import get; print('SENDER_EMAIL set=', bool(get.SENDER_EMAIL)); print('EMAIL_PASSWORD set=', bool(get.EMAIL_PASSWORD)); print('AUTHORIZATION set=', bool(get.AUTHORIZATION))"
```

若输出为 True（或非空），说明 `.env` 加载成功。

## 测试邮件发送（可选，谨慎）
请先确保：
- `SENDER_EMAIL` 与 `EMAIL_PASSWORD`（SMTP 授权码）已正确填写
- 你的网络允许连接 `smtp.qq.com:465`（无防火墙或代理阻断）
- QQ 邮箱已在设置中开启“开启 POP3/SMTP 服务”并生成授权码

确认后可运行：

```powershell
python -c "from get import send_email; send_email('测试邮件', '这是一封测试邮件。')"
```

脚本会重试 3 次。如果出现 `Connection unexpectedly closed` 或类似错误，请参阅“常见问题与排查”。

## 运行脚本
- 单次运行（仅测试一次，支持多个 templateId）：

```powershell
python get.py --once --templates 45636,62036
```

- 长轮询模式（持续监控）：

```powershell
python get.py
```

脚本默认会每隔 5~6 分钟（随机）轮询一次。

## 常见问题与排查
- 问：邮件发送失败，提示 `Connection unexpectedly closed`。
  - 排查：确认 `EMAIL_PASSWORD` 是否为邮箱 SMTP 授权码（QQ 邮箱需单独生成）。
  - 排查：尝试启用调试日志：在本地运行一个小脚本测试 SMTP 连接：

```powershell
python - <<'PY'
import smtplib
try:
    s = smtplib.SMTP_SSL('smtp.qq.com', 465)
    s.set_debuglevel(1)
    s.login('SENDER_EMAIL', 'EMAIL_PASSWORD')
    print('SMTP 连接成功')
    s.quit()
except Exception as e:
    print('SMTP 连接失败:', e)
PY
```

- 问：接口返回 `未登录` / 身份失效
  - 排查：确认 `AUTHORIZATION` 是否过期或需更新。登录相关 token 需在网站或 API 控制台获取并更新到 `.env`。

- 问：脚本无法安装依赖或导入 requests
  - 排查：确保在正确的 Python 环境中安装了 `requests`（参见 `pip install -r requirements.txt`）

## 安全建议
- 永远不要把 `.env` 提交到版本控制。使用远端运行时（如服务器或 CI）时，优先使用环境变量或 secret 管理服务。
- 不要在公共或共享机器上保存明文授权码。考虑使用操作系统的密钥环或专门的 secret 管理工具。

## 后续改进建议
- 增加 `--show-config` 命令行选项（只显示哪些 env 已设置，不显示值）
- 支持更多邮件服务（如 SMTP via OAuth）以提升安全性
- 将邮件发送逻辑抽成可配置的后端（例如使用 SendGrid、AWS SES 等）

---
如果你希望我现在：
- 帮你添加 `--show-config` 功能，或
- 现在执行一次真实的邮件发送测试（我会在运行前再次确认），
请告诉我你的选择。