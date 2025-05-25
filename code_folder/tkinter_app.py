from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, filedialog, Text, END, DISABLED, NORMAL, Scrollbar, RIGHT, Y
)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

from treat_files import treat_new_file, get_map_stats_from_data, plot_times, move_whole_directory, sanitise_replays
from data_handler import save, load, recur_display



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
                self.app.log(f"Error searching map data, contact Heavysaur0 for more info - {e}")
                print(f"Error searching map data - {e}")
            except Exception as e:
                self.app.log("Error searching map data, are you sure the map is uploaded to TMX ?")
                print(f"Error searching map data - {e}")
            
            self.app.save_data()


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
        print("Loaded data:")
        recur_display("source", self.source, 1)
        recur_display("destination", self.destination, 1)
        recur_display("data", self.data, 1)

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
        # Button(self.frame, text="Show All Map Stats", command=self.show_all_stats).pack(pady=(0, 10))

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

        Button(frame, text="Show map stats", command=self.display_map_stats).pack(pady=5)
        Button(frame, text="Plot map times", command=self.plot_map_times).pack(pady=5)
        Button(frame, text="Back", command=self.build_main_ui).pack(pady=10)
        
        self.log_area = Text(self.master, height=15, state=DISABLED)
        scrollbar = Scrollbar(self.master, command=self.log_area.yview)
        self.log_area.config(yscrollcommand=scrollbar.set)
        self.log_area.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side=RIGHT, fill=Y)
    
    
    def show_all_stats(self):
        pass


    def display_map_stats(self):
        """
        Goal of stats is to display:
        
        Map: map_data["name"]
        Author: map_data["author]
        Section: map_data["section"]
        Environment: map_data["environment"]
        Type: map_data["type"]
        Mood: map_data["mood"]
        | Record Times | Total | Players | Date (local time) | Respawn avr. | Stuntscore avr. |
        | ------------ | ----- | ------- | ----------------- | ------------ | --------------- |
        | ............ | ..... | ....... | ................. | ............ | ............... |
        
        text being justified on the right
        """
        data_file = self.selected_map_folder / "data.pkl"
        map_data = load(data_file)
        recur_display("map_data", map_data, 0)
        
        map_stats = get_map_stats_from_data(map_data)
        stats = []
        for login, dic in map_stats.items():
            for key, value in dic.items():
                if key == "names": 
                    continue
                
                min_date = min(value["dates"], key=lambda dt: dt.timestamp())
                total = value["times"]
                respawn_avr = value["respawns"] / total
                stuntscore_avr =  value["stunt_score"] / total
                stats.append((key / 1000, total, login, min_date, respawn_avr, stuntscore_avr))
        
        stats.sort(key=lambda lst: lst[3].timestamp()) # Sort by date
        stats.sort(key=lambda lst: lst[0]) # Sort by time
        
        # Add headers
        header_titles = [
            "Record Times", "Total", "Players", 
            "Date (local time)", "Respawn avr.", "Stuntscore avr."
        ]
        
        def format_value(i, value):
            if i == 0:
                hours = int(value // 3600)
                minutes = int((value % 3600) // 60)
                secs = value % 60
                
                if hours > 0:
                    return f"{hours}:{minutes:02}:{secs:05.2f}"
                if minutes > 0:
                    return f"{minutes}:{secs:05.2f}"
                return f"{secs:.2f}"
            if i == 1 or i == 2:
                return str(value)
            if i == 3:
                return value.strftime('%Y-%m-%d %H:%M:%S')
            return f"{value:.2f}"
        
        # Determine max column width
        col_widths = [len(title) for title in header_titles]
        for row in stats:
            for i, value in enumerate(row):
                formatted = format_value(i, value)
                col_widths[i] = max(col_widths[i], len(formatted))
        
        # Create the header
        header_line = " | ".join(title.rjust(col_widths[i]) for i, title in enumerate(header_titles))
        separator = " | ".join("-" * col_widths[i] for i in range(len(col_widths)))

        # Build stat lines
        stat_lines = []
        for row in stats:
            line = " | ".join(
                format_value(i, value).rjust(col_widths[i])
                for i, value in enumerate(row)
            )
            stat_lines.append(line)

        # Assemble final text
        lines = [
            f"Map: {map_data['name']}",
            f"Author: {map_data['author']}",
            f"Section: {map_data['section']}",
            f"Environment: {map_data['environment']}",
            f"Type: {map_data['type']}",
            f"Mood: {map_data['mood']}",
            "",
            f"| {header_line} |",
            f"| {separator} |",
        ]
        for stat_line in stat_lines:
            lines.append(f"| {stat_line} |")

        self.log("\n".join(lines))

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
