from os import getenv
from dotenv import load_dotenv
from srcs.bot import Bot
from srcs.helpers import create_exports_directory


def main():
    create_exports_directory()
    load_dotenv()
    bot = Bot()
    bot.run(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
