import pymysql
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# MySQL 配置
connection = pymysql.connect(
    host='127.0.0.1',         # 如果在本地运行脚本
    user='root001',           # 替换为你的数据库用户名
    password='shuqi520',      # 替换为你的数据库密码
    database='school',        # 数据库名
    charset='utf8mb4'
)

# 邮件配置（如果使用外部 SMTP 服务）
SMTP_SERVER = 'smtp.qq.com'  # 使用 QQ 邮箱的 SMTP 服务器
SMTP_PORT = 587
SENDER_EMAIL = '376085855@qq.com'  # 替换为你的发件人邮箱
SENDER_PASSWORD = 'uxvmbpmgodaxbghi'  # 替换为 QQ 邮箱的授权码
RECIPIENT_EMAIL = 'liangkaixi@163.com'  # 替换为接收邮件的邮箱

# 从 MySQL 数据库获取最后一行开奖数据


def fetch_latest_draw():
    query = "SELECT draw_number, draw_date, red1, red2, red3, red4, red5, red6, blue FROM ssq ORDER BY draw_number DESC LIMIT 1"
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
    return result

# 定义函数来判定某一组号码的中奖等级


def check_prize_for_ticket(row, my_reds, my_blue):
    current_reds = {row['red1'], row['red2'], row['red3'],
                    row['red4'], row['red5'], row['red6']}
    current_blue = row['blue']

    red_match_count = len(my_reds.intersection(current_reds))
    blue_match = my_blue == current_blue

    if red_match_count == 6 and blue_match:
        return "一等奖"
    elif red_match_count == 6:
        return "二等奖"
    elif red_match_count == 5 and blue_match:
        return "三等奖"
    elif red_match_count == 5 or (red_match_count == 4 and blue_match):
        return "四等奖"
    elif red_match_count == 4 or (red_match_count == 3 and blue_match):
        return "五等奖"
    elif blue_match:
        return "六等奖"
    else:
        return "未中奖"

# 发送中奖结果邮件


def send_lottery_results_via_email(results_df, use_local=True):
    # 过滤出中奖结果不等于 "未中奖" 的记录
    winning_results_df = results_df[results_df['Prize'] != '未中奖']

    # 生成HTML格式的结果表格
    if not winning_results_df.empty:
        subject = "双色球中奖结果 有中奖请尽快查看"
        # 如果有中奖的结果，单独列出
        html = f"""
        <html>
        <body>
            <p>以下是你的彩票中奖结果：</p>
            {results_df.to_html(index=False)}
            <br>
            <h3>恭喜！以下号码中奖：</h3>
            {winning_results_df.to_html(index=False)}
        </body>
        </html>
        """
        body = f"以下是你的彩票中奖结果：\n\n{results_df.to_string(index=False)}\n\n恭喜！以下号码中奖：\n\n{winning_results_df.to_string(index=False)}"
    else:
        subject = "双色球中奖结果，很遗憾，未中奖，期待下一次"
        # 如果没有中奖结果
        html = f"""
        <html>
        <body>
            <p>以下是你的彩票中奖结果：</p>
            {results_df.to_html(index=False)}
            <br>
            <h3>很遗憾，本次没有中奖的号码。</h3>
        </body>
        </html>
        """
        body = f"以下是你的彩票中奖结果：\n\n{results_df.to_string(index=False)}\n\n很遗憾，本次没有中奖的号码。"

    # 构建邮件
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"Liang Kaixi <{SENDER_EMAIL}>"
    message["To"] = RECIPIENT_EMAIL

    # 将文本和HTML版本的内容添加到邮件中
    text_part = MIMEText(body, "plain")
    html_part = MIMEText(html, "html")
    message.attach(text_part)
    message.attach(html_part)

    # 发送邮件
    try:
        if use_local:
            # 使用本地邮件服务发送
            server = smtplib.SMTP('localhost')
        else:
            # 使用外部 SMTP 服务发送
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()  # 启用TLS加密
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())
        server.quit()
        print("邮件发送成功!")
    except Exception as e:
        print(f"发送邮件时发生错误: {e}")


# 获取最后一行开奖数据
latest_draw = fetch_latest_draw()

# 针对最后一行开奖数据，依次比对每组彩票号码
my_tickets = [
    {'reds': {6, 9, 16, 20, 27, 30}, 'blue': 1},
    {'reds': {3, 8, 12, 21, 25, 31}, 'blue': 10},
    {'reds': {2, 5, 14, 18, 26, 33}, 'blue': 6},
    {'reds': {7, 13, 16, 22, 28, 32}, 'blue': 4},
    {'reds': {1, 9, 15, 23, 27, 30}, 'blue': 8},
    {'reds': {3, 12, 19, 22, 25, 30}, 'blue': 5},
    {'reds': {1, 8, 15, 20, 26, 33}, 'blue': 9},
    {'reds': {2, 10, 17, 21, 28, 31}, 'blue': 7},
    {'reds': {5, 11, 13, 18, 23, 32}, 'blue': 3},
    {'reds': {4, 7, 14, 19, 24, 29}, 'blue': 12},
    {'reds': {3, 10, 20, 23, 28, 30}, 'blue': 8},
    {'reds': {2, 9, 20, 21, 26, 30}, 'blue': 8},
    {'reds': {1, 6, 14, 17, 22, 26}, 'blue': 4},

]

results = []

for ticket in my_tickets:
    prize = check_prize_for_ticket(latest_draw, ticket['reds'], ticket['blue'])
    results.append({'Draw Number': latest_draw['draw_number'],
                   'My Reds': ticket['reds'], 'My Blue': ticket['blue'], 'Prize': prize})

# 将结果转换为 DataFrame
results_df = pd.DataFrame(results)

# 发送邮件，选择是否使用本地邮件服务
use_local = False  # 如果使用外部 SMTP 服务，将其设置为 False；使用本地服务设置为 True
send_lottery_results_via_email(results_df, use_local)

# 关闭数据库连接
connection.close()