#!/usr/bin/env python3
"""
Emoji Platformer v6 - The ultimate emoji platformer with level editor.
New in v7: Character selection screen with preview, names, descriptions, keyboard navigation,
animated card selection, confirm button, and per-character color themes.
v6: Parallax background hills, ambient theme particles, landing dust burst, sprint speed lines,
coin magnet attraction, achievement popups, Spring Launcher tile, Cannon tiles, Ghost Chaser enemy.
v5: Background music loop, drop-through platforms, level grade system (S/A/B/C),
enemy death poof animation, enhanced pause menu, animated menu title, low-health heartbeat.

Controls:
  Play:   Arrows/WASD move, Space/Up jump (tap=short, hold=full), Shift sprint, E dash
          Down+Jump = drop through one-way platforms, Wall+Jump = wall-jump
          P pause, M mute, R restart, ESC menu
  Editor: LClick place, RClick erase, MClick set spawn, Scroll/0-9 tile, G grid
          F flood fill, T test, Ctrl+S/L save/load, Ctrl+Z undo, Ctrl+N new
          Ctrl+C/V copy/paste, +/- resize, Tab theme, X clear, L filter, M minimap, ESC menu
"""

import pygame, sys, json, os, math, random, time as _time

SW, SH = 960, 640
TS = 40
FPS = 60
GRAVITY = 0.6
JUMP_FORCE = -12.5
JUMP_CUT = -4           # variable jump: release early → vy capped here
PLAYER_SPEED = 5
SPRINT_MULT = 1.6
MAX_FALL = 15
COYOTE = 6
JBUF = 6
WSLIDE_SPD = 2
WJUMP_H = 6; WJUMP_V = -11
DJUMP_F = -10.5
BOUNCE_F = -18
SHAKE_T = 12; SHAKE_I = 6
COMBO_WINDOW = 90       # frames to chain combos
TIME_BONUS_MAX = 3000   # max time bonus points
MUSIC_VOL = 0.12        # background music volume
DROP_THROUGH = True     # allow dropping through one-way platforms
DASH_SPD = 14; DASH_DUR = 8; DASH_CD = 30
ICE_FRIC = 0.92; WATER_SLOW = 0.55; WATER_GRAV = 0.25
SPEED_BOOST_T = 90; SPEED_BOOST_MULT = 2.0
TRAP_RANGE = TS * 2.5; POTION_T = 300
LAVA_PARTICLE_RANGE = TS * 4
SPRING_F = -22
CANNON_SPD = 5; CANNON_CD = 150
ACHIEVEMENT_QUEUE_MAX = 3

WHITE=(255,255,255); BLACK=(0,0,0); GRAY=(180,180,180)
DARK_GRAY=(80,80,80); LGRAY=(220,220,220)
PANEL_BG=(40,40,60); PBORDER=(80,80,120); HILITE=(255,220,50)
GREEN_B=(60,180,75); RED_B=(220,60,60); BLUE_B=(60,120,220)
ORANGE_B=(220,150,30); PURPLE_B=(130,60,180); CYAN_B=(40,180,200)

LEVELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emoji_levels")
SCORES_F = os.path.join(LEVELS_DIR, "highscores.json")
os.makedirs(LEVELS_DIR, exist_ok=True)

SKY_THEMES = {
    "meadow":((135,206,250),(200,230,255)),
    "cave":  ((40,35,60),(80,70,100)),
    "sky":   ((100,180,255),(180,220,255)),
    "lava":  ((60,20,10),(140,50,20)),
    "ice":   ((180,210,240),(230,240,255)),
    "fortress":((50,40,70),(100,80,130)),
    "sunset":((255,140,80),(255,200,150)),
    "space": ((5,5,20),(20,10,50)),
}

# (emoji, category, solid, description)
# special categories: one_way, conveyor_l, conveyor_r, wind, shield, magnet, multiplier
TD = {
    0:  ("",     "empty",       False, "Eraser"),
    1:  ("🧱",   "terrain",     True,  "Brick"),
    2:  ("🟫",   "terrain",     True,  "Ground"),
    3:  ("🪨",   "terrain",     True,  "Stone"),
    4:  ("🌿",   "deco",        False, "Grass"),
    5:  ("⭐",   "collect",     False, "Star 100"),
    6:  ("💎",   "collect",     False, "Gem 250"),
    7:  ("👾",   "enemy",       False, "Alien"),
    8:  ("🤖",   "enemy",       False, "Robot"),
    9:  ("💀",   "hazard",      False, "Skull"),
    10: ("🔥",   "hazard",      False, "Fire"),
    11: ("🚩",   "goal",        False, "Flag"),
    12: ("☁️",   "deco",        False, "Cloud"),
    13: ("🌟",   "collect",     False, "Bonus 200"),
    14: ("🍄",   "powerup",     False, "Mushroom +1up"),
    15: ("📦",   "terrain",     True,  "Crate"),
    16: ("❄️",   "hazard",      False, "Ice Spike"),
    17: ("🌈",   "deco",        False, "Rainbow"),
    18: ("🌸",   "deco",        False, "Blossom"),
    19: ("🔄",   "moving_h",    True,  "Move H"),
    20: ("↕️",   "moving_v",    True,  "Move V"),
    21: ("🦘",   "bounce",      True,  "Bounce"),
    22: ("🏁",   "checkpoint",  False, "Checkpoint"),
    23: ("🪽",   "powerup",     False, "Wings (dbl jump)"),
    24: ("💨",   "crumble",     True,  "Crumble"),
    25: ("🌀",   "teleport",    False, "Teleporter"),
    26: ("🦇",   "flying_enemy",False, "Bat"),
    27: ("🪙",   "collect",     False, "Coin 50"),
    28: ("🪜",   "one_way",     True,  "One-Way Plat"),
    29: ("⬅️",   "conveyor_l",  True,  "Conveyor ←"),
    30: ("➡️",   "conveyor_r",  True,  "Conveyor →"),
    31: ("🛡️",   "powerup",     False, "Shield"),
    32: ("🧲",   "powerup",     False, "Coin Magnet"),
    33: ("🌬️",   "wind",        False, "Wind"),
    34: ("🎯",   "powerup",     False, "Score x2"),
    35: ("🧊",   "ice",         True,  "Ice (slippery)"),
    36: ("🌊",   "water",       False, "Water (slow)"),
    37: ("⚡",   "speed_pad",   False, "Speed Pad"),
    38: ("🔑",   "key",         False, "Key"),
    39: ("🚪",   "door",        True,  "Locked Door"),
    40: ("🧪",   "powerup",     False, "Potion (invinc)"),
    41: ("🐉",   "dragon_enemy",False, "Dragon"),
    42: ("🔮",   "collect",     False, "Crystal 500"),
    43: ("🪤",   "trap",        False, "Trap (hidden)"),
    44: ("🔊",   "deco",        False, "Speaker"),
    45: ("🎪",   "spring",      True,  "Spring Launcher"),
    46: ("💣",   "cannon_l",    False, "Cannon ←"),
    47: ("💣",   "cannon_r",    False, "Cannon →"),
    48: ("👻",   "chaser",      False, "Ghost Chaser"),
}

SKINS = [
    "😀","🥳","😎","🤠","👽","🦊","🐱","🐸","🐵","🐧","🦄","🐲",
    "🎃","🤖","👻","💀","🐼","🦁","🐺","🐉","🦅","🐙","🐝","🦀",
]
SKIN_NAMES = {
    "😀": "Smiley",       "🥳": "Party Star",   "😎": "Cool Cat",
    "🤠": "Cowboy",       "👽": "Alien",        "🦊": "Fox",
    "🐱": "Kitty",        "🐸": "Froggy",       "🐵": "Monkey",
    "🐧": "Penguin",      "🦄": "Unicorn",      "🐲": "Dragon Lord",
    "🎃": "Pumpkin",      "🤖": "Robo Buddy",   "👻": "Spooky",
    "💀": "Bone Head",    "🐼": "Panda",        "🦁": "Lion Heart",
    "🐺": "Dark Wolf",    "🐉": "Dragon",       "🦅": "Sky Eagle",
    "🐙": "Octo Squid",   "🐝": "Bumblebee",    "🦀": "Shell Shock",
}
SKIN_DESCS = {
    "😀": "The classic. Happy, reliable, always ready.",
    "🥳": "Born to celebrate every victory with style!",
    "😎": "Too cool for school. Shades always on.",
    "🤠": "Yeehaw! Lassos platforms like a pro.",
    "👽": "From another world. Gravity? Optional.",
    "🦊": "Quick and clever. Never misses a coin.",
    "🐱": "Nine lives? That's just cheating!",
    "🐸": "Hop, hop, hop! Built for platforming.",
    "🐵": "Swings through levels with wild energy.",
    "🐧": "Slippery but unstoppable on ice.",
    "🦄": "Magical and majestic. A rare choice.",
    "🐲": "The ultimate. Feared by all enemies.",
    "🎃": "Spooky season never ends with this one.",
    "🤖": "Beep boop. Calculated platforming efficiency.",
    "👻": "Boo! Phases through obstacles... almost.",
    "💀": "Live fast, die young, respawn faster.",
    "🐼": "Chill vibes only. Too relaxed to worry.",
    "🦁": "Brave heart. Roars at enemies for intimidation.",
    "🐉": "Ancient power. Unstoppable fire breathing.",
    "🐺": "Lone wolf. Howls at the moon between levels.",
    "🦅": "Soars above with eagle-eyed precision.",
    "🐙": "Eight legs, zero mercy. Tentacle power!",
    "🐝": "Busy buzzer. Collects coins at lightspeed.",
    "🦀": "Tough shell, tough attitude. Never backs down.",
}
SKIN_COLORS = {
    "😀": (255,220,50),  "🥳": (255,150,200), "😎": (80,80,80),
    "🤠": (180,130,50), "👽": (100,200,100), "🦊": (220,140,50),
    "🐱": (255,180,100), "🐸": (80,200,80),   "🐵": (180,130,90),
    "🐧": (80,80,100),   "🦄": (200,150,255), "🐲": (220,60,60),
    "🎃": (255,140,30),  "🤖": (100,180,220), "👻": (180,180,220),
    "💀": (200,200,200), "🐼": (60,60,60),    "🦁": (220,180,50),
    "🐺": (140,140,160), "🐉": (60,180,60),  "🦅": (180,130,50),
    "🐙": (180,80,180),  "🐝": (240,200,50),  "🦀": (220,80,50),
}
# ── v7: Emoji combiner parts for Character Creator ──
CREATOR_BASES = [
    "😀","😎","🥳","🤠","😈","🤡","👹","👺",
    "👶","🧒","🧑","👱","🧔","👴","🧙","🧚",
    "🦊","🐱","🐸","🐵","🐧","🦁","🐺","🦄",
    "🎃","💀","👻","🤖","👽","🎃","🦅","🐙",
]
CREATOR_MODS = [
    ("", "None"),
    ("\u200d\u2728", "Sparkles"),
    ("\u200d\u26a1", "Lightning"),
    ("\u200d\U0001f525", "Fire"),
    ("\u200d\U0001f48e", "Gem"),
    ("\u200d\u2764\ufe0f", "Heart"),
    ("\u200d\u2b50", "Star"),
    ("\u200d\U0001f6e1\ufe0f", "Shield"),
    ("\u200d\U0001f52e", "Crystal Ball"),
    ("\u200d\U0001f3b5", "Music"),
    ("\u200d\U0001f9e0", "Brain"),
    ("\u200d\U0001f4a5", "Boom"),
    ("\u200d\U0001f300", "Cyclone"),
    ("\u200d\U0001f31f", "Glowing Star"),
    ("\u200d\U0001f49c", "Purple Heart"),
    ("\u200d\u26bd", "Soccer"),
]
CREATOR_SUFFIX = [
    ("", "None"),
    ("\u200d\u26a1", "Lightning"),
    ("\u200d\U0001f525", "Fire"),
    ("\u200d\u2b50", "Star"),
    ("\u200d\U0001f48e", "Gem"),
    ("\u200d\u2764\ufe0f", "Heart"),
    ("\u200d\U0001f52e", "Crystal"),
    ("\u200d\U0001f4a5", "Boom"),
]
MAX_CUSTOM_SKINS = 6
P_JUMP="🤸"; P_DEAD="😵"; P_WALL="🧗"; HEART="❤️"

def get_all_skins(hs):
    """Return the full skin list: built-in SKINS + any saved custom skins."""
    base = list(SKINS)
    customs = hs.get("custom_skins", [])
    base.extend(customs)
    return base

def get_skin_name(em):
    if em in SKIN_NAMES: return SKIN_NAMES[em]
    # check custom skins
    if len(em) > 4:  # likely a combined emoji
        return "Custom"
    return "?"

def get_skin_desc(em):
    if em in SKIN_DESCS: return SKIN_DESCS[em]
    if len(em) > 4: return "A custom creation from the Character Creator."
    return ""

def get_skin_color(em):
    if em in SKIN_COLORS: return SKIN_COLORS[em]
    if len(em) > 4: return (200, 150, 255)  # purple for custom
    return HILITE

# ─── Sound ────────────────────────────────────────────────────────────────
class Snd:
    """Retro 8-bit chiptune sound engine using square/triangle/noise waves."""
    def __init__(self):
        self.on = True
        try: pygame.mixer.init(22050,-16,1,512)
        except: self.on = False
        self.c = {}

    def _sq(self, f, d, v=0.25, duty=0.25):
        """Square wave — the classic 8-bit sound."""
        if not self.on: return None
        sr=22050; n=int(sr*d); buf=bytearray(n)
        for i in range(n):
            env=max(0.0, 1.0-i/n)
            phase=(f*i/sr) % 1.0
            val= v*255 if phase < duty else -v*255
            buf[i]=max(0,min(255,int(128+val*env)))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _tri(self, f, d, v=0.25):
        """Triangle wave — softer, mellow 8-bit tone."""
        if not self.on: return None
        sr=22050; n=int(sr*d); buf=bytearray(n)
        for i in range(n):
            env=max(0.0, 1.0-i/n)
            phase=(f*i/sr) % 1.0
            if phase<0.25: val=phase*4
            elif phase<0.75: val=2-phase*4
            else: val=(phase-1)*4
            buf[i]=max(0,min(255,int(128+val*v*255*env)))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _noise(self, d, v=0.2):
        """White noise — for percussion/explosions."""
        if not self.on: return None
        sr=22050; n=int(sr*d); buf=bytearray(n)
        seed=42
        for i in range(n):
            env=max(0.0, 1.0-i/n)
            seed=(seed*1103515245+12345)&0x7FFF
            val=((seed/0x7FFF)*2-1)*v*255*env
            buf[i]=max(0,min(255,int(128+val)))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _arp(self, freqs, note_d, v=0.2):
        """Arpeggio — rapidly cycles through frequencies."""
        if not self.on: return None
        sr=22050; total=len(freqs)*int(sr*note_d)
        total=min(total, int(sr*2.0)); buf=bytearray(total)
        idx=0
        for fi, f in enumerate(freqs):
            nn=int(sr*note_d)
            for i in range(nn):
                if idx>=total: break
                env=max(0.0, 1.0-idx/total)
                phase=(f*idx/sr)%1.0
                val= v*255 if phase<0.25 else -v*255
                buf[idx]=max(0,min(255,int(128+val*env)))
                idx+=1
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _sweep(self, f1, f2, d, v=0.25):
        """Frequency sweep — for power-ups and slides."""
        if not self.on: return None
        sr=22050; n=int(sr*d); buf=bytearray(n)
        for i in range(n):
            env=max(0.0, 1.0-i/n)
            t=i/n; f=f1+(f2-f1)*t
            phase=(f*i/sr)%1.0
            val= v*255 if phase<0.25 else -v*255
            buf[i]=max(0,min(255,int(128+val*env)))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, n):
        if self.on and n in self.c and self.c[n]: self.c[n].play()

    def init(self):
        if not self.on: return
        c = self.c
        c["jump"]    = self._sweep(260, 520, 0.12, 0.22)
        c["djump"]   = self._arp([440, 660, 880], 0.04, 0.18)
        c["wjump"]   = self._sweep(300, 500, 0.08, 0.18)
        c["stomp"]   = self._sq(180, 0.12, 0.28)
        c["collect"] = self._arp([988, 1319], 0.06, 0.18)
        c["hurt"]    = self._sweep(400, 80, 0.25, 0.28)
        c["bounce"]  = self._arp([330, 440, 660], 0.04, 0.22)
        c["checkpoint"] = self._arp([523, 659, 784], 0.08, 0.16)
        c["win"]     = self._arp([523, 659, 784, 1047, 1319], 0.1, 0.2)
        c["crumble"] = self._noise(0.18, 0.12)
        c["teleport"]= self._sweep(200, 1600, 0.2, 0.18)
        c["shield"]  = self._sq(1200, 0.06, 0.15)
        c["combo"]   = self._sq(900, 0.04, 0.15)
        c["magnet"]  = self._arp([600, 700, 600, 800], 0.04, 0.15)
        c["conveyor"]= self._sq(100, 0.05, 0.08)
        # v4 new sounds
        c["dash"]    = self._sweep(200, 900, 0.1, 0.2)
        c["key"]     = self._arp([784, 988, 1175], 0.06, 0.18)
        c["door"]    = self._sweep(800, 400, 0.2, 0.18)
        c["speed"]   = self._arp([523, 659, 784, 1047], 0.03, 0.16)
        c["potion"]  = self._arp([660, 880, 1100, 880, 660], 0.05, 0.16)
        c["ice"]     = self._noise(0.05, 0.06)
        c["trap"]    = self._sq(150, 0.15, 0.25)
        c["fireball"]= self._sweep(300, 100, 0.15, 0.2)
        c["crystal"] = self._arp([1319, 1568, 2093], 0.05, 0.15)
        c["death_j"] = self._arp([440, 370, 330, 262], 0.12, 0.2)
        c["intro"]   = self._arp([262, 330, 392, 523], 0.12, 0.18)
        # v5 new sounds
        c["drop"]    = self._sweep(400, 200, 0.08, 0.15)
        c["grade_s"] = self._arp([523, 659, 784, 1047, 1319, 1568], 0.08, 0.2)
        c["grade_a"] = self._arp([523, 659, 784, 1047, 1319], 0.08, 0.18)
        c["hb"]      = self._sq(60, 0.08, 0.15)
        c["coin_attract"] = self._tri(1200, 0.04, 0.08)
        # v6 new sounds
        c["spring"]  = self._arp([440, 660, 880, 1320], 0.04, 0.22)
        c["cannon"]  = self._noise(0.15, 0.25)
        c["achieve"] = self._arp([523, 659, 784, 1047, 784, 1047], 0.06, 0.18)
        c["chaser"]  = self._sweep(200, 400, 0.1, 0.12)
    def _make_music(s):
        """Generate a looping background music track."""
        if not s.on: return None
        sr=22050
        # Simple 8-bar melody loop (~8 seconds at 120 BPM)
        # Notes: C4 D4 E4 G4 A4 G4 E4 D4 | C4 E4 G4 C5 G4 E4 C4 -
        melody=[262,294,330,392,440,392,330,294, 262,330,392,523,392,330,262,0,
                294,330,392,440,523,440,392,330, 262,294,330,392,330,294,262,0,
                330,392,440,523,587,523,440,392, 330,392,523,440,392,330,294,0,
                262,330,392,523,659,523,392,330, 262,294,330,262,0,0,0,0]
        note_d=0.125  # 8th notes
        # bass line: simple root notes
        bass=[131,131,165,165,196,196,165,165, 131,131,165,165,196,196,131,131,
              147,147,165,165,196,196,165,165, 131,131,147,147,165,165,131,131,
              165,165,196,196,220,220,196,196, 165,165,196,196,165,165,147,147,
              131,131,165,165,196,196,165,165, 131,131,131,131,131,131,131,131]
        total_notes=len(melody)
        note_samples=int(sr*note_d)
        total_samples=total_notes*note_samples
        buf=bytearray(total_samples)
        idx=0
        for i in range(total_notes):
            f_mel=melody[i]; f_bas=bass[i] if i<len(bass) else 131
            for j in range(note_samples):
                if idx>=total_samples: break
                t_note=j/note_samples  # 0→1 within note
                env=max(0.0, 1.0-t_note*0.7)  # decay envelope
                # melody: square wave
                if f_mel>0:
                    phase_m=(f_mel*idx/sr)%1.0
                    val_m= 0.18*255 if phase_m<0.25 else -0.18*255
                else: val_m=0
                # bass: triangle wave (softer)
                phase_b=(f_bas*idx/sr)%1.0
                if phase_b<0.25: val_b=phase_b*4
                elif phase_b<0.75: val_b=2-phase_b*4
                else: val_b=(phase_b-1)*4
                val_b*=0.10*255
                # drums on beats 0,4,8,12 (every 4th note = quarter note)
                drum=0
                beat=i%4
                if beat==0 and j<int(note_samples*0.05):  # kick
                    seed2=(idx*17+42)&0x7FFF; drum=((seed2/0x7FFF)*2-1)*0.2*255*(1-j/(note_samples*0.05))
                elif beat==2 and j<int(note_samples*0.03):  # snare/hihat
                    seed2=(idx*31+99)&0x7FFF; drum=((seed2/0x7FFF)*2-1)*0.1*255*(1-j/(note_samples*0.03))
                val=int(128+(val_m+val_b+drum)*env)
                buf[idx]=max(0,min(255,val))
                idx+=1
        snd=pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(MUSIC_VOL)
        return snd

def load_hs():
    try:
        with open(SCORES_F) as f: return json.load(f)
    except: return {}
def save_hs(s):
    try:
        with open(SCORES_F,"w") as f: json.dump(s,f,indent=2)
    except: pass

# ─── Renderers ────────────────────────────────────────────────────────────
class ER:
    def __init__(s, sz):
        s.sz=sz; s.c={}
        try: s.f=pygame.font.Font("/usr/share/fonts/truetype/emoji/NotoColorEmoji.ttf",sz)
        except: s.f=pygame.font.SysFont(None,sz)
    def render(s, em):
        if em not in s.c:
            surf=s.f.render(em,True,WHITE); w,h=surf.get_size()
            sc=min(TS/max(w,1),TS/max(h,1))
            s.c[em]=pygame.transform.smoothscale(surf,(max(1,int(w*sc)),max(1,int(h*sc))))
        return s.c[em]

class SkyBG:
    def __init__(s): s.c={}
    def get(s, th="meadow"):
        if th not in s.c:
            top,bot=SKY_THEMES.get(th,SKY_THEMES["meadow"])
            sf=pygame.Surface((SW,SH))
            for y in range(SH):
                t=y/SH; r=int(top[0]*(1-t)+bot[0]*t); g=int(top[1]*(1-t)+bot[1]*t); b=int(top[2]*(1-t)+bot[2]*t)
                pygame.draw.line(sf,(r,g,b),(0,y),(SW,y))
            s.c[th]=sf
        return s.c[th]

# ─── Camera (with look-ahead) ───────────────────────────────────────────
class Cam:
    def __init__(s,w,h):
        s.ox=0.0;s.oy=0.0;s.w=w;s.h=h;s.sm=0.1
        s.look_x=0.0;s.look_y=0.0
    def update(s,tx,ty,vx,vy,lw,lh):
        # look-ahead
        s.look_x+=(vx*12-s.look_x)*0.05
        s.look_y+=(vy*6-s.look_y)*0.05
        dx=max(0,min(tx+s.look_x-s.w//2,lw-s.w))
        dy=max(0,min(ty+s.look_y-s.h//2,lh-s.h))
        s.ox+=(dx-s.ox)*s.sm; s.oy+=(dy-s.oy)*s.sm
        if abs(dx-s.ox)<1: s.ox=dx
        if abs(dy-s.oy)<1: s.oy=dy
    def apply(s,x,y): return x-int(s.ox),y-int(s.oy)
    @property
    def oxi(s): return int(s.ox)
    @property
    def oyi(s): return int(s.oy)

# ─── FX classes ──────────────────────────────────────────────────────────
class Shake:
    def __init__(s): s.t=0;s.i=0
    def trigger(s,i=SHAKE_I,d=SHAKE_T): s.t=d;s.i=i
    def update(s):
        if s.t>0: s.t-=1; return True
        return False
    def off(s):
        if s.t<=0: return 0,0
        v=int(s.i*s.t/SHAKE_T); return random.randint(-v,v),random.randint(-v,v)

class FText:
    def __init__(s,x,y,txt,col=HILITE,sz=22):
        s.x=x;s.y=y;s.txt=txt;s.col=col
        s.f=pygame.font.SysFont("Arial",sz,True);s.life=50;s.ml=50
    def update(s): s.y-=1.2;s.life-=1; return s.life>0
    def draw(s,scr,cam):
        a=int(255*s.life/s.ml);sx,sy=cam.apply(s.x,s.y)
        t=s.f.render(s.txt,True,s.col);t.set_alpha(a);scr.blit(t,(sx,sy))

class Part:
    def __init__(s,x,y,em,vx,vy,l=40):
        s.x=x;s.y=y;s.em=em;s.vx=vx;s.vy=vy;s.l=l;s.ml=l
    def update(s): s.x+=s.vx;s.y+=s.vy;s.vy+=0.15;s.l-=1; return s.l>0
    def draw(s,scr,rd,cam):
        a=s.l/s.ml;sx,sy=cam.apply(s.x,s.y);sf=rd.render(s.em)
        if a<1: sf=sf.copy();sf.set_alpha(int(255*a))
        scr.blit(sf,(sx,sy))

class PoofAnim:
    """Enemy death poof: expanding ring + shrinking emoji."""
    def __init__(s,x,y,em):
        s.x=x;s.y=y;s.em=em;s.life=25;s.ml=25
    def update(s): s.life-=1; return s.life>0
    def draw(s,scr,rd,cam):
        t=1.0-s.life/s.ml  # 0→1
        sx,sy=cam.apply(s.x,s.y)
        # expanding white ring
        radius=int(TS*0.5+t*TS*0.6)
        a=int(200*(1-t))
        ring=pygame.Surface((radius*2+4,radius*2+4),pygame.SRCALPHA)
        pygame.draw.circle(ring,(255,255,255,a),(radius+2,radius+2),radius,3)
        scr.blit(ring,(sx-radius-2+TS//2,sy-radius-2+TS//2))
        # shrinking emoji
        if t<0.6:
            sf=rd.render(s.em)
            sc=max(0.1,1.0-t*1.5)
            ow,oh=sf.get_size();nw=max(1,int(ow*sc));nh=max(1,int(oh*sc))
            sf=pygame.transform.smoothscale(sf,(nw,nh))
            sf.set_alpha(int(255*(1-t/0.6)))
            scr.blit(sf,(sx+(TS-nw)//2,sy+(TS-nh)//2-t*15))

class DeathAnim:
    """Player death animation: fly up then fall."""
    def __init__(s,x,y,emoji):
        s.x=float(x);s.y=float(y);s.em=emoji
        s.vx=random.uniform(-3,3);s.vy=-10;s.life=60;s.ml=60
    def update(s):
        s.vy+=0.5;s.x+=s.vx;s.y+=s.vy;s.life-=1;return s.life>0
    def draw(s,scr,rd,cam):
        a=int(255*s.life/s.ml);sx,sy=cam.apply(s.x,s.y)
        sf=rd.render(s.em);sf.set_alpha(a);scr.blit(sf,(sx,sy))

class Fireball:
    """Projectile from dragon enemies."""
    def __init__(s,x,y,dx):
        s.x=float(x);s.y=float(y);s.dx=dx
        s.sp=3.5;s.alive=True;s.life=120
    def update(s,lw):
        s.x+=s.dx;s.life-=1
        if s.life<=0 or s.x<0 or s.x>lw: s.alive=False
    def rect(s): return pygame.Rect(s.x,s.y,TS-8,TS-8)
    def draw(s,scr,rd,cam):
        if not s.alive: return
        sx,sy=cam.apply(s.x,s.y)
        sf=rd.render("🔥");scr.blit(sf,(sx,sy))

class BGStars:
    """Twinkling stars for dark themes."""
    def __init__(s):
        s.stars=[(random.randint(0,SW),random.randint(0,SH),random.uniform(0.5,2.5),random.uniform(0,6.28)) for _ in range(60)]
    def draw(s,scr,t):
        for x,y,sp,ph in s.stars:
            b=int(120+135*math.sin(t*0.002*sp+ph))
            pygame.draw.circle(scr,(b,b,b),(x,y),1 if sp<1.5 else 2)

class ParallaxClouds:
    def __init__(s):
        s.cs=[{"x":random.uniform(0,SW*2),"y":random.uniform(20,SH*0.5),
               "sp":random.uniform(0.2,0.6),"sc":random.uniform(0.6,1.2)} for _ in range(8)]
    def update(s):
        for c in s.cs:
            c["x"]-=c["sp"]
            if c["x"]<-80: c["x"]=SW+random.randint(20,100);c["y"]=random.uniform(20,SH*0.5)
    def draw(s,scr,ox,rd):
        for c in s.cs:
            x=(c["x"]-ox*0.3)%(SW+200)-100
            sf=rd.render("☁️");sw,sh=sf.get_size()
            nw,nh=int(sw*c["sc"]),int(sh*c["sc"])
            if nw>0 and nh>0:
                sf=pygame.transform.smoothscale(sf,(nw,nh));sf.set_alpha(100);scr.blit(sf,(x,c["y"]))

# ─── v6: Parallax Background Hills ──────────────────────────────────────
class ParallaxHills:
    """Generates layered mountain/hill silhouettes that scroll with parallax."""
    def __init__(s):
        s.layers = {}  # cached per theme
    def _gen(s, theme):
        if theme in s.layers: return s.layers[theme]
        configs = {
            "meadow":  [(0.15, (60,130,60),  0.35, 80), (0.25, (80,160,80),  0.55, 50)],
            "sky":     [(0.12, (100,150,200), 0.30, 90), (0.22, (130,180,220), 0.50, 55)],
            "cave":    [(0.10, (30,25,50),    0.25, 100),(0.20, (50,40,70),   0.45, 60)],
            "lava":    [(0.12, (60,20,10),    0.30, 85), (0.22, (100,40,15),  0.50, 50)],
            "ice":     [(0.14, (160,190,220), 0.35, 75), (0.24, (190,210,235), 0.55, 45)],
            "fortress":[(0.10, (40,30,55),    0.25, 95), (0.20, (70,55,90),   0.45, 55)],
            "sunset":  [(0.14, (120,60,40),   0.30, 80), (0.24, (180,100,50),  0.50, 50)],
            "space":   [],  # no hills in space
        }
        layers = []
        cfgs = configs.get(theme, configs["meadow"])
        for parallax, color, base_y, amplitude in cfgs:
            pts = []
            for x in range(0, SW + 40, 20):
                y = int(SH * base_y + math.sin(x * 0.008) * amplitude + math.sin(x * 0.02) * amplitude * 0.3)
                pts.append((x, y))
            pts.append((SW + 40, SH)); pts.append((0, SH))
            layers.append((parallax, color, pts))
        s.layers[theme] = layers
        return layers
    def draw(s, scr, ox, theme):
        for parallax, color, pts in s._gen(theme):
            offset = int(ox * parallax) % (SW + 40)
            shifted = [((x - offset) % (SW + 40), y) for x, y in pts]
            pygame.draw.polygon(scr, color, shifted)

# ─── v6: Ambient Theme Particles ────────────────────────────────────────
class AmbientParticles:
    """Theme-specific ambient floating particles."""
    def __init__(s):
        s.particles = []
    def reset(s, theme):
        s.particles = []
        count = 25
        if theme == "meadow":
            for _ in range(count):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                    "vx": random.uniform(-0.3, 0.3), "vy": random.uniform(-0.5, -0.1),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.5, 1.5),
                    "col": (180, 255, 100), "sz": random.choice([1, 2]),
                    "type": "firefly"
                })
        elif theme == "lava":
            for _ in range(count):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(SH * 0.5, SH),
                    "vx": random.uniform(-0.2, 0.2), "vy": random.uniform(-1.5, -0.5),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.8, 2.0),
                    "col": (255, random.randint(100, 200), 0), "sz": random.choice([1, 2, 2]),
                    "type": "ember"
                })
        elif theme == "ice":
            for _ in range(30):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                    "vx": random.uniform(-0.5, 0.5), "vy": random.uniform(0.3, 1.0),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.5, 1.0),
                    "col": (220, 235, 255), "sz": random.choice([1, 2]),
                    "type": "snow"
                })
        elif theme == "cave":
            for _ in range(15):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                    "vx": random.uniform(-0.1, 0.1), "vy": random.uniform(-0.3, -0.05),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.3, 0.8),
                    "col": (150, 200, 255), "sz": 1,
                    "type": "drip"
                })
        elif theme == "space":
            # handled by BGStars already, add shooting stars
            for _ in range(3):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH * 0.4),
                    "vx": random.uniform(3, 6), "vy": random.uniform(0.5, 1.5),
                    "ph": random.uniform(0, 6.28), "sp": 1.0,
                    "col": (255, 255, 255), "sz": 2,
                    "type": "shooting_star", "life": random.randint(60, 180), "trail": []
                })
        elif theme == "sunset":
            for _ in range(15):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                    "vx": random.uniform(-0.3, 0.3), "vy": random.uniform(-0.4, -0.1),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.5, 1.2),
                    "col": (255, 200, 100), "sz": 1,
                    "type": "firefly"
                })
        elif theme == "fortress":
            for _ in range(10):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                    "vx": random.uniform(-0.2, 0.2), "vy": random.uniform(-0.6, -0.1),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.5, 1.0),
                    "col": (200, 150, 255), "sz": 1,
                    "type": "firefly"
                })
        elif theme == "sky":
            for _ in range(count):
                s.particles.append({
                    "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                    "vx": random.uniform(-0.4, 0.4), "vy": random.uniform(-0.3, 0.3),
                    "ph": random.uniform(0, 6.28), "sp": random.uniform(0.5, 1.5),
                    "col": (255, 255, 200), "sz": 1,
                    "type": "firefly"
                })
    def update(s, t):
        for p in s.particles:
            if p["type"] == "shooting_star":
                p["trail"].append((p["x"], p["y"]))
                if len(p["trail"]) > 12: p["trail"].pop(0)
                p["x"] += p["vx"]; p["y"] += p["vy"]
                p["life"] -= 1
                if p["life"] <= 0 or p["x"] > SW + 20 or p["y"] > SH:
                    p["x"] = random.uniform(-50, 0); p["y"] = random.uniform(0, SH * 0.4)
                    p["life"] = random.randint(60, 180); p["trail"] = []
                continue
            p["x"] += p["vx"] + math.sin(t * 0.001 * p["sp"] + p["ph"]) * 0.3
            p["y"] += p["vy"]
            if p["y"] < -10: p["y"] = SH + 5
            elif p["y"] > SH + 10: p["y"] = -5
            if p["x"] < -10: p["x"] = SW + 5
            elif p["x"] > SW + 10: p["x"] = -5
    def draw(s, scr, t):
        for p in s.particles:
            if p["type"] == "shooting_star":
                # draw trail
                for i, (tx, ty) in enumerate(p["trail"]):
                    a = int(255 * (i + 1) / len(p["trail"]) * 0.5)
                    sz = max(1, p["sz"] * (i + 1) // len(p["trail"]))
                    c = (*p["col"][:3],)
                    sf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                    pygame.draw.circle(sf, (*c, a), (sz, sz), sz)
                    scr.blit(sf, (int(tx) - sz, int(ty) - sz))
                pygame.draw.circle(scr, p["col"], (int(p["x"]), int(p["y"])), p["sz"])
                continue
            alpha = int(120 + 100 * math.sin(t * 0.003 * p["sp"] + p["ph"]))
            alpha = max(0, min(255, alpha))
            sz = p["sz"]
            sf = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            pygame.draw.circle(sf, (*p["col"], alpha), (sz * 2, sz * 2), sz)
            # glow for fireflies
            if p["type"] == "firefly":
                pygame.draw.circle(sf, (*p["col"], alpha // 4), (sz * 2, sz * 2), sz * 3)
            scr.blit(sf, (int(p["x"]) - sz * 2, int(p["y"]) - sz * 2))

# ─── v6: Achievement Popup ──────────────────────────────────────────────
class AchievementPopup:
    """Slides in from the right, shows achievement name, then fades out."""
    def __init__(s, name, desc, icon="🏆"):
        s.name = name; s.desc = desc; s.icon = icon
        s.life = 180; s.ml = 180  # 3 seconds
        s.x_off = SW  # starts offscreen right
    def update(s):
        s.life -= 1
        # slide in for first 20 frames, hold, slide out last 30
        if s.life > s.ml - 20:
            s.x_off = SW - (s.ml - s.life) * (320 // 20)
        elif s.life < 30:
            s.x_off = SW - 320 + (30 - s.life) * (320 // 30)
        else:
            s.x_off = SW - 320
        return s.life > 0
    def draw(s, scr, rds):
        a = min(255, s.life * 4)
        panel = pygame.Surface((300, 60), pygame.SRCALPHA)
        panel.fill((20, 20, 40, min(200, a)))
        pygame.draw.rect(panel, (255, 215, 0, min(255, a)), (0, 0, 300, 60), 2, border_radius=10)
        sf = rds.render(s.icon)
        panel.blit(sf, (8, 10))
        nf = pygame.font.SysFont("Arial", 16, True)
        df = pygame.font.SysFont("Arial", 12)
        nt = nf.render(s.name, True, (255, 215, 0))
        dt = df.render(s.desc, True, (200, 200, 220))
        nt.set_alpha(a); dt.set_alpha(a)
        panel.blit(nt, (50, 8)); panel.blit(dt, (50, 30))
        panel.set_alpha(a)
        scr.blit(panel, (s.x_off, 60))

# ─── v6: Cannonball ──────────────────────────────────────────────────────
class Cannonball:
    """Projectile from cannon tiles."""
    def __init__(s, x, y, dx):
        s.x = float(x); s.y = float(y); s.dx = dx
        s.sp = CANNON_SPD; s.alive = True; s.life = 200
        s.at = 0
    def update(s, lw, solids):
        s.x += s.dx * s.sp; s.life -= 1; s.at += 1
        if s.life <= 0 or s.x < 0 or s.x > lw: s.alive = False
        r = s.rect()
        for sr in solids:
            if r.colliderect(sr):
                s.alive = False; break
    def rect(s): return pygame.Rect(s.x, s.y, TS - 8, TS - 8)
    def draw(s, scr, rd, cam):
        if not s.alive: return
        sx, sy = cam.apply(s.x, s.y)
        sf = rd.render("💣")
        # rotation effect based on movement
        angle = s.at * 15
        sf = pygame.transform.rotate(sf, angle if s.dx > 0 else -angle)
        scr.blit(sf, (sx, sy))

# ─── Moving Platform ─────────────────────────────────────────────────────
class MovPlat:
    def __init__(s,x,y,d):
        s.sx=float(x);s.sy=float(y);s.x=float(x);s.y=float(y)
        s.d=d;s.dist=TS*3;s.sp=1.5;s.t=0.0;s.px=s.x;s.py=s.y
    def update(s):
        s.px,s.py=s.x,s.y;s.t+=s.sp/s.dist
        if s.t>1: s.t-=2
        if s.d=="h": s.x=s.sx+math.sin(s.t*math.pi)*s.dist
        else: s.y=s.sy+math.sin(s.t*math.pi)*s.dist
    def delta(s): return s.x-s.px, s.y-s.py
    def rect(s): return pygame.Rect(s.x,s.y,TS,TS)

class CrumblePlat:
    def __init__(s,x,y):
        s.x=x;s.y=y;s.t=0;s.gone=False;s.rt=0
    def trigger(s):
        if s.t==0: s.t=1
    def update(s):
        if s.gone:
            s.rt-=1
            if s.rt<=0: s.gone=False;s.t=0
            return
        if s.t>0:
            s.t+=1
            if s.t>30: s.gone=True;s.rt=180
    def rect(s): return None if s.gone else pygame.Rect(s.x,s.y,TS,TS)

# ─── Player ──────────────────────────────────────────────────────────────
class Player:
    def __init__(s,x,y,skin=0):
        s.sx,s.sy=x,y;s.cx,s.cy=x,y
        s.x,s.y=float(x),float(y)
        s.w,s.h=TS-4,TS-2
        s.vx=s.vy=0.0;s.ground=False;s.right=True
        s.alive=True;s.lives=3;s.score=0;s.inv=0;s.at=0;s.skin=skin
        s.coyote=0;s.jbuf=0;s.djump=False;s.has_dj=False
        s.wall=0;s.wslide=False;s.sprint=False;s.trail=0
        s.jump_held=False  # for variable jump
        s.has_shield=False;s.has_magnet=False;s.mult=1;s.mult_t=0
        s.squash=1.0  # squash-stretch
        # v4: dash
        s.dash_t=0;s.dash_cd=0;s.dash_dx=0.0
        # v4: ice/water
        s.on_ice=False;s.in_water=False
        # v4: key/door
        s.has_key=False
        # v4: speed boost
        s.speed_boost_t=0
        # v4: potion invincibility
        s.potion_t=0
        # v4: dust timer
        s.dust_t=0
        # v5: drop-through
        s.drop_through=False
        # v6: landing detection
        s.was_airborne=False
        s.landed_this_frame=False
        s.land_vy=0  # velocity when landing (for dust intensity)
    @property
    def em(s):
        # v7: skin is always resolved to a string now
        if isinstance(s.skin, str):
            return s.skin
        return SKINS[s.skin % len(SKINS)]
    def checkpoint(s,x,y): s.cx,s.cy=x,y
    def spawn(s,x,y): s.sx,s.sy=x,y;s.cx,s.cy=x,y
    def to_cp(s):
        s.x,s.y=float(s.cx),float(s.cy);s.vx=s.vy=0.0
        s.ground=False;s.alive=True;s.inv=90;s.djump=s.has_dj
        s.coyote=s.jbuf=0;s.dash_t=0;s.dash_cd=0
        s.speed_boost_t=0
    def full_reset(s):
        s.x,s.y=float(s.sx),float(s.sy);s.cx,s.cy=s.sx,s.sy
        s.vx=s.vy=0.0;s.ground=False;s.alive=True;s.inv=60
        s.has_dj=s.djump=False;s.coyote=s.jbuf=0
        s.has_shield=s.has_magnet=False;s.mult=1;s.mult_t=0
        s.dash_t=s.dash_cd=0;s.dash_dx=0.0
        s.on_ice=False;s.in_water=False;s.has_key=False
        s.speed_boost_t=0;s.potion_t=0;s.dust_t=0;s.drop_through=False
        s.was_airborne=False;s.landed_this_frame=False;s.land_vy=0
    def try_jump(s,drop=False):
        if not s.alive: return
        s.jbuf=JBUF;s.jump_held=True
        # v5: drop through one-way platform
        if drop and s.ground and DROP_THROUGH:
            s.y+=4;s.ground=False;s.coyote=0;return "drop"
        if s.ground or s.coyote>0: s._jump();return "jump"
        if s.wslide: s._wjump();return "wjump"
        if s.djump and not s.ground:
            s.vy=DJUMP_F;s.djump=False;return "djump"
        return None
    def try_dash(s):
        if not s.alive or s.dash_cd>0 or s.dash_t>0: return False
        s.dash_t=DASH_DUR;s.dash_cd=DASH_CD
        s.dash_dx=s.w*1.5 if s.right else -s.w*1.5
        return True
    def update_dash(s):
        if s.dash_t>0:
            s.dash_t-=1;s.vx=s.dash_dx;s.vy=0
            return True
        if s.dash_cd>0: s.dash_cd-=1
        return False
    def release_jump(s):
        """Variable jump: cut velocity if releasing early while rising."""
        s.jump_held=False
        if s.vy < JUMP_CUT: s.vy = JUMP_CUT
    def _jump(s): s.vy=JUMP_FORCE;s.ground=False;s.coyote=s.jbuf=0
    def _wjump(s):
        s.vy=WJUMP_V;s.vx=-WJUMP_H if s.wall==-1 else WJUMP_H
        s.right=(s.wall==-1);s.jbuf=0
    def bounce(s): s.vy=BOUNCE_F;s.ground=False
    def update(s,keys,solids,conveyors=None,wind_zones=None,ice_rects=None,water_rects=None):
        if not s.alive: return
        s.at+=1
        if s.inv>0: s.inv-=1
        if s.jbuf>0: s.jbuf-=1
        if s.mult_t>0: s.mult_t-=1
        else: s.mult=1
        if s.speed_boost_t>0: s.speed_boost_t-=1
        if s.potion_t>0: s.potion_t-=1
        # squash recovery
        s.squash+=(1.0-s.squash)*0.15

        # dash overrides movement
        if s.update_dash(): return

        s.sprint=keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        spd=PLAYER_SPEED*(SPRINT_MULT if s.sprint else 1.0)
        if s.speed_boost_t>0: spd*=SPEED_BOOST_MULT
        s.vx=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: s.vx=-spd;s.right=False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: s.vx=spd;s.right=True

        # ice friction: keep momentum, don't zero vx
        s.on_ice=False
        if ice_rects and s.ground:
            pr=s.rect()
            for ir in ice_rects:
                if pr.colliderect(ir):
                    s.on_ice=True
                    # keep previous vx direction with friction
                    if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                        s.vx = getattr(s,'_ice_vx',s.vx)*ICE_FRIC
                    break

        # water: slow movement, reduced gravity
        s.in_water=False
        if water_rects:
            pr=s.rect()
            for wr in water_rects:
                if pr.colliderect(wr):
                    s.in_water=True;s.vx*=WATER_SLOW;break

        # dust particles (only when grounded and moving)
        if s.ground and abs(s.vx)>1:
            s.dust_t+=1
        else:
            s.dust_t=0

        # conveyor push
        if conveyors and s.ground:
            for cr,cd in conveyors:
                pr=s.rect()
                if pr.colliderect(cr):
                    s.vx += cd
                    break

        # wind
        if wind_zones:
            for wr,wd in wind_zones:
                pr=s.rect()
                if pr.colliderect(wr):
                    s.vx+=wd[0];s.vy+=wd[1]

        grav = WATER_GRAV if s.in_water else GRAVITY
        old_vy=s.vy
        s.vy+=grav
        mf = MAX_FALL*0.4 if s.in_water else MAX_FALL
        if s.vy>mf: s.vy=mf

        # wall sliding (works when pressing into wall too)
        s.wslide=False;s.wall=0
        if not s.ground and s.vy>0:
            tl=pygame.Rect(s.x-3,s.y+2,3,s.h-4)
            tr=pygame.Rect(s.x+s.w,s.y+2,3,s.h-4)
            for sr in solids:
                if tl.colliderect(sr): s.wall=-1;s.wslide=True
                if tr.colliderect(sr): s.wall=1;s.wslide=True
        if s.wslide and s.vy>WSLIDE_SPD: s.vy=WSLIDE_SPD

        if s.ground: s.coyote=COYOTE;s.djump=s.has_dj
        elif s.coyote>0: s.coyote-=1

        # v5: drop-through: skip one-way collision when dropping
        skip_one_way = s.drop_through and s.vy>0
        if s.vy>0 and not (keys[pygame.K_DOWN] or keys[pygame.K_s]):
            s.drop_through=False
        s.x+=s.vx;s._cx(solids)
        old_ground=s.ground
        s.ground=False;s.y+=s.vy;s._cy(solids,one_way_pass=not skip_one_way)
        # v6: landing detection
        if s.ground and not old_ground and s.was_airborne:
            s.landed_this_frame=True
            s.land_vy=old_vy
        else:
            s.landed_this_frame=False
        if s.ground: s.was_airborne=False
        elif not s.ground and old_ground: s.was_airborne=True
        if s.jbuf>0 and (s.ground or s.coyote>0): s._jump()
    def _cx(s,rects):
        pr=s.rect()
        for r in rects:
            if pr.colliderect(r):
                if s.vx>0: s.x=r.left-s.w
                elif s.vx<0: s.x=r.right
                pr=s.rect()
    def _cy(s,rects,one_way_pass=False):
        pr=s.rect()
        for r in rects:
            if pr.colliderect(r):
                if s.vy>0:
                    # one-way: only collide if player was above
                    if one_way_pass and hasattr(r,'_oneway') and r._oneway:
                        if s.y+s.h-s.vy > r.top+4: continue
                    s.y=r.top-s.h;s.vy=0;s.ground=True
                    # landing squash
                    if s.squash>0.95: s.squash=0.7
                    if s.on_ice: s._ice_vx=s.vx
                elif s.vy<0:
                    s.y=r.bottom;s.vy=0
                pr=s.rect()
    def rect(s): return pygame.Rect(s.x,s.y,s.w,s.h)
    def hurt(s):
        if s.inv>0 or s.potion_t>0: return False
        if s.has_shield:
            s.has_shield=False;s.inv=30;return False
        s.lives-=1;s.alive=False;return True
    def draw(s,scr,rd,cam):
        if not s.alive: return
        if s.inv>0 and (s.inv//4)%2==0: return
        sx,sy=cam.apply(s.x,s.y)
        em=P_JUMP if not s.ground else (P_WALL if s.wslide else s.em)
        sf=rd.render(em)
        # squash-stretch
        if abs(s.squash-1.0)>0.02:
            ow,oh=sf.get_size()
            nw=max(1,int(ow*(2-s.squash)));nh=max(1,int(oh*s.squash))
            sf=pygame.transform.smoothscale(sf,(nw,nh))
            sx-=(nw-ow)//2;sy+=(oh-nh)  # anchor at feet
        # idle breathing animation
        elif s.ground and abs(s.vx)<0.5 and s.alive:
            breath=1.0+0.03*math.sin(s.at*0.05)
            ow,oh=sf.get_size()
            nw=max(1,int(ow*breath));nh=max(1,int(oh*(2.0-breath)))
            sf=pygame.transform.smoothscale(sf,(nw,nh))
            sx-=(nw-ow)//2;sy+=(oh-nh)
        if not s.right: sf=pygame.transform.flip(sf,True,False)
        scr.blit(sf,(sx,sy))
        # dash afterimage
        if s.dash_t>0:
            sf2=sf.copy();sf2.set_alpha(100)
            scr.blit(sf2,(sx-(8 if s.right else -8),sy))
        # shield indicator
        if s.has_shield:
            ss=rd.render("🛡️");ss.set_alpha(100)
            scr.blit(ss,(sx-4,sy-4))
        # potion glow
        if s.potion_t>0:
            t=pygame.time.get_ticks()
            glow=pygame.Surface((s.w+12,s.h+12),pygame.SRCALPHA)
            a=int(80+40*math.sin(t*0.015))
            glow.fill((255,255,100,a))
            scr.blit(glow,(sx-6,sy-6))
        # water tint
        if s.in_water:
            wt=pygame.Surface((s.w,s.h),pygame.SRCALPHA);wt.fill((50,100,255,40))
            scr.blit(wt,(sx,sy))

# ─── Enemy ───────────────────────────────────────────────────────────────
class Enemy:
    def __init__(s,x,y,tt):
        s.x,s.y=float(x),float(y);s.tt=tt;s.em=TD[tt][0]
        s.w,s.h=TS-4,TS-4;s.alive=True;s.at=0
        if tt==7: s.vx=1.5;s.fly=False
        elif tt==8: s.vx=1.0;s.fly=False
        elif tt==26: s.vx=1.2;s.fly=True;s.by=float(y);s.fa=TS*2;s.fs=0.03
        elif tt==41: s.vx=0.8;s.fly=True;s.by=float(y);s.fa=TS*1.5;s.fs=0.025;s.shoot_cd=90
    def update(s,sol,lw,pl=None):
        if not s.alive: return
        s.at+=1
        # v6: chaser AI (tt=48) - follows player
        if s.tt==48:
            if pl and pl.alive:
                dx=pl.x-s.x; dy=pl.y-s.y
                dist=math.sqrt(dx*dx+dy*dy)
                if dist>0:
                    spd=2.2 if dist<TS*8 else 1.2  # speed up when close
                    if dist>TS*15: spd=0.8  # slow when far
                    s.vx = (dx/dist)*spd
                    s.vy = (dy/dist)*spd * 0.6  # less vertical tracking
                    s.x+=s.vx; s.y+=s.vy
                    s.x=max(0,min(s.x,lw-s.w))
                    s.y=max(0,min(s.y,2000-s.h))  # keep in bounds
                    return
        if s.fly:
            s.x+=s.vx;s.y=s.by+math.sin(s.at*s.fs)*s.fa
            if s.x<0 or s.x+s.w>lw: s.vx*=-1;s.x=max(0,min(s.x,lw-s.w))
        else:
            s.x+=s.vx;pr=s.rect()
            for r in sol:
                if pr.colliderect(r):
                    if s.vx>0: s.x=r.left-s.w
                    else: s.x=r.right
                    s.vx*=-1;pr=s.rect()
            if s.x<0 or s.x+s.w>lw: s.vx*=-1;s.x=max(0,min(s.x,lw-s.w))
        # dragon shoot cooldown
        if s.tt==41 and hasattr(s,'shoot_cd'):
            if s.shoot_cd>0: s.shoot_cd-=1
    def rect(s): return pygame.Rect(s.x,s.y,s.w,s.h)
    def draw(s,scr,rd,cam):
        if not s.alive: return
        sx,sy=cam.apply(s.x,s.y)
        bob=math.sin(s.at*0.1)*(4 if s.fly else 3)
        sf=rd.render(s.em)
        if s.vx<0: sf=pygame.transform.flip(sf,True,False)
        scr.blit(sf,(sx,sy+bob))

# ─── Level ───────────────────────────────────────────────────────────────
class Level:
    def __init__(s,cols=60,rows=16):
        s.cols=cols;s.rows=rows;s.tiles=[[0]*cols for _ in range(rows)]
        s.name="Untitled";s.theme="meadow"
        s.width=cols*TS;s.height=rows*TS
        s.spawn=(TS*2,TS*(rows-3))
    def set(s,r,c,t):
        if 0<=r<s.rows and 0<=c<s.cols: s.tiles[r][c]=t
    def get(s,r,c):
        if 0<=r<s.rows and 0<=c<s.cols: return s.tiles[r][c]
        return 0

    def solid_rects(s):
        R=[]
        for r in range(s.rows):
            for c in range(s.cols):
                t=s.tiles[r][c];cat=TD[t][1]
                if TD[t][2] and cat not in ("moving_h","moving_v","bounce","crumble","speed_pad","spring","cannon_l","cannon_r"):
                    rc=pygame.Rect(c*TS,r*TS,TS,TS)
                    if cat=="one_way": rc._oneway=True
                    R.append(rc)
        return R
    def ice_rects(s):
        return [pygame.Rect(c*TS,r*TS,TS,TS) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==35]
    def water_rects(s):
        return [pygame.Rect(c*TS,r*TS,TS,TS) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==36]
    def speed_pads(s):
        return [pygame.Rect(c*TS,r*TS,TS,TS) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==37]
    def doors(s):
        return [(r,c) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==39]
    def traps(s):
        return [(r,c) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==43]
    def dragon_fireballs(s):
        return []  # managed dynamically in game
    def mov_plats(s):
        R=[]
        for r in range(s.rows):
            for c in range(s.cols):
                t=s.tiles[r][c]
                if t==19: R.append(MovPlat(c*TS,r*TS,"h"))
                elif t==20: R.append(MovPlat(c*TS,r*TS,"v"))
        return R
    def crumble_plats(s):
        R=[]
        for r in range(s.rows):
            for c in range(s.cols):
                if s.tiles[r][c]==24: R.append(CrumblePlat(c*TS,r*TS))
        return R
    def bounce_pads(s):
        return [pygame.Rect(c*TS,r*TS,TS,TS) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==21]
    def checkpoints(s):
        return [(r,c) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==22]
    def teleporters(s):
        return [(c*TS,r*TS) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==25]
    def enemies(s):
        return [(t,c*TS,r*TS) for r in range(s.rows) for c in range(s.cols) if (t:=s.tiles[r][c]) in (7,8,26,41,48)]
    def springs(s):
        return [pygame.Rect(c*TS,r*TS,TS,TS) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c]==45]
    def cannons(s):
        R=[]
        for r in range(s.rows):
            for c in range(s.cols):
                t=s.tiles[r][c]
                if t==46: R.append((c*TS,r*TS,-1,0))  # (x,y,dx,cd)
                elif t==47: R.append((c*TS,r*TS,1,0))
        return R
    def collectibles(s):
        return [(t,r,c) for r in range(s.rows) for c in range(s.cols) if (t:=s.tiles[r][c]) in (5,6,13,14,23,27,31,32,34,38,40,42)]
    def magnet_coins(s):
        """v6: Returns collectible tile positions for magnet attraction."""
        return [(t,r,c) for r in range(s.rows) for c in range(s.cols) if (t:=s.tiles[r][c]) in (5,6,13,27,42)]
    def hazards(s):
        return [pygame.Rect(c*TS+4,r*TS+4,TS-8,TS-8) for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c] in (9,10,16,36,43)]
    def goal(s):
        for r in range(s.rows):
            for c in range(s.cols):
                if s.tiles[r][c]==11: return pygame.Rect(c*TS,r*TS,TS,TS)
        return None
    def wind_zones(s):
        R=[]
        for r in range(s.rows):
            for c in range(s.cols):
                if s.tiles[r][c]==33: R.append((pygame.Rect(c*TS,r*TS,TS,TS),(1.5,0)))
        return R
    def conveyors(s):
        R=[]
        for r in range(s.rows):
            for c in range(s.cols):
                t=s.tiles[r][c]
                if t==29: R.append((pygame.Rect(c*TS,r*TS,TS,TS),-1.5))
                elif t==30: R.append((pygame.Rect(c*TS,r*TS,TS,TS),1.5))
        return R
    def total_col(s):
        return sum(1 for r in range(s.rows) for c in range(s.cols) if s.tiles[r][c] in (5,6,13,27,42))
    def clear_col(s,r,c):
        if 0<=r<s.rows and 0<=c<s.cols: s.tiles[r][c]=0
    def to_dict(s):
        return {"name":s.name,"cols":s.cols,"rows":s.rows,"tiles":s.tiles,"spawn":list(s.spawn),"theme":s.theme}
    @staticmethod
    def from_dict(d):
        lv=Level(d.get("cols",60),d.get("rows",16));lv.name=d.get("name","Untitled")
        lv.tiles=d["tiles"];lv.spawn=tuple(d.get("spawn",[80,lv.height-120]))
        lv.theme=d.get("theme","meadow");lv.width=lv.cols*TS;lv.height=lv.rows*TS;return lv
    def save(s,fn):
        with open(os.path.join(LEVELS_DIR,fn),"w") as f: json.dump(s.to_dict(),f,indent=2)
    @staticmethod
    def load(fn):
        with open(os.path.join(LEVELS_DIR,fn)) as f: return Level.from_dict(json.load(f))

# ─── Button ──────────────────────────────────────────────────────────────
class Btn:
    def __init__(s,x,y,w,h,txt,col,tc=WHITE,fs=28):
        s.r=pygame.Rect(x,y,w,h);s.txt=txt;s.col=col;s.tc=tc
        s.hc=tuple(min(c+40,255) for c in col)
        s.f=pygame.font.SysFont("Arial",fs,True);s.hov=False
    def upd(s,mp): s.hov=s.r.collidepoint(mp)
    def draw(s,scr):
        c=s.hc if s.hov else s.col
        pygame.draw.rect(scr,c,s.r,border_radius=10)
        pygame.draw.rect(scr,WHITE,s.r,2,border_radius=10)
        t=s.f.render(s.txt,True,s.tc);scr.blit(t,(s.r.centerx-t.get_width()//2,s.r.centery-t.get_height()//2))
    def hit(s,e): return e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and s.r.collidepoint(e.pos)

# ─── Level helpers ───────────────────────────────────────────────────────
def _gnd(lv,a,b,rows=(14,15),t=2):
    for r in rows:
        for c in range(a,b): lv.set(r,c,t)
def _grs(lv,a,b,row=13):
    for c in range(a,b): lv.set(row,c,4)
def _plt(lv,row,a,b,t=1):
    for c in range(a,b): lv.set(row,c,t)
def _gap(lv,a,b,rows=(13,14,15)):
    for r in rows:
        for c in range(a,b): lv.set(r,c,0)
def _coin_line(lv,row,cols,t=5):
    for c in cols: lv.set(row,c,t)

# ═══════════════════════════════════════════════════════════════════════
# LEVELS
# ═══════════════════════════════════════════════════════════════════════
def _lv1():
    lv=Level(60,16);lv.name="Green Meadows";lv.theme="meadow"
    _gnd(lv,0,60);_grs(lv,0,60);_gap(lv,15,18);_gap(lv,30,33)
    _plt(lv,11,8,13);_plt(lv,10,18,23);_plt(lv,8,25,29)
    _plt(lv,9,34,38);_plt(lv,7,40,46)
    # water pool
    for c in range(20,23): lv.set(15,c,36)
    for c in range(40,43): lv.set(15,c,36)
    # one-way platforms (new)
    _plt(lv,12,14,17,28);_plt(lv,11,28,31,28)
    _coin_line(lv,10,(9,10,11));_coin_line(lv,9,(19,20,21))
    _coin_line(lv,7,(26,27,28),6);_coin_line(lv,8,(35,36))
    _coin_line(lv,6,(42,43,44),13)
    lv.set(13,6,7);lv.set(13,22,8);lv.set(13,38,7)
    lv.set(15,16,10);lv.set(14,31,9)
    lv.set(6,20,14)  # mushroom
    lv.set(12,16,28);lv.set(12,28,28)  # one-way
    # conveyor
    lv.set(14,3,30);lv.set(14,4,30);lv.set(14,5,30)
    # shield
    lv.set(5,45,31)
    # wind
    lv.set(12,40,33);lv.set(12,41,33);lv.set(12,42,33)
    # score multiplier
    lv.set(4,50,34)
    # decorations
    lv.set(5,5,12);lv.set(4,6,12);lv.set(6,35,12);lv.set(5,36,12);lv.set(5,37,12)
    lv.set(3,50,17)
    # magnet
    lv.set(10,52,32)
    # flag
    lv.set(13,55,11);lv.spawn=(TS*2,TS*12)
    return lv

def _lv2():
    lv=Level(70,16);lv.name="Crystal Caves";lv.theme="cave"
    for c in range(70):
        if c not in range(10,12) and c not in range(22,25) and c not in range(38,41) and c not in range(52,55):
            lv.set(15,c,3);lv.set(14,c,3)
    _plt(lv,0,5,15,1);_plt(lv,0,30,45,1)
    _plt(lv,12,10,13,15);_plt(lv,10,18,22,1);_plt(lv,8,24,28,3)
    _plt(lv,11,32,37,15);_plt(lv,9,40,44,1);_plt(lv,7,46,51,3)
    _plt(lv,10,55,60,15);_plt(lv,6,62,67,1)
    # one-ways
    _plt(lv,13,10,14,28);_plt(lv,11,24,28,28)
    for r,c in [(11,11),(9,19),(9,20),(7,25),(7,26),(7,27),(10,34),(10,35),(8,42),(6,48),(6,49),(6,50),(9,57),(9,58),(5,64),(5,65)]:
        lv.set(r,c,6)
    lv.set(13,8,8);lv.set(13,20,7);lv.set(13,35,8);lv.set(13,48,7);lv.set(13,58,8)
    for c in range(10,12): lv.set(15,c,16)
    for c in range(22,25): lv.set(15,c,10)
    for c in range(38,41): lv.set(15,c,16)
    # wind zone
    lv.set(5,30,33);lv.set(5,31,33);lv.set(5,32,33)
    # conveyor
    lv.set(13,40,29);lv.set(13,41,29);lv.set(13,42,29)
    # shield + magnet
    lv.set(4,50,31);lv.set(8,60,32)
    # multiplier
    lv.set(3,65,34)
    # deco
    lv.set(1,7,18);lv.set(1,8,18);lv.set(2,33,12);lv.set(1,34,12)
    lv.set(5,50,14);lv.set(13,65,11);lv.spawn=(TS*2,TS*12)
    return lv

def _lv3():
    lv=Level(80,20);lv.name="Sky Gardens";lv.theme="sky"
    for a,b in [(0,8),(20,28),(42,50),(60,68),(73,80)]:
        _gnd(lv,a,b,(18,19),2);_grs(lv,a,b,17)
    _plt(lv,15,10,14);_plt(lv,13,16,20);_plt(lv,11,29,34,15)
    _plt(lv,14,35,40);_plt(lv,12,51,56);_plt(lv,10,58,63,15)
    _plt(lv,8,69,74)
    # one-way sections
    _plt(lv,16,8,11,28);_plt(lv,14,28,34,28)
    # movers
    lv.set(16,8,19);lv.set(12,14,20);lv.set(10,27,19)
    lv.set(15,41,20);lv.set(11,50,19);lv.set(9,57,20);lv.set(7,68,19)
    # bounce
    for c in (5,25,45,65): lv.set(17,c,21)
    for c in (15,35,55): lv.set(17,c,37)  # speed pads
    # checkpoints
    for c in (22,44,62): lv.set(17,c,22)
    # double jump
    lv.set(9,32,23);lv.set(6,71,23)
    # collectibles
    _coin_line(lv,14,(11,12,13));_coin_line(lv,12,(17,18,19))
    _coin_line(lv,10,(30,31,32,33),13);_coin_line(lv,13,(36,37,38,39))
    _coin_line(lv,11,(52,53,54,55),6);_coin_line(lv,9,(59,60,61,62),13)
    _coin_line(lv,7,(70,71,72,73));_coin_line(lv,6,(75,76,77,78),6)
    # enemies
    lv.set(17,21,7);lv.set(17,43,8);lv.set(17,61,7)
    # bats
    lv.set(8,15,26);lv.set(6,35,26);lv.set(9,55,26);lv.set(5,70,26)
    # wind
    for c in range(35,40): lv.set(12,c,33)
    # conveyor
    lv.set(16,50,30);lv.set(16,51,30)
    # shield + magnet + multiplier
    lv.set(7,40,31);lv.set(5,60,32);lv.set(4,75,34)
    # hazards
    lv.set(18,15,10);lv.set(18,35,9);lv.set(18,55,10)
    # deco
    lv.set(4,10,12);lv.set(3,12,12);lv.set(5,30,12);lv.set(3,50,17)
    lv.set(4,70,12);lv.set(3,72,12)
    # mushroom
    lv.set(8,40,14);lv.set(5,65,14)
    lv.set(17,77,11);lv.spawn=(TS*2,TS*15)
    return lv

def _lv4():
    lv=Level(75,16);lv.name="Lava Dungeon";lv.theme="lava"
    for c in range(75): lv.set(15,c,10)
    _gnd(lv,0,5,(14,),3);_plt(lv,14,8,11,15)
    _plt(lv,14,14,17,24);_plt(lv,14,19,22,3);_plt(lv,14,25,28,24)
    _plt(lv,13,30,34,1);_plt(lv,14,36,39,24);_plt(lv,12,40,44,1)
    _plt(lv,14,46,49,3);_plt(lv,14,51,54,24);_plt(lv,11,55,60,1)
    _plt(lv,14,62,65,15);_plt(lv,14,67,70,24);_gnd(lv,71,75,(14,),3)
    # one-ways
    _plt(lv,12,8,11,28);_plt(lv,10,30,34,28)
    # upper gems
    _plt(lv,10,10,13,1);_plt(lv,8,20,24,3);_plt(lv,9,33,36,1)
    _plt(lv,7,42,46,15);_plt(lv,8,57,61,1);_plt(lv,6,64,68,1)
    # movers
    for c in (5,17,24,34,39,45,50,54,60,65,70): lv.set(13 if c<30 else 12 if c<50 else 10 if c<60 else 7, c, 19)
    # bounce
    lv.set(13,12,21);lv.set(11,22,21);lv.set(10,35,21)
    # checkpoints
    for c in (10,30,46,62): lv.set(13 if c<40 else 10, c, 22)
    # gems
    _coin_line(lv,9,(11,12),6);_coin_line(lv,7,(21,22,23),6)
    _coin_line(lv,8,(34,35),13);_coin_line(lv,6,(43,44,45),6)
    _coin_line(lv,7,(58,59,60),13);_coin_line(lv,5,(65,66,67),6)
    # coins
    _coin_line(lv,13,(9,10),27);_coin_line(lv,13,(20,21),27)
    _coin_line(lv,12,(31,32,33),27);_coin_line(lv,11,(41,42,43),27)
    _coin_line(lv,10,(56,57),27);_coin_line(lv,13,(63,64),27)
    # enemies
    lv.set(13,9,8);lv.set(13,21,7);lv.set(12,32,8)
    lv.set(11,41,7);lv.set(10,56,8);lv.set(13,63,7)
    # bats
    lv.set(6,15,26);lv.set(5,28,26);lv.set(4,48,26);lv.set(3,61,26)
    # wind + conveyor
    for c in range(25,28): lv.set(10,c,33)
    lv.set(14,40,29);lv.set(14,41,29)
    # powerups
    lv.set(6,23,23);lv.set(5,44,14);lv.set(4,59,23)
    lv.set(3,35,31);lv.set(2,50,32);lv.set(2,70,34)
    # key+door puzzle
    lv.set(10,15,38);lv.set(12,28,39)  # key then door
    # teleporter
    lv.set(12,18,25);lv.set(9,42,25)
    # deco
    lv.set(1,5,17);lv.set(1,25,17);lv.set(2,45,12);lv.set(1,60,12)
    lv.set(13,73,11);lv.spawn=(TS*2,TS*12)
    return lv

def _lv5():
    lv=Level(80,18);lv.name="Frozen Peaks";lv.theme="ice"
    _gnd(lv,0,80,(16,17),3)
    for a,b in [(12,15),(28,31),(45,48),(62,65)]:
        _gap(lv,a,b,(16,17))
        for c in range(a,b): lv.set(17,c,16)
    # platforms
    _plt(lv,13,5,9);_plt(lv,11,10,12,24);_plt(lv,14,15,18,3)
    _plt(lv,13,6,8,35)  # ice patches
    _plt(lv,12,20,24);_plt(lv,10,25,28,24);_plt(lv,13,31,35,15)
    _plt(lv,11,36,39);_plt(lv,9,40,44,24);_plt(lv,12,48,53)
    _plt(lv,11,37,39,35)  # ice
    _plt(lv,10,55,58,15);_plt(lv,8,59,62,24);_plt(lv,13,65,70,3)
    _plt(lv,11,72,77)
    # one-ways
    _plt(lv,12,15,18,28);_plt(lv,10,31,35,28);_plt(lv,8,48,53,28)
    # upper route
    _plt(lv,8,8,12);_plt(lv,6,22,26,3);_plt(lv,7,37,41)
    _plt(lv,5,50,54,15);_plt(lv,6,66,71)
    # movers
    for c,sp in [(3,19),(13,20),(19,19),(29,19),(35,20),(44,19),(47,19),(54,20),(63,19),(71,19)]:
        lv.set(sp if sp==19 else 11, c, sp)
    # bounce
    for c in (7,25,42,58): lv.set(15,c,21)
    # checkpoints
    for c in (10,30,50,68): lv.set(15,c,22)
    # collectibles main
    _coin_line(lv,12,(6,7,8),27);_coin_line(lv,13,(16,17),5)
    _coin_line(lv,11,(21,22,23),27);_coin_line(lv,12,(32,33,34),5)
    _coin_line(lv,10,(37,38),27);_coin_line(lv,11,(49,50,51,52),5)
    _coin_line(lv,9,(56,57),27);_coin_line(lv,12,(66,67,68,69),5)
    _coin_line(lv,10,(73,74,75,76),27)
    # gems upper
    _coin_line(lv,7,(9,10,11),6);_coin_line(lv,5,(23,24,25),6)
    _coin_line(lv,6,(38,39,40),6);_coin_line(lv,4,(51,52,53),13)
    _coin_line(lv,5,(67,68,69,70),6)
    # enemies
    lv.set(15,6,8);lv.set(15,17,7);lv.set(15,33,8);lv.set(15,40,7)
    lv.set(15,52,8);lv.set(15,60,7);lv.set(15,70,8)
    # bats
    lv.set(5,14,26);lv.set(4,27,26);lv.set(3,43,26);lv.set(4,60,26);lv.set(3,74,26)
    # hazards
    lv.set(15,20,16);lv.set(15,36,16);lv.set(15,55,16)
    # wind + conveyor
    for c in range(40,44): lv.set(8,c,33)
    lv.set(15,30,30);lv.set(15,31,30);lv.set(15,50,29)
    # powerups
    lv.set(9,26,14);lv.set(6,39,14);lv.set(7,70,14)
    lv.set(5,24,23);lv.set(4,52,23)
    lv.set(3,35,31);lv.set(2,60,32);lv.set(2,75,34)
    # teleporter
    lv.set(11,20,25);lv.set(8,48,25)
    # deco
    for c in (2,15,30,46,60,75): lv.set(2,c,12)
    lv.set(1,40,17)
    lv.set(15,78,11);lv.spawn=(TS*2,TS*13)
    return lv

def _lv6():
    lv=Level(90,18);lv.name="Final Fortress";lv.theme="fortress"
    for c in range(90):
        if c not in range(8,10) and c not in range(18,21) and c not in range(32,35) \
           and c not in range(46,49) and c not in range(58,61) and c not in range(72,75) and c not in range(84,87):
            lv.set(16,c,1);lv.set(17,c,1)
    _plt(lv,0,5,15,3);_plt(lv,0,25,40,3);_plt(lv,0,50,65,3);_plt(lv,0,75,90,3)
    for a,b,h in [(8,10,10),(18,21,9),(32,35,10),(46,49,16),(58,61,10),(72,75,9),(84,87,10)]:
        for c in range(a,b): lv.set(17,c,h)
    # layered platforms
    _plt(lv,13,10,14,24);_plt(lv,11,15,19);_plt(lv,8,5,9,15)
    _plt(lv,13,21,25,3);_plt(lv,10,26,30,24);_plt(lv,12,31,34)
    _plt(lv,8,22,27,15);_plt(lv,6,28,33)
    _plt(lv,14,40,44,3);_plt(lv,11,45,48,24);_plt(lv,13,49,54)
    _plt(lv,9,42,47,15);_plt(lv,7,51,56);_plt(lv,5,43,48,3)
    _plt(lv,12,61,65);_plt(lv,10,66,70,24);_plt(lv,13,71,74,3)
    _plt(lv,8,62,67,15);_plt(lv,6,68,73)
    _plt(lv,11,76,80);_plt(lv,9,81,85,24);_plt(lv,12,86,89,3)
    _plt(lv,7,77,82,15);_plt(lv,5,83,88)
    # one-ways
    _plt(lv,12,15,19,28);_plt(lv,10,49,54,28);_plt(lv,8,76,80,28)
    # movers
    for c,r in [(7,12),(10,14),(17,11),(20,12),(25,9),(30,10),(35,11),(39,13),(44,10),(48,12),(52,8),(56,11),(60,13),(65,10),(70,11),(75,13),(80,10),(85,8)]:
        lv.set(r,c,19 if r%2==0 else 20)
    # bounce
    for c in (5,22,42,62,78): lv.set(15,c,21)
    # checkpoints
    for c in (10,28,46,64,80): lv.set(15,c,22)
    # wings
    lv.set(5,30,23);lv.set(4,52,23);lv.set(3,70,23)
    # coins
    for g in [(6,7),(11,12,13),(22,23,24),(31,32,33),(41,42,43),(49,50,51,52,53),(61,62,63,64),(71,72,73),(76,77,78,79),(86,87,88)]:
        for c in g: lv.set(15,c,27)
    # gems
    for g in [(7,8,9),(23,24,25,26),(43,44,45,46),(63,64,65,66),(68,69,70,71,72),(78,79,80,81),(84,85,86,87)]:
        for c in g: lv.set(7 if g[0]<30 else 4 if g[0]<50 else 7, c, 6 if len(g)<5 else 13)
    # enemies
    for r,c,t in [(15,4,8),(15,12,7),(15,23,8),(15,34,7),(15,44,8),(15,55,7),(15,63,8),(15,74,7),(15,82,8)]:
        lv.set(r,c,t)
    # dragons
    for c,r in [(8,20),(6,48),(5,72)]: lv.set(r,c,41)
    # bats
    for c,r in [(14,26),(8,35),(12,47),(7,55),(10,68),(6,76),(9,83)]: lv.set(r,c,26)
    # mushrooms
    for c in (9,33,47,67,82): lv.set(7 if c<20 else 6 if c<40 else 4 if c<60 else 5, c, 14)
    # wind + conveyor
    for c in range(25,30): lv.set(8,c,33)
    for c in range(65,70): lv.set(10,c,33)
    lv.set(15,50,29);lv.set(15,51,29)
    lv.set(15,76,30);lv.set(15,77,30)
    # powerups
    lv.set(3,45,31);lv.set(2,60,32);lv.set(2,88,34)
    # teleporters
    lv.set(12,16,25);lv.set(9,42,25);lv.set(10,59,25);lv.set(7,77,25)
    # deco
    for c in (3,20,40,60,80): lv.set(2,c,12)
    lv.set(1,35,17);lv.set(1,70,17)
    lv.set(15,89,11);lv.spawn=(TS*2,TS*13)
    return lv

def _lv7():
    lv=Level(85,18);lv.name="Sunset Beach";lv.theme="sunset"
    # ground with sandy gaps (water = fire tiles below)
    _gnd(lv,0,85,(16,17),2)
    for a,b in [(8,12),(20,24),(35,39),(50,54),(65,69),(78,82)]:
        _gap(lv,a,b,(16,17))
        for c in range(a,b): lv.set(17,c,10)  # "water" hazard
    # beach platforms
    _plt(lv,14,5,9);_plt(lv,12,12,17);_plt(lv,13,18,21)
    _plt(lv,11,24,28);_plt(lv,13,30,35);_plt(lv,10,37,41)
    _plt(lv,12,42,46);_plt(lv,9,47,50);_plt(lv,11,54,58)
    _plt(lv,13,60,65);_plt(lv,10,67,71);_plt(lv,12,74,78);_plt(lv,11,82,85)
    # crumble bridges over water
    for c in range(8,12): lv.set(15,c,24)
    for c in range(35,39): lv.set(15,c,24)
    for c in range(65,69): lv.set(15,c,24)
    # one-ways
    _plt(lv,13,12,17,28);_plt(lv,11,30,35,28);_plt(lv,9,47,50,28)
    # upper scenic route
    _plt(lv,8,10,14);_plt(lv,6,22,27);_plt(lv,7,40,44)
    _plt(lv,5,55,59);_plt(lv,6,72,76)
    # movers (surf platforms)
    lv.set(14,5,19);lv.set(11,17,20);lv.set(13,28,19)
    lv.set(10,40,20);lv.set(12,50,19);lv.set(9,62,20);lv.set(11,75,19)
    # bounce pads (trampolines on beach)
    for c in (7,22,42,62,80): lv.set(15,c,21)
    # checkpoints
    for c in (15,33,52,70): lv.set(15,c,22)
    # conveyor "currents" in water gaps
    lv.set(14,9,30);lv.set(14,10,30);lv.set(14,11,30)
    lv.set(14,36,29);lv.set(14,37,29);lv.set(14,38,29)
    lv.set(14,66,30);lv.set(14,67,30);lv.set(14,68,30)
    # wind zones (sea breeze)
    for c in range(25,30): lv.set(10,c,33)
    for c in range(58,63): lv.set(8,c,33)
    # collectibles
    _coin_line(lv,13,(6,7,8),27);_coin_line(lv,11,(13,14,15,16),5)
    _coin_line(lv,12,(19,20),27);_coin_line(lv,10,(25,26,27),5)
    _coin_line(lv,12,(31,32,33,34),27);_coin_line(lv,9,(38,39,40),5)
    _coin_line(lv,11,(43,44,45),27);_coin_line(lv,8,(48,49),5)
    _coin_line(lv,12,(55,56,57),27);_coin_line(lv,11,(61,62,63,64),5)
    _coin_line(lv,10,(68,69,70),27);_coin_line(lv,11,(75,76,77),5)
    # gems on upper route
    _coin_line(lv,7,(11,12,13),6);_coin_line(lv,5,(23,24,25,26),6)
    _coin_line(lv,6,(41,42,43),6);_coin_line(lv,4,(56,57,58),6)
    _coin_line(lv,5,(73,74,75),6)
    # bonus stars
    _coin_line(lv,9,(14,15),13);_coin_line(lv,6,(27,28),13);_coin_line(lv,8,(44,45),13);_coin_line(lv,7,(59,60),13)
    # enemies
    lv.set(15,4,7);lv.set(15,16,8);lv.set(15,33,7);lv.set(15,46,8)
    lv.set(15,60,7);lv.set(15,73,8)
    # bats
    lv.set(6,20,26);lv.set(5,45,26);lv.set(4,65,26);lv.set(5,82,26)
    # powerups
    lv.set(8,14,14);lv.set(5,26,14);lv.set(7,45,14)
    lv.set(4,59,14);lv.set(5,76,14)
    lv.set(5,30,23);lv.set(4,55,23)
    lv.set(3,40,31);lv.set(3,70,32);lv.set(2,80,34)
    # teleporters
    lv.set(12,22,25);lv.set(9,42,25)
    # decorations
    for c in (3,18,35,52,70,83): lv.set(4,c,12)
    for c in (10,28,48,68): lv.set(3,c,17)
    lv.set(15,83,11);lv.spawn=(TS*2,TS*13)
    return lv

def _lv8():
    lv=Level(90,22);lv.name="Neon Station";lv.theme="space"
    # floating platforms in space — no full ground
    _gnd(lv,0,10,(20,21),1);_gnd(lv,80,90,(20,21),1)
    # starting area
    _plt(lv,18,10,16,15);_plt(lv,16,17,22);_plt(lv,14,24,28,3)
    # first section: mover gauntlet
    lv.set(18,12,19);lv.set(16,18,20);lv.set(14,25,19)
    # mid-ground platforms
    _plt(lv,12,30,35);_plt(lv,10,37,42,15);_plt(lv,13,43,48)
    _plt(lv,11,49,54,3);_plt(lv,9,55,60,15);_plt(lv,12,61,66)
    _plt(lv,10,67,72,3);_plt(lv,8,73,78,15);_plt(lv,11,79,84)
    # one-way layers
    _plt(lv,17,10,16,28);_plt(lv,15,22,28,28);_plt(lv,13,35,40,28)
    _plt(lv,11,48,54,28);_plt(lv,9,66,72,28)
    # upper route (riskier but rewarding)
    _plt(lv,8,12,16);_plt(lv,6,20,25,3);_plt(lv,7,32,37)
    _plt(lv,5,42,47,15);_plt(lv,6,56,61);_plt(lv,4,68,73,3)
    _plt(lv,5,78,83)
    # movers (space elevators)
    lv.set(17,14,20);lv.set(15,22,19);lv.set(13,30,20)
    lv.set(11,38,19);lv.set(12,45,20);lv.set(10,52,19)
    lv.set(11,58,20);lv.set(9,65,19);lv.set(10,72,20);lv.set(8,80,19)
    # vertical movers
    lv.set(16,16,20);lv.set(12,35,20);lv.set(8,50,20);lv.set(6,70,20)
    # crumble platforms (space debris)
    for c in (11,26,40,53,64,76): lv.set(17 if c<30 else 14 if c<50 else 11 if c<65 else 9, c, 24)
    # bounce pads
    for c in (8,33,48,62,75,85): lv.set(19 if c<30 else 16 if c<50 else 13 if c<70 else 10, c, 21)
    # teleporter pairs (warp stations)
    lv.set(15,15,25);lv.set(10,40,25)   # pair 1
    lv.set(12,50,25);lv.set(7,70,25)    # pair 2
    lv.set(9,60,25);lv.set(5,82,25)    # pair 3
    # checkpoints
    for c in (20,40,60,80): lv.set(19 if c<40 else 16 if c<60 else 13 if c<80 else 10, c, 22)
    # wind zones (thrusters)
    for c in range(28,33): lv.set(10,c,33)
    for c in range(55,60): lv.set(8,c,33)
    for c in range(73,78): lv.set(6,c,33)
    # conveyor belts (spacewalk treads)
    lv.set(19,10,30);lv.set(19,11,30);lv.set(19,12,30)
    lv.set(13,43,29);lv.set(13,44,29);lv.set(13,45,29)
    lv.set(16,78,30);lv.set(16,79,30);lv.set(16,80,30)
    # collectibles main path
    _coin_line(lv,17,(11,12,13),27);_coin_line(lv,15,(18,19,20,21),5)
    _coin_line(lv,13,(25,26,27),27);_coin_line(lv,11,(31,32,33,34),5)
    _coin_line(lv,12,(44,45,46,47),27);_coin_line(lv,10,(50,51,52,53),5)
    _coin_line(lv,11,(62,63,64,65),27);_coin_line(lv,12,(68,69,70,71),5)
    _coin_line(lv,9,(74,75,76,77),27);_coin_line(lv,10,(80,81,82,83),5)
    # gems on upper route
    _coin_line(lv,7,(13,14,15),6);_coin_line(lv,5,(21,22,23,24),6)
    _coin_line(lv,6,(33,34,35,36),6);_coin_line(lv,4,(43,44,45,46),13)
    _coin_line(lv,5,(57,58,59,60),6);_coin_line(lv,3,(69,70,71,72),13)
    _coin_line(lv,4,(79,80,81,82),6)
    # bonus stars
    for r,c in [(16,16),(14,28),(12,37),(10,46),(8,56),(9,65),(7,74),(6,84)]: lv.set(r,c,13)
    # enemies
    for r,c,t in [(18,10,8),(16,20,7),(14,28,8),(12,36,7),(11,44,8),(10,52,7),(12,60,8),(10,68,7),(9,76,8),(10,82,7)]:
        lv.set(r,c,t)
    # bats (lots in space)
    for c,r in [(15,13),(10,23),(8,32),(6,42),(8,52),(5,62),(7,72),(4,83)]: lv.set(r,c,26)
    # powerups
    lv.set(7,15,14);lv.set(4,25,14);lv.set(6,38,14)
    lv.set(3,48,14);lv.set(5,62,14);lv.set(4,78,14)
    lv.set(6,22,23);lv.set(4,42,23);lv.set(3,65,23)
    lv.set(2,50,31);lv.set(2,72,32);lv.set(1,85,34)
    # hazards (space mines)
    for r,c in [(17,15),(15,25),(13,35),(11,45),(9,55),(10,65),(8,75),(7,85)]:
        lv.set(r,c,9)
    # decorations
    for c in (5,20,40,60,80): lv.set(2,c,12)
    for c in (15,35,55,75): lv.set(1,c,17)
    # flag
    lv.set(19,87,11);lv.spawn=(TS*2,TS*17)
    return lv

def _lv9():
    lv=Level(95,18);lv.name="Rainbow Temple";lv.theme="meadow"
    # temple floor with ornate gaps
    _gnd(lv,0,95,(16,17),15)
    # ritual gaps
    for a,b in [(10,13),(25,28),(42,45),(58,61),(75,78),(88,91)]:
        _gap(lv,a,b,(16,17))
        for c in range(a,b): lv.set(17,c,9)  # skull pits
    # temple platforms (brick and stone mix)
    _plt(lv,13,5,10,1);_plt(lv,11,10,14,3);_plt(lv,12,14,18,1)
    _plt(lv,10,18,22,3);_plt(lv,12,22,26,1);_plt(lv,11,28,32,3)
    _plt(lv,9,32,36,1);_plt(lv,11,36,40,15);_plt(lv,10,40,44,3)
    _plt(lv,12,44,48,1);_plt(lv,9,48,52,15);_plt(lv,11,52,56,3)
    _plt(lv,10,56,60,1);_plt(lv,8,60,64,15);_plt(lv,11,64,68,3)
    _plt(lv,10,68,72,1);_plt(lv,9,72,76,15);_plt(lv,12,76,80,3)
    _plt(lv,10,80,84,1);_plt(lv,11,84,88,3);_plt(lv,12,88,95,1)
    # one-way temple ceilings
    _plt(lv,12,5,10,28);_plt(lv,10,22,26,28);_plt(lv,9,40,44,28)
    _plt(lv,9,56,60,28);_plt(lv,8,72,76,28)
    # upper temple route (rainbow bridge)
    _plt(lv,7,8,13);_plt(lv,5,20,25,3);_plt(lv,6,35,40,1)
    _plt(lv,4,48,53,3);_plt(lv,5,63,68,1);_plt(lv,3,78,83,3)
    # crumble temple steps
    for c in range(10,13): lv.set(15,c,24)
    for c in range(25,28): lv.set(15,c,24)
    for c in range(42,45): lv.set(15,c,24)
    for c in range(58,61): lv.set(15,c,24)
    for c in range(75,78): lv.set(15,c,24)
    for c in range(88,91): lv.set(15,c,24)
    # movers (temple mechanisms)
    lv.set(12,7,19);lv.set(10,15,20);lv.set(11,23,19)
    lv.set(9,30,20);lv.set(10,37,19);lv.set(8,45,20)
    lv.set(10,52,19);lv.set(9,59,20);lv.set(10,67,19);lv.set(8,74,20)
    lv.set(10,82,19);lv.set(11,90,20)
    # bounce pads (temple springs)
    for c in (8,20,35,50,65,80,92): lv.set(15,c,21)
    # teleporter chains (temple portals)
    lv.set(11,12,25);lv.set(8,30,25)    # pair 1
    lv.set(10,38,25);lv.set(6,50,25)    # pair 2
    lv.set(9,55,25);lv.set(5,70,25)    # pair 3
    lv.set(10,76,25);lv.set(7,88,25)   # pair 4
    # checkpoints
    for c in (15,30,48,65,82): lv.set(15,c,22)
    # wind (temple gusts)
    for c in range(15,20): lv.set(8,c,33)
    for c in range(50,55): lv.set(7,c,33)
    for c in range(82,87): lv.set(6,c,33)
    # conveyors (temple conveyor floors)
    lv.set(14,5,30);lv.set(14,6,30);lv.set(14,7,30)
    lv.set(14,32,29);lv.set(14,33,29);lv.set(14,34,29)
    lv.set(14,62,30);lv.set(14,63,30);lv.set(14,64,30)
    # collectibles main path
    _coin_line(lv,12,(6,7,8),27);_coin_line(lv,10,(11,12,13,14),5)
    _coin_line(lv,11,(15,16,17),27);_coin_line(lv,9,(19,20,21),5)
    _coin_line(lv,11,(23,24,25),27);_coin_line(lv,10,(29,30,31),5)
    _coin_line(lv,8,(33,34,35),27);_coin_line(lv,11,(37,38,39),5)
    _coin_line(lv,9,(41,42,43),27);_coin_line(lv,11,(45,46,47),5)
    _coin_line(lv,8,(49,50,51),27);_coin_line(lv,10,(53,54,55),5)
    _coin_line(lv,9,(57,58,59),27);_coin_line(lv,10,(61,62,63),5)
    _coin_line(lv,7,(65,66,67),27);_coin_line(lv,11,(69,70,71),5)
    _coin_line(lv,9,(73,74,75),27);_coin_line(lv,11,(77,78,79),5)
    _coin_line(lv,9,(81,82,83),27);_coin_line(lv,11,(85,86,87,88),5)
    # gems upper
    _coin_line(lv,6,(9,10,11,12),6);_coin_line(lv,4,(21,22,23,24),6)
    _coin_line(lv,5,(36,37,38,39),6);_coin_line(lv,3,(49,50,51,52),13)
    _coin_line(lv,4,(64,65,66,67),6);_coin_line(lv,2,(79,80,81,82),13)
    # bonus stars
    for r,c in [(10,13),(8,22),(7,35),(6,45),(7,55),(5,68),(6,78),(8,90)]: lv.set(r,c,13)
    # enemies (temple guardians)
    for r,c,t in [(15,5,8),(15,16,7),(15,30,8),(15,40,7),(15,50,8),(15,60,7),(15,70,8),(15,82,7),(15,92,8)]:
        lv.set(r,c,t)
    # bats
    for c,r in [(14,18),(10,28),(8,38),(6,48),(8,58),(5,68),(7,78),(5,90)]: lv.set(r,c,26)
    # powerups
    lv.set(7,10,14);lv.set(4,22,14);lv.set(6,38,14)
    lv.set(3,50,14);lv.set(5,66,14);lv.set(4,82,14)
    lv.set(5,20,23);lv.set(3,42,23);lv.set(4,62,23);lv.set(3,85,23)
    lv.set(2,45,31);lv.set(2,72,32);lv.set(1,90,34)
    # decorations
    for c in (3,18,33,48,63,78,93): lv.set(3,c,12)
    for c in (10,28,45,62,80): lv.set(2,c,17)
    for c in (15,38,58,75,90): lv.set(1,c,18)  # rainbows
    # crystals (high value)
    for r,c in [(5,20),(4,50),(3,80)]: lv.set(r,c,42)
    # traps
    for r,c in [(15,20),(15,45),(15,70)]: lv.set(r,c,43)
    # potion
    lv.set(4,60,40)
    # flag
    lv.set(15,93,11);lv.spawn=(TS*2,TS*13)
    return lv

def _lv10():
    lv=Level(110,20);lv.name="The Gauntlet";lv.theme="fortress"
    # fortress floor with many hazard pits
    for c in range(110):
        if c not in range(6,9) and c not in range(16,19) and c not in range(28,31) \
           and c not in range(40,43) and c not in range(52,55) and c not in range(64,67) \
           and c not in range(76,79) and c not in range(88,91) and c not in range(100,103):
            lv.set(18,c,1);lv.set(19,c,1)
    # walls on sides
    for r in range(20):
        lv.set(r,0,1);lv.set(r,109,1)
    # hazard pits
    for a,b in [(6,9),(16,19),(28,31),(40,43),(52,55),(64,67),(76,79),(88,91),(100,103)]:
        for c in range(a,b): lv.set(19,c,10)  # lava in pits
    # platforms — multi-layered fortress
    # ground level
    _plt(lv,0,5,15,3);_plt(lv,0,25,40,3);_plt(lv,0,45,60,3)
    _plt(lv,0,65,80,3);_plt(lv,0,85,100,3);_plt(lv,0,100,110,3)
    # mid platforms
    _plt(lv,15,8,12,15);_plt(lv,13,14,18,1);_plt(lv,16,18,22,15)
    _plt(lv,14,22,26,3);_plt(lv,12,26,30,15);_plt(lv,15,30,34,1)
    _plt(lv,13,34,38,15);_plt(lv,16,38,42,3);_plt(lv,14,42,46,15)
    _plt(lv,12,46,50,1);_plt(lv,15,50,54,15);_plt(lv,13,54,58,3)
    _plt(lv,16,58,62,15);_plt(lv,14,62,66,1);_plt(lv,12,66,70,15)
    _plt(lv,15,70,74,3);_plt(lv,13,74,78,15);_plt(lv,16,78,82,1)
    _plt(lv,14,82,86,15);_plt(lv,12,86,90,3);_plt(lv,15,90,94,15)
    _plt(lv,13,94,98,1);_plt(lv,16,98,102,15);_plt(lv,14,102,106,3)
    # upper platforms
    _plt(lv,10,6,10);_plt(lv,8,15,20,3);_plt(lv,9,25,30,15)
    _plt(lv,7,35,40,3);_plt(lv,8,45,50,15);_plt(lv,6,55,60,3)
    _plt(lv,7,65,70,15);_plt(lv,5,75,80,3);_plt(lv,6,85,90,15)
    _plt(lv,4,95,100,3);_plt(lv,5,105,109,15)
    # top route (highest risk, best rewards)
    _plt(lv,4,8,13);_plt(lv,3,20,25,1);_plt(lv,4,32,37)
    _plt(lv,2,42,47,15);_plt(lv,3,52,57);_plt(lv,2,62,67,1)
    _plt(lv,3,72,77);_plt(lv,2,82,87,15);_plt(lv,3,92,97);_plt(lv,2,102,107,1)
    # one-way sections
    _plt(lv,14,8,12,28);_plt(lv,12,22,26,28);_plt(lv,14,38,42,28)
    _plt(lv,12,54,58,28);_plt(lv,14,70,74,28);_plt(lv,12,86,90,28)
    _plt(lv,14,98,102,28)
    # movers (fortress machinery)
    for c,r in [(7,16),(10,14),(13,15),(16,13),(19,16),(22,14),(25,15),
                (28,13),(31,16),(34,14),(37,15),(40,13),(43,16),(46,14),
                (49,15),(52,13),(55,16),(58,14),(61,15),(64,13),(67,16),
                (70,14),(73,15),(76,13),(79,16),(82,14),(85,15),(88,13),
                (91,16),(94,14),(97,15),(100,13),(103,16),(106,14)]:
        lv.set(r,c,19 if r%2==0 else 20)
    # crumble platforms over lava
    for a in [(6,9),(16,19),(28,31),(40,43),(52,55),(64,67),(76,79),(88,91),(100,103)]:
        for c in range(a[0],a[1]): lv.set(17,c,24)
    # bounce pads
    for c in (5,15,25,35,45,55,65,75,85,95,105): lv.set(17,c,21)
    # checkpoints every ~15 tiles
    for c in (10,25,40,55,70,85,100): lv.set(17,c,22)
    # teleporter pairs
    lv.set(14,12,25);lv.set(10,28,25)    # pair 1
    lv.set(12,35,25);lv.set(8,48,25)     # pair 2
    lv.set(14,55,25);lv.set(10,68,25)    # pair 3
    lv.set(12,78,25);lv.set(8,92,25)     # pair 4
    # wind zones
    for c in range(20,25): lv.set(10,c,33)
    for c in range(48,53): lv.set(8,c,33)
    for c in range(75,80): lv.set(6,c,33)
    for c in range(98,103): lv.set(5,c,33)
    # conveyors
    lv.set(17,5,30);lv.set(17,6,30)
    lv.set(17,20,29);lv.set(17,21,29)
    lv.set(17,35,30);lv.set(17,36,30)
    lv.set(17,50,29);lv.set(17,51,29)
    lv.set(17,65,30);lv.set(17,66,30)
    lv.set(17,80,29);lv.set(17,81,29)
    lv.set(17,95,30);lv.set(17,96,30)
    # collectibles main path (lots of coins)
    for c in range(5,108):
        r = 16 if c%4==0 else 0  # every 4th tile on main path
        if r: lv.set(r,c,27)
    # gems scattered
    for r,c in [(11,8),(9,15),(11,22),(9,30),(11,38),(9,45),(11,52),(9,60),
                (11,68),(9,75),(11,82),(9,90),(11,98),(9,105)]:
        lv.set(r,c,5)
    for r,c in [(8,10),(7,20),(8,28),(6,35),(7,42),(5,50),(6,58),(5,65),
                (7,72),(5,78),(6,85),(4,95),(5,102)]:
        lv.set(r,c,6)
    for r,c in [(5,12),(4,22),(5,32),(3,42),(4,52),(3,62),(4,72),(3,82),
                (4,92),(3,102)]:
        lv.set(r,c,13)
    # bonus stars on top route
    for r,c in [(3,9),(2,22),(3,34),(1,44),(2,55),(1,64),(3,74),(1,84),(2,94),(1,104)]:
        lv.set(r,c,13)
    # enemies — lots of them
    for r,c,t in [(17,5,8),(17,12,7),(17,20,8),(17,28,7),(17,35,8),(17,42,7),
                  (17,50,8),(17,58,7),(17,65,8),(17,72,7),(17,80,8),(17,88,7),
                  (17,95,8),(17,105,7)]:
        lv.set(r,c,t)
    # robots too
    for r,c in [(17,8),(17,18),(17,32),(17,48),(17,62),(17,78),(17,92),(17,102)]:
        lv.set(r,c,8)
    # bats everywhere
    for c,r in [(16,10),(14,18),(12,25),(10,33),(12,40),(10,48),(8,55),(10,62),
                (8,70),(10,78),(6,85),(8,92),(6,100),(8,108)]:
        lv.set(r,c,26)
    # powerups
    for c in (10,25,40,55,70,85,100):
        lv.set(8,c,14)  # mushrooms
    lv.set(6,18,23);lv.set(5,35,23);lv.set(4,52,23);lv.set(3,70,23);lv.set(2,88,23);lv.set(2,105,23)
    lv.set(3,30,31);lv.set(2,48,31)
    lv.set(3,65,32);lv.set(2,82,32)
    lv.set(1,45,34);lv.set(1,75,34);lv.set(1,108,34)
    # decorations
    for c in range(3,108,12):
        lv.set(2,c,12)
    for c in range(8,108,15):
        lv.set(1,c,17)
    # flag at end
    lv.set(17,107,11);lv.spawn=(TS*2,TS*15)
    return lv

# ═══════════════════════════════════════════════════════════════════════
# GAME
# ═══════════════════════════════════════════════════════════════════════
class Game:
    MENU=0;PLAY=1;EDIT=2;SEL=3;WIN=4;GO=5;PAUSE=6;SKINS=7;STATS=8;CREATOR=9

    def __init__(s):
        pygame.init();pygame.display.set_caption("\U0001f3ae Emoji Platformer v7")
        s.scr=pygame.display.set_mode((SW,SH));s.clk=pygame.time.Clock()
        s.snd=Snd();s.snd.init()
        # v5: background music
        s.music=s.snd._make_music()
        s.music_on=True
        s.rd=ER(40);s.rdb=ER(72);s.rds=ER(24);s.sky=SkyBG()
        s.st=0;s.hs=load_hs()
        s.builtins=[_lv1(),_lv2(),_lv3(),_lv4(),_lv5(),_lv6(),_lv7(),_lv8(),_lv9(),_lv10()]
        s.levels=list(s.builtins);s._scan()
        s.li=0;s.lv=None;s.pl=None;s.ens=[];s.mps=[];s.cps=[]
        s.cam=Cam(SW,SH);s.parts=[];s.ftxts=[];s.danims=[]
        s.fireballs=[];s.dust_parts=[]
        s.cannonballs=[];s.cannons_cd=[]  # v6: cannon projectiles + cooldowns
        s.collected=set();s.shake=Shake();s.clouds=ParallaxClouds()
        s.bgstars=BGStars();s.pstate=None;s.totcol=0;s.deaths=0
        s.combo=0;s.combo_t=0;s.start_time=0;s.elapsed=0
        s.tp_cooldown=0;s.activated_cp=set()
        s.opened_doors=set();s.triggered_traps=set()
        # v4: screen fade
        s.fade_alpha=255;s.fade_dir=-1  # -1=fading in, 0=none, 1=fading out
        s.fade_callback=None
        # v5: enemy poofs, heartbeat timer
        s.poofs=[];s.hb_t=0
        # v6: parallax hills, ambient particles, achievements, coin positions
        s.hills=ParallaxHills();s.ambient=AmbientParticles()
        s.ach_queue=[];s.ach_granted=set()
        # v6: achievement definitions
        s.achievements={
            "first_blood":  ("First Blood!",    "Stomp your first enemy",       "💀"),
            "combo_5":      ("Combo King!",     "Get a 5x combo",              "🔥"),
            "combo_10":     ("Unstoppable!",    "Get a 10x combo",             "⚡"),
            "speed_run":    ("Speed Demon!",    "Complete a level under 30s",   "🏃"),
            "coin_master":  ("Coin Master!",    "Collect all coins in a level", "🪙"),
            "no_death":     ("Flawless!",       "Complete a level with 0 deaths","✨"),
            "shield_save":  ("Shielded!",       "Block damage with a shield",  "🛡️"),
            "spring_king":  ("Spring Master!",  "Use a spring launcher",        "🎪"),
        }
        s.ambient_theme=None  # track current theme for ambient resets
        # editor
        s.elv=None;s.et=1;s.ec=Cam(SW,SH-100);s.eg=True
        s.em="";s.emt=0;s.efn="my_level";s.ehist=[]
        s.eti=0;s.etl=list(SKY_THEMES.keys())
        s.ecopy=None  # copy buffer for paste
        s.eshow_minimap=False
        s.ed_layer_filter=None  # None=show all, or category string

    def _scan(s):
        if not os.path.isdir(LEVELS_DIR): return
        for fn in sorted(os.listdir(LEVELS_DIR)):
            if fn.endswith(".json") and fn!="highscores.json":
                try:
                    lv=Level.load(fn)
                    if not any(l.name==lv.name for l in s.levels): s.levels.append(lv)
                except: pass

    def _unlocked(s): return s.hs.get("unlocked", 1)

    def _fx(s,x,y,em,n=6):
        for _ in range(n): s.parts.append(Part(x,y,em,random.uniform(-3,3),random.uniform(-5,-1),random.randint(20,40)))
    def _ft(s,x,y,txt,col=HILITE): s.ftxts.append(FText(x,y,txt,col))
    def _add_combo(s):
        s.combo+=1;s.combo_t=COMBO_WINDOW
        if s.combo>1: s.snd.play("combo")
        # v6: combo screen shake
        if s.combo>=5: s.shake.trigger(3, min(s.combo, 10))
        # v6: combo achievements
        if s.combo>=5 and "combo_5" not in s.ach_granted:
            s._grant_ach("combo_5")
        if s.combo>=10 and "combo_10" not in s.ach_granted:
            s._grant_ach("combo_10")
    def _grant_ach(s, key):
        if key in s.ach_granted: return
        s.ach_granted.add(key)
        if key in s.achievements and len(s.ach_queue)<ACHIEVEMENT_QUEUE_MAX:
            name, desc, icon = s.achievements[key]
            s.ach_queue.append(AchievementPopup(name, desc, icon))
            s.snd.play("achieve")
            # persist to highscores
            achs = s.hs.get("achievements", [])
            if key not in achs: achs.append(key)
            s.hs["achievements"] = achs
            save_hs(s.hs)

    def _start(s,i):
        if i>=len(s.levels): return
        if i>=s._unlocked(): return
        s.li=i;s.lv=s.levels[i]
        sk=s.hs.get("skin",0)
        # v7: resolve skin to string (handles custom skins)
        all_sk = get_all_skins(s.hs)
        if isinstance(sk, int):
            sk_str = all_sk[sk % len(all_sk)]
        else:
            sk_str = str(sk)
        s.pl=Player(*s.lv.spawn,skin=sk_str)
        s.ens=[Enemy(ex,ey,t) for t,ex,ey in s.lv.enemies()]
        s.mps=s.lv.mov_plats();s.cps=s.lv.crumble_plats()
        s.cam=Cam(SW,SH);s.parts=[];s.ftxts=[];s.danims=[]
        s.fireballs=[];s.dust_parts=[];s.poofs=[];s.hb_t=0
        s.cannonballs=[];s.cannons_cd=[]
        s.collected=set();s.shake=Shake();s.totcol=s.lv.total_col()
        s.deaths=0;s.combo=0;s.combo_t=0
        s.start_time=_time.time();s.elapsed=0
        s.tp_cooldown=0;s.activated_cp=set()
        s.opened_doors=set();s.triggered_traps=set()
        s.fade_alpha=255;s.fade_dir=-1;s.fade_callback=None
        # v6: reset ambient particles for theme
        s.ambient_theme=None
        s.snd.play("intro")
        # v5: start music
        if s.music and s.music_on and not pygame.mixer.get_busy():
            s.music.play(loops=-1)
        s.st=s.PLAY

    def _stars(s):
        if s.totcol==0: return 3
        p=len(s.collected)/s.totcol
        return 3 if p>=0.9 else 2 if p>=0.5 else 1

    def _grade(s):
        """v5: Level grade S/A/B/C based on time, coins, and deaths."""
        # score components
        time_score = max(0, 1.0 - s.elapsed / 120.0)  # 120s par
        coin_score = len(s.collected) / max(1, s.totcol)
        death_penalty = min(s.deaths * 0.05, 0.5)  # each death costs 5%
        total = time_score * 0.4 + coin_score * 0.4 + (1.0 - death_penalty) * 0.2
        if total >= 0.85: return "S", (255, 215, 0)
        elif total >= 0.65: return "A", (100, 255, 100)
        elif total >= 0.45: return "B", (100, 200, 255)
        else: return "C", (200, 200, 200)

    def _update_fade(s):
        if s.fade_dir==-1:
            s.fade_alpha=max(0,s.fade_alpha-8)
            if s.fade_alpha<=0: s.fade_dir=0
        elif s.fade_dir==1:
            s.fade_alpha=min(255,s.fade_alpha+8)
            if s.fade_alpha>=255:
                s.fade_dir=0
                if s.fade_callback: s.fade_callback();s.fade_callback=None
    def _draw_fade(s):
        if s.fade_alpha>0:
            fade=pygame.Surface((SW,SH));fade.fill(BLACK)
            fade.set_alpha(s.fade_alpha);s.scr.blit(fade,(0,0))

    def run(s):
        ok=True
        while ok:
            s.clk.tick(FPS);evts=pygame.event.get();mp=pygame.mouse.get_pos()
            for e in evts:
                if e.type==pygame.QUIT: ok=False;break
            if not ok: break
            s._update_fade()
            if s.fade_dir==1: pygame.display.flip();continue  # still fading out, skip input
            {s.MENU:s._t_menu,s.SEL:s._t_sel,s.PLAY:s._t_play,s.EDIT:s._t_edit,
             s.WIN:s._t_win,s.GO:s._t_go,s.PAUSE:s._t_pause,s.SKINS:s._t_skins,
             s.STATS:s._t_stats,s.CREATOR:s._t_creator}[s.st](evts,mp)
            # v5: stop music when not playing
            if s.st!=s.PLAY and s.st!=s.PAUSE and s.music and pygame.mixer.get_busy():
                s.music.stop()
            s._draw_fade()
            pygame.display.flip()
        save_hs(s.hs);pygame.quit();sys.exit()

    # ── Menu ─────────────────────────────────────────────────────────────
    def _t_menu(s,evts,mp):
        cx=SW//2
        bs=[Btn(cx-130,250,260,55,"Play",GREEN_B),Btn(cx-130,315,260,55,"Skins",PURPLE_B),
            Btn(cx-130,380,260,55,"Stats",CYAN_B),Btn(cx-130,445,260,55,"Level Editor",BLUE_B),
            Btn(cx-130,510,260,55,"Quit",RED_B)]
        for b in bs: b.upd(mp)
        for e in evts:
            if bs[0].hit(e): s.st=s.SEL
            elif bs[1].hit(e): s.st=s.SKINS
            elif bs[2].hit(e): s.st=s.STATS
            elif bs[3].hit(e): s._init_ed()
            elif bs[4].hit(e): pygame.quit();sys.exit()
        s.scr.blit(s.sky.get("meadow"),(0,0))
        f=pygame.font.SysFont("Arial",52,True)
        # v5: animated bouncing title
        t_ms=pygame.time.get_ticks()
        title_y=40+math.sin(t_ms*0.002)*4
        t=f.render("Emoji Platformer",True,(50,50,80))
        sh=f.render("Emoji Platformer",True,BLACK)
        s.scr.blit(sh,(cx-sh.get_width()//2+3,title_y+3));s.scr.blit(t,(cx-t.get_width()//2,title_y))
        sf=pygame.font.SysFont("Arial",20)
        v=sf.render("v7.0  |  24 Characters  |  Character Creator  |  49 Tiles  |  Achievements  |  Parallax Hills!",True,(80,80,120))
        s.scr.blit(v,(cx-v.get_width()//2,100))
        # v5: animated emoji parade with wave pattern
        menu_ems=["😀","⭐","👾","🧱","🚩","💎","🔥","🍄","🦘","🪽","🦇","🌀","🛡️","🧲","🌬️","🎯","🐉","🧊","🧪","🔮"]
        for i,em in enumerate(menu_ems):
            sf2=s.rdb.render(em);x=8+i*48;y=130+math.sin(t_ms*0.003+i*0.7)*10
            # scale bounce
            sc2=1.0+0.15*math.sin(t_ms*0.005+i*0.5)
            ow,oh=sf2.get_size();nw=max(1,int(ow*sc2));nh=max(1,int(oh*sc2))
            sf2=pygame.transform.smoothscale(sf2,(nw,nh))
            s.scr.blit(sf2,(x-nw//2+16,y-nh//2))
        for b in bs: b.draw(s.scr)
        cf=pygame.font.SysFont("Arial",13)
        s.scr.blit(cf.render("Move: Arrows/WASD | Jump: Space | Sprint: Shift | Dash: E | Drop: Down+Jump | P: Pause | M: Mute",True,GRAY),(cx-310,SH-20))

    # ── Character Selection (v7) ───────────────────────────────────────
    def _t_skins(s, evts, mp):
        cx = SW // 2
        back = Btn(20, SH - 60, 120, 45, "Back", DARK_GRAY); back.upd(mp)
        confirm = Btn(cx - 90, SH - 65, 180, 50, "Confirm  ✓", GREEN_B, fs=24); confirm.upd(mp)
        creator_btn = Btn(SW - 220, SH - 60, 195, 45, "Character Creator", PURPLE_B, fs=18); creator_btn.upd(mp)

        # Build full skin list (built-in + custom)
        all_sk = get_all_skins(s.hs)
        n_builtin = len(SKINS)
        cur = s.hs.get("skin", 0)
        # Initialize selection cursor if not set
        if not hasattr(s, '_skin_cursor'):
            s._skin_cursor = cur if isinstance(cur, int) else 0
            if s._skin_cursor >= len(all_sk): s._skin_cursor = 0
        if s._skin_cursor >= len(all_sk): s._skin_cursor = len(all_sk) - 1

        # Grid layout for the character cards (scrollable if many)
        cn = 4; bw = 150; bh = 120; mg = 16
        sx = (SW - (cn * bw + (cn - 1) * mg)) // 2
        sy = 80
        sbs = []
        for i in range(len(all_sk)):
            em = all_sk[i]
            col, row = i % cn, i // cn
            r = pygame.Rect(sx + col * (bw + mg), sy + row * (bh + mg), bw, bh)
            sbs.append((r, i))
        # Scroll offset for when there are many skins
        max_visible_rows = (SH - 220) // (bh + mg)
        total_rows = (len(all_sk) - 1) // cn + 1
        if not hasattr(s, '_skin_scroll'): s._skin_scroll = 0
        # Auto-scroll to keep cursor visible
        cursor_row = s._skin_cursor // cn
        if cursor_row < s._skin_scroll: s._skin_scroll = cursor_row
        if cursor_row >= s._skin_scroll + max_visible_rows: s._skin_scroll = cursor_row - max_visible_rows + 1

        clicked = None
        t_ms = pygame.time.get_ticks()
        for e in evts:
            if back.hit(e):
                s.st = s.MENU; return
            if confirm.hit(e):
                s.hs["skin"] = s._skin_cursor
                save_hs(s.hs); s.st = s.MENU; return
            if creator_btn.hit(e):
                s.st = s.CREATOR; return
            # Scroll wheel
            if e.type == pygame.MOUSEWHEEL:
                s._skin_scroll = max(0, min(s._skin_scroll - e.y, max(0, total_rows - max_visible_rows)))
            # Mouse click on a card
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for r, i in sbs:
                    # Adjust card position by scroll
                    adj_r = r.move(0, -s._skin_scroll * (bh + mg))
                    if adj_r.collidepoint(e.pos):
                        clicked = i
            # Keyboard navigation
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    s._skin_cursor = (s._skin_cursor - 1) % len(all_sk)
                    s.snd.play("collect")
                elif e.key == pygame.K_RIGHT:
                    s._skin_cursor = (s._skin_cursor + 1) % len(all_sk)
                    s.snd.play("collect")
                elif e.key == pygame.K_UP:
                    s._skin_cursor = max(0, s._skin_cursor - cn)
                    s.snd.play("collect")
                elif e.key == pygame.K_DOWN:
                    s._skin_cursor = min(len(all_sk) - 1, s._skin_cursor + cn)
                    s.snd.play("collect")
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    s.hs["skin"] = s._skin_cursor
                    save_hs(s.hs); s.snd.play("win"); s.st = s.MENU; return
                elif e.key == pygame.K_ESCAPE:
                    s.st = s.MENU; return
                elif e.key == pygame.K_c:
                    s.st = s.CREATOR; return
        if clicked is not None:
            s._skin_cursor = clicked
            s.snd.play("collect")
        # ── Draw ──
        s.scr.blit(s.sky.get("meadow"), (0, 0))
        # Title
        tf = pygame.font.SysFont("Arial", 36, True)
        ttl = tf.render("Choose Your Character", True, (50, 50, 80))
        s.scr.blit(ttl, (cx - ttl.get_width() // 2, 10))
        sub = pygame.font.SysFont("Arial", 14)
        hint_text = "Arrows/Click browse  |  Enter confirm  |  C Creator  |  Scroll wheel"
        s.scr.blit(sub.render(hint_text, True, (100, 100, 140)),
                    (cx - sub.render(hint_text, True, (100, 100, 140)).get_width() // 2, 50))

        # "BUILT-IN" and "CUSTOM" section headers
        customs = s.hs.get("custom_skins", [])
        n_custom = sum(1 for c in customs if c is not None)
        count_text = f"{n_builtin} built-in"
        if n_custom > 0: count_text += f"  +  {n_custom} custom"
        hf = pygame.font.SysFont("Arial", 13)
        s.scr.blit(hf.render(count_text, True, GRAY), (sx, 67))

        # Clip region for cards
        clip_rect = pygame.Rect(0, sy - 5, SW, SH - 210)
        s.scr.set_clip(clip_rect)

        sel_em = all_sk[s._skin_cursor]
        sel_color = get_skin_color(sel_em)
        sel_name = get_skin_name(sel_em)
        # For custom skins, use the stored name/color
        if s._skin_cursor >= n_builtin:
            ci = s._skin_cursor - n_builtin
            customs = s.hs.get("custom_skins", [])
            if ci < len(customs) and customs[ci]:
                sel_name = customs[ci].get("name", "Custom")
                sc = customs[ci].get("color", None)
                if sc and isinstance(sc, list) and len(sc) == 3:
                    sel_color = tuple(sc)
                sel_em = customs[ci].get("emoji", sel_em)

        for r, i in sbs:
            em = all_sk[i]
            is_sel = (i == s._skin_cursor)
            is_cur = (i == cur)
            hov = r.collidepoint(mp)
            # Skip if outside visible area
            row_i = i // cn
            if row_i < s._skin_scroll or row_i >= s._skin_scroll + max_visible_rows:
                continue
            # Get name/color for this skin
            if i >= n_builtin:
                ci2 = i - n_builtin
                cskin = customs[ci2] if ci2 < len(customs) else None
                if cskin:
                    card_name = cskin.get("name", "Custom")
                    cc2 = cskin.get("color", None)
                    card_color = tuple(cc2) if cc2 and isinstance(cc2, list) and len(cc2)==3 else (200,150,255)
                    em_display = cskin.get("emoji", em)
                else:
                    continue  # skip empty custom slots
            else:
                card_name = SKIN_NAMES.get(em, "?")
                card_color = SKIN_COLORS.get(em, HILITE)
                em_display = em
            # Adjusted rect for scroll
            ar = r.move(0, -s._skin_scroll * (bh + mg))
            hov = ar.collidepoint(mp)
            # Card background
            if is_sel:
                pulse = int(20 * math.sin(t_ms * 0.006) + 20)
                glow_col = tuple(min(c + pulse, 255) for c in sel_color)
                pygame.draw.rect(s.scr, glow_col, ar.inflate(8, 8), border_radius=16)
                pygame.draw.rect(s.scr, sel_color, ar, 3, border_radius=14)
                card_bg = (50, 50, 75)
            elif hov:
                card_bg = (55, 55, 80)
                pygame.draw.rect(s.scr, WHITE, ar, 2, border_radius=12)
            else:
                card_bg = PANEL_BG
                pygame.draw.rect(s.scr, GRAY, ar, 1, border_radius=12)
            pygame.draw.rect(s.scr, card_bg, ar, border_radius=12)
            # Custom badge
            if i >= n_builtin:
                bf2 = pygame.font.SysFont("Arial", 9, True)
                bt2 = bf2.render("CUSTOM", True, (180, 130, 255))
                s.scr.blit(bt2, (ar.x + 5, ar.y + 4))
            # Emoji with bounce for selected
            sf = s.rdb.render(em_display)
            if is_sel:
                bounce = math.sin(t_ms * 0.005) * 4
                sc2 = 1.0 + 0.1 * math.sin(t_ms * 0.004)
                ow, oh = sf.get_size()
                nw = max(1, int(ow * sc2)); nh = max(1, int(oh * sc2))
                sf = pygame.transform.smoothscale(sf, (nw, nh))
                s.scr.blit(sf, (ar.centerx - nw // 2, ar.y + 12 + bounce - (nh - oh) // 2))
            else:
                s.scr.blit(sf, (ar.centerx - sf.get_width() // 2, ar.y + 14))
            # Name under emoji
            nf = pygame.font.SysFont("Arial", 14, True)
            nt = nf.render(card_name, True, card_color if is_sel else WHITE)
            s.scr.blit(nt, (ar.centerx - nt.get_width() // 2, ar.y + 70))
            # Equipped badge
            if is_cur and not is_sel:
                bf = pygame.font.SysFont("Arial", 11)
                bt = bf.render("Equipped", True, (150, 255, 150))
                s.scr.blit(bt, (ar.centerx - bt.get_width() // 2, ar.bottom - 22))
            elif is_sel and is_cur:
                bf = pygame.font.SysFont("Arial", 11)
                bt = bf.render("✓ Equipped", True, (100, 255, 100))
                s.scr.blit(bt, (ar.centerx - bt.get_width() // 2, ar.bottom - 22))

        s.scr.set_clip(None)  # remove clip

        # ── Bottom panel: large preview + description ──
        panel_y = SH - 140
        preview_panel = pygame.Rect(30, panel_y, SW - 60, 70)
        pp_surf = pygame.Surface((preview_panel.w, preview_panel.h), pygame.SRCALPHA)
        pp_surf.fill((30, 30, 50, 200))
        s.scr.blit(pp_surf, preview_panel.topleft)
        pygame.draw.rect(s.scr, sel_color, preview_panel, 2, border_radius=10)
        # Large emoji preview
        big_em = s.rd.render(sel_em)
        big_sc = 1.3 + 0.08 * math.sin(t_ms * 0.004)
        bow, boh = big_em.get_size()
        bnw = max(1, int(bow * big_sc)); bnh = max(1, int(boh * big_sc))
        big_em = pygame.transform.smoothscale(big_em, (bnw, bnh))
        s.scr.blit(big_em, (preview_panel.x + 15, preview_panel.centery - bnh // 2))
        # Name
        pnf = pygame.font.SysFont("Arial", 24, True)
        pnt = pnf.render(sel_name, True, sel_color)
        s.scr.blit(pnt, (preview_panel.x + 90, panel_y + 6))
        # Description
        sel_desc = get_skin_desc(sel_em)
        if s._skin_cursor >= n_builtin:
            sel_desc = "A custom creation from the Character Creator."
        pdf = pygame.font.SysFont("Arial", 15)
        pdt = pdf.render(sel_desc, True, LGRAY)
        s.scr.blit(pdt, (preview_panel.x + 90, panel_y + 38))
        # Index
        psf = pygame.font.SysFont("Arial", 13)
        idx_text = f"{s._skin_cursor + 1} / {len(all_sk)}"
        pst = psf.render(idx_text, True, GRAY)
        s.scr.blit(pst, (preview_panel.right - pst.get_width() - 15, panel_y + 8))

        # Buttons
        confirm.draw(s.scr)
        creator_btn.draw(s.scr)
        back.draw(s.scr)

    # ── Character Creator (v7) ──────────────────────────────────────────
    def _t_creator(s, evts, mp):
        cx = SW // 2
        t_ms = pygame.time.get_ticks()
        # Initialize creator state
        if not hasattr(s, '_cr_base'): s._cr_base = 0
        if not hasattr(s, '_cr_mod'): s._cr_mod = 0
        if not hasattr(s, '_cr_suf'): s._cr_suf = 0
        if not hasattr(s, '_cr_color'): s._cr_color = (200, 150, 255)
        if not hasattr(s, '_cr_slot'): s._cr_slot = 0
        if not hasattr(s, '_cr_name'): s._cr_name = ""
        if not hasattr(s, '_cr_naming'): s._cr_naming = False
        if not hasattr(s, '_cr_saved_msg'): s._cr_saved_msg = 0  # countdown frames

        # Buttons
        back = Btn(20, SH - 60, 120, 45, "Back", DARK_GRAY); back.upd(mp)
        save_btn = Btn(cx - 200, SH - 60, 180, 48, "Save to Slot", BLUE_B, fs=20); save_btn.upd(mp)
        equip_btn = Btn(cx + 20, SH - 60, 180, 48, "Equip Now", GREEN_B, fs=20); equip_btn.upd(mp)

        # Build the combined emoji
        base_em = CREATOR_BASES[s._cr_base]
        mod_seq = CREATOR_MODS[s._cr_mod][0]
        suf_seq = CREATOR_SUFFIX[s._cr_suf][0]
        # Combine: base + mod_zwj + suffix_zwj  (unique suffixes only)
        if suf_seq and suf_seq != mod_seq:
            combined = base_em + mod_seq + suf_seq
        else:
            combined = base_em + mod_seq

        # ── Events ──
        if s._cr_saved_msg > 0:
            s._cr_saved_msg -= 1

        if s._cr_naming:
            # Text input mode
            for e in evts:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN:
                        s._cr_naming = False
                    elif e.key == pygame.K_ESCAPE:
                        s._cr_naming = False
                        s._cr_name = ""
                    elif e.key == pygame.K_BACKSPACE:
                        s._cr_name = s._cr_name[:-1]
                    elif len(s._cr_name) < 12 and e.unicode.isprintable() and e.unicode:
                        s._cr_name += e.unicode
        else:
            for e in evts:
                if back.hit(e): s.st = s.SKINS; return
                if save_btn.hit(e):
                    # Save to slot
                    customs = s.hs.get("custom_skins", [])
                    display_name = s._cr_name if s._cr_name else f"Custom {s._cr_slot+1}"
                    entry = {"emoji": combined, "name": display_name, "color": list(s._cr_color)}
                    while len(customs) <= s._cr_slot:
                        customs.append(None)
                    customs[s._cr_slot] = entry
                    s.hs["custom_skins"] = customs
                    save_hs(s.hs)
                    s._cr_saved_msg = 120  # 2 second message
                    s.snd.play("win")
                    return
                if equip_btn.hit(e):
                    # Save to a temp slot and equip immediately
                    customs = s.hs.get("custom_skins", [])
                    # find first empty slot or overwrite last
                    all_sk = get_all_skins(s.hs)
                    idx = len(SKINS)
                    # check if this combo already exists
                    found = False
                    for ci, cs in enumerate(customs):
                        if cs and cs["emoji"] == combined:
                            s.hs["skin"] = len(SKINS) + ci
                            save_hs(s.hs); s.snd.play("win")
                            found = True; break
                    if not found:
                        display_name = s._cr_name if s._cr_name else f"Custom"
                        entry = {"emoji": combined, "name": display_name, "color": list(s._cr_color)}
                        customs.append(entry)
                        s.hs["custom_skins"] = customs
                        s.hs["skin"] = len(SKINS) + len(customs) - 1
                        save_hs(s.hs); s.snd.play("win")
                    s.st = s.SKINS; return
                # Click on base grid
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for bi in range(len(CREATOR_BASES)):
                        col, row = bi % 8, bi // 8
                        br = pygame.Rect(30 + col * 58, 100 + row * 58, 52, 52)
                        if br.collidepoint(e.pos):
                            s._cr_base = bi; s.snd.play("collect")
                    # Click on modifier row
                    for mi in range(len(CREATOR_MODS)):
                        mr = pygame.Rect(30 + mi * 58, 230, 52, 52)
                        if mr.collidepoint(e.pos):
                            s._cr_mod = mi; s.snd.play("collect")
                    # Click on suffix row
                    for si in range(len(CREATOR_SUFFIX)):
                        sr2 = pygame.Rect(30 + si * 72, 310, 66, 52)
                        if sr2.collidepoint(e.pos):
                            s._cr_suf = si; s.snd.play("collect")
                    # Click on color swatches
                    color_opts = [(220,60,60),(60,160,60),(60,100,220),(220,180,50),
                                  (180,80,220),(60,200,200),(220,120,50),(200,200,200)]
                    for ci2, cc in enumerate(color_opts):
                        cr = pygame.Rect(30 + ci2 * 42, 395, 36, 36)
                        if cr.collidepoint(e.pos):
                            s._cr_color = cc; s.snd.play("collect")
                    # Slot buttons
                    for si2 in range(MAX_CUSTOM_SKINS):
                        slr = pygame.Rect(30 + si2 * 75, 445, 68, 32)
                        if slr.collidepoint(e.pos):
                            s._cr_slot = si2; s.snd.play("collect")
                    # Name button
                    name_r = pygame.Rect(30, 490, 200, 36)
                    if name_r.collidepoint(e.pos):
                        s._cr_naming = True
                # Keyboard shortcuts
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_TAB:
                        s._cr_naming = True

        # ── Draw ──
        s.scr.blit(s.sky.get("space"), (0, 0))  # space theme for creator

        # Title
        tf = pygame.font.SysFont("Arial", 30, True)
        ttl = tf.render("Character Creator", True, (200, 180, 255))
        s.scr.blit(ttl, (cx - ttl.get_width() // 2, 10))
        sub = pygame.font.SysFont("Arial", 14)
        s.scr.blit(sub.render("Combine emojis with Unicode ZWJ sequences to create unique characters!", True, (160, 150, 200)),
                    (cx - sub.render("Combine emojis with Unicode ZWJ sequences to create unique characters!", True, (160, 150, 200)).get_width() // 2, 45))

        # ── Left column: Pickers ──
        lf = pygame.font.SysFont("Arial", 15, True)

        # Base emoji grid
        s.scr.blit(lf.render("Base Emoji:", True, WHITE), (30, 78))
        for bi in range(len(CREATOR_BASES)):
            col, row = bi % 8, bi // 8
            br = pygame.Rect(30 + col * 58, 100 + row * 58, 52, 52)
            hov = br.collidepoint(mp)
            sel = (bi == s._cr_base)
            bc = (60, 60, 90) if sel else ((50, 50, 75) if hov else (35, 35, 55))
            pygame.draw.rect(s.scr, bc, br, border_radius=8)
            if sel: pygame.draw.rect(s.scr, s._cr_color, br, 2, border_radius=8)
            elif hov: pygame.draw.rect(s.scr, GRAY, br, 1, border_radius=8)
            esf = s.rds.render(CREATOR_BASES[bi])
            s.scr.blit(esf, (br.centerx - esf.get_width()//2, br.centery - esf.get_height()//2))

        # Modifier row
        s.scr.blit(lf.render("Modifier (ZWJ):", True, WHITE), (30, 210))
        for mi in range(len(CREATOR_MODS)):
            mr = pygame.Rect(30 + mi * 58, 230, 52, 52)
            hov = mr.collidepoint(mp)
            sel = (mi == s._cr_mod)
            bc = (60, 60, 90) if sel else ((50, 50, 75) if hov else (35, 35, 55))
            pygame.draw.rect(s.scr, bc, mr, border_radius=8)
            if sel: pygame.draw.rect(s.scr, s._cr_color, mr, 2, border_radius=8)
            elif hov: pygame.draw.rect(s.scr, GRAY, mr, 1, border_radius=8)
            mod_label = CREATOR_MODS[mi][1]
            if mi == 0:
                esf = s.rds.render("✕")
            else:
                # render the base+mod combo small to show effect
                combo = CREATOR_BASES[s._cr_base] + CREATOR_MODS[mi][0]
                esf = s.rds.render(combo[:4] if len(combo) <= 8 else CREATOR_BASES[s._cr_base])
            s.scr.blit(esf, (mr.centerx - esf.get_width()//2, mr.y + 4))
            mlf = pygame.font.SysFont("Arial", 10)
            ml = mlf.render(mod_label, True, LGRAY if not sel else WHITE)
            s.scr.blit(ml, (mr.centerx - ml.get_width()//2, mr.bottom - 14))

        # Suffix row
        s.scr.blit(lf.render("Suffix:", True, WHITE), (30, 290))
        for si in range(len(CREATOR_SUFFIX)):
            sr2 = pygame.Rect(30 + si * 72, 310, 66, 52)
            hov = sr2.collidepoint(mp)
            sel = (si == s._cr_suf)
            bc = (60, 60, 90) if sel else ((50, 50, 75) if hov else (35, 35, 55))
            pygame.draw.rect(s.scr, bc, sr2, border_radius=8)
            if sel: pygame.draw.rect(s.scr, s._cr_color, sr2, 2, border_radius=8)
            elif hov: pygame.draw.rect(s.scr, GRAY, sr2, 1, border_radius=8)
            suf_label = CREATOR_SUFFIX[si][1]
            if si == 0:
                esf = s.rds.render("✕")
            else:
                esf = s.rds.render(CREATOR_BASES[s._cr_base])
            s.scr.blit(esf, (sr2.centerx - esf.get_width()//2, sr2.y + 4))
            slf = pygame.font.SysFont("Arial", 10)
            sl = slf.render(suf_label, True, LGRAY if not sel else WHITE)
            s.scr.blit(sl, (sr2.centerx - sl.get_width()//2, sr2.bottom - 14))

        # Color swatches
        s.scr.blit(lf.render("Color Theme:", True, WHITE), (30, 375))
        color_opts = [(220,60,60),(60,160,60),(60,100,220),(220,180,50),
                      (180,80,220),(60,200,200),(220,120,50),(200,200,200)]
        for ci2, cc in enumerate(color_opts):
            cr = pygame.Rect(30 + ci2 * 42, 395, 36, 36)
            pygame.draw.rect(s.scr, cc, cr, border_radius=6)
            if cc == s._cr_color:
                pygame.draw.rect(s.scr, WHITE, cr, 3, border_radius=6)
            else:
                pygame.draw.rect(s.scr, DARK_GRAY, cr, 1, border_radius=6)

        # Save slot selector
        s.scr.blit(lf.render("Save Slot:", True, WHITE), (30, 427))
        customs = s.hs.get("custom_skins", [])
        for si2 in range(MAX_CUSTOM_SKINS):
            slr = pygame.Rect(30 + si2 * 75, 445, 68, 32)
            has_skin = si2 < len(customs) and customs[si2] is not None
            sel = (si2 == s._cr_slot)
            bc = (70, 70, 100) if sel else ((45, 45, 65) if has_skin else (30, 30, 45))
            pygame.draw.rect(s.scr, bc, slr, border_radius=6)
            if sel: pygame.draw.rect(s.scr, HILITE, slr, 2, border_radius=6)
            elif has_skin: pygame.draw.rect(s.scr, GRAY, slr, 1, border_radius=6)
            slf = pygame.font.SysFont("Arial", 12, True)
            if has_skin:
                slot_name = customs[si2].get("name", f"#{si2+1}")[:6]
                slt = slf.render(slot_name, True, WHITE)
            else:
                slt = slf.render(f"Empty {si2+1}", True, DARK_GRAY)
            s.scr.blit(slt, (slr.centerx - slt.get_width()//2, slr.centery - slt.get_height()//2))

        # Name input
        s.scr.blit(lf.render("Name (click to edit):", True, WHITE), (30, 482))
        name_r = pygame.Rect(30, 500, 200, 36)
        nc = (70, 70, 100) if s._cr_naming else (40, 40, 60)
        pygame.draw.rect(s.scr, nc, name_r, border_radius=6)
        pygame.draw.rect(s.scr, HILITE if s._cr_naming else GRAY, name_r, 2, border_radius=6)
        nf = pygame.font.SysFont("Arial", 18)
        display_name = s._cr_name if s._cr_name else "Unnamed"
        if s._cr_naming and (t_ms // 500) % 2 == 0:
            display_name += "|"
        nt = nf.render(display_name, True, WHITE)
        s.scr.blit(nt, (name_r.x + 10, name_r.centery - nt.get_height()//2))

        # ── Right column: Live Preview ──
        preview_x = 520
        preview_panel = pygame.Rect(preview_x, 70, SW - preview_x - 30, SH - 150)
        pp = pygame.Surface((preview_panel.w, preview_panel.h), pygame.SRCALPHA)
        pp.fill((20, 20, 40, 220))
        s.scr.blit(pp, preview_panel.topleft)
        pygame.draw.rect(s.scr, s._cr_color, preview_panel, 2, border_radius=12)

        # "LIVE PREVIEW" header
        pvf = pygame.font.SysFont("Arial", 14, True)
        pvt = pvf.render("LIVE PREVIEW", True, s._cr_color)
        s.scr.blit(pvt, (preview_panel.centerx - pvt.get_width()//2, preview_panel.y + 10))

        # Big combined emoji - render it large
        big_sf = s.rdb.render(combined)
        # animated bounce
        bsc = 2.0 + 0.2 * math.sin(t_ms * 0.003)
        bow, boh = big_sf.get_size()
        bnw = max(1, int(bow * bsc)); bnh = max(1, int(boh * bsc))
        big_sf = pygame.transform.smoothscale(big_sf, (bnw, bnh))
        bounce_y = math.sin(t_ms * 0.004) * 6
        s.scr.blit(big_sf, (preview_panel.centerx - bnw//2, preview_panel.y + 45 + bounce_y - (bnh - boh)//2))

        # Glow effect behind emoji
        glow_surf = pygame.Surface((bnw + 40, bnh + 40), pygame.SRCALPHA)
        ga = int(40 + 25 * math.sin(t_ms * 0.005))
        pygame.draw.ellipse(glow_surf, (*s._cr_color, ga), (0, 0, bnw + 40, bnh + 40))
        s.scr.blit(glow_surf, (preview_panel.centerx - (bnw+40)//2, preview_panel.y + 45 + bounce_y - (bnh - boh)//2 - 20))

        # Combined string display (raw unicode info)
        raw_y = preview_panel.y + 45 + bnh + 20
        irf = pygame.font.SysFont("Arial", 12)
        # Show the raw sequence
        raw_display = combined.replace("\u200d", "+").replace("\ufe0f", "")
        if len(raw_display) > 30: raw_display = raw_display[:30] + "..."
        irt = irf.render(f"Sequence: {raw_display}", True, (150, 150, 180))
        s.scr.blit(irt, (preview_panel.x + 15, raw_y))

        # Character count
        char_info = irf.render(f"Codepoints: {len(combined)}", True, (120, 120, 150))
        s.scr.blit(char_info, (preview_panel.x + 15, raw_y + 20))

        # Show base name + modifiers
        mod_name = CREATOR_MODS[s._cr_mod][1]
        suf_name = CREATOR_SUFFIX[s._cr_suf][1]
        combo_name = CREATOR_BASES[s._cr_base]
        if mod_name != "None": combo_name += f" + {mod_name}"
        if suf_name != "None" and suf_name != mod_name: combo_name += f" + {suf_name}"
        cnf = pygame.font.SysFont("Arial", 16, True)
        cnt = cnf.render(combo_name, True, WHITE)
        s.scr.blit(cnt, (preview_panel.centerx - cnt.get_width()//2, raw_y + 45))

        # Saved confirmation message
        if s._cr_saved_msg > 0:
            alpha = min(255, s._cr_saved_msg * 4)
            msg_f = pygame.font.SysFont("Arial", 22, True)
            msg = msg_f.render("Saved!", True, (100, 255, 100))
            msg.set_alpha(alpha)
            s.scr.blit(msg, (preview_panel.centerx - msg.get_width()//2, raw_y + 80))

        # Tips at bottom of preview
        tips = [
            "ZWJ = Zero Width Joiner (U+200D)",
            "Combines two emojis into one glyph",
            "Results vary by system font support",
            "Tab to name your creation!",
        ]
        tip_y = raw_y + 110
        tipf = pygame.font.SysFont("Arial", 11)
        for tip in tips:
            tt = tipf.render(tip, True, (110, 110, 140))
            s.scr.blit(tt, (preview_panel.x + 15, tip_y))
            tip_y += 16

        # Buttons
        back.draw(s.scr)
        save_btn.draw(s.scr)
        equip_btn.draw(s.scr)

        # Naming cursor overlay
        if s._cr_naming:
            overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            s.scr.blit(overlay, (0, 0))
            # Name input dialog
            dlg = pygame.Rect(cx - 160, SH//2 - 60, 320, 120)
            pygame.draw.rect(s.scr, (30, 30, 50), dlg, border_radius=12)
            pygame.draw.rect(s.scr, HILITE, dlg, 2, border_radius=12)
            df = pygame.font.SysFont("Arial", 22, True)
            dt = df.render("Name Your Character", True, WHITE)
            s.scr.blit(dt, (dlg.centerx - dt.get_width()//2, dlg.y + 15))
            # Text field
            tfr = pygame.Rect(dlg.x + 20, dlg.y + 50, dlg.w - 40, 36)
            pygame.draw.rect(s.scr, (50, 50, 70), tfr, border_radius=6)
            pygame.draw.rect(s.scr, HILITE, tfr, 2, border_radius=6)
            it = df.render(s._cr_name + ("|" if (t_ms//500)%2==0 else ""), True, WHITE)
            s.scr.blit(it, (tfr.x + 10, tfr.centery - it.get_height()//2))
            hf = pygame.font.SysFont("Arial", 13)
            ht = hf.render("Enter to confirm  |  Esc to cancel", True, GRAY)
            s.scr.blit(ht, (dlg.centerx - ht.get_width()//2, dlg.bottom - 22))

    # ── Stats ────────────────────────────────────────────────────────────
    def _t_stats(s,evts,mp):
        cx=SW//2;back=Btn(20,SH-60,120,45,"Back",DARK_GRAY);back.upd(mp)
        for e in evts:
            if back.hit(e): s.st=s.MENU
        s.scr.blit(s.sky.get("meadow"),(0,0))
        f=pygame.font.SysFont("Arial",34,True)
        s.scr.blit(f.render("Game Statistics",True,(50,50,80)),(cx-f.render("Game Statistics",True,(50,50,80)).get_width()//2,25))
        y=90;sf=pygame.font.SysFont("Arial",22,True);sl=pygame.font.SysFont("Arial",20)
        # Total stars
        ts=sum(s.hs.get(lv.name+"_stars",0) for lv in s.builtins)
        ms=len(s.builtins)*3
        s.scr.blit(sf.render(f"Total Stars: {ts}/{ms}  {'⭐'*ts}{'☆'*(ms-ts)}",True,HILITE),(80,y));y+=40
        # Best scores
        s.scr.blit(sf.render("Best Scores:",True,WHITE),(80,y));y+=30
        for lv in s.builtins:
            sc=s.hs.get(lv.name,0);st=s.hs.get(lv.name+"_stars",0)
            tm=s.hs.get(lv.name+"_time",None)
            tstr=f"  {tm:.1f}s" if tm else "  --"
            s.scr.blit(sl.render(f"  {lv.name}: {sc} pts  {'⭐'*st}{'☆'*(3-st)}  {tstr}",True,LGRAY),(80,y));y+=26
        y+=20
        # Levels unlocked
        ul=s._unlocked()
        s.scr.blit(sf.render(f"Levels Unlocked: {ul}/{len(s.levels)}",True,WHITE),(80,y));y+=35
        # Reset button
        rb=Btn(cx-80,y,160,45,"Reset All Data",RED_B,fs=18);rb.upd(mp)
        for e in evts:
            if rb.hit(e): s.hs={};save_hs(s.hs)
        rb.draw(s.scr)
        back.draw(s.scr)

    # ── Level Select ─────────────────────────────────────────────────────
    def _t_sel(s,evts,mp):
        back=Btn(20,SH-60,120,45,"Back",DARK_GRAY);back.upd(mp)
        cn=3;bw=260;bh=70;mg=15;sx=(SW-(cn*bw+(cn-1)*mg))//2
        bs=[]
        for i,lv in enumerate(s.levels):
            col,row=i%cn,i//cn
            r=pygame.Rect(sx+col*(bw+mg),75+row*(bh+mg),bw,bh)
            bs.append((r,i))
        for r,_ in bs: pass
        for e in evts:
            if back.hit(e): s.st=s.MENU
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                for r,i in bs:
                    if r.collidepoint(e.pos) and i<s._unlocked(): s._start(i)
        s.scr.blit(s.sky.get("meadow"),(0,0))
        f=pygame.font.SysFont("Arial",34,True)
        s.scr.blit(f.render("Select Level",True,(50,50,80)),(SW//2-f.render("Select Level",True,(50,50,80)).get_width()//2,20))
        for r,i in bs:
            lv=s.levels[i];hov=r.collidepoint(mp);locked=i>=s._unlocked()
            if locked: col=(50,50,50)
            else: col=tuple(min(x+30,255) for x in BLUE_B) if hov else BLUE_B
            pygame.draw.rect(s.scr,col,r,border_radius=10)
            pygame.draw.rect(s.scr,WHITE if hov and not locked else GRAY,r,2,border_radius=10)
            nf=pygame.font.SysFont("Arial",17,True)
            label=f"Lv {i+1}: {lv.name}" if not locked else f"Lv {i+1}: 🔒 Locked"
            s.scr.blit(nf.render(label,True,WHITE if not locked else DARK_GRAY),(r.x+10,r.y+8))
            sf2=pygame.font.SysFont("Arial",12)
            if not locked:
                hs=s.hs.get(lv.name,0);st=s.hs.get(lv.name+"_stars",0)
                tm=s.hs.get(lv.name+"_time",None)
                tstr=f"Best: {tm:.1f}s" if tm else ""
                # v6: show grade on level card
                grade_str = ""
                best_score = s.hs.get(lv.name, 0)
                if best_score > 0 and tm:
                    # rough grade from stored time
                    if tm < 30: grade_str = " S"
                    elif tm < 60: grade_str = " A"
                    elif tm < 90: grade_str = " B"
                    else: grade_str = " C"
                info = f"Theme: {lv.theme}  |  Best: {hs}  {'⭐'*st}{'☆'*(3-st)}  {tstr}{grade_str}"
                s.scr.blit(sf2.render(info,True,LGRAY),(r.x+10,r.y+32))
                # v6: grade badge
                if grade_str:
                    gcol = (255,215,0) if grade_str.strip()=="S" else (100,255,100) if grade_str.strip()=="A" else (100,200,255) if grade_str.strip()=="B" else (200,200,200)
                    gf=pygame.font.SysFont("Arial",18,True)
                    gs=gf.render(grade_str.strip(),True,gcol)
                    s.scr.blit(gs,(r.x+bw-65,r.y+30))
                # Mini preview
                _draw_minimap(s.scr,lv,r.x+bw-60,r.y+5,50,30,1)
            else:
                s.scr.blit(sf2.render(f"Complete Lv {i} to unlock",True,DARK_GRAY),(r.x+10,r.y+35))
        back.draw(s.scr)

    # ── Playing ──────────────────────────────────────────────────────────
    def _t_play(s,evts,mp):
        keys=pygame.key.get_pressed()
        for e in evts:
            if e.type==pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w):
                    # v5: drop-through if holding down
                    drop = keys[pygame.K_DOWN] or keys[pygame.K_s]
                    res=s.pl.try_jump(drop=drop)
                    if res=="drop": s.snd.play("drop");s.pl.vy=2
                    elif res=="djump": s.snd.play("djump");s._fx(s.pl.x,s.pl.y,"✨",4)
                    elif res=="jump": s.snd.play("jump")
                    elif res=="wjump": s.snd.play("wjump");s._fx(s.pl.x+(0 if s.pl.right else s.pl.w),s.pl.y,"💨",4)
                elif e.key==pygame.K_e:
                    if s.pl.try_dash():
                        s.snd.play("dash");s._fx(s.pl.x,s.pl.y+s.pl.h//2,"💨",6)
                elif e.key==pygame.K_r: s._start(s.li)
                elif e.key in (pygame.K_ESCAPE,pygame.K_p): s.pstate=s.PLAY;s.st=s.PAUSE
                elif e.key==pygame.K_m: s.snd.on=not s.snd.on
                elif e.key==pygame.K_n:
                    # v5: toggle music
                    s.music_on=not s.music_on
                    if s.music_on and s.music and not pygame.mixer.get_busy():
                        s.music.play(loops=-1)
                    elif not s.music_on and s.music:
                        s.music.stop()
            if e.type==pygame.KEYUP:
                if e.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w):
                    s.pl.release_jump()

        solids=s.lv.solid_rects()
        convs=s.lv.conveyors()
        winds=s.lv.wind_zones()
        ice_r=s.lv.ice_rects()
        water_r=s.lv.water_rects()
        s.pl.update(keys,solids,convs,winds,ice_r,water_r)
        # update movers
        for mp2 in s.mps: mp2.update()
        # carry player on movers
        pr=s.pl.rect()
        for mp2 in s.mps:
            mr=mp2.rect()
            if pr:
                feet=pygame.Rect(s.pl.x,s.pl.y+s.pl.h,s.pl.w,4)
                if feet.colliderect(mr) and s.pl.vy>=0:
                    dx,dy=mp2.delta();s.pl.x+=dx;s.pl.y+=dy
        # crumble
        for cp in s.cps:
            cp.update()
            if not cp.gone and cp.t==0:
                cr=cp.rect()
                if cr:
                    feet=pygame.Rect(s.pl.x,s.pl.y+s.pl.h,s.pl.w,4)
                    if feet.colliderect(cr) and s.pl.vy>=0 and s.pl.ground: cp.trigger()
        # bounce
        if s.pl.alive and s.pl.vy>0:
            feet=pygame.Rect(s.pl.x,s.pl.y+s.pl.h-2,s.pl.w,6)
            for bp in s.lv.bounce_pads():
                if feet.colliderect(bp): s.pl.bounce();s.snd.play("bounce");s._fx(bp.centerx,bp.top,"⚡",6);break
        # v6: spring launcher
        if s.pl.alive and s.pl.vy>0:
            feet=pygame.Rect(s.pl.x,s.pl.y+s.pl.h-2,s.pl.w,6)
            for sp in s.lv.springs():
                if feet.colliderect(sp):
                    s.pl.vy=SPRING_F;s.pl.ground=False;s.pl.squash=0.5
                    s.snd.play("spring");s._fx(sp.centerx,sp.top,"🎪",10);s._ft(sp.centerx,sp.top-15,"SPRING!",(255,200,50))
                    s.shake.trigger(4,8)
                    if "spring_king" not in s.ach_granted: s._grant_ach("spring_king")
                    break
        # v6: landing dust burst
        if s.pl.alive and s.pl.landed_this_frame:
            intensity = min(abs(s.pl.land_vy) / 5.0, 3.0)
            n = int(3 + intensity * 4)
            for _ in range(n):
                s.dust_parts.append(Part(
                    s.pl.x + s.pl.w//2 + random.uniform(-s.pl.w//3, s.pl.w//3),
                    s.pl.y + s.pl.h,
                    random.choice(["💨","☁️"]),
                    random.uniform(-2, 2) * intensity,
                    random.uniform(-2, -0.5) * intensity,
                    random.randint(15, 30)
                ))
        # v6: cannon logic
        if s.pl.alive:
            # init cannon cooldowns if needed
            if not s.cannons_cd:
                s.cannons_cd = [[x, y, dx, 0] for x, y, dx, cd in s.lv.cannons()]
            for i, (cx, cy, cdx, _) in enumerate(s.cannons_cd):
                if s.cannons_cd[i][3] > 0:
                    s.cannons_cd[i][3] -= 1
                    continue
                # check if player is in range (within 6 tiles horizontally)
                dx_to_pl = s.pl.x - cx
                if abs(dx_to_pl) < TS * 8 and ((cdx > 0 and dx_to_pl > 0) or (cdx < 0 and dx_to_pl < 0)):
                    s.cannonballs.append(Cannonball(cx + TS//2 - 4, cy + TS//2 - 4, cdx))
                    s.cannons_cd[i][3] = CANNON_CD
                    s.snd.play("cannon")
                    s._fx(cx + TS//2, cy + TS//2, "💨", 4)
        for cb in s.cannonballs: cb.update(s.lv.width, solids)
        s.cannonballs=[f for f in s.cannonballs if f.alive]
        # v6: coin magnet attraction (coins slide toward player)
        if s.pl.has_magnet and s.pl.alive:
            pr2 = s.pl.rect()
            pcx, pcy = pr2.centerx, pr2.centery
            for tt, r, c in s.lv.magnet_coins():
                if (r, c) in s.collected: continue
                ccx, ccy = c*TS + TS//2, r*TS + TS//2
                dist = math.sqrt((pcx - ccx)**2 + (pcy - ccy)**2)
                if dist < TS * 5 and dist > 5:
                    # Move coin toward player visually (modify tile position won't work,
                    # so we handle collection at increased range in the collectibles section)
                    speed = 3.0 * (1 - dist / (TS * 5))
                    # attract particle line effect
                    if random.random() < 0.3:
                        s.parts.append(Part(ccx + random.uniform(-4,4), ccy + random.uniform(-4,4),
                            "✨", (pcx-ccx)/dist * speed * 2, (pcy-ccy)/dist * speed * 2, 12))
            # Also expand collection range significantly when magnet active
        # camera with look-ahead
        s.cam.update(s.pl.x+s.pl.w//2,s.pl.y+s.pl.h//2,s.pl.vx,s.pl.vy,s.lv.width,s.lv.height)
        for en in s.ens: en.update(solids,s.lv.width, s.pl)
        # dragon fireballs
        for en in s.ens:
            if en.alive and en.tt==41 and hasattr(en,'shoot_cd') and en.shoot_cd<=0:
                dx = 1 if en.vx>0 else -1
                s.fireballs.append(Fireball(en.x+en.w//2-4,en.y+en.h//2-4,dx*3.5))
                en.shoot_cd=120;s.snd.play("fireball")
        for fb in s.fireballs: fb.update(s.lv.width)
        s.fireballs=[f for f in s.fireballs if f.alive]
        pr=s.pl.rect()
        # enemies
        for en in s.ens:
            if not en.alive: continue
            if pr.colliderect(en.rect()):
                if s.pl.vy>0 and s.pl.y+s.pl.h-8<en.y+en.h//2:
                    en.alive=False;s.pl.vy=JUMP_FORCE*0.6;s.pl.score+=50
                    s.snd.play("stomp");s._fx(en.x,en.y,"💥",8);s._ft(en.x,en.y-10,"+50")
                    s._add_combo();s.pl.squash=0.6
                    # v5: poof animation on enemy death
                    s.poofs.append(PoofAnim(en.x,en.y,en.em))
                    # v6: first blood achievement
                    if "first_blood" not in s.ach_granted: s._grant_ach("first_blood")
                    # stomp combo variety text
                    if s.combo>=5: s._ft(en.x,en.y-30,"AMAZING!",(255,100,255))
                    elif s.combo>=3: s._ft(en.x,en.y-30,"Great!",(255,200,50))
                    elif s.combo>=2: s._ft(en.x,en.y-30,"Nice!",(100,255,150))
                elif s.pl.hurt():
                    s.snd.play("hurt");s.snd.play("death_j")
                    # explosion particles on death
                    for _ in range(15):
                        s.parts.append(Part(s.pl.x+s.pl.w//2,s.pl.y+s.pl.h//2,
                            random.choice(["💥","✨","🔥","💨"]),
                            random.uniform(-5,5),random.uniform(-6,2),random.randint(25,50)))
                    s.danims.append(DeathAnim(s.pl.x,s.pl.y,s.pl.em))
                    s.shake.trigger(8,16);s.deaths+=1
                    if s.pl.lives<=0: s.st=s.GO
                    else: s.pl.to_cp()
        # fireball + cannonball hits
        if s.pl.alive:
            pr=s.pl.rect()
            for fb in s.fireballs:
                if fb.alive and pr.colliderect(fb.rect()):
                    fb.alive=False
                    if s.pl.hurt():
                        s.snd.play("hurt");s.snd.play("death_j")
                        for _ in range(12):
                            s.parts.append(Part(s.pl.x+s.pl.w//2,s.pl.y+s.pl.h//2,
                                random.choice(["💥","🔥"]),
                                random.uniform(-4,4),random.uniform(-5,1),random.randint(20,40)))
                        s.danims.append(DeathAnim(s.pl.x,s.pl.y,s.pl.em))
                        s.shake.trigger(6,12);s.deaths+=1
                        if s.pl.lives<=0: s.st=s.GO
                        else: s.pl.to_cp()
                    else:
                        s._fx(fb.x,fb.y,"🔥",6)
                    break
            # v6: cannonball hits
            for cb in s.cannonballs:
                if cb.alive and pr.colliderect(cb.rect()):
                    cb.alive=False
                    if s.pl.hurt():
                        s.snd.play("hurt");s.snd.play("death_j")
                        for _ in range(12):
                            s.parts.append(Part(s.pl.x+s.pl.w//2,s.pl.y+s.pl.h//2,
                                random.choice(["💥","💣"]),
                                random.uniform(-4,4),random.uniform(-5,1),random.randint(20,40)))
                        s.danims.append(DeathAnim(s.pl.x,s.pl.y,s.pl.em))
                        s.shake.trigger(8,14);s.deaths+=1
                        if s.pl.lives<=0: s.st=s.GO
                        else: s.pl.to_cp()
                    else:
                        s._fx(cb.x,cb.y,"💥",8)
                    break
        # trap tiles (reveal when player is near)
        if s.pl.alive:
            pr=s.pl.rect()
            for tr,tc in s.lv.traps():
                if (tr,tc) in s.triggered_traps: continue
                trap_cx=tc*TS+TS//2;trap_cy=tr*TS+TS//2
                dist=math.sqrt((s.pl.x+s.pl.w//2-trap_cx)**2+(s.pl.y+s.pl.h//2-trap_cy)**2)
                if dist<TRAP_RANGE:
                    s.triggered_traps.add((tr,tc))
                    s.snd.play("trap");s.shake.trigger(4,8)
                    s._fx(tc*TS,tr*TS,"🪤",8)
        # door opening
        if s.pl.has_key:
            pr=s.pl.rect()
            for dr,dc in s.lv.doors():
                if (dr,dc) not in s.opened_doors:
                    dr_rect=pygame.Rect(dc*TS,dr*TS,TS,TS)
                    if pr.colliderect(dr_rect):
                        s.opened_doors.add((dr,dc))
                        s.lv.set(dr,dc,0)  # remove door tile
                        s.pl.has_key=False
                        s.snd.play("door");s.snd.play("key")
                        s._fx(dc*TS,dr*TS,"🚪",10)
                        s._ft(dc*TS,dr*TS-15,"Door Opened!",(100,255,200))
                        # rebuild solid rects for next frame
                        break
        # collectibles
        for tt,r,c in s.lv.collectibles():
            if (r,c) in s.collected: continue
            ir=pygame.Rect(c*TS,r*TS,TS,TS)
            # magnet: expand collection range
            collect_r=ir
            if s.pl.has_magnet and tt in (5,6,13,27,42):
                collect_r=ir.inflate(TS*4,TS*4)  # v6: bigger magnet range
            if pr.colliderect(collect_r):
                s.collected.add((r,c));s.lv.clear_col(r,c)
                pts={5:100,13:200,6:250,27:50,42:500}.get(tt,0)
                # combo multiplier
                mult=max(1,s.combo) if s.combo>1 else 1
                pts*=mult;s.pl.score+=pts
                s.snd.play("collect");s._add_combo()
                if tt==14: s.pl.lives=min(s.pl.lives+1,9);s._fx(c*TS,r*TS,HEART,8);s._ft(c*TS,r*TS-10,"+1 Life",(255,100,100))
                elif tt==38: s.pl.has_key=True;s.snd.play("key");s._fx(c*TS,r*TS,"🔑",10);s._ft(c*TS,r*TS-10,"Key!",(255,220,100))
                elif tt==40: s.pl.potion_t=POTION_T;s.snd.play("potion");s._fx(c*TS,r*TS,"🧪",10);s._ft(c*TS,r*TS-10,"Invincible!",(255,200,255))
                elif tt==42: s.snd.play("crystal");s._fx(c*TS,r*TS,"🔮",10);s._ft(c*TS,r*TS-10,f"+{pts*s.pl.mult}",(200,150,255))
                elif tt==23: s.pl.has_dj=True;s.pl.djump=True;s._fx(c*TS,r*TS,"✨",10);s._ft(c*TS,r*TS-10,"Double Jump!",(150,200,255))
                elif tt==31: s.pl.has_shield=True;s.snd.play("shield");s._fx(c*TS,r*TS,"🛡️",8);s._ft(c*TS,r*TS-10,"Shield!",(100,200,255))
                elif tt==32: s.pl.has_magnet=True;s.snd.play("magnet");s._fx(c*TS,r*TS,"🧲",8);s._ft(c*TS,r*TS-10,"Magnet!",(200,200,100))
                elif tt==34: s.pl.mult=2;s.pl.mult_t=600;s._fx(c*TS,r*TS,"🎯",10);s._ft(c*TS,r*TS-10,"Score x2!",(255,200,50))
                else:
                    em="⭐" if tt in (5,13,27) else "💎"
                    s._fx(c*TS,r*TS,em,5)
                    txt=f"+{pts}" + (f" x{mult}" if mult>1 else "")
                    s._ft(c*TS,r*TS-10,txt)
        # checkpoints
        for cr,cc in s.lv.checkpoints():
            if (cr,cc) not in s.activated_cp:
                ckr=pygame.Rect(cc*TS,cr*TS,TS,TS)
                if pr.colliderect(ckr):
                    s.activated_cp.add((cr,cc));s.pl.checkpoint(cc*TS,cr*TS-s.pl.h)
                    s.snd.play("checkpoint");s._ft(cc*TS,cr*TS-15,"Checkpoint!",(100,255,100))
        # teleporters (with cooldown)
        if s.tp_cooldown>0: s.tp_cooldown-=1
        tps=s.lv.teleporters()
        if len(tps)>=2 and s.pl.alive and s.tp_cooldown<=0:
            for i in range(0,len(tps)-1,2):
                t1=pygame.Rect(tps[i][0],tps[i][1],TS,TS)
                t2=pygame.Rect(tps[i+1][0],tps[i+1][1],TS,TS)
                if pr.colliderect(t1):
                    s.pl.x=tps[i+1][0];s.pl.y=tps[i+1][1]-s.pl.h+4
                    s.tp_cooldown=30;s.snd.play("teleport")
                    s._fx(*tps[i],"🌀",10);s._fx(*tps[i+1],"🌀",10);break
                elif pr.colliderect(t2):
                    s.pl.x=tps[i][0];s.pl.y=tps[i][1]-s.pl.h+4
                    s.tp_cooldown=30;s.snd.play("teleport")
                    s._fx(*tps[i+1],"🌀",10);s._fx(*tps[i],"🌀",10);break
        # hazards (water just slows, traps only hurt if triggered)
        if s.pl.alive:
            pr=s.pl.rect()
            for hr in s.lv.hazards():
                if pr.colliderect(hr):
                    # check if this is water (already handled by water_rects) - skip
                    # water hazard: only hurt if no ground below (drowning in deep water)
                    hcol=hr.x//TS;hrow=hr.y//TS
                    tile_below=s.lv.get(hrow+1,hcol) if hrow+1<s.lv.rows else 0
                    is_water = (s.lv.tiles[min(hr.y//TS, s.lv.rows-1)][hr.x//TS] == 36)
                    is_trap = (s.lv.tiles[min(hr.y//TS, s.lv.rows-1)][hr.x//TS] == 43)
                    if is_water: continue  # water handled by water_rects physics
                    if is_trap and (hrow,hcol) not in s.triggered_traps: continue
                    if s.pl.hurt():
                        s.snd.play("hurt");s.snd.play("death_j")
                        for _ in range(10):
                            s.parts.append(Part(s.pl.x+s.pl.w//2,s.pl.y+s.pl.h//2,
                                random.choice(["💥","🔥","✨"]),
                                random.uniform(-4,4),random.uniform(-5,1),random.randint(20,40)))
                        s.danims.append(DeathAnim(s.pl.x,s.pl.y,s.pl.em))
                        s.shake.trigger();s.deaths+=1
                        if s.pl.lives<=0: s.st=s.GO
                        else: s.pl.to_cp()
                    break
        # goal
        goal=s.lv.goal()
        if goal and pr.colliderect(goal):
            s.snd.play("win")
            s.elapsed=_time.time()-s.start_time
            # time bonus
            tb=max(0,int(TIME_BONUS_MAX*(1-s.elapsed/120)))  # 120s par
            s.pl.score+=tb
            # save
            key=s.lv.name;old=s.hs.get(key,0)
            if s.pl.score>old: s.hs[key]=s.pl.score
            os2=s.hs.get(key+"_stars",0);ns=s._stars()
            if ns>os2: s.hs[key+"_stars"]=ns
            ot=s.hs.get(key+"_time",999)
            if s.elapsed<ot: s.hs[key+"_time"]=round(s.elapsed,1)
            # v6: win achievements
            if s.elapsed < 30 and "speed_run" not in s.ach_granted:
                s._grant_ach("speed_run")
            if s.totcol > 0 and len(s.collected) >= s.totcol and "coin_master" not in s.ach_granted:
                s._grant_ach("coin_master")
            if s.deaths == 0 and "no_death" not in s.ach_granted:
                s._grant_ach("no_death")
            # unlock next
            if s.li+1>=s.hs.get("unlocked",1):
                s.hs["unlocked"]=min(s.li+2,len(s.levels))
            save_hs(s.hs);s.st=s.WIN
        # fall
        if s.pl.y>s.lv.height+100:
            s.pl.lives-=1;s.deaths+=1;s.snd.play("hurt");s.shake.trigger()
            if s.pl.lives<=0: s.st=s.GO
            else: s.pl.to_cp()
        # combo timer
        if s.combo_t>0: s.combo_t-=1
        else: s.combo=0
        # v5: low-health heartbeat
        if s.pl.alive and s.pl.lives==1:
            s.hb_t+=1
            if s.hb_t>=45: s.hb_t=0;s.snd.play("hb")
        else: s.hb_t=0
        # update FX
        s.shake.update();s.parts=[p for p in s.parts if p.update()]
        s.ftxts=[f for f in s.ftxts if f.update()]
        s.danims=[d for d in s.danims if d.update()]
        s.dust_parts=[p for p in s.dust_parts if p.update()]
        s.poofs=[p for p in s.poofs if p.update()]  # v5
        s.ach_queue=[a for a in s.ach_queue if a.update()]  # v6
        s.clouds.update()
        # v6: ambient particles update
        theme = getattr(s.lv,'theme','meadow') or 'meadow'
        if s.ambient_theme != theme:
            s.ambient.reset(theme)
            s.ambient_theme = theme
        t_ms_now = pygame.time.get_ticks()
        s.ambient.update(t_ms_now)
        # sprint trail
        if s.pl.alive and s.pl.sprint and abs(s.pl.vx)>0:
            s.pl.trail+=1
            if s.pl.trail%3==0: s.parts.append(Part(s.pl.x+s.pl.w//2,s.pl.y+s.pl.h,"💨",-s.pl.vx*0.2,0.5,15))
        # wall-slide sparkles
        if s.pl.alive and s.pl.wslide and s.pl.at%4==0:
            wx=s.pl.x if s.pl.wall==-1 else s.pl.x+s.pl.w
            s.parts.append(Part(wx,s.pl.y+s.pl.h//2+random.randint(-8,8),
                random.uniform(-1,1),random.uniform(-2,0.5),"✨",12))
        # lava/fire ambient particles
        if s.pl.alive:
            pcx=s.pl.x+s.pl.w//2;pcy=s.pl.y+s.pl.h//2
            for r in range(max(0,int(pcy//TS)-1),min(s.lv.rows,int(pcy//TS)+2)):
                for c in range(max(0,int(pcx//TS)-2),min(s.lv.cols,int(pcx//TS)+3)):
                    if s.lv.tiles[r][c]==10 and random.random()<0.03:
                        s.parts.append(Part(c*TS+random.randint(0,TS),r*TS,
                            "🔥",random.uniform(-0.5,0.5),random.uniform(-3,-1),20))
        # timer
        if s.st==s.PLAY: s.elapsed=_time.time()-s.start_time
        s._draw_play()

    def _draw_play(s):
        theme=getattr(s.lv,'theme','meadow') or 'meadow'
        s.scr.blit(s.sky.get(theme),(0,0))
        # bg stars for dark themes
        if theme in ("cave","lava","fortress","space"):
            s.bgstars.draw(s.scr,pygame.time.get_ticks())
        cam=s.cam;sox,soy=s.shake.off()
        # parallax clouds
        if theme in ("meadow","sky","ice","sunset"): s.clouds.draw(s.scr,cam.oxi,s.rds)
        # v6: parallax hills (behind tiles)
        s.hills.draw(s.scr, cam.oxi, theme)
        # v6: ambient particles (behind tiles)
        s.ambient.draw(s.scr, pygame.time.get_ticks())
        sc=max(0,cam.oxi//TS-1);ec=min(s.lv.cols,(cam.oxi+SW)//TS+2)
        sr=max(0,cam.oyi//TS-1);er=min(s.lv.rows,(cam.oyi+SH)//TS+2)
        for r in range(sr,er):
            for c in range(sc,ec):
                t=s.lv.tiles[r][c]
                if t==0: continue
                cat=TD[t][1]
                if cat in ("moving_h","moving_v","crumble","speed_pad","trap","spring","cannon_l","cannon_r"): continue
                tx,ty=cam.apply(c*TS,r*TS)
                # animated collectibles bob
                bob=0
                if cat=="collect": bob=math.sin(pygame.time.get_ticks()*0.005+c+r)*3
                elif cat=="powerup": bob=math.sin(pygame.time.get_ticks()*0.004+c*2)*4
                elif cat=="teleport": bob=math.sin(pygame.time.get_ticks()*0.008+c)*2
                elif cat=="speed_pad": bob=math.sin(pygame.time.get_ticks()*0.01+c)*2
                sf_t=s.rd.render(TD[t][0])
                # ice shimmer
                if cat=="ice":
                    shimmer=int(20*math.sin(pygame.time.get_ticks()*0.003+c*2+r))
                    if shimmer>0: sf_t=sf_t.copy();sf_t.fill((200,230,255,shimmer*3),special_flags=pygame.BLEND_RGBA_ADD)
                s.scr.blit(sf_t,(tx+sox,ty+soy+bob))
        # speed pads (animated)
        t_ms=pygame.time.get_ticks()
        for spr in s.lv.speed_pads():
            tx,ty=cam.apply(spr.x,spr.y)
            bob=math.sin(t_ms*0.01+spr.x*0.05)*2
            sf=s.rd.render("⚡");scr_x,scr_y=tx+sox,ty+soy+bob
            # pulsing glow
            glow_a=int(60+40*math.sin(t_ms*0.008))
            gs=pygame.Surface((TS,TS),pygame.SRCALPHA);gs.fill((255,255,100,glow_a))
            s.scr.blit(gs,(scr_x,scr_y));s.scr.blit(sf,(scr_x,scr_y))
        # v6: spring launchers (animated bounce)
        for sp in s.lv.springs():
            tx,ty=cam.apply(sp.x,sp.y)
            sf=s.rd.render("🎪")
            # pulsing glow + squish animation
            pulse = abs(math.sin(t_ms*0.008 + sp.x*0.05))
            sc_y = 1.0 - pulse * 0.15
            ow,oh = sf.get_size()
            nw = max(1, int(ow)); nh = max(1, int(oh * sc_y))
            sf = pygame.transform.smoothscale(sf, (nw, nh))
            # glow
            glow_a = int(40 + 30 * pulse)
            gs=pygame.Surface((TS,TS),pygame.SRCALPHA)
            gs.fill((255,100,255,glow_a))
            s.scr.blit(gs,(tx+sox,ty+soy))
            s.scr.blit(sf,(tx+sox,ty+soy+(oh-nh)//2))
        # v6: cannons (with directional indicator)
        all_cannons = s.lv.cannons()
        for i, (cx, cy, cdx, _) in enumerate(s.cannons_cd if s.cannons_cd else []):
            tx,ty=cam.apply(cx,cy)
            sf=s.rd.render("💣")
            if cdx < 0: sf=pygame.transform.flip(sf,True,False)
            s.scr.blit(sf,(tx+sox,ty+soy))
            # cooldown indicator bar
            cd_val = s.cannons_cd[i][3]
            if cd_val > 0:
                cd_pct = cd_val / CANNON_CD
                bar_w = int(TS * (1 - cd_pct))
                if bar_w > 0:
                    pygame.draw.rect(s.scr,(100,255,100),(tx+sox,ty+soy+TS-4,bar_w,3))
        # also draw cannons that haven't been initialized yet
        if not s.cannons_cd:
            for cx, cy, cdx, _ in all_cannons:
                tx,ty=cam.apply(cx,cy)
                sf=s.rd.render("💣")
                if cdx < 0: sf=pygame.transform.flip(sf,True,False)
                s.scr.blit(sf,(tx+sox,ty+soy))
        # trap tiles (hidden or revealed)
        for tr,tc in s.lv.traps():
            tx,ty=cam.apply(tc*TS,tr*TS)
            if (tr,tc) in s.triggered_traps:
                s.scr.blit(s.rd.render("🪤"),(tx+sox,ty+soy))
            else:
                # subtle hint (very faint)
                hs=pygame.Surface((TS,TS),pygame.SRCALPHA)
                dist=math.sqrt((s.pl.x+s.pl.w//2-tc*TS-TS//2)**2+(s.pl.y+s.pl.h//2-tr*TS-TS//2)**2)
                if dist<TRAP_RANGE*1.5:
                    a=int(max(0,min(40,(1-dist/(TRAP_RANGE*1.5))*40)))
                    hs.fill((255,100,100,a));s.scr.blit(hs,(tx+sox,ty+soy))
        # movers (v5: with trail effect)
        for mp2 in s.mps:
            tx,ty=cam.apply(mp2.x,mp2.y)
            em=TD[19 if mp2.d=="h" else 20][0]
            # v5: motion trail
            ptx,pty=cam.apply(mp2.px,mp2.py)
            trail=pygame.Surface((TS,TS),pygame.SRCALPHA)
            trail.fill((200,200,255,40))
            s.scr.blit(trail,(ptx+sox,pty+soy))
            # direction arrow indicator
            arr_col=(200,220,255,80)
            if mp2.d=="h":
                arr_x=tx+sox+TS//2;arr_y=ty+soy+TS//2
                ad=1 if mp2.x>mp2.px else -1
                asf=pygame.Surface((12,8),pygame.SRCALPHA)
                pygame.draw.polygon(asf,arr_col,[(0,4) if ad>0 else (12,4),(12,0) if ad>0 else (0,0),(12,8) if ad>0 else (0,8)])
                s.scr.blit(asf,(arr_x-6,arr_y-4))
            s.scr.blit(s.rd.render(em),(tx+sox,ty+soy))
        # crumble
        for cp in s.cps:
            if cp.gone: continue
            tx,ty=cam.apply(cp.x,cp.y)
            sf=s.rd.render("💨")
            if cp.t>0: off=random.randint(-2,2) if cp.t<20 else 0
            else: off=0
            s.scr.blit(sf,(tx+sox+off,ty+soy))
        for en in s.ens: en.draw(s.scr,s.rd,cam)
        s.pl.draw(s.scr,s.rd,cam)
        for p in s.parts: p.draw(s.scr,s.rd,cam)
        for ft in s.ftxts: ft.draw(s.scr,cam)
        for da in s.danims: da.draw(s.scr,s.rd,cam)
        for fb in s.fireballs: fb.draw(s.scr,s.rd,cam)
        for cb in s.cannonballs: cb.draw(s.scr,s.rd,cam)  # v6
        for dp in s.dust_parts: dp.draw(s.scr,s.rd,cam)
        # v5: enemy poof animations
        for pf in s.poofs: pf.draw(s.scr,s.rd,cam)
        # v5: coin magnet visual lines
        if s.pl.has_magnet and s.pl.alive:
            pr2=s.pl.rect()
            pcx2=pr2.centerx;pcy2=pr2.centery
            ls=pygame.Surface((SW,SH),pygame.SRCALPHA)  # single surface for all lines
            for tt,r,c in s.lv.collectibles():
                if (r,c) in s.collected: continue
                if tt not in (5,6,13,27): continue
                ccx=c*TS+TS//2;ccy=r*TS+TS//2
                dist=math.sqrt((pcx2-ccx)**2+(pcy2-ccy)**2)
                if dist<TS*4:
                    a=int(max(0,min(120,(1-dist/(TS*4))*120)))
                    sx1,sy1=cam.apply(pcx2,pcy2)
                    sx2,sy2=cam.apply(ccx,ccy)
                    pygame.draw.line(ls,(255,220,100,a),(sx1+sox,sy1+soy),(sx2+sox,sy2+soy),1)
            s.scr.blit(ls,(0,0))
        # water overlay for visible water tiles
        t_ms2=pygame.time.get_ticks()
        for wr in s.lv.water_rects():
            tx,ty=cam.apply(wr.x,wr.y)
            ws=pygame.Surface((TS,TS),pygame.SRCALPHA)
            wave=int(4*math.sin(t_ms2*0.003+wr.x*0.05))
            ws.fill((30,80,200,70+wave*5));s.scr.blit(ws,(tx+sox,ty+soy+wave))
        # wind zone arrows
        wind_zones_vis = s.lv.wind_zones()
        if wind_zones_vis:
            for wr,wd in wind_zones_vis:
                tx,ty=cam.apply(wr.x,wr.y)
                # animated arrow indicators
                phase=(t_ms2*0.006+wr.x*0.02)%1.0
                arrow_col=(200,220,255,int(80+40*math.sin(t_ms2*0.005)))
                for ai in range(3):
                    ax=tx+sox+int(phase*TS*0.6+ai*TS*0.25)%TS
                    ay=ty+soy+TS//2+int(math.sin(t_ms2*0.008+ai+wr.x*0.01)*4)
                    asf=pygame.Surface((8,6),pygame.SRCALPHA)
                    asf.fill(arrow_col)
                    # draw small arrow shape
                    if wd[0]>0:  # right
                        pygame.draw.polygon(asf,arrow_col,[(0,3),(8,0),(8,6)])
                    else:
                        pygame.draw.polygon(asf,arrow_col,[(8,3),(0,0),(0,6)])
                    s.scr.blit(asf,(ax,ay))
        # conveyor belt arrows
        convs_vis = s.lv.conveyors()
        if convs_vis:
            for cr,cd in convs_vis:
                tx,ty=cam.apply(cr.x,cr.y)
                direction = 1 if cd>0 else -1
                ac=(255,180,50,int(100+50*math.sin(t_ms2*0.008+cr.x*0.03)))
                for ai in range(3):
                    phase=((t_ms2*0.004*direction+cr.x*0.02+ai*0.33)%1.0)
                    ax=tx+sox+int(phase*TS)
                    ay=ty+soy+TS//2
                    asf=pygame.Surface((6,4),pygame.SRCALPHA)
                    if direction>0:
                        pygame.draw.polygon(asf,ac,[(0,2),(6,0),(6,4)])
                    else:
                        pygame.draw.polygon(asf,ac,[(6,2),(0,0),(0,4)])
                    s.scr.blit(asf,(ax,ay))
        # goal flag pulse
        goal=s.lv.goal()
        if goal:
            gtx,gty=cam.apply(goal.x,goal.y)
            pulse=int(6*math.sin(t_ms2*0.005))
            gs=pygame.Surface((TS+pulse*2,TS+pulse*2),pygame.SRCALPHA)
            gs.fill((255,255,100,int(30+20*math.sin(t_ms2*0.004))))
            s.scr.blit(gs,(gtx-pulse, gty-pulse))
        # activated checkpoints: dimmed vs bright
        for cr,cc in s.lv.checkpoints():
            tx,ty=cam.apply(cc*TS,cr*TS)
            if (cr,cc) in s.activated_cp:
                # dim overlay on activated
                dim=pygame.Surface((TS,TS),pygame.SRCALPHA);dim.fill((0,0,0,100))
                s.scr.blit(dim,(tx+sox,ty+soy))
        # HUD
        hud=pygame.Surface((SW,52),pygame.SRCALPHA);hud.fill((0,0,0,130));s.scr.blit(hud,(0,0))
        f=pygame.font.SysFont("Arial",20,True)
        s.scr.blit(f.render(f"Lv {s.li+1}: {s.lv.name}",True,WHITE),(10,4))
        st=f.render(f"Score: {s.pl.score}",True,HILITE)
        s.scr.blit(st,(SW//2-st.get_width()//2,4))
        # timer
        mins=int(s.elapsed)//60;secs=int(s.elapsed)%60
        time_warn = s.elapsed > 90
        tt_col = (255,80,80) if time_warn and (s.elapsed*3)%1<0.5 else WHITE
        tt=f.render(f"{mins}:{secs:02d}",True,tt_col)
        s.scr.blit(tt,(SW//2-tt.get_width()//2,28))
        # coins
        cc=f.render(f"🪙 {len(s.collected)}/{s.totcol}",True,(200,200,255))
        s.scr.blit(cc,(SW//2-cc.get_width()//2-100,28))
        # combo
        if s.combo>1:
            ct=f.render(f"Combo x{s.combo}!",True,(255,150,50))
            s.scr.blit(ct,(SW//2+80,28))
        # multiplier
        if s.pl.mult>1:
            mt=f.render(f"x{s.pl.mult}",True,(255,255,100))
            s.scr.blit(mt,(SW//2+180,28))
        # lives + powerups
        hs=s.rds.render(HEART)
        for i in range(s.pl.lives): s.scr.blit(hs,(SW-35-i*28,6))
        if s.pl.has_dj: s.scr.blit(s.rds.render("🪽"),(SW-35,30))
        if s.pl.has_shield: s.scr.blit(s.rds.render("🛡️"),(SW-60,30))
        if s.pl.has_magnet: s.scr.blit(s.rds.render("🧲"),(SW-85,30))
        if s.pl.has_key: s.scr.blit(s.rds.render("🔑"),(SW-110,30))
        if s.pl.potion_t>0:
            s.scr.blit(s.rds.render("🧪"),(SW-135,30))
            si=pygame.font.SysFont("Arial",11,True).render(f"{s.pl.potion_t//60+1}s",True,(255,200,255))
            s.scr.blit(si,(SW-118,34))
        if s.pl.speed_boost_t>0:
            si=pygame.font.SysFont("Arial",12,True).render("SPEED!",True,(255,255,100))
            s.scr.blit(si,(SW-190,34))
        if s.pl.sprint and s.pl.alive:
            si=pygame.font.SysFont("Arial",12,True).render("SPRINT",True,(255,200,50))
            s.scr.blit(si,(SW-210,34))
        # dash cooldown
        if s.pl.dash_cd>0:
            si=pygame.font.SysFont("Arial",11).render(f"Dash:{s.pl.dash_cd//6}",True,(150,150,150))
            s.scr.blit(si,(SW-260,34))
        elif s.pl.alive:
            si=pygame.font.SysFont("Arial",11,True).render("E:Dash",True,(100,255,100))
            s.scr.blit(si,(SW-260,34))
        # minimap
        _draw_minimap(s.scr,s.lv,SW-130,SH-80,120,50,3,(s.pl.x,s.pl.y))
        # combo timer bar
        if s.combo>1 and s.combo_t>0:
            bar_w=80;bar_h=6;bar_x=SW//2-bar_w//2;bar_y=50
            pygame.draw.rect(s.scr,(40,40,40),(bar_x,bar_y,bar_w,bar_h),border_radius=3)
            fill_w=int(bar_w*(s.combo_t/COMBO_WINDOW))
            bar_col=(255,150,50) if s.combo<5 else (255,100,255) if s.combo<10 else (100,255,255)
            if fill_w>0: pygame.draw.rect(s.scr,bar_col,(bar_x,bar_y,fill_w,bar_h),border_radius=3)
        hf=pygame.font.SysFont("Arial",13)
        s.scr.blit(hf.render("R:Restart P:Pause M:Mute N:Music E:Dash Down+Space:Drop",True,(180,180,180)),(SW//2-160,SH-16))
        # v6: sprint speed lines
        if s.pl.alive and s.pl.sprint and abs(s.pl.vx) > PLAYER_SPEED * SPRINT_MULT * 0.8:
            line_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
            dir_sign = 1 if s.pl.vx > 0 else -1
            sx_pl, sy_pl = cam.apply(s.pl.x + s.pl.w//2, s.pl.y + s.pl.h//2)
            for i in range(5):
                ly = sy_pl + random.randint(-s.pl.h, s.pl.h)
                lx = sx_pl - dir_sign * random.randint(10, 60)
                a = random.randint(30, 80)
                pygame.draw.line(line_surf, (255, 255, 255, a),
                    (lx, ly), (lx - dir_sign * random.randint(15, 40), ly), 1)
            s.scr.blit(line_surf, (0, 0))
        # v6: achievement popups (drawn on top of everything in game)
        for ap in s.ach_queue: ap.draw(s.scr, s.rdb)
        # low health warning vignette
        if s.pl.alive and s.pl.lives==1 and (pygame.time.get_ticks()//500)%2==0:
            vig=pygame.Surface((SW,SH),pygame.SRCALPHA)
            # red edge gradient
            for i in range(20):
                a=int(40*(1-i/20))
                pygame.draw.rect(vig,(255,0,0,a),(i,i,SW-2*i,SH-2*i))
            s.scr.blit(vig,(0,0))

    # ── Pause ────────────────────────────────────────────────────────────
    def _t_pause(s,evts,mp):
        cx=SW//2
        bs=[Btn(cx-120,300,240,50,"Resume",GREEN_B),Btn(cx-120,360,240,50,"Restart",ORANGE_B),Btn(cx-120,420,240,50,"Menu",DARK_GRAY)]
        for b in bs: b.upd(mp)
        for e in evts:
            if bs[0].hit(e): s.st=s.pstate or s.PLAY
            elif bs[1].hit(e): s._start(s.li)
            elif bs[2].hit(e): s.st=s.MENU
            if e.type==pygame.KEYDOWN and e.key==pygame.K_p: s.st=s.pstate or s.PLAY
        dim=pygame.Surface((SW,SH),pygame.SRCALPHA);dim.fill((0,0,0,160));s.scr.blit(dim,(0,0))
        f=pygame.font.SysFont("Arial",48,True);t=f.render("PAUSED",True,WHITE)
        s.scr.blit(t,(cx-t.get_width()//2,80))
        ps=s.rdb.render("⏸️");s.scr.blit(ps,(cx-ps.get_width()//2,140))
        # v5: enhanced pause info panel
        panel=pygame.Surface((380,130),pygame.SRCALPHA);panel.fill((30,30,50,200))
        pygame.draw.rect(panel,(80,80,120,200),(0,0,380,130),2,border_radius=10)
        s.scr.blit(panel,(cx-190,170))
        inf=pygame.font.SysFont("Arial",16)
        s.scr.blit(inf.render(f"Level: {s.lv.name}   Score: {s.pl.score}",True,WHITE),(cx-175,180))
        s.scr.blit(inf.render(f"Lives: {s.pl.lives}   Coins: {len(s.collected)}/{s.totcol}",True,LGRAY),(cx-175,205))
        mins=int(s.elapsed)//60;secs=int(s.elapsed)%60
        s.scr.blit(inf.render(f"Time: {mins}:{secs:02d}   Deaths: {s.deaths}",True,LGRAY),(cx-175,230))
        s.scr.blit(inf.render(f"Music: {'ON' if s.music_on else 'OFF'} (N)   SFX: {'ON' if s.snd.on else 'OFF'} (M)",True,LGRAY),(cx-175,255))
        for b in bs: b.draw(s.scr)

    # ── Win ──────────────────────────────────────────────────────────────
    def _t_win(s,evts,mp):
        has_next=s.li+1<len(s.levels) and s.li+1<s._unlocked()
        cx=SW//2
        # v5: play grade sound on first frame
        if not hasattr(s,'_win_parts'):
            s._win_parts=[];s._win_timer=0;s._win_grade_played=False
        if not s._win_grade_played:
            grade,grade_col=s._grade()
            if grade=="S": s.snd.play("grade_s")
            elif grade in ("A","B"): s.snd.play("grade_a")
            s._win_grade_played=True
        bs=[Btn(cx-120,520,240,55,"Next Level",GREEN_B),Btn(cx-120,585,240,55,"Menu",DARK_GRAY)]
        for b in bs: b.upd(mp)
        for e in evts:
            if bs[0].hit(e) and has_next: s._start(s.li+1)
            elif bs[1].hit(e): s.st=s.MENU
        s.scr.blit(s.sky.get("meadow"),(0,0))
        # firework particles celebration
        s._win_timer+=1
        if s._win_timer%8==0 and s._win_timer<120:
            fx=random.randint(100,SW-100);fy=random.randint(50,200)
            for _ in range(12):
                s._win_parts.append(Part(fx,fy,random.choice(["✨","🎉","⭐","🌟","💥"]),
                    random.uniform(-4,4),random.uniform(-5,1),random.randint(30,60)))
        s._win_parts=[p for p in s._win_parts if p.update()]
        for p in s._win_parts: p.draw(s.scr,s.rds,Cam(SW,SH))
        fb=pygame.font.SysFont("Arial",46,True);t=fb.render("Level Complete!",True,(50,180,50))
        sh=fb.render("Level Complete!",True,BLACK)
        s.scr.blit(sh,(cx-sh.get_width()//2+3,53));s.scr.blit(t,(cx-t.get_width()//2,50))
        tr=s.rdb.render("🏆");s.scr.blit(tr,(cx-tr.get_width()//2,105))
        f=pygame.font.SysFont("Arial",24)
        s.scr.blit(f.render(f"Score: {s.pl.score}",True,(50,50,80)),(cx-f.render(f"Score: {s.pl.score}",True,(50,50,80)).get_width()//2,195))
        # v5: grade display
        grade,grade_col=s._grade()
        gf=pygame.font.SysFont("Arial",64,True)
        # grade glow
        t_ms=pygame.time.get_ticks()
        glow_r=int(8+4*math.sin(t_ms*0.008))
        gs=pygame.Surface((80+glow_r*2,80+glow_r*2),pygame.SRCALPHA)
        gs.fill((*grade_col,int(40+20*math.sin(t_ms*0.006))))
        s.scr.blit(gs,(cx-40-glow_r,225-glow_r))
        gt=gf.render(grade,True,grade_col)
        s.scr.blit(gt,(cx-gt.get_width()//2,225))
        # stars
        st=s._stars();ssf=pygame.font.SysFont("Arial",36)
        sst=ssf.render("⭐"*st+"☆"*(3-st),True,HILITE)
        s.scr.blit(sst,(cx-sst.get_width()//2,305))
        # time
        mins=int(s.elapsed)//60;secs=int(s.elapsed)%60
        tb=max(0,int(TIME_BONUS_MAX*(1-s.elapsed/120)))
        tf=pygame.font.SysFont("Arial",20)
        s.scr.blit(tf.render(f"Time: {mins}:{secs:02d}  |  Time Bonus: +{tb}",True,(80,80,120)),(cx-150,350))
        # collectible %
        if s.totcol>0:
            pct=len(s.collected)*100//s.totcol
            s.scr.blit(tf.render(f"Collectibles: {len(s.collected)}/{s.totcol} ({pct}%)",True,(80,80,120)),(cx-150,378))
        s.scr.blit(tf.render(f"Deaths: {s.deaths}",True,GRAY),(cx-150,406))
        # v5: grade explanation
        ef=pygame.font.SysFont("Arial",14)
        grade_info = "S: Fast + All Coins  |  A: Great  |  B: Good  |  C: Complete"
        s.scr.blit(ef.render(grade_info,True,(120,120,150)),(cx-170,440))
        for b in bs: b.draw(s.scr)

    # ── Game Over ────────────────────────────────────────────────────────
    def _t_go(s,evts,mp):
        cx=SW//2
        bs=[Btn(cx-120,340,240,55,"Retry",GREEN_B),Btn(cx-120,410,240,55,"Menu",DARK_GRAY)]
        for b in bs: b.upd(mp)
        for e in evts:
            if bs[0].hit(e): s._start(s.li)
            elif bs[1].hit(e): s.st=s.MENU
        s.scr.blit(s.sky.get("meadow"),(0,0))
        fb=pygame.font.SysFont("Arial",46,True);t=fb.render("Game Over",True,(220,50,50))
        sh=fb.render("Game Over",True,BLACK)
        s.scr.blit(sh,(cx-sh.get_width()//2+3,133));s.scr.blit(t,(cx-t.get_width()//2,130))
        sk=s.rdb.render("💀");s.scr.blit(sk,(cx-sk.get_width()//2,200))
        f=pygame.font.SysFont("Arial",24)
        s.scr.blit(f.render(f"Final Score: {s.pl.score}",True,(80,80,120)),(cx-100,285))
        s.scr.blit(f.render(f"Deaths: {s.deaths}",True,GRAY),(cx-60,315))
        for b in bs: b.draw(s.scr)

    # ── Editor ───────────────────────────────────────────────────────────
    def _init_ed(s):
        s.elv=Level(60,16);s.elv.name="Custom Level"
        s.et=1;s.ec=Cam(SW,SH-100);s.eg=True
        s.em="";s.emt=0;s.efn="my_level";s.ehist=[]
        s.eti=0;s.ecopy=None;s.eshow_minimap=False;s.ed_layer_filter=None
        s.st=s.EDIT

    def _ed_undo(s):
        if s.ehist: s.elv.tiles=[r[:] for r in s.ehist.pop()];s.em="Undo!";s.emt=60

    def _flood(s,r,c,nt):
        """Flood fill: replace contiguous same-tile area with nt."""
        if r<0 or r>=s.elv.rows or c<0 or c>=s.elv.cols: return
        ot=s.elv.tiles[r][c]
        if ot==nt: return
        stack=[(r,c)];visited=set()
        while stack:
            cr,cc=stack.pop()
            if (cr,cc) in visited: continue
            if cr<0 or cr>=s.elv.rows or cc<0 or cc>=s.elv.cols: continue
            if s.elv.tiles[cr][cc]!=ot: continue
            visited.add((cr,cc));s.elv.set(cr,cc,nt)
            stack.extend([(cr-1,cc),(cr+1,cc),(cr,cc-1),(cr,cc+1)])

    def _t_edit(s,evts,mp):
        PY=SH-100
        if s.emt>0: s.emt-=1
        keys=pygame.key.get_pressed()
        sp=10 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 5
        if keys[pygame.K_LEFT]: s.ec.ox-=sp
        if keys[pygame.K_RIGHT]: s.ec.ox+=sp
        if keys[pygame.K_UP]: s.ec.oy-=sp
        if keys[pygame.K_DOWN]: s.ec.oy+=sp
        s.ec.ox=max(0,min(s.ec.ox,s.elv.width-SW))
        s.ec.oy=max(0,min(s.ec.oy,s.elv.height-PY))
        mb=pygame.mouse.get_pressed();ined=mp[1]<PY
        if ined and (mb[0] or mb[2]):
            wx=mp[0]+s.ec.ox;wy=mp[1]+s.ec.oy
            c,r=int(wx//TS),int(wy//TS)
            if 0<=r<s.elv.rows and 0<=c<s.elv.cols:
                nv=s.et if mb[0] else 0
                if s.elv.tiles[r][c]!=nv: s.elv.set(r,c,nv)
        for e in evts:
            if e.type==pygame.MOUSEBUTTONDOWN:
                if e.button==1 and ined:
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    if len(s.ehist)>50: s.ehist.pop(0)
                if e.button==3 and ined:
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    if len(s.ehist)>50: s.ehist.pop(0)
                if e.button==2 and ined:  # middle click = set spawn
                    wx=mp[0]+s.ec.ox;wy=mp[1]+s.ec.oy
                    c,r=int(wx//TS),int(wy//TS)
                    s.elv.spawn=(c*TS,r*TS);s.em=f"Spawn set at ({c},{r})";s.emt=90
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_0: s.et=0
                elif pygame.K_1<=e.key<=pygame.K_9:
                    idx=e.key-pygame.K_1+1
                    if idx in TD: s.et=idx
                elif e.key==pygame.K_g: s.eg=not s.eg
                elif e.key==pygame.K_f and ined:
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    wx=mp[0]+s.ec.ox;wy=mp[1]+s.ec.oy
                    c,r=int(wx//TS),int(wy//TS)
                    s._flood(r,c,s.et);s.em=f"Flood fill [{s.et}]";s.emt=60
                elif e.key==pygame.K_t:
                    test=Level.from_dict(s.elv.to_dict());test.name=f"[TEST] {s.elv.name}"
                    if len(s.levels)>len(s.builtins) and s.levels[-1].name.startswith("[TEST]"): s.levels[-1]=test
                    else: s.levels.append(test)
                    s._start(len(s.levels)-1)
                elif e.key==pygame.K_z and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]): s._ed_undo()
                elif e.key==pygame.K_c and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    # copy region around cursor
                    wx=mp[0]+s.ec.ox;wy=mp[1]+s.ec.oy
                    cc,cr=int(wx//TS),int(wy//TS)
                    w=min(5,s.elv.cols-cc);h=min(3,s.elv.rows-cr)
                    if w>0 and h>0:
                        s.ecopy=[[s.elv.get(cr+rr,cc+rc) for rc in range(w)] for rr in range(h)]
                        s.em=f"Copied {w}x{h}";s.emt=60
                elif e.key==pygame.K_v and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    if s.ecopy:
                        s.ehist.append([row[:] for row in s.elv.tiles])
                        wx=mp[0]+s.ec.ox;wy=mp[1]+s.ec.oy
                        pc,pr=int(wx//TS),int(wy//TS)
                        for rr,row in enumerate(s.ecopy):
                            for rc,t in enumerate(row):
                                if t and 0<=pr+rr<s.elv.rows and 0<=pc+rc<s.elv.cols:
                                    s.elv.set(pr+rr,pc+rc,t)
                        s.em="Pasted!";s.emt=60
                elif e.key==pygame.K_s and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    fn=s.efn.strip()
                    if not fn.endswith(".json"): fn+=".json"
                    s.elv.name=fn.replace(".json","").replace("_"," ").title()
                    s.elv.theme=s.etl[s.eti];s.elv.save(fn)
                    s.em=f"Saved: {fn}";s.emt=120;s._scan()
                elif e.key==pygame.K_l and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    fn=s.efn.strip()
                    if not fn.endswith(".json"): fn+=".json"
                    try: s.elv=Level.load(fn);s.em=f"Loaded: {fn}";s.emt=120
                    except FileNotFoundError: s.em=f"Not found: {fn}";s.emt=120
                elif e.key==pygame.K_n and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    s.elv=Level(60,16);s.elv.name="Custom Level";s.em="New level!";s.emt=90
                elif e.key==pygame.K_EQUALS or e.key==pygame.K_PLUS:
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    nl=Level(s.elv.cols+10,s.elv.rows)
                    for r in range(s.elv.rows):
                        for c in range(s.elv.cols): nl.tiles[r][c]=s.elv.tiles[r][c]
                    nl.name=s.elv.name;nl.theme=s.elv.theme;nl.spawn=s.elv.spawn;s.elv=nl
                    s.em=f"Resized: {nl.cols}x{nl.rows}";s.emt=90
                elif e.key==pygame.K_MINUS and s.elv.cols>20:
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    nl=Level(s.elv.cols-10,s.elv.rows)
                    for r in range(nl.rows):
                        for c in range(min(s.elv.cols-10,nl.cols)): nl.tiles[r][c]=s.elv.tiles[r][c]
                    nl.name=s.elv.name;nl.theme=s.elv.theme;nl.spawn=s.elv.spawn;s.elv=nl
                    s.em=f"Resized: {nl.cols}x{nl.rows}";s.emt=90
                elif e.key==pygame.K_TAB:
                    s.eti=(s.eti+1)%len(s.etl);s.elv.theme=s.etl[s.eti]
                    s.em=f"Theme: {s.elv.theme}";s.emt=90
                elif e.key==pygame.K_x:
                    s.ehist.append([row[:] for row in s.elv.tiles])
                    s.elv.tiles=[[0]*s.elv.cols for _ in range(s.elv.rows)]
                    s.em="Cleared!";s.emt=90
                elif e.key==pygame.K_m:
                    s.eshow_minimap=not s.eshow_minimap
                elif e.key==pygame.K_l and not (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    # L without ctrl = cycle layer filter
                    cats=[None,"terrain","collect","enemy","hazard","powerup","deco","goal","moving_h","moving_v","bounce","checkpoint","crumble","teleport","flying_enemy","dragon_enemy","one_way","conveyor_l","conveyor_r","wind","ice","water","speed_pad","key","door","trap","spring","cannon_l","cannon_r","chaser"]
                    if s.ed_layer_filter is None: s.ed_layer_filter=cats[0]
                    else:
                        idx=cats.index(s.ed_layer_filter) if s.ed_layer_filter in cats else 0
                        s.ed_layer_filter=cats[(idx+1)%len(cats)]
                    fname=s.ed_layer_filter if s.ed_layer_filter else "All"
                    s.em=f"Filter: {fname}";s.emt=60
                elif e.key==pygame.K_ESCAPE: s.st=s.MENU
            if e.type==pygame.MOUSEWHEEL:
                tids=sorted(TD.keys())
                i=tids.index(s.et) if s.et in tids else 0
                s.et=tids[(i+e.y)%len(tids)]
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and mp[1]>=PY:
                tids=sorted(TD.keys());idx=mp[0]//36
                if idx<len(tids): s.et=tids[idx]
        # Draw
        theme=getattr(s.elv,'theme','meadow') or 'meadow'
        s.scr.fill((30,30,50));cam=s.ec
        sky_area=pygame.Surface((SW,PY));sky_area.blit(s.sky.get(theme),(0,0));sky_area.set_alpha(30)
        s.scr.blit(sky_area,(0,0))
        sc2=max(0,int(cam.ox//TS)-1);ec2=min(s.elv.cols,int((cam.ox+SW)//TS)+2)
        sr2=max(0,int(cam.oy//TS)-1);er2=min(s.elv.rows,int((cam.oy+PY)//TS)+2)
        for r in range(sr2,er2):
            for c in range(sc2,ec2):
                t=s.elv.tiles[r][c]
                if t==0: continue
                if s.ed_layer_filter and TD[t][1]!=s.ed_layer_filter: continue
                tx,ty=cam.apply(c*TS,r*TS)
                s.scr.blit(s.rd.render(TD[t][0]),(tx,ty))
        if s.eg:
            for c in range(sc2,ec2+1):
                x,_=cam.apply(c*TS,0);pygame.draw.line(s.scr,(50,50,70),(x,0),(x,PY))
            for r in range(sr2,er2+1):
                _,y=cam.apply(0,r*TS);pygame.draw.line(s.scr,(50,50,70),(0,y),(SW,y))
        if mp[1]<PY:
            wx=mp[0]+cam.ox;wy=mp[1]+cam.oy
            cc,rr=int(wx//TS),int(wy//TS)
            tx,ty=cam.apply(cc*TS,rr*TS)
            hl=pygame.Surface((TS,TS),pygame.SRCALPHA);hl.fill((255,255,100,60))
            s.scr.blit(hl,(tx,ty));pygame.draw.rect(s.scr,HILITE,(tx,ty,TS,TS),2)
            if s.et:
                pv=s.rd.render(TD[s.et][0]);pv.set_alpha(120);s.scr.blit(pv,(tx,ty))
        # spawn
        spx,spy=s.elv.spawn;sx2,sy2=cam.apply(spx,spy)
        pygame.draw.rect(s.scr,(0,255,0),(sx2,sy2,36,38),2)
        sf=pygame.font.SysFont("Arial",11);s.scr.blit(sf.render("SPAWN",True,(0,255,0)),(sx2,sy2-14))
        # minimap
        if s.eshow_minimap:
            _draw_minimap(s.scr,s.elv,SW-160,5,150,75,2)
        # palette
        pygame.draw.rect(s.scr,PANEL_BG,(0,PY,SW,100))
        pygame.draw.line(s.scr,PBORDER,(0,PY),(SW,PY),2)
        tids=sorted(TD.keys());pw=36
        for i,tid in enumerate(tids):
            x=i*pw+3
            if tid==s.et: pygame.draw.rect(s.scr,HILITE,(x-1,PY+2,pw-2,48),3,border_radius=4)
            em=TD[tid][0]
            if em: s.scr.blit(s.rds.render(em),(x+7,PY+3))
            nf=pygame.font.SysFont("Arial",9);s.scr.blit(nf.render(str(tid),True,LGRAY),(x+pw//2-4,PY+30))
        inf=pygame.font.SysFont("Arial",15)
        s.scr.blit(inf.render(f"[{s.et}] {TD[s.et][0]} {TD[s.et][3]}",True,WHITE),(8,PY+52))
        hf=pygame.font.SysFont("Arial",11)
        s.scr.blit(hf.render("LClick:Place RClick:Erase MClick:Spawn Scroll/0-9:Tile G:Grid F:Flood T:Test Ctrl+Z:Undo C/V:Copy/Paste Ctrl+S/L:Save/Load +/-:Resize Tab:Theme X:Clear L:Filter M:Minimap ESC:Menu",True,GRAY),(8,PY+72))
        ff=pygame.font.SysFont("Arial",13)
        ft=ff.render(f"{s.efn}.json | {s.elv.theme} | {s.elv.cols}x{s.elv.rows} | Filter:{s.ed_layer_filter or 'All'}",True,LGRAY)
        s.scr.blit(ft,(SW-ft.get_width()-8,PY+52))
        if s.emt>0:
            mf=pygame.font.SysFont("Arial",18,True);ms=mf.render(s.em,True,(100,255,100))
            ms.set_alpha(min(255,s.emt*4));s.scr.blit(ms,(SW//2-ms.get_width()//2,10))

# ─── Minimap helper ─────────────────────────────────────────────────────
def _draw_minimap(scr,lv,x,y,w,h,ps,player_pos=None):
    mm=pygame.Surface((w,h),pygame.SRCALPHA);mm.fill((0,0,0,140))
    sx=w/max(lv.width,1);sy=h/max(lv.height,1)
    for r in range(lv.rows):
        for c in range(lv.cols):
            t=lv.tiles[r][c]
            if t==0: continue
            px=int(c*TS*sx);py=int(r*TS*sy);pw2=max(1,int(TS*sx));ph2=max(1,int(TS*sy))
            cat=TD[t][1]
            if cat=="terrain" or TD[t][2]: col=(140,140,140)
            elif cat in ("collect",): col=(255,220,50)
            elif cat in ("enemy","flying_enemy","dragon_enemy"): col=(255,60,60)
            elif cat=="hazard" or cat=="water" or cat=="trap": col=(255,100,0) if cat!="water" else (50,100,220)
            elif cat=="goal": col=(50,255,50)
            elif cat=="powerup": col=(100,200,255)
            elif cat=="ice": col=(150,200,240)
            elif cat=="speed_pad": col=(255,255,100)
            elif cat=="key": col=(255,220,100)
            elif cat=="door": col=(180,120,60)
            else: col=(100,100,120)
            pygame.draw.rect(mm,col,(px,py,pw2,ph2))
    # v5: show player position on minimap
    if player_pos:
        ppx=int(player_pos[0]*sx);ppy=int(player_pos[1]*sy)
        pygame.draw.rect(mm,(255,255,255),(ppx,ppy,max(3,int(TS*sx)),max(3,int(TS*sy))))
    scr.blit(mm,(x,y))

if __name__=="__main__":
    Game().run()