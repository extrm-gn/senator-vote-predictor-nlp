import psycopg2
import pandas as pd
from database_utils import connection_postgres
from dagster import op

@op
def export_table_to_csv():

    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()
    table_name = "comment"
    file_path = "output.csv"
    try:
        # Execute the query to fetch all rows from the specified table
        query = f"SELECT * FROM {table_name}"
        query = "SELECT comment_id, translated_comment_text, like_count, search_query, label FROM comment JOIN video ON comment.video_id=video.video_id WHERE translated_comment_text IS NOT NULL"
        cur.execute(query)
        rows = cur.fetchall()

        # Get column names from the cursor
        columns = [desc[0] for desc in cur.description]

        # Convert the rows and column names into a DataFrame
        df = pd.DataFrame(rows, columns=columns)
        df['concatenated_text'] = df.apply(lambda row: f"{row['search_query']}: {row['translated_comment_text']}",
                                           axis=1)
        # Export to CSV
        df.to_csv(file_path, index=False)
        print(f"Table {table_name} exported to {file_path}")

    except Exception as e:
        print(f"Error exporting table: {e}")
    finally:
        if conn:
            conn.close()


# Example Usage
if __name__ == "__main__":
    export_table_to_csv()
