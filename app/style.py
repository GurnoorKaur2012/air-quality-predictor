"""All the look-and-feel: colours, fonts, glass cards and the moving misty-hills wallpaper."""
import base64
import random
from pathlib import Path

AQI_COLORS = {"Good": "#3ddc84", "Satisfactory": "#a3d65c", "Moderate": "#ffd23f",
              "Poor": "#ff8c42", "Very Poor": "#ef476f", "Severe": "#a4243b"}
ACCENT = "#86efac"      # tea-leaf green
ACCENT2 = "#7dd3fc"     # clear-sky blue
WARN = "#ff8c42"        # smog orange

WALLPAPER = Path(__file__).resolve().parent / "assets" / "wallpaper.jpg"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root{
  --glass:rgba(8,24,19,.50); --glass-2:rgba(8,24,19,.68);
  --line:rgba(255,255,255,.16); --text:#f1f8f4; --muted:#b6cbc2;
  --mint:#86efac; --sky:#7dd3fc; --smog:#ff8c42; --danger:#ef476f;
}

/* ================= MOVING WALLPAPER ================= */
.stApp{background:#07140f; color:var(--text); font-family:'Inter',sans-serif}
.wall{position:fixed; inset:-6%; z-index:0; pointer-events:none;
  background-size:cover; background-position:center;
  animation:kenburns 48s ease-in-out infinite alternate}
@keyframes kenburns{
  0%  {transform:scale(1.02) translate(0,0)}
  50% {transform:scale(1.12) translate(-2.5%,-1.5%)}
  100%{transform:scale(1.06) translate(2%,1%)}}
/* drifting fog: three wide soft layers moving at different speeds */
.mist{position:fixed; left:0; width:300%; z-index:0; pointer-events:none; filter:blur(18px)}
.mist.m1{top:8%;  height:45%; opacity:.30; animation:drift 95s linear infinite;
  background:radial-gradient(closest-side,rgba(255,255,255,.9),transparent) 0 0/33.3% 100% repeat-x}
.mist.m2{top:40%; height:55%; opacity:.25; animation:drift 140s linear infinite reverse;
  background:radial-gradient(closest-side,rgba(235,245,240,.85),transparent) 0 0/25% 100% repeat-x}
.mist.m3{bottom:-10%; height:45%; opacity:.35; animation:drift 70s linear infinite;
  background:radial-gradient(closest-side,rgba(255,255,255,.95),transparent) 0 0/20% 100% repeat-x}
@keyframes drift{from{transform:translateX(0)} to{transform:translateX(-33.3%)}}
/* dark veil so text stays readable */
.veil{position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(120% 90% at 60% 30%, rgba(4,14,10,.05), rgba(4,14,10,.60)),
    linear-gradient(180deg, rgba(4,14,10,.30) 0%, rgba(4,14,10,.42) 50%, rgba(4,14,10,.72) 100%)}
/* floating mist droplets */
.particles{position:fixed; inset:0; pointer-events:none; z-index:0; overflow:hidden}
.particles span{position:absolute; bottom:-10px; border-radius:50%;
  background:rgba(235,255,245,.7); box-shadow:0 0 8px rgba(134,239,172,.7);
  animation: rise linear infinite}
@keyframes rise{ 0%{transform:translateY(0) translateX(0); opacity:0}
  10%{opacity:.9} 100%{transform:translateY(-110vh) translateX(60px); opacity:0} }

/* ================= HIDE DEFAULT STREAMLIT CHROME ================= */
#MainMenu, footer, header[data-testid="stHeader"]{visibility:hidden; height:0}
.block-container{padding-top:1.2rem; max-width:1380px; position:relative; z-index:1}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif !important; color:var(--text) !important; letter-spacing:-.01em}
p, li, label, .stMarkdown{color:var(--text)}

/* ================= TOP BAR + NAV PILLS ================= */
.topbar{display:flex; align-items:center; justify-content:space-between; margin-bottom:.5rem}
.brand{display:flex; gap:.6rem; align-items:center; font-family:'Space Grotesk'; font-weight:600; letter-spacing:.1em}
.brand .dot{width:12px; height:12px; border-radius:50%; background:var(--mint);
  box-shadow:0 0 14px var(--mint); animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1} 50%{opacity:.35}}
.stage-count{font-size:.8rem; color:var(--muted); letter-spacing:.14em}

div[role="radiogroup"]{gap:.35rem !important; flex-wrap:wrap}
div[role="radiogroup"] label{
  background:var(--glass); border:1px solid var(--line); border-radius:999px;
  padding:.3rem .9rem !important; margin:0 !important; transition:all .25s; cursor:pointer;
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px)}
div[role="radiogroup"] label:hover{border-color:var(--mint); transform:translateY(-1px)}
div[role="radiogroup"] > label > div:first-child,
label[data-testid="stRadioOption"] > div > div:first-child{display:none}   /* hide radio circles */
div[role="radiogroup"] label p{font-size:.78rem !important; letter-spacing:.04em; margin:0}
div[role="radiogroup"] label:has(input:checked),
div[role="radiogroup"] label[data-selected="true"]{
  background:linear-gradient(90deg,rgba(134,239,172,.32),rgba(125,211,252,.22));
  border-color:var(--mint); box-shadow:0 0 18px rgba(134,239,172,.3)}
.progress{height:3px; background:rgba(255,255,255,.12); border-radius:3px; margin:.7rem 0 1.5rem}
.progress > div{height:100%; border-radius:3px; transition:width .6s ease;
  background:linear-gradient(90deg,var(--mint),var(--sky)); box-shadow:0 0 12px var(--mint)}

/* ================= GLASS CARDS ================= */
.glass{background:var(--glass); border:1px solid var(--line); border-radius:22px;
  padding:1.2rem 1.35rem; backdrop-filter:blur(18px) saturate(1.2); -webkit-backdrop-filter:blur(18px) saturate(1.2);
  box-shadow:0 10px 40px rgba(0,0,0,.30); margin-bottom:1rem; animation:fadeUp .7s ease both}
.glass:hover{border-color:rgba(134,239,172,.45)}
.glass h4{margin:.1rem 0 .5rem; font-size:1.05rem}
.glass p{color:var(--muted); margin:0; line-height:1.55}
.kicker{font-size:.72rem; letter-spacing:.18em; color:var(--muted); text-transform:uppercase;
  display:flex; justify-content:space-between; gap:.5rem}
.kicker b{color:var(--mint); font-weight:600}
.big{font-family:'Space Grotesk'; font-size:2.1rem; font-weight:600; line-height:1.1; margin-top:.35rem}
@keyframes fadeUp{from{opacity:0; transform:translateY(16px)} to{opacity:1; transform:none}}
[data-testid="stPlotlyChart"]{background:var(--glass); border:1px solid var(--line); border-radius:20px;
  padding:.4rem .5rem; backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); animation:fadeUp .7s ease both}

/* KPI tiles on the Results page */
.kpi{text-align:center; padding:1.3rem 1rem}
.kpi .v{font-family:'Space Grotesk'; font-size:2.6rem; font-weight:700;
  background:linear-gradient(90deg,var(--mint),var(--sky)); -webkit-background-clip:text; color:transparent}
.kpi .l{font-size:.72rem; letter-spacing:.18em; color:var(--muted)}
.kpi .n{font-size:.8rem; color:var(--muted); margin-top:.2rem}

/* ================= PAGE HEADER ================= */
.stage-tag{display:inline-flex; gap:.5rem; align-items:center; padding:.3rem .8rem; border-radius:999px;
  border:1px solid var(--line); background:var(--glass); font-size:.72rem; letter-spacing:.16em; color:var(--muted)}
.stage-tag i{width:8px; height:8px; border-radius:50%; background:var(--mint); box-shadow:0 0 8px var(--mint)}
.page-title{font-family:'Space Grotesk'; font-size:3.1rem; font-weight:700; line-height:1.05; margin:.6rem 0 .3rem;
  text-shadow:0 4px 30px rgba(0,0,0,.45)}
.page-title span{background:linear-gradient(90deg,var(--mint),var(--sky)); -webkit-background-clip:text; color:transparent}
.page-sub{color:var(--muted); font-size:1.05rem; max-width:820px; margin-bottom:1.4rem}

/* ================= HERO ================= */
.hero{position:relative; min-height:560px; display:grid; grid-template-columns:1.1fr .95fr 110px; gap:1.5rem; align-items:center}
.pill{display:inline-flex; align-items:center; gap:.5rem; border:1px solid var(--line); border-radius:999px;
  padding:.35rem .9rem; font-size:.72rem; letter-spacing:.16em; color:var(--muted); background:var(--glass); backdrop-filter:blur(12px)}
.pill b{color:var(--mint); font-weight:600} .pill i{width:7px;height:7px;border-radius:50%;background:var(--mint);box-shadow:0 0 8px var(--mint)}
.headline{font-family:'Space Grotesk'; font-weight:500; font-size:5.4rem; line-height:.98; letter-spacing:-.02em; margin:1.2rem 0;
  text-shadow:0 6px 40px rgba(0,0,0,.5)}
.headline .glow{background:linear-gradient(90deg,#86efac,#d9f99d,#7dd3fc); -webkit-background-clip:text; color:transparent;
  filter:drop-shadow(0 0 22px rgba(134,239,172,.35))}
.lead{color:#d5e5dd; font-size:1.12rem; line-height:1.6; max-width:480px}

/* monitor panel with animated gauge */
.monitor{background:var(--glass-2); border:1px solid var(--line); border-radius:28px; padding:1.4rem 1.5rem;
  backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); box-shadow:0 20px 60px rgba(0,0,0,.35);
  animation:fadeUp .9s ease both, float 7s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)}}
.gauge{display:flex; justify-content:center; position:relative; margin:.4rem 0 .2rem}
.gauge svg circle.arc{stroke-dasharray:0 999; animation:fill 2.2s cubic-bezier(.2,.8,.2,1) .3s forwards}
@keyframes fill{to{stroke-dasharray:var(--v) 999}}
.gauge .center{position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center}
.gauge .pct{font-family:'Space Grotesk'; font-size:3rem; font-weight:700}
.gauge .cap{font-size:.65rem; letter-spacing:.18em; color:var(--muted)}
.spark{width:100%; height:60px}
.spark path.line{stroke-dasharray:1200; stroke-dashoffset:1200; animation:draw 3s ease forwards .5s}
@keyframes draw{to{stroke-dashoffset:0}}
.chips{display:flex; gap:.5rem; flex-wrap:wrap; margin-top:.6rem}
.chip{font-size:.7rem; letter-spacing:.1em; padding:.25rem .6rem; border-radius:999px; border:1px solid var(--line); color:var(--muted)}

.strip{border-left:1px solid var(--line); padding-left:1rem; display:flex; flex-direction:column; gap:2.2rem; text-align:center}
.strip .n{font-family:'Space Grotesk'; font-size:1.55rem; font-weight:600}
.strip .l{font-size:.6rem; letter-spacing:.16em; color:var(--muted)}
.strip .ic{width:30px; height:30px; margin:0 auto .3rem; border-radius:50%; border:1px solid var(--line);
  display:flex; align-items:center; justify-content:center; font-size:.85rem; background:var(--glass)}

.scale{display:flex; border-radius:12px; overflow:hidden; margin:.4rem 0 1rem}
.scale div{flex:1; padding:.55rem .3rem; text-align:center; font-size:.72rem; color:#081418; font-weight:600}
.scale div small{display:block; font-weight:400; opacity:.8}

/* ================= BUTTONS ================= */
.stButton > button{border-radius:999px; border:1px solid var(--line); background:var(--glass);
  color:var(--text); padding:.6rem 1.4rem; transition:all .25s; backdrop-filter:blur(12px)}
.stButton > button p{font-weight:600; letter-spacing:.08em}
.stButton > button:hover{border-color:var(--mint); color:var(--mint); box-shadow:0 0 22px rgba(134,239,172,.3); transform:translateY(-2px)}
.stButton > button[kind="primary"]{background:#f3fbf6; border-color:#f3fbf6}
.stButton > button[kind="primary"], .stButton > button[kind="primary"] p{color:#06140e !important}
.stButton > button[kind="primary"]:hover{background:var(--mint); border-color:var(--mint)}

/* ================= WIDGETS ================= */
[data-testid="stSidebar"]{background:rgba(5,16,12,.78); border-right:1px solid var(--line); backdrop-filter:blur(18px)}
[data-testid="stMetric"]{background:var(--glass); border:1px solid var(--line); border-radius:18px; padding:.9rem 1rem; backdrop-filter:blur(14px)}
[data-testid="stMetricValue"]{font-family:'Space Grotesk'}
[data-testid="stDataFrame"]{border-radius:14px; overflow:hidden}
.stTabs [data-baseweb="tab-list"]{gap:.4rem; flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{background:var(--glass); border-radius:999px; padding:.35rem 1rem; border:1px solid var(--line); backdrop-filter:blur(12px)}
.stTabs [aria-selected="true"]{border-color:var(--mint) !important; color:var(--mint) !important}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{display:none}
[data-testid="stExpander"]{background:var(--glass); border-radius:16px}

.alert{border-radius:22px; padding:1.4rem 1.5rem; border:1px solid; animation:fadeUp .5s ease both; backdrop-filter:blur(16px)}
.alert .t{font-family:'Space Grotesk'; font-size:1.6rem; font-weight:700}

@media (max-width: 900px){
  .hero{grid-template-columns:1fr} .headline{font-size:3.2rem}
  .strip{flex-direction:row; border-left:none; justify-content:space-around}
  .page-title{font-size:2.2rem}
}
</style>
"""

# Drawn hills, used only if assets/wallpaper.jpg is missing
_HILLS_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 900' preserveAspectRatio='xMidYMid slice'>
<defs><linearGradient id='s' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#cfd8d3'/><stop offset='1' stop-color='#6f8a7c'/></linearGradient></defs>
<rect width='1600' height='900' fill='url(#s)'/>
<path d='M0 420 Q250 300 520 380 T1050 340 T1600 360 V900 H0Z' fill='#56735f' opacity='.55'/>
<path d='M0 540 Q300 420 640 500 T1250 470 T1600 500 V900 H0Z' fill='#3d5e45' opacity='.75'/>
<path d='M0 650 Q350 540 760 620 T1600 600 V900 H0Z' fill='#2c4a32'/>
<path d='M0 780 Q420 690 900 760 T1600 740 V900 H0Z' fill='#1b3321'/></svg>"""


def background_html():
    """The fixed moving wallpaper: photo (or drawn hills) + 3 drifting mist layers + dark veil."""
    if WALLPAPER.exists():
        img = "data:image/jpeg;base64," + base64.b64encode(WALLPAPER.read_bytes()).decode()
    else:
        img = "data:image/svg+xml;base64," + base64.b64encode(_HILLS_SVG.encode()).decode()
    return (f'<div class="wall" style="background-image:url({img})"></div>'
            '<div class="mist m1"></div><div class="mist m2"></div><div class="mist m3"></div>'
            '<div class="veil"></div>' + particles_html())


def particles_html(n=30):
    """Little glowing mist droplets that drift up the screen."""
    random.seed(3)
    spans = []
    for _ in range(n):
        size = random.uniform(1.5, 4.5)
        spans.append(
            f'<span style="left:{random.uniform(0, 100):.1f}%; width:{size:.1f}px; height:{size:.1f}px;'
            f' animation-duration:{random.uniform(14, 34):.1f}s; animation-delay:-{random.uniform(0, 30):.1f}s"></span>')
    return '<div class="particles">' + "".join(spans) + "</div>"
