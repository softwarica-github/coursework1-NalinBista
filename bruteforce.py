import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import requests
import threading
from queue import Queue, Empty
import random

# Initialize the root window
root = tk.Tk()
root.title("Directory Bruteforcer")

# Adjust these settings as needed
MAX_WORKERS = 10  # Concurrent threads

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
]

# Safe to create StringVar after initializing root window
filepath = tk.StringVar()  # To store the path of the selected wordlist

# Global flag for managing state
stop_requested = False

def select_wordlist():
    path = filedialog.askopenfilename()
    filepath.set(path)  # Store path in StringVar
    wordlist_path_label.config(text=f"Selected Wordlist: {path}")  # Update label with path

def stop_bruteforce():
    global stop_requested
    stop_requested = True
    messagebox.showinfo("Stop", "Stop requested. Waiting for current operations to finish...")

def task(directory, target_url, queue):
    if stop_requested:
        return
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        full_url = f"{target_url}/{directory}"
        response = requests.get(full_url, headers=headers, timeout=10)
        if response.status_code == 200:
            queue.put(('result', f"Found: {full_url}"))
        elif response.status_code == 403:
            queue.put(('result', f"Forbidden: {full_url}"))
    except requests.RequestException as e:
        queue.put(('result', f"Error accessing {full_url}: {e}"))

def bruteforce_thread(target_url, wordlist_path, queue):
    try:
        with open(wordlist_path, 'r') as file:
            directories = [line.strip() for line in file.readlines()]
    except Exception as e:
        queue.put(('error', f"Failed to read wordlist: {e}"))
        return

    queue.put(('max', len(directories)))

    for directory in directories:
        if stop_requested:
            break
        task(directory, target_url, queue)

    queue.put(('status', "Finished scanning."))

def start_bruteforce():
    target_url = url_entry.get().strip()
    wordlist_path = filepath.get()
    if not target_url or not wordlist_path:
        messagebox.showinfo("Error", "URL or Wordlist path is missing!")
        return
    clear_results()  # Clear previous results
    threading.Thread(target=bruteforce_thread, args=(target_url, wordlist_path, queue), daemon=True).start()

def clear_results():
    result_area.delete('1.0', tk.END)
    progress_bar['value'] = 0
    wordlist_path_label.config(text="Selected Wordlist: None")  # Reset label when cleared

def update_ui():
    try:
        while True:
            message_type, message = queue.get_nowait()
            if message_type == 'max':
                progress_bar['maximum'] = message
            elif message_type == 'result':
                result_area.insert(tk.END, f"{message}\n")
                progress_bar['value'] += 1
            elif message_type == 'status':
                result_area.insert(tk.END, f"{message}\n")
            elif message_type == 'error':
                messagebox.showerror("Error", message)
    except Empty:
        pass
    root.after(100, update_ui)

# GUI Setup
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tk.Label(frame, text="Target URL:").pack(side=tk.LEFT)
url_entry = tk.Entry(frame, width=50)
url_entry.pack(side=tk.LEFT, padx=5)

tk.Button(root, text="Select Wordlist", command=select_wordlist).pack(pady=5)
wordlist_path_label = tk.Label(root, text="Selected Wordlist: None")
wordlist_path_label.pack()

tk.Button(root, text="Start Bruteforce", command=start_bruteforce).pack(side=tk.LEFT, padx=2)
tk.Button(root, text="Stop", command=stop_bruteforce).pack(side=tk.LEFT, padx=2)
tk.Button(root, text="Clear", command=clear_results).pack(side=tk.LEFT, padx=2)

result_area = scrolledtext.ScrolledText(root, height=15, width=75)
result_area.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress_bar.pack(pady=20)

queue = Queue()
update_ui()  # Start the periodic UI update

root.mainloop()
