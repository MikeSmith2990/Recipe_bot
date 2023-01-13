# Script to grab the highest upvoted recipes from gifrecipes, and grab the instructions for each.
# Posts to telegram daily

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os
import praw
import telegram
from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler
import random
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
USERAGENT = os.getenv('USERAGENT')

TG_TOKEN = os.getenv('TG_TOKEN')

# found at: t.me/KitRecipeBot @KitRecipeBot



# commands supported:
# /start gives some starting commands
# /list <number of posts> returns number of hot posts
# /recipe <partial searchterm> search the cached posts for the term

# ideas?
# /search <search term> search hot 100 posts for the term and return results
# /random give me a random recipe from the top 5





# SHIT TODO: check to make sure a message isnt a fucking billion miles long before we send it,
#  so we can send it in CHUNKS with a 1/<num chunks> tag at the end

# TODO: figure out why the gif forwarding doesnt work

# TODO: get a link to the reddit post included so they can go look for themselves



class RecipeBot:
    def __init__(self):
        # create reddit connection object to use
        self.reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            #password=PASSWORD,
            user_agent=USERAGENT,
            #username=USERNAME,
        )

        for submission in self.reddit.subreddit("gifrecipes").hot(limit=10):
            print(submission.title)

        # connect to the Telegram bot
        self.bot = telegram.Bot(token=TG_TOKEN)

        #self.user_post_dict = dict()

        #self.updater = Updater(token=TG_TOKEN, use_context=True)

        #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                            level=logging.INFO)

        #start_handler = CommandHandler('start', self.start)
        #self.updater.dispatcher.add_handler(start_handler)

        #list_handler = CommandHandler('list', self.list)
        #self.updater.dispatcher.add_handler(list_handler)

        #recipe_handler = CommandHandler('recipe', self.recipe)
        #self.updater.dispatcher.add_handler(recipe_handler)

        #random_handler = CommandHandler('random', self.random)
        #self.updater.dispatcher.add_handler(random_handler)

    def run(self):
        self.updater.start_polling()

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Hi\! Please request some posts with `/list <num posts 1-25>` \n" +
                                      "Then use `/recipe <partial post name>` to get that recipe\. " +
                                      "use `/random` to give a random recipe from the hottest 5" +
                                      "Right now I only support r/GifRecipes\.",
                                 parse_mode=telegram.ParseMode.MARKDOWN_V2)

    def random(self, update, context):
        chat_id = update.effective_chat.id
        post_list = self.get_sorted_hot_posts(5)
        val = random.randint(0, 4)

        recipe_text = self.get_recipe_from_post(post_list[val])
        context.bot.send_message(chat_id=chat_id, text="Heres your random recipe result: " + str(post_list[val][1]))
        if not post_list[val][2].is_self:
            try:
                context.bot.send_animation(chat_id=chat_id, animation=post_list[val][2].url)
            except:
                pass
        context.bot.send_message(chat_id=chat_id, text=str(recipe_text))
        return

    def list(self, update, context):
        num = None
        chat_id = update.effective_chat.id
        try:
            num = int(context.args[0])
            print("Got /recipe " + str(num) + " from: " + str(chat_id))
        except:
            context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request.")
            return
        if num > 25 or num < 1:
            context.bot.send_message(chat_id=chat_id, text="Invalid number of recipes requested.")
            return

        context.bot.send_message(chat_id=chat_id,
                                 text="Heres the highest " + str(num) + " scoring posts on r/GifRecipes right now")

        post_list = self.get_sorted_hot_posts(num=num)

        self.user_post_dict[chat_id] = post_list

        for post in post_list:
            context.bot.send_message(chat_id=chat_id, text=str(post[1]) + " - " + str(post[0]) + " Points")

    def recipe(self, update, context):
        search_text = None
        chat_id = update.effective_chat.id
        try:
            search_text = ' '.join(context.args)
        except:
            context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request")
            return
        # make sure were searching on actual text
        if search_text is None:
            return

        # Has this user searched for posts before? if not lets do a default search
        post_list = None
        try:
            post_list = self.user_post_dict[chat_id]
        except KeyError:
            post_list = self.get_sorted_hot_posts()

        # attempt to match search to post list
        for post in post_list:
            if search_text in post[1].lower():
                recipe_text = self.get_recipe_from_post(post)
                context.bot.send_message(chat_id=chat_id, text="Heres the recipe result for " + str(post[1]))
                if not post[2].is_self:
                    try:
                        context.bot.send_animation(chat_id=chat_id, animation=post[2].url)
                    except:
                        pass
                context.bot.send_message(chat_id=chat_id, text=str(recipe_text))
                return

        context.bot.send_message(chat_id=chat_id,
                                 text="Couldn't find that post title among your last post request")

    def get_sorted_hot_posts(self, num=10, flair=None):
        # Gets number of posts from gifrecipe hot list, sorted by score. Default is 10
        # returns tuple of (score, post title, post object, post flair)

        post_list = list()
        count = 0

        for post in self.reddit.subreddit("gifrecipes").hot(limit=None):
            if post.stickied or post.is_self or (post.link_flair_text != flair and flair is not None):
                continue
            # add to tuple...
            post_list.append((post.score, post.title, post, post.link_flair_text))
            count += 1
            if count == num:
                break

        # sort them by score
        sorted_post_list = sorted(post_list, key=lambda post: post[0])
        sorted_post_list.reverse()
        return sorted_post_list

    def get_recipe_from_post(self, post_tup=None):
        if post_tup is None:
            return None

        post = post_tup[2]
        comments = post.comments
        comments.replace_more(limit=1)
        first_comment = comments[0]  # should be the sticky comment...

        recipe_comment = None
        for recipe in first_comment.replies:
            recipe_comment = recipe
            break
        return recipe_comment.body





if __name__ == '__main__':
    random.seed()
    bot = RecipeBot()
    #bot.run()

