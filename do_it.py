import datetime

from alert_bot import AlertBot
from config import GROUPS, MIXIN_BOT_KEYSTORE, MIXIN_IDS, PORT

for group_name, group_id in GROUPS:
    print(datetime.datetime.now(), group_name)
    bot = AlertBot(PORT, group_id, MIXIN_BOT_KEYSTORE)
    bot.check_sync(10)
    bot.alert_by_mixin(group_name, MIXIN_IDS)
