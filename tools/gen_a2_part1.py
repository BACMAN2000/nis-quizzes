#!/usr/bin/env python3
"""Regenerate A2 Part 1 as 5 separate mp3 (one per conversation), with lead-in.
Output: mp3/A2/A2-P1-q1.mp3 ... A2-P1-q5.mp3.  Run from repo root."""
import os, re, subprocess, tempfile, json, urllib.request, time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY=open(os.path.join(ROOT,"A2 Level.txt"),encoding="utf-8").read().strip()
OUT=os.path.join(ROOT,"mp3","A2"); os.makedirs(OUT,exist_ok=True)
MODEL="eleven_multilingual_v2"; FMT="mp3_44100_128"
V_F="FGY2WhTYpPnrIDTdsKH5"; V_M="TX3LPaxmHKxFdv7VOQHJ"; V_N="JBFqnCBsd6RMkjVDRZzb"
FEMALE={"Girl","Woman","Mum"}; MALE={"Boy","Man"}
SPK=re.compile(r'\s*\b(Girl|Boy|Woman|Man|Mum):\s*')
CONVS=[
 "Question one. Girl: What did you get Mum for her birthday? Boy: I wanted to buy her a book, but in the end I made her a chocolate cake. She loved it.",
 "Question two. Boy: Shall we meet at the cafe on Saturday? Girl: It's a lovely day, let's meet in the park instead. Boy: OK, the park it is.",
 "Question three. Woman: Do you want to walk to the shops? Man: Have you looked outside? It's raining really hard. Woman: Oh, then let's wait.",
 "Question four. Mum: What's the matter? Girl: I can't find my phone anywhere. I think I left it on the bus. Mum: Don't worry, we'll call it.",
 "Question five. Boy: What time does the film start? Girl: At half past eight, not eight o'clock. Boy: Good, then we have time for dinner first.",
]
def vfor(s): return V_F if s in FEMALE else V_M if s in MALE else V_N
def segs(sc):
    p=SPK.split(sc); out=[]; lead=p[0].strip()
    if lead: out.append((V_N,lead))
    for i in range(1,len(p),2):
        t=p[i+1].strip() if i+1<len(p) else ""
        if t: out.append((vfor(p[i]),t))
    return out
def tts(vid,txt,dest):
    body=json.dumps({"text":txt,"model_id":MODEL,"voice_settings":{"stability":0.45,"similarity_boost":0.8}}).encode()
    req=urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format={FMT}",
        data=body,method="POST",headers={"xi-api-key":KEY,"Content-Type":"application/json","Accept":"audio/mpeg"})
    with urllib.request.urlopen(req,timeout=120) as r,open(dest,"wb") as f: f.write(r.read())
def main():
    tmp=tempfile.mkdtemp(prefix="p1_")
    sil=os.path.join(tmp,"s.mp3"); lead=os.path.join(tmp,"l.mp3")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t","0.5","-q:a","9",sil],check=True,capture_output=True)
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t","1.5","-q:a","9",lead],check=True,capture_output=True)
    for n,sc in enumerate(CONVS,1):
        files=[lead]
        for j,(vid,txt) in enumerate(segs(sc)):
            seg=os.path.join(tmp,f"{n}_{j}.mp3"); print(f"  q{n} seg {j+1}..."); tts(vid,txt,seg); files+=[seg,sil]; time.sleep(0.15)
        lst=os.path.join(tmp,f"{n}.txt"); open(lst,"w",encoding="utf-8").write("".join(f"file '{f.replace(os.sep,'/')}'\n" for f in files))
        out=os.path.join(OUT,f"A2-P1-q{n}.mp3")
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c:a","libmp3lame","-q:a","4",out],check=True,capture_output=True)
        print(f"OK A2-P1-q{n}.mp3 ({os.path.getsize(out)//1024} KB)")
    print("DONE")
main()
