import pymysql
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# MySQL 配置
connection = pymysql.connect(
    host='47.108.214.185',         # 如果在本地运行脚本
    user='root001',           # 替换为你的数据库用户名
    password='shuqi520',      # 替换为你的数据库密码
    database='school',        # 数据库名
    charset='utf8mb4'
)

# 邮件配置
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 587
SENDER_EMAIL = '376085855@qq.com'  # 替换为你的发件人邮箱
SENDER_PASSWORD = 'uxvmbpmgodaxbghi'  # 替换为 QQ 邮箱的授权码

# 获取所有用户及其彩票信息


def fetch_users_and_tickets():
    query = """
        SELECT u.id, u.name, u.email, t.red1, t.red2, t.red3, t.red4, t.red5, t.red6, t.blue
        FROM lottery_users u
        JOIN lottery_tickets t ON u.id = t.user_id
        ORDER BY u.id
    """
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
    return result

# 获取最新一期的 ssq 开奖数据，包括 draw_number 和 draw_date


def fetch_latest_ssq():
    query = """
        SELECT draw_number, draw_date, red1, red2, red3, red4, red5, red6, blue
        FROM ssq
        ORDER BY draw_number DESC
        LIMIT 1
    """
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
    return result

# 定义函数来判定某一组号码的中奖等级


def check_prize_for_ticket(row, latest_ssq_reds, latest_ssq_blue):
    my_reds = {row['red1'], row['red2'], row['red3'],
               row['red4'], row['red5'], row['red6']}
    my_blue = row['blue']

    red_match_count = len(my_reds.intersection(latest_ssq_reds))
    blue_match = my_blue == latest_ssq_blue

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


def send_lottery_results_via_email(email, results_df, user_name, draw_number, draw_date):
    winning_results_df = results_df[results_df['中奖情况'] != '未中奖']

    # 定义红球和蓝球样式
    def format_ball(ball_number, color):
        # 将 ball_number 转换为字符串以确保 join 可用
        formatted_number = '&#8203;'.join(str(ball_number))
        return f'<span style="display:inline-block; width:30px; height:30px; border-radius:50%; background-color:{color}; color:white !important; text-align:center; line-height:30px; text-decoration:none !important;">{formatted_number}</span>'

    # 动态设置中奖等级的颜色

    def format_prize(prize):
        if prize != '未中奖':
            return f'<span style="color:red;">{prize}</span>'
        return prize

    def format_ticket_row(row):
        red_balls = ''.join(
            [format_ball(row[f'红{i}'], 'red') for i in range(1, 7)])
        blue_ball = format_ball(row['蓝球'], 'blue')
        prize = format_prize(row["中奖情况"])  # 中奖等级条件样式
        return f'<tr><td>{row["期号"]}</td><td>{row["开奖日期"]}</td><td>{red_balls}</td><td>{blue_ball}</td><td>{prize}</td></tr>'
    # 提取开奖号码
    # 使用 format_ball 函数格式化显示最新一期的红球和蓝球
    latest_ssq_reds_html = ''.join(
        [format_ball(latest_ssq[f'red{i}'], 'red') for i in range(1, 7)])
    latest_ssq_blue_html = format_ball(latest_ssq['blue'], 'blue')
    # 生成表格内容
    table_rows = ''.join([format_ticket_row(row)
                         for _, row in results_df.iterrows()])

    # 如果有中奖的结果，生成带有中奖结果的邮件
    if not winning_results_df.empty:
        subject = f"双色球 {draw_number} 期中奖结果：恭喜 {user_name} 中奖！"
        html = f"""
            <html>
            <body>
                <h1>双色球{draw_number} 期开奖号码：</h1>
                <p>开奖日期：{draw_date}</p>
                <p>红球: {latest_ssq_reds_html}</p>
                <p>蓝球: {latest_ssq_blue_html}</p>
                <p>点击查看开奖详情：<a href="https://www.cwl.gov.cn/ygkj/kjgg/" target="_blank">中国福利彩票官网</a></p>
                <p>以下是你的彩票中奖结果（期号: {draw_number}, 开奖日期: {draw_date}）：</p>
                <table border="1" cellpadding="10" cellspacing="0">
                    <tr>
                        <th>期号</th>
                        <th>开奖日期</th>
                        <th>红球</th>
                        <th>蓝球</th>
                        <th>中奖等级</th>
                    </tr>
                    {table_rows}
                </table>
                <br>
                <h3>恭喜！以下号码中奖：</h3>
                {winning_results_df.to_html(index=False)}
            </body>
            </html>
        """
        body = f"以下是你的彩票中奖结果（期号: {draw_number}, 开奖日期: {draw_date}）：\n\n{results_df.to_string(index=False)}\n\n恭喜！以下号码中奖：\n\n{winning_results_df.to_string(index=False)}"

    # 如果没有中奖结果，生成没有中奖的邮件
    else:
        subject = f"双色球 {draw_number} 期中奖结果，很遗憾 {user_name}，未中奖"
        html = f"""
            <html>
            <body>
                <p>以下是你的彩票中奖结果（期号: {draw_number}, 开奖日期: {draw_date}）：</p>
                <table border="1" cellpadding="10" cellspacing="0">
                    <tr>
                        <th>期号</th>
                        <th>开奖日期</th>
                        <th>红球</th>
                        <th>蓝球</th>
                        <th>中奖等级</th>
                    </tr>
                    {table_rows}
                </table>
                <br>
                <h3>很遗憾，本次没有中奖的号码。</h3>
            </body>
            </html>
        """
        body = f"以下是你的彩票中奖结果（期号: {draw_number}, 开奖日期: {draw_date}）：\n\n{results_df.to_string(index=False)}\n\n很遗憾，本次没有中奖的号码。"

    # 构建邮件
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"Liang Kaixi <{SENDER_EMAIL}>"
    message["To"] = email

    # 将文本和HTML版本的内容添加到邮件中
    text_part = MIMEText(body, "plain")
    html_part = MIMEText(html, "html")
    message.attach(text_part)
    message.attach(html_part)

    # 发送邮件
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # 启用TLS加密
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, message.as_string())
        server.quit()
        print(f"邮件发送成功给 {email}!")
    except Exception as e:
        print(f"发送邮件时发生错误: {e}")


# 获取所有用户和他们的彩票数据
users_tickets = fetch_users_and_tickets()

# 获取最新一期的 ssq 开奖数据
latest_ssq = fetch_latest_ssq()
latest_ssq_reds = {latest_ssq['red1'], latest_ssq['red2'], latest_ssq['red3'],
                   latest_ssq['red4'], latest_ssq['red5'], latest_ssq['red6']}
latest_ssq_blue = latest_ssq['blue']
draw_number = latest_ssq['draw_number']
draw_date = latest_ssq['draw_date']

# 处理每个用户的彩票号码，判断是否中奖，并发送邮件
current_user_id = None
user_tickets = []

for row in users_tickets:
    # 当处理完一个用户后，发送中奖结果邮件
    if current_user_id is not None and row['id'] != current_user_id:
        results_df = pd.DataFrame(user_tickets)
        send_lottery_results_via_email(
            current_email, results_df, current_user_name, draw_number, draw_date)
        user_tickets = []

    # 更新当前用户信息
    current_user_id = row['id']
    current_user_name = row['name']
    current_email = row['email']

    # 添加用户的彩票号码到列表
    ticket = {
        '期号': draw_number,
        '开奖日期': draw_date,
        '红1': row['red1'],
        '红2': row['red2'],
        '红3': row['red3'],
        '红4': row['red4'],
        '红5': row['red5'],
        '红6': row['red6'],
        '蓝球': row['blue'],
        '中奖情况': check_prize_for_ticket(row, latest_ssq_reds, latest_ssq_blue)
    }
    user_tickets.append(ticket)

# 最后一个用户的彩票数据发送
if user_tickets:
    results_df = pd.DataFrame(user_tickets)
    send_lottery_results_via_email(
        current_email, results_df, current_user_name, draw_number, draw_date)

# 关闭数据库连接
connection.close()
