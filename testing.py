import asyncio
import logging, os
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
from multiprocessing import Pool, Process, current_process, freeze_support

chat = ChatOpenAI(temperature=0)
# patientSimulations = defaultdict(dict)

## initializes a patient simulation with id, initial inputMessages (e.g. initial questions from doc) and patient specification 
## defaults to glaucoma patient if no patient specification is passed
## initializes patientSimulations[id]["patientConvo"] with all initial messages and adds first patient response
async def initPatientSimulation(id, inputMessages, patientSpecification = None, logger = logging.getLogger()):
    logger.info("Initializing Patient Simulation with ID "+ str(id)+ " (testing.initPatientSimulation())")
    patientSimulation = defaultdict(dict)
    patientSimulation["id"] = "Patient "+str(id)
    patientSimulation["patientConvo"] = None
    #patientSimulation["patientConvo"] = None

    if not patientSpecification:
        patientSpecification = "Ms. Rodriqguez, a 60 year old smoker with yet undiagnosed glaucoma."
    
    patientSimulation["patientSpecification"] = patientSpecification

    patientSys = """
    You are PatientGPT, designed to simulate patients as realistically as possible for med students and doctors to practice their anamnesis skills.
    Today, you will play the following patient:"""+ patientSimulation["patientSpecification"] +""".
    As the medics are asking you questions, make up realistic symptoms, patient history and do a good job of providing a realistic patient anamnesis experience. This means that you sometimes tell irrelevant information and sometimes don't share information unless explicitly asked.
    Keep in mind that you should only ever simulate the responses of the patient and let the students/doctors ask the questions. 
    The next thing the patient says is:
    """

    patientConvo = Conversation(SystemMessage(patientSys))
    
    for msg in inputMessages:
        patientConvo.addMessage(HumanMessage(content=msg.content))
    
    patientAnswer = chat(patientConvo)

    logger.info("Patient:"+patientAnswer.content+ "(testing.initPatientSimulation())")
    #print("testing.initPatientSimulation(): Patient:"+patientAnswer.content)
    patientConvo.addMessage(patientAnswer)
    patientSimulation["patientConvo"] = patientConvo
    return patientSimulation

## takes patient simulation and appends one patient response to it, returns patientsimulation with patientSimulation["patientConvo"] with appended response
def generatePatientAnswer(patientSimulation):
    ## fetches patientConvo based on id
    
    patientConvo = patientSimulation["patientConvo"]

    # generates patient response based on patientConvo and updates patientConvo
    #print("testing.generatePatientAnswer() - patientConvo:")
    #print(patientConvo)
    patientResponse = chat(patientConvo)
    print("Patient:"+patientResponse.content + "(testing.generatePatientAnswer())")
    patientConvo.addMessage(patientResponse)

    patientSimulation["patientConvo"] = patientConvo
    #print("Patient:"+patientSimulations[id]["patientConvo"][-1].content)
    return patientSimulation


def getLogger(type = "terminal", id = "NAN"):
    log_dir = r"C:\Users\User\BayesDoc Discord\Logs"
    log_name = f"logfile_Patient_{str(id)}_{str(current_process().pid)}.log"
    logfile_path = os.path.join(log_dir, log_name)
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(str(current_process().pid)) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if type == "terminal":
        handler = logging.StreamHandler()
    if type == "file":
        handler = logging.FileHandler(logfile_path)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def getDemoUserContext():
    testDict = defaultdict(dict)
    user_context=testDict["demoConversation"]
    user_context["user_id"]="demoConversation"
    return user_context

#discordFront.testing()
#async def testing():
 #   await discordBack.sendCustomMessage("general","Hi")

#asyncio.run(testing())

## initializes a demo conversation between a patient simulation and langdoc
async def initDemoConversation():

    # initializes patient simulation id
    user_context = getDemoUserContext()
    user_context["logger"]=logging.getLogger("file", "demoConvo")    

    # initializes langdoc api and first doc messages and prints them
    tester=langDocBack.initLangDocAPI(user_context)["docConvo"]
    #print(tester)
    response = Conversation(tester)
    #response.print
    response.flipRoles(False)
    response.addMessage("To get started, could you please provide your age, sex, and nationality?","user")

    #for msg in response:
        #print("Doctor: "+msg.content)

    
    # initializes patient simulation with doc messages and simulation id
    patientSimulation = await initPatientSimulation(user_context["user_id"],response,None)
    patientConvo = patientSimulation["patientConvo"]

    # gets doctor's first answer to patient's intro messages
    docAnswer = Conversation(langDocBack.initPatientConvo(patientConvo.lastMessage().content, user_context)["docConvo"])

    patientConvo.addMessage(UserMessage(docAnswer.lastMessage().content))
    patientSimulation["patientConvo"] = patientConvo
    
    #print("testing.initDemoConversation() - patientConvo after last init:")
    #print(patientSimulations[user_context["user_id"]]["patientConvo"])

    #print("Doctor: "+patientSimulations[user_context["user_id"]]["patientConvo"][-1].content)

    while True:
        patientSimulation = generatePatientAnswer(patientSimulation)
        patientConvo = patientSimulation["patientConvo"]
        docReply = langDocBack.processResponse(patientConvo[-1].content, user_context)
        patientSimulation["patientConvo"].addMessage(UserMessage(docReply["docConvo"].lastMessage().content)) 
       # print("Doctor: "+docReply[-1].content)
        #patientConvo.print("\n\n TESTING COUNTMESSAGE FUNCTION")
        #print("Count:"+str(patientConvo.countMessagesOfType(HumanMessage)))

def runPatientSimulation(id, vignette):
    try:
        logger = getLogger("file", id)
        user_context = getDemoUserContext()   
        user_context["logger"] = logger

        # initializes langdoc api and first doc messages and prints them, flips roles of generated answers so that patient AI thinks that the doc AI's messages are coming from the user
        tester=langDocBack.initLangDocAPI(user_context)
        #logger.info(tester)
        response = Conversation(tester["docConvo"])
        #response.print
        response.flipRoles(False)
        response.addMessage("To get started, could you please provide your age, sex, and nationality?","user")

        # inits patient simulation 
        logger.info("Initializing patient simulation of ID "+str(id)+" Vignette: "+ vignette + "testing.runPatientSimulation()")
        patientSimulation = asyncio.run(initPatientSimulation(user_context["user_id"],response,vignette,logger))
        #patientSimulation = await initPatientSimulation(user_context["user_id"],response,vignette)
        patientSimulation["user_id"] = id
        patientSimulation["user_context"] = user_context

        patientConvo = patientSimulation["patientConvo"]

        # gets doctor's first answer to patient's intro messages
        docAnswer = Conversation(langDocBack.initPatientConvo(patientConvo.lastMessage().content, user_context)["docConvo"])
        patientConvo.addMessage(UserMessage(docAnswer.lastMessage().content))
        patientSimulation["patientConvo"] = patientConvo
        user_context = patientSimulation["user_context"]
        while True:
                patientSimulation = generatePatientAnswer(patientSimulation)
                patientConvo = patientSimulation["patientConvo"]
                docreply = langDocBack.processResponse(patientConvo[-1].content, user_context)
                patientSimulation["patientConvo"].addMessage(UserMessage(docreply["docConvo"].lastMessage().content)) 
                # logger.info("Doctor: "+docReply[-1].content)
                # patientConvo.logger.info("\n\n TESTING COUNTMESSAGE FUNCTION")
                # logger.info("Count:"+str(patientConvo.countMessagesOfType(HumanMessage)))
    except Exception as e:
        logger = logging.getLogger(str(current_process().pid)) 
        logger.error(f"An error occurred: {e}")

## initializes a demo conversation between a patient simulation and langdoc
def initVignettesDemo(vignettes):
    with Pool() as p:
        logger = logging.getLogger()
        logger.info("Initializing "+ str(len(vignettes))+ " vignettes. (testing.initVignettesDemo())")        
        id_vignette_pairs = [(i+1, v) for i, v in enumerate(vignettes)]
        result = p.starmap(runPatientSimulation, id_vignette_pairs)
        result.get()
    # initializes patient simulations
    
    """
    logger.info("Initializing "+ str(vignettes.__len__())+ " vignettes. (testing.initVignettesDemo())")
    id = 1
    for v in vignettes:
        # runs patient simulation with vignette v and incrementally higher id 
        logger.info("Initializing patient simulation no."+str(id))
        coro = runPatientSimulation(id,  v)
        asyncio.create_task(coro)
        logger.info("TEST")
        id = id + 1 
    #loop.run_forever()
    """
       
def loadVignettes():
    f = open("vignettes.txt", "r")
    contents = f.read()
    vignettes = contents.split("===")
    return vignettes

#takes conversation and tests summary bot with it
def testSummaryBot(conversation):
    testDict = defaultdict(dict)
    user_context = testDict["demoConversation"]
    user_context["docConvo"]= conversation    
    user_context["user_id"]="Test_User"
    user_context["logger"] = logging.getLogger()
    print(langDocBack.summarizeData(user_context))


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



if __name__ == '__main__':
    vignettes = loadVignettes()
    print("INIT")
    langDocBack.initSysMsgs()
    #testSummaryBot(exampleConversation(1))
    #asyncio.run(initDemoConversation())
    initVignettesDemo(vignettes)