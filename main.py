from Tkinter import *
import Tkinter as ttk
import threading
import zmq
import json

class IncomingMessageThread(threading.Thread):
    callback = None

    def run(self):
        context = zmq.Context()

        try:
            subscription = context.socket(zmq.SUB)
            subscription.connect("tcp://localhost:5002")

            # TODO: Use json for messages!
            subscription.setsockopt(zmq.SUBSCRIBE, "MESSAGE ")
        except zmq.error.ZMQError as e:
            print("Failed to subscribe")

        while True:
            message = subscription.recv()
            self.callback(message)


class ChatClient(ttk.Frame):
    def __init__(self, width, height):
        self.root = Tk()

        self.window_dimensions = {
            "height": self.root.winfo_screenheight(),
            "width": self.root.winfo_screenwidth()
        }

        self.app_dimensions = {
            "height": height,
            "width": width
        }

        self.buffers = {
            "message": StringVar(),
            "username": StringVar(),
            "connection": StringVar()
        }

        # Holds a scrollable list of the conversation history.
        self.message_history = None

        self.frames = {}
        self.labels = {}

        # Networking data structures
        self.networking = {
            "context": None,
            "sockets": {},
            "status": {
                "error": False,
                "error_message": ""
            },
            "client_token": None
        }

        self.incoming_message_thread = None

    def start(self):
        self.setup_networking()

        self.build_ui()

        self.root.mainloop()

    def setup_networking(self):
        """
        Setup the networking data structures

        :return: void
        """
        self.networking["context"] = zmq.Context()

        try:
            # The sending socket sends messages to the chat server
            # which are then routes to all other chat clients.
            send_socket = self.networking["context"].socket(zmq.PUSH)
            send_socket.connect("tcp://localhost:5000")
            self.networking["sockets"]["sender"] = send_socket

            # The connection socket handles establishing a connection
            # between this particular client and the server.
            connection_socket = self.networking["context"].socket(zmq.REQ)
            connection_socket.connect("tcp://localhost:5001")
            self.networking["sockets"]["connector"] = connection_socket

            self.incoming_message_thread = IncomingMessageThread()
            self.incoming_message_thread.callback = self.handle_incoming_message
            self.incoming_message_thread.daemon = True
            self.incoming_message_thread.start()

        except zmq.error.ZMQError as e:
            self.networking["status"]["error"] = True
            self.networking["status"]["message"] = e.message

    def build_ui(self):
        self.build_connection_frame()
        self.center()

    def build_connection_frame(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=BOTH, expand=1)

        self.labels["connection"] = ttk.Label(frame, textvariable=self.buffers["connection"])
        self.labels["connection"].pack()

        # Entry for username
        entry = ttk.Entry(frame, textvariable=self.buffers["username"])
        entry.pack()

        button = ttk.Button(frame, text="Connect", command=self.connect)
        button.pack()

        self.frames["connection"] = frame

    def connect(self):
        username = self.buffers["username"].get()

        if len(username) == 0:
            self.buffers["connection"].set("Please enter a username.")
        else:
            connection_message = {"username": username}

            self.networking["sockets"]["connector"].send(json.dumps(connection_message))

            reply = json.loads(self.networking["sockets"]["connector"].recv())

            if reply["success"] == True:
                self.networking["client_token"] = reply["token"]
                self.build_chat_frame()
            else:
                self.buffers["connection"].set(reply["error"])

    def build_chat_frame(self):
        self.frames["connection"].pack_forget();

        mainframe = ttk.Frame(self.root)
        mainframe.pack(fill=BOTH, expand=1)

        self.message_history = Listbox(mainframe)
        self.message_history.pack(fill=BOTH, expand=1)

        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(fill=BOTH, expand=1)

        entry = ttk.Entry(bottom_frame, textvariable=self.buffers["message"])
        entry.pack(fill=BOTH, expand=1)

        self.root.bind('<Return>', self.post_message)

        self.frames["chat"] = mainframe

    def post_message(self, something):
        message = {
            "token": self.networking["client_token"],
            "message": self.buffers["message"].get()
        }

        self.networking["sockets"]["sender"].send(json.dumps(message))

    def center(self):
        app_width = self.app_dimensions["width"]
        app_height = self.app_dimensions["height"]

        # We're starting the app at the center of the screen.
        start_x = (self.window_dimensions["width"] / 2) - (app_width / 2)
        start_y = (self.window_dimensions["height"] / 2) - (app_height / 2)

        self.root.geometry("%dx%d+%d+%d" % (app_width, app_height, start_x, start_y))

    def handle_incoming_message(self, message):
        print(message)
        return
        self.message_history.insert(END, message)


def main():
    app = ChatClient(800, 650)
    app.start()


if __name__ == "__main__":
    main()
