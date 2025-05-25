# Trackmania Replay Auto Logger

This is a simple and beginner-friendly Python tool to automatically organize your Trackmania hunting replays, log your times, and visualize your stats.

I thank auxlua for the project idea. The code is meant to upgrade what he did before, to have a open source, and free to access code for everyone.

## Requirements

* A Windows computer
* An internet connection (needed for search the track name)
* A folder where your Trackmania replays are saved
* A destination folder where you want replays to be organized and logged

## How It Works

This tool is a Tkinter-based GUI app that:

1. Lets you select the folder where your replays are saved.
2. Lets you choose where you want them to be moved and organized.
3. Automatically extracts replay information (like map name and time).
4. Logs everything in a structured format (for stats).
5. Provides a "Map Stats" tool to:

   * See statistics for a specific map
   * Plot your replay times over time

## Step 0: Get the Project

### Option 1: GitHub ZIP (Easier)

1. Go to the GitHub project page
2. Click the green "Code" button → Download ZIP
3. Extract the ZIP to a folder on your computer

### Option 2: Git

```bash
git clone https://github.com/your_username/your_repo.git
cd your_repo
```

## Step 1: Check If Python Is Installed

Open a terminal (Command Prompt or PowerShell on Windows), and run:

```bash
python --version
# Or
python3 --version
```

You should see something like:

```bash
Python 3.x.x
```

If not, Python is probably not installed.

### Installing Python

1. Go to the [official Python website](https://www.python.org/downloads/)
2. Download the latest version for your system
3. Run the installer
4. **Important**: Check the box that says "Add Python to PATH" during installation
5. Restart your terminal

### Installing Pip

Ensure that pip is also installed with:

```bash
pip --version
# Or
pip3 --version
```

If not, run those commands:

```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
# Or
python3 get-pip.py
```

Try `python --version` again to confirm it's working.

## Step 2: Run the Project

Once you're in the extracted or cloned project folder open a terminal or command prompt in that folder.

If you have already downloaded the project before and are just updating it I recommend to run first:

```bash
python sanitise.py
# Or
python3 sanitise.py
```

To run the program you have to type in the command prompt:

```bash
python run.py
# Or
python3 run.py
```

The `run.py` script will:

* Check if `pip` is available
* Automatically install required packages (like `tkinter`, `matplotlib`, etc.)
* Launch the app (`tkinter_app.py`)

## Features

* Replay Organizer: Automatically move and rename replays
* Replay Logger: Save each run’s data (map, time, date, etc.)
* Map Stats Viewer:

  * View stats for a chosen map
  * Plot your performance over time with a simple click
* Auto updater:
  
  * The project folder will auto update by checking the github repo
  * Handle data changes by sanitising replays

## Future Features (To Do List)

* Make a proper plot
* Make it compatible with ModLoader
* Handle (shomehow) duplicate map names

## Potential Troubles

The beta testing was done only on my computer, some problem may arise and need involve me for fixing so please reach me out.

## Having Trouble?
  
If you ever think that a problem occured with the replay files (data-wise).  
You can try to potentially fix it by running `sanitise.py` with:

```bash
python sanitise.py
# Or
python3 sanitise.py
```

Otherwise:

* Make sure you're in the right folder (where `run.py` is located)
* Make sure you're connected to the internet (for installing dependencies)
* Try both `python` and `python3` if one doesn't work
* Check that your replay paths exist and are correctly set in the GUI
* Check the terminal console, and send it to Heavysaur0 (me) and ask for help

Try to download the newest version of the project in github.  
You don't have to worry about data being lost, you just have to re-input the destination folder correctly, everything else is handled by the program.

## Need Help?

Feel free to open an issue on the GitHub repo or contact me for support.
