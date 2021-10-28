import requests
import json
class DingTalk_Base:
    def __init__(self):
        self.__headers = {'Content-Type': 'application/json;charset=utf-8'}
        self.url = ''
    def send_msg(self,text):
        json_text = {
            "msgtype": "text",
            "text": {
                "content": '自定义消息:'+text
            },
            "at": {
                "atMobiles": [
                    "15395835100"
                ],
                "isAtAll": False
            }
        }
        return requests.post(self.url, json.dumps(json_text), headers=self.__headers).content
class DingTalk_Disaster(DingTalk_Base):
    def __init__(self):
        super().__init__()
        # 填写机器人的url
        self.url = 'https://oapi.dingtalk.com/robot/send?access_token=2598062b6e0467a7b25fc383f6b81810c5189bd74dcd6c27e5fb9fac47753b32'
# if __name__ == '__main__':
#     ding = DingTalk_Disaster()
#     ding.send_msg('22')