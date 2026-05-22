#!/usr/bin/env python3
"""Generate C1 Listening audio with ElevenLabs. Run from repo root.
Outputs mp3/C1/C1-P1-q1..q6 (per extract), C1-P2, C1-P3, C1-P4."""
import os, re, subprocess, tempfile, json, urllib.request, time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY=open(os.path.join(ROOT,"A2 Level.txt"),encoding="utf-8").read().strip()
OUT=os.path.join(ROOT,"mp3","C1"); os.makedirs(OUT,exist_ok=True)
MODEL="eleven_multilingual_v2"; FMT="mp3_44100_128"
V_F="FGY2WhTYpPnrIDTdsKH5"; V_M="TX3LPaxmHKxFdv7VOQHJ"; V_N="JBFqnCBsd6RMkjVDRZzb"
FEMALE={"Woman","Helena"}; MALE={"Man","Marcus"}
SPK=re.compile(r'\s*\b(Woman|Man|Interviewer|Marcus|Helena):\s*')
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
    with urllib.request.urlopen(req,timeout=180) as r,open(dest,"wb") as f: f.write(r.read())
JOBS=[
 ("C1-P1-q1","Question one. Woman: I've finished the slides for Monday. Man: They look great, very thorough. If anything, I'd cut about half of them. People stop listening when there's too much detail, and your strongest points get lost."),
 ("C1-P1-q2","Question two. Man: Did you enjoy the novel? Woman: The plot was a bit predictable, to be honest, and some characters felt flat. But the way the author describes the city, almost like a living thing, that's what stayed with me."),
 ("C1-P1-q3","Question three. Woman: So we'd booked the restaurant for the view, which everyone had praised. The food, surprisingly, was excellent. What let it down was the service: we waited nearly an hour between courses, and nobody apologised."),
 ("C1-P1-q4","Question four. Man: I've read your report. The research itself is solid and the data's convincing. My only real concern is the conclusion, it overstates what the figures actually show. I'd be more cautious there."),
 ("C1-P1-q5","Question five. Woman: When we ran the experiment, we expected the warmer samples to react faster. In fact, they barely changed at all. It was the cold samples that transformed completely, which nobody had predicted."),
 ("C1-P1-q6","Question six. Man: Have you decided about the job offer? Woman: I have, actually. The salary's tempting and it's a real step up, but it would mean relocating, and right now keeping my family settled matters more to me than any promotion."),
 ("C1-P2","Hello, I'm Helena, and I keep bees on rooftops here in the city. People are often surprised to learn that city honey is frequently purer than honey from the countryside, mainly because there are fewer pesticides. I started keeping bees five years ago, after I inherited a single hive from my uncle. Today I look after twelve hives across the city. A common myth is that bees are dangerous, but in fact they only sting when they feel threatened. The biggest challenge for a beekeeper isn't the bees, it's actually the weather, especially long periods of rain. Each hive can produce up to twenty kilograms of honey a year. If you want to start, the most important piece of equipment is a good smoker, which keeps the bees calm. And my final tip: never open a hive in the afternoon, always do it in the morning."),
 ("C1-P3","Interviewer: Marcus, what first drew you to marine biology? Marcus: Everyone assumes it was childhood holidays by the sea, but actually I grew up far inland. It was a single documentary I watched at fifteen that changed everything. Interviewer: Your research focuses on coral. Why coral specifically? Marcus: Because coral reefs are like the rainforests of the ocean. They cover a tiny fraction of the sea floor, yet they support a quarter of all marine species. If they go, the consequences are unimaginable. Interviewer: Is your work mostly underwater? Marcus: People picture me diving all day, but honestly I spend far more time analysing data in the lab than in the water. The diving is the small, glamorous part. Interviewer: What's the biggest misconception about coral? Marcus: That it's a plant. It's actually an animal, and that distinction matters enormously for how we protect it. Interviewer: Are you optimistic about the future? Marcus: I'm cautiously hopeful. The science is alarming, but I've seen damaged reefs recover surprisingly quickly when given the chance. Interviewer: What advice would you give a young scientist? Marcus: Don't specialise too early. The most interesting discoveries happen at the borders between subjects. Interviewer: Marcus, thank you."),
 ("C1-P4","Speaker one. Woman: I'd been a lawyer for fifteen years and I was simply bored, the same cases over and over. So I retrained as a teacher. The hardest thing now? Honestly, it's the drop in income, I earn about half what I used to. Speaker two. Man: I loved my office job, but a serious illness made me rethink everything. I now run a small bakery. The baking I adore, but I never expected how lonely it would feel working on my own all day. Speaker three. Woman: I was made redundant when the factory closed, so the change wasn't really my choice. I became a nurse. The most difficult part is learning so many new skills at my age, it's exhausting but rewarding. Speaker four. Man: I'd always dreamed of being a photographer, so I finally followed my passion and quit accounting. The work is wonderful, but the uncertainty is hard, never knowing if there'll be money coming in next month. Speaker five. Woman: A friend offered me a job in her travel company completely out of the blue, and I took the chance. I love it, but the hours are brutal, far longer than I ever worked before."),
]
def main():
    tmp=tempfile.mkdtemp(prefix="c1_")
    sil=os.path.join(tmp,"s.mp3"); lead=os.path.join(tmp,"l.mp3")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t","0.5","-q:a","9",sil],check=True,capture_output=True)
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t","1.5","-q:a","9",lead],check=True,capture_output=True)
    for name,sc in JOBS:
        files=[lead]
        for j,(vid,txt) in enumerate(segs(sc)):
            seg=os.path.join(tmp,f"{name}_{j}.mp3"); print(f"  {name} seg {j+1}..."); tts(vid,txt,seg); files+=[seg,sil]; time.sleep(0.12)
        lst=os.path.join(tmp,f"{name}.txt"); open(lst,"w",encoding="utf-8").write("".join(f"file '{f.replace(os.sep,'/')}'\n" for f in files))
        out=os.path.join(OUT,f"{name}.mp3")
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c:a","libmp3lame","-q:a","4",out],check=True,capture_output=True)
        print(f"OK {name}.mp3 ({os.path.getsize(out)//1024} KB)")
    print("DONE")
main()
