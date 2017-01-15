from Tkinter import *
import Tkinter as ttk

import threading
import zmq

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

        # Holds the text in the entry element.
        self.message_buffer = StringVar()

        # Holds a scrollable list of the conversation history.
        self.message_history = None

        # Networking data structures
        self.networking = {
            "context": None,
            "sockets": {},
            "status": {
                "error": False,
                "error_message": ""
            }
        }

        self.incoming_message_thread = None

    def start(self):
        self.setupNetworking()

        self.buildUI()

        self.root.mainloop()

    def setupNetworking(self):
        """
        Setup the networking structures and connect to the chat server.

        :return: void
        """
        self.networking["context"] = zmq.Context()

        try:
            # Create some sockets.

            # The sending socket sends messages to the chat server
            # which are then routes to all other chat clients.
            send_socket = self.networking["context"].socket(zmq.PUSH)
            send_socket.connect("tcp://localhost:5000")

            self.networking["sockets"]["sender"] = send_socket

            self.incoming_message_thread = IncomingMessageThread()

            self.incoming_message_thread.callback = self.handle_incoming_message

            # Python will terminate the app, in the face of running threads, if those
            # threads are daemon threads.
            self.incoming_message_thread.daemon = True
            self.incoming_message_thread.start()

        except zmq.error.ZMQError as e:
            self.networking["status"]["error"] = True
            self.networking["status"]["messgae"] = e.message

    def buildUI(self):
        mainframe = ttk.Frame(self.root)
        mainframe.pack(fill=BOTH, expand=1)

        self.message_history = Listbox(mainframe)
        self.message_history.pack(fill=BOTH, expand=1)

        bottom_frame = ttk.Frame(mainframe)
        bottom_frame.pack(fill=BOTH, expand=1)

        entry = ttk.Entry(bottom_frame, textvariable=self.message_buffer)
        entry.pack(fill=BOTH, expand=1)

        self.root.bind('<Return>', self.sendMessage)

        self.center()

    def sendMessage(self, *args):
        self.networking["sockets"]["sender"].send(self.message_buffer.get())

    def center(self):
        app_width = self.app_dimensions["width"]
        app_height = self.app_dimensions["height"]

        # We're starting the app at the center of the screen.
        start_x = (self.window_dimensions["width"] / 2) - (app_width / 2)
        start_y = (self.window_dimensions["height"] / 2) - (app_height / 2)

        self.root.geometry("%dx%d+%d+%d" % (app_width, app_height, start_x, start_y))

    def handle_incoming_message(self, message):
        self.message_history.insert(END, message)

def main():
    app = ChatClient(800, 650)
    app.start()

if __name__ == "__main__":
    main()