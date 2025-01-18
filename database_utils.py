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
                           date_id INT PRIMARY KEY,
                           month INT,
                           day INT);"""

    create_video_table = """CREATE TABLE IF NOT EXISTS video (
                            video_id INT PRIMARY KEY, 
                            title VARCHAR(255),
                            description VARCHAR(255),
                            comment_count INT,
                            upload_date DATE,
                            channel_id INT);"""

    create_author_table = """CREATE TABLE IF NOT EXISTS author (
                             author_id SERIAL PRIMARY KEY,
                             author_name VARCHAR(150));"""

    create_comment_table = """CREATE TABLE IF NOT EXISTS comment (
                              comment_id INT PRIMARY KEY, 
                              comment_text TEXT,
                              date_id INT,
                              author_id INT,
                              video_id INT,
                              FOREIGN_KEY(author_id) REFERENCES author(author_id),
                              FOREIGN_KEY(video_id) REFERENCES video(video_id),
                              FOREIGN_KEY(date_id) REFERENCES date(date_id));"""

    return 0


def insert_comments(comments):
    #TODO: Create placeholder code for the insertion of comments that would come from calling a function from another file

    return 0


def main():
    conn = None
    try:
        load_dotenv()

        # Access environment variables
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

        cur = conn.cursor()

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