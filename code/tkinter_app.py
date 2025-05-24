import shutil
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, filedialog, Text, END, DISABLED, NORMAL, Scrollbar, RIGHT, Y
)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from treat_files import treat_new_file, get_map_stats, plot_times, move_whole_directory
from data_handler import save, load


class FileMover(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        self.dest = app.destination
        self.data = app.data

    def on_created(self, event):
        if not event.is_directory:
            src = Path(event.src_path)
            try:
                treat_new_file(src, self.dest, self.data)
            except IndexError as e:
                self.log("Error searching map data, contact Heavysaur0 for more info - {e}")
            except Exception as e:
                self.log("Error searching map data, are you sure the map is uploaded to TMX ?")


class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Replay Folder Watcher")

        self.source = None
        self.destination = None
        self.data = {"map_uids": {}}
        self.observer = None
        self.watching = False
        self.watch_button = None
        self.selected_map_folder = None

        self.load_saved_data()
        self.build_main_ui()

    def load_saved_data(self):
        self.source, self.destination, self.data = load("data.pkl")
        print(f"Loaded data:")
        print(f"  source - {self.source}")
        print(f"  destination - {self.destination}")
        print(f"  data - [")
        for key, value in self.data.items():
            print(f"    {key} - {value}")
        print("  ]")

    def save_data(self):
        if self.destination:
            save((self.source, self.destination, self.data), "data.pkl")

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def build_main_ui(self):
        self.clear_window()

        self.frame = Frame(self.master)
        self.frame.pack(padx=10, pady=10)

        Label(self.frame, text="Select Replay Folders", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        self.source_label = Label(self.frame, text=f"Source Folder: {self.source or 'None'}")
        self.source_label.pack()
        Button(self.frame, text="Change Replay Source Folder", command=self.set_source).pack()

        self.dest_label = Label(self.frame, text=f"Destination Folder: {self.destination or 'None'}")
        self.dest_label.pack(pady=(10, 0))
        Button(self.frame, text="Change Replay Destination Folder", command=self.set_destination).pack()

        self.watch_button = Button(self.frame, text="Start Watching", command=self.toggle_watching)
        self.watch_button.pack(pady=15)

        Button(self.frame, text="Map Data", command=self.build_map_data_folder_select_ui).pack(pady=(0, 10))

        self.log_area = Text(self.master, height=15, state=DISABLED)
        scrollbar = Scrollbar(self.master, command=self.log_area.yview)
        self.log_area.config(yscrollcommand=scrollbar.set)
        self.log_area.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side=RIGHT, fill=Y)

    def set_source(self):
        path = filedialog.askdirectory(title="Select Replay Source Folder")
        if path:
            self.source = Path(path)
            self.source_label.config(text=f"Source Folder: {self.source}")
            self.log(f"Selected source folder: {self.source}")
            self.save_data()

    def set_destination(self):
        path = filedialog.askdirectory(title="Select Replay Destination Folder")
        if path:
            new_path = Path(path)
            move_whole_directory(self.destination, new_path)
            self.destination = new_path
            self.dest_label.config(text=f"Destination Folder: {self.destination}")
            self.log(f"Selected destination folder: {self.destination}")
            self.save_data()

    def toggle_watching(self):
        if self.watching:
            self.stop_watching()
        else:
            self.start_watching()

    def start_watching(self):
        if not self.source or not self.destination:
            self.log("Error: Please select both source and destination folders.")
            return

        self.log("Started watching folder. Click again or close the window to stop.")
        handler = FileMover(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.source), recursive=False)
        self.observer.start()

        self.watching = True
        self.watch_button.config(text="Stop Watching")

        for widget in self.frame.winfo_children():
            if widget != self.watch_button:
                widget.config(state=DISABLED)

    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.watching = False
        self.watch_button.config(text="Start Watching")
        self.log("Stopped watching folder.")

        for widget in self.frame.winfo_children():
            widget.config(state=NORMAL)

    def build_map_data_folder_select_ui(self):
        self.clear_window()

        frame = Frame(self.master)
        frame.pack(padx=10, pady=10)

        Label(frame, text="Select Map Data Folder", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        self.map_folder_label = Label(frame, text="No folder selected.")
        self.map_folder_label.pack()

        Button(frame, text="Browse Map Folder", command=self.select_map_folder).pack(pady=5)
        Button(frame, text="OK", command=self.build_map_data_actions_ui).pack(pady=5)
        Button(frame, text="Back", command=self.build_main_ui).pack(pady=10)

    def select_map_folder(self):
        if not self.destination:
            self.log("Please select a destination folder first.")
            return
        self.log_area = None

        path = Path(filedialog.askdirectory(title="Select a Folder Inside Destination", initialdir=self.destination))
        if path:
            if path.parent.resolve() == self.destination.resolve():
                self.selected_map_folder = Path(path)
                self.map_folder_label.config(text=f"Selected: {self.selected_map_folder}")
                self.log(f"Selected map data folder: {self.selected_map_folder}")
            else:
                self.map_folder_label.config(text=f"Selected folder is not in the destination directory.")

    def build_map_data_actions_ui(self):
        if not self.selected_map_folder:
            self.log("No map data folder selected.")
            return

        self.clear_window()

        frame = Frame(self.master)
        frame.pack(padx=10, pady=10)

        Label(frame, text="Map Data Actions", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        Button(frame, text="Show map stats", command=self.map_stats).pack(pady=5)
        Button(frame, text="Plot map times", command=self.plot_map_times).pack(pady=5)
        Button(frame, text="Back", command=self.build_main_ui).pack(pady=10)
        
        self.log_area = Text(self.master, height=15, state=DISABLED)
        scrollbar = Scrollbar(self.master, command=self.log_area.yview)
        self.log_area.config(yscrollcommand=scrollbar.set)
        self.log_area.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side=RIGHT, fill=Y)

    def map_stats(self):
        map_stats = get_map_stats(self.selected_map_folder)
        string = ""
        for login, stats in map_stats.items():
            string += f"{login} - [\n"
            string += f"  names - {stats["names"]}\n"
            for time, stat in stats.items():
                if time == "names": continue
                string += f"  {time} - [\n"
                for key, value in stat.items():
                    if key == "dates":
                        string += "    dates - { "
                        for dt in value:
                            string += str(dt.astimezone()) + " "
                        string += "}\n"
                    else:
                        string += f"    {key} - {value}\n"
                string += "  ]\n"
            string += "]\n"
        
        self.log(string)

    def plot_map_times(self):
        plot_times(self.selected_map_folder)

    def log(self, message):
        if not hasattr(self, "log_area") or self.log_area is None:
            return
        self.log_area.config(state=NORMAL)
        self.log_area.insert(END, f"{message}\n")
        self.log_area.see(END)
        self.log_area.config(state=DISABLED)


def main():
    root = Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
