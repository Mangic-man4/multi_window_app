import tkinter as tk
from screeninfo import get_monitors
import cv2
from PIL import Image, ImageTk
import numpy as np

class CookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Main Window")

        # Get all available monitors
        self.monitors = get_monitors()
        self.primary_monitor = self.monitors[0]
        self.secondary_monitor = self.monitors[1] if len(self.monitors) > 1 else self.primary_monitor 
        if len(self.monitors) == 1:
            print("Only one monitor detected! Running in single-screen mode.")
        
        # Set main window on the primary monitor
        self.root.geometry(f"{self.primary_monitor.width}x{self.primary_monitor.height}+{self.primary_monitor.x}+{self.primary_monitor.y}")
        self.root.state('zoomed')

        # Create the sidebar menu on the primary screen
        self.create_sidebar()

        # Track window resizing
        self.root.bind("<Configure>", self.update_sidebar_font)

        # Open Simulated View if a second monitor exists
        self.patties = []  # Store patties for simulation
        self.simulated_window = None
        if self.secondary_monitor:
            self.open_simulated_view()

        # Initialize webcam
        self.cap = None
        self.video_label = None

    def find_camera(self):
        """Attempts to find an external camera, falls back to default webcam if not found."""
        """Only used with secondary camera find method"""
        for i in range(1, 2):  # Check for external cameras at indices 1, 2, 3, etc.
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"External camera found at index {i}.")
                return cap
            cap.release()
        print("No external camera found, falling back to default webcam at index 0.")
        cap = cv2.VideoCapture(0)  # Fallback to default webcam
        return cap

    def create_sidebar(self):
        """Creates a sidebar menu that adjusts based on window size."""
        self.sidebar = tk.Frame(self.root, bg="gray30", width=200)
        self.sidebar.pack(side="left", fill="y")

        self.menu_buttons = []
        menu_options = {
            "Main Menu": self.show_main_menu,
            "Settings": self.show_settings,
            "Calibration": self.show_calibration,
            "Coordinate Testing": self.show_coordinate_testing,
            "Webcam/Griddle View": self.show_griddle_view,
            "Simulated View": self.open_simulated_view,
            "Burger Vision": self.show_burger_vision 

        }

        for text, command in menu_options.items():
            #btn = tk.Button(self.sidebar, text=text, command=command, fg="white", bg="gray40")
            btn = tk.Button(self.sidebar, text=text, command=lambda cmd=command: self.switch_tab(cmd), fg="white", bg="gray40")

            btn.pack(fill="x", pady=5)
            self.menu_buttons.append(btn)

        self.main_content = tk.Frame(self.root, bg="gray25")
        self.main_content.pack(side="right", fill="both", expand=True)

        self.current_screen = None
        self.show_main_menu()
    
    def switch_tab(self, command):
        """Switches tabs and ensures the webcam is properly released when needed."""
        if self.cap:
            self.close_webcam()
        command()

    def update_sidebar_font(self, event=None):
        """Dynamically adjusts sidebar button font size based on window height."""
        window_height = self.root.winfo_height()
        font_size = max(10, window_height // 55)  # Adjust based on screen size

        for button in self.menu_buttons:
            button.config(font=("Arial", font_size))

    def switch_screen(self, text):
        if self.current_screen:
            self.current_screen.destroy()
        self.current_screen = tk.Frame(self.main_content, bg="gray25")
        self.current_screen.pack(fill="both", expand=True)
        label = tk.Label(self.current_screen, text=text, font=("Arial", 18), fg="white", bg="gray25")
        label.pack(pady=100)


    def show_main_menu(self): self.switch_screen("🏠 Main Menu")
    def show_settings(self): self.switch_screen("⚙️ Settings")
    def show_calibration(self): self.switch_screen("🔧 Calibration")
    def show_coordinate_testing(self): self.setup_coordinate_testing()

    def show_griddle_view(self):
        """Displays the live video feed and applies color-based burger detection."""
        self.switch_screen("📷 Webcam/Griddle View")
        self.video_label = tk.Label(self.current_screen)
        self.video_label.pack()
        
        #self.cap = self.find_camera()  # Use the method to find the correct camera (secondary method)
        self.cap = cv2.VideoCapture(1)  # Default method (0 for pc's webcam, 1 for external camera)

        if not self.cap.isOpened():  # Check if the camera opened successfully
            print("External camera not found. Falling back to default webcam at index 0.")
            self.cap = cv2.VideoCapture(0)  # Fallback to the built-in webcam (index 0)

        self.update_webcam_feed()
        

    def show_burger_vision(self): 
        """Displays Burger Vision analysis in the main window."""

        self.switch_screen("🍔 Burger Vision Analysis")
        
        self.image_label = tk.Label(self.current_screen, bg="gray25")
        self.image_label.pack()
        
        self.analysis_label = tk.Label(self.current_screen, text="", font=("Arial", 14), fg="white", bg="gray25")
        self.analysis_label.pack(pady=10)

        self.color_display = tk.Canvas(self.current_screen, width=300, height=50, bg="gray25", highlightthickness=0)
        self.color_display.pack(pady=5)
        
        self.analyze_burger_images()
        self.update_burger_image()

    def update_webcam_feed(self):
        """Captures video frames, applies burger detection, and updates the Tkinter UI."""
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)  # Flip horizontally for natural mirroring
                processed_frame = self.detect_burgers(frame)  # Apply burger detection
                img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                img = ImageTk.PhotoImage(img)
                
                self.video_label.config(image=img)
                self.video_label.image = img
                
            self.current_screen.after(10, self.update_webcam_feed)  # Refresh at ~60 FPS

    def detect_burgers(self, frame):
        """Detects burger patties using color and shape analysis."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define color range for detecting browned patties (adjust if needed)
        lower_brown = np.array([5, 50, 50])  # Lower HSV threshold
        upper_brown = np.array([30, 255, 255])  # Upper HSV threshold
        mask = cv2.inRange(hsv, lower_brown, upper_brown)
        
        # Find contours from the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:  # Ignore small noise
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Draw bounding box
                cv2.putText(frame, "Burger", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame

    def close_webcam(self):
        """Releases the webcam when switching away from the Webcam/Griddle View."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def analyze_burger_images(self):
        """Loads burger images and dynamically determines cooking states."""
        try:
            self.raw_patty = cv2.imread("patty_raw.png")
            self.half_patty = cv2.imread("patty_half_cooked.png")
            self.cooked_patty = cv2.imread("patty_ready.png")

            if self.raw_patty is None or self.half_patty is None or self.cooked_patty is None:
                print("Error: One or more images not found!")
                self.analysis_label.config(text="Error: One or more images not found!")
                return

            print("All images loaded successfully!")
            height_raw, width_raw, _ = self.raw_patty.shape
            self.half_patty = cv2.resize(self.half_patty, (width_raw, height_raw))
            self.cooked_patty = cv2.resize(self.cooked_patty, (width_raw, height_raw))

            # Convert to HSV
            hsv_raw = cv2.cvtColor(self.raw_patty, cv2.COLOR_BGR2HSV)
            hsv_half = cv2.cvtColor(self.half_patty, cv2.COLOR_BGR2HSV)
            hsv_cooked = cv2.cvtColor(self.cooked_patty, cv2.COLOR_BGR2HSV)

            # Extract dominant hue values using the center region of the patty
            hues = [
                self.get_dominant_hue(hsv_raw),
                self.get_dominant_hue(hsv_half),
                self.get_dominant_hue(hsv_cooked)
            ]

            # Assign fixed categories
            labels = ["Raw (10%)", "Half-Cooked (60%)", "Fully Cooked (100%)"]
            colors = [self.hue_to_rgb(hue) for hue in hues]
            
            result_text = "\nCooking State Detection:\n"
            self.color_display.delete("all")
            for i, (hue, label, color) in enumerate(zip(hues, labels, colors)):
                result_text += f" {label}: Hue {hue}\n"
                self.color_display.create_rectangle(10 + i * 100, 10, 90 + i * 100, 40, fill=color, outline="white")
            
            self.analysis_label.config(text=result_text)
        
        except Exception as e:
            print(f"Error in processing images: {e}")
            self.analysis_label.config(text=f"Error: {e}")

    def get_dominant_hue(self, hsv_image):
        """Finds the dominant hue value in the central region of an image, ignoring dark pixels."""
        h, w, _ = hsv_image.shape
        center_region = hsv_image[h//4:3*h//4, w//4:3*w//4, 0]  # Crop center
        hue_values = center_region.flatten()
        hue_values = hue_values[hue_values > 10]  # Ignore dark pixels
        if len(hue_values) == 0:
            return 0
        return int(np.median(hue_values))
    
    def hue_to_rgb(self, hue):
        """Converts a hue value to an approximate RGB color."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 180.0, 1, 1)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

    def update_burger_image(self):
        """Displays the combined burger cooking images in the UI."""
        combined_image = np.hstack((self.raw_patty, self.half_patty, self.cooked_patty))
        combined_image = cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(combined_image)
        img = img.resize((600, 200))
        img_tk = ImageTk.PhotoImage(img)

        self.image_label.configure(image=img_tk)
        self.image_label.image = img_tk

    def setup_coordinate_testing(self):
        """Creates UI for entering patty positions and timer duration."""
        if self.current_screen:
            self.current_screen.destroy()
        self.current_screen = tk.Frame(self.main_content, bg="gray25") #-----------------
        self.current_screen.pack(fill="both", expand=True)

        frame = tk.Frame(self.current_screen, bg="gray25")
        frame.pack(pady=400)

        tk.Label(frame, text="X Position:", bg="gray25", fg="white", font=("Arial", 15)).grid(row=0, column=0)
        tk.Label(frame, text="Y Position:", bg="gray25", fg="white", font=("Arial", 15)).grid(row=1, column=0)
        tk.Label(frame, text="Timer (seconds):", bg="gray25", fg="white", font=("Arial", 15)).grid(row=2, column=0)

        self.x_entry = tk.Entry(frame)
        self.y_entry = tk.Entry(frame)
        self.time_entry = tk.Entry(frame)
        self.x_entry.grid(row=0, column=1)
        self.y_entry.grid(row=1, column=1)
        self.time_entry.grid(row=2, column=1)

        add_button = tk.Button(frame, text="Add Patty", command=self.add_patty)
        add_button.grid(row=3, column=0, columnspan=2, pady=10)

    def open_simulated_view(self):
        """Creates or reopens the secondary window for displaying simulated patties."""
        if self.simulated_window and tk.Toplevel.winfo_exists(self.simulated_window):
            self.simulated_window.deiconify()
            return
        
        self.simulated_window = tk.Toplevel(self.root)
        self.simulated_window.title("Simulated View")
        self.simulated_window.geometry(f"{self.secondary_monitor.width}x{self.secondary_monitor.height}+{self.secondary_monitor.x}+{self.secondary_monitor.y}")
        self.simulated_window.state('zoomed')
        self.simulated_window.protocol("WM_DELETE_WINDOW", self.hide_simulated_view)

        self.canvas = tk.Canvas(self.simulated_window, bg="black")
        self.canvas.pack(fill="both", expand=True)

    def hide_simulated_view(self):
        """Hides the simulated view instead of destroying it."""
        self.simulated_window.withdraw()

    def add_patty(self):
        """Adds a patty with a countdown timer."""
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            time_value = int(self.time_entry.get()) if self.time_entry.get() else 30
        except ValueError:
            print("Invalid input! Enter integer values for X, Y, and Time.")
            return

        patty = {'x': x, 'y': y, 'time': time_value, 'circle': None, 'text': None, 'blinking': False, 'blink_state': True}
        self.patties.append(patty)
        self.update_simulated_view()
        self.start_timer(patty)

    def update_simulated_view(self):
        """Redraws patties on the simulated screen."""
        if not hasattr(self, 'canvas'):
            return
        self.canvas.delete("all")
        
        for patty in self.patties:
            color = "green" if patty['time'] > 10 else "orange" if patty['time'] > 5 else "red"
            patty['circle'] = self.canvas.create_oval(
                patty['x'] - 150, patty['y'] - 150,
                patty['x'] + 150, patty['y'] + 150,
                fill=color
            )
            patty['text'] = self.canvas.create_text(
                patty['x'], patty['y'], 
                text=str(patty['time']), 
                font=("Arial", 30), 
                fill="white" if patty ['time'] > 10 else "black" if patty['time'] > 5 else "white"
            )
    
    def start_timer(self, patty):
        """Countdown for the patty timer using after()."""
        def countdown():
            if patty['time'] >= 0:
                self.update_simulated_view()
                patty['time'] -= 1

                if patty['time'] == 4 and not patty['blinking']:
                    patty['blinking'] = True
                    self.blink_patty(patty)

                self.root.after(1000, countdown)
            else:
                self.patties.remove(patty)
                self.update_simulated_view()
        countdown()

    def blink_patty(self, patty):
        """Blinks the patty at a constant rate of 0.4 seconds."""
        def toggle():
            if patty in self.patties and patty['time'] >= 0:
                patty['blink_state'] = not patty['blink_state']
                new_color = "red" if patty['blink_state'] else "black"
                self.canvas.itemconfig(patty['circle'], fill=new_color)
                self.root.after(400, toggle)

        if patty['blinking']:
            toggle()

if __name__ == "__main__":
    root = tk.Tk()
    app = CookingApp(root)
    root.mainloop()
