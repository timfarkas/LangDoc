import collections
import logging
import langchain.schema
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

class Conversation:
    """
    This class implements a Conversation type that is designed to manage a sequence of messages in a conversation history. It provides the following methods:
    - __init__(self, messages=None, logger=None): Initializes the conversation with an optional list of messages and an optional logger. If 'messages' is provided, it should be a list of message objects or another Conversation instance. The 'logger' argument allows for a custom logging.Logger object to be used; if not provided, the default logger is used.
    - __iter__(self): Allows iteration over the messages in the conversation, returning an iterator object.
    - __getitem__(self, key): Enables access to messages by their index, where 'key' is the index of the desired message in the conversation history.
    - __len__(self): Returns the number of messages in the conversation by delegating to the conversation's internal list __len__ method.
    - addMessage(self, messages, messageType=None): Adds one or more messages to the conversation. If 'messages' is a single message object or a string representing the message content, it is appended to the conversation. If 'messages' is a list or another Conversation instance, each message is added individually. The 'messageType' parameter is optional and should be provided as a string if 'messages' is a string, indicating the type of the message ('human', 'AI', or 'System').
    Additional methods include:
    - getLastMessage(self): Retrieves the last message in the conversation, if any, or returns None if the conversation is empty.
    - clear(self): Clears all messages from the conversation, resetting the conversation history to an empty state.
    - getMessagesByType(self, messageType): Retrieves a list of messages of a specific type from the conversation, where 'messageType' is a string indicating the desired message type ('human', 'AI', or 'System').
    """

    conversation = None
    logger = None
    lastNewRequestLen = 0

    ## initializes the conversation with several messages
    def __init__(self, messages = None, logger = None):
        conversation = []
        if messages:
            if checkIfMessages(messages):
                if isinstance(messages, collections.abc.Sequence) or isinstance(messages, Conversation):
                    for msg in messages:
                        conversation.append(msg)
                else:
                    conversation.append(messages)
            else:
                raise TypeError("Conversation(): Error! Provided initial objecs are no messages.")
        self.conversation = conversation
        if logger == None:
            self.logger = logging.getLogger()

    def __iter__(self): return iter(self.conversation)

    def __getitem__(self, key): return self.conversation[key]

    def __len__(self): return self.conversation.__len__()

    ## adds one or several messages to the conversation
    ## either takes a msg object in the second arg
    ## or takes a string and a message type string; types: "human"/"user", "AI"/"bot", "System"
    def addMessage(self, messages, messageType = None):
        logger = self.logger
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
                        logger.warning("Conversation.addMessage() - WARNING: message type provided does not match ai/human/system, skipping message.")
            self.conversation = conversation

    ## returns last message of conversation
    def lastMessage(self, type = None):
        logger = self.logger
        if type == None:
            conversation = self.conversation
            return conversation[-1]
        else:
            logger.warning("Conversation.lastMessage(): TODO - ADD THIS FUNCTIONALITY")

    ### returns an array with the last *span* messages of type, returns all types if type == None
    def lastMessages(self, span, type = None):
        logger = self.logger
        output = []
        if type == None:
            if span == None:
                span = conversation.__len__() 
            conversation = self.conversation
            for i in range(span):
                msg = conversation[-(span-i)]
                output.append(msg) 
            return output
        else:
            if span == None:
                span = conversation.__len__() 
            conversation = self.conversation
            for i in range(span):
                msg = conversation[-(span-i)]
                if isinstance(msg, type):
                    output.append(msg) 
            return output

    ## returns all messages that have been added to the conversation since the last time this method was called
    def newMessages(self, type = None, static = False):
        logger = self.logger
        lenThen = self.lastNewRequestLen
        lenNow = self.conversation.__len__()
        diff = lenNow - lenThen
        if not static:
            self.lastNewRequestLen = lenNow
        return self.lastMessages(diff, type)


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
        logger = self.logger    
        if message:
            logger.info(message)
        for msg in self.conversation:
            logger.info([msg.type, msg.content])

    ## logs conversation
    def log(self):
        logger = self.logger
        for msg in self.conversation:
            logger.info([msg.type, msg.content])

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
        logger.info(flag)
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



                