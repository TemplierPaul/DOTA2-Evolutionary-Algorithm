from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from optparse import OptionParser
import threading
import random
import requests

from DOTA_fitness_evaluator import FitnessEvaluator

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
    Decision function getter and setter
    """
    
    @property
    def decision_func(self):
        # assert self._decision_func is not None
        return self.server._decision_func

    @decision_func.setter
    def decision_func(self, func):
        self._decision_func = func

    """
    Fitness evaluator getter and setter
    """

    @property
    def fitness_evaluator(self):
        # assert self._decision_func is not None
        return self.server._fitness_evaluator

    @fitness_evaluator.setter
    def fitness_evaluator(self, fe):
        self._fitness_evaluator = fe

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
        # print(self.path)
        # print("Received GET request.")
        self.postResponse(json.dumps({"response": "Hello"}))

    """
    POST used for getting features and returning action.
    """

    def do_POST(self):
        global keep_server_up
        # print(self.path)

        if self.path == "/update":
            """
            Update route is called, game finished.
            """

            global breezyIp
            global breezyPort

            # print("Game done.")
            content = self.getContent().decode("utf-8")
            # print(content)
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

                """
                Stop server
                """
                keep_server_up = False
                self.server.shutdown()

            # send whatever to server
            # self.postResponse(json.dumps({"fitness":42}))

        else:  # relay path gives features from current game to agent
            """
            Relay route is called, gives features from the game for the agent.
            """

            # print("Received features.")
            # get data as json, then save to list
            content = self.getContent().decode("utf-8")
            global features
            features_list = json.loads(content)

            if features_list[0] != 'id':
                features = features_list
            else:
                keep_server_up = False
                print("Last Feature Array Reached")
            # print(features)

            self.fitness_evaluator.frame_evaluation(features)

            if self.fitness_evaluator.early_stop:
                keep_server_up = False
                self.server.shutdown()

            """
            Agent code to determine action from features would go here.
            """
            action = self.decision_func(features)
            self.postResponse(json.dumps({"actionCode": action}))


def stop_game():
    response = requests.delete(
        url="http://{}:{}/run/active".format(opts.breezyIp, opts.breezyPort))

    print(response)


def start_server(decision_func, fitness_evaluator):
    """
        Sets up and starts the Agent server and triggers the start of a run on the
        Breezy server.
    """
    # start the Agent server in other thread
    print("Agent Server starting at {}:{}...".format(opts.agentIp, opts.agentPort))
    agentHandler = HTTPServer((opts.agentIp, int(opts.agentPort)), ServerHandler)

    # Set GA functions
    agentHandler._decision_func = decision_func
    agentHandler._fitness_evaluator = fitness_evaluator

    thread = threading.Thread(target=agentHandler.serve_forever)
    thread.daemon = True
    thread.start()
    print("Agent server started.")

    # create a run config for this agent, to run 1 game, send to breezy server
    startData = {
        "agent": "NEAT Agent",
        "size": 1
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

    global features

    # serve until told to stop (end of the game)
    global keep_server_up
    keep_server_up = True

    while keep_server_up:
        pass

    stop_game()
    agentHandler.shutdown()
    thread.join()

    return fitness_evaluator.final_evaluation()


if __name__ == "__main__":
    def decision(arg):
        print("%d Features" % len(arg))
        return random.randint(0, 29)

    fitness_evaluator = FitnessEvaluator()

    fitness = start_server(decision_func=decision, fitness_evaluator=fitness_evaluator)
    print("\nFITNESS\n", fitness)
