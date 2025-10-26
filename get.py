import os
import requests
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import logging

# 尝试使用 python-dotenv 加载 .env 文件（如果安装了）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # 如果没有安装 python-dotenv，则依赖系统环境变量
    pass

# 1. 把cURL信息填入这里
# 完整的请求URL
url = "https://api.youpin898.com/api/homepage/pc/goods/market/queryOnSaleCommodityList"

# 完整的请求数据 (Payload)
payload = {
  "gameId": "730",
    "listType": "10",
    # 默认 templateId，可通过命令行覆盖
    "templateId": "45636",
  "listSortType": 1,
  "sortType": 0,
  "pageIndex": 1,
  "pageSize": 10
}

# 完整的请求头 (Headers)。
# 为了保险起见，最好把cURL里的所有 -H 都复制过来。
# 尤其重要的是 'authorization', 'User-Agent', 和 'Content-Type'
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5,nl;q=0.4,zh-TW;q=0.3",
    "App-Version": "5.26.0",
    "AppVersion": "5.26.0",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://www.youpin898.com",
    "Referer": "https://www.youpin898.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
    "appType": "1",
    # 敏感信息从环境变量读取（在 .env 中配置）
    # 可通过 SENDER_EMAIL / RECEIVER_EMAIL / EMAIL_PASSWORD 配置邮件
    "authorization": os.getenv('AUTHORIZATION', ''),
    "deviceId": os.getenv('DEVICE_ID', ''),
    "deviceUk": os.getenv('DEVICE_UK', ''),
    "platform": "pc",
    "secret-v": "h5_v1",
    "uk": "5FQGXI5wSq1qzwe9Pz7IQJMIXdWEqzLioFFSPIRVbvYOswCcplW1GISnzfg2DO91L"
    # 你可以把cURL里其他的header也一并添加进来，越全越好
}

# 如果环境变量中有 UK，覆盖
if os.getenv('UK'):
    headers['uk'] = os.getenv('UK')

# 配置日志记录
logging.basicConfig(
    filename="error_log.txt",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def send_email(subject, body):
    """发送邮件通知"""
    # 优先从环境变量读取
    sender_email = os.getenv('SENDER_EMAIL')
    receiver_email = os.getenv('RECEIVER_EMAIL')
    password = os.getenv('EMAIL_PASSWORD')

    # 基本校验，避免在没有配置的情况下尝试发送邮件
    if not sender_email or not password:
        print("邮件配置不完整：请在 .env 中设置 SENDER_EMAIL 和 EMAIL_PASSWORD 后重试。")
        logging.error("邮件配置不完整（SENDER_EMAIL/EMAIL_PASSWORD 未设置）")
        return

    # 创建邮件内容
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    # 添加邮件正文
    message.attach(MIMEText(body, 'plain', 'utf-8'))

    for attempt in range(3):  # 最多重试 3 次
        try:
            # 连接到 QQ 邮箱的 SMTP 服务器
            with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                print(f"邮件已发送至 {receiver_email}")
                return
        except Exception as e:
            print(f"邮件发送失败 (尝试 {attempt + 1}/3): {e}")
            if attempt == 2:
                print("邮件发送失败，已放弃重试。")


# 导出一些配置变量便于测试（模块导入时可检查）
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
AUTHORIZATION = os.getenv('AUTHORIZATION')
DEVICE_ID = os.getenv('DEVICE_ID')
DEVICE_UK = os.getenv('DEVICE_UK')
UK = os.getenv('UK')

def check_price():
    try:
        # 发送POST请求
        # 注意：使用 json=payload 会自动设置 Content-Type，但我们为了保险起见在headers里也指定了
        response = requests.post(url, headers=headers, json=payload)

        # 检查请求是否成功 (状态码 200)
        if response.status_code == 200:
            # 解析 JSON
            try:
                data = response.json()
            except ValueError:
                print("响应不是有效的 JSON：")
                print(response.text)
                return

            # 打印完整的返回数据，帮助你调试
            print("== 原始返回 JSON ==")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("== 返回 JSON 结束 ==\n")

            res = find_first_price(data)
            if res:
                name, price = res
                print(f"查询成功：{name} 当前价格为：￥{price}")

                # 检测价格是否低于 2100
                if price and float(price) < 2100:
                    subject = f"价格警报：{name} 价格低于 2100"
                    body = f"商品 {name} 当前价格为 ￥{price}，低于设定阈值 2100，请及时查看。"
                    send_email(subject, body)
            else:
                print("未在返回数据中找到任何带 'price' 字段的商品。")
                # 检查是否是 'msg' 字段提示了错误，比如 "未登录"
                if data.get('msg'):
                    print(f"服务器消息: {data.get('msg')}")
                    if "登录" in data.get('msg'):
                        print(">>> 警告：身份令牌(authorization)可能已过期！<<<")

        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"服务器响应: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"发生网络错误: {e}")

# 定义递归函数 find_first_price

def find_first_price(obj):
    """递归查找第一个包含 'price' 字段的字典，并返回 (name, price)。"""
    if isinstance(obj, dict):
        # 直接包含 price
        if 'price' in obj:
            name = obj.get('commodityName') or obj.get('commodity_name') or obj.get('name')
            return (name, obj.get('price'))
        # 否则遍历其值
        for v in obj.values():
            res = find_first_price(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_first_price(item)
            if res:
                return res
    return None

# --- 运行你的监控 ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="查询并打印商品价格（可选一次运行/多个模板）")
    parser.add_argument('--once', action='store_true', help='只运行一次并退出（用于测试）')
    parser.add_argument('--templates', type=str, default=None,
                        help='用逗号分隔的 templateId 列表，例如 "45636,62036,62041"')
    args = parser.parse_args()

    # 解析 templates 参数
    templates = None
    if args.templates:
        templates = [t.strip() for t in args.templates.split(',') if t.strip()]

    def run_once_for_templates(template_list):
        for tid in template_list:
            print(f"\n--- 查询 templateId={tid} ---")
            # 更新 payload 并请求
            payload['templateId'] = tid
            check_price()

    if args.once:
        if templates:
            run_once_for_templates(templates)
        else:
            # 只查询默认的 templateId
            run_once_for_templates([payload.get('templateId')])
    else:
        # 长轮询模式：按每个 templateId 循环查询
        if templates:
            template_list = templates
        else:
            template_list = [payload.get('templateId')]

        def monitor_prices(template_list):
            """监控价格，每隔 5~6 分钟查询一次"""
            while True:
                for tid in template_list:
                    print(f"\n--- 查询 templateId={tid} ---")
                    payload['templateId'] = tid

                    for attempt in range(3):  # 最多重试 3 次
                        try:
                            response = requests.post(url, headers=headers, json=payload)

                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                except ValueError:
                                    print("响应不是有效的 JSON：")
                                    print(response.text)
                                    break

                                # 自动提取第一个包含 price 字段的商品
                                res = find_first_price(data)
                                if res:
                                    name, price = res
                                    print(f"查询成功：{name} 当前价格为：￥{price}")

                                    # 检测价格是否低于 2100
                                    if price and float(price) < 2100:
                                        subject = f"价格警报：{name} 价格低于 2100"
                                        body = f"商品 {name} 当前价格为 ￥{price}，低于设定阈值 2100，请及时查看。"
                                        send_email(subject, body)
                                else:
                                    print("未找到任何带 'price' 字段的商品。")
                                break
                            else:
                                print(f"请求失败，状态码: {response.status_code}")
                                print(f"服务器响应: {response.text}")
                                logging.error(f"templateId={tid} 请求失败，状态码: {response.status_code}, 响应: {response.text}")

                                if response.status_code == 502 and attempt < 2:
                                    print("502 错误，正在重试...")
                                    time.sleep(random.randint(5, 10))  # 增加随机延迟
                                else:
                                    print(f"跳过 templateId={tid}，重试次数已用尽。")
                                    break
                        except requests.exceptions.RequestException as e:
                            print(f"发生网络错误: {e}")
                            logging.error(f"templateId={tid} 网络错误: {e}")
                            if attempt < 2:
                                print("正在重试...")
                                time.sleep(random.randint(5, 10))  # 增加随机延迟
                            else:
                                print(f"跳过 templateId={tid}，重试次数已用尽。")
                                break

                # 随机等待 5~6 分钟
                wait_time = random.randint(300, 360)
                print(f"等待 {wait_time} 秒后再次查询...")
                time.sleep(wait_time)

        # 启动监控
        monitor_prices(template_list)
