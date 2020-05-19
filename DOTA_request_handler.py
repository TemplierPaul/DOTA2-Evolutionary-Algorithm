from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from optparse import OptionParser
import threading
import random
import requests


class DotaServerHandler(BaseHTTPRequestHandler):
    """
    Mute the printing of each request
    """

    def log_message(self, format, *args):
        return
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

            print("Game done.")
            self.server.manager.running_game = False

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

            """
            Compute in-game fitness
            """
            self.server.manager.fitness_evaluator.frame_evaluation(features)

            """
            Determine if early stop is needed
            """
            if self.server.manager.fitness_evaluator.early_stop:
                self.server.manager.stop_game()

            """
            Agent code to determine action from features would go here.
            """
            action = self.server.manager.decision_function(features)
            self.postResponse(json.dumps({"actionCode": action}))
