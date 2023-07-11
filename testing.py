import discordBack, discordFront, langDocBack
from Conversation import Conversation, BotMessage, UserMessage, SystemMessage
from collections import defaultdict
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage
)

chat = ChatOpenAI(temperature=0)
patientSimulations = defaultdict(dict)

## initializes a patient simulation with id, initial inputMessages (e.g. initial questions from doc) and patient specification 
## defaults to glaucoma patient if no patient specification is passed
## initializes patientSimulations[id]["patientConvo"] with all initial messages and adds first patient response
async def initPatientSimulation(id, inputMessages, patientSpecification):
    print("Initializing Patient Simulation with ID "+ str(id)+ "(testing.initPatientSimulation())")
    global patientSimulations
    patientSimulation = patientSimulations[id]
    patientSimulation["patientConvo"] = None
    #patientSimulation["patientConvo"] = None

    if not patientSpecification:
        patientSpecification = "Ms. Rodriqguez, a 60 year old smoker with yet undiagnosed glaucoma."
    
    patientSimulation["patientSpecification"] = patientSpecification

    patientSys = """
    You are PatientGPT, designed to simulate patients as realistically as possible for med students and doctors to practice their anamnesis skills.
    Today, you will play the following patient:"""+ patientSimulation["patientSpecification"] +""".
    As the medics are asking you questions, make up realistic symptoms, patient history and do a good job of providing a realistic patient anamnesis experience.
    Keep in mind that you should only ever simulate the responses of the patient and let the students/doctors ask the questions. 
    The next thing the patient says is:
    """

    patientConvo = Conversation(SystemMessage(patientSys))
    
    for msg in inputMessages:
        patientConvo.addMessage(HumanMessage(content=msg.content))
    
    patientAnswer = chat(patientConvo)

    print("Patient:"+patientAnswer.content+ "(testing.initPatientSimulation())")
    #print("testing.initPatientSimulation(): Patient:"+patientAnswer.content)
    patientConvo.addMessage(patientAnswer)
    patientSimulation["patientConvo"] = patientConvo
    patientSimulations[id] = patientSimulation

## takes id of patient simulation and appends one patient response to it, returns conversation with appended response
def generatePatientAnswer(id):
    ## fetches patientConvo based on id
    global patientSimulations
    patientConvo = patientSimulations[id]["patientConvo"]

    # generates patient response based on patientConvo and updates patientConvo
    #print("testing.generatePatientAnswer() - patientConvo:")
    #print(patientConvo)
    patientResponse = chat(patientConvo)
    print("Patient:"+patientResponse.content+ + "(testing.generatePatientAnswer())")
    patientConvo.addMessage(patientResponse)

    patientSimulations[id]["patientConvo"] = patientConvo
    #print("Patient:"+patientSimulations[id]["patientConvo"][-1].content)
    return patientSimulations[id]["patientConvo"]



#discordFront.testing()
#async def testing():
 #   await discordBack.sendCustomMessage("general","Hi")

#asyncio.run(testing())

## initializes a demo conversation between a patient simulation and langdoc
def initDemoConversation():
    # initializes patient simulation id
    global patientSimulations
    
    testDict = defaultdict(dict)
    user_context=testDict["demoConversation"]
    user_context["user_id"]="demoConversation"
    
    # initializes langdoc api and first doc messages and prints them
    tester=langDocBack.initLangDocAPI(user_context)
    #print(tester)
    response = Conversation(tester)
    #response.print
    response.flipRoles(False)

    #for msg in response:
        #print("Doctor: "+msg.content)


    # initializes patient simulation with doc messages and simulation id
    initPatientSimulation(user_context["user_id"],response,None)
    patientConvo = patientSimulations[user_context["user_id"]]["patientConvo"]

    # gets doctor's first answer to patient's intro messages
    docAnswer = Conversation(langDocBack.initPatientConvo(patientConvo.lastMessage().content, user_context))

    patientConvo.addMessage(UserMessage(docAnswer[-1].content))
    patientSimulations[user_context["user_id"]]["patientConvo"] = patientConvo
    
    #print("testing.initDemoConversation() - patientConvo after last init:")
    #print(patientSimulations[user_context["user_id"]]["patientConvo"])

    #print("Doctor: "+patientSimulations[user_context["user_id"]]["patientConvo"][-1].content)

    while True:
        generatePatientAnswer(user_context["user_id"])
        patientConvo = patientSimulations[user_context["user_id"]]["patientConvo"]
        docReply = langDocBack.processResponse(patientConvo[-1].content, user_context)
        patientSimulations[user_context["user_id"]]["patientConvo"].addMessage(UserMessage(docReply[-1].content)) 
       # print("Doctor: "+docReply[-1].content)
        patientConvo.print("\n\n TESTING COUNTMESSAGE FUNCTION")
        print("Count:"+str(patientConvo.countMessagesOfType(HumanMessage)))


## initializes a demo conversation between a patient simulation and langdoc
def initVignettesDemo():
    # initializes patient simulation id
    global patientSimulations
    vignettes = loadVignettes()

    id = 0
    for v in vignettes:
        testDict = defaultdict(dict)
        user_context=testDict["demoConversation"]
        user_context["user_id"]="demoConversation"
    
    # initializes langdoc api and first doc messages and prints them
    tester=langDocBack.initLangDocAPI(user_context)
    #print(tester)
    response = Conversation(tester)
    #response.print
    response.flipRoles(False)

    #for msg in response:
        #print("Doctor: "+msg.content)


    # initializes patient simulation with doc messages and simulation id
    initPatientSimulation(user_context["user_id"],response,None)
    patientConvo = patientSimulations[user_context["user_id"]]["patientConvo"]

    # gets doctor's first answer to patient's intro messages
    docAnswer = Conversation(langDocBack.initPatientConvo(patientConvo.lastMessage().content, user_context))

    patientConvo.addMessage(UserMessage(docAnswer[-1].content))
    patientSimulations[user_context["user_id"]]["patientConvo"] = patientConvo
    
    #print("testing.initDemoConversation() - patientConvo after last init:")
    #print(patientSimulations[user_context["user_id"]]["patientConvo"])

    #print("Doctor: "+patientSimulations[user_context["user_id"]]["patientConvo"][-1].content)

    while True:
        generatePatientAnswer(user_context["user_id"])
        patientConvo = patientSimulations[user_context["user_id"]]["patientConvo"]
        docReply = langDocBack.processResponse(patientConvo[-1].content, user_context)
        patientSimulations[user_context["user_id"]]["patientConvo"].addMessage(UserMessage(docReply[-1].content)) 
       # print("Doctor: "+docReply[-1].content)
        patientConvo.print("\n\n TESTING COUNTMESSAGE FUNCTION")
        print("Count:"+str(patientConvo.countMessagesOfType(HumanMessage)))


#takes conversation and tests summary bot with it
def testSummaryBot(conversation):
    print(langDocBack.summarizeData(conversation))


# returns example COnversation of key i
def exampleConversation(i):
    if i == 1:
        convo = Conversation()
        convo.addMessage("Hi, I am Dr. Who, how can I help you today.", "ai")
        convo.addMessage("Hi, I am Anna, 22 years old, and I have a headache.", "human")
        convo.addMessage("I see. Could you tell me more?", "AI")
        convo.addMessage("Well it started two days ago and it has been getting worse ever since. Now it is really bad and it's been affecting my sleep and concentration.", "human")
        convo.addMessage("Could you summarize the pain in more detail?", "ai")
        convo.addMessage("Yes certainly, it's a kind of diffuse, dull pain everywhere in my head and it's really bad. It gets worse when I lower my head.", "human")
        return convo

def loadVignettes():
    f = open("vignettes.txt", "r")
    contents = f.read()
    vignettes = contents.split("===")
    return vignettes





vignettes = loadVignettes()

# for vignette in vignettes:
    # initPatientSimulation

langDocBack.initSysMsgs()
#testSummaryBot(exampleConversation(1))
initDemoConversation()
