import os
import logging
from telegram.ext import CommandHandler, ApplicationBuilder
import random
from dotenv import load_dotenv
from reddit_scrape import RedditScrape

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')


class BotApp:

    def __init__(self):

        random.seed()

        self.reddit = RedditScrape()
        # for submission in self.reddit.subreddit("gifrecipes").hot(limit=10):
        #    print(submission.title)

        # connect to the Telegram bot
        # self.bot = telegram.Bot(token=TG_TOKEN)

        self.user_post_dict = dict()

        self.bot_app = ApplicationBuilder().token(TG_TOKEN).build()

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        self.init_handlers()

    def run(self):
        self.bot_app.run_polling()

    def init_handlers(self):

        start_handler = CommandHandler('start', self.start)
        self.bot_app.add_handler(start_handler)

        list_handler = CommandHandler('list', self.list)
        self.bot_app.add_handler(list_handler)

        recipe_handler = CommandHandler('recipe', self.recipe)
        self.bot_app.add_handler(recipe_handler)

        random_handler = CommandHandler('random', self.random)
        self.bot_app.add_handler(random_handler)

    async def start(self, update, context):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Hi! Please request some posts with `/list <num posts 1-25>` \n" +
                                       "Then use `/recipe <partial post name>` to get that recipe. " +
                                       "use `/random` to give a random recipe from the hottest 5" +
                                       "Right now I only support r/GifRecipes.",
                                       )

    async def random(self, update, context):
        chat_id = update.effective_chat.id
        post_list = self.reddit.get_sorted_hot_posts(5)
        val = random.randint(0, 4)

        recipe_text = self.get_recipe_from_post(post_list[val])
        await context.bot.send_message(chat_id=chat_id, text="Heres your random recipe result: " + str(post_list[val][1]))
        if not post_list[val][2].is_self:
            try:
                await context.bot.send_animation(chat_id=chat_id, animation=post_list[val][2].url)
            except:
                pass
        await context.bot.send_message(chat_id=chat_id, text=str(recipe_text))
        return

    async def list(self, update, context):
        num = None
        chat_id = update.effective_chat.id
        try:
            num = int(context.args[0])
            print("Got /recipe " + str(num) + " from: " + str(chat_id))
        except:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request.")
            return
        if num > 25 or num < 1:
            await context.bot.send_message(chat_id=chat_id, text="Invalid number of recipes requested.")
            return

        await context.bot.send_message(chat_id=chat_id,
                                 text="Heres the highest " + str(num) + " scoring posts on r/GifRecipes right now")

        post_list = self.reddit.get_sorted_hot_posts(num=num)

        self.user_post_dict[chat_id] = post_list

        for post in post_list:
            await context.bot.send_message(chat_id=chat_id, text=str(post[1]) + " - " + str(post[0]) + " Points")

    async def recipe(self, update, context):
        search_text = None
        chat_id = update.effective_chat.id
        try:
            search_text = ' '.join(context.args)
        except:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request")
            return
        # make sure were searching on actual text
        if search_text is None:
            return

        # Has this user searched for posts before? if not lets do a default search
        post_list = None
        try:
            post_list = self.user_post_dict[chat_id]
        except KeyError:
            post_list = self.reddit.get_sorted_hot_posts()

        # attempt to match search to post list
        for post in post_list:
            if search_text in post[1].lower():
                recipe_text = self.get_recipe_from_post(post)
                await context.bot.send_message(chat_id=chat_id, text="Heres the recipe result for " + str(post[1]))
                if not post[2].is_self:
                    try:
                        await context.bot.send_animation(chat_id=chat_id, animation=post[2].url)
                    except:
                        pass
                await context.bot.send_message(chat_id=chat_id, text=str(recipe_text))
                return

        await context.bot.send_message(chat_id=chat_id,
                                 text="Couldn't find that post title among your last post request")

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
