import psycopg2
from datetime import date, timedelta, datetime
import pandas as pd

conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres",
                        password="1234", port=5432)

cur = conn.cursor()

# cur.execute("""CREATE TABLE IF NOT EXISTS person (
#                 id INT PRIMARY KEY,
#                 name VARCHAR(255),
#                 age INT,
#                 gender CHAR);""")
#
# cur.execute("""INSERT INTO person (id,name,age,gender) VALUES
#                 (2, 'Mike', 30, 'm')""")
# conn.commit()

cur.close()
conn.close()

def create_date_dimension():
    start_date = datetime(2024, 10, 1)
    end_date = datetime(2025, 5, 12)

    date_list = []

    while start_date < end_date:
        date_list.append(start_date)
        start_date += timedelta(days=1)

    date_data = []

    for date in date_list:
        date_dict = {
            'id': f"{date.month}{date.day}{date.year}",
            'month': date.month,
            'day': date.day,
            'year': date.year
        }
        date_data.append(date_dict)

    date_df = pd.DataFrame(date_data).set_index('id')

    return date_df


def init_db():
    #TODO: create necessary tables such as the date, video, author, and comment table

    date_df = create_date_dimension()

    print(date_df)

    create_date_table = """CREATE TABLE IF NOT EXISTS date (
                     date_id PRIMARY KEY,
                     month INT,
                     day INT);"""

    create_video_table = """"""

    create_author_table = """"""

    create_comment_table = """"""

    return 0

init_db()

def insert_comments(comments):
    #TODO: Create placeholder code for the insertion of comments that would come from calling a function from another file

    return 0