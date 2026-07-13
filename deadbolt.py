import os
import tkinter as tk
from tkinter import messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import SHA256, Hash
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

MAGIC_BYTES = b"PPFN"

def derive_keys(password: str, salt: bytes):
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=64,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    key_material = kdf.derive(password.encode('utf-8'))
    enc_key = key_material[:32]
    mac_key = key_material[32:]
    return enc_key, mac_key

def generate_verifier(password: str, salt: bytes):
    digest = Hash(SHA256(), backend=default_backend())
    digest.update(password.encode('utf-8') + salt)
    return digest.finalize()

class DeadboltApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DEADBOLT")
        self.root.geometry("750x420")
        self.root.resizable(False, False)

        try:
            icon_img = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "logo.png"))
            self.root.iconphoto(True, icon_img)
        except Exception:
            pass

        self.selected_file_path = ""
        self.current_dir = os.getcwd()
        
        self.configure_styles()
        self.create_widgets()
        self.refresh_file_list()
        
    def configure_styles(self):
        self.root.configure(bg="#0E1717")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure("TFrame", background="#0E1717")
        self.style.configure("Panel.TFrame", background="#132222")
        
        self.style.configure("TLabel", background="#0E1717", foreground="#A0C2C2", font=("Helvetica", 10))
        self.style.configure("Panel.TLabel", background="#132222", foreground="#A0C2C2", font=("Helvetica", 10))
        self.style.configure("Title.TLabel", background="#0E1717", font=("Helvetica", 16, "bold"), foreground="#00F0FF")
        self.style.configure("Dir.TLabel", background="#132222", font=("Helvetica", 9, "italic"), foreground="#00A3B0")
        
        self.style.configure("TEntry", fieldbackground="#1A2E2E", foreground="#FFFFFF", bordercolor="#004D52", lightcolor="#004D52")
        self.style.map("TEntry", fieldbackground=[('focus', '#203A3A')])
        
        self.style.configure("Action.TButton", font=("Helvetica", 10, "bold"), background="#1A2E2E", foreground="#00F0FF", bordercolor="#00666D")
        self.style.map("Action.TButton", background=[('active', '#004D52'), ('disabled', '#0B1313')], foreground=[('disabled', '#335252')])
        
        self.style.configure("Treeview", background="#162626", fieldbackground="#162626", foreground="#E0F2F2", bordercolor="#004D52", rowheight=24)
        self.style.map("Treeview", background=[('selected', '#004D52')], foreground=[('selected', '#FFFFFF')])
        self.style.configure("Treeview.Heading", background="#1A2E2E", foreground="#00F0FF", bordercolor="#004D52", font=("Helvetica", 9, "bold"))

    def create_widgets(self):
        split_container = ttk.Frame(self.root)
        split_container.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(split_container, padding="15", style="Panel.TFrame")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.dir_label = ttk.Label(left_panel, text=self.current_dir, style="Dir.TLabel", anchor="w")
        self.dir_label.pack(fill=tk.X, pady=(0, 5))
        
        columns = ('name', 'type')
        self.file_tree = ttk.Treeview(left_panel, columns=columns, show='headings', selectmode='browse')
        self.file_tree.heading('name', text='File Name', anchor='w')
        self.file_tree.heading('type', text='Type', anchor='w')
        self.file_tree.column('name', width=240, anchor='w')
        self.file_tree.column('type', width=80, anchor='w')
        self.file_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.file_tree.bind('<<TreeviewSelect>>', self.handle_tree_select)
        self.file_tree.bind('<Double-1>', self.handle_tree_double_click)
        
        nav_btn_frame = ttk.Frame(left_panel, style="Panel.TFrame")
        nav_btn_frame.pack(fill=tk.X)
        
        up_btn = ttk.Button(nav_btn_frame, text="Back", style="Action.TButton", command=self.go_up_dir)
        up_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        refresh_btn = ttk.Button(nav_btn_frame, text="Refresh", style="Action.TButton", command=self.refresh_file_list)
        refresh_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        right_panel = ttk.Frame(split_container, padding="20", width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_panel.pack_propagate(False)
        
        title_label = ttk.Label(right_panel, text="Deadbolt by 'Null'", style="Title.TLabel")
        title_label.pack(pady=(0, 15), anchor="w")
        
        self.drop_zone = tk.Label(
            right_panel, 
            text="Drag & Drop Target", 
            bg="#162626", 
            fg="#00A3B0", 
            font=("Helvetica", 10),
            bd=1, 
            relief="solid",
            highlightthickness=0
        )
        self.drop_zone.pack(fill=tk.X, ipady=20, pady=(0, 15))
        
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.handle_drop)
        
        pass_label = ttk.Label(right_panel, text="Please enter a password:")
        pass_label.pack(pady=(0, 5), anchor="w")
        
        self.pass_entry = ttk.Entry(right_panel, show="*", width=30)
        self.pass_entry.pack(fill=tk.X, pady=(0, 20))
        
        self.lock_btn = ttk.Button(right_panel, text="Lock File (.ppfbn)", style="Action.TButton", command=self.lock_file, state=tk.DISABLED)
        self.lock_btn.pack(fill=tk.X, pady=(0, 10))
        
        self.unlock_btn = ttk.Button(right_panel, text="Unlock File", style="Action.TButton", command=self.unlock_file, state=tk.DISABLED)
        self.unlock_btn.pack(fill=tk.X)

    def refresh_file_list(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.dir_label.config(text=self.current_dir)
        
        try:
            for entry in os.scandir(self.current_dir):
                if entry.is_dir():
                    self.file_tree.insert('', tk.END, values=(entry.name, 'Folder'))
                elif entry.is_file():
                    self.file_tree.insert('', tk.END, values=(entry.name, 'File'))
        except Exception as e:
            messagebox.showerror("Error", f"Could not read directory: {str(e)}")

    def go_up_dir(self):
        parent_dir = os.path.dirname(self.current_dir)
        if parent_dir != self.current_dir:
            self.current_dir = parent_dir
            self.refresh_file_list()

    def handle_tree_select(self, event):
        selected_item = self.file_tree.selection()
        if not selected_item:
            return
        values = self.file_tree.item(selected_item, 'values')
        if values and values[1] == 'File':
            full_path = os.path.join(self.current_dir, values[0])
            self.update_file_selection(full_path)

    def handle_tree_double_click(self, event):
        selected_item = self.file_tree.selection()
        if not selected_item:
            return
        values = self.file_tree.item(selected_item, 'values')
        if values and values[1] == 'Folder':
            self.current_dir = os.path.join(self.current_dir, values[0])
            self.refresh_file_list()

    def handle_drop(self, event):
        file_path = event.data.strip('{}')
        if os.path.isfile(file_path):
            self.update_file_selection(file_path)

    def update_file_selection(self, file_path):
        self.selected_file_path = file_path
        display_name = os.path.basename(file_path)
        self.drop_zone.config(text=display_name, fg="#00FFC2", bg="#0D3A3A")
        self.lock_btn.config(state=tk.NORMAL)
        self.unlock_btn.config(state=tk.NORMAL)

    def lock_file(self):
        password = self.pass_entry.get()
        if not password:
            messagebox.showerror("Error", "You need to create a password for this file!")
            return
            
        try:
            with open(self.selected_file_path, "rb") as f:
                raw_content = f.read()

            base_path, original_ext = os.path.splitext(self.selected_file_path)
            output_filepath = base_path + ".ppfbn"

            salt = os.urandom(16)
            iv = os.urandom(16)
            
            verifier = generate_verifier(password, salt)
            enc_key, mac_key = derive_keys(password, salt)
            
            ext_bytes = original_ext.encode('utf-8')
            ext_len = len(ext_bytes)
            
            payload_to_encrypt = bytes([ext_len]) + ext_bytes + raw_content
            
            padding_length = 16 - (len(payload_to_encrypt) % 16)
            padded_data = payload_to_encrypt + bytes([padding_length] * padding_length)
            
            cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_payload = encryptor.update(padded_data) + encryptor.finalize()
            
            hmac_obj = HMAC(mac_key, SHA256(), backend=default_backend())
            hmac_obj.update(iv + encrypted_payload)
            hmac_tag = hmac_obj.finalize()
            
            with open(output_filepath, "wb") as f:
                f.write(MAGIC_BYTES)
                f.write(salt)
                f.write(verifier)
                f.write(iv)
                f.write(hmac_tag)
                f.write(encrypted_payload)
                
            messagebox.showinfo("Success", f"File locked successfully!\nSaved as: {os.path.basename(output_filepath)}")
            self.reset_ui()
            self.refresh_file_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to lock file: {str(e)}")

    def unlock_file(self):
        password = self.pass_entry.get()
        if not password:
            messagebox.showerror("Error", "The point of this is to enter a password, sherlock")
            return
            
        try:
            with open(self.selected_file_path, "rb") as f:
                file_magic = f.read(4)
                if file_magic != MAGIC_BYTES:
                    messagebox.showerror("Error", "I don't think this is a .ppfbn file.")
                    return
                    
                salt = f.read(16)
                file_verifier = f.read(32)
                iv = f.read(16)
                file_hmac_tag = f.read(32)
                encrypted_payload = f.read()
                
            computed_verifier = generate_verifier(password, salt)
            if computed_verifier != file_verifier:
                messagebox.showerror("Error", "Wrong password! Double check and try again.")
                return
                
            enc_key, mac_key = derive_keys(password, salt)
            
            try:
                hmac_obj = HMAC(mac_key, SHA256(), backend=default_backend())
                hmac_obj.update(iv + encrypted_payload)
                hmac_obj.verify(file_hmac_tag)
            except Exception:
                messagebox.showerror("Error", "The password is correct, but the file seems to have been modified or corrupted.")
                return
                
            cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_payload) + decryptor.finalize()
            
            padding_length = padded_data[-1]
            unpadded_data = padded_data[:-padding_length]
            
            ext_len = unpadded_data[0]
            original_ext = unpadded_data[1:1+ext_len].decode('utf-8')
            original_binary_data = unpadded_data[1+ext_len:]
            
            base_path, _ = os.path.splitext(self.selected_file_path)
            output_filepath = base_path + "_decrypted" + original_ext
            
            with open(output_filepath, "wb") as f:
                f.write(original_binary_data)
                
            messagebox.showinfo("Success", f"File unlocked successfully!\nSaved as: {os.path.basename(output_filepath)}")
            self.reset_ui()
            self.refresh_file_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unlock file: {str(e)}")

    def reset_ui(self):
        self.selected_file_path = ""
        self.pass_entry.delete(0, tk.END)
        self.drop_zone.config(text="Drag & Drop Target", fg="#00A3B0", bg="#162626")
        self.lock_btn.config(state=tk.DISABLED)
        self.unlock_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = DeadboltApp(root)
    root.mainloop()
