from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from optparse import OptionParser
import threading
import requests
from tpg.trainer import Trainer
from tpg.agent import Agent
import numpy as np
import datetime

parser = OptionParser()
# the address of this agent server
parser.add_option("-i", "--ip", type="string", dest="agentIp", default="127.0.0.1")
parser.add_option("-p", "--port", type="string", dest="agentPort", default="8086")

# the address of the breezy server
parser.add_option("--ipb", type="string", dest="breezyIp", default="127.0.0.1")
parser.add_option("--portb", type="string", dest="breezyPort", default="8085")

"""
Arguments for TPG setup.
"""
# population size
parser.add_option("-P", "--pop", type="int", dest="popSize", default=200)
parser.add_option("-g", "--gens", type="int", dest="gens", default=100)
parser.add_option("-r", "--gameReps", type="int", dest="gameReps", default=3)

(opts, args) = parser.parse_args()


"""
Handles HTTP requests from the dota server.
"""
class ServerHandler(BaseHTTPRequestHandler):

    """
    Get the fitness from the final game state.
    """
    def getFitness(self, state, win):
        # incomplete, missing kills and not dead bonus
        return 10*state[24] + 15*state[25] + state[23] + 2000*win

    """
    Helper function to get content passed with http request.
    """
    def getContent(self):
        cLen = int(self.headers["Content-Length"])
        return self.rfile.read(cLen)

    """
    Sends a response containing a json object (usually the action).
    """
    def postResponse(self, response):
        # response code and info
        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        # set the actual response data
        self.wfile.write(str(response).encode("utf-8"))

    """
    GET used for testing connection.
    """
    def do_GET(self):
        print(self.path)
        print("Received GET request.")
        self.postResponse(json.dumps({"response":"Hello"}))

    """
    POST used for getting features and returning action.
    """
    def do_POST(self):
    
        # agent used in either path
        global agent
        global lastState
        
        if self.path == "/update": 
            """
            Update route is called, game finished.
            """
            
            global breezyIp
            global breezyPort
            
            global agentScores
            
            print("Game done.")
            content = self.getContent().decode("utf-8")
            print(content)
            runData = json.loads(content)
            
            # save score to list of scores for current agent
            curFitness = self.getFitness(
                lastState, runData["winner"] == "Radiant")
            agentScores.append(curFitness)
            print("Agent scored {}!".format(curFitness))
            
            # webhook to start new game in existing set of games
            if "webhook" in runData:
                """
                A webhook was sent to the agent to start a new game in the current
                set of games.
                """
                
                print("Starting rep #{}.".format(runData["progress"]+1))
                
                webhookUrl = "http://{}:{}{}".format(
                    breezyIp, breezyPort, runData["webhook"])
                
                # call webhook to trigger new game
                response = requests.get(url=webhookUrl)
                
            # otherwise start new set of games, or end session
            else:
                """
                This sample agent just runs indefinately. So here I will just start
                a new set of 5 games. You could just always set the amount of games
                to 1, and forget about the webhook part, whatever works for you.
                In here would probably be where you put the code to ready a new agent
                (update NN weights, evolutions, next agent in current gen. etc.).
                """
                
                global trainer
                global agents
                global totalGens
                global gameReps
                global curGen
                global logName
                
                """
                Prepare next TPG agent (or generation if required).
                """
                
                if curGen == totalGens:
                    print("Done Training.")
                    return
                    
                
                
                # reward score to current agent
                fitness = sum(agentScores)/gameReps
                agent.reward(fitness, "dota")
                print("Agent done. Fitness: {}.".format(fitness))
                agentScores = []
                
                # log the current score
                with open(logName, "a") as f:
                    f.write("{},{}".format(curGen, fitness))
                
                if len(agents) == 0:
                    curGen += 1
                    print("On to generation #{}.".format(curGen))
                    
                    # start new generation
                    trainer.evolve(tasks=["dota"])
                    # get new agents
                    agents = trainer.getAgents(skipTasks=["dota"])
                    
                    
                # get next agent
                agent = agents.pop()
                
                
                
                # build url to dota 2 breezy server
                startUrl = "http://{}:{}/run/".format(
                    breezyIp, breezyPort)
                # create a run config for this agent, to run 5 games
                startData = {
                    "agent": "Sample TPG Agent",
                    "size": gameReps
                }
                response = requests.post(url=startUrl, data=json.dumps(startData))
                
                
            # send whatever to server
            self.postResponse(json.dumps({"fitness":42}))
            
        else: # relay path gives features from current game to agent
            """
            Relay route is called, gives features from the game for the agent.
            """
            
            # get data as json, then save to list
            content = self.getContent().decode("utf-8")
            features = json.loads(content)
            
            lastState = features # save last state to calculate fitness at end
        
            """
            Agent code to determine action from features goes here.
            """
            action = agent.act(np.array(features, dtype=np.float64))
            self.postResponse(json.dumps({"actionCode":action}))

if __name__ == "__main__":
    """
    Sets up and starts the Agent server and triggers the start of a run on the 
    Breezy server.
    """

    # start the Agent server in other thread
    print("Agent Server starting at {}:{}...".format(opts.agentIp, opts.agentPort))
    agentHandler = HTTPServer((opts.agentIp, int(opts.agentPort)), ServerHandler)
    thread = threading.Thread(target=agentHandler.serve_forever)
    thread.daemon = True
    thread.start()
    print("Agent server started.")

    # create a run config for this agent, to run 5 games, send to breezy server
    startData = {
        "agent": "Sample TPG Agent",
        "size": opts.gameReps
    }
    # tell breezy server to start the run
    response = requests.post(
        url="http://{}:{}/run/".format(opts.breezyIp, opts.breezyPort), 
        data=json.dumps(startData))
    
    print(response)
    
    """
    Declare variables global that you want the agent server to have access to.
    Also initialization.
    """
    # from options
    global breezyIp
    global breezyPort
    global totalGens
    global gameReps
    
    # for agent
    global trainer
    global agents
    global agent
    global agentScores
    global curGen
    global lastState
    
    
    breezyIp = opts.breezyIp
    breezyPort = opts.breezyPort
    totalGens = opts.gens
    gameReps = opts.gameReps
    
    # set up of the TPG agent
    trainer = Trainer(actions=range(30), 
                      teamPopSize=opts.popSize, 
                      rTeamPopSize=opts.popSize,
                      sourceRange=310)
    agents = trainer.getAgents()
    agent = agents.pop()
    agentScores = []
    curGen = 0
    lastState = None
    
    # create a log file 
    global logName
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    logName = "log-{}.txt".format(timestamp)

    # serve until force stop
    while True:
        pass
    
