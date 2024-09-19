import requests
import pymysql
import pandas as pd

# MySQL 配置
connection = pymysql.connect(
    host='127.0.0.1',  # 替换为你的数据库 IP
    user='root001',         # 替换为你的数据库用户名
    password='shuqi520',    # 替换为你的数据库密码
    database='school',      # 数据库名
    charset='utf8mb4'
)

# 发送请求获取数据
url = 'https://data.17500.cn/ssq_asc.txt'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}
response = requests.get(url, headers=headers)

# 解析数据并获取最后一行
if response.status_code == 200:
    data = response.content.decode('utf-8')

    # 以空格分割数据，并仅取前9列
    lines = data.split('\n')
    parsed_data = [line.split()[:9] for line in lines if line.strip()]

    # 获取最后一行
    last_row = parsed_data[-1]
    column_names = ['draw_number', 'draw_date', 'red1',
                    'red2', 'red3', 'red4', 'red5', 'red6', 'blue']

    # 将最后一行数据创建成 DataFrame
    last_row_df = pd.DataFrame([last_row], columns=column_names)

    # 插入最后一行数据到 MySQL
    try:
        with connection.cursor() as cursor:
            insert_query = """
                INSERT INTO ssq (draw_number, draw_date, red1, red2, red3, red4, red5, red6, blue)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                int(last_row_df['draw_number'][0]
                    ), last_row_df['draw_date'][0],
                int(last_row_df['red1'][0]), int(last_row_df['red2'][0]),
                int(last_row_df['red3'][0]), int(last_row_df['red4'][0]),
                int(last_row_df['red5'][0]), int(last_row_df['red6'][0]),
                int(last_row_df['blue'][0])
            ))
            connection.commit()
            print("最后一行数据插入成功!")
    except Exception as e:
        print(f"插入数据时发生错误: {e}")
    finally:
        connection.close()
else:
    print(f"请求失败，状态码: {response.status_code}")
