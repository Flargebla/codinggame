import os
import time
import threading
from operator import itemgetter
from slackclient import SlackClient
from pprint import pprint


class SlackBot:
    def __init__(self, from_discord, to_discord):
        # init client
        self.slack_token = os.environ.get("SLACK_API_TOKEN")
        self.sc = SlackClient(self.slack_token)

        # Store queues
        self.from_discord = from_discord
        self.to_discord = to_discord

        # establish channel dict from api
        _channels = self.sc.api_call("channels.list")
        self.channels = {channel["id"]: channel["name"] for channel in _channels["channels"]}
        
        # initialize user dict from api
        _users = self.sc.api_call("users.list")
        print(_users.keys())
        self.userlist = {user["id"]: user["name"] for user in _users['members']}


    def config(self):
      channels = [v for k,v in self.channels.items()]
      self.to_discord.put({
        'type': 'CONF',
        'channels': channels
      })
    
    def start_listeners(self):
      for k, v in self.channels.items():
        t = threading.Thread(target=self.channel_listener, args=(k,))
        t.start()

    def channel_listener(self, channel):
      last_ts = None
      while(True):
        if (last_ts):
          ret = self.sc.api_call(
            "channels.history",
            channel=channel,
            oldest=last_ts,
          )
        else:
          ret = self.sc.api_call(
            "channels.history",
            channel=channel,
          )
        if(len(ret['messages']) > 0):
          print(ret)
          last_ts = sorted(ret['messages'], key=itemgetter('ts'))[-1]['ts']
          for message in ret['messages']:
            m = {
              'type': 'MSG',
              'sender': self.userlist[message['user']],
              'channel': self.channels[channel],
              'text': message['text']
            }
            self.to_discord.put(m)
        else:
          print("no new messages")
        time.sleep(1)

    def run(self):
      self.send_channels()
      self.start_listeners()