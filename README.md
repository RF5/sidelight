# Sidelight GPU monitor
TL;DR a lightweigth live GPU monitor that sits in the corner of your screen (or second screen).

Pros:
- Very small
- Super lightweight
- Easily customizable (even more so for those who know a little python)

Cons:
- Requires manual installation and python

Here's what it looks like with an RTX2070 super:

<p align="center"><img src="img/capture.png" /></p>

## Features
- Customizable size/location, update frequency...
- Works for any (reasonably new) Nvidia GPU
- Statistics are color graded from a deep blue when the resource is hardly being used, to a bright red when the resource is being fully used.
- Works great/best with multiple monitors.

## Requirements
- Windows 10 or Debian-based Linux (e.g Ubuntu)
- Nvidia GPU with Nvidia GPU driver installed
- Python 3.6+ with [matplotlib](https://matplotlib.org/) and [PIL](https://pillow.readthedocs.io/) (or Anaconda)

## Installation
1. Download the latest `sidelightGPU.zip` release from the 'releases' tab in this repo
2. Extact the zip file to wherever you want on your computer
3. Install python 3.6+ with matplotlib.
   - If python is not installed, install it from https://www.python.org/downloads/ (3.6+, usually go for the newest one).
   - Once installed, open cmd and run `pip install matplotlib` and `pip install pillow`.
   - OPTIONAL: if you already have [Anaconda](https://www.anaconda.com/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (preferred), you can skip separately installing python and just uncomment the first line in the bash script `sidelight.bat` (by removing the two `:: ` characters) once you have unzipped.
4. Customize installation
    - Open `settings.config` in your favorite text editor (notepad, whatever)
    - Adjust the first 4 lines to be your primary (and optionally secondary) screen size. Each line has a comment to indicate what it does, so feel free to mess around and customize things how you like, but to get things up and running you only need to adjust the first 4 settings to be your primary and secondary screen size. Note that primary screen is the one windows identifies as screen 1 in your display settings. PS: Adjusting this also allows you to place the sidelight widget anywhere on the screen if you are careful enough.
 5. Test it out! Try double clicking `sidelight.bat` (on windows) or `sidelight.sh` (on linux) to start sidelight. Note it may take a couple of seconds for the statistics to first update. The Linux version also requires miniconda to be installed in your home directory. However, inspecting the code of `sidelight.sh` should allow you to customize the paths if necessary.

That's it :). 

## Making sidelight automatically start when the computer starts
Finding and clicking `sidelight.bat` or `sidelight.sh` each time you start your PC can be quite annoying, so to automatically run sidelight whever you login to your PC, do this:

### On Windows:
1. In the start menu, search "schedule tasks", and click on the Schedule tasks result.
2. In the right panel, hit `create basic task`, enter a name and description of your choice.
3. Hit next, select trigger for every time you log on, next, chose `start a program`, next, for the program to run, use the Browse button to select the `sidelight.bat` file from where you extracted sidelight. Hit next, finish and you're done!
### On Debian-based linux (e.g Ubuntu):
1. Go to startup applications
2. Add a new startup application, enter an arbitrary name/comment if you feel like it, and make the command `/path/to/sidelightGPU/sidelight.sh` so that it runs the shell script on startup.
3. Hit confirm, and you're done. If you notice any bugs, check in `.config/autostart/the-startup-command-file`, and add a line at the end `X-GNOME-Autostart-Delay=10`, which will cause linux to wait 10 seconds before starting sidelight when you log in.

Now whenever you logon to your PC, it will start sidelight :).

