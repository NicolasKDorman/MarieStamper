"""STAMPER - puts the date and time a photo was taken onto the photo.

Folders are created next to this program:
  1 - Pictures That Need Stamps
  2 - Stamped Pictures
  3 - Originals Already Stamped
"""
import json
import os
import shutil
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk

APP_NAME = "STAMPER"
EXTS = (".jpg", ".jpeg")


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE = app_dir()
F1 = os.path.join(BASE, "1 - Pictures That Need Stamps")
F2 = os.path.join(BASE, "2 - Stamped Pictures")
F3 = os.path.join(BASE, "3 - Originals Already Stamped")
SETTINGS = os.path.join(BASE, "stamper-settings.json")
DEFAULTS = {"position": "bottom-right", "size": 4.0}  # size = % of photo height

POSITIONS = [
    ["top-left", "top-center", "top-right"],
    ["middle-left", "middle-center", "middle-right"],
    ["bottom-left", "bottom-center", "bottom-right"],
]


def resource(name):
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, name)


def load_settings():
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            s = {**DEFAULTS, **json.load(f)}
        if s["position"] not in sum(POSITIONS, []):
            s["position"] = DEFAULTS["position"]
        s["size"] = min(12.0, max(1.0, float(s["size"])))
        return s
    except Exception:
        return dict(DEFAULTS)


def save_settings(s):
    try:
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(s, f)
    except OSError:
        pass


def make_folders():
    for p in (F1, F2, F3):
        os.makedirs(p, exist_ok=True)


def list_pictures(folder):
    try:
        return sorted(n for n in os.listdir(folder)
                      if n.lower().endswith(EXTS) and os.path.isfile(os.path.join(folder, n)))
    except OSError:
        return []


def open_folder(path):
    make_folders()
    os.startfile(path)


def photo_date(img):
    """Date the photo was taken, from its hidden EXIF data, or None."""
    try:
        exif = img.getexif()
        candidates = []
        sub = exif.get_ifd(0x8769)  # Exif sub-block: DateTimeOriginal / Digitized
        candidates += [sub.get(0x9003), sub.get(0x9004), exif.get(0x0132)]
        for raw in candidates:
            if raw:
                if isinstance(raw, bytes):
                    raw = raw.decode("ascii", "ignore")
                try:
                    return datetime.strptime(raw.strip("\x00 "), "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    continue
    except Exception:
        pass
    return None


def format_date(d):
    hour = d.hour % 12 or 12
    return f"{d.month}/{d.day}/{d.year} {hour}:{d.minute:02d} {'AM' if d.hour < 12 else 'PM'}"


def get_font(px):
    for name in ("arialbd.ttf", "arial.ttf", "segoeuib.ttf"):
        try:
            return ImageFont.truetype(os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", name), px)
        except OSError:
            continue
    return ImageFont.load_default(size=px)


def draw_stamp(img, text, position, size_pct):
    """White text with a black outline, so it reads on any background."""
    img = img.convert("RGB")
    w, h = img.size
    px = max(12, int(h * size_pct / 100))
    font = get_font(px)
    outline = max(2, px // 10)
    draw = ImageDraw.Draw(img)
    l, t, r, b = draw.textbbox((0, 0), text, font=font, stroke_width=outline)
    tw, th = r - l, b - t
    margin = max(6, int(px * 0.6))
    row, col = position.split("-")
    x = {"left": margin, "center": (w - tw) // 2, "right": w - tw - margin}[col]
    y = {"top": margin, "middle": (h - th) // 2, "bottom": h - th - margin}[row]
    draw.text((x - l, y - t), text, font=font, fill="white", stroke_width=outline, stroke_fill="black")
    return img


def unique_path(folder, name):
    base, ext = os.path.splitext(name)
    p, n = os.path.join(folder, name), 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{base} ({n}){ext}")
        n += 1
    return p


def stamp_one(name, settings):
    """Returns (ok, message). Original moves to folder 3 only after the stamped copy is saved."""
    src = os.path.join(F1, name)
    with Image.open(src) as im:
        taken = photo_date(im)
        if taken is None:
            return False, "has no date saved in it"
        exif = im.getexif()
        img = ImageOps.exif_transpose(im)  # turn sideways phone photos upright first
        exif = img.getexif() if img is not im else exif
        exif[0x0112] = 1  # orientation now baked in
        stamped = draw_stamp(img, format_date(taken), settings["position"], settings["size"])
        out = unique_path(F2, name)
        stamped.save(out, "JPEG", quality=95, exif=exif.tobytes())
    ts = taken.timestamp()
    try:
        os.utime(out, (ts, ts))
    except OSError:
        pass
    shutil.move(src, unique_path(F3, name))
    return True, ""


# ---------------------------------------------------------------- UI
class PlacementWindow(tk.Toplevel):
    def __init__(self, parent, settings, on_save):
        super().__init__(parent)
        self.title("Stamp Position and Size")
        self.resizable(False, False)
        self.transient(parent)
        self.on_save = on_save
        self.pos = tk.StringVar(value=settings["position"])
        self.size = tk.DoubleVar(value=settings["size"])
        self.sample = self._load_sample()

        tk.Label(self, text="Click where the date should go:", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 4), padx=10)
        grid = tk.Frame(self)
        grid.grid(row=1, column=0, padx=10, sticky="n")
        for r, row in enumerate(POSITIONS):
            for c, p in enumerate(row):
                tk.Radiobutton(grid, variable=self.pos, value=p, indicatoron=False, width=4, height=2,
                               text=["↖", "↑", "↗", "←", "•", "→", "↙", "↓", "↘"][r * 3 + c],
                               font=("Segoe UI", 14), command=self.refresh).grid(row=r, column=c, padx=2, pady=2)
        tk.Label(self, text="How big?", font=("Segoe UI", 12, "bold")).grid(row=2, column=0, pady=(12, 0))
        tk.Scale(self, variable=self.size, from_=1, to=12, resolution=0.5, orient="horizontal", length=200,
                 showvalue=False, command=lambda _v: self.refresh()).grid(row=3, column=0, padx=10)
        tk.Label(self, text="smaller  ←→  bigger").grid(row=4, column=0)

        self.preview = tk.Label(self, bd=1, relief="solid")
        self.preview.grid(row=1, column=1, rowspan=4, padx=10, pady=4)
        tk.Button(self, text="Save and Close", font=("Segoe UI", 12, "bold"), command=self.save,
                  bg="#2e7d32", fg="white").grid(row=5, column=0, columnspan=2, pady=10, ipadx=10, ipady=3)
        self.refresh()

    def _load_sample(self):
        for n in list_pictures(F1):
            try:
                with Image.open(os.path.join(F1, n)) as im:
                    img = ImageOps.exif_transpose(im).convert("RGB")
                    img.thumbnail((360, 360))
                    return img
            except Exception:
                continue
        img = Image.new("RGB", (360, 270), (110, 150, 190))  # plain sample if she has no photos yet
        ImageDraw.Draw(img).ellipse((120, 70, 240, 190), fill=(240, 220, 120))
        return img

    def refresh(self):
        demo = draw_stamp(self.sample.copy(), "10/3/2026 2:07 PM", self.pos.get(), self.size.get())
        self.tkimg = ImageTk.PhotoImage(demo)
        self.preview.configure(image=self.tkimg)

    def save(self):
        self.on_save({"position": self.pos.get(), "size": float(self.size.get())})
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        try:
            self.iconbitmap(resource("stamper.ico"))
        except tk.TclError:
            pass
        self.resizable(False, False)
        self.settings = load_settings()
        self.running = False
        make_folders()

        tk.Label(self, text="STAMPER", font=("Segoe UI", 22, "bold")).pack(pady=(12, 0))
        tk.Label(self, text="Puts the date and time on your photos.", font=("Segoe UI", 11)).pack()

        self.count1 = self._step(1, "Make sure your unmarked pictures are in this folder!",
                                 "Open Folder 1", lambda: open_folder(F1))
        self._step2()
        self.count2 = self._step(3, "Check this folder for your stamped pictures!",
                                 "Open Folder 2 (Stamped)", lambda: open_folder(F2))
        self.count3 = self._step(4, "Check this folder to see your original pictures that have been stamped already.",
                                 "Open Folder 3 (Originals)", lambda: open_folder(F3))
        self.status = tk.Label(self, text="", font=("Segoe UI", 11), wraplength=520, justify="left")
        self.status.pack(padx=14, pady=(2, 12), anchor="w")
        self.update_counts()

    def _box(self, num, text):
        f = tk.LabelFrame(self, text=f" Step {num} ", font=("Segoe UI", 12, "bold"), padx=10, pady=6)
        f.pack(fill="x", padx=14, pady=6)
        tk.Label(f, text=text, font=("Segoe UI", 11), wraplength=500, justify="left").pack(anchor="w")
        return f

    def _step(self, num, text, button_text, cmd):
        f = self._box(num, text)
        row = tk.Frame(f)
        row.pack(fill="x", pady=(6, 0))
        tk.Button(row, text=button_text, font=("Segoe UI", 12), command=cmd).pack(side="left", ipadx=6, ipady=2)
        count = tk.Label(row, text="", font=("Segoe UI", 11, "bold"))
        count.pack(side="left", padx=12)
        return count

    def _step2(self):
        f = self._box(2, "Press this button to put the date and time on your pictures.")
        row = tk.Frame(f)
        row.pack(fill="x", pady=(6, 0))
        self.go = tk.Button(row, text="GO - Stamp My Pictures", font=("Segoe UI", 14, "bold"),
                            bg="#2e7d32", fg="white", command=self.start)
        self.go.pack(side="left", ipadx=10, ipady=4)
        tk.Button(row, text="Stamp position and size...", font=("Segoe UI", 11),
                  command=lambda: PlacementWindow(self, self.settings, self.set_settings)).pack(side="left", padx=12)
        self.bar = ttk.Progressbar(f, length=480, mode="determinate")
        self.bar.pack(pady=(8, 0))

    def set_settings(self, s):
        self.settings = s
        save_settings(s)

    def update_counts(self):
        make_folders()
        n1, n2, n3 = (len(list_pictures(p)) for p in (F1, F2, F3))
        self.count1.config(text=f"{n1} picture{'s' if n1 != 1 else ''} waiting")
        self.count2.config(text=f"{n2} stamped")
        self.count3.config(text=f"{n3} originals")

    def start(self):
        if self.running:
            return
        make_folders()
        names = list_pictures(F1)
        if not names:
            messagebox.showinfo(APP_NAME, "There are no pictures in Folder 1.\n\nPress the Step 1 button, "
                                          "put your pictures in that folder, then try again.")
            return
        self.running = True
        self.go.config(state="disabled", text="Working... please wait")
        self.bar.config(maximum=len(names), value=0)
        threading.Thread(target=self.work, args=(names, dict(self.settings)), daemon=True).start()

    def work(self, names, settings):
        done, problems = 0, []
        for i, n in enumerate(names, 1):
            try:
                ok, why = stamp_one(n, settings)
                if ok:
                    done += 1
                else:
                    problems.append(f"{n}: {why}")
            except Exception as e:
                problems.append(f"{n}: could not be stamped ({e})")
            self.after(0, self.progress, i, len(names))
        self.after(0, self.finish, done, problems)

    def progress(self, i, total):
        self.bar.config(value=i)
        self.status.config(text=f"Stamping picture {i} of {total}...")

    def finish(self, done, problems):
        self.running = False
        self.go.config(state="normal", text="GO - Stamp My Pictures")
        self.update_counts()
        msg = f"All done! {done} picture{'s' if done != 1 else ''} stamped."
        if problems:
            msg += (f"\n\n{len(problems)} picture{'s were' if len(problems) != 1 else ' was'} left in "
                    "Folder 1 because they could not be stamped:\n" + "\n".join(problems[:10]))
            if len(problems) > 10:
                msg += f"\n...and {len(problems) - 10} more"
        self.status.config(text=msg)
        messagebox.showinfo(APP_NAME, msg + ("\n\nNow press Step 3 to see them." if done else ""))


if __name__ == "__main__":
    App().mainloop()
