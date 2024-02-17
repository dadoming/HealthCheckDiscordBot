import json
from os import getenv
import discord
from discord.ext import commands
from srcs.monitor import Monitor
from srcs.service import Service
from srcs.helpers import (
    CustomEncoder,
    get_timestamp,
    invalid_cmd_msg_formater,
    print_help_msg,
    col,
)


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.services: Service = {}
        self.myGuild = None
        self.monitor = None
        self.channels = None
        self.commands_map = {
            "ping": self.ping_api,
            "help": self.help,
            "status": self.status,
            "export": self.export,
            "clean": self.clean,
            "remove": self.remove,
        }

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        params = message.content.split(" ")
        params = list(map(lambda x: x.lower(), params))
        command = params[0][1:]
        if command in self.commands_map:
            await self.commands_map[command](message.channel, params)
        else:
            await message.channel.send("Invalid command")

    async def on_ready(self):
        self.myGuild = self.get_guild(int(getenv("GUILD_ID")))
        self.console_log("Online", "🟢")
        self.console_log("Getting all disconnected services", "🔍")
        channels = self.get_channels_from_discord()
        await self.create_warning_channel()
        self.monitor = Monitor(self.warning_channel)
        self.monitor.start()
        restarted_services = []
        all_services = []
        if channels:
            self.console_log("Restarting disconnected services", "🔄")
            for channel in channels:
                if channel.permissions_for(self.myGuild).manage_channels:
                    all_services.append(channel.name)
                    channel_topic = channel.topic.split(" ")
                    if channel_topic[0][1:].lower() == "ping":
                        await self.turn_on_service(channel_topic, channel)
                        restarted_services.append(channel_topic[1])
            if len(restarted_services) == len(all_services):
                self.console_log("All services restarted ", "✅")

            else:
                missed_services = list(set(all_services) - set(restarted_services))
                self.console_log(f"Failed restarting: {missed_services}", "❌")
        else:
            self.console_log("No services found to restart", "😐")

    async def create_warning_channel(self):
        warning_channel = discord.utils.get(
            self.myGuild.text_channels, name="warning-channel"
        )
        if not warning_channel:
            self.console_log("Creating warning channel", "🟢")
            self.warning_channel = await self.myGuild.create_text_channel(
                "warning-channel",
                overwrites={
                    self.myGuild.default_role: discord.PermissionOverwrite(
                        send_messages=False
                    ),
                    self.myGuild.me: discord.PermissionOverwrite(send_messages=True),
                },
            )
        else:
            self.warning_channel = warning_channel
        await self.warning_channel.set_permissions(
            self.myGuild.default_role, send_messages=False
        )

    async def turn_on_service(self, channel_topic, channel):
        name = channel_topic[1]
        url = channel_topic[2]
        interval = int(channel_topic[3])
        service = Service(name, url, interval, channel, self.warning_channel)
        await service.start(self.myGuild)
        await service.channel.edit(topic=f"!ping {name} {url} {interval}")
        self.services[name] = service
        self.monitor.add_service(service)

    def console_log(self, msg, emoji=" "):
        date = get_timestamp()
        print(
            f"{date}  {emoji}      {col.CYELLOW}BOT{col.CEND} {col.CBLUE}{self.user.name}{col.CEND}: {msg}"
        )

    async def ping_api(self, channel, params):
        if len(params) < 4:
            await channel.send(invalid_cmd_msg_formater("ping"))
            return
        self.console_log("Received ping command: " + " ".join(params), "🔔")
        if int(params[3]) <= 0:
            await channel.send("Interval must be greater than 0")
            self.console_log("Contains invalid interval", "❌")
            return
        full_list = self.get_channels_from_discord()
        name = params[1]
        if full_list:
            for channel in full_list:
                if channel.name == name:
                    await channel.send(f"Service {name} already exists")
                    self.console_log("Channel already exists", "❌")
                    return
        await self.turn_on_service(params, None)
        self.console_log("Service " + name + " started", "✅")
        await channel.send(f"Service {name} added")

    async def remove(self, channel, params):
        if len(params) < 2:
            await channel.send(invalid_cmd_msg_formater("stop"))
            return
        if params[2] == "option":
            self.reload_channels_from_discord()
            self.console_log("Received remove command: " + " ".join(params), "🔔")
        service_name = params[1]
        service = self.services.get(service_name)
        if service:
            await service.stop()
            await service.channel.delete()
            del self.services[service_name]
            self.monitor.remove_service(service)
            await channel.send(f"Service {service_name} removed")
            self.console_log("Service " + service_name + " removed", "✅")
        else:
            await channel.send(f"No service with name {service_name} found")
            self.console_log("Service " + service_name + " not found", "❌")

    async def clean(self, channel, params):
        self.console_log("Received clean command: " + " ".join(params), "🔔")
        self.reload_channels_from_discord()
        if self.services:
            for service in list(self.services.values()):
                await self.remove(channel, ["remove", service.name, "option"])
            self.services = {}
            self.console_log("All services removed", "✅")
            await channel.send("All services removed")
        else:
            self.console_log("No services to remove", "😐")
            await channel.send("No services to remove")

    async def status(self, channel, params):
        self.console_log("Received status command: " + " ".join(params), "🔔")
        send_string = ""
        if self.services:
            send_string += "Active Services:\n"
            for service in self.services.values():
                send_string += f"{service.name}: {service.url}\n"
            await channel.send(send_string)
        else:
            await channel.send("No active services")

    def get_channels_from_discord(self):
        self.reload_channels_from_discord()
        return self.channels

    def reload_channels_from_discord(self):
        self.channels = self.myGuild.text_channels
        channels = list(
            filter(
                lambda x: x.name.lower()
                not in [
                    "geral",
                    "canais de texto",
                    "canais de voz",
                ]
                and "warning-channel" not in x.name.lower(),
                self.channels,
            )
        )
        self.channels = channels

    async def export(self, channel, params):
        if len(params) < 2:
            await channel.send(invalid_cmd_msg_formater("Export"))
            return
        self.console_log("Received export command: " + " ".join(params), "🔔")
        wanted_channel: discord.TextChannel = discord.utils.get(
            self.channels, name=params[1]
        )
        if not wanted_channel:
            await wanted_channel.send(f"No service with name {params[1]} found")
            self.console_log("Service " + params[1] + " not found", "❌")
            return
        channel_topic = wanted_channel.topic.split(" ")
        name, url, interval = channel_topic[1], channel_topic[2], channel_topic[3]
        messages = []
        async for message in wanted_channel.history(limit=None):
            messages.append(message.content)
        separated_content = []
        for message in messages:
            parts = message.split(" ")
            if len(parts) >= 4:
                status = parts[0]
                code = parts[1]
                time = parts[2]
                day = parts[3]
                json_string = json.dumps(
                    {"status": status, "code": code, "time": time, "day": day}
                )
                separated_content.append(json_string)
        if separated_content:
            filename = f"exports/{name}.json"
            data = {
                "name": name,
                "url": url,
                "interval": int(interval),
                "messages": separated_content,
            }
            json_string = json.dumps(data, cls=CustomEncoder)
            with open(filename, "w") as file:
                file.write(json_string)
            self.console_log(
                f"File has been exported and can be found at exports/{name}.json", "✅"
            )
            file = discord.File(filename, filename=filename, spoiler=False)
            await channel.send("Here is your file!", file=file)
        else:
            await channel.send(f"No data to export for {name}")
            self.console_log(f"No data to export for {name}", "❌")

    async def help(self, channel, params):
        self.console_log("Received help command: " + " ".join(params), "🔔")
        if len(params) == 1:
            send_string = (
                "List of all available commands:\n"
                + print_help_msg(channel, "ping")
                + print_help_msg(channel, "remove")
                + print_help_msg(channel, "clean")
                + print_help_msg(channel, "export")
                + print_help_msg(channel, "status")
                + print_help_msg(channel, "help")
            )
            await channel.send(send_string)
            return
