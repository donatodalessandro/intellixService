from cheroot import wsgi

# Importazione del modulo di PyMongo
from flask import Flask

app = Flask(__name__)
addr = '127.0.0.1', 5000
server = wsgi.Server(addr, app)
if __name__ == '__main__':
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        server.stop()
        print("-----------------Debug message: server stopped")
