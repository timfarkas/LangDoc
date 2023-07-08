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

chat = ChatOpenAI(temperature=0)

docSysMsg = ""
bayesSysMsg = ""
summarySysMsg = ""

# TODO make these local
summary = None
docConvo = None


# inits LangDoc and returns first doc greeting message
def initLangDocAPI(api_key):
    print("Initializing LangDocAPI")
    initSysMsgs()
    return initDocAgent()
    summary = None

def initSysMsgs():
    global docSysMsg, bayesSysMsg, summarySysMsg
    # docSysMsg = "You are 'Dr. John', a diligent and smart doctor's assistant AI starting a conversation with a new patient. You are to explore their symptoms step by step, doing a structured, symptom-oriented anamnesis. Keep in mind that you should only ever simulate the responses of the doc and let the patient talk about their symptoms. You only ever ask one question at a time to avoid overwhelming patients. You will get further instructions by a Bayesian Clinical AI on what to ask the patient, which you follow. The next thing the doc says is:"
    docSysMsg = '''You are Anna Johns, a diligent and smart medical assistant starting a conversation with a new patient. 
    You are to explore their symptoms step by step, doing a structured, symptom-oriented anamnesis. 
    There is a doctor AI in the room, who will give you advice on what the most important next questions are. You take his recommendations very seriously, as he has a lot of experience, and you ask one question at a time.
    You only ever ask one question at a time to avoid overwhelming patients, that is, *you only ever ask one questions at a time*. Obviously, you don't reask questions that have already been answered, but you should aim for a thorough and comprehensive picture. You will only end the conversation or mention next diagnostic/medical steps once the doctors tells you that we have gathered enough information.
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
    You use medical terminology and you may adjust and restructure the summary as needed. However, you don't add any assessments or possible diagnoses, unless explicitly mentioned in the dialogue, as that is the doctor's job.
    For example:
    - Symptoms:
        - Urination: Hematuria, Pollakiuria, Alguria
            - Abnormal urination known for half a year, blood is new
    If specific data have not been mentioned yet, you can leave their fields empty or mark them as missing.
    If the conversation contains no data on the patient, be sure to write "No information yet".'''

# inits doc agent with docSysMsg, generates and returns doc's first greeting message 
def initDocAgent():
    print("Initializing LangDoc Agent")
    global docConvo
    docConvo = [SystemMessage(content=docSysMsg)]
    docGreeting = chat(docConvo)
    docConvo.append(docGreeting)
    return docGreeting

# generates the doctor's response to user's first replies
def initPatientConvo(patientMessage):
    global docConvo, summary
    if patientMessage:
        patientMsg = HumanMessage(content=patientMessage)
        docConvo.append(patientMsg)
        docResponse = chat(docConvo)
        docConvo.append(AIMessage(content=docResponse.content))
    else:
        docResponse = AIMessage(content="To get started, could you please provide your age, sex, and nationality?")
        docConvo.append(docResponse)
    
    ## generate a first summary
    summary = summarizeData()
    return docResponse

# takes a user's reply and processes it, generating an answer by the doc
def processResponse(patientMessage):
    global docConvo, summary
    patientMsg = HumanMessage(content=patientMessage)
    docConvo.append(patientMsg)

    # updates summary using last two messages by doc and patient
    summary = updateSummary([docConvo[-2],patientMsg])
    # generates advice from bayesian agent to inform next question and advises doc on it
    bayesResponse = planNextQuestion(summary)
    adviseDoc(bayesResponse)
    # generates response
    docResponse = chat(docConvo)
    docConvo.append(AIMessage(content=docResponse.content))

    return docResponse


# asks a summary agent to look at the conversation history and previous summaries and outputs an updated summary of the conversation
def summarizeData():
    global docConvo
    global summary
    global summarySysMsg
    # go through the whole conversation. if there is no summary yet, update summary
    if not summary:
        if docConvo.__len__()>3:
            print("Init Summary")
            summarySysMsg = summarySysMsg + "Here is the conversation history:"
            pastConvo=[SystemMessage(content=summarySysMsg)]   
            for msg in docConvo:
                #print("DocConvoMessage, type "+str(type(msg))+": "+msg.content)
                if not type(msg) == SystemMessage:
                    pastConvo.append(msg)
                print("\n")
            command = SystemMessage(content="Now, please generate the summary:")
            pastConvo.append(command)
            summary = chat(pastConvo).content
            print(summary)
        else:
            summary = "No information yet."
    else:
        # updates the summary using the whole conversation, not recommended, better to call updateSummary directly and give it only the last few messages
        updateSummary(docConvo)
    return summary

## takes the conversation history and outputs an updated summary using the previous summary and the messages in convo 
def updateSummary(convo):
    global summarySysMsg
    summarySysMsg = summarySysMsg + "\nSummary of the conversation so far:"
    pastConvo=[SystemMessage(content=summarySysMsg)]
    global summary
    currentSummary = AIMessage(content=summary) 
    pastConvo.append(currentSummary)

    summarySysMsg2 = "Conversation history since the last summary:"
    sysMsg2 = SystemMessage(content=summarySysMsg2)
    pastConvo.append(sysMsg2)
    for msg in convo:
        if not type(msg) == SystemMessage:
            pastConvo.append(msg) 
    
    summarySysMsg3 = "Now, please generate an updated bullet point summary:"
    sysMsg3 = SystemMessage(content=summarySysMsg3)
    pastConvo.append(sysMsg3)

    newSummary = chat(pastConvo)
    summary = newSummary.content
    print(summary)
    return newSummary.content


# initializes a bayesian agent who gets a summary string of the conversation and then plans the next question, 
# outputting a system message instruction

def planNextQuestion(summary):
    global docConvo    
    bayesConvo=[SystemMessage(content=bayesSysMsg)]
    bayesConvo.append(HumanMessage(content=summary))
    reply = chat(bayesConvo).content
    bayesResponse = SystemMessage(content=reply)
    print(bayesResponse.content)
    return bayesResponse.content

### uses advice of bayesian agent to inform doc of most important next questions
def adviseDoc(bayesAdvice):
    global docConvo
    if bayesAdvice.__contains__('#### List of Questions'):
        questions = bayesAdvice.split('#### List of Questions')[1]
        bayesMsg = SystemMessage(content=("The Doctor AI requests you to prioritize asking these questions next, if you have not asked them before:"+questions))
        docConvo.append(bayesMsg)
    else: 
        print("No advice for now.")

def printToFile(string):
    return
    with open("convo.txt", "a") as f:
        print(string)
        print(string, file=f)



#docAnswer = initLangDocAPI(None)
#print(docAnswer)
#docAnswer = initPatientConvo(None)
#print(docAnswer)

#while True:
 #  print(processResponse(input("Your response:")))



