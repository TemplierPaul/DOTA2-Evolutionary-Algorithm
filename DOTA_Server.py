from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from optparse import OptionParser
import threading
import random
import requests
import time

from DOTA_request_handler import DotaServerHandler
from fitness_evaluator import FitnessEvaluator

parser = OptionParser()
# the address of this agent server
parser.add_option("-i", "--ip", type="string", dest="agentIp", default="127.0.0.1")
parser.add_option("-p", "--port", type="string", dest="agentPort", default="8086")

# the address of the breezy server
parser.add_option("--ipb", type="string", dest="breezyIp", default="127.0.0.1")
parser.add_option("--portb", type="string", dest="breezyPort", default="8085")

(opts, args) = parser.parse_args()


class DotaServer(HTTPServer):
    def __init__(self, manager):
        HTTPServer.__init__(self, (opts.agentIp, int(opts.agentPort)), DotaServerHandler)
        self.manager = manager

    def show(self):
        print(self.manager.decision_function)


class DotaServerManager():
    def __init__(self):
        self.server = DotaServer(self)
        self.decision_function = None
        self.fitness_evaluator = FitnessEvaluator()
        self.started = False
        self.running_game = False

    def start_server(self):
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        print("Agent server started.")

        """
        Declare variables global that you want the agent server to have access to.
        """
        global breezyIp
        global breezyPort

        breezyIp = opts.breezyIp
        breezyPort = opts.breezyPort
        self.started = True

    def stop_server(self):
        try:
            self.stop_game()
        except:
            pass
        self.server.shutdown()
        print("Agent server stopped")

    def start_game(self, decision_func=None):
        assert self.started
        self.running_game = True

        self.fitness_evaluator.reset()
        self.decision_function = decision_func

        # create a run config for this agent, to run 1 game, send to breezy server
        startData = {
            "agent": "NEAT Agent",
            "size": 1
        }
        # tell breezy server to start the run
        response = requests.post(
            url="http://{}:{}/run/".format(opts.breezyIp, opts.breezyPort),
            data=json.dumps(startData))

        print("Start Game", response)

    def stop_game(self):
        response = requests.delete(
            url="http://{}:{}/run/active".format(opts.breezyIp, opts.breezyPort))
        print("Stop Game", response)
        self.running_game = False

    def play_game(self):
        def decision(*args, **kwargs):
            print(args)
            return 0

        self.start_game(decision_func=decision)

        while self.running_game == True:
            pass

        fitness = self.fitness_evaluator.final_evaluation()
        print("FITNESS:", fitness)
        return fitness


if __name__ == "__main__":
    manager = DotaServerManager()
    manager.start_server()
    manager.play_game()
    # manager.stop_game()
    manager.stop_server()
