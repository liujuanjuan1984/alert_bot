"""AlertBot module"""
import datetime
import os
import time

from mixinsdk.clients.http_client import HttpClient_AppAuth
from mixinsdk.clients.user_config import AppConfig
from mixinsdk.types.message import pack_message, pack_text_data
from officy import JsonFile
from rumpy import FullNode
from rumpy.utils import timestamp_to_datetime

HTTP_ZEROMESH = "https://mixin-api.zeromesh.net"


class AlertBot:
    """count daily blocks, trxs, pubkeys and sent the result to mixin"""

    def __init__(self, rum_fullnode_port, rum_group_id, mixin_bot_keystore):
        self.rum = FullNode(port=rum_fullnode_port)
        self.rum.group_id = rum_group_id
        self.xin = HttpClient_AppAuth(
            AppConfig.from_payload(mixin_bot_keystore), api_base=HTTP_ZEROMESH
        )
        self.datafile = os.path.join(
            os.path.dirname(__file__), f"count_daily_data_{rum_group_id}.json"
        )

    def update_data(self):
        """count daily blocks, trxs, pubkeys and update the data file"""
        data = JsonFile(self.datafile).read({})
        if not data:
            data = {"block": {}, "trx": {}, "pubkey": {}, "progress_block_id": None}

        bid = self.rum.api.group_info().highest_block_id
        _progress_bid = bid

        while bid and bid != data["progress_block_id"]:
            block = self.rum.api.block(bid)
            block_day = str(timestamp_to_datetime(block["TimeStamp"]))[:10]
            # count daily blocks
            if block_day not in data["block"]:
                data["block"][block_day] = 1
            else:
                data["block"][block_day] += 1
            trxs = block.get("Trxs", [])

            for trx in trxs:
                trx_day = str(timestamp_to_datetime(trx["TimeStamp"]))[:10]
                pubkey = trx["SenderPubkey"]
                # count daily trxs
                if trx_day not in data["trx"]:
                    data["trx"][trx_day] = 1
                else:
                    data["trx"][trx_day] += 1
                # count daily trxs sent by pubkey
                if pubkey not in data["pubkey"]:
                    data["pubkey"][pubkey] = {trx_day: 1}
                elif trx_day not in data["pubkey"][pubkey]:
                    data["pubkey"][pubkey][trx_day] = 1
                else:
                    data["pubkey"][pubkey][trx_day] += 1

            bid = block.get("PrevBlockId")

        data["progress_block_id"] = _progress_bid
        JsonFile(self.datafile).write(data)
        return data

    def _check_data(self, data, data_type):
        """check data and return text and percent"""
        _sum = 0
        today = str(datetime.date.today())
        num = data[data_type].get(today, 0)
        text = f"\n- {today}: {num}\n"
        for i in range(-1, -8, -1):
            key = str(datetime.date.today() + datetime.timedelta(days=i))
            value = data[data_type].get(key, 0)
            text += f"- {key}: {value}\n"
            _sum += value
        _avg = int(_sum / 7)
        _percent = int(100 * num / _avg) if _avg != 0 else 0
        text += (
            f"{data_type} avg: {_avg} today: {num or '???'} {'!'*int(_percent/100) }\n"
        )

        return text

    def check_sync(self, max_try=10):
        """check the group block hightest and start sync"""
        info = self.rum.api.group_info()
        _now_hight = info.highest_height
        _to_hight = info.snapshot_info.get("HighestHeight", 0)
        if _now_hight < _to_hight and max_try > 0:
            self.rum.api.startsync()
            print(
                datetime.datetime.now(),
                f"{max_try} check block highest, now: {_now_hight} to: {_to_hight}",
            )
            time.sleep(5)
            max_try -= 1
            self.check_sync(max_try)
        else:
            self.update_data()

    def check_pubkey(self, data, days=0, num=10):
        "check pubkey that days before today who sent trxs more than num"
        text = ""
        day = str(datetime.date.today() + datetime.timedelta(days=days))
        for pubkey in data["pubkey"]:
            _n = data["pubkey"][pubkey].get(day, 0)
            if _n > num:
                text += f"- {pubkey} {_n}\n"
        if text:
            text = f"\n\npubkeys daily trxs {day}:\n" + text
        return text

    def check_data_and_init_text(self):
        """check data and alert"""
        data = JsonFile(self.datafile).read({})
        block_text = self._check_data(data, "block")
        trx_text = self._check_data(data, "trx")

        _bid = data["progress_block_id"]
        _dt = timestamp_to_datetime(self.rum.api.block(_bid)["TimeStamp"])

        info = self.rum.api.group_info()
        _now_hight = info.highest_height
        _to_hight = info.snapshot_info.get("HighestHeight", 0)

        text = (
            f"<{self.rum.group_id}>\n\n"
            + block_text
            + "\n"
            + trx_text
            + f"\nblock updated to: {_dt}\n<{_bid}>\nhight now {_now_hight} to {_to_hight}"
        )

        for i in [0, -1]:
            text += self.check_pubkey(data, days=i, num=10)
        return text

    def alert_by_mixin(self, group_name, to_mixin_ids, text=None):
        """alert by mixin"""
        text = text or self.check_data_and_init_text()
        text = f"🥂{group_name}🥂\n{text}"
        packed = pack_text_data(text)
        for mid in to_mixin_ids:
            cid = self.xin.get_conversation_id_with_user(mid)
            msg = pack_message(packed, conversation_id=cid)
            self.xin.api.send_messages(msg)
