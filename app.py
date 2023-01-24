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

        # Seed the RNG, Create the reddit instance for pulling data
        # Create the dict to store information (This will be replaced by persistent DB later)
        # create the bot app to get requests and reply
        # set up logging

        random.seed()

        self.reddit = RedditScrape()

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

        self.bot_app.add_handler(CommandHandler('start', self.start))
        logging.log(level=logging.INFO, msg="/Start handler added...")

        self.bot_app.add_handler(CommandHandler('list', self.list))
        logging.log(level=logging.INFO, msg="/List handler added...")

        self.bot_app.add_handler(CommandHandler('recipe', self.recipe))
        logging.log(level=logging.INFO, msg="/Recipe handler added...")

        self.bot_app.add_handler(CommandHandler('random', self.random))
        logging.log(level=logging.INFO, msg="/Random handler added...")

        self.bot_app.add_handler(CommandHandler('test', self.test))

    async def start(self, update, context):
        chat_id = update.effective_chat.id

        logging.log(level=logging.INFO, msg="Got /start from: " + str(chat_id))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Hi! Please request some posts with `/list <num posts 1-25>` \n" +
                                       "Then use `/recipe <partial post name>` to get that recipe. " +
                                       "use `/random` to give a random recipe from the hottest 5" +
                                       "Right now I only support r/GifRecipes.",
                                       )

    async def test(self, update, context):
        chat_id = update.effective_chat.id

        search_text = ' '.join(context.args)

        # Testing issue when supplying blank argument
        print("context.args: " + str(context.args))
        print("search_text: " + str(search_text))


    async def random(self, update, context):
        chat_id = update.effective_chat.id

        logging.log(level=logging.INFO, msg="Got /random from: " + str(chat_id))

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

        # check if there are args
        if not self.check_if_args_exist(context.args):
            await context.bot.send_message(chat_id=chat_id, text="No arguments supplied in command.")
            logging.log(level=logging.WARNING, msg="No arguments supplied in /list from " + str(chat_id))
            return

        # we have args, parse them
        try:
            num = int(context.args[0])
            logging.log(level=logging.INFO, msg="Got /list " + str(num) + " from: " + str(chat_id))
        except:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request.")
            logging.log(level=logging.WARNING, msg="Unable to parse request: " + str(context.args))
            return
        if num > 25 or num < 1:
            await context.bot.send_message(chat_id=chat_id, text="Invalid number of recipes requested.")
            return

        await context.bot.send_message(chat_id=chat_id,
                                       text="Here are the highest " + str(num) +
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

        # check if there are args
        if not self.check_if_args_exist(context.args):
            await context.bot.send_message(chat_id=chat_id, text="No arguments supplied in command.")
            logging.log(level=logging.WARNING, msg="No arguments supplied in /recipe from " + str(chat_id))
            return

        # we have args, parse them
        try:
            search_text = ' '.join(context.args)
            logging.log(level=logging.INFO, msg="Got /recipe " + str(search_text) + " from: " + str(chat_id))
        except:
            await context.bot.send_message(chat_id=chat_id, text="Sorry, couldn't parse that request.")
            logging.log(level=logging.WARNING, msg="Unable to parse request: " + str(context.args))
            return
        # make sure were searching on actual text
        if search_text.isspace():
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
            if search_text.lower() in post["title"].lower():
                recipe_text = self.get_recipe_from_post(post)
                await context.bot.send_message(chat_id=chat_id,
                                               text="Here is the recipe result for " + str(post["title"]))
                # send the gif link
                await context.bot.send_message(chat_id=chat_id,
                                               text="reddit.com" + str(post["post"].permalink))
                # send recipe
                await context.bot.send_message(chat_id=chat_id,
                                               disable_web_page_preview=True,
                                               text=str(recipe_text))
                return

        # we did not find the title in the list
        await context.bot.send_message(chat_id=chat_id,
                                       text="Couldn't find that post title among your last post request")

    @staticmethod
    def check_if_args_exist(args_list):
        return False if args_list == [] else True

    @staticmethod
    def get_recipe_from_post(post_dict=None):
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
