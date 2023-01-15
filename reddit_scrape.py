import os
import praw
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
USERAGENT = os.getenv('USERAGENT')


class RedditScrape:

    def __init__(self):
        # Create the reddit connection object
        self.reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            # password=PASSWORD,
            user_agent=USERAGENT,
            # username=USERNAME,
            check_for_async=False
        )

    def get_sorted_hot_posts(self, num=10, flair=None):
        # Gets number of posts from gifrecipe hot list, sorted by score. Default is 10
        # returns dict of Post object, post score, post title, post flair

        # if no posts requested, return
        if num == 0:
            return None

        post_list = list()
        count = 0

        for post in self.reddit.subreddit("gifrecipes").hot(limit=None):
            if post.stickied or post.is_self or (post.link_flair_text != flair and flair is not None):
                continue
            # add to tuple...
            post_list.append({
                "post": post,
                "score": post.score,
                "title": post.title,
                "flair": post.link_flair_text
                             })
            count += 1
            if count == num:
                break

        # sort them by score
        sorted_post_list = sorted(post_list, key=lambda post: post["score"])
        sorted_post_list.reverse()
        return sorted_post_list
