import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
import socket
import threading
import re
import webbrowser

# Main Code Running
class client:
    def __init__(self, root, host = '127.0.0.1', port = 5020):
        self.root = root
        self.root.title(f"Chat App Client on Port: {port}")

        # Emoji shortcut dictionary
        # Will be used later on can increase the size or decrease
        self.emoji_dict = {
            ":smile:": "😊",
            ":laugh:": "😂",
            ":thumbsup:": "👍",
            ":heart:": "❤️",
            ":sad:": "😢",
            ":angry:": "😡",
            ":sparkles:": "✨",
            ":rocket:": "🚀"
        }

        # Get the username
        self.get_username()
        if not self.username:
            self.root.destroy()
            return
        

        # Setup the client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((host, port))
            self.client_socket.send(self.username.encode()) # Send the name as the first message
        except ConnectionRefusedError:
            messagebox.showerror("Server Connection Error", "Could not connect to the server")
            self.root.destroy()
            return
        
    
        # User Interface

        # Emoji Setup
        emoji_font = ("Segoe UI Emoji", 12)  # Adjust size as needed
        self.chat_log = scrolledtext.ScrolledText(root, state = 'disabled', wrap = tk.WORD, height = 20, font = emoji_font)
        self.chat_log.pack(padx = 10, pady = (10, 5), fill = tk.BOTH, expand = True)
        # Tag configuration for clickable URLs
        self.chat_log.tag_config('link', foreground='blue', underline=True)

        # Frame for text bar input
        frame = tk.Frame(root)
        frame.pack(padx = 10, pady = (0, 10), fill = tk.X)

        # Text bar input
        self.entry = tk.Entry(frame)
        self.entry.focus()  # Automatically focus the input box after the username prompt.
        self.entry.pack(side = tk.LEFT, fill = tk.X, expand = True, padx = (0, 5))
        self.entry.bind("<Return>", self.send_message)

        # Send Button 
        button = tk.Button(frame, text = "Send", command = self.send_message)
        button.pack(side = tk.RIGHT)

        # Emoji Button
        emoji_button = tk.Button(frame, text="😊", command=self.show_emoji_picker)
        emoji_button.pack(side=tk.RIGHT, padx=5)

        # Threads
        self.running = True
        threading.Thread(target = self.receive_message, daemon = True).start()

        # Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    

    # Function: To output the emoji options
    def show_emoji_picker(self):

        emojis = list(self.emoji_dict.values())  # Get only emojis

        picker = tk.Toplevel(self.root)
        picker.title("Emoji Picker")
        # Set a fixed size (width x height in pixels)
        picker.geometry("300x100")  # Adjust as needed
        picker.resizable(False, False)  # Prevent resizing

        # Create a frame to hold the emoji buttons
        frame = tk.Frame(picker)
        frame.pack(pady=5, padx=5)

        # Use a grid layout for alignment (e.g., 4 columns)
        cols = 4  # Number of columns
        for i, emoji in enumerate(emojis):
            row = i // cols  # Calculate row number
            col = i % cols   # Calculate column number
            btn = tk.Button(frame, text=emoji, font=("Segoe UI Emoji", 14),
                            command=lambda e=emoji: self.insert_emoji(e),
                            width=2, height=1)  # Fixed button size
            btn.grid(row=row, column=col, padx=2, pady=2)

        picker.transient(self.root)  # Keep picker on top of main window
        picker.grab_set()  # Make it modal

    # Function
    def insert_emoji(self, emoji):
        self.entry.insert(tk.END, emoji)
        self.entry.focus()
    
    # Function: Prompts the user for a username. Closes the program if they dont enter
    def get_username(self):

        # Prompt for the username
        self.username = simpledialog.askstring("Username", "Enter a username", parent = self.root)

        # No username entered close the program
        if not self.username:
            self.root.quit()

        # Normal operations
        else:
            # Debug: make sure we process input correctly
            print(f"Username entered: {self.username}\n")
    
    # Function: Replaces the text input for the emojis. Must match dictionary definition
    def replace_shortcuts(self, msg):
        for shortcut, emoji in self.emoji_dict.items():
            msg = msg.replace(shortcut, emoji)
        return msg
    
    # Function: Sends the msg to the server. Iterates through for DMs
    def send_message(self, event=None):
            msg = self.entry.get().strip()
            print("Send message")
            if msg:
                try:
                    msg_with_emojis = self.replace_shortcuts(msg)
                    # Check if it's a direct message
                    if msg_with_emojis.startswith('@'):
                        # Extract recipient username (e.g., "@Ben" from "@Ben Hi")
                        match = re.match(r'@(\w+)\s*(.*)', msg_with_emojis)
                        if match:
                            recipient, content = match.groups()
                            # Format as DM with "DM:" prefix for server to recognize
                            full_msg = f"DM:{recipient}:{self.username}: {content}"
                            self.client_socket.send(full_msg.encode())
                            # Display locally as a DM
                            self.display_message("You (to " + recipient + ")", content, is_dm=True)
                        else:
                            self.display_message("System", "Invalid DM format. Use @username message")
                    else:
                        # Regular broadcast message
                        full_msg = f"{self.username}: {msg_with_emojis}"
                        self.client_socket.send(full_msg.encode())
                        self.display_message("You", msg_with_emojis)
                    
                    self.entry.delete(0, tk.END) # clears the text bar input
                except Exception as e:
                    print(f"Send message error: {e}")
                    self.display_message("System", f"Failed to send message {e}")
    
    # Function: 
    def receive_message(self):
        while self.running:
            try:
                msg = self.client_socket.recv(1024)
                if not msg:
                    break
                decoded_msg = msg.decode()
                print(f"Received message: {decoded_msg}")  # Debug to see what the server sends
                # Check if it's a DM
                if decoded_msg.startswith("DM:"):
                    _, sender, content = decoded_msg.split(":", 2)
                    print(f"DM from {sender} to {self.username}")  # Debug to check sender
                    # Skip displaying if this is the user's own DM
                    if sender == self.username:
                        print(f"Skipping display of own DM: {content}")  # Debug to confirm skip
                        continue
                    self.root.after(0, self.display_message, f"{sender} (DM)", content, True)
                else:
                    self.root.after(0, self.display_message, "", decoded_msg)
            except (ConnectionResetError, ConnectionAbortedError):
                self.root.after(0, self.display_message, "System", "[Connection lost to server]")
                self.root.after(0, self.show_server_terminated_message)
                break
        self.root.after(0, self.on_close)

    # Function: Shows server connection failure
    def show_server_terminated_message(self):
        """Display a message informing the user that the server has terminated."""
        messagebox.showerror("Server Error", "The server has disconnected unexpectedly. Closing the client.")
    
    # Function:
    def display_message(self, sender, msg, is_dm = False):
    # This method is only for updating the UI. No background thread calls here.
        self.root.after(0, self._display_message, sender, msg, is_dm)

    def _display_message(self, sender, msg, is_dm = False):

    # Now this is the actual UI update (running safely on the main thread)
        self.chat_log.config(state='normal')

        url_pattern = r"(http://[^\s]+|https://[^\s]+|www\.[^\s]+)"
        urls = re.findall(url_pattern, msg)


        if sender:
            tag = 'dm' if is_dm else None
            self.chat_log.insert(tk.END, f"{sender}: {msg}\n", tag)
            # self.chat_log.insert(tk.END, f"{msg}\n")
        else:
            self.chat_log.insert(tk.END, f"{msg}\n")

              # Now check for URLs and make them clickable
        for url in urls:
            self._insert_link(url)

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

#if __name__ == "__main__":
root = tk.Tk()
app = client(root)
root.geometry("680x700")
# root.resizable(False, False)
root.mainloop()


