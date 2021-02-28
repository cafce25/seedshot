#!/usr/bin/env python
from PIL import Image, ImageTk
from pynput import keyboard
import io
import mss
import pytesseract
import tkinter as tk
import requests
import json
from config import Config

debug = False

ENCODING = "utf-8"
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
        # limit tries to upload
        self.timeout = 1
        self.tries = 0

        def on_reroll():
            print("rerolling")
            self.reroll_pressed = True
            self.watching = True
            self.loop()

        def on_stop_watch():
            self.watching = False
            self.save()
            self.upload(self.seed.strip())

        self.listener = keyboard.GlobalHotKeys({
            self.config["hotkeys"]["reroll"]: on_reroll,
            self.config["hotkeys"]["start-map"]: on_stop_watch,
        })
        self.listener.start()


    def save(self):
        self.map_img.save(f"screenshot-{self.seed.strip()}.png")

    def upload(self, seed):
        headers = {'Authorization': f'Client-ID {self.config["imgur-client-id"]}'}
        img_byte_arr = io.BytesIO()
        self.map_img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        payload = {'image': img_byte_arr}
        if not debug:
            response = requests.request("POST", "https://api.imgur.com/3/image", data=payload, headers=headers)
            response_data = json.loads(response.text.encode("utf-8"))
        else:
            response_data = json.loads(DUMMY_RESPONSE)

        if response_data["success"]:
            print(f'successful upload{response_data}')
            self.timeout = 1
            self.tries = 0
            send_twitch_message(
                    self.config["twitch-oauth-token"],
                    self.config["twitch-user-name"],
                    self.config["twitch-channel"],
                    f'!command update !seed {seed} {response_data["data"]["link"]}')
        else:
            print(f'failed upload {self.tries} {self.timeout} {response_data}')
            self.timeout *= 2
            self.tries += 1
            if tries < 6:
                self.after(self.timeout * 1000, self.upload, seed)



    def loop(self):
        if debug:
            import os
            image_dir = os.path.realpath(
                    os.path.join(
                        os.path.dirname(__file__),
                        ".."))

            seed_img = Image.open(os.path.join(image_dir, "seed.png"))
            self.map_img = Image.open(os.path.join(image_dir, "map.png"))
        else:
            seed_tmp = self.sct.grab(self.config["seed-box"])
            seed_img = Image.frombytes(
                    "RGB", seed_tmp.size, seed_tmp.bgra, "raw", "BGRX")

            map_tmp  = self.sct.grab(self.config["map-box"])
            self.map_img  = Image.frombytes(
                    "RGB", map_tmp.size, map_tmp.bgra, "raw", "BGRX")

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
        if self.watching:
            self.after(100, self.loop)

import socket
import time

def send_twitch_message(token, bot_name, channel, msg):
    connection_data = ("irc.chat.twitch.tv", 6667)
    with socket.socket() as server:
        server = socket.socket()
        server.connect(connection_data)
        server.send(bytes(f"PASS {token}\r\n", ENCODING))
        server.send(bytes(f"NICK {bot_name}\r\n", ENCODING))
        server.send(bytes(f"JOIN #{channel}\r\n", ENCODING))
        server.send(bytes(f"PRIVMSG #{channel} :{msg}\r\n", ENCODING))

DUMMY_RESPONSE = b'{"data":{"id":"9Z2sK5t","title":null,"description":null,"datetime":1614467962,"type":"image\\/png","animated":false,"width":742,"height":515,"size":357984,"views":0,"bandwidth":0,"vote":null,"favorite":false,"nsfw":null,"section":null,"account_url":null,"account_id":0,"is_ad":false,"in_most_viral":false,"has_sound":false,"tags":[],"ad_type":0,"ad_url":"","edited":"0","in_gallery":false,"deletehash":"hONRkceVHKRDbaF","name":"","link":"https:\\/\\/i.imgur.com\\/9Z2sK5t.png"},"success":true,"status":200}'
if __name__ == "__main__":
    main()
