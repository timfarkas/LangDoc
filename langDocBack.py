from multiprocessing import log_to_stderr
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import logging, traceback
from collections import defaultdict
from Conversation import Conversation, isType

chat3 = ChatOpenAI(temperature=0)
chat4 = ChatOpenAI(temperature=0, model_name="gpt-4")
dev_mode = False

# set this to true before starting langDocBack in CLI to be able to chat with it directly
commandLineMode = False

auditTime = 5
docSysMsg = ""
bayesSysMsg = ""
summarySysMsg = ""

user_contexts = defaultdict(dict)
summary = None
docConvo = None

#logger = multiprocessing.log_to_stderr() 
#logger.getL(logging.INFO)
logging.basicConfig(level=logging.INFO)

# inits LangDoc taking a user context and returns user_context with user_context["docConvo"] containing doc's first greeting message
def initLangDocAPI(user_context, logger = None):
    try:
        logger = user_context["logger"]
    except KeyError as e:
        if logger == None: 
            logger = logging.getLogger("langDocBack")
            user_context["logger"] = logger
        else:
            user_context["logger"] = logger
    if dev_mode:
        logger.setLevel(logging.DEBUG)      
    logger.debug("Initializing LangDocAPI (langDocBack.initLangDocAPI())")
    initSysMsgs()

    
    return initDocAgent(user_context)

def initSysMsgs():
    global docSysMsg, bayesSysMsg, summarySysMsg
    # docSysMsg = "You are 'Dr. John', a diligent and smart doctor's assistant AI starting a conversation with a new patient. You are to explore their symptoms step by step, doing a structured, symptom-oriented anamnesis. Keep in mind that you should only ever simulate the responses of the doc and let the patient talk about their symptoms. You only ever ask one question at a time to avoid overwhelming patients. You will get further instructions by a Bayesian Clinical AI on what to ask the patient, which you follow. The next thing the doc says is:"
    docSysMsg = '''You are Anna Johns, a diligent and smart medical assistant starting a conversation with a new patient. 
    You are to explore their symptoms step by step, doing a structured, symptom-oriented anamnesis, in a professional, empathetic way, asking open-ended questions and taking patients seriously.
    There is a doctor AI in the room, who will give you advice on what the most important next questions are. You take his recommendations very seriously, as he has a lot of experience, and you ask one question at a time.
    You only ever ask one question at a time to avoid overwhelming patients, that is, *you only ever ask one questions at a time*. You don't re-ask questions that have already been answered, but you should aim for a thorough and comprehensive picture, which means that you sometimes ask follow-up questions to dig deeper. You will only end the conversation or mention next diagnostic/medical steps once the doctors tells you that we have gathered enough information.
    The next thing Anna Johns says to the new patient is:
    '''
    #patientSys = "You are PatientGPT, designed to simulate patients as realistically as possible for med students and doctors to practice their anamnesis skills. Today, you will play Ms. Rodriqguez, a 60 year old smoker with yet undiagnosed morbus meniere. As the medics are asking you questions, make up realistic symptoms, patient history and do a good job of providing a realistic patient anamnesis experience. Keep in mind that you should only ever simulate the responses of the patient and let the students/doctors ask the questions. The next thing the patient says is:"
    bayesSysMsg = '''You are BayesGPT, a Bayesian clinical AI. 
    You will get a summary of the most important facts within a conversation between a doctor and a patient. 
    Your task is to advise the doctor on what the most important next questions are. 
    For that, you should first think in a structured manner, following the rules of Bayesian clinical thinking, and then generate a list of questions for the doctor. 
    Focus on verbal anamnesis and leave out further diagnostics.  
    Remember the rules of Bayesian clinical thinking: 
    Step 1: Use epidemiological data such as demographics, environment, sex to construct priors on what conditions are most likely a priori, giving percentages. Write down your reasoning and think step by step, citing epidemiological empirical data. If you realise that you do not have certain epidemiological data yet, note it down so you can put it in the questions list later. 
    Step 2: Use your clinical knowledge and knowledge of physiology, pathology, pathophysiology (especially symptoms) to determine which kinds of Bayesian evidence would most update your priors on what differential diagnoses are likely, leading to exclusion or promotion of possible diagnoses. Reference predictive values to arrive at quantitative updates. Write down your reasoning. 
    Step 3: List the differential diagnoses ordered by their likelihood.  
    Step 4: Generate a short list of the most important questions based on 1 and 2 which is denoted by \n #### List of Questions. You never include questions that have already been asked or where you already have the data. 
    Let's work out Step 1,2, and 3 in a step by step way to be sure we have the right answer. Don't forget to always output a \n '#### List of Questions' at the end so that the system will properly parse them, and don't include questions that have already been asked.   
    '''
    summarySysMsg = '''You are a clinical assistant AI tasked with helping doctors with patient anamnesis.
    Your job is to go through the past conversation and output a concise, comprehensive, and formatted overview of their demographics, symptoms, and all relevant data in a bullet point format, ordered by relevance and categorized in a meaningful way. Make sure that you are not missing anything! 
    You use appropriate medical terminology and you may adjust and restructure the summary as needed. However, you don't add any assessments or possible diagnoses, unless explicitly mentioned in the dialogue, as that is the doctor's job.
    For example:
    - Symptoms:
        - Urination: Hematuria, Pollakisuria, Alguria
            - Abnormal urination known for half a year, blood is new
    If specific data have not been mentioned yet, you can leave their fields empty or mark them as missing.If symptoms are not being experienced (negative experience), you add that too.
    If the conversation contains no data on the patient yet, or if it is very short (<4 messages), write "Not enough data yet".'''

# inits doc agent with docSysMsg, generates and returns user_context with user_context["docConvo"] with doc's first greeting message 
def initDocAgent(user_context):
    logger = user_context["logger"]
    logger.debug("Initializing LangDoc Agent (langDocBack.initDocAgent())")
    docConvo = Conversation(SystemMessage(content=docSysMsg))
    docGreeting = chat3(docConvo)
    logger.info("Doctor:"+docGreeting.content+"(langDocBack.initDocAgent())")
    docConvo.addMessage(docGreeting)
    
    # adds docConvo to local user_context which is being initialized
    user_context["docConvo"] = docConvo

    # initializes user_context entry in global variable user_contexts using user_id as the key 
    # and copying the user context passed from outside
    # user_contexts[user_context["user_id"]] = user_context
    user_context["newMsgs"] = user_context["docConvo"].newMessages(type = AIMessage)

    return user_context

# generates the doctor's response to a user's first replies
# takes user context and initialMessages
def initPatientConvo(initialMessages, user_context):
    logger = user_context["logger"]
    logger.debug("langDocBack.initPatientConvo()")

    user_id = user_context["user_id"]
    docConvo = user_context["docConvo"]
    user_context["summary"] = None
    user_context["bayesAdvice"] = None
    user_context["lastAudit"] = None
    user_context["auditAdvice"] = None
    user_context["lastSummary"] = None

    if initialMessages:
        docConvo.addMessage(initialMessages, "human")
        logger.info("Initializing doc's response to first user replies (langDocBack.initPatientConvo())")
        docResponse = chat3(docConvo)
        logger.info("Doctor: "+docResponse.content+"(initPatientConvo())")
        docConvo.addMessage(AIMessage(content=docResponse.content))
        ## generate a first summary
        summary = summarizeData(user_context)
        user_context["summary"] = summary
    else:
        docResponse = AIMessage(content="To get started, could you please provide your age, sex, ethnicity and country of residence?")
        docConvo.addMessage(docResponse)
        user_context["summary"] = "No information yet."
    user_context["docConvo"] = docConvo
    user_context["newMsgs"] = user_context["docConvo"].newMessages()
    
    return user_context

# takes a user's reply and processes it, returning user_context with user_context["docConvo"] with added reply from doc 
def processResponse(patientMessage, user_context):
    logger = user_context["logger"]
    logger.debug("langDocBack.processResponse()")
    ## appends patient message to convo
    patientMsg = HumanMessage(content=patientMessage)
    user_context["docConvo"].addMessage(patientMsg)
    docConvo = user_context["docConvo"]

    # updates summary using last four messages by doc and patient
    if user_context["summary"]:
        summary = user_context["summary"]
    summary = updateSummary(user_context, 4)
    user_context["summary"] = summary

    # generates advice from bayesian agent to inform next question and advises doc on it
    bayesResponse = planNextQuestion(user_context)
    user_context["bayesAdvice"] = bayesResponse
    

    # audit logic
    global auditTime
    lastAudit = user_context["lastAudit"]
    if lastAudit == None:
        lastAudit = 0
    else:
        if lastAudit > auditTime:
            lastAudit = 1
            user_context = auditConvo(user_context)
            if user_context["auditAdvice"]:
                logger.info("Audit Advice: "+user_context["auditAdvice"])
                user_context = passAuditAdvice(user_context)
        else:
            lastAudit = lastAudit + 1
    user_context["lastAudit"] = lastAudit

    ## advises doc
    user_context = adviseDoc(user_context)

    # generates response
    docResponse = chat3(user_context["docConvo"])
    logger.info("processResponse() - Doctor: "+docResponse.content)
    docConvo.addMessage(AIMessage(content=docResponse.content))

    user_context["newMsgs"] = docConvo.newMessages(type = AIMessage)
    user_context["docConvo"] = docConvo

    return user_context

# propagates audit advice to the discord frontend
def passAuditAdvice(user_context):
    logger = user_context["logger"]
    logger.debug("langDocBack.passAuditAdvice()")
    user_context["docConvo"].addMessage("*Analyzing our conversation so far, here's my assessment for now:*", "ai")
    user_context["docConvo"].addMessage("**"+user_context["auditAdvice"]+"**", "ai")
    user_context["docConvo"].addMessage("*You may continue to refine this assessment by continuing to answer further questions.*", "ai")
    return user_context

# asks a summary agent to look at the conversation history in the user_context and an optional previous summaries and outputs an (updated) summary of the conversation as a string
def summarizeData(user_context):
    logger = user_context["logger"]
    logger.debug("langDocBack.summarizeData()")
    updateSummary(user_context)

    """
    docConvo = conversation.stripSystemMessages()
    global summarySysMsg

    # go through the whole conversation. if there is no summary yet, update summary
    if not summary:
        if docConvo.countMessagesOfType(HumanMessage)>1:
            summarySysMsg = summarySysMsg + "Here is the conversation history:"
            pastConvo=Conversation(SystemMessage(content=summarySysMsg))
            for msg in docConvo:
                #logger.info("DocConvoMessage, type "+str(type(msg))+": "+msg.content)
                pastConvo.addMessage(msg)
                #logger.info("\n")
            command = SystemMessage(content="Now, please generate the summary:")
            pastConvo.addMessage(command)
            summary = chat(pastConvo).content
            logger.info(summary)
            return summary
        else:
            summary = None
            return summary
    else:
        # updates the summary using the whole conversation, not recommended, better to call updateSummary directly and give it only the last few messages
        summary = updateSummary(user_context, user_context["docConvo"].__len__())
        return summary
    """
## takes the user_context, looks at the conversation history and returns user_context with the updated summary
#  an updated summary using the previous summary and the previous two messages in convo 
## if span = None, it looks at the whole conversation
def updateSummary(user_context, span = None):
    logger = user_context["logger"]
    logger.debug("langDocBack.updateSummary()")
    try:
        summary = user_context["summary"]
    except KeyError as e:
        logger.warning("Found no summary in user context, creating initial one.")    
        summaryInit = True
        user_context["summary"] = None
        summary = None

    convo = user_context["docConvo"].stripSystemMessages()
    if span == None:
        span = convo.__len__()
    

    global summarySysMsg
    summarySysMsg = summarySysMsg + "\nSummary of the conversation so far:"
    
    pastConvo = Conversation(SystemMessage(content=summarySysMsg))
    
    if summary:
        currentSummary = AIMessage(content=summary) 
        pastConvo.addMessage(currentSummary)
    else:
        pastConvo.addMessage("No information yet.","bot")

    summarySysMsg2 = "Conversation history since the last summary:"
    sysMsg2 = SystemMessage(content=summarySysMsg2)
    pastConvo.addMessage(sysMsg2)
    
    try:
        for i in range(span):
            #print("Message "+str(i)+" / "+str(-(span-i)))
            #print(str(convo[-(span-i)])) 
            msg = convo[-(span-i)]
            if not type(msg) == SystemMessage:
                pastConvo.addMessage(msg) 
    except:
        logger.error("Error while iterating through conversation, did you provide a range that is shorter than the conversation? langDocBack.updateSummary()")
        logger.error(traceback.format_exc())

    summarySysMsg3 = "Now, please generate an updated bullet point summary:"
    sysMsg3 = SystemMessage(content=summarySysMsg3)
    pastConvo.addMessage(sysMsg3)
    newSummary = chat3(pastConvo)
    if not summary or len(newSummary.content)>len(summary)/2:
        summary = newSummary.content
    logger.info("--- SUMMARY OF " + str(user_context["user_id"]) + "---\n"+summary)
    return summary


# initializes a bayesian agent who gets a summary string of the conversation and then plans the next question, 
# outputting a system message instruction

def planNextQuestion(user_context): 
    logger = user_context["logger"]
    logger.debug("langDocBack.planNextQuestion()")
    summary = user_context["summary"]
    if summary and (len(summary)>200 or user_context["docConvo"].__len__()>8):
        bayesConvo=Conversation(SystemMessage(content=bayesSysMsg))
        bayesConvo.addMessage(HumanMessage(content=summary))
        reply = chat4(bayesConvo).content
        bayesResponse = SystemMessage(content=reply)
        logger.info("--- BAYESIAN ADVICE ---\n"+ bayesResponse.content)
        return bayesResponse
    else:
        return None

### uses advice of bayesian agent and/or audit agent to inform doc of most important next questions/steps
### takes user_context with bayesAdvice and auditAdvice, returns user_context with system messages for the doc
def adviseDoc(user_context):
    logger = user_context["logger"]
    logger.debug("langDocBack.adviseDoc()")
    docConvo = user_context["docConvo"]
    bayesAdvice = user_context["bayesAdvice"]
    auditAdvice = user_context["auditAdvice"]

    if bayesAdvice and bayesAdvice.content.__contains__('#### List of Questions'):
        questions = bayesAdvice.content.split('#### List of Questions')[1]
        bayesMsg = SystemMessage(content=("The Doctor AI requests you to prioritize asking one of these questions next, if you have not asked them before:"+questions))
        ## TODO add logic so that this message is not only appended but that the old bayes msg gets deleted 
        docConvo.addMessage(bayesMsg)
        user_context["docConvo"] = docConvo
    else: 
        bayesMsg = SystemMessage(content=("No advice for now."))
        docConvo.addMessage(bayesMsg)
        user_context["docConvo"] = docConvo

    """
    if auditAdvice:
        docConvo.addMessage("The Doctor AI requests you to also take this advice to the patient into account, especially if it constitutes an emergency: '"+auditAdvice+"'\n If it is not an emergency, you should continue the conversation.", "system")
        #logger.info("The Doctor AI requests you to also take this advice to the patient into account, which may be urgent: "+auditAdvice+"(langDocBack.adviseDoc())")
    """
    return user_context

# takes user context with bayesAdvice and summary and audits it to look for exit criteria
# returns 
def auditConvo(user_context):
    logger = user_context["logger"]
    logger.debug("langDocBack.auditConvo()")
    bayesAdvice = user_context["bayesAdvice"]
    summary = user_context["summary"]
    diagnoses = None
    if bayesAdvice and (bayesAdvice.content.__contains__('#### List of Questions') or bayesAdvice.content.__contains__('Step 4: List of Questions')) and bayesAdvice.content.__contains__("Step 2:"):
        try:
            diagnoses = user_context["bayesAdvice"].content.split('Step 3:')[1]
            if bayesAdvice.content.__contains__('#### List of Questions'):
                diagnoses = diagnoses.split('#### List of Questions')[0]  
            else:
                diagnoses = diagnoses.split('Step 4: List of Questions')[0]
        except:
            logger.info("ERROR (langDocBack.auditConvo())")

    auditSysMsg =  """
    You are a medical triaging agent tasked with carefully and accurately evaluating whether a patient should call an ambulance, or seek out the emergency room.
    You will receive a medical summary of a patient's symptoms and history along with information on most likely differential diagnoses.
    You will then reason about the case being an emergency. Think step by step.
    Conclude your reasoning with "### ADVICE" followed by the advice that should be shown to the patient, where you include the information on which conditions are likely. If the case is not an emergency, just give advice about the medical problem that the patient could be experiencing.
    """
    
    auditConvo = Conversation(SystemMessage(content=auditSysMsg))
    auditConvo.addMessage(AIMessage(content="Sure, could you please provide me with the medical summary?"))
    
    if summary:
        auditConvo.addMessage(HumanMessage(content="Of course, here it is:\n"+summary)) 
    else:
        auditConvo.addMessage("Sorry, I don't have a summary yet.","human")

    auditConvo.addMessage("Thanks. Now, could you provide information on the most likely diagnoses?","ai")
    
    if diagnoses:
        auditConvo.addMessage(HumanMessage(content="Sure, here are the most likely diagnoses as generated by a Bayesian clinical agent:\n"+diagnoses)) 
    else:
        auditConvo.addMessage("Sorry, I don't have the diagnoses yet.","human")
    

    auditConvo.addMessage("""Now, please reason about what kind of help the patient should seek, thinking step by step. Be sure to conclude your reasoning with "### ADVICE" followed by the advice that should be shown to the patient.""","system")
    
    audit = chat4(auditConvo)
    audit = audit.content

    logger.info("--- AUDIT OF " + str(user_context["user_id"]) + "---\n"+audit)
    if audit.__contains__('### ADVICE'):
        logger.info("AUDIT CONTAINS ADVICE; SPLITTING")
        audit = audit.split('### ADVICE')   
        user_context["auditAdvice"] = audit[1]
        logger.info("ADVICE SPLIT: "+user_context["auditAdvice"]+"(auditConvo)")
    else:
        logger.info("NO ADVICE GENERATED (auditConvo)")
        user_context["auditAdvice"] = None

    return user_context


def printToFile(string):
    return
    with open("convo.txt", "a") as f:
        logger.info(string)
        logger.info(string, file=f)


if commandLineMode:
    user_context = {}
    user_context["user_id"] = "TEST_USER"
    
    user_context = initLangDocAPI(user_context)
    #logger.info(user_context["docConvo"].lastMessage())
    
    user_context = initPatientConvo("Hi, I have a medical problem.", user_context)
    logger.info("Patient: Hi, I have a medical problem.")
    #logger.info(user_context["docConvo"].lastMessage())

    #logger.info("TRUE LOOP REACHED")
    while True:
        user_context = processResponse(input("Your response:"), user_context)


