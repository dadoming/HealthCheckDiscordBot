## ONCE THE TEMP COMMAND IS GIVEN, THE BOT WILL CREATE A CHANNEL FOR THE SERVICE AND START PINGING THE URL
## Thus removing the need for the interval, the bot will ping the url every minute and store the information in the database
## or there is no need to store the information in the database, the bot will just store the information in the service object

## When main is called , the bot will check if there are channels and will grab the last information from them

## Há servicos permanentes e temporarios porque os temporarios sao para mandar um certo numero de pings e os permanentes sao para ficar pinging para sempre
### assim o bot tem mais facilidade em questoes de limpeza e de organizacao
#### Implementar um sistema de limpeza para os servicos temporarios que ja acabaram (Cleaning Thread)

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests
import threading
import time
import json
import datetime
from datetime import timedelta

command_table = {
    "BotOn": {
        "full_command": "BotOn",
        "help_message": "Turns the bot on, starting again the Health Check services\n",
    },
    "BotOff": {
        "full_command": "BotOff",
        "help_message": "Turns the bot off, stopping all pings for the Health Check services\n",
    },
    "PingTemp": {
        "full_command": "PingTemp Name(Channel) URL Interval(seconds) Times(Total pings)",
        "help_message": "Starts the Heath Check on a service for n_Times\n",
    },
    "PingPerm": {
        "full_command": "PingPerm Name(Channel) URL Interval(seconds)",
        "help_message": "Starts the Health Check forever on a service until stopped\n",
    },
    "Stop": {
        "full_command": "Stop Name(Channel)",
        "help_message": "Stops the Health Check on a service\n",
    },
    "Help": {
        "full_command": "Help <command>...<n>...<command>",
        "help_message": "Shows the list of commands, optional keywords \{bot, ping, status, export\}\n",
    },
    "Export": {
        "full_command": "Export Name(Channel)",
        "help_message": "Exports the information of the services to a JSON file and allows it to be downloaded\n",
    },
    "Status": {
        "full_command": "Status",
        "help_message": "Shows the status of the bot and all Active Health Checks (active or inactive)\n",
    },
    "Clean": {
        "full_command": "Clean",
        "help_message": "Cleans the temporary services that have existed for more than 5 minutes\n",
    },
}


def invalid_cmd_msg_formater(command: str):
    return f"Invalid Command, do !{command_table[command]['full_command']}"


def print_help_msg(channel, command):
    return f"-> {command_table[command]['full_command']}: {command_table[command]['help_message']}"


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return str(obj)
        return super().default(obj)


class Service:
    def __init__(self, name, url, interval, times, type):
        print(f"Service {name} created")
        self.url = url
        self.interval = interval
        self.times = times
        self.active = True
        self.timeOfLastPing = ""
        self.timeOfLastResponse = ""
        self.responseCode = 0
        self.responseTime = 0
        self.responseMessage = ""
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.channel = None
        self.type = type
        self.name = name

    def restart_service(self, name, url, interval, times, type):
        self.url = url
        self.interval = interval
        self.type = type
        self.times = times
        self.active = True
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    def start_pinging(self):
        self.active = True
        while not self.stop_event.is_set():
            with self.lock:
                if not self.active:
                    break
            try:
                print(f"Pinging {self.url}")
                response = requests.get(self.url)
                self.timeOfLastPing = response.elapsed
                self.timeOfLastResponse = response.elapsed
                self.responseCode = response.status_code
                self.responseTime = response.elapsed
                self.responseMessage = response.text
                print(
                    f"Response from {self.url}: {self.responseCode} - {self.responseTime} - {self.responseMessage}"
                )
            except Exception as error:
                print(f"Error occurred while pinging {self.url}: {error}")
                self.active = False
            with self.lock:
                if self.times != float("inf"):
                    self.times -= 1
                    if self.times <= 0:
                        break
            time.sleep(self.interval)
        self.active = False

    def stop_service(self):
        self.stop_event.set()

    def join_thread(self):
        if self.thread:
            self.thread.join()

    def reset_values(self):
        self.active = False
        self.responseCode = 0
        self.responseTime = 0
        self.responseMessage = ""
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.botCommands = BotCommands(self)
        self.active = False
        self.permanentServices = {}
        self.temporaryServices = {}
        self.threads = {}
        # check if there are guilds and if there are, get the last msg from each channel
        # channels = self.get_all_channels()
        # print(channels)
        # if channels:
        #     for guild in self.guilds:
        #         for channel in guild.text_channels:
        #             print(channel)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        print(
            f"{message.channel}: {message.author}: {message.author.name}: {message.content}"
        )
        params = message.content.split(" ")
        params[0] = params[0].lower()
        await self.which_cmd(params, message)

    async def which_cmd(self, params, message):
        if params[0] == "!boton":
            await self.botCommands.bot_on(message.channel)
        elif params[0] == "!botoff":
            await self.botCommands.bot_off(message.channel)
        elif params[0] == "!pingtemp":
            await self.botCommands.start_health_check(
                message.channel, message, params, "temp"
            )
        elif params[0] == "!pingperm":
            await self.botCommands.start_health_check(
                message.channel, message, params, "perm"
            )
        elif params[0] == "!stop":
            await self.botCommands.stop_running_service(message.channel, params)
        elif params[0] == "!help":
            await self.botCommands.help(message.channel, params)
        elif params[0] == "!status":
            await self.botCommands.status(message.channel, params)
        elif params[0] == "!export":
            await self.botCommands.export(message.channel, params)
        elif params[0] == "!clean":
            await self.botCommands.clean(message.channel, params)
        else:
            await message.channel.send("Invalid Command")

    async def on_ready(self):
        print(f"We have logged in as {self.user.name}")

    async def setup_channel(self, name, guild):
        channel = await guild.create_text_channel(
            name,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                guild.me: discord.PermissionOverwrite(send_messages=True),
            },
        )
        return channel

    async def stop_service(self, channel, service_name):
        service = self.temporaryServices.get(service_name)
        if service:
            service.stop_service()
            service.join_thread()
            await channel.send(f"Service {service_name} stopped")
            print(f"Service {service_name} stopped")
            service.reset_values()
        else:
            await channel.send(f"No service with name {service_name} found")
            print(f"No service with name {service_name} found")


class BotCommands:
    def __init__(self, bot):
        self.bot = bot

    async def bot_on(self, channel):
        if self.bot.active:
            await channel.send("Bot is already active")
        self.bot.active = True
        await channel.send("Bot is now active")
        # TODO: Start the ping loop with the permanent services
        if self.bot.permanentServices:
            for service in self.bot.permanentServices.values():
                service.thread = threading.Thread(target=self.bot.start_pinging)
                service.thread.start()

    # TODO: Is not stopping the threads
    async def bot_off(self, channel):
        if not self.bot.active:
            await channel.send("Bot is already inactive")
        if self.bot.temporaryServices:
            for service in self.bot.temporaryServices.values():
                self.bot.stop_service(channel, service.name)
        if self.bot.permanentServices:
            for service in self.bot.permanentServices.values():
                print(f"--> Stopping {service.name}")
                service.stop_service(channel, service.name)
        self.bot.active = False
        await channel.send("Bot is now inactive")

    async def stop_running_service(self, channel, params):
        if len(params) < 2:
            await channel.send(invalid_cmd_msg_formater("Stop"))
            return
        service_name = params[1]
        await self.bot.stop_service(channel, service_name)

    async def start_health_check(self, channel, message, params, type):
        if not self.bot.active:
            await channel.send("Bot is inactive, do !boton")
            return
        if len(params) < 5 and type == "temp":
            await channel.send(invalid_cmd_msg_formater("PingTemp"))
            return
        if len(params) < 4 and type == "perm":
            await channel.send(invalid_cmd_msg_formater("PingPerm"))
            return

        name = params[1]
        url = params[2]
        try:
            interval = int(params[3])
            if interval <= 10:
                await channel.send("Do an interval greater than 10 seconds")
                return
            if len(params) < 5 and type == "temp":
                times = int(params[4])
            if type == "temp" and times <= 0:
                await channel.send("Times must be greater than 0")
            elif type == "perm":
                times = float("inf")
        except ValueError:
            await channel.send("Interval must be a number")
            return

        if (
            name in self.bot.temporaryServices
            and self.bot.temporaryServices[name].active
            or name in self.bot.permanentServices
            and self.bot.permanentServices[name].active
        ):
            await channel.send(f"You are already pinging {name}")
            return

        if name in self.bot.temporaryServices and type == "perm":
            service = self.bot.temporaryServices[name]
            self.bot.temporaryServices.pop(name)
            service.restart_service(name, url, interval, times, type)
            self.bot.permanentServices[name] = service
            await channel.send(f"Service {name} added to the permanent services")
        elif name in self.bot.permanentServices and type == "temp":
            await channel.send(
                f"Service {name} is already permanent so it cannot be temporary, remove it first"
            )
        else:
            service = Service(name, url, interval, times, type)
            service.channel = await self.bot.setup_channel(name, message.guild)
            self.bot.temporaryServices[name] = service
            await channel.send(f"Service {url} added to the Health Check services")

        if (service.name not in self.bot.threads) or (
            not self.bot.threads[service.name].is_alive()
        ):
            service.thread = threading.Thread(target=service.start_pinging)
            service.thread.start()

    async def help(self, channel, params):
        print(f"Params: {params} len {len(params)}")
        if len(params) == 1:
            send_string = (
                "List of all available commands:\n"
                + print_help_msg(channel, "BotOn")
                + print_help_msg(channel, "BotOff")
                + print_help_msg(channel, "PingTemp")
                + print_help_msg(channel, "PingPerm")
                + print_help_msg(channel, "Stop")
                + print_help_msg(channel, "Help")
                + print_help_msg(channel, "Export")
                + print_help_msg(channel, "Status")
                + print_help_msg(channel, "Clean")
            )
            await channel.send(send_string)
            return
        else:
            unique_params = list(set(params))
            send_string = ""
            for param in unique_params:
                param = param.lower()
                if param == "bot":
                    send_string += print_help_msg(channel, "BotOn")
                    send_string += print_help_msg(channel, "BotOff")
                elif param == "ping":
                    send_string += print_help_msg(channel, "PingTemp")
                    send_string += print_help_msg(channel, "PingPerm")
                    send_string += print_help_msg(channel, "Stop")
                elif param == "status":
                    send_string += print_help_msg(channel, "Status")
                elif param == "export":
                    send_string += print_help_msg(channel, "Export")
                elif param == "clean":
                    send_string += print_help_msg(channel, "Clean")
            if send_string == "":
                send_string = "Invalid command"
            await channel.send(send_string)

    # TODO printing inative and still has services rolling
    async def status(self, channel, params):
        if self.bot.active:
            send_string = "Active\n"
            if self.bot.permanentServices:
                send_string += "Active Permanent Services:\n"
                for service in self.bot.permanentServices.values():
                    send_string += f"{service.name}: {service.url}\n"
            if self.bot.temporaryServices:
                send_string += "Active Temporary Services:\n"
                for service in self.bot.temporaryServices.values():
                    send_string += f"{service.name}: {service.url}\n"
            await channel.send(send_string)
        else:
            await channel.send("Inactive\nAll Health Check services are also inactive")

    async def export(self, channel, params):
        if len(params) < 2:
            await channel.send(invalid_cmd_msg_formater("Export"))
            return
        service_name = params[1]

        if service_name in self.bot.permanentServices:
            service = self.bot.permanentServices[service_name]
        elif service_name in self.bot.temporaryServices:
            service = self.bot.temporaryServices[service_name]
        else:
            await channel.send(f"No service with name {service_name} found")
            return

        filename = f"exports/{service_name}.json"

        # put time in json
        data = {
            "url": str(service.url),
            "interval": str(service.interval),
            "active": str(service.active),
            "timeOfLastPing": str(service.timeOfLastPing),
            "timeOfLastResponse": str(service.timeOfLastResponse),
            "responseCode": str(service.responseCode),
            "responseTime": str(service.responseTime),
            "responseMessage": str(service.responseMessage),
            "name": str(service.name),
        }

        json_string = json.dumps(data, cls=CustomEncoder)
        with open(filename, "w") as file:
            file.write(json_string)

        file = discord.File(filename, filename=filename, spoiler=False)
        await channel.send("Here is your file!", file=file)

    ## Clean the temporary services that have existed for more than 5 minutes
    ## TODO: Implement a cleaning thread that will clean the temporary services that have existed for more than 5 minutes
    async def clean(self, channel, params):
        if self.bot.temporaryServices:
            for service in self.bot.temporaryServices.values():
                if not service.active:
                    self.bot.temporaryServices.pop(service.name)
                    await channel.send(f"Service {service.name} removed")
        else:
            await channel.send("No temporary services to clean")


def main():
    load_dotenv()
    bot = Bot()
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
