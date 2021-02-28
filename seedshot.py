#!/usr/bin/env python
from PIL import Image, ImageTk
from pynput import keyboard
import http.client
import io
import mss
import mss.tools
import pytesseract
import tkinter as tk
import twitchAPI
import requests
import urllib.parse
import yaml
import base64

# config
# TODO move this to it's own file

credentials = yaml.load(open("credentials.yaml"))

debug = True
reroll_hotkey = "q" # or <ctrl>+<alt>+q
stop_watch_hotkey = "c"

# Values are default for 1080p
# coordinates of the seed input field in factorio
seedbox = {
    "left": 352,
    "top": 47,
    "width": 142,
    "height": 20,
    "mon": 1,
}

# coordinates of the map we want to share later
mapbox = {
    "left": 546,
    "top": 76,
    "width": 1350,
    "height": 936,
    "mon": 1,
}


class SeedShot(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, width=mapbox["width"], height=mapbox["height"])

        self.parent = parent
        # should we be taking screenshots and analyze them (enables with reroll button,
        # disables with stop_watch_hotkey)
        self.watching = False
        self.sct = mss.mss()
        self.i = 1

        def on_reroll():
            print("rerolling")
            self.reroll_pressed = True
            self.watching = True
            self.loop()

        def on_stop_watch():
            headers = {
                    'Authorization': f'Client-ID {credentials["client-id"]}',
                    }
            print(self.seed)
            img_byte_arr = io.BytesIO()
            self.map_img.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            payload = {'image': img_byte_arr}
            response = requests.request("POST", "https://api.imgur.com/3/image", data=payload, headers=headers)
            print(response.text.encode("utf-8"))

            self.watching = False

        self.listener = keyboard.GlobalHotKeys({
            reroll_hotkey: on_reroll,
            stop_watch_hotkey: on_stop_watch,
        })
        self.listener.start()


    def loop(self):
        if debug:
            seed_img = Image.open("img/seed/059.png")
            map_img = Image.open("img/map/059.png")
        else:
            seed_tmp = self.sct.grab(seedbox)
            seed_img = Image.frombytes("RGB", seed_tmp.size, seed_tmp.bgra, "raw", "BGRX")

            map_tmp  = self.sct.grab(mapbox)
            self.map_img  = Image.frombytes("RGB", map_tmp.size, map_tmp.bgra, "raw", "BGRX")

        w_factor = self.parent.winfo_width() / map_img.width
        h_factor = self.parent.winfo_height() / map_img.height
        factor = min(w_factor, h_factor)
        width = int(map_img.width * factor)
        height = int(map_img.height * factor)

        self.map_img = map_img.resize((width, height))
        self.map_tk = ImageTk.PhotoImage(map_img)
        self.create_image(
                self.parent.winfo_width()//2,
                self.parent.winfo_height()//2,
                image=self.map_tk
                )
        self.seed = pytesseract.image_to_string(seed_img)
        #print(pytesseract.image_to_string(seed_img))
        #print(f"saving screenshot {self.i}")
        if not debug:
            map_img.save(f"img/map/{self.i:03}.png")
        self.i += 1

        self.update()
        if self.watching:
            self.after(1000, self.loop)

root = tk.Tk()
print(root.winfo_width())


frame = tk.Frame(root)
frame.pack(expand=True, fill=tk.BOTH)

ss = SeedShot(frame)
ss.pack(expand=True, fill=tk.BOTH)

root.mainloop()
