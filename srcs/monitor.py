import discord
from discord.ext import tasks
from srcs.service import Service


class Monitor:
    def __init__(self, warningChannel: discord.TextChannel):
        self.services: Service = {}
        self.current_status = {}
        self.previous_status = {}
        self.task = tasks.loop(seconds=5)(self.execute_task)
        self.warningChannel = warningChannel

    async def execute_task(self):
        await self.define_title()

        await self.remove_command_messages(self.warningChannel)
        for service_name, service in self.services.items():
            await self.remove_command_messages(service.channel)
            self.previous_status[service_name] = self.current_status[service_name]
            self.current_status[service_name] = service.status
            if self.current_status[service_name] != self.previous_status[service_name]:
                self.previous_status[service_name] = self.current_status[service_name]
                if self.current_status[service_name] == "KO":
                    await self.warningChannel.send(f"{service_name}: is KO !!!")
                else:
                    await self.warningChannel.send(f"{service_name}: back online !!!")

    async def remove_command_messages(self, channel: discord.TextChannel):
        async for message in channel.history(limit=15):
            if message.author != self.warningChannel.guild.me:
                await message.delete()
            elif (
                message.author == self.warningChannel.guild.me
                and message.content.startswith("Invalid")
            ):
                await message.delete()

    def start(self):
        self.task.start()

    async def add_service(self, service):
        self.services[service.name] = service
        self.current_status[service.name] = "OK"
        self.previous_status[service.name] = "OK"
        await self.define_title()

    async def remove_service(self, service):
        del self.services[service.name]
        del self.current_status[service.name]
        del self.previous_status[service.name]
        await self.define_title()

    async def clean(self):
        self.services = {}
        self.current_status = {}
        self.previous_status = {}
        self.clean_channel()
        await self.define_title()

    async def define_title(self):
        isAnyServiceKO = any(
            service.status == "KO" for service in self.services.values()
        )
        if not isAnyServiceKO:
            await self.warningChannel.edit(name="🟢-warning-channel")
        else:
            await self.warningChannel.edit(name="🔴-warning-channel")
        await self.warningChannel.edit(name="🟢-warning-channel")

    async def clean_channel(self, channel, params):
        await self.warningChannel.purge()
        await self.define_title()
