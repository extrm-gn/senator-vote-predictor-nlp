import googleapiclient.discovery
import pandas as pd
from dotenv import load_dotenv
import os
from database_utils import connection_postgres, insert_code, create_date_dimension, insert_author, insert_comment
from init_db import init_db
from datetime import datetime

load_dotenv()

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = os.getenv('YT2_API_KEY')

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY
)


def get_video_in_table():
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    cur.execute("""SELECT video_id FROM video;""")

    # Fetch all rows from the result of the query
    video_ids = cur.fetchall()
    conn.commit()

    cur.close()
    conn.close()

    return video_ids

def get_video_details(video_id):
    """Fetch video details like title, publishing date, and comment count."""
    try:
        request = youtube.videos().list(
            part="snippet,statistics",  # Include 'statistics' for comment count
            id=video_id
        )
        response = request.execute()

        if not response['items']:
            raise ValueError(f"Video with ID {video_id} not found.")

        video_data = response['items'][0]
        video_title = video_data['snippet']['title']
        video_published_at = video_data['snippet']['publishedAt']
        comment_count = int(video_data.get('statistics', {}).get('commentCount', 0))  # Handle missing 'statistics'

        return video_title, video_published_at

    except Exception as e:
        print(f"Error fetching video details for video ID {video_id}: {e}")
        return None, None, 0  # Default values if there's an error


def search_videos(query, max_results=10, published_after=None, published_before=None, region_code="PH"):
    """Search for videos based on a query and date range."""
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="date",
        maxResults=max_results,
        publishedAfter=published_after,
        publishedBefore=published_before,
        regionCode = region_code
    )
    response = request.execute()

    # Step 2: Extract video IDs from search results
    video_ids = [item['id']['videoId'] for item in response['items']]
    if not video_ids:
        print("No videos found.")
        return []

    # Step 3: Fetch video statistics, including comment count
    stats_request = youtube.videos().list(
        part="statistics",
        id=','.join(video_ids)  # Combine video IDs into a single request
    )
    stats_response = stats_request.execute()

    # Step 4: Map video IDs to their statistics
    video_stats = {
        item['id']: {
            "comment_count": int(item.get('statistics', {}).get('commentCount', 0)),
            "view_count": int(item.get('statistics', {}).get('viewCount', 0))
        }
        for item in stats_response['items']
    }

    # Extract video IDs and titles from the search results
    videos = [
        {
            "video_id": item['id']['videoId'],
            "title": item['snippet']['title'],
            "upload_date": item['snippet']['publishedAt'],
            "channel_id": item['snippet']['channelId'],
            "description": item['snippet']['description'],
            "comment_count": video_stats.get(item['id']['videoId'], {}).get("comment_count", 0),
            "view_count": video_stats.get(item['id']['videoId'], {}).get("view_count", 0)
        }
        for item in response['items']
    ]
    return videos


def getcomments(video, max_comments=99):
    """Fetch a limited number of comments and include video metadata."""
    video_title, video_published_at = video["title"], video["upload_date"]

    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video["video_id"],
            maxResults=min(max_comments, 100)
        )

        comments = []
        total_fetched = 0

        try:
            response = request.execute()

            # Get the comments from the response.
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                public = item['snippet']['isPublic']
                author_channel_id = comment.get('authorChannelId', {}).get('value', None)
                comments.append([
                    video_title,
                    video_published_at,
                    comment['authorDisplayName'],
                    author_channel_id,
                    comment['publishedAt'],
                    comment['likeCount'],
                    comment['textOriginal'],
                    video["video_id"],
                    public
                ])
                total_fetched += 1
                if total_fetched >= max_comments:
                    break

            # If more comments are needed and available, loop through additional pages.
            while total_fetched < max_comments:
                try:
                    nextPageToken = response['nextPageToken']
                except KeyError:
                    break
                nextRequest = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video["video_id"],
                    maxResults=min(max_comments - total_fetched, 100),
                    pageToken=nextPageToken
                )
                response = nextRequest.execute()
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    public = item['snippet']['isPublic']
                    comments.append([
                        video_title,
                        video_published_at,
                        comment['authorDisplayName'],
                        comment['publishedAt'],
                        comment['likeCount'],
                        comment['textOriginal'],
                        video["video_id"],
                        public
                    ])
                    total_fetched += 1
                    if total_fetched >= max_comments:
                        break

        except KeyError as e:
            print(f"KeyError: {e} - No comments found or comment fetching interrupted.")

    except googleapiclient.errors.HttpError as e:
        print(f"HttpError: {e} - Comments might be disabled for video ID: {video['video_id']}")

    # If no comments were fetched, log a message and skip appending

    # Create DataFrame with additional columns for video metadata
    df2 = pd.DataFrame(
        comments,
        columns=['video_title', 'video_published_at', 'author_name','author_id', 'updated_at', 'like_count', 'comment_text', 'video_id', 'public']
    )

    return df2


def gather_comments_op():
    query = "Senatorial Election"
    published_after = "2025-01-01T00:00:00Z"
    published_before = "2025-01-15T23:59:59Z"

    all_data = []

    videos = search_videos(query, max_results=8, published_after=published_after, published_before=published_before)
    print("Videos Found:")
    for video in videos:

        print(f"{video['title']} (ID: {video['video_id']}) Published At: {video['upload_date']}")

        video_dict = {
            "video_id": video['video_id'],
            "title": video['title'],
            "description": video['description'],
            "upload_date": video['upload_date'],
            "channel_id": video['channel_id'],
            "comment_count": video['comment_count'],
            "view_count": video['view_count']
        }
        all_data.append(video_dict)

    df_video = pd.DataFrame(all_data)
    df_join = pd.DataFrame(all_data)

    # Fetch comments for each video
    for video in videos:
        print(f"\nFetching comments for video: {video['title']} ({video['video_id']})")
        comments_df = getcomments(video, max_comments=20)  # Fetch 20 comments per video
        #print(comments_df.head())  # Display the first few rows

        df_merge = df_join.merge(comments_df, on='video_id', how='inner')
        try:
            df_merge['updated_at'] = pd.to_datetime(df_merge['updated_at'], errors='coerce')
        except Exception as e:
            print(f"Error parsing 'updated_at': {e}")

            # Handle any NaT values in 'updated_at' by filtering or filling them
        if df_merge['updated_at'].isnull().any():
            print("Warning: Some 'updated_at' values are invalid or missing, these rows will be dropped.")
            df_merge = df_merge.dropna(subset=['updated_at'])

        # Extract the month from the datetime column
        df_merge['month'] = df_merge['updated_at'].dt.month
        df_merge['day'] = df_merge['updated_at'].dt.day
        df_merge['year'] = df_merge['updated_at'].dt.year

        df_merge['date_id'] = df_merge['updated_at'].dt.strftime('%m%d%Y')

        print(df_merge.keys())

    video_df = df_video[['video_id', 'title', 'description', 'upload_date',
                         'channel_id',"view_count", "comment_count"]].drop_duplicates()

    author_df= df_merge[['author_name', 'author_id']]
    comment_df = df_merge[['comment_text', 'like_count', 'date_id', 'video_id','author_id']]

    return video_df, author_df, comment_df


def insert_comments_op():
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    try:
        # Get data from the gather_comments_op function
        video_df, author_df, comment_df = gather_comments_op()

        print("Video DataFrame Shape:", video_df.shape)
        print("Author DataFrame Shape:", author_df.shape)
        print("Comment DataFrame Shape:", comment_df.shape)

        # Validate that all DataFrames are not None and not empty
        if video_df is None or video_df.empty:
            print("No new videos to insert.")
            video_df = pd.DataFrame(columns=["video_id", "title", "description", "upload_date", "channel_id"])
        if author_df is None or author_df.empty:
            print("No new authors to insert.")
            author_df = pd.DataFrame(columns=["author_name", "author_id"])
        if comment_df is None or comment_df.empty:
            print("No new comments to insert.")
            comment_df = pd.DataFrame(columns=["comment_text", "like_count", "date_id", "video_id", "author_id"])

        # Generate SQL commands for non-empty DataFrames
        if not video_df.empty:
            video_sql_command = insert_code(video_df, "video")
            if video_sql_command:  # Check if the SQL command is not empty
                cur.execute(video_sql_command)
                print("Inserted videos.")
            else:
                print("No video data to insert (empty SQL command).")

        if not author_df.empty:
            for index, row in author_df.iterrows():
                # Directly call the insert_author function to handle insertion
                insert_author(row['author_id'], row['author_name'])
                print(f"Inserted author: {row['author_name']}")
        else:
            print("No author data to insert (author_df is empty).")

        if not comment_df.empty:
            for index, row in comment_df.iterrows():
                # Directly call the insert_author function to handle insertion
                print(f"Inserted author id: {row['author_id']}")
                insert_comment(row['comment_text'], row['like_count'], row['date_id'], row['video_id'], row['author_id'])
                print(f"Inserted author: {row['author_id']}")
            else:
                print("No comment data to insert (empty SQL command).")

        # Commit changes
        conn.commit()

    except Exception as e:
        # Rollback in case of an error
        conn.rollback()
        print(f"Error during insertion: {e}")

    finally:
        # Close the database connection
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_comments_op()
