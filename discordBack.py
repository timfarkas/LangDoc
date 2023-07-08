# from OpenAIAPI import initAPI, initPrompt, interact_with_openai, getAssistantMessage, quitLangDoc, check_api_key
from langDocBack import initLangDocAPI, initPatientConvo, processResponse
from collections import defaultdict
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


api_key = None
dev_mode = True
command_word = "!langdoc"

if dev_mode == True:
    command_word = "!dev"
    logging.basicConfig(level=logging.DEBUG)

user_contexts = defaultdict(dict)

async def generateResponse(data) -> str:
        # logger.debug("generateResponse")
        message = data['message'] 
        user_id = data['user_id']
        responses = {"responses": []}
        global user_contexts
        
        user_context = user_contexts[user_id]
        api_key = "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"
        user_context["api_key"] = api_key
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
                assistantMessage = init(data, api_key).content
                logger.debug("LangDoc is now running!")
                user_context["running"] = True
                user_contexts[user_id] = user_context

                responses["responses"].append(assistantMessage)
                responses["responses"].append("You can use '"+command_word+" quit' to quit LangDoc.")
                
                # save text after !LangDoc and send it to openai if long enough
                inputMessage = message[len(command_word+" "):]
                if len(inputMessage) > 3:
                    logger.debug("initial Text is being sent to openai here:" + inputMessage)
                    response = initPatientConvo(inputMessage).content
                    responses["responses"].append(response)
                else:    
                    response = initPatientConvo(None).content
                    responses["responses"].append(response)
                return responses
        else:
            logger.debug("LangDoc is running.")
            if message.startswith(command_word):
                inputMessage = message[len(command_word + " "):]
                if "quit" in inputMessage.lower() and len(inputMessage) < 6:
                    logger.debug("Quitting LangDoc")
                    responses["responses"].append("Thank you for supporting LangDoc, we hope it could help you today!")
                    user_context["running"] = False
                    user_contexts[user_id] = user_context
                    # quitLangDoc()
                    return responses
            inputMessage = message
            logger.debug("input message:"+inputMessage)
            response = processResponse(inputMessage).content
            responses["responses"].append(response)        
            return responses

# inits LangDocAPI and gets first answer
def init(data, api_key):

        user_id = data['user_id']
        global user_contexts
        
        user_context = user_contexts[user_id]
        api_key = user_context['api_key']
        # if bot is not running, initializes the back end, otherwise proceeds as it normally would
        
        if user_context.get("running", False) == False:
            logger.info("Starting LangDoc for User: "+str(user_id))
            user_context["running"] = True 
            message = data['message']
            response = initLangDocAPI(api_key)
            return response   
        else: 
            generateResponse(data)

async def start_bot(loop):
    # Add any necessary startup code here
    pass

async def process_message(data):
    response = await generateResponse(data)
    if not response or not response["responses"]:
        return None
    return response

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot(loop))


#if __name__ == '__main__':
   # app.run(debug=True, port=5000)


