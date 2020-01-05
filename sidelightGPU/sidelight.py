import os, sys, time
import signal
import subprocess
import threading
from pathlib import Path
from queue import Empty, Queue
import tkinter as tk
from tkinter import END, Frame, Tk, mainloop, ttk

from matplotlib import cm, colors

# Loading config
ON_POSIX = 'posix' in sys.builtin_module_names
sidelight_dir = os.path.dirname(os.path.abspath(__file__))

with open(Path(sidelight_dir)/'settings.config', 'r') as file:
    lines = file.readlines()
    lines = [l.split('#')[0].strip() for l in lines]
    line_infos = [l.split('=') for l in lines]
    settings_dict = {l[0]: l[1] for l in line_infos}

update_freq_s = int(settings_dict['update_freq_s'])#5
bring_to_front_delay = int(settings_dict['bring_to_front_delay'])#15


smi_path = Path(os.getenv("SystemDrive") + '/Program Files/NVIDIA Corporation/NVSMI')
if settings_dict['nvidia_smi_path'] != 'default': smi_path = Path(settings_dict['nvidia_smi_path'])
cmd_str = ' --query-gpu=driver_version,power.draw,power.limit,pcie.link.gen.current,temperature.gpu,\
utilization.gpu,utilization.memory,memory.total,memory.free,memory.used --format=csv -l ' + str(update_freq_s)

def run_checks():
    if os.name != 'nt':
        raise AssertionError("Sidelight only works on windows")
    if smi_path.is_dir() != True:
        raise AssertionError("Requires NVIDIA SMI. This should be installed by default if your GPU supports \
                it and you have the latest graphics card drivers")
    if (smi_path/'nvidia-smi.exe').is_file() != True:
        raise AssertionError("NVIDIA SMI missing executable")

    return True

def place_root(root):
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen
    w = 205 # width for the Tk self.root
    h = 270 # height for the Tk self.root
    # print(ws, hs)
    # x = (ws/2) - (w/2)
    # y = (hs/2) - (h/2)
    second_height = int(settings_dict['second_screen_height'])
    if second_height == 0:
        second_height = hs
    root.geometry('%dx%d+%d+%d' % (w, 
                h, 
                int(settings_dict['main_screen_width'])+int(settings_dict['second_screen_width'])-w, 
                second_height-h-40))

def get_lbl_kwargs(bold=False, anchor=None, fsize=10):
    basic_kwargs = {
        'fg': 'white',
        'bg': 'black',
        'font': ('Courier New', fsize),
        'anchor': 'w'
    }
    if bold: basic_kwargs['font'] = ('Courier New', fsize, 'bold')
    if anchor: basic_kwargs['anchor'] = anchor
    return basic_kwargs

class Sidelight:
    def __init__(self):
        ### Basic constructions
        self.root = Tk()
        self.root.wm_title("Sidelight for Nvidia GPUs")
        self.running = True
        self.root.withdraw()
        self.root.update()
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.configure(background='black')
        self.root.attributes('-alpha', float(settings_dict['alpha']))
        self.root.overrideredirect(True)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        place_root(self.root)

        ### Defining exit button
        # print(sidelight_dir, Path(sidelight_dir)/'close.png')
        im = tk.PhotoImage(file=Path(sidelight_dir)/'close.png')
        button = tk.Button(self.root, image=im , command=lambda: self.close(), height=10, width=10, bg='black', borderwidth=0)
        button.place(relx=1, x=-3, y=4, anchor=tk.NE)
        def on_enter(e): button['bg'] = 'red'
        def on_leave(e): button['bg'] = 'black'
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

        ######
        ## Defining text labels
        ######

        # Title
        name = run_smi_cmd(' --query-gpu=gpu_name --format=csv')
        name = name.split('\n')[1].strip()
        self.title = tk.Label(self.root, text=name, **get_lbl_kwargs(bold=True))
        self.title['fg'] = 'gold'
        # title.place(relx=0, rely=0, x=4, y=4, anchor=tk.NW)
        self.title.grid(row=0, sticky='w')

        # Memory label
        memlbl = tk.Label(self.root, text=' Memory', **get_lbl_kwargs(anchor='n', fsize=11), padx=5)
        memlbl.grid(row=1, sticky='n')

        self.gpu_mem_used = tk.Label(self.root, text='used: ????', **get_lbl_kwargs(), padx=5)
        self.gpu_mem_used.grid(row=2, column=0, sticky='w')

        self.gpu_mem_free = tk.Label(self.root, text='free: ????', **get_lbl_kwargs(), padx=5)
        self.gpu_mem_free.grid(row=3, column=0, sticky='w')

        self.gpu_mem_active = tk.Label(self.root, text='active: ????', **get_lbl_kwargs(), padx=5)
        self.gpu_mem_active.grid(row=4, column=0, sticky='w')
        
        # Compute labels
        complbl = tk.Label(self.root, text='Utilization', **get_lbl_kwargs(anchor='n', fsize=11), padx=5)
        complbl.grid(row=5, sticky='n')

        self.comp_util = tk.Label(self.root, text='compute: ????', **get_lbl_kwargs(), padx=5)
        self.comp_util.grid(row=6, column=0, sticky='w')
        self.temp_meas = tk.Label(self.root, text='temperature: ????', **get_lbl_kwargs(), padx=5)
        self.temp_meas.grid(row=7, column=0, sticky='w')
        self.power_draw = tk.Label(self.root, text='power: ????', **get_lbl_kwargs(), padx=5)
        self.power_draw.grid(row=8, column=0, sticky='w')

        misclbl = tk.Label(self.root, text='Misc.', **get_lbl_kwargs(anchor='n', fsize=11), padx=5)
        misclbl.grid(row=9, sticky='n')

        self.driver_ver = tk.Label(self.root, text='driver ver: ????', **get_lbl_kwargs(), padx=5)
        self.driver_ver.grid(row=10, column=0, sticky='w')
        self.pcie_ver = tk.Label(self.root, text='pcie ver: ????', **get_lbl_kwargs(), padx=5)
        self.pcie_ver.grid(row=11, column=0, sticky='w')

        ### Defining colormaps
        self.color_mappings = {}
        norm = colors.Normalize(vmin=0, vmax=1.0)
        self.color_mappings['gpu_mem_used'] = cm.ScalarMappable(norm=norm, cmap=cm.rainbow)
        self.color_mappings['gpu_mem_free'] = cm.ScalarMappable(norm=norm, cmap=cm.rainbow_r)
        self.color_mappings['gpu_mem_active'] = cm.ScalarMappable(norm=norm, cmap=cm.rainbow)
        self.color_mappings['comp_util'] = self.color_mappings['gpu_mem_active']
        temp_norm = colors.Normalize(vmin=28, vmax=74, clip=True)
        self.color_mappings['temp_meas'] = cm.ScalarMappable(norm=temp_norm, cmap=cm.rainbow)
        self.color_mappings['power_draw'] = self.color_mappings['comp_util']

        ### Start updating the GPU info
        self.queue = Queue()
        self.start_subproc()
        self.update_gpu_info()
        self.root.after(bring_to_front_delay*1000, self.bring_to_front)
        ### Final runtime updates
        self.root.update()
        self.root.mainloop()

    def bring_to_front(self):
        if self.running == True: self.root.after(bring_to_front_delay*1000, self.bring_to_front)
        self.root.attributes("-topmost", True)
        self.root.attributes("-topmost", False)
        
    def start_subproc(self):
        self.gpu_info_pipe = subprocess.Popen('"' + str(smi_path/'nvidia-smi.exe') + '"' + cmd_str, stdout=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX, shell=True)
        self.t = threading.Thread(target=enqueue_output, args=(self.gpu_info_pipe.stdout, self.queue, lambda: self.running))
        self.t.daemon = True
        self.t.start()

    def update_gpu_info(self):
        if self.running == True: self.root.after(update_freq_s*1000-1, self.update_gpu_info)
        try: line = self.queue.get_nowait().decode('utf-8').strip()
        except Empty: pass
        else: 
            if len(line) < 130:
                infos = line.split(', ')
                # print(infos)

                pct = int(infos[-1].replace('MiB', '').strip())/int(infos[-3].replace('MiB', '').strip())
                _used_str = infos[-1] + ' ({:02.0f}%)'.format(100*pct)
                self.gpu_mem_used['text'] = 'used: {:>17s}'.format(_used_str)
                val = self.color_mappings['gpu_mem_used'].to_rgba(pct, bytes=True)
                self.gpu_mem_used['fg'] = _from_rgb(val[0:3])

                pct = int(infos[-2].replace('MiB', '').strip())/int(infos[-3].replace('MiB', '').strip())
                _free_str = infos[-2] + ' ({:02.0f}%)'.format(100*pct)
                self.gpu_mem_free['text'] = 'free: {:>17s}'.format(_free_str)
                val = self.color_mappings['gpu_mem_free'].to_rgba(pct, bytes=True)
                self.gpu_mem_free['fg'] = _from_rgb(val[0:3])

                _active_str = infos[-4].replace('%', '').strip() + '%'
                self.gpu_mem_active['text'] = 'active: {:>14s}'.format(_active_str)
                pct = int(infos[-4].replace('%', '').strip())/100.0
                val = self.color_mappings['gpu_mem_active'].to_rgba(pct, bytes=True)
                self.gpu_mem_active['fg'] = _from_rgb(val[0:3])
                
                _comp_str = infos[-5].replace('%', '').strip() + '%'
                self.comp_util['text'] = 'compute: {:>13s}'.format(_comp_str)
                pct = int(infos[-5].replace('%', '').strip())/100.0
                val = self.color_mappings['comp_util'].to_rgba(pct, bytes=True)
                self.comp_util['fg'] = _from_rgb(val[0:3])

                _tmp_str = infos[-6].strip() + '°C'
                self.temp_meas['text'] = 'temperature: {:>9s}'.format(_tmp_str)
                val = self.color_mappings['temp_meas'].to_rgba(int(infos[-6].strip()), bytes=True)
                self.temp_meas['fg'] = _from_rgb(val[0:3])

                _pwn_drawn = float(infos[1].replace('W', '').strip())
                _pwn_tot = float(infos[2].replace('W', '').strip())
                _power_pct = _pwn_drawn/_pwn_tot
                _power_str = '{:>5.2f}W ({:02.0f}%)'.format(_pwn_drawn, 100*_power_pct)
                self.power_draw['text'] = 'power: {:>16s}'.format(_power_str)
                val = self.color_mappings['power_draw'].to_rgba(_power_pct, bytes=True)
                self.power_draw['fg'] = _from_rgb(val[0:3])

                self.driver_ver['text'] = 'driver ver: {:>10s}'.format(infos[0])
                self.pcie_ver['text'] = 'pcie ver: {:>12s}'.format('gen ' + infos[3])

    def close(self):
        # print("closing...")
        self.root.quit()
        self.root.destroy()
        self.running = False
        self.gpu_info_pipe.terminate()
        self.gpu_info_pipe.kill()
        while True:
            if self.gpu_info_pipe.poll() is not None:
                break
            time.sleep(0.1)

        self.t.join()

def enqueue_output(out, queue, running):
    for line in iter(out.readline, b''):
        queue.put(line)
        if running() == False:
            break
    out.close()


def run_smi_cmd(cmd_str):
    s = subprocess.run(str(smi_path/'nvidia-smi.exe') + cmd_str, stdout=subprocess.PIPE)
    return s.stdout.decode('utf-8')

def _from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb   


if __name__ == "__main__":
    if run_checks(): 
        # print("Checks passed")
        Sidelight()
