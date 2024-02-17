from os import getenv
from dotenv import load_dotenv
from srcs.bot import Bot

## import flask to get the server running and accepting requests from front end


def main():
    load_dotenv()
    bot = Bot()
    bot.run(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
