import os

address = "192.168.1.103"


def connect():
    os.system(
        'netsh interface portproxy add v4tov4 listenaddress=localhost listenport=8086 connectaddress=%s connectport=8086' % address)


def disconnect():
    os.system('netsh interface portproxy delete v4tov4 listenaddress=localhost listenport=8086')
