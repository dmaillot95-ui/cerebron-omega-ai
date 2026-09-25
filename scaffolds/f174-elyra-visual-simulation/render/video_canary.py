#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, math
from pathlib import Path

W,H=320,180
BG=(12,16,24)
FG=(220,226,235)
ACCENT=(120,180,255)
GROUND=(65,75,90)

def canvas():
    return [list(BG)*W for _ in range(H)]

def setpx(img,x,y,c):
    if 0<=x<W and 0<=y<H:
        row=img[y]
        i=x*3
        row[i:i+3]=c

def line(img,x0,y0,x1,y1,c):
    dx=abs(x1-x0); sx=1 if x0<x1 else -1
    dy=-abs(y1-y0); sy=1 if y0<y1 else -1
    err=dx+dy
    while True:
        setpx(img,x0,y0,c)
        if x0==x1 and y0==y1: break
        e2=2*err
        if e2>=dy: err+=dy; x0+=sx
        if e2<=dx: err+=dx; y0+=sy

def circle(img,cx,cy,r,c,fill=True):
    rr=r*r
    for y in range(cy-r,cy+r+1):
        for x in range(cx-r,cx+r+1):
            d=(x-cx)*(x-cx)+(y-cy)*(y-cy)
            if (d<=rr if fill else rr-r*2<=d<=rr+r*2):
                setpx(img,x,y,c)

def rect(img,x0,y0,x1,y1,c):
    for y in range(max(0,y0),min(H,y1+1)):
        row=img[y]
        for x in range(max(0,x0),min(W,x1+1)):
            i=x*3
            row[i:i+3]=c

def render_frame(index,total):
    img=canvas()
    line(img,0,150,W-1,150,GROUND)
    phase=index/max(1,total-1)
    cx=70+int(180*phase)
    bob=int(4*math.sin(phase*math.pi*2))
    cy=86+bob

    # head + torso
    circle(img,cx,cy-35,12,FG,True)
    rect(img,cx-8,cy-20,cx+8,cy+22,ACCENT)

    # limbs
    swing=int(14*math.sin(phase*math.pi*4))
    line(img,cx-5,cy-8,cx-25,cy+5+swing,FG)
    line(img,cx+5,cy-8,cx+25,cy+5-swing,FG)
    line(img,cx-5,cy+22,cx-16,cy+52-swing//2,FG)
    line(img,cx+5,cy+22,cx+16,cy+52+swing//2,FG)

    # simple progress bar
    rect(img,18,164,301,170,(35,42,55))
    rect(img,18,164,18+int(283*phase),170,ACCENT)
    return img

def ppm_bytes(img):
    header=f"P6\n{W} {H}\n255\n".encode()
    body=bytearray()
    for row in img:
        body.extend(row)
    return header+bytes(body)

def generate(out_dir:Path,frames:int):
    if not (2<=frames<=240):
        raise ValueError("frames must be between 2 and 240")
    out_dir.mkdir(parents=True,exist_ok=True)
    hashes=[]
    for i in range(frames):
        raw=ppm_bytes(render_frame(i,frames))
        p=out_dir/f"frame_{i:03d}.ppm"
        p.write_bytes(raw)
        hashes.append(hashlib.sha256(raw).hexdigest())
    sequence_hash=hashlib.sha256("\n".join(hashes).encode()).hexdigest()
    return sequence_hash

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",default="artifacts/frames")
    ap.add_argument("--frames",type=int,default=24)
    args=ap.parse_args()
    seq=generate(Path(args.out_dir),args.frames)
    print(f"frames={args.frames}")
    print(f"sequence_sha256={seq}")
    print("physical_validation_claimed=false")
    print("video_production_claimed=false")

if __name__=="__main__":
    main()
