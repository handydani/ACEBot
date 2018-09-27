import os
from slackclient import SlackClient
import re

class acebot:
    def __init__(self):
        slack_token = os.environ["SLACK_API_TOKEN"]
        self.sc=SlackClient(slack_token)
        self.channelList=self.apiCall("conversations.list",exclude_archived=1)
        self.replies = {}
        self.history = {}
        self.channelIDs = {}
        self.aceTunesURI = set()
    def apiCall(self, method, **kwargs):
        return self.sc.api_call(method,**kwargs)
    def updateChannelList(self):
        self.channelList=self.apiCall("conversations.list",exclude_archived=1)
        for channel in self.channelList['channels']:
            self.channelIDs[channel['name']]=channel['id']
        return None
    def getChannelID(self,name):
        if name not in self.channelIDs:
            self.updateChannelList()
        if name in self.channelIDs:
            return self.channelIDs[name]
        else:
            return None
    def getConversationHistory(self,CID):
        if CID not in self.history:
            self.history[CID] =  self.apiCall("conversations.history",channel=CID)
        return self.history[CID]
    def hasReply(self,message):
        return 'reply_count' in message
    def getReply(self,message,CID):
        ts = message['ts']
        if CID not in self.replies:
            self.replies[CID] = {}
        if ts not in self.replies[CID]:
            self.replies[CID][ts] = self.apiCall("conversations.replies",channel=CID,ts=ts)
        return self.replies[CID][ts]
    def getReplies(self,message,CID):
        for reply in self.getReply(message,CID):
            yield reply
    def getURI(self,url):
        if 'spotify' in url:
            return re.search('(?<=track\/)(.+?)(?=\?)',url).group()
        return None
    def getAttachmentLinks(self,message):
        if 'attachments' in message:
            for attachment in message['attachments']:
                yield attachment['original_url']
    def gatherReplyHistory(self,history,CID):
        for message in history[CID]['messages']:
            if self.hasReply(message):
                self.getReply(message,CID)
    def iterateFullHistory(self,CID):
        if CID not in self.history:
            self.getConversationHistory(CID)
        for message in self.history[CID]['messages']:
            if self.hasReply(message):
                yield self.getReplies(message,CID)
            else:
                yield message
    def iterateAttachmentLinks(self,CID):
        for message in self.iterateFullHistory(CID):
            for url in self.getAttachmentLinks(message):
                yield url
    def scrapeACETunes(self):
        CID = self.getChannelID('ace-tunes')
        for url in self.iterateAttachmentLinks(CID):
            self.aceTunesURI.add(self.getURI(url))
        return self.aceTunesURI

