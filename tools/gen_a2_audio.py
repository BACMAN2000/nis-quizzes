#!/usr/bin/env python3
"""
Generate A2 Listening audio with ElevenLabs (young voices), one mp3 per Part.
- Splits each script by speaker, assigns a young voice, generates each line,
  and concatenates the lines (with short pauses) into mp3/A2-P<N>.mp3 via ffmpeg.
- Reads the API key from "A2 Level.txt" (gitignored). Key is never printed.

Run from the repo root:  python tools/gen_a2_audio.py
"""
import os, re, sys, json, time, subprocess, urllib.request, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, "A2 Level.txt")
MP3_DIR  = os.path.join(ROOT, "mp3", "A2")  # organized by level
MODEL    = "eleven_multilingual_v2"
OUTFMT   = "mp3_44100_128"

# Young voices from the account
V_FEMALE = "FGY2WhTYpPnrIDTdsKH5"  # Laura (young female)
V_MALE   = "TX3LPaxmHKxFdv7VOQHJ"  # Liam  (young male)
V_NARR   = "JBFqnCBsd6RMkjVDRZzb"  # George (warm narrator / teacher)

FEMALE = {"Girl","Woman","Mum","Sara","Mia","Anna","Carla","Emma"}
MALE   = {"Boy","Man","Leo","Tom","Ben","David"}
NARR   = {"Teacher"}
SPEAKER_RE = re.compile(r'\s*\b(Girl|Boy|Woman|Man|Teacher|Mum|Sara|Leo|Tom|Mia|Anna|Ben|Carla|David|Emma):\s*')

# A2 scripts (must match listening-quiz.html QUIZ.A2)
PARTS = {
 "A2-P1": [
  "Question one. Girl: What did you get Mum for her birthday? Boy: I wanted to buy her a book, but in the end I made her a chocolate cake. She loved it.",
  "Question two. Boy: Shall we meet at the cafe on Saturday? Girl: It's a lovely day, let's meet in the park instead. Boy: OK, the park it is.",
  "Question three. Woman: Do you want to walk to the shops? Man: Have you looked outside? It's raining really hard. Woman: Oh, then let's wait.",
  "Question four. Mum: What's the matter? Girl: I can't find my phone anywhere. I think I left it on the bus. Mum: Don't worry, we'll call it.",
  "Question five. Boy: What time does the film start? Girl: At half past eight, not eight o'clock. Boy: Good, then we have time for dinner first.",
 ],
 "A2-P2": [
  "Listen to your teacher talking about the class trip. Teacher: Here are the details for our class trip to the city farm. The trip costs eight pounds. Please give your money to Mr Davies before Wednesday. We will leave school at nine o'clock in the morning, so don't be late. We are going to travel by train. Everyone must bring a packed lunch, and please wear warm clothes.",
 ],
 "A2-P3": [
  "Sara: Hi Leo, are you coming to the beach on Saturday? Leo: I'd love to, but I have a guitar lesson at ten o'clock. Maybe in the afternoon? Sara: Great, we'll go after lunch. How will you get there? Leo: My dad said he'll drive us. Sara: Perfect. Don't forget to bring sun cream, it's going to be really hot. Leo: I will. Should I bring some food too? Sara: No, my mum is making sandwiches for everyone.",
 ],
 "A2-P4": [
  "Tom: I joined the swimming club three months ago. At first it was difficult because I couldn't swim very well, but my coach is really patient, and now I love it. We train on Tuesdays and Thursdays after school. The best part is meeting new friends. My parents were worried it would take too much time, but my school marks are still good. Next month there's a competition, and I'm a bit nervous, but my coach says I'm ready.",
 ],
 "A2-P5": [
  "Mia: Everyone is helping with our class party. Anna is bringing the music, because she has really good speakers. Ben said he'll make a big cake. Carla is going to bring the drinks. David is great at art, so he's making the decorations. And Emma will bring some games, so nobody gets bored.",
 ],
}

def voice_for(speaker):
    if speaker in FEMALE: return V_FEMALE
    if speaker in MALE:   return V_MALE
    return V_NARR

def segments(script):
    """Return ordered list of (voice_id, text)."""
    parts = SPEAKER_RE.split(script)
    out = []
    lead = parts[0].strip()
    if lead: out.append((V_NARR, lead))
    for i in range(1, len(parts), 2):
        spk = parts[i]; txt = parts[i+1].strip() if i+1 < len(parts) else ""
        if txt: out.append((voice_for(spk), txt))
    return out

def tts(key, voice_id, text, dest):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format={OUTFMT}"
    body = json.dumps({"text": text, "model_id": MODEL,
                       "voice_settings": {"stability":0.45,"similarity_boost":0.8,"style":0.0}}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "xi-api-key": key, "Content-Type":"application/json", "Accept":"audio/mpeg"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())

def main():
    key = open(KEY_FILE, encoding="utf-8").read().strip()
    os.makedirs(MP3_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="a2tts_")
    # 0.6s silence between lines, 1.5s lead-in so the start is never clipped
    sil = os.path.join(tmp, "sil.mp3")
    lead = os.path.join(tmp, "lead.mp3")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t","0.6","-q:a","9",sil],
                   check=True, capture_output=True)
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t","1.5","-q:a","9",lead],
                   check=True, capture_output=True)
    for pid, scripts in PARTS.items():
        segs = []
        for sc in scripts:
            segs += segments(sc)
        files = [lead]  # lead-in silence so the first word is never clipped
        for j,(vid,txt) in enumerate(segs):
            seg = os.path.join(tmp, f"{pid}_{j:02d}.mp3")
            print(f"  {pid} seg {j+1}/{len(segs)} ({len(txt)} chars)...")
            tts(key, vid, txt, seg)
            files.append(seg); files.append(sil)
            time.sleep(0.2)
        # concat list
        lst = os.path.join(tmp, f"{pid}.txt")
        with open(lst,"w",encoding="utf-8") as f:
            for fp in files: f.write(f"file '{fp.replace(os.sep,'/')}'\n")
        out = os.path.join(MP3_DIR, f"{pid}.mp3")
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
                        "-c:a","libmp3lame","-q:a","4",out], check=True, capture_output=True)
        kb = os.path.getsize(out)//1024
        print(f"OK {pid}.mp3  ({kb} KB, {len(segs)} lines)")
    print("DONE")

if __name__ == "__main__":
    main()
