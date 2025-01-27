import googleapiclient.discovery
import pandas as pd
from dotenv import load_dotenv
import os, time
from text_utils import get_translation
from datetime import datetime, timedelta
from database_utils import connection_postgres, insert_code

load_dotenv()

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = os.getenv('YT_API_KEY')

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY
)


def get_video_details(video_id):
    """Fetch video details like title and publishing date."""
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()
    video_title = response['items'][0]['snippet']['title']
    video_published_at = response['items'][0]['snippet']['publishedAt']
    return video_title, video_published_at


def search_videos(query, max_results, published_after=None, published_before=None, region_code="PH"):
    """Search for videos based on a query and date range and get comment count."""

    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="date",
        maxResults=max_results,
        publishedAfter=published_after,
        publishedBefore=published_before,
        regionCode=region_code
    )
    response = request.execute()

    videos = []

    for item in response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        upload_date = item['snippet']['publishedAt']
        channel_id = item['snippet']['channelId']
        description = item['snippet']['description']

        # Fetch comment count for each video
        video_request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        video_response = video_request.execute()

        # Extract comment count
        comment_count = int(video_response['items'][0]['statistics'].get('commentCount', 0))

        videos.append({
            "video_id": video_id,
            "title": video_title,
            "upload_date": upload_date,
            "channel_id": channel_id,
            "description": description,
            "comment_count": comment_count
        })

    return videos


def getcomments(video, max_comments=99):
    """Fetch a limited number of comments and include video metadata."""
    video_title, video_published_at = video["title"], video["upload_date"]

    try:
        # Get video details like comment count
        video_request = youtube.videos().list(
            part="statistics",
            id=video["video_id"]
        )
        video_response = video_request.execute()
        total_comments = int(video_response["items"][0]["statistics"].get("commentCount", 0))
        print(f"Total comments for video {video['video_id']}: {total_comments}")

        if total_comments == 0:
            print(f"No comments for video {video['video_id']}. Skipping comment collection.")
            return None

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

    # Create DataFrame with additional columns for video metadata
    if total_comments > 0:
        df2 = pd.DataFrame(
            comments,
            columns=['video_title', 'video_published_at', 'author_name', 'author_id', 'updated_at', 'like_count', 'comment_text', 'video_id', 'public']
        )
        return df2
    else:
        return None


def get_published_date_range():
    # Establish database connection
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    # Query to get the latest date
    query = """
        SELECT day, month, year 
        FROM video 
        JOIN date ON video.date_id = date.date_id 
        ORDER BY year DESC, month DESC, day DESC 
        LIMIT 1
    """
    cur.execute(query)
    latest_date = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if latest_date:
        # Extract day, month, year and create a datetime object
        day, month, year = latest_date
        latest_datetime = datetime(year, month, day)

        published_after = (latest_datetime + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Ensure that published_before doesn't exceed today
        published_before = min((latest_datetime + timedelta(weeks=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                               datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ'))

        return published_after, published_before
    else:
        published_after = "2024-10-01T00:00:00Z"
        published_before = "2024-10-06T00:00:00Z"

        return published_after, published_before


def gather_comments_op():
    all_comments_data = pd.DataFrame()

    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    query = "SELECT video_id FROM video"
    cur.execute(query)
    rows = cur.fetchall()

    existing_video_ids = [row[0] for row in rows]

    queries = [{'Kiko Pangilinan': 'C', 'Benhur Abalos': 'A', 'Abby Binay': 'A', 'Pia Cayetano': 'A', 'Panfilo Lacson': 'A',
                'Lito lapid': 'A', 'Imee Marcos': 'A', 'Manny Pacquiao': 'A', 'Bong Revilla': 'A', 'Tito Sotto': 'A', 'Francis Tolentino': 'A',
                'Erwin Tulfo': 'A', 'Camille Villar': 'A', 'Bam Aquino': 'C', 'Jimmy Bondoc': 'B', 'Teddy Casino': 'C', 'France Castro':'C',
                'Bato Dela Rosa': 'B', 'Bong Go': 'B', 'Willie Ong': 'A', 'Willie Revillame': 'A', 'Ben Tulfo': 'A'}]

    # queries = [{'Pia Cayetano': 'A', 'Imee Marcos':'A'}]

    all_videos_data = []

    query = "SELECT day, month, year FROM video join date on video.date_id=date.date_id order by year desc, month desc, day desc LIMIT 1"
    cur.execute(query)
    latest_date = cur.fetchall()

    published_after, published_before = get_published_date_range()

    # published_after = "2024-01-21T00:00:00Z"
    # published_before = "2025-01-25T23:59:59Z"

    for query_dict in queries:
        for query_term, label in query_dict.items():
            print(f"\nProcessing query: {query_term}")
            videos = search_videos(query_term, max_results=5, published_after=published_after,
                                   published_before=published_before)
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
                    "label": label,
                    "search_query": query_term
                }
                all_videos_data.append(video_dict)

                # Fetch comments for each video
                print(f"\nFetching comments for video: {video['title']} ({video['video_id']})")
                comments_df = getcomments(video, max_comments=25)

                if comments_df is not None:
                    all_comments_data = pd.concat([all_comments_data, comments_df], ignore_index=True)

    video_df = pd.DataFrame(all_videos_data).drop_duplicates()

    video_df['upload_date'] = pd.to_datetime(video_df['upload_date'])
    video_df['date_id'] = video_df['upload_date'].dt.strftime('%m%d%Y')

    video_df.drop(columns=['upload_date'], inplace=True)

    # Prepare author and comment DataFrames if comments exist
    if not all_comments_data.empty:
        all_comments_data['updated_at'] = pd.to_datetime(all_comments_data['updated_at'])
        all_comments_data['month'] = all_comments_data['updated_at'].dt.month
        all_comments_data['day'] = all_comments_data['updated_at'].dt.day
        all_comments_data['year'] = all_comments_data['updated_at'].dt.year
        all_comments_data['date_id'] = all_comments_data['updated_at'].dt.strftime('%m%d%Y')

        author_df = all_comments_data[['author_name', 'author_id']].drop_duplicates()

        all_comments_data['translated_comment_text'] = all_comments_data.apply(
            lambda row: 'repeated comment' if row['video_id'] in existing_video_ids else get_translation(
                row['comment_text']),
            axis=1
        )

        comment_df = all_comments_data[['comment_text','translated_comment_text', 'like_count', 'date_id', 'video_id', 'author_id']].drop_duplicates()
    else:
        author_df = pd.DataFrame()
        comment_df = pd.DataFrame()

    return video_df, author_df, comment_df

def insert_comments_op(video_df, author_df, comment_df):
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    query = "SELECT video_id FROM video"
    cur.execute(query)
    rows = cur.fetchall()

    existing_video_ids = [row[0] for row in rows]

    # Filter out rows in comment_df with video_id already in the video table
    filtered_comment_df = comment_df[~comment_df['video_id'].isin(existing_video_ids)]

    if not video_df.empty:
        video_sql_command = insert_code(video_df, "video")
        cur.execute(video_sql_command)

    if not author_df.empty:
        author_sql_command = insert_code(author_df, "author")
        cur.execute(author_sql_command)

    if not filtered_comment_df.empty:
        comment_sql_command = insert_code(filtered_comment_df, "comment")
        cur.execute(comment_sql_command)

    conn.commit()

    cur.close()
    conn.close()

if __name__ == "__main__":
    start_time = time.time()

    video_df, author_df, comment_df = gather_comments_op()
    insert_comments_op(video_df, author_df, comment_df)

    end_time = time.time()

    # Calculate elapsed time
    elapsed_time = end_time - start_time
    print(f"Filtering comments took {elapsed_time:.2f} seconds.")