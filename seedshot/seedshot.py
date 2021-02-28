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
import base64
from config import Config

debug = True

def main():
    config = Config()
    print(config.safe_to_str())

    root = tk.Tk()

    frame = tk.Frame(root)
    frame.pack(expand=True, fill=tk.BOTH)

    ss = SeedShot(frame, config)
    ss.pack(expand=True, fill=tk.BOTH)

    root.mainloop()

class SeedShot(tk.Canvas):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        self.parent = parent
        # should we be taking screenshots and analyze them (enables with reroll button,
        # disables with stop_watch_hotkey)
        self.watching = False
        self.sct = mss.mss()

        def on_reroll():
            print("rerolling")
            self.reroll_pressed = True
            self.watching = True
            self.loop()

        def on_stop_watch():
            self.watching = False

            self.upload()
            self.save()

            # TODO factor out uploading, saving the image and posting the message to chat


        self.listener = keyboard.GlobalHotKeys({
            self.config["hotkeys"]["reroll"]: on_reroll,
            self.config["hotkeys"]["start-map"]: on_stop_watch,
        })
        self.listener.start()


    def save():
        self.map_img.save(f"screenshot.png")

    def upload():
        headers = {'Authorization': f'Client-ID {self.config["imgur-client-id"]}'}
        img_byte_arr = io.BytesIO()
        self.map_img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        payload = {'image': img_byte_arr}
        if not debug:
            response = requests.request("POST", "https://api.imgur.com/3/image", data=payload, headers=headers)
            response_data = response.text.encode("utf-8")
        else:
            response_data = b'{"data":{"id":"9Z2sK5t","title":null,"description":null,"datetime":1614467962,"type":"image\\/png","animated":false,"width":742,"height":515,"size":357984,"views":0,"bandwidth":0,"vote":null,"favorite":false,"nsfw":null,"section":null,"account_url":null,"account_id":0,"is_ad":false,"in_most_viral":false,"has_sound":false,"tags":[],"ad_type":0,"ad_url":"","edited":"0","in_gallery":false,"deletehash":"hONRkceVHKRDbaF","name":"","link":"https:\\/\\/i.imgur.com\\/9Z2sK5t.png"},"success":true,"status":200}'
        pass

    def loop(self):
        if debug:
            seed_img = Image.open("img/seed/059.png")
            self.map_img = Image.open("img/map/059.png")
        else:
            seed_tmp = self.sct.grab(self.config["seed-box"])
            seed_img = Image.frombytes("RGB", seed_tmp.size, seed_tmp.bgra, "raw", "BGRX")

            map_tmp  = self.sct.grab(self.config["map-box"])
            self.map_img  = Image.frombytes("RGB", map_tmp.size, map_tmp.bgra, "raw", "BGRX")

        w_factor = self.parent.winfo_width() / self.map_img.width
        h_factor = self.parent.winfo_height() / self.map_img.height
        factor = min(w_factor, h_factor)
        width = int(self.map_img.width * factor)
        height = int(self.map_img.height * factor)

        map_img = self.map_img.resize((width, height))
        self.map_tk = ImageTk.PhotoImage(map_img)
        self.create_image(
                self.parent.winfo_width()//2,
                self.parent.winfo_height()//2,
                image=self.map_tk
                )
        self.seed = pytesseract.image_to_string(seed_img)
        #print(pytesseract.image_to_string(seed_img))

        self.update()
        print("here")
        if self.watching:
            self.after(1000, self.loop)

if __name__ == "__main__":
    main()
