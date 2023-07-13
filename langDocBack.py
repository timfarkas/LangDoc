from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
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
import time, logging
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain import PromptTemplate, OpenAI, LLMChain
from collections import defaultdict
from Conversation import Conversation, isType

chat = ChatOpenAI(temperature=0)

# set this to true before starting langDocBack in CLI to be able to chat with it directly
commandLineMode = False

auditTime = 5
docSysMsg = ""
bayesSysMsg = ""
summarySysMsg = ""

user_contexts = defaultdict(dict)

# TODO make these local
summary = None
docConvo = None


# inits LangDoc taking a user context and returns user_context with user_context["docConvo"] containing doc's first greeting message
def initLangDocAPI(user_context):
    print("Initializing LangDocAPI (langDocBack.initLangDocAPI())")
    initSysMsgs()
    return initDocAgent(user_context)
    summary = None

def initSysMsgs():
    global docSysMsg, bayesSysMsg, summarySysMsg
    # docSysMsg = "You are 'Dr. John', a diligent and smart doctor's assistant AI starting a conversation with a new patient. You are to explore their symptoms step by step, doing a structured, symptom-oriented anamnesis. Keep in mind that you should only ever simulate the responses of the doc and let the patient talk about their symptoms. You only ever ask one question at a time to avoid overwhelming patients. You will get further instructions by a Bayesian Clinical AI on what to ask the patient, which you follow. The next thing the doc says is:"
    docSysMsg = '''You are Anna Johns, a diligent and smart medical assistant starting a conversation with a new patient. 
    You are to explore their symptoms step by step, doing a structured, symptom-oriented anamnesis. 
    There is a doctor AI in the room, who will give you advice on what the most important next questions are. You take his recommendations very seriously, as he has a lot of experience, and you ask one question at a time.
    You only ever ask one question at a time to avoid overwhelming patients, that is, *you only ever ask one questions at a time*. You don't re-ask questions that have already been answered, but you should aim for a thorough and comprehensive picture. You will only end the conversation or mention next diagnostic/medical steps once the doctors tells you that we have gathered enough information.
    The next thing Anna Johns says is:
    '''
    #patientSys = "You are PatientGPT, designed to simulate patients as realistically as possible for med students and doctors to practice their anamnesis skills. Today, you will play Ms. Rodriqguez, a 60 year old smoker with yet undiagnosed morbus meniere. As the medics are asking you questions, make up realistic symptoms, patient history and do a good job of providing a realistic patient anamnesis experience. Keep in mind that you should only ever simulate the responses of the patient and let the students/doctors ask the questions. The next thing the patient says is:"
    bayesSysMsg = '''You are BayesGPT, a Bayesian clinical AI. 
    You will get a summary of the most important facts within a conversation between a doctor and a patient. 
    Your task is to advise the doctor on what the most important next questions are. 
    For that, you should first think in a structured manner, following the rules of Bayesian clinical thinking, and then generate a list of questions for the doctor. 
    Focus on verbal anamnesis and leave out further diagnostics.  
    Remember the rules of Bayesian clinical thinking: 
    Step 1: Use epidemiological data such as demographics, environment, sex to construct quantiative priors on what conditions are most likely a priori. Write down your reasoning. If you realise that you do not have certain epidemiological data yet, note it down so you can put it in the questions list later. 
    Step 2: Use your knowledge of physiology, pathology and pathophysiology (especially symptoms) to determine which kinds of Bayesian evidence would most update your priors on what differential diagnoses are likely, leading to exclusion or promotion of possible diagnoses. Write down your reasoning. 
    Step 3: Generate a short list of the most important questions based on 1 and 2 which is denoted by \n #### List of Questions. You never include questions that have already been asked or where you already have the data. 
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
    print("Initializing LangDoc Agent (langDocBack.initDocAgent())")
    docConvo = Conversation(SystemMessage(content=docSysMsg))
    docGreeting = chat(docConvo)
    print("Doctor:"+docGreeting.content+"(langDocBack.initDocAgent())")
    docConvo.addMessage(docGreeting)
    
    # adds docConvo to local user_context which is being initialized
    user_context["docConvo"] = docConvo

    # initializes user_context entry in global variable user_contexts using user_id as the key 
    # and copying the user context passed from outside
    # user_contexts[user_context["user_id"]] = user_context
    return user_context

# generates the doctor's response to a user's first replies
# takes user context and initialMessages
def initPatientConvo(initialMessages, user_context):
    print("Initializing doc's response to first user replies (langDocBack.initPatientConvo())")

    user_id = user_context["user_id"]
    docConvo = user_context["docConvo"]
    user_context["summary"] = None
    user_context["bayesAdvice"] = None
    user_context["lastAudit"] = None
    user_context["auditAdvice"] = None
    user_context["lastSummary"] = None

    if initialMessages:
        docConvo.addMessage(initialMessages, "human")
        docResponse = chat(docConvo)
        print("Doctor: "+docResponse.content+"(initPatientConvo())")
        docConvo.addMessage(AIMessage(content=docResponse.content))
    else:
        docResponse = AIMessage(content="To get started, could you please provide your age, sex, and nationality?")
        docConvo.addMessage(docResponse)
    user_context["docConvo"] = docConvo
    
    ## generate a first summary
    summary = summarizeData(user_context["docConvo"])
    user_context["summary"] = summary
    return user_context

# takes a user's reply and processes it, returning user_context with user_context["docConvo"] with added reply from doc 
def processResponse(patientMessage, user_context):

    ## appends patient message to convo
    patientMsg = HumanMessage(content=patientMessage)
    user_context["docConvo"].addMessage(patientMsg)
    docConvo = user_context["docConvo"]

    # updates summary using last two messages by doc and patient
    if user_context["summary"]:
        summary = user_context["summary"]
    summary = updateSummary(user_context, 2)
    user_context["summary"] = summary

    # generates advice from bayesian agent to inform next question and advises doc on it
    bayesResponse = planNextQuestion(user_context["summary"])
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
                print("Audit Advice: "+user_context["auditAdvice"])
        else:
            lastAudit = lastAudit + 1
    user_context["lastAudit"] = lastAudit

    ## advises doc
    user_context = adviseDoc(user_context)

    # generates response
    docResponse = chat(user_context["docConvo"])
    print("processResponse() - Doctor: "+docResponse.content)
    docConvo.addMessage(AIMessage(content=docResponse.content))

    user_context["docConvo"] = docConvo
    
    
    return user_context


# asks a summary agent to look at the provided conversation history and an optional previous summaries and outputs an (updated) summary of the conversation as a string
def summarizeData(conversation, summary = None):
    docConvo = conversation.stripSystemMessages()
    global summarySysMsg

    # go through the whole conversation. if there is no summary yet, update summary
    if not summary:
        if docConvo.countMessagesOfType(HumanMessage)>1:
            summarySysMsg = summarySysMsg + "Here is the conversation history:"
            pastConvo=Conversation(SystemMessage(content=summarySysMsg))
            for msg in docConvo:
                #print("DocConvoMessage, type "+str(type(msg))+": "+msg.content)
                pastConvo.addMessage(msg)
                #print("\n")
            command = SystemMessage(content="Now, please generate the summary:")
            pastConvo.addMessage(command)
            summary = chat(pastConvo).content
            print(summary)
            return summary
        else:
            summary = None
            return summary
    else:
        # updates the summary using the whole conversation, not recommended, better to call updateSummary directly and give it only the last few messages
        summary = updateSummary(user_context, user_context["docConvo"].__len__())
        return summary
    
## takes the user_context, looks at the conversation history and returns user_context with the updated summary
#  an updated summary using the previous summary and the previous two messages in convo 
def updateSummary(user_context, span = 3):
    summary = user_context["summary"]
    convo = user_context["docConvo"]
    
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
    
    for i in range(span):
        msg = convo[-(span-i)]
        if not type(msg) == SystemMessage:
            pastConvo.addMessage(msg) 
    
    summarySysMsg3 = "Now, please generate an updated bullet point summary:"
    sysMsg3 = SystemMessage(content=summarySysMsg3)
    pastConvo.addMessage(sysMsg3)
    newSummary = chat(pastConvo)
    summary = newSummary.content
    print("--- SUMMARY OF " + str(user_context["user_id"]) + "---\n"+summary)
    return summary


# initializes a bayesian agent who gets a summary string of the conversation and then plans the next question, 
# outputting a system message instruction

def planNextQuestion(summary):
    if summary and len(summary)>150:
        bayesConvo=Conversation(SystemMessage(content=bayesSysMsg))
        bayesConvo.addMessage(HumanMessage(content=summary))
        reply = chat(bayesConvo).content
        bayesResponse = SystemMessage(content=reply)
        print("--- BAYESIAN ADVICE ---\n"+ bayesResponse.content)
        return bayesResponse
    else:
        return None

### uses advice of bayesian agent and/or audit agent to inform doc of most important next questions/steps
### takes user_context with bayesAdvice and auditAdvice, returns user_context with system messages for the doc
def adviseDoc(user_context):
    docConvo = user_context["docConvo"]
    bayesAdvice = user_context["bayesAdvice"]
    auditAdvice = user_context["auditAdvice"]

    if bayesAdvice and bayesAdvice.content.__contains__('#### List of Questions'):
        questions = bayesAdvice.content.split('#### List of Questions')[1]
        bayesMsg = SystemMessage(content=("The Doctor AI requests you to prioritize asking one of these questions next, if you have not asked them before:"+questions))
        docConvo.addMessage(bayesMsg)
        user_context["docConvo"] = docConvo
    else: 
        bayesMsg = SystemMessage(content=("No advice for now."))
        docConvo.addMessage(bayesMsg)
        user_context["docConvo"] = docConvo

    if auditAdvice:
        docConvo.addMessage("The Doctor AI requests you to also take this advice to the patient into account, especially if it seems urgent: "+auditAdvice, "system")
        #print("The Doctor AI requests you to also take this advice to the patient into account, which may be urgent: "+auditAdvice+"(langDocBack.adviseDoc())")

    return user_context

# takes user context with bayesAdvice and summary and audits it to look for exit criteria
# returns 
def auditConvo(user_context):
    bayesAdvice = user_context["bayesAdvice"]
    summary = user_context["summary"]

    if bayesAdvice and bayesAdvice.content.__contains__('#### List of Questions') and bayesAdvice.content.__contains__("Step 2:"):
        try:
            diagnoses = user_context["bayesAdvice"].content.split('Step 2:')[1]
            diagnoses = diagnoses.split('#### List of Questions')[0]
        except:
            print("ERROR (langDocBack.auditConvo())")

    auditSysMsg =  """
    You are a medical triaging agent tasked with carefully and accurately evaluating whether a patient should call an ambulance, or seek out the emergency room.
    You will receive a medical summary of a patient's symptoms and history along with information on most likely differential diagnoses.
    You will then reason about the case being an emergency. Think step by step.
    Conclude your reasoning with "### ADVICE" followed by the advice that should be shown to the patient. If the case is not an emergency, just give advice about the medical problem that the patient could be experiencing.
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
    
    audit = chat(auditConvo)
    audit = audit.content

    print("--- AUDIT OF " + str(user_context["user_id"]) + "---\n"+audit)
    if audit.__contains__('### ADVICE'):
        print("AUDIT CONTAINS ADVICE; SPLITTING")
        audit = audit.split('### ADVICE')   
        user_context["auditAdvice"] = audit[1]
        print("ADVICE SPLIT: "+user_context["auditAdvice"]+"(auditConvo)")
    else:
        print("NO ADVICE GENERATED (auditConvo)")
        user_context["auditAdvice"] = None

    return user_context


def printToFile(string):
    return
    with open("convo.txt", "a") as f:
        print(string)
        print(string, file=f)


if commandLineMode:
    user_context = {}
    user_context["user_id"] = "TEST_USER"
    
    user_context = initLangDocAPI(user_context)
    #print(user_context["docConvo"].lastMessage())
    
    user_context = initPatientConvo("Hi, I have a medical problem.", user_context)
    print("Patient: Hi, I have a medical problem.")
    #print(user_context["docConvo"].lastMessage())

    #print("TRUE LOOP REACHED")
    while True:
        user_context = processResponse(input("Your response:"), user_context)


