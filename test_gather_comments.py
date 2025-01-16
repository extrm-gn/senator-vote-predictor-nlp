import googleapiclient.discovery
import pandas as pd
from dotenv import load_dotenv
import os

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

    # Extract video IDs and titles from the search results
    videos = [
        {
            "video_id": item['id']['videoId'],
            "title": item['snippet']['title'],
            "published_at": item['snippet']['publishedAt']
        }
        for item in response['items']
    ]
    return videos


def getcomments(video, max_comments=50):
    """Fetch a limited number of comments and include video metadata."""
    video_title, video_published_at = video["title"], video["published_at"]

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video["video_id"],
        maxResults=min(max_comments, 100)
    )

    comments = []
    total_fetched = 0

    response = request.execute()

    # Get the comments from the response.
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

    # Create DataFrame with additional columns for video metadata
    df2 = pd.DataFrame(
        comments,
        columns=['video_title', 'video_published_at', 'author', 'updated_at', 'like_count', 'text', 'video_id', 'public']
    )
    pd.set_option('display.max_columns', None)
    return df2


if __name__ == "__main__":

    query = "Kiko Pangilinan"
    published_after = "2025-01-01T00:00:00Z"
    published_before = "2025-01-15T23:59:59Z"

    videos = search_videos(query, max_results=3, published_after=published_after, published_before=published_before)
    print("Videos Found:")
    for video in videos:
        print(f"{video['title']} (ID: {video['video_id']}) Published At: {video['published_at']}")

    # Fetch comments for each video
    for video in videos:
        print(f"\nFetching comments for video: {video['title']} ({video['video_id']})")
        comments_df = getcomments(video, max_comments=20)  # Fetch 20 comments per video
        print(comments_df.head())  # Display the first few rows
