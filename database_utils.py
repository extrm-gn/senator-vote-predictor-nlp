import psycopg2
from datetime import date, timedelta, datetime
import pandas as pd
import os
from dotenv import load_dotenv

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
            'date_id': f"{date.month}{date.day}{date.year}",
            'month': date.month,
            'day': date.day,
            'year': date.year
        }
        date_data.append(date_dict)

    date_df = pd.DataFrame(date_data)

    return date_df


def connection_postgres():

    load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")

    conn = psycopg2.connect(dbname=db_name,
                            user=db_user,
                            password=db_password,
                            host=db_host,
                            port=db_port)

    cursor = conn.cursor()

    return db_host, db_name, db_user, db_password, db_port, conn, cursor


def insert_video(video_id, title, description, comment_count, upload_date, channel_id):

    db_host, db_name, db_user, db_password, db_port, conn, cursor = connection_postgres()

    cursor.execute("""
        INSERT INTO video (video_id, title, description, comment_count, upload_date, channel_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (video_id) DO NOTHING
    """, (video_id, title, description, comment_count, upload_date, channel_id))
    conn.commit()
    cursor.close()
    conn.close()


def insert_author(author_id, author_name):

    db_host, db_name, db_user, db_password, db_port, conn, cursor = connection_postgres()

    cursor.execute("""
        INSERT INTO author (author_id, author_name)
        VALUES (%s, %s)
        ON CONFLICT (author_id) DO NOTHING
    """, (author_id, author_name))
    conn.commit()
    cursor.close()
    conn.close()


def insert_comment(comment_text, like_count, date_id, author_id, video_id):
    db_host, db_name, db_user, db_password, db_port, conn, cursor = connection_postgres()

    cursor.execute("""
        INSERT INTO comment (comment_text, like_count, date_id, author_id, video_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (comment_id) DO NOTHING
    """, (comment_text,like_count, date_id, author_id, video_id))
    conn.commit()
    cursor.close()
    conn.close()


def insert_code(df, table_name):
    # Generate SQL statements
    db_host, db_name, db_user, db_password, db_port, conn, cursor = connection_postgres()

    print(f"Inserting into {table_name} with DataFrame shape: {df.shape}")

    cursor.execute('SELECT DISTINCT video_id FROM video;')

    # Fetch all rows from the executed query
    rows = cursor.fetchall()

    # Convert the result into a list of video_ids
    unique_videos = [row[0] for row in rows]

    conn.commit()

    sql_statements = []
    for index, row in df.iterrows():
        # Escape single quotes in string values
        values = [
            f"'{str(value).replace("'", "''")}'" if isinstance(value, str) else str(value)
            for value in row
        ]
        if table_name == 'video' and row['video_id'] in unique_videos:
            print(f"duplicate: {df['comment_count']}")
            continue
        else:
            sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(values)});"
            sql_statements.append(sql)

    # Combine all SQL statements
    sql_script = "\n".join(sql_statements)

    try:
        if sql_statements:
            cursor.execute(sql_script)
            conn.commit()
            print(f"Inserted {len(sql_statements)} rows into {table_name}.")
    except Exception as e:
        print(f"Error executing SQL: {e}")
        conn.rollback()

    print("sql script")
    print(sql_script)

    return sql_script


def main():
    conn = None
    try:
        db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Connection closed.")


if __name__ == "__main__":
    main()