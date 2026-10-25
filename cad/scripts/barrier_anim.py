#!/usr/bin/env python3
"""Render the demo boom barrier 0 -> 90 deg (12 frames) with OpenSCAD and assemble a GIF.
Usage: python3 cad/scripts/barrier_anim.py   (needs openscad, xvfb-run, Pillow)
Output: cad/renders/barrier_anim.gif (+ frames in cad/renders/anim_frames/)
"""
import os, subprocess
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAD = os.path.join(HERE, "openscad", "barrier_assembly.scad")
OUT = os.path.join(HERE, "renders")
FR = os.path.join(OUT, "anim_frames")
os.makedirs(FR, exist_ok=True)

N = 12
frames = []
# fixed camera (no --viewall) so the scene does not jump between frames
cam = "350,-200,850,62,0,35,5600"
for i in range(N):
    ang = 90.0 * i / (N - 1)
    png = os.path.join(FR, f"barrier_{i:02d}.png")
    subprocess.run(["xvfb-run", "-a", "openscad", "-q", "-o", png, "--imgsize=1200,900",
                    "--colorscheme=Tomorrow", f"--camera={cam}", "--projection=o",
                    "-D", f"boom_angle={ang:.2f}", SCAD], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    im = Image.open(png).convert("RGB")
    d = ImageDraw.Draw(im)
    d.text((30, 30), f"ParkFlow demo barrier - boom {ang:4.1f} deg", fill=(40, 40, 40))
    frames.append(im)
    print(f"frame {i}: {ang:.1f} deg")

seq = frames + [frames[-1]] * 3 + frames[::-1] + [frames[0]] * 3
pal = [f.quantize(colors=128, method=Image.MEDIANCUT) for f in seq]
gif = os.path.join(OUT, "barrier_anim.gif")
pal[0].save(gif, save_all=True, append_images=pal[1:], duration=120, loop=0, optimize=True)
print("wrote", gif)
