import pandas as pd
import time
from text_utils import get_translation
from database_utils import connection_postgres


def translate_text(batch_size=50, max_retries=3):
    """Fetches untranslated comments, translates them, and updates the database in bulk."""

    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    try:
        while True:
            # Fetch batch of untranslated comments
            query = """
                SELECT comment_id, comment_text 
                FROM comment 
                JOIN date ON(comment.date_id = date.date_id) 
                WHERE translated_comment_text IS NULL 
                ORDER BY year ASC, month ASC, day ASC 
                LIMIT %s;
            """
            cur.execute(query, (batch_size,))
            results = cur.fetchall()

            if not results:
                print("✅ No more text to translate.")
                break  # Exit loop if no results

            # Convert to DataFrame
            df = pd.DataFrame(results, columns=["comment_id", "comment_text"])

            # Translate comments with retries
            def safe_translate(text):
                for attempt in range(max_retries):
                    try:
                        return get_translation(text)  # Call translation API
                    except Exception as e:
                        print(f"⚠️ Translation failed (Attempt {attempt + 1}/{max_retries}): {e}")
                        time.sleep(2)  # Wait before retrying
                return "ERROR"  # Mark failed translations to avoid retrying them infinitely

            df['translated_comment_text'] = df['comment_text'].apply(safe_translate)

            # Batch update translated comments
            update_query = """
                UPDATE comment 
                SET translated_comment_text = %s 
                WHERE comment_id = %s;
            """
            cur.executemany(update_query, df[['translated_comment_text', 'comment_id']].values.tolist())

            conn.commit()
            print(f"✅ Translated and updated {len(df)} comments.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    translate_text()
