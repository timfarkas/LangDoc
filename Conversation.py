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
    def __init__(self, messages = None):
        conversation = []
        if messages:
            if checkIfMessages(messages):
                if isinstance(messages, collections.abc.Sequence) or isinstance(messages, Conversation):
                    for msg in messages:
                        conversation.append(msg)
                else:
                    conversation.append(messages)
            else:
                print("Conversation(): Error! Provided initial object are no messages.")
        self.conversation = conversation

    def __iter__(self): return iter(self.conversation)

    def __getitem__(self, key): return self.conversation[key]

    def __len__ (self): return self.conversation.__len__()

    ## adds one or several messages to the conversation
    ## either takes a msg object in the second arg
    ## or takes a string and a message type string; types: "human"/"user", "AI"/"bot", "System"
    def addMessage(self, messages, messageType = None):
        if messageType == None:
            conversation = self.conversation
            if checkIfMessages(messages):
                if isinstance(messages, collections.abc.Sequence) or isinstance(messages, Conversation):
                    for msg in messages:
                        conversation.append(msg)
                else:
                    conversation.append(messages)
            else:
                raise TypeError("Provided argument does not seem to be of Message type. If you are trying to pass a string, don't forget to pass a messageType argument.")  
            self.conversation = conversation
        else:
            messageType = messageType.lower()
            conversation = self.conversation
            if messageType == "human" or messageType == "user":
                conversation.append(UserMessage(messages))  
            else:
                if messageType == "bot" or messageType == "ai":
                    conversation.append(BotMessage(messages))
                else:
                    if messageType == "system":
                        conversation.append(SystemMessage(messages))
                    else:
                        print("Conversation.addMessage() - WARNING: message type provided does not match ai/human/system, skipping message.")
            self.conversation = conversation

    ## returns last message of conversation
    def lastMessage(self, type = None):
        if type == None:
            conversation = self.conversation
            return conversation[-1]
        else:
            print("Conversation.lastMessage(): TODO - ADD THIS FUNCTIONALITY")

    ## counts messages of type provided in conversation
    def countMessagesOfType(self, type):
        return countMessagesOfTypeInConvo(self.conversation, type)

    ## returns conversation without system messages
    def stripSystemMessages(self):
        conversation = self.conversation
        output = Conversation()
        for msg in conversation:
            if not isinstance(msg, langchain.schema.SystemMessage):
                output.addMessage(msg)
        return output

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
    def print(self, message = None):
        if message:
            print(message)
        for msg in self.conversation:
            print([msg.type, msg.content])

    ## logs conversation
    def log(self):
        for msg in self.conversation:
            Logger.log([msg.type, msg.content])

### takes an object and checks if it is one or several messages
def checkIfMessages(messages):
    flag = None
    if isinstance(messages, collections.abc.Sequence) or isinstance(messages, Conversation):
        for msg in messages:
            if not (isinstance(msg, langchain.schema.AIMessage) or isinstance(msg, langchain.schema.HumanMessage) or isinstance(msg, langchain.schema.SystemMessage)):
                flag = "Conversation.checkIfMessages(): WARNING - Provided sequence contains non-message type:" + str(msg)
            else:
                return True
    else:
        if isinstance(messages, langchain.schema.AIMessage) or isinstance(messages, langchain.schema.HumanMessage) or isinstance(messages, langchain.schema.SystemMessage):
            return True
        else:
            flag = "Conversation.checkIfMessages(): WARNING - Provided message is non-message type:" + str(messages)
    if flag:
        print(flag)
        return False

## counts messages of type in provided conversation, returns None if it is given non-messages
def countMessagesOfTypeInConvo(conversation, type):
    if checkIfMessages(conversation):
        i = 0
        for msg in conversation:
            if isinstance(msg, type):
                i = i+1
        return i
    else:
        return None

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

## takes a message and checks if it is of the provided type (taking in a string specification of the type)
def isType(msg, messageType):
    if messageType == "human" or messageType == "user":
        if isinstance(msg, langchain.schema.HumanMessage):
            return True
    else:
        if messageType == "bot" or messageType == "ai":
            if isinstance(msg, AIMessage):
                return True
        else:
            if messageType == "system":
                if isinstance(msg, langchain.schema.SystemMessage):
                    return True
    return False

def BotMessage(text):
    return AIMessage(content=text)

def UserMessage(text):
    return HumanMessage(content=text)

def SystemMessage(text):
    return langchain.schema.SystemMessage(content=text)



                