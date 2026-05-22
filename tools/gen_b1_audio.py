#!/usr/bin/env python3
"""Generate B1 Listening audio with ElevenLabs (young voices). Run from repo root.
Outputs mp3/B1/B1-P1-q1..q7, B1-P2-q1..q6 (one per recording), B1-P3, B1-P4."""
import os, re, subprocess, tempfile, json, urllib.request, time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY=open(os.path.join(ROOT,"A2 Level.txt"),encoding="utf-8").read().strip()
OUT=os.path.join(ROOT,"mp3","B1"); os.makedirs(OUT,exist_ok=True)
MODEL="eleven_multilingual_v2"; FMT="mp3_44100_128"
V_F="FGY2WhTYpPnrIDTdsKH5"; V_M="TX3LPaxmHKxFdv7VOQHJ"; V_N="JBFqnCBsd6RMkjVDRZzb"
FEMALE={"Girl","Woman","Mum","Mia","Anna"}; MALE={"Boy","Man","Sam","Tom","Leo"}
SPK=re.compile(r'\s*\b(Girl|Boy|Woman|Man|Mum|Teacher|Interviewer|Mia|Anna|Sam|Tom|Leo):\s*')
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
 ("B1-P1-q1","Question one. Boy: Are we taking pizza to the picnic on Sunday? Mum: No, I've already made sandwiches for everyone. Boy: Great, I love your sandwiches."),
 ("B1-P1-q2","Question two. Girl: Are you cycling to school tomorrow, Sam? Boy: My bike has a flat tyre, so my dad's going to drive me. Girl: OK, see you there."),
 ("B1-P1-q3","Question three. Woman: Shall we go for a walk this afternoon? Man: The radio says it's going to rain heavily later. Woman: Then let's just stay in."),
 ("B1-P1-q4","Question four. Boy: What would you like for your birthday, Mia? Girl: I'd really love a camera. I want to take photos of the birds in our garden. Boy: Good idea."),
 ("B1-P1-q5","Question five. Girl: Did you buy that book you wanted, Tom? Boy: They'd sold out, so I bought a new school bag instead. Girl: Oh well, that's useful too."),
 ("B1-P1-q6","Question six. Man: What time does our train leave? Woman: At nine o'clock, not half past eight like yesterday. Man: Good, then we've got time for a coffee."),
 ("B1-P1-q7","Question seven. Mum: What's the matter, Anna? Girl: I've lost my keys somewhere here in the park. Mum: Don't worry, let's go back and look for them."),
 ("B1-P2-q1","You will hear a girl talking about a school trip. Girl: The museum was interesting, and lunch by the river was nice, but the best part was definitely the boat ride. I'd never been on a boat before, and the views were amazing."),
 ("B1-P2-q2","You will hear a boy talking about his weekend. Boy: On Saturday I really wanted to play football, but I had a maths test on Monday, so I stayed home and studied all afternoon. I visited my grandparents on Sunday instead."),
 ("B1-P2-q3","You will hear a woman talking about a new cafe. Woman: It's not the cheapest place in town, and it can get a bit noisy, but honestly the cakes are absolutely delicious. That's why I keep going back."),
 ("B1-P2-q4","You will hear a teacher talking to a student. Teacher: Your essay is well written and you handed it in on time, well done. But your ideas need support, so I'd like you to add a few more examples before I mark it."),
 ("B1-P2-q5","You will hear a girl talking about a book. Girl: I expected a happy ending, so I was completely surprised when the main character moved away. I didn't see it coming at all, but I still enjoyed it."),
 ("B1-P2-q6","You will hear a man explaining why he is late. Man: I'm so sorry. I actually woke up on time, but there was a terrible accident on the main road, so the traffic was awful and I couldn't get here any faster."),
 ("B1-P3","Hello everyone. I'd like to tell you about our after-school Drama Club. The club meets every Thursday in the school hall, that's the big room next to the library. We start at four o'clock and finish at half past five. The cost is twenty pounds for the whole term, and that covers all of the costumes. This term, our first play is going to be a comedy, so it should be really good fun. One last thing: please remember to bring a bottle of water, because the practices can be quite tiring. We hope to see you there!"),
 ("B1-P4","Interviewer: Today I'm talking to Leo, a young photographer. Leo, how did you start? Leo: My grandfather gave me his old camera when I was eleven. At first I just took photos of my dog, but I quickly fell in love with it. Interviewer: What do you like photographing most? Leo: People often expect me to say landscapes, but actually I prefer photographing animals, especially birds, they're a real challenge. Interviewer: Is it difficult? Leo: The hardest part isn't the camera, it's the waiting. You sometimes wait hours for the perfect moment, so you need a lot of patience. Interviewer: Have you won any prizes? Leo: I won a small local competition last year, which was a surprise. It gave me the confidence to keep going. Interviewer: What advice would you give beginners? Leo: Don't buy an expensive camera at first. Just practise with what you have and learn to look carefully. Interviewer: And the future? Leo: I'd love to travel and photograph wildlife all over the world one day."),
]
def main():
    tmp=tempfile.mkdtemp(prefix="b1_")
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
