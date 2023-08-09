# from OpenAIAPI import initAPI, initPrompt, interact_with_openai, getAssistantMessage, quitLangDoc, check_api_key
from langDocBack import initLangDocAPI, initPatientConvo, processResponse
from collections import defaultdict
import asyncio
import logging
from Conversation import Conversation

logging.basicConfig(level=logging.INFO)



api_key = None
dev_mode = True
command_word = "!langdoc"

logger = logging.getLogger("discordBack")
if dev_mode == True:
    command_word = "!dev"
    logger.setLevel(logging.DEBUG)


user_contexts = defaultdict(dict)

def get_dev_mode():
    return dev_mode

async def generateResponse(bot, data) -> str:
        logger.debug("discordBack.generateResponse()")
        message = data['message'] 
        user_id = data['user_id']
        channel = data['channel']
        
        global user_contexts
        user_context = user_contexts[user_id]
        api_key = "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"
        responses = []
        user_context["user_id"] = user_id
        user_context["logger"] = logger
        user_context["api_key"] = api_key
        user_context["responses"] = responses
        
        """
        # API KEY RETRIEVAL LOGIC
        api_key = user_context.get("api_key")
        
        if not api_key:
            if message.startswith("!LangDoc"):
                if message.startswith("!LangDoc setkey "):
                    api_key_candidate = message[len("!LangDoc setkey "):].strip()
                    if check_api_key(api_key_candidate):  # Check if the provided API key is valid
                        api_key = api_key_candidate
                        user_context["api_key"] = api_key
                        user_contexts[user_id] = user_context
                        responses["responses"].append("API key has been set. You can now use !LangDoc to start the conversation.")
                    else:
                        responses["responses"].append("Invalid API key. Please enter a valid API key using the format: !LangDoc setkey YOUR_API_KEY")
                else:
                    responses["responses"].append("Please set your API key using the format: !LangDoc setkey YOUR_API_KEY")
                return responses
            else:
                return responses
        """    
                
        
        # Initialize LangDoc if not running, if a message starts with !LangDoc
        if user_context.get("running", False) == False:
            logger.debug("LangDoc is not running (yet).")
            if message.startswith(command_word):
                assistantMessage = init(data, user_context).content.strip('"')
                logger.debug("LangDoc is now running!")
                user_context["running"] = True
                user_contexts[user_id] = user_context

                user_context["responses"].append(
"""*LangDoc is a symptom checker chat bot, that will walk you through a number of questions about your symptoms to determine most likely diagnoses. 
After a few messages, it will share its first assessment, and give you advice about appropriate next steps. You may choose to continue the conversation to further refine diagnoses.
You can use '"""+command_word+""" quit' to quit LangDoc.*""")
                user_context["responses"].append("""*LangDoc Alpha is very early stage and should only be used for testing purposes. Please do not share medical data that you wish to keep private.*""")                
                user_context["responses"].append(assistantMessage.replace("Anna Johns", "LangDoc"))

                

                # save text after !LangDoc and send it to openai if long enough
                inputMessage = message[len(command_word+" "):]
                if len(inputMessage) > 3:
                    logger.debug("initial Text is being sent to openai here:" + inputMessage+" (discordBack.generateResponse())") 
                    # TYPING
                    user_context = await initPatientConvo(inputMessage, user_context)
                    user_context["responses"].append(user_context["newMsgs"][-1].content)
                else:
                    # TYPING
                    logger.debug("calling initPatientConvo() (discordBack.generateResponse())")
                    user_context = await initPatientConvo(None, user_context)
                    user_context["responses"].append(user_context["newMsgs"][-1].content)
                return user_context["responses"]
        else:
            logger.debug("LangDoc is running.")
            if message.startswith(command_word):
                inputMessage = message[len(command_word + " "):]
                if "quit" in inputMessage.lower() and len(inputMessage) < 6:
                    logger.debug("Quitting LangDoc")
                    user_context["responses"].append("Thank you for supporting LangDoc, we hope it could help you today!")
                    user_context["running"] = False
                    user_contexts[user_id] = user_context
                    # quitLangDoc()
                    return user_context["responses"]
            inputMessage = message
            logger.debug("input message:"+inputMessage)
            # TYPING
            logger.debug("calling langDocBack.processResponse() (discordBack.generateResponse())")
            response = (await processResponse(inputMessage, user_context))["newMsgs"]
            for msg in response:
                user_context["responses"].append(msg.content)
            return user_context["responses"]

# inits LangDocAPI and gets first answer
def init(data, user_context):

        user_id = data['user_id']
        global user_contexts
        user_context = user_contexts[user_id]
        api_key = user_context['api_key']
        # if bot is not running, initializes the back end, otherwise proceeds as it normally would
        
        if user_context.get("running", False) == False:
            logger.info("Starting LangDoc for User: "+str(user_id))
            user_context["running"] = True 
            message = data['message']
            # HERE
            response = initLangDocAPI(user_context)["newMsgs"][-1]
            return response   
        else: 
            generateResponse(data)

async def start_bot():
    # Add any necessary startup code here
    pass

async def process_message(bot, data):
    user_id = data['user_id']
    global user_contexts
    user_context = user_contexts[user_id]
    response = await generateResponse(bot, data)
    if not response or not user_context["responses"]:
        return None
    return response

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot(loop))


#if __name__ == '__main__':
   # app.run(debug=True, port=5000)


