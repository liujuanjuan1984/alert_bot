import datetime

from alert_bot import AlertBot
from config import MIXIN_BOT_KEYSTORE, MIXIN_IDS

fullnode_port = 62663

groups = [
    (
        "去中心推特",
        "bd119dd3-081b-4db6-9d9b-e19e3d6b387e",
    ),
    (
        "去中心微博",
        "3bb7a3be-d145-44af-94cf-e64b992ff8f0",
    ),
]

for group_name, group_id in groups:
    print(datetime.datetime.now(), group_name)
    bot = AlertBot(fullnode_port, group_id, MIXIN_BOT_KEYSTORE)
    bot.check_sync(2)
    bot.alert_by_mixin(group_name, MIXIN_IDS)
