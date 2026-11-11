"""Generate a football-manager-themed FLIX Director app icon."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

S=1024
im=Image.new("RGB",(S,S))
px=im.load()
for y in range(S):
    for x in range(S):
        glow=max(0,1-math.hypot((x-510)/760,(y-300)/780))
        px[x,y]=(int(7+16*glow),int(27+37*glow),int(27+30*glow))
d=ImageDraw.Draw(im)
# Football tactical pitch on a manager's board
d.rounded_rectangle((132,102,892,695),radius=62,fill="#163e35",outline="#d7b65c",width=17)
for x in [164,860]:
    d.line([(x,149),(x,657)],fill="#80b8a0",width=9)
for y in [149,657]:
    d.line([(164,y),(860,y)],fill="#80b8a0",width=9)
d.line([(512,149),(512,657)],fill="#80b8a0",width=8)
d.ellipse((407,294,617,504),outline="#80b8a0",width=8)
d.rectangle((164,291,293,519),outline="#80b8a0",width=8)
d.rectangle((731,291,860,519),outline="#80b8a0",width=8)
# Coach's tactical player markers
for x,y,c in [(267,245,"#f5d66e"),(371,387,"#f5d66e"),(293,550,"#f5d66e"),(670,242,"#e8e8ec"),(736,383,"#e8e8ec"),(654,551,"#e8e8ec")]:
    d.ellipse((x-31,y-31,x+31,y+31),fill=c,outline="#09251e",width=6)
d.line([(371,387),(480,450),(600,404)],fill="#ffd85d",width=16)
d.polygon([(600,404),(553,386),(566,433)],fill="#ffd85d")
font_paths=["/System/Library/Fonts/Supplemental/Arial Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
font_path=next((p for p in font_paths if Path(p).exists()),None)
def write(text,y,size,color,stroke):
    f=ImageFont.truetype(font_path,size) if font_path else ImageFont.load_default()
    bb=d.textbbox((0,0),text,font=f,stroke_width=stroke)
    x=(S-(bb[2]-bb[0]))/2-bb[0]
    d.text((x,y),text,font=f,fill=color,stroke_width=stroke,stroke_fill="#041814")
write("FLIX",715,126,"#ffffff",5)
write("DIRECTOR",851,91,"#f5d66e",4)
target=Path("ios/App/App/Assets.xcassets/AppIcon.appiconset")
target.mkdir(parents=True,exist_ok=True)
im.save(target/"AppIcon-512@2x.png",format="PNG",optimize=True)
(target/"Contents.json").write_text('{"images":[{"filename":"AppIcon-512@2x.png","idiom":"universal","platform":"ios","size":"1024x1024"}],"info":{"author":"xcode","version":1}}')
print("Generated football manager FLIX Director icon.")
