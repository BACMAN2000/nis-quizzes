#!/usr/bin/env python3
"""Generate B2 Listening audio with ElevenLabs (young/adult voices). Run from repo root.
Outputs mp3/B2/B2-P1-q1..q8 (per extract), B2-P2, B2-P3, B2-P4."""
import os, re, subprocess, tempfile, json, urllib.request, time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY=open(os.path.join(ROOT,"A2 Level.txt"),encoding="utf-8").read().strip()
OUT=os.path.join(ROOT,"mp3","B2"); os.makedirs(OUT,exist_ok=True)
MODEL="eleven_multilingual_v2"; FMT="mp3_44100_128"
V_F="FGY2WhTYpPnrIDTdsKH5"; V_M="TX3LPaxmHKxFdv7VOQHJ"; V_N="JBFqnCBsd6RMkjVDRZzb"
FEMALE={"Woman","Girl","Sofia"}; MALE={"Man","Boy"}
SPK=re.compile(r'\s*\b(Woman|Man|Girl|Boy|Teacher|Interviewer|Sofia):\s*')
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
 ("B2-P1-q1","Question one. Woman: So, what did you think of the film? Man: Honestly, the actors were brilliant and it looked beautiful, but it went on far too long. By the end I just wanted it to finish."),
 ("B2-P1-q2","Question two. Man: Hello, I'm calling about the table I ordered. Woman: Has it not arrived? Man: Oh, it arrived this morning, on time, but one of the legs is badly scratched. I'd like it replaced."),
 ("B2-P1-q3","Question three. Teacher: Right, the exam is on Friday. I'm not going to tell you to study all night, that never helps. The most important thing is to get a good night's sleep, so you can think clearly."),
 ("B2-P1-q4","Question four. Woman: How's the new job going? Girl: Everyone keeps asking if I'm nervous, but I'm not at all. I genuinely can't wait to get started. It's exactly what I've always wanted to do."),
 ("B2-P1-q5","Question five. Man: Shall we go to the mountains this summer? Woman: We did that last year. I'd love to be by the sea this time. Man: You're right, let's book somewhere on the coast."),
 ("B2-P1-q6","Question six. Woman: This is a reminder that Saturday's concert will now take place at the Riverside Hall, not the Town Theatre as printed on your tickets. The date and time are unchanged."),
 ("B2-P1-q7","Question seven. Boy: We lost three nil. Girl: Was it the rain? Boy: No, the pitch was fine. The problem was that our best striker twisted his ankle in the first ten minutes, and after that we couldn't score."),
 ("B2-P1-q8","Question eight. Woman: I bought this jacket last week, but it's too small. Man: Would you like a larger size? Woman: Actually, I've changed my mind about it completely, so I'd just like my money back."),
 ("B2-P2","Hi everyone, I'm Daniel and I volunteer at the city wildlife park. The park first opened in nineteen ninety-eight, and today it relies on around fifty volunteers like me. Most of us help mainly with feeding the animals, which is my favourite job. Before you start, the training takes three weeks, so you really learn what you're doing. Without doubt, the most popular animals with visitors are the otters, and we're all very excited because a brand-new reptile section is opening in March. There are a few rules: volunteers must be over sixteen, and because it gets muddy, you have to wear waterproof boots. We don't provide food, so please bring your own lunch. If you'd like to join us, the only thing you need to do is fill in a form on our website. We'd love to have you!"),
 ("B2-P3","Speaker one. Woman: I'd been feeling really tense at work for months. A colleague said running might help, and honestly, after a long run my mind feels completely clear. It's the only thing that calms me down. Speaker two. Man: My sister signed up for a marathon to support a hospital, and I didn't want her doing it alone, so I joined her. We collected quite a lot of money in the end. Speaker three. Woman: I spend all day inside, staring at a screen. For me, running isn't really about fitness, it's just the chance to be outside in the fresh air and see the sky. Speaker four. Man: My check-up wasn't great, and the doctor told me very clearly that I needed to start exercising. So really, I had no choice, I started the very next morning. Speaker five. Woman: I was new in town and didn't know anyone. I joined a local running club, and now most of my closest friends are people I met there."),
 ("B2-P4","Interviewer: Sofia, welcome. How did your food blog begin? Sofia: It was a complete accident, really. I posted a photo of a cake I'd made for friends, and so many people asked for the recipe that I decided to start writing them down. Interviewer: Did you study cooking? Sofia: No, that surprises people. I actually studied business at university, and I think that's helped me more than any cooking course would have. Interviewer: What's the hardest part of running the blog? Sofia: People assume it's the cooking, but the truth is, photographing the food takes the most time. A single photo can take an hour. Interviewer: Where do your ideas come from? Sofia: Mostly from travelling. I get far more inspiration from markets abroad than from cookbooks. Interviewer: What mistake do beginners make? Sofia: They try to make everything look perfect. My advice is to keep it simple, because readers trust honest, simple recipes. Interviewer: And what's next? Sofia: I've been offered the chance to write a book, but for now I want to focus on filming short videos instead. Interviewer: Sofia, thank you."),
]
def main():
    tmp=tempfile.mkdtemp(prefix="b2_")
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
