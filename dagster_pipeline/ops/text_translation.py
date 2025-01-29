import pandas as pd
from text_utils import get_translation
from database_utils import connection_postgres
from dagster import op

@op
def translate_text():
    """Fetch untranslated comments, translate them, and update the database."""

    # Establish database connection
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    try:
        while True:
            # Fetch a batch of untranslated comments
            query = """
                SELECT comment_id, comment_text 
                FROM comment 
                JOIN date ON comment.date_id = date.date_id 
                WHERE translated_comment_text IS NULL 
                ORDER BY year ASC, month ASC, day ASC 
                LIMIT 10;
            """
            cur.execute(query)
            results = cur.fetchall()

            # If no more untranslated comments, exit loop
            if not results:
                print("No more text to translate.")
                break

            # Convert query results to DataFrame
            col_names = [desc[0] for desc in cur.description]
            df = pd.DataFrame(results, columns=col_names)

            # Translate comments
            df['translated_comment_text'] = df['comment_text'].apply(lambda x: get_translation(x))

            # Update the database with translated text
            for index, row in df.iterrows():
                update_query = """
                    UPDATE comment 
                    SET translated_comment_text = %s 
                    WHERE comment_id = %s;
                """
                cur.execute(update_query, (row['translated_comment_text'], row['comment_id']))

            conn.commit()
            print("Translated comments updated successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Ensure resources are properly closed
        cur.close()
        conn.close()


# Run translation when script is executed
if __name__ == '__main__':
    translate_text()