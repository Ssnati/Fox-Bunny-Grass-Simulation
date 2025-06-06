import tkinter as tk
from tkinter import ttk
import json
import os

class ConfigWindow:
    def __init__(self, default_params):
        self.root = tk.Tk()
        self.root.title("Configuración de la Simulación")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        self.params = default_params.copy()
        self.entries = {}
        
        # Estilo
        style = ttk.Style()
        style.configure('TLabel', padding=5, font=('Arial', 10))
        style.configure('TEntry', padding=5)
        style.configure('TButton', padding=5)
        
        # Estilos personalizados para botones
        style.configure('Start.TButton',
                      background='#e8f5e9',  # Verde muy suave
                      foreground='black',  # Texto negro
                      font=('Arial', 10, 'bold'),
                      padding=10)  # Añadir padding para mejor apariencia
                      
        style.configure('Exit.TButton',
                      background='#ffebee',  # Rojo muy suave
                      foreground='black',  # Texto negro
                      font=('Arial', 10, 'bold'),
                      padding=10)  # Añadir padding para mejor apariencia
                      
        style.map('Start.TButton',
                background=[('active', '#c8e6c9')])  # Verde un poco más oscuro al pasar el ratón
                
        style.map('Exit.TButton',
                background=[('active', '#ffcdd2')])  # Rojo un poco más oscuro al pasar el ratón
                
        style.configure('Error.TEntry', fieldbackground='#ffdddd')
        
        # Frame principal con scroll
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas y scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Título
        title_label = ttk.Label(
            self.scrollable_frame,
            text="Configuración de la Simulación",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Crear campos de entrada
        self.create_input_fields()
        
        # Frame para los botones
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill=tk.X, pady=(20, 10), padx=10)
        
        # Frame para alinear botones a la derecha
        right_frame = ttk.Frame(button_frame)
        right_frame.pack(side=tk.RIGHT, expand=True)
        
        # Botón de iniciar simulación (derecha)
        save_btn = ttk.Button(
            right_frame,
            text="Iniciar Simulación",
            command=self.on_save,
            style='Start.TButton',
            width=20
        )
        save_btn.pack(side=tk.RIGHT, padx=(100, 0))
        
        # Botón de salir (izquierda)
        exit_btn = ttk.Button(
            right_frame,
            text="Salir",
            command=self.on_close,
            style='Exit.TButton',
            width=10
        )
        exit_btn.pack(side=tk.LEFT)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Hacer que la rueda del mouse funcione
        self.root.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Enfocar la ventana
        self.root.focus_force()
        
        # Cargar configuración guardada si existe
        self.load_config()
    
    def create_input_fields(self):
        # Configuración de los campos
        fields = [
            ("Conejos iniciales:", "initial_rabbits", "int", (1, 1000)),
            ("Zorros iniciales:", "initial_foxes", "int", (1, 200)),
            ("Comida inicial:", "initial_food", "int", (10, 1000)),
            ("Velocidad conejos:", "rabbit_speed", "float", (0.1, 10.0)),
            ("Velocidad zorros:", "fox_speed", "float", (0.1, 15.0)),
            ("Tasa de comida:", "food_respawn_rate", "int", (1, 20)),
            ("Máx. conejos:", "max_rabbits", "int", (10, 2000)),
            ("Máx. zorros:", "max_foxes", "int", (1, 500))
        ]
        
        for label_text, param_name, param_type, (min_val, max_val) in fields:
            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(fill=tk.X, pady=5)
            
            label = ttk.Label(frame, text=label_text, width=20, anchor='e')
            label.pack(side=tk.LEFT, padx=5)
            
            if param_type == "int":
                validate_cmd = (frame.register(self.validate_int), '%P', str(min_val), str(max_val))
                entry = ttk.Entry(frame, validate="key")
                entry.configure(validatecommand=validate_cmd)
            else:  # float
                validate_cmd = (frame.register(self.validate_float), '%P', str(min_val), str(max_val))
                entry = ttk.Entry(frame, validate="key")
                entry.configure(validatecommand=validate_cmd)
            
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            entry.insert(0, str(self.params[param_name]))
            
            # Añadir tooltip con el rango permitido
            tooltip = f"Rango: {min_val} - {max_val}"
            self.create_tooltip(entry, tooltip)
            
            self.entries[param_name] = (entry, param_type)
    
    @staticmethod
    def validate_int(value, min_val, max_val):
        if value == "":
            return True
        try:
            min_val = int(min_val)
            max_val = int(max_val)
            num = int(value)
            return min_val <= num <= max_val
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_float(value, min_val, max_val):
        if value == "" or value == ".":
            return True
        try:
            min_val = float(min_val)
            max_val = float(max_val)
            num = float(value)
            return min_val <= num <= max_val
        except (ValueError, TypeError):
            return False
    
    def create_tooltip(self, widget, text):
        tooltip = None
        
        def enter(event):
            nonlocal tooltip
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                padding=5
            )
            label.pack()
        
        def leave(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
    
    def load_config(self):
        config_file = "simulation_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    saved_params = json.load(f)
                
                for param_name, (entry, _) in self.entries.items():
                    if param_name in saved_params:
                        entry.delete(0, tk.END)
                        entry.insert(0, str(saved_params[param_name]))
                        self.params[param_name] = saved_params[param_name]
            except Exception as e:
                print(f"Error al cargar configuración: {e}")
    
    def save_config(self):
        config_file = "simulation_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(self.params, f, indent=4)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
    
    def on_save(self):
        # Validar y guardar todos los valores
        valid = True
        for param_name, (entry, param_type) in self.entries.items():
            try:
                if param_type == "int":
                    value = int(entry.get())
                else:  # float
                    value = float(entry.get())
                self.params[param_name] = value
            except ValueError:
                valid = False
                entry.config(style='Error.TEntry')
            else:
                entry.config(style='TEntry')
        
        if valid:
            self.save_config()
            self.root.quit()
            self.root.destroy()
    
    def get_params(self):
        return self.params
    
    def run(self):
        # Configurar el cierre de la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
        return self.params
        
    def on_close(self, event=None):
        # Guardar la configuración y cerrar
        self.save_config()
        self.root.quit()
        self.root.destroy()
        # Salir del programa
        import sys
        sys.exit(0)

def show_config_window(default_params):
    app = ConfigWindow(default_params)
    return app.run()

if __name__ == "__main__":
    default_params = {
        "initial_rabbits": 50,
        "initial_foxes": 6,
        "initial_food": 100,
        "rabbit_speed": 1.5,
        "fox_speed": 2.2,
        "food_respawn_rate": 2,
        "max_rabbits": 300,
        "max_foxes": 50
    }
    params = show_config_window(default_params)
    print("Parámetros configurados:", params)
