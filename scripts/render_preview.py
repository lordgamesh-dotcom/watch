#!/usr/bin/env python3
"""Render a 480px circular cyberpunk watch face preview with Pillow."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "watchface/src/main/res/drawable-nodpi/preview.png"
S=2; im=Image.new("RGBA",(480*S,480*S),(0,0,0,255)); d=ImageDraw.Draw(im)
def xy(v): return int(v*S)
cyan="#19E6FF"; yellow="#F5EB0A"; red="#FF2D4A"; green="#3DFF8A"; orange="#FF8A1F"
for i in range(120):
    a=math.radians(i*3-90); r=230; x=240+r*math.cos(a); y=240+r*math.sin(a)
    d.line((xy(x),xy(y),xy(x-8*math.cos(a)),xy(y-8*math.sin(a))),fill=(25,230,255,115),width=xy(2))
d.ellipse((xy(25),xy(25),xy(455),xy(455)),outline=(25,230,255,65),width=xy(1))
for a,c in [(-135,cyan),(-45,red),(45,cyan),(135,red)]:
    d.arc((xy(18),xy(18),xy(462),xy(462)),start=a-14,end=a+14,fill=c,width=xy(4))
for y in range(50,440,4): d.line((0,xy(y),xy(480),xy(y)),fill=(25,230,255,12),width=1)
def font(name,size):
    candidates=[Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    return ImageFont.truetype(str(candidates[0]),xy(size))
def text_center(s,y,size,color):
    f=font('',size); box=d.textbbox((0,0),s,font=f); d.text(((480*S-(box[2]-box[0]))/2,xy(y)),s,font=f,fill=color)
text_center("B A T T     87%",61,18,green)
for i in range(9): d.polygon([(xy(150+i*19),xy(84)),(xy(165+i*19),xy(84)),(xy(161+i*19),xy(97)),(xy(146+i*19),xy(97))],fill=green)
text_center("QUI  //  05.NOV.26",110,16,cyan)
text_center("10:09",148,88,yellow)
d.line((xy(70),xy(246),xy(210),xy(246),xy(216),xy(252),xy(264),xy(252),xy(270),xy(246),xy(410),xy(246)),fill=cyan,width=xy(2))
for x,c,val,glyph,label in [(135,red,"72","♥","BPM"),(240,cyan,"8432","»","PASSOS"),(345,orange,"34","△","STRESS")]:
    d.ellipse((xy(x-47),xy(285),xy(x+47),xy(379)),outline=(120,120,120,90),width=xy(1)); d.ellipse((xy(x-40),xy(292),xy(x+40),xy(372)),outline=c,width=xy(6));
    f=font('',18); b=d.textbbox((0,0),glyph,font=f); d.text((xy(x)-(b[2]-b[0])/2,xy(302)),glyph,font=f,fill=c)
    f=font('',20 if label!="PASSOS" else 16); b=d.textbbox((0,0),val,font=f); d.text((xy(x)-(b[2]-b[0])/2,xy(330)),val,font=f,fill="white")
    f=font('',13); b=d.textbbox((0,0),label,font=f); d.text((xy(x)-(b[2]-b[0])/2,xy(384)),label,font=f,fill=c)
d.rectangle((xy(190),xy(428),xy(290),xy(434)),fill=yellow)
im=im.resize((480,480),Image.Resampling.LANCZOS)
mask=Image.new('L',(480,480),0)
ImageDraw.Draw(mask).ellipse((1,1,479,479),fill=255)
im.putalpha(mask)
im.save(OUT)
print(OUT)
