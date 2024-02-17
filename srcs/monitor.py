from discord.ext import tasks
from srcs.service import Service


class Monitor:
    def __init__(self, warningChannel):
        self.services: Service = {}
        self.current_status = {}
        self.previous_status = {}
        self.task = tasks.loop(seconds=5)(self.execute_task)
        self.warningChannel = warningChannel

    async def execute_task(self):
        isAnyServiceKO = any(
            service.status == "KO" for service in self.services.values()
        )
        if isAnyServiceKO:
            await self.warningChannel.edit(name="🔴-warning-channel")
        else:
            await self.warningChannel.edit(name="🟢-warning-channel")

        for service_name, service in self.services.items():
            self.previous_status[service_name] = self.current_status[service_name]
            self.current_status[service_name] = service.status
            current_status = "KO" if service.status == "KO" else "OK"
            if current_status != self.previous_status[service_name]:
                self.previous_status[service_name] = current_status
                if current_status == "KO":
                    await self.warningChannel.send(f"{service_name}: is KO !!!")
                else:
                    await self.warningChannel.send(f"{service_name}: back online !!!")

    def start(self):
        self.task.start()

    def add_service(self, service):
        self.services[service.name] = service
        self.current_status[service.name] = "OK"
        self.previous_status[service.name] = "OK"

    async def remove_service(self, service):
        del self.services[service.name]
        del self.current_status[service.name]
        del self.previous_status[service.name]
        isAnyServiceKO = any(
            service.status == "KO" for service in self.services.values()
        )
        if not isAnyServiceKO:
            await self.warningChannel.edit(name="🟢-warning-channel")
        else:
            await self.warningChannel.edit(name="🔴-warning-channel")
