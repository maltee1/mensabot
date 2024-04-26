from maubot import Plugin, MessageEvent
from maubot.handlers import command
from .studierendenwerk import *
import datetime

class MensaBot(Plugin):
    @command.new()
    async def speiseplan(self, evt: MessageEvent) -> None:
        today = datetime.datetime.today().date().isoformat()
        htmlMenu = download_menu(321, today)
        textMenu = parse_menu(htmlMenu)
        await evt.reply(textMenu, allow_html=True)