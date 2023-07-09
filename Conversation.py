import collections
from logging import Logger
import langchain.schema
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

class Conversation:
    conversation = None
    
    ## initializes the conversation with several messages
    def __init__(self, messages):
        conversation = []
        if checkIfMessages(messages):
            if isinstance(messages, collections.abc.Sequence):
                for msg in messages:
                    conversation.append(msg)
            else:
                conversation.append(messages)
        else:
            print("Conversation(): Error! Provided initial object are no messages.")
        self.conversation = conversation

    def __iter__(self): return iter(self.conversation)

    def __getitem__(self, key): return self.conversation[key]

    ## adds one or several messages to the conversation
    ## either takes a msg object in the second arg
    ## or takes a string and a message type string; types: "human"/"user", "AI"/"bot", "System"
    def addMessage(self, messages, messageType = None):
        if messageType == None:
            conversation = self.conversation
            if checkIfMessages(messages):
                if isinstance(messages, collections.abc.Sequence):
                    for msg in messages:
                        conversation.append(msg)
                else:
                    conversation.append(messages)
            self.conversation = conversation
        else:
            conversation = self.conversation
            if messageType == "Human" or messageType == "User":
                conversation.append(UserMessage(messages))  
            else:
                if messageType == "Bot" or messageType == "AI":
                    conversation.append(BotMessage(messages))
                else:
                    if messageType == "System":
                        conversation.append(SystemMessage(messages))
            self.conversation = conversation

    ## goes through conversation history and swaps all human messages with AI messages and vice versa    
    def flipRoles(self):
        conversation = self.conversation
        conversation = swapRolesInConversation(conversation)
        self.conversation = conversation

    ## goes through conversation history and swaps all human messages with AI messages and vice versa    
    ## keeps system messages if keepSysMsg is true, otherwise deletes them
    def flipRoles(self, keepSysMsg):
        conversation = self.conversation
        conversation = swapRolesInConversation(conversation, keepSysMsg)
        self.conversation = conversation

    ## prints out conversation
    def print(self):
        for msg in self.conversation:
            print([msg.type, msg.content])

    ## prints out conversation
    def print(self, message):
        print(message)
        for msg in self.conversation:
            print([msg.type, msg.content])

    ## logs conversation
    def log(self):
        for msg in self.conversation:
            Logger.log([msg.type, msg.content])

### takes an object and checks if it is one or several messages
def checkIfMessages(messages):
        if isinstance(messages, collections.abc.Sequence):
            for msg in messages:
                if not (isinstance(msg, langchain.schema.AIMessage) or isinstance(msg, langchain.schema.HumanMessage) or isinstance(msg, langchain.schema.SystemMessage)):
                    return False
                else:
                    return True
        else:
            if isinstance(messages, langchain.schema.AIMessage) or isinstance(messages, langchain.schema.HumanMessage) or isinstance(messages, langchain.schema.SystemMessage):
                return True
            else:
                print("THIS SHOULD NOT OCCUR")
                return False


## takes conversation history and swaps all humans with AIs and vice versa    
def swapRolesInConversation(conversation):
    output = []
    for msg in conversation:
        if isinstance(msg, SystemMessage):
            output.append(msg)
        if isinstance(msg, AIMessage):
            output.append(UserMessage(msg.content))
        if isinstance(msg, HumanMessage):
            output.append(BotMessage(msg.content))
    return output


## takes conversation history and swaps all humans with AIs and vice versa   
## deletes sysmsgs if second parameter is False
def swapRolesInConversation(conversation, keepSysMsg):
    output = []
    for msg in conversation:
        if isinstance(msg, langchain.schema.SystemMessage) and keepSysMsg:
            output.append(msg)
        if isinstance(msg, langchain.schema.AIMessage):
            output.append(UserMessage(msg.content))
        if isinstance(msg, langchain.schema.HumanMessage):
            output.append(BotMessage(msg.content))
    return output



def BotMessage(text):
    return AIMessage(content=text)

def UserMessage(text):
    return HumanMessage(content=text)

def SystemMessage(text):
    return langchain.schema.SystemMessage(content=text)



                