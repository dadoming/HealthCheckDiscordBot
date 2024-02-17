from discord.ext import tasks
from srcs.service import Service


class Monitor:
    def __init__(self, warningChannel):
        self.services: Service = {}
        self.current_status = {}
        self.previous_status = {}
        self.task = tasks.loop(seconds=1)(self.execute_task)
        self.warningChannel = warningChannel

    async def execute_task(self):
        for service in self.services:
            if self.services[service].status == "KO":
                self.current_status[service] = "KO"
            else:
                self.current_status[service] = "OK"
            if self.current_status[service] != self.previous_status[service]:
                self.previous_status[service] = self.current_status[service]
                if self.current_status[service] == "KO":
                    await self.warningChannel.send(
                        f"{service}: is {self.current_status[service]} !!!"
                    )
                else:
                    await self.warningChannel.send(f"{service}: back online !!!")

    def start(self):
        self.task.start()

    def add_service(self, service):
        self.services[service.name] = service
        self.current_status[service.name] = "OK"
        self.previous_status[service.name] = "OK"

    def remove_service(self, service):
        del self.services[service.name]
        del self.current_status[service.name]
        del self.previous_status[service.name]
