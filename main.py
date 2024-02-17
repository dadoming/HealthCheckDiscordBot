from os import getenv
from dotenv import load_dotenv
from srcs.bot import Bot


def main():
    load_dotenv()
    bot = Bot()
    bot.run(getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
