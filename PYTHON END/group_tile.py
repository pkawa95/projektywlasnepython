import customtkinter as ctk
import requests
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk


class GroupTile(ctk.CTkFrame):
    def __init__(self, master, app, group_id, group_info, on_double_click):
        super().__init__(master, corner_radius=12, height=100)
        self.app = app
        self.group_id = group_id
        self.group_info = group_info
        self.on_double_click = on_double_click

        self.configure(border_width=1, border_color="#444444", fg_color="transparent")
        self.pack_propagate(False)

        # === Canvas z gradientem ===
        self.canvas = tk.Canvas(self, width=660, height=100, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        gradient = self.generate_gradient()
        self.tk_gradient = ImageTk.PhotoImage(gradient)
        self.bg_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_gradient)
        self.canvas.tag_lower(self.bg_image_id)

        # === Kontener na zawartość ===
        self.build_content()

        # === Obsługa kliknięć ===
        self.bind("<Button-1>", self.single_click)
        self.bind("<Double-Button-1>", self.double_click)

        # === Sprawdzanie gradientu czas rzeczywisty ===
        self.start_gradient_updater()

    def build_content(self):
        # === Górna część ===
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        # === Nazwa grupy ===
        self.label = ctk.CTkLabel(
            top_frame,
            text=self.group_info["name"],
            font=self.app.font_title,
            text_color="white",
            fg_color="transparent"
        )
        self.label.pack(side="left")

        # === Suwak jasności ===
        self.slider = ctk.CTkSlider(
            self,
            from_=1,
            to=254,
            number_of_steps=253,
            fg_color="gray30",
            progress_color="#1f6aa5",
            corner_radius=10
        )
        self.slider.set(self.group_info["action"].get("bri", 254))
        self.slider.pack(fill="x", padx=10, pady=(0, 10))

        # === Suwak NIE wywołuje pojedynczego kliknięcia ===
        self.slider.bind("<Button-1>", lambda e: "break")
        self.slider.bind("<ButtonRelease-1>", self.set_brightness)

        # === Kliknięcia dla elementów ===
        for widget in [top_frame, self.label]:
            widget.bind("<Button-1>", self.single_click)
            widget.bind("<Double-Button-1>", self.double_click)

    def update_group_info(self):
        self.group_info = self.app.bridge.groups.get(self.group_id, self.group_info)

    def single_click(self, event):
        self.update_group_info()
        current = self.group_info["action"]["on"]
        self.toggle_group(not current)

    def update_toggle_color(self):
        pass  # Placeholder for visual state if needed

    def toggle_group(self, new_state):
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/groups/{self.group_id}/action"
        try:
            requests.put(url, json={"on": new_state})
            self.group_info["action"]["on"] = new_state
        except Exception as e:
            self.app.bridge.update_status(f"❌ Błąd grupy: {e}")

    def set_brightness(self, event):
        value = self.slider.get()
        url = f"http://{self.app.bridge.bridge_ip}/api/{self.app.bridge.token}/groups/{self.group_id}/action"
        try:
            requests.put(url, json={"bri": int(value), "on": True})
        except Exception as e:
            self.app.bridge.update_status(f"❌ Jasność: {e}")

    def double_click(self, event):
        self.on_double_click(self.group_id)

    def xy_to_rgb(self, x, y, brightness=254):
        z = 1.0 - x - y
        Y = brightness / 254
        X = (Y / y) * x
        Z = (Y / y) * z

        r = X * 1.612 - Y * 0.203 - Z * 0.302
        g = -X * 0.509 + Y * 1.412 + Z * 0.066
        b = X * 0.026 - Y * 0.072 + Z * 0.962

        r = max(0, min(1, r))
        g = max(0, min(1, g))
        b = max(0, min(1, b))

        r = int(r ** (1 / 2.2) * 255)
        g = int(g ** (1 / 2.2) * 255)
        b = int(b ** (1 / 2.2) * 255)

        return (r, g, b)

    def start_gradient_updater(self):
        def update_loop():
            self.update_gradient_image()
            self.after(1000, update_loop)  # ⏱️ Co 1 sekundę

        self.after(1000, update_loop)
    def generate_gradient(self):
        colors = []
        all_off = True  # Domyślnie zakładamy, że wszystko jest wyłączone

        for light_id in self.group_info.get("lights", []):
            light = self.app.lights.lights.get(light_id)
            if light and light["state"].get("xy"):
                if light["state"].get("on"):
                    all_off = False
                    xy = light["state"]["xy"]
                    rgb = self.xy_to_rgb(xy[0], xy[1])
                    colors.append(rgb)

        width, height = 660, 100
        img = Image.new("RGB", (width, height), color=0)
        draw = ImageDraw.Draw(img)

        if all_off or not colors:
            # Szary gradient gdy światła wyłączone
            gray = (60, 60, 60)
            for i in range(width):
                draw.line([(i, 0), (i, height)], fill=gray)
            return img

        # Inaczej generuj klasyczny gradient
        for i in range(width):
            ratio = i / max(width - 1, 1)
            index = int(ratio * (len(colors) - 1))
            next_index = min(index + 1, len(colors) - 1)
            frac = (ratio * (len(colors) - 1)) - index

            r = int(colors[index][0] * (1 - frac) + colors[next_index][0] * frac)
            g = int(colors[index][1] * (1 - frac) + colors[next_index][1] * frac)
            b = int(colors[index][2] * (1 - frac) + colors[next_index][2] * frac)

            draw.line([(i, 0), (i, height)], fill=(r, g, b))

        return img

    def update_gradient_image(self):
        new_gradient = self.generate_gradient()
        self.tk_gradient = ImageTk.PhotoImage(new_gradient)
        self.canvas.itemconfig(self.bg_image_id, image=self.tk_gradient)
