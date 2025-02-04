import tkinter as tk

def open_second_window():
    second_window = tk.Toplevel(root)
    second_window.title("Second Window")
    second_window.geometry("300x200")
    tk.Label(second_window, text="This is the second window").pack(pady=20)

# Create the main window
root = tk.Tk()
root.title("Main Window")
root.geometry("300x200")

# Add a button to open the second window
button = tk.Button(root, text="Open Second Window", command=open_second_window)
button.pack(pady=20)

# Run the application
root.mainloop()
