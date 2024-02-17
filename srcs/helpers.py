import json
from datetime import timedelta
from discord import utils

command_table = {
    "ping": {
        "full_command": "!ping <channel_name> <url> <interval>",
        "help_message": "Starts the Health Check on a service for every time interval until removed\n",
    },
    "help": {
        "full_command": "!help",
        "help_message": "Shows the list of commands\n",
    },
    "export": {
        "full_command": "!export <channel_name>",
        "help_message": "Exports the information of the services to a JSON file and allows it to be downloaded\n",
    },
    "status": {
        "full_command": "!status",
        "help_message": "Shows the status of all Health Checks\n",
    },
    "clean": {
        "full_command": "!clean",
        "help_message": "Removes all services\n",
    },
    "remove": {
        "full_command": "!remove <channel_name>",
        "help_message": "Removes specified Health Check\n",
    },
}


class col:
    CYELLOW = "\33[33m"
    CBLUE = "\33[34m"
    CEND = "\33[0m"


def get_timestamp():
    return utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def invalid_cmd_msg_formater(command: str):
    return f"Invalid Command, do !{command_table[command]['full_command']}"


def print_help_msg(channel, command):
    return f"-> {command_table[command]['full_command']}: {command_table[command]['help_message']}"


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return str(obj)
        return super().default(obj)
