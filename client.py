import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import socket
import threading
import re
import webbrowser

class client:
    def __init__(self, root, host = '127.0.0.1', port = 5020):
        self.root = root
        self.root.title(f"Chat App Client on Port: {port}")

        # self.server_address = f"{host}:{port}"  # Server IP and Port
        # self.local_ip = self.get_local_ip()  # Get local machine's IP address
        # self.root.title(f"Chat App Client - Local IP: {self.local_ip}, Server: {self.server_address}")  # Title with server and local IP


        # Username
        # Run the username prompt in a separate thread
        # threading.Thread(target=self.get_username, daemon=True).start()

        # self.username = simpledialog.askstring("Username:", "", parent = self.root)
        self.get_username()
        if not self.username:
            self.root.destroy()
            return
        

        # Setup the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((host, port))
            self.client_socket.send(self.username.encode()) # Send the name as the first message
            server_ip, server_addr = self.client_socket.getpeername()
            # print(f"server addr : {server_addr}")
            # self.root.title(f"Chat App Client on Port: {server_addr}")
        except ConnectionRefusedError:
            messagebox.showerror("Server Connection Error", "Could not connect to the server")
            self.root.destroy()
            return
        
    
        # User Interface
        self.chat_log = scrolledtext.ScrolledText(root, state = 'disabled', wrap = tk.WORD, height = 20)
        self.chat_log.pack(padx = 10, pady = (10, 5), fill = tk.BOTH, expand = True)

        frame = tk.Frame(root)
        frame.pack(padx = 10, pady = (0, 10), fill = tk.X)

        self.entry = tk.Entry(frame)
        self.entry.focus()  # Automatically focus the input box after the username prompt.
        self.entry.pack(side = tk.LEFT, fill = tk.X, expand = True, padx = (0, 5))
        self.entry.bind("<Return>", self.send_message)
        # self.entry.delete(1.0, tk.END)  # Clears the text box


        button = tk.Button(frame, text = "Send", command = self.send_message)
        button.pack(side = tk.RIGHT)

        self.running = True
        threading.Thread(target = self.receive_message, daemon = True).start()

        # Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Tag configuration for clickable URLs
        self.chat_log.tag_config('link', foreground='blue', underline=True)

    def get_local_ip(self):
        """Get the local IP address of the machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # Google's public DNS server
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    
    def get_username(self):
        self.username = simpledialog.askstring("Username", "Enter a username", parent = self.root)

        # No username entered close the program
        if not self.username:
            self.root.quit()

        # Normal operations
        else:
            print(f"Username entered: {self.username}\n")


    def send_message(self, event = None):
        msg = self.entry.get().strip()
        if msg:
            try:
                full_msg = f"{self.username}: {msg}"
                self.client_socket.send(full_msg.encode())
                self.display_message("You", msg)
                self.entry.delete(0, tk.END)
                self.entry.focus() # Fixes button delay
            except:
                self.display_message("System", "Failed to send message")

    # def receive_message(self):
    #     while self.running:
    #         try:
    #             msg = self.client_socket.recv(1024)
    #             if not msg:
    #                 break
    #             # self.display_message("", msg.decode())
    #              # Schedule UI update in the main thread to fix lag when pressing the text bar
    #             self.root.after(0, self.display_message, "", msg.decode())
    #         except:
    #             break
    #     self.root.after(0, self.display_message, "System", "[Connection lost to server]")
    #     # self.display_message("System", "[Connection lost to server]")
    #     self.client_socket.close()

    def receive_message(self):
        while self.running:
            try:
                msg = self.client_socket.recv(1024)
                if not msg:
                    break
                self.root.after(0, self.display_message, "", msg.decode())
            except (ConnectionResetError, ConnectionAbortedError):
                self.root.after(0, self.display_message, "System", "[Connection lost to server]")
                self.root.after(0, self.show_server_terminated_message)
                break

        # Gracefully close the application when the server disconnects
        self.root.after(0, self.on_close)

    def show_server_terminated_message(self):
        """Display a message informing the user that the server has terminated."""
        messagebox.showerror("Server Error", "The server has disconnected unexpectedly. Closing the client.")



    # need to add a fix to get rid of lag when clicking on the display text
    
    # This fixed a little of the lag
    def display_message(self, sender, msg):
    # This method is only for updating the UI. No background thread calls here.
        self.root.after(0, self._display_message, sender, msg)

    def _display_message(self, sender, msg):
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Now this is the actual UI update (running safely on the main thread)
        self.chat_log.config(state='normal')
            # Remove unwanted colons from the sender (if any)
        # sender = sender.lstrip(':').rstrip(':')  # Remove leading and trailing colons

        url_pattern = r"(http://[^\s]+|https://[^\s]+|www\.[^\s]+)"
        urls = re.findall(url_pattern, msg)


        if sender:
            self.chat_log.insert(tk.END, f"{sender}: {msg}\n")
            # self.chat_log.insert(tk.END, f"{msg}\n")
        else:
            self.chat_log.insert(tk.END, f"{msg}\n")
            # self.chat_log.insert(tk.END, f"{sender}: {msg}\n")

              # Now check for URLs and make them clickable
        for url in urls:
            self._insert_link(url)

        # Check if the sender is "You", which means the message was sent by the user
        # if sender == "You":
        #     self.chat_log.insert(tk.END, f"{msg}\n", "sent_msg")
        # else:
        #     # If not, consider the message as received
        #     self.chat_log.insert(tk.END, f"{sender}: {msg}\n", "received_msg")
    
        self.chat_log.config(state='disabled')
        self.chat_log.yview(tk.END)

        # Adding tags for styling
        # self.chat_log.tag_config("sent_msg", foreground="white", background="blue", font=("Helvetica", 10, "bold"))
        # self.chat_log.tag_config("received_msg", foreground="black", background="lightgray", font=("Helvetica", 10))

    def _insert_link(self, url):
        """Make an existing URL in the chat log clickable."""
        # Find the last occurrence of the URL in the chat log
        chat_text = self.chat_log.get("1.0", tk.END)
        last_pos = chat_text.rfind(url)
        if last_pos == -1:
            return  # URL not found (shouldn't happen since we just inserted it)
        # Convert the position to Tkinter's line.column format
        lines = chat_text[:last_pos].split('\n')
        line_num = len(lines)
        col_num = len(lines[-1])
        start_idx = f"{line_num}.{col_num}"
        end_idx = f"{line_num}.{col_num + len(url)}"
        # Apply the 'link' tag to the URL's position
        self.chat_log.tag_add(url, start_idx, end_idx)
        self.chat_log.tag_config(url, foreground='blue', underline=True)
        self.chat_log.tag_bind(url, "<Button-1>", lambda e, url=url: self.open_url(url))                                                              
    
    def open_url(self, url):
        """Open the URL in the default web browser."""
        if not url.startswith('http'):
            url = 'http://' + url
        webbrowser.open(url)

    def on_close(self):
        self.running = False
        try:
                    # Notify the server that the client is disconnecting
            disconnect_msg = f"{self.username} has left the chat"
            self.client_socket.send(disconnect_msg.encode())  # Sending disconnect message

            self.client_socket.close()
        except:
            pass
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = client(root)
    root.geometry("680x700")
    root.resizable(False, False)
    root.mainloop()


