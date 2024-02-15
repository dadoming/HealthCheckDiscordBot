
## Make the bot react to a message when received
## Make the bot be on and off upon command
## Make the bot be able to start looping in ping loop, this means constantly pinging the url's (every minute?)
## Link the bot to a mongoDB database to store the information of the services and make a search through the database to see if the service is already there
##  if it is, then continue adding it to that id. This happens by url, if the url is the same, then it is the same service


## Types of commands:
## 1. BotON
## 2. BotOFF
## 3. PingTemp URL interval times -> Pings the URL every interval
##    PingPerm URL interval -> Pings the URL every interval
## 4. Help
## 5. Status -> Shows the status of the bot (active or inactive)
##           -> If active shows what he is doing
##

# Service Class:
#  Variables:
#    - url: String
#    - interval: int
#    - active: Boolean
#    - timeOfLastPing: DateTime
#    - timeOfLastResponse: DateTime
#    - responseCode: int
#    - responseTime: int
#    - responseMessage: String
#  Methods:

# Bot Class:
#  Variables:
#    - active: Boolean
#    - permanentServices: List of Services
#    - temporaryServices: List of Services
#    - info: String(JSON)
#listen_to_commands

import discord
import threading
import requests
import asyncio
import time
import json

class Bot(discord.Client):
    def __init__(self):
        self.active = False
        self.permanentServices = []
        self.temporaryServices = []
        self.info = ""
        self.loop.create_task(listen_to_commands(self))

    #def bot_on(self):
    #    self.active = True
        #Start the ping loop with the permanent services

    #def bot_off(self):
     #   self.active = False
      #  self.temporaryServices = []

    #def ping_temp(self):
        # add to the list of temporary services

    #def ping_perm(self):
        # add to the list of permanent services

    #def help(self):
     #   return "Commands: \n 1. BotON \n 2. BotOFF \n 3. PingTemp URL interval \n 4. PingPerm URL interval \n 5. Help \n 6. Status"

    #def status(self):
        ## 5. Status -> Shows the status of the bot (active or inactive)
        ##           -> If active shows what he is doing
      #  if self.active:
       #     return "Active"
        #else:
         #   return "Inactive"


# if interval == 0 start loop, == 0 means break
class Service:
    def __init__(self, url, interval):
        self.url = url
        self.interval = interval
        self.times = 0
        self.active = False
        self.timeOfLastPing = ""
        self.timeOfLastResponse = ""
        self.responseCode = 0
        self.responseTime = 0
        self.responseMessage = ""
        self.thread = threading.Thread(target=self.start_pinging)

    def start_pinging(self):
        self.active = True
        while self.active:
            response = requests.get(self.url)
            self.timeOfLastPing = response.elapsed
            self.timeOfLastResponse = response.elapsed
            self.responseCode = response.status_code
            self.responseTime = response.elapsed
            self.responseMessage = response.text
            if self.interval != 0:
                   time.sleep(self.interval)
            else:
                break



bot = Bot
@bot.event
async def listen_to_commands():
    command = await bot.wait_for('message')
    send_message(command.content)

async def send_message(message):
    await bot.send_message(message.channel, message)

def main():
    bot.run('TOKEN')

if __name__ == "__main__":
    main()
