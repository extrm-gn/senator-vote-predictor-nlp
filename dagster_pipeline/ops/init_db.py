import psycopg2
from database_utils import create_date_dimension, connection_postgres, insert_code

def init_db():
    #TODO: create necessary tables such as the date, video, author, and comment table

    date_df = create_date_dimension()

    create_date_table = """CREATE TABLE IF NOT EXISTS date (
                           date_id INT PRIMARY KEY,
                           month INT,
                           day INT,
                           year INT);"""

    create_video_table = """CREATE TABLE IF NOT EXISTS video (
                            video_id VARCHAR(25) PRIMARY KEY, 
                            title VARCHAR(255),
                            description VARCHAR(255),
                            comment_count INT,
                            upload_date DATE,
                            channel_id VARCHAR(25));"""

    create_author_table = """CREATE TABLE IF NOT EXISTS author (
                             author_id VARCHAR(25) PRIMARY KEY,
                             author_name VARCHAR(150));"""

    create_comment_table = """CREATE TABLE IF NOT EXISTS comment (
                              comment_id SERIAL PRIMARY KEY, 
                              comment_text TEXT,
                              date_id INT,
                              author_id VARCHAR(25),
                              video_id VARCHAR(25),
                              like_count INT,
                              FOREIGN KEY(author_id) REFERENCES author(author_id),
                              FOREIGN KEY(video_id) REFERENCES video(video_id),
                              FOREIGN KEY(date_id) REFERENCES date(date_id));"""


    conn = None
    try:
        db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

        cur.execute(create_date_table)
        cur.execute(create_video_table)
        cur.execute(create_author_table)
        cur.execute(create_comment_table)
        cur.execute(insert_code(date_df, 'date'))
        conn.commit()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Connection closed.")

    return 0

init_db()