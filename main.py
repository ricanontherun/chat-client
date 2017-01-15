from Tkinter import *
import Tkinter as ttk

import zmq

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

def main():
    app = ChatClient(800, 650)
    app.start()

if __name__ == "__main__":
    main()