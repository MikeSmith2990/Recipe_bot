# Script to grab the highest upvoted recipes from gifrecipes, and grab the instructions for each.
# Posts to telegram daily

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from app import BotApp

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

if __name__ == '__main__':
    app = BotApp()
    app.run()


