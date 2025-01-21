import googleapiclient.discovery
import pandas as pd
from dotenv import load_dotenv
import os
from database_utils import connection_postgres, insert_code, create_date_dimension
from init_db import init_db
from datetime import datetime

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


def search_videos(query, max_results=10, published_after=None, published_before=None, region_code="PH"):
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
            "comment_count": comment_count  # Add the comment count to the video data
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
            return None  # Return None if no comments are found

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
        return None  # No comments found, return None

def gather_comments_op():
    query = "Senatorial Election"
    published_after = "2025-01-01T00:00:00Z"
    published_before = "2025-01-15T23:59:59Z"

    all_data = []

    videos = search_videos(query, max_results=6, published_after=published_after, published_before=published_before)
    print("Videos Found:")
    for video in videos:
        print(f"{video['title']} (ID: {video['video_id']}) Published At: {video['upload_date']}")
        print(video.keys())

        video_dict = {
            "video_id": video['video_id'],
            "title": video['title'],
            "description": video['description'],
            "upload_date": video['upload_date'],
            "channel_id": video['channel_id'],
            "comment_count": video['comment_count']
        }
        all_data.append(video_dict)

    df_video = pd.DataFrame(all_data)
    df_merge = pd.DataFrame()

    # Fetch comments for each video
    for video in videos:
        print(f"\nFetching comments for video: {video['title']} ({video['video_id']})")
        comments_df = getcomments(video, max_comments=20)  # Fetch 20 comments per video
        if comments_df is not None:  # Only merge if comments are found
            df_merge = pd.concat([df_merge, comments_df], ignore_index=True)  # Append new comments

            df_merge['updated_at'] = pd.to_datetime(df_merge['updated_at'])

            # Extract the month from the datetime column
            df_merge['month'] = df_merge['updated_at'].dt.month
            df_merge['day'] = df_merge['updated_at'].dt.day
            df_merge['year'] = df_merge['updated_at'].dt.year

            df_merge['date_id'] = df_merge['updated_at'].dt.strftime('%m%d%Y')

            print(df_merge.keys())

    # Prepare dataframes for insertion
    video_df = df_video[['video_id', 'title', 'description', 'upload_date', 'channel_id', 'comment_count']].drop_duplicates()

    # Only include rows where comments exist
    if not df_merge.empty:
        author_df = df_merge[['author_name', 'author_id']]
        comment_df = df_merge[['comment_text', 'like_count', 'date_id', 'video_id', 'author_id']]
    else:
        author_df = pd.DataFrame()  # Empty DataFrame if no comments
        comment_df = pd.DataFrame()  # Empty DataFrame if no comments

    return video_df, author_df, comment_df

def insert_comments_op(video_df, author_df, comment_df):
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    if not video_df.empty:
        video_sql_command = insert_code(video_df, "video")
        cur.execute(video_sql_command)

    if not author_df.empty:
        author_sql_command = insert_code(author_df, "author")
        cur.execute(author_sql_command)

    if not comment_df.empty:
        comment_sql_command = insert_code(comment_df, "comment")
        cur.execute(comment_sql_command)

    conn.commit()

    cur.close()
    conn.close()

if __name__ == "__main__":
    video_df, author_df, comment_df = gather_comments_op()
    insert_comments_op(video_df, author_df, comment_df)
