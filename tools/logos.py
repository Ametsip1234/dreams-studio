import math, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
R = sys.argv[1]

def text_path(fontfile, text, x, baseline, size, tracking=0, idx=None):
    f = TTFont(fontfile, fontNumber=idx) if idx is not None else TTFont(fontfile)
    gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f['head'].unitsPerEm
    s = size/upm; out=[]; cx=x
    for ch in text:
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen,(s,0,0,-s,cx,baseline)))
        out.append(pen.getCommands())
        cx += gs[g].width*s + tracking
    return ' '.join(out), cx

def bounds(fontfile, text, size):
    f=TTFont(fontfile); gs=f.getGlyphSet(); cmap=f.getBestCmap(); upm=f['head'].unitsPerEm
    bp=BoundsPen(gs); gs[cmap[ord(text)]].draw(bp); return [v*size/upm for v in bp.bounds], gs[cmap[ord(text)]].width*size/upm

BLACK=f'{R}/f/InterDisplay-Black.otf'
JP='/usr/share/fonts/truetype/fonts-japanese-gothic.ttf'

# ---------- Logotipo Liminal 8 (2000 x 926, como el original), para fondo oscuro ----------
W,H=2000,926
kata,_ = text_path(JP,'リミナル',378,430,212,tracking=-10)
lat,lend = text_path(BLACK,"Liminal",356,710,252,tracking=-12)
(b8,bw8)=bounds(BLACK,'8',1000)
k8=500/(b8[3]-b8[1]); x8=1582-b8[0]*k8
eight,_ = text_path(BLACK,'8',x8,725+b8[1]*k8,1000*k8)

# columna de azulejos
cx0,cw,ct,cb,ry=1232,302,118,842,24
col=[f'<path d="M{cx0} {ct} V{cb} A{cw/2} {ry} 0 0 0 {cx0+cw} {cb} V{ct}" class="cf"/>',
     f'<ellipse cx="{cx0+cw/2}" cy="{ct}" rx="{cw/2}" ry="{ry}" class="cf ct"/>']
for i in range(1,12):
    a=math.pi*i/12; x=cx0+cw/2-math.cos(a)*cw/2
    col.append(f'<line x1="{x:.1f}" y1="{ct+math.sin(a)*ry:.1f}" x2="{x:.1f}" y2="{cb+math.sin(a)*ry:.1f}" class="cl"/>')
y=ct+56
while y<cb:
    col.append(f'<path d="M{cx0} {y:.0f} A{cw/2} {ry} 0 0 0 {cx0+cw} {y:.0f}" class="cl"/>'); y+=57.5

chair = '''<g class="w lg-chair">
<rect x="143" y="248" width="20" height="440" rx="5"/><rect x="287" y="248" width="20" height="415" rx="5"/>
<rect x="150" y="262" width="150" height="32"/>
<rect x="176" y="298" width="15" height="122"/><rect x="203" y="298" width="15" height="122"/><rect x="230" y="298" width="15" height="122"/><rect x="257" y="298" width="15" height="122"/>
<rect x="150" y="418" width="150" height="22"/>
<path d="M66 500 L150 478 L300 486 L300 512 L240 522 L66 524 Z"/>
<rect x="66" y="505" width="24" height="186" rx="6"/><rect x="220" y="512" width="24" height="196" rx="6"/>
<path d="M90 586 L143 566 L143 582 L90 604 Z"/><path d="M244 600 L287 578 L287 594 L244 616 Z"/>
</g>'''

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="40 80 1920 800" role="img" aria-label="Liminal 8">
<style>.w,.w *{{fill:var(--lg-fg,#f7f6f1)}}.k{{fill:var(--lg-fg,#f7f6f1);stroke:var(--lg-fg,#f7f6f1);stroke-width:9;stroke-linejoin:round}}.cf{{fill:var(--lg-colf,rgba(124,194,240,.22));stroke:var(--lg-col,#a9d8f7);stroke-width:5}}.ct{{fill:var(--lg-colt,rgba(124,194,240,.4))}}.cl{{fill:none;stroke:var(--lg-col,#a9d8f7);stroke-width:4;opacity:.75}}.e{{fill:var(--lg-8,#f6c90e)}}</style>
{chair}
<path class="k lg-kata" d="{kata}"/>
<path class="w lg-lat" d="{lat}"/>
<g class="lg-col">{''.join(col)}</g>
<path class="e lg-8" d="{eight}"/>
</svg>'''
open(f'{R}/img/logo-liminal.svg','w').write(svg)

# ---------- Icono "8" con una captura real de las Poolrooms dentro ----------
e2,_=None,None
(b,bw)=bounds(BLACK,'8',1000)
gw,gh=b[2]-b[0],b[3]-b[1]
sc=356/gh; ox=256-(b[0]+gw/2)*sc; base=256+ (b[1]+gh/2)*sc
p8,_=text_path(BLACK,'8',ox/sc*sc,base,1000*sc)
icon=f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 512 512">
<defs><clipPath id="c"><path d="{p8}"/></clipPath></defs>
<rect x="16" y="16" width="480" height="480" rx="92" fill="#ecba30"/>
<image href="POOL" x="-90" y="-10" width="1040" height="585" preserveAspectRatio="xMidYMid slice" clip-path="url(#c)"/>
</svg>'''
open(f'{R}/../icon-src.svg','w').write(icon)
print('ok', lend)
