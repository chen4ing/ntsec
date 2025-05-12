import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import sys
import traceback

# Add the directory of index.py to sys.path to allow importing
# This assumes gui.py and index.py are in the same directory.
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

try:
    import index as ntsec_processor
except ImportError:
    messagebox.showerror("Error", "Could not import index.py. Make sure it's in the same directory as gui.py or in your PYTHONPATH.")
    sys.exit(1)

class TranslationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Translation Parameter Adjuster")

        # Initial translation values from your selection
        self.translations_vars = [
            tk.DoubleVar(value=-7.5), tk.DoubleVar(value=-3.7),
            tk.DoubleVar(value=7.5), tk.DoubleVar(value=0.0),
            tk.DoubleVar(value=7.5), tk.DoubleVar(value=0.0),
            tk.DoubleVar(value=-7.5), tk.DoubleVar(value=0.0)
        ]
        self.steps_vars = [tk.DoubleVar(value=0.1) for _ in range(8)]

        self.param_frame = ttk.LabelFrame(master, text="Translation Parameters (Sensor X, Y)")
        self.param_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        param_labels = ["S1_X", "S1_Y", "S2_X", "S2_Y", "S3_X", "S3_Y", "S4_X", "S4_Y"]
        self.entries = []
        self.step_entries = []

        for i in range(8):
            # Determine row and column for grid layout
            # Each sensor pair (X,Y) gets a conceptual row in the UI, 
            # but parameters are laid out horizontally.
            # 4 sensors, 2 params (X,Y) each. We can do 4 rows in the grid for sensors.
            # X params in one set of columns, Y in another.
            sensor_idx_for_label = i // 2 
            coord_label_text = param_labels[i] # "S1_X", "S1_Y", etc.

            # Layout: Label | Entry | Up | Down | StepLabel | StepEntry
            current_row_ui = i 
            
            ttk.Label(self.param_frame, text=f"{coord_label_text}:").grid(row=current_row_ui, column=0, padx=5, pady=3, sticky="w")
            
            entry = ttk.Entry(self.param_frame, textvariable=self.translations_vars[i], width=8)
            entry.grid(row=current_row_ui, column=1, padx=2, pady=3)
            self.entries.append(entry)

            up_button = ttk.Button(self.param_frame, text="▲", width=2, command=lambda i=i: self.adjust_value(i, 1))
            up_button.grid(row=current_row_ui, column=2, padx=(0,1), pady=3, sticky="w")
            
            down_button = ttk.Button(self.param_frame, text="▼", width=2, command=lambda i=i: self.adjust_value(i, -1))
            down_button.grid(row=current_row_ui, column=3, padx=(0,5), pady=3, sticky="w")

            ttk.Label(self.param_frame, text="Step:").grid(row=current_row_ui, column=4, padx=(5,0), pady=3, sticky="e")
            step_entry = ttk.Entry(self.param_frame, textvariable=self.steps_vars[i], width=6)
            step_entry.grid(row=current_row_ui, column=5, padx=(2,5), pady=3, sticky="w")
            self.step_entries.append(step_entry)

        self.controls_frame = ttk.Frame(master)
        self.controls_frame.grid(row=1, column=0, padx=10, pady=(5,10), sticky="ew")

        # REMOVE Checkbutton for "Process only first .chan file"
        # self.process_first_var = tk.BooleanVar(value=True)
        # self.process_first_check = ttk.Checkbutton(self.controls_frame, text="Process only first .chan file", variable=self.process_first_var)
        # self.process_first_check.pack(side=tk.LEFT, padx=5)

        # ADD Combobox for file selection
        self.file_selection_label = ttk.Label(self.controls_frame, text="File to Process:")
        self.file_selection_label.pack(side=tk.LEFT, padx=(5, 2))
        
        self.file_selection_var = tk.StringVar()
        self.file_selection_combo = ttk.Combobox(self.controls_frame, textvariable=self.file_selection_var, width=30)
        self.file_selection_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.populate_file_selection_dropdown() # Populate with .chan files

        self.process_button = ttk.Button(self.controls_frame, text="Process and View", command=self.process_data)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        self.input_dir_label = ttk.Label(self.controls_frame, text=f"Input Dir: {os.path.abspath(script_dir)}") # Use script_dir
        self.input_dir_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.image_frame = ttk.LabelFrame(master, text="Output Image")
        self.image_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        self.image_label = ttk.Label(self.image_frame) # Will hold the image
        self.image_label.pack(padx=5, pady=5, expand=True, fill="both")

        # Configure resizing behavior
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1) # Make label inside frame expand
        self.image_frame.grid_columnconfigure(0, weight=1)


    def adjust_value(self, index, direction):
        current_val = self.translations_vars[index].get()
        step_val = self.steps_vars[index].get()
        try:
            new_val = round(current_val + (direction * step_val), 4) # Round to 4 decimal places
            self.translations_vars[index].set(new_val)
        except tk.TclError: # Handles case where step_val might be non-numeric temporarily
            messagebox.showwarning("Input Error", "Please ensure step value is a valid number.")

    def populate_file_selection_dropdown(self):
        input_chan_dir = script_dir # Or os.path.abspath('.')
        try:
            chan_files = sorted([f for f in os.listdir(input_chan_dir) if f.endswith(".chan")])
        except FileNotFoundError:
            chan_files = []
            messagebox.showwarning("Directory Not Found", f"Input directory for .chan files not found: {input_chan_dir}")

        options = ["Process first .chan file", "Process all .chan files"] + chan_files
        self.file_selection_combo['values'] = options
        if options:
            self.file_selection_combo.current(0) # Default to "Process first"

    def process_data(self):
        current_translations_flat = []
        try:
            for var in self.translations_vars:
                current_translations_flat.append(var.get())
        except tk.TclError:
             messagebox.showerror("Input Error", "Invalid character in translation values. Please use numbers.")
             return

        current_translations_paired = []
        for i in range(0, 8, 2):
            current_translations_paired.append((current_translations_flat[i], current_translations_flat[i+1]))

        # process_first = self.process_first_var.get() # Old logic
        selected_option_str = self.file_selection_var.get()
        
        # Determine the actual parameter for run_processing_for_gui
        if selected_option_str == "Process first .chan file":
            actual_file_selection = "__FIRST__"
        elif selected_option_str == "Process all .chan files":
            actual_file_selection = "__ALL__"
        elif selected_option_str.endswith(".chan"): # A specific file is selected
            actual_file_selection = selected_option_str
        else:
            messagebox.showerror("Selection Error", "Invalid file selection. Please select an option from the dropdown.")
            return
        
        gui_output_dir = os.path.join(script_dir, "output_pngs_gui") 
        os.makedirs(gui_output_dir, exist_ok=True)
        
        input_chan_dir = script_dir 

        try:
            self.master.config(cursor="watch") 
            self.master.update_idletasks()

            image_path = ntsec_processor.run_processing_for_gui(
                translations=current_translations_paired,
                # process_first_file=process_first, # Old parameter
                selected_file_option=actual_file_selection, # New parameter
                output_directory=gui_output_dir,
                input_directory=input_chan_dir 
            )
            
            self.master.config(cursor="")

            if image_path and os.path.exists(image_path):
                self.display_image(image_path)
                # No success messagebox needed if image is displayed.
                # messagebox.showinfo("Success", f"Image generated: {os.path.basename(image_path)}")
            elif image_path: # Path returned but file not found
                 messagebox.showerror("Error", f"Processing completed, but image not found at: {image_path}")
            else: 
                messagebox.showwarning("Processing Incomplete", "No image was generated. Check if .chan files exist in the input directory or if there were other errors (see console).")

        except AttributeError as e:
            self.master.config(cursor="")
            messagebox.showerror("Error", f"Function 'run_processing_for_gui' not found in index.py or an error occurred within it: {e}. Please ensure index.py is correctly modified.")
            print(traceback.format_exc())
        except Exception as e:
            self.master.config(cursor="")
            messagebox.showerror("Processing Error", f"An unexpected error occurred: {str(e)}")
            print(traceback.format_exc())

    def display_image(self, image_path):
        try:
            img = Image.open(image_path)
            
            # Get the actual size of the label frame for resizing
            # This needs to happen after the window is drawn and sized.
            # Using a fixed max size initially, then trying to adapt.
            # For robust resizing, one might need to bind to <Configure> event of image_frame.
            
            # Simple approach: scale to fit within a max dimension, or image_label's current size
            container_width = self.image_label.winfo_width()
            container_height = self.image_label.winfo_height()

            if container_width < 2 or container_height < 2: # Min size before fully drawn
                container_width = 600 # Default max width
                container_height = 400 # Default max height
            
            img_copy = img.copy() # Work on a copy
            img_copy.thumbnail((container_width - 10, container_height - 10), Image.Resampling.LANCZOS) # -10 for some padding
            
            photo = ImageTk.PhotoImage(img_copy)
            self.image_label.config(image=photo, text="") # Clear any previous text
            self.image_label.image = photo # Keep a reference!
        except FileNotFoundError:
            self.image_label.config(image=None, text=f"Error: Image not found at\n{image_path}")
            self.image_label.image = None
        except Exception as e:
            self.image_label.config(image=None, text=f"Error displaying image:\n{str(e)}")
            self.image_label.image = None
            messagebox.showerror("Image Display Error", f"Could not display image {os.path.basename(image_path)}: {str(e)}")


if __name__ == '__main__':
    root = tk.Tk()
    gui = TranslationGUI(root)
    root.mainloop()