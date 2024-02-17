import datetime
import discord
from discord.ext import tasks
import requests


class Service:
    def __init__(
        self,
        name,
        url,
        interval,
        chan: discord.TextChannel,
        warningChannel: discord.TextChannel,
    ):
        self.name = name
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        self.url = url
        if interval < 5:
            interval = 5
        self.interval = interval
        self.date = None
        self.time = None
        self.numeric = None
        self.status = None
        self.warningChannel = warningChannel
        self.channel = chan if chan is not None else None
        self.task = tasks.loop(seconds=interval)(self.execute_task)

    async def start(self, curr_guild: discord.Guild):
        if not self.channel:
            self.channel = await curr_guild.create_text_channel(
                self.name,
                overwrites={
                    curr_guild.default_role: discord.PermissionOverwrite(
                        send_messages=False
                    ),
                    curr_guild.me: discord.PermissionOverwrite(send_messages=True),
                },
            )
        await self.channel.set_permissions(curr_guild.default_role, send_messages=False)
        self.task.start()

    async def stop(self):
        self.task.stop()

    def __str__(self):
        return f"{self.name} {self.url} {self.interval}"

    def msg_formater(self):
        return f"{self.numeric} {self.status} {self.date} {self.time}"

    def load_time(self):
        self.date = datetime.datetime.now().strftime("%d-%m-%Y")
        self.time = datetime.datetime.now().strftime("%H:%M:%S")

    async def execute_task(self):
        try:
            if self.channel:
                if self.channel.guild.get_channel(self.channel.id) is not None:
                    response = requests.get(self.url, timeout=15)
                    self.numeric = response.status_code
                    response.raise_for_status()
                    self.status = self.numeric != 500 and "OK" or "KO"
                    self.load_time()
                    await self.channel.send(self.msg_formater())
        except requests.Timeout:
            self.numeric = 408
            self.status = "KO"
            self.load_time()
            msg = self.msg_formater()
            if (
                self.channel
                and self.channel.guild.get_channel(self.channel.id) is not None
            ):
                await self.channel.send(msg)
        except requests.RequestException as e:
            if e.response:
                self.numeric = e.response.status_code if e.response else 500
            else:
                self.numeric = 500
            self.status = "KO"
            self.load_time()
            msg = self.msg_formater()
            if (
                self.channel
                and self.channel.guild.get_channel(self.channel.id) is not None
            ):
                await self.channel.send(msg)
