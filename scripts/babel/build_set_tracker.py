"""Build the Babel Alpha Set tracker artifact (90-slot grid with tappable faces and a log).

State lives in series/2026-Q1/tracker-state.json ({"pilot": {"<number>": {"status", "note"}}, "log": [{"when", "what"}]}).
Usage: build_set_tracker.py [out.html]
"""
import base64, html, io, json, sys
from pathlib import Path
import yaml
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "series" / "2026-Q1" / "tracker" / "babel-alpha-set.html"
STATE = json.loads((REPO / "series/2026-Q1/tracker-state.json").read_text(encoding="utf-8"))
idx = {int(c["number"]): c for c in yaml.safe_load((REPO / "series/2026-Q1/cards_index.yml").read_text())["cards"]}
grammar = yaml.safe_load((REPO / "series/2026-Q1/slot-grammar.yml").read_text())["slots"]
slots = {s["number"]: s for s in grammar}

def esc(x): return html.escape(str(x or ""))

def thumb(path, width=300, quality=80):
    if not Path(path).exists(): return ""
    im = Image.open(path).convert("RGB"); im.thumbnail((width, width * 3 // 2))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def card_dir(n):
    hits = list((REPO / "series/2026-Q1/cards").glob(f"{n:03d}-*"))
    return hits[0] if hits else None

cells, built_legacy, pilot_done = [], 0, 0
for n in range(1, 91):
    if n in idx:
        c = idx[n]; d = card_dir(n)
        img = thumb(d / "outputs/card_1024x1536.png", 220) if d else ""
        hires = thumb(d / "outputs/card_1024x1536.png", 640, quality=72) if d else ""
        pilot = STATE["pilot"].get(str(n))
        if pilot:
            st, cls = pilot.get("status", "pilot"), {"pass": "ok", "fail": "fail"}.get(pilot.get("status"), "watch")
            if pilot.get("status") == "pass": pilot_done += 1
        elif n <= 31:
            st, cls = "legacy face", "watch"; built_legacy += 1
        else:
            st, cls = "built", "ok"
        word, typ, rar = c["word"], c["type"], c["rarity"]
        note = esc((STATE["pilot"].get(str(n)) or {}).get("note", ""))
    else:
        s = slots.get(n)
        word, typ, rar = (s or {}).get("word", "?"), (s or {}).get("type", ""), (s or {}).get("rarity", "")
        st, cls = ("pilot queued", "pending") if (s or {}).get("status") == "pilot" else ("planned", "pending")
        img, hires, note = "", "", ""
    imgtag = f'<img src="{img}" alt="#{n:03d} {esc(word)}" loading="lazy">' if img else '<div class="ph">not rendered</div>'
    fig = (f'<figure class="tap" data-full="{hires}" data-label="#{n:03d} {esc(word)}" tabindex="0" role="button" '
           f'aria-label="Enlarge #{n:03d} {esc(word)}">{imgtag}</figure>') if hires else f'<figure>{imgtag}</figure>'
    cells.append(f'''<div class="slot"><div class="slot-head"><span class="mono">#{n:03d}</span><span class="chip {cls}">{esc(st)}</span></div>
    {fig}<div class="slot-name">{esc(word)}</div><div class="meta mono">{esc(typ)} · {esc(rar)}</div>{f'<p class="note">{note}</p>' if note else ''}</div>''')

log_html = "".join(f'<li><span class="mono">{esc(e["when"])}</span>{esc(e["what"])}</li>' for e in reversed(STATE["log"]))
counts = f"{len(idx)} built ({built_legacy} on legacy faces) · {sum(1 for s in grammar if s['status']=='pilot')} pilot · {sum(1 for s in grammar if s['status']=='planned')} planned"

CSS = """
:root{--parch:#EFE4CC;--parch-2:#E6D8BA;--ink:#1B2233;--ink-2:#4A5163;--navy:#102030;--gold:#C0A060;--gold-2:#8E7437;--line:#CDB98C;--ok:#3F7A4E;--watch:#B8862B;--fail:#A6453B;--pend:#7A7F8C;--card:#F6EEDC;--chip-ink:#fff}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--parch:#0E1726;--parch-2:#15213A;--ink:#EADFC6;--ink-2:#B9AD92;--navy:#EADFC6;--gold:#C9AA63;--gold-2:#E2C888;--line:#3A4A6A;--ok:#6DBB82;--watch:#E0B05A;--fail:#E07A6C;--pend:#8F97A8;--card:#152238;--chip-ink:#0E1726}}
:root[data-theme="dark"]{--parch:#0E1726;--parch-2:#15213A;--ink:#EADFC6;--ink-2:#B9AD92;--navy:#EADFC6;--gold:#C9AA63;--gold-2:#E2C888;--line:#3A4A6A;--ok:#6DBB82;--watch:#E0B05A;--fail:#E07A6C;--pend:#8F97A8;--card:#152238;--chip-ink:#0E1726}
*{box-sizing:border-box}body{margin:0;background:var(--parch);color:var(--ink);font-family:"Spectral",Georgia,serif;font-size:17px;line-height:1.5}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.8em;font-variant-numeric:tabular-nums}
h1,h2{font-family:"Cinzel",Georgia,serif;font-weight:600;letter-spacing:.04em;margin:0;color:var(--navy)}
.wrap{max-width:1240px;margin:0 auto;padding:2.2rem 1.4rem 4rem}
.masthead{border-bottom:2px solid var(--gold);padding-bottom:1.2rem;margin-bottom:1.6rem;display:grid;gap:.5rem}
.eyebrow{font-family:"Cinzel",serif;font-size:.76rem;letter-spacing:.18em;text-transform:uppercase;color:var(--gold-2)}
.masthead p{margin:0;color:var(--ink-2);max-width:70ch}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:.7rem}
.slot{border:1px solid var(--line);background:var(--card);padding:.5rem;display:grid;gap:.3rem}
.slot-head{display:flex;justify-content:space-between;align-items:center}
.chip{font-family:"IBM Plex Mono",monospace;font-size:.62rem;text-transform:uppercase;padding:.12rem .4rem;border-radius:2px;color:var(--chip-ink)}
.chip.ok{background:var(--ok)}.chip.watch{background:var(--watch)}.chip.fail{background:var(--fail)}.chip.pending{background:var(--pend)}
figure{margin:0;aspect-ratio:2/3;background:var(--parch-2);display:grid;place-items:center;overflow:hidden}
figure img{width:100%;height:100%;object-fit:contain}.ph{color:var(--ink-2);font-style:italic;font-size:.8rem}
figure.tap{cursor:zoom-in}figure.tap:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.lb{position:fixed;inset:0;background:rgba(8,12,22,.88);display:none;place-items:center;z-index:50;padding:1rem}
.lb.open{display:grid}.lb-frame{max-width:min(94vw,760px);max-height:94vh;overflow:auto;display:grid;gap:.4rem;justify-items:center}
.lb-frame img{max-width:100%;height:auto;cursor:zoom-in;box-shadow:0 8px 40px rgba(0,0,0,.5)}
.lb-frame.zoomed img{max-width:none;width:1400px;cursor:zoom-out}
.lb-cap{color:#EADFC6;font-family:"IBM Plex Mono",monospace;font-size:.8rem;letter-spacing:.06em}
.lb-close{position:fixed;top:.8rem;right:1rem;background:none;border:none;color:#EADFC6;font-size:2rem;cursor:pointer;line-height:1}
.slot-name{font-family:"Cinzel",serif;font-size:.86rem;letter-spacing:.05em}
.meta{color:var(--ink-2)}.note{margin:0;font-size:.8rem}
.log{list-style:none;padding:0;margin:.6rem 0 0;display:grid;gap:.35rem}.log li{display:grid;grid-template-columns:7rem 1fr;gap:.8rem;font-size:.95rem}
section{margin-top:2.2rem}
@media (max-width:1000px){.grid{grid-template-columns:repeat(4,1fr)}}@media (max-width:640px){.grid{grid-template-columns:repeat(2,1fr)}}
"""
page = f'''<title>Babel Alpha Set</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&family=Spectral:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="masthead"><span class="eyebrow">Hypertext · 2026-Q1 · 90 Word Cards</span><h1>Babel Alpha Set</h1>
<p>Every slot of the Babel Alpha deck as it is planned, generated, gated, and approved. {esc(counts)}. Slot plan: series/2026-Q1/slot-grammar.yml; visual authority: the 20-template golden matrix. Legacy faces (#001–#031) keep their content and await regeneration against the matrix.</p></header>
<div class="grid">{"".join(cells)}</div>
<section><h2>Log</h2><ul class="log">{log_html}</ul></section>
</div>
<div class="lb" id="lb" aria-modal="true" role="dialog">
<button class="lb-close" id="lb-close" aria-label="Close">&times;</button>
<div class="lb-frame" id="lb-frame"><img id="lb-img" alt=""><div class="lb-cap" id="lb-cap"></div></div>
</div>
<script>
(function() {{
  var lb = document.getElementById('lb'), frame = document.getElementById('lb-frame'),
      img = document.getElementById('lb-img'), cap = document.getElementById('lb-cap');
  function open(fig) {{ img.src = fig.dataset.full; img.alt = fig.dataset.label; cap.textContent = fig.dataset.label; frame.classList.remove('zoomed'); lb.classList.add('open'); }}
  function close() {{ lb.classList.remove('open'); img.src = ''; }}
  document.querySelectorAll('figure.tap').forEach(function(fig) {{
    fig.addEventListener('click', function() {{ open(fig); }});
    fig.addEventListener('keydown', function(e) {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); open(fig); }} }});
  }});
  img.addEventListener('click', function(e) {{ e.stopPropagation(); frame.classList.toggle('zoomed'); }});
  lb.addEventListener('click', function(e) {{ if (e.target === lb || e.target === frame) close(); }});
  document.getElementById('lb-close').addEventListener('click', close);
  document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') close(); }});
}})();
</script>'''
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
