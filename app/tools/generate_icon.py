"""Create a 1024px iOS app icon for FLIX Director (opaque PNG)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math

S = 1024
im = Image.new("RGB", (S, S), "#0b1020")
p = im.load()
for y in range(S):
    for x in range(S):
        glow = max(0, 1-math.hypot((x-520)/820, (y-220)/640))
        p[x,y]=(int(11+67*glow),int(16+17*glow),int(32+12*glow))
d = ImageDraw.Draw(im)
# Golden stage light halo
for r in range(355, 175, -4):
    alpha=(355-r)/180
    color=(int(80+40*alpha),int(34+17*alpha),int(28+6*alpha))
    d.ellipse((512-r, 414-r, 512+r, 414+r), outline=color, width=3)
# Red clapperboard
d.rounded_rectangle((189,250,836,628), radius=34, fill="#161923",outline="#eb3a30",width=16)
d.polygon([(200,255),(812,180),(829,284),(215,364)],fill="#eeeeed")
for i in range(6):
    x=225+i*100
    d.polygon([(x,254-i*12),(x+45,247-i*12),(x+104,321-i*12),(x+55,329-i*12)],fill="#1d2330")
d.rounded_rectangle((225,370,799,591),radius=12,fill="#191b24")
# Film camera lens
d.ellipse((405,399,619,576),fill="#d8432b",outline="#f6ab47",width=13)
d.ellipse((462,445,560,541),fill="#171c31",outline="#fff2bb",width=10)
# White title and gold DIRECTOR
fontpaths=[
"/System/Library/Fonts/Supplemental/Arial Bold.ttf",
"/System/Library/Fonts/Supplemental/Arial.ttf",
"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
]
fontfile=next((v for v in fontpaths if Path(v).exists()), None)
def font(size):
    return ImageFont.truetype(fontfile,size) if fontfile else ImageFont.load_default()
def center(s,y,size,color,stroke=0,stroke_fill="#17111b"):
    f=font(size)
    bb=d.textbbox((0,0),s,font=f,stroke_width=stroke)
    x=(S-(bb[2]-bb[0]))/2-bb[0]
    d.text((x,y),s,font=f,fill=color,stroke_width=stroke,stroke_fill=stroke_fill)
center("FLIX",645,190,"#ffffff",9,"#b62225")
center("DIRECTOR",825,84,"#ffcb51",4,"#3a1115")
out=Path("ios/App/App/Assets.xcassets/AppIcon.appiconset")
out.mkdir(parents=True,exist_ok=True)
im.save(out/"AppIcon-512@2x.png",format="PNG",optimize=True)
(out/"Contents.json").write_text('{"images":[{"filename":"AppIcon-512@2x.png","idiom":"universal","platform":"ios","size":"1024x1024"}],"info":{"author":"xcode","version":1}}')
print("FLIX Director icon installed")
