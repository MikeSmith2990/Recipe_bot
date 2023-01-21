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

        test_handler = CommandHandler('test', self.test)
        self.bot_app.add_handler(test_handler)

    async def start(self, update, context):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Hi! Please request some posts with `/list <num posts 1-25>` \n" +
                                       "Then use `/recipe <partial post name>` to get that recipe. " +
                                       "use `/random` to give a random recipe from the hottest 5" +
                                       "Right now I only support r/GifRecipes.",
                                       )

    async def test(self, update, context):
        chat_id = update.effective_chat.id
        print("trying to grab image from second post")
        post_list = self.reddit.get_sorted_hot_posts(5)
        post = post_list[2]
        print("Post list:")
        print(str(post_list))
        print("post 2?")
        print(str(post))

    async def random(self, update, context):
        chat_id = update.effective_chat.id
        print("Got /random from: " + str(chat_id))

        await context.bot.send_message(chat_id=chat_id, text="Got request for random post. Processing...")

        post_list = self.reddit.get_sorted_hot_posts(5)
        val = random.randint(0, 4)

        recipe_text = self.get_recipe_from_post(post_list[val])
        await context.bot.send_message(chat_id=chat_id,
                                       text="Heres your random recipe result: " + str(post_list[val]["title"]))

        await context.bot.send_message(chat_id=chat_id,
                                       text="reddit.com" + str(post_list[val]["post"].permalink))

        await context.bot.send_message(chat_id=chat_id,
                                       disable_web_page_preview=True,
                                       text=str(recipe_text))
        return

    async def list(self, update, context):
        num = None
        chat_id = update.effective_chat.id
        try:
            num = int(context.args[0])
            print("Got /list " + str(num) + " from: " + str(chat_id))
        except:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request.")
            return
        if num > 25 or num < 1:
            await context.bot.send_message(chat_id=chat_id, text="Invalid number of recipes requested.")
            return

        await context.bot.send_message(chat_id=chat_id,
                                       text="Heres the highest " + str(num) +
                                            " scoring posts on r/GifRecipes right now")

        post_list = self.reddit.get_sorted_hot_posts(num=num)

        self.user_post_dict[chat_id] = post_list

        for post in post_list:
            await context.bot.send_message(chat_id=chat_id,
                                           text=str(post["title"]) + " - " + str(post["score"]) + " Points")

    async def recipe(self, update, context):
        search_text = None
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Got your request. Processing...")

        try:
            search_text = ' '.join(context.args)
            print("Got /recipe " + str(search_text) + " from: " + str(chat_id))
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

        # attempt to match search to post list,
        # returns first result that has the search text inside the post title
        for post in post_list:
            if search_text in post["title"].lower():
                recipe_text = self.get_recipe_from_post(post)
                await context.bot.send_message(chat_id=chat_id,
                                               text="Heres the recipe result for " + str(post["title"]))
                # send the gif link
                await context.bot.send_message(chat_id=chat_id,
                                             text="reddit.com" + str(post["post"].permalink))
                #send recipe
                await context.bot.send_message(chat_id=chat_id,
                                               disable_web_page_preview=True,
                                               text=str(recipe_text))
                return

        await context.bot.send_message(chat_id=chat_id,
                                       text="Couldn't find that post title among your last post request")

    def get_recipe_from_post(self, post_dict=None):
        if post_dict is None:
            return None

        post = post_dict["post"]
        comments = post.comments
        comments.replace_more(limit=1)
        first_comment = comments[0]  # should be the sticky comment...

        recipe_comment = None
        for recipe in first_comment.replies:
            recipe_comment = recipe
            break
        return recipe_comment.body

    def get_post_image(self, post_tup=None):
        if post_tup is None:
            return None

        post = post_tup[2]
        print(post.url)


