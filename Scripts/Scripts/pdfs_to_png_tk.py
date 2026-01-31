import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

selected_folder = None

def get_resource_path(filename):
    """
    Returns the path to bundled resource files so it works with Platypus or in development.
    """
    # For Platypus .app bundles, resources are inside the .app in Contents/Resources
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
        base_path = os.path.abspath(base_path)
    else:
        # When running as a normal script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

root = tk.Tk()
root.title("PDFs to PNGs Batch Converter")
root.configure(bg="white")
root.geometry("440x370")

# Display the logo at the top
logo_path = get_resource_path("TEA_Logo.png")
try:
    logo_img = Image.open(logo_path)
    logo_img = logo_img.resize((100, 100))
    logo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(root, image=logo, bg="white")
    logo_label.pack(pady=(18, 10))
except Exception as e:
    logo_label = tk.Label(root, text="TEA Logo Not Found", fg="red", bg="white")
    logo_label.pack(pady=8)

desc_label = tk.Label(root, text="Batch convert PDFs to PNGs (each in its own folder):",
                      bg="white", font=("Arial", 13))
desc_label.pack(pady=(0, 8))

folder_label = tk.Label(root, text="No folder selected.", wraplength=410, fg="blue",
                        bg="white", font=("Arial", 10, "bold"), justify="center")
folder_label.pack(pady=(0, 10))

def select_folder():
    global selected_folder
    folder = filedialog.askdirectory(title="Choose PDF Folder")
    if folder:
        selected_folder = folder
        folder_label.config(text=f"Selected folder:\n{selected_folder}")
        run_button.config(state=tk.NORMAL)
    else:
        folder_label.config(text="No folder selected.")
        run_button.config(state=tk.DISABLED)

def run_script():
    if not selected_folder:
        messagebox.showerror("Error", "Please select a folder first.")
        return
    script_path = get_resource_path("pdfs_to_png_folders.sh")
    if not os.path.exists(script_path):
        messagebox.showerror("Error", f"Script not found: {script_path}")
        return
    try:
        result = subprocess.run([script_path, selected_folder], capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo("Done!", f"PDF to PNG conversion complete!\n{result.stdout}")
        else:
            messagebox.showerror("Error", f"Script error:\n{result.stderr}")
    except Exception as e:
        messagebox.showerror("Exception", str(e))

select_button = tk.Button(root, text="Select PDF Folder", command=select_folder,
                         bg="#f5f5f5", font=("Arial", 11, "bold"))
select_button.pack(pady=7)

run_button = tk.Button(root, text="Run Conversion", command=run_script,
                      state=tk.DISABLED, bg="#e0e0e0", font=("Arial", 11, "bold"))
run_button.pack(pady=5)

# --- About menu functionality ---
def show_about():
    readme_path = get_resource_path("README.txt")
    if os.path.exists(readme_path):
        with open(readme_path, "r") as f:
            about_text = f.read()
    else:
        about_text = "README.txt not found."
    about_win = tk.Toplevel(root)
    about_win.title("About PDFs to PNGs")
    about_win.configure(bg="white")
    text = tk.Text(about_win, wrap="word", width=60, height=20, bg="white", font=("Arial", 10))
    text.insert("1.0", about_text)
    text.config(state="disabled")
    text.pack(padx=12, pady=12)
    about_win.transient(root)
    about_win.grab_set()
    about_win.focus()

# Add an "About" menu
menubar = tk.Menu(root)
help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menubar.add_cascade(label="Help", menu=help_menu)
root.config(menu=menubar)

root.mainloop()
