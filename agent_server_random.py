from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from optparse import OptionParser
import threading
import random
import requests

parser = OptionParser()
# the address of this agent server
parser.add_option("-i", "--ip", type="string", dest="agentIp", default="127.0.0.1")
parser.add_option("-p", "--port", type="string", dest="agentPort", default="8086")

# the address of the breezy server
parser.add_option("--ipb", type="string", dest="breezyIp", default="127.0.0.1")
parser.add_option("--portb", type="string", dest="breezyPort", default="8085")

(opts, args) = parser.parse_args()

"""
Handles HTTP requests from the dota server.
"""
class ServerHandler(BaseHTTPRequestHandler):

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
        print(self.path)
        
        if self.path == "/update": 
            """
            Update route is called, game finished.
            """
            
            global breezyIp
            global breezyPort
            
            print("Game done.")
            content = self.getContent().decode("utf-8")
            print(content)
            rundata = json.loads(content)
            
            # webhook to start new game in existing set of games
            if "webhook" in rundata:
                """
                A webhook was sent to the agent to start a new game in the current
                set of games.
                """
            
                webhookUrl = "http://{}:{}{}".format(
                    breezyIp, breezyPort, rundata["webhook"])
                print(webhookUrl)
                
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
                
                # build url to dota 2 breezy server
                startUrl = "http://{}:{}/run/".format(
                    breezyIp, breezyPort)
                # create a run config for this agent, to run 5 games
                startData = {
                    "agent": "Sample Random Agent",
                    "size": 5
                }
                response = requests.post(url=startUrl, data=json.dumps(startData))
                
            # send whatever to server
            self.postResponse(json.dumps({"fitness":42}))
            
        else: # relay path gives features from current game to agent
            """
            Relay route is called, gives features from the game for the agent.
            """
            
            print("Received features.")
            # get data as json, then save to list
            content = self.getContent().decode("utf-8")
            features = json.loads(content)
            print(features)
        
            """
            Agent code to determine action from features would go here.
            """
            action = random.randint(0,29) # just random action for this example
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
        "agent": "Sample Random Agent",
        "size": 5
    }
    # tell breezy server to start the run
    response = requests.post(
        url="http://{}:{}/run/".format(opts.breezyIp, opts.breezyPort), 
        data=json.dumps(startData))
    
    print(response)
    
    """
    Declare variables global that you want the agent server to have access to.
    """
    global breezyIp
    global breezyPort
    
    breezyIp = opts.breezyIp
    breezyPort = opts.breezyPort

    # serve until force stop
    while True:
        pass
    
