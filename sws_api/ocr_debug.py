import sqlite3, sys
from PIL import Image, ImageOps
import pytesseract

db = sqlite3.connect("sws.db"); db.row_factory = sqlite3.Row
t = db.execute("SELECT Name, Season, Picture FROM Teams LIMIT 1").fetchone()
path = t["Picture"].lstrip("/")
im = Image.open(path)
print("plik:", path, "rozmiar:", im.size)
w, h = im.size
crop = im.convert("L").crop((0, h // 2, w // 2, h))
crop = ImageOps.autocontrast(crop.resize((crop.width * 3, crop.height * 3)))
crop.save("debug_crop.png")
for psm in (6, 4, 11):
    print(f"\n===== PSM {psm} =====")
    print(pytesseract.image_to_string(crop, config=f"--psm {psm}")[:900])
