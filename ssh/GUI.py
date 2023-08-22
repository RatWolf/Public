import tkinter as tk, os, sys, threading, time, psutil, configparser, subprocess, threading
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

ssh_process = None
ssh_active = False
ssh_command = []
port_bindings_entries = []
use_line_checkboxes = []
Pfad = os.path.dirname(sys.argv[0])

def add_port_row():
    row_index = len(port_bindings_entries)

    use_line_var = tk.BooleanVar()
    use_line_checkbox = ttk.Checkbutton(lower_frame, variable=use_line_var)
    use_line_checkbox.grid(row=row_index + 1, column=0, padx=5, pady=2, sticky=tk.W)
    use_line_checkboxes.append(use_line_var)

    entries = [ttk.Entry(lower_frame) for _ in range(3)]
    for i, entry in enumerate(entries):
        entry.grid(row=row_index + 1, column=i + 1, padx=5, pady=2, sticky=tk.W)
    port_bindings_entries.append(entries)

    add_port_row_button.grid(row=row_index + 2, column=0, columnspan=1, padx=5, pady=2, sticky=tk.W)
    execute_button.grid(row=row_index + 2, column=2, columnspan=1, padx=5, pady=2, sticky=tk.W)
    save_button.grid(row=row_index + 2, column=3, padx=5, pady=10, sticky=tk.E)
    load_button.grid(row=row_index + 3, column=3, padx=5, pady=10, sticky=tk.E)

def on_closing():
    if messagebox.askyesno("Speichern", "Sollen die änderungen gespeichert werden?"):
        save_to_ini(os.path.join(Pfad, 'config.ini'))
    app.destroy()

def check_ssh_process_status():
    global execute_button, ssh_active, ssh_process
    while True:
        ssh_processes = [p for p in psutil.process_iter(attrs=['pid', 'name']) if 'ssh' in p.info['name']]
        if ssh_processes:
            ssh_active = True
            ssh_process = ssh_processes[0]
            execute_button.config(text="...Executing...")
        else:
            ssh_active =False
            ssh_process = None
            execute_button.config(text="Execute SSH")
        time.sleep(5)

def save_settings():
    save_path = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("INI Files", "*.ini")])
    if save_path:
        save_to_ini(save_path)

def save_to_ini(filename):
    config = configparser.ConfigParser()

    config['General'] = {
        'SchluesseldateiPfad': schluesseldatei_entry.get(),
        'SSHPort': ssh_port_entry.get(),
        'Host': host_entry.get(),
        'SSHUser': ssh_user_entry.get(),
        'NumPortRows': len(port_bindings_entries)
    }

    for i, entries in enumerate(port_bindings_entries):
        section_name = f'PortRow_{i}'
        config[section_name] = {
            'UseLine': use_line_checkboxes[i].get(),
            'LocalPort': entries[0].get(),
            'TargetAddress': entries[1].get(),
            'TargetPort': entries[2].get()
        }

    if filename:
        with open(filename, 'w') as config_file:
            config.write(config_file)

def load_settings():
    file_path = filedialog.askopenfilename(filetypes=[("INI Files", "*.ini")])
    if file_path:
        load_from_ini(file_path)

def load_from_ini(filename):
    clear_fields()
    
    if os.path.exists(filename):
        config = configparser.ConfigParser()
        config.read(filename)

        schluesseldatei_entry.insert(0, config['General']['SchluesseldateiPfad'])
        ssh_port_entry.insert(0, config['General']['SSHPort'])
        host_entry.insert(0, config['General']['Host'])
        ssh_user_entry.insert(0, config['General']['SSHUser'])

        num_rows = int(config['General']['NumPortRows'])
        
        num_new_rows = num_rows - len(port_bindings_entries)
        for _ in range(num_new_rows):
            add_port_row()

        for i in range(num_rows):
            use_line_checkboxes[i].set(config[f'PortRow_{i}']['UseLine'])
            if len(port_bindings_entries) > i:
                port_bindings_entries[i][0].insert(0, config[f'PortRow_{i}']['LocalPort'])
                port_bindings_entries[i][1].insert(0, config[f'PortRow_{i}']['TargetAddress'])
                port_bindings_entries[i][2].insert(0, config[f'PortRow_{i}']['TargetPort'])

def clear_fields():
    schluesseldatei_entry.delete(0, tk.END)
    ssh_port_entry.delete(0, tk.END)
    host_entry.delete(0, tk.END)
    ssh_user_entry.delete(0, tk.END)
    for entries in port_bindings_entries:
        for entry in entries:
            entry.delete(0, tk.END)

def select_keyfile():
    file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
    if not os.path.splitext(file_path)[1]:
        schluesseldatei_entry.delete(0, tk.END)
        schluesseldatei_entry.insert(0, file_path)

def execute_ssh():
    ssh_thread = threading.Thread(target=ssh_thread_func)
    ssh_thread.start()

    ssh_output = subprocess.PIPE
    ssh_process = subprocess.Popen(ssh_command, stdout=ssh_output, stderr=ssh_output, text=True)

    stdout, stderr = ssh_process.communicate()

    if "UNPROTECTED PRIVATE KEY FILE" in stderr:
        messagebox.showwarning("Warning", "Unprotected private key file!")
    elif ssh_process.returncode != 0:
        messagebox.showerror("Error", "SSH command failed!")

def ssh_thread_func():
    global ssh_process

    schluesseldatei_pfad = schluesseldatei_entry.get()
    ssh_port = ssh_port_entry.get()
    host = host_entry.get()
    ssh_user = ssh_user_entry.get()

    port_bindings = []
    for i in range(len(port_bindings_entries)):
        use_line = use_line_checkboxes[i].get()
        if use_line:
            local_port = port_bindings_entries[i][0].get()
            target_address = port_bindings_entries[i][1].get()
            target_port = port_bindings_entries[i][2].get()
            if local_port and target_address and target_port:
                port_bindings.append((local_port, target_address, target_port))
            else:
                print(f"Skipping line {i+1} due to missing values.")

    ssh_command = [
        'ssh',
        '-i', schluesseldatei_pfad,
        '-p', ssh_port,
        '-f',  # Führe im Hintergrund aus
        '-N',  # Kein Kommando ausführen
    ]

    for local_port, target_address, target_port in port_bindings:
        ssh_command.extend([
            '-L', f'{local_port}:{target_address}:{target_port}'
        ])

    ssh_command.append(f'{ssh_user}@{host}')
    ssh_process = subprocess.Popen(ssh_command)
    print(ssh_command)

def toggle_ssh_button():
    global ssh_active, ssh_process

    if ssh_active:
        execute_button.config(text="End...")

        if ssh_process:
            stop_ssh_tunnel()
            ssh_active = False
        execute_button.config(text="Execute SSH")
    else:
        ssh_active = True
        execute_button.config(text="Executing...")
        execute_ssh()
        execute_button.config(text="Execution!")

def stop_ssh_tunnel():
    global ssh_process
    if ssh_process:
        ssh_process.terminate()
        ssh_process.wait()
        ssh_process = None

app = tk.Tk()
app.title("SSH-Tunnel-GUI")
app.style = ttk.Style()
icon = Image.open(os.path.join(Pfad,"ssh.ico"))
app.iconphoto(True, ImageTk.PhotoImage(icon))

app.style.configure("Upper.TFrame", background="#FFFFFF")
app.style.configure("Inner.TFrame", background="#FFFFFF")
app.style.configure("Transparent.TLabel", background="#FFFFFF")

upper_frame = ttk.Frame(app)
lower_frame = ttk.Frame(app)
inner_frame = ttk.Frame(upper_frame)

upper_frame.grid_columnconfigure(0, weight=1)
inner_frame.grid_columnconfigure(0, weight=1)
lower_frame.grid_columnconfigure(0, weight=1)

upper_frame.configure(style="Upper.TFrame")
inner_frame.configure(style="Inner.TFrame")

upper_frame.grid(row=0, column=0, padx=10, pady=10, columnspan=4)
inner_frame.grid(row=0, column=0, padx=10, pady=10)
lower_frame.grid(row=1, column=0, padx=10, pady=10, columnspan=4)

schluesseldatei_label = ttk.Label(inner_frame, text="Schlüsseldatei Pfad:", style="Transparent.TLabel")
schluesseldatei_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
schluesseldatei_entry = ttk.Entry(inner_frame)
schluesseldatei_entry.grid(row=0, column=1, sticky=tk.W)
schluesseldatei_button = ttk.Button(inner_frame, text="Auswählen", command=select_keyfile) #, style="Transparent.TLabel")
schluesseldatei_button.grid(row=0, column=2, sticky=tk.W)

ssh_port_label = ttk.Label(inner_frame, text="SSH Port:", style="Transparent.TLabel")
ssh_port_label.grid(row=1, column=0, sticky=tk.W)
ssh_port_entry = ttk.Entry(inner_frame)
ssh_port_entry.grid(row=1, column=1, sticky=tk.W)

host_label = ttk.Label(inner_frame, text="Host:", style="Transparent.TLabel")
host_label.grid(row=2, column=0, sticky=tk.W)
host_entry = ttk.Entry(inner_frame)
host_entry.grid(row=2, column=1, sticky=tk.W)

ssh_user_label = ttk.Label(inner_frame, text="SSH User:", style="Transparent.TLabel")
ssh_user_label.grid(row=3, column=0, sticky=tk.W)
ssh_user_entry = ttk.Entry(inner_frame)
ssh_user_entry.grid(row=3, column=1, sticky=tk.W)

bind_use_label = ttk.Label(lower_frame, text="Use")
bind_use_label.grid(row=0, column=0, sticky=tk.W)
bind_use_label = ttk.Label(lower_frame, text="Lokaler Port")
bind_use_label.grid(row=0, column=1)
bind_use_label = ttk.Label(lower_frame, text="Ziel Address")
bind_use_label.grid(row=0, column=2)
bind_use_label = ttk.Label(lower_frame, text="Ziel Port")
bind_use_label.grid(row=0, column=3)

add_port_row_button = ttk.Button(lower_frame, text="+", command=add_port_row)
execute_button = ttk.Button(lower_frame, text="Execute SSH", command=toggle_ssh_button)
save_button = ttk.Button(lower_frame, text="Save Settings", command=save_settings)
load_button = ttk.Button(lower_frame, text="Load Settings", command=load_settings)

add_port_row_button.config(width=len(add_port_row_button["text"]))

ssh_status_thread = threading.Thread(target=check_ssh_process_status)
ssh_status_thread.daemon = True
ssh_status_thread.start()

add_port_row()
load_from_ini(os.path.join(Pfad, 'config.ini'))
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()