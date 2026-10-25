"""Minimal KiCad 7 schematic writer: places library symbols, connects every pin
by a 2.54 mm wire stub + net label, adds no-connect flags. Netlist-correct by construction."""
import re, uuid, math
LIBDIR='/usr/share/kicad/symbols'
_cache={}
def _extract(lib,name):
    key=(lib,name)
    if key in _cache: return _cache[key]
    if lib=='ParkFlow':
        txt=open(CUSTOM_LIB).read()
    else:
        txt=open(f'{LIBDIR}/{lib}.kicad_sym').read()
    start=txt.find(f'\n  (symbol "{name}"')
    assert start>=0,(lib,name)
    i=start+1; depth=0
    while True:
        c=txt[i]
        if c=='"':
            j=i+1
            while txt[j]!='"':
                if txt[j]=='\\': j+=1
                j+=1
            i=j
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0: break
        i+=1
    s=txt[start+1:i+1]
    assert '(extends' not in s.split('\n')[0], 'derived symbol not supported: '+name
    # pins
    pins=[]
    for m in re.finditer(r'\(pin (\w+) \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length [-\d.]+\)( hide)?\s*\(name "((?:[^"\\]|\\.)*)"[^\n]*\n?\s*\(number "([^"]+)"',s):
        pins.append(dict(type=m.group(1),x=float(m.group(2)),y=float(m.group(3)),ang=int(m.group(4)),name=m.group(6),num=m.group(7)))
    if not pins:
        for m in re.finditer(r'\(pin (\w+) \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(name "((?:[^"\\]|\\.)*)".*?\(number "([^"]+)"',s,re.S):
            pins.append(dict(type=m.group(1),x=float(m.group(2)),y=float(m.group(3)),ang=int(m.group(4)),name=m.group(5),num=m.group(6)))
    full=s.replace(f'(symbol "{name}"',f'(symbol "{lib}:{name}"',1)
    _cache[key]=(full,pins)
    return _cache[key]
CUSTOM_LIB=None
def U(): return str(uuid.uuid4())
def rot(px,py,r):
    a=math.radians(r); c=round(math.cos(a)); s=round(math.sin(a))
    return (px*c-py*s, px*s+py*c)
class Sch:
    def __init__(s,title,project):
        s.title=title; s.project=project; s.root=U(); s.items=[]; s.libs={}; s.comps=[]
    def add(s,lib,name,ref,value,at,nets,rot_=0,fp='',ds='~',extra=None,dnp=False):
        full,pins=_extract(lib,name); s.libs[f'{lib}:{name}']=full
        X,Y=at
        # snap the symbol origin to the 1.27 mm schematic grid so every pin / wire end lands on grid (ERC endpoint_off_grid)
        X=round(round(X/1.27)*1.27,2); Y=round(round(Y/1.27)*1.27,2)
        pinuuids=' '.join(f'(pin "{p["num"]}" (uuid {U()}))' for p in pins)
        props=[('Reference',ref),('Value',value),('Footprint',fp),('Datasheet',ds)]+list((extra or {}).items())
        pts=[rot(p['x'],p['y'],rot_) for p in pins]
        xs=[q[0] for q in pts] or [0]; ys=[-q[1] for q in pts] or [0]
        ptxt=''
        if lib=='power':
            pos={'Reference':(X,Y+5,'center'),'Value':(X,Y-4,'center')}
        elif len(pins)<=3 and max(xs)-min(xs)<1:   # vertical small part: text right
            pos={'Reference':(X+2.5,Y-1.0,'left'),'Value':(X+2.5,Y+1.6,'left')}
        elif len(pins)<=3 and max(ys)-min(ys)<1:   # horizontal small part: text above
            pos={'Reference':(X,Y-4.2,'center'),'Value':(X,Y-2.2,'center')}
        elif len(pins)<=4:
            pos={'Reference':(X+min(xs),Y+min(ys)-4.5,'left'),'Value':(X+min(xs),Y+min(ys)-2.5,'left')}
        else:
            pos={'Reference':(X+min(xs)+3,Y+min(ys)-6.5,'left'),'Value':(X+min(xs)+3,Y+min(ys)-4.0,'left')}
        for k,(pn,pv) in enumerate(props):
            if pn in pos:
                px_,py_,j=pos[pn]; jt='' if j=='center' else f' (justify {j})'
                ptxt+=f'    (property "{pn}" "{pv}" (at {px_:.2f} {py_:.2f} 0) (effects (font (size 1.27 1.27)){jt}))\n'
            else:
                ptxt+=f'    (property "{pn}" "{pv}" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        s.items.append(f'  (symbol (lib_id "{lib}:{name}") (at {X} {Y} {rot_}) (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid {U()})\n{ptxt}    {pinuuids}\n    (instances (project "{s.project}" (path "/{s.root}" (reference "{ref}") (unit 1))))\n  )')
        # connect pins
        done=set()
        for p in pins:
            key=(p['x'],p['y'])
            net=nets.get(p['num'], nets.get(p['name']))
            px,py=rot(p['x'],p['y'],rot_)
            sx,sy=X+px, Y-py
            a=(p['ang']+rot_)%360
            # outward direction = opposite of pin direction ; in y-up: pin dir (cos a, sin a)
            dx,dy=-round(math.cos(math.radians(a))),-round(math.sin(math.radians(a)))
            ex,ey=sx+2.54*dx, sy-2.54*dy
            if key in done: continue
            done.add(key)
            if net is None:
                raise ValueError(f'{ref} pin {p["num"]} {p["name"]} unassigned')
            if net=='NC':
                s.items.append(f'  (no_connect (at {sx:.2f} {sy:.2f}) (uuid {U()}))'); continue
            s.items.append(f'  (wire (pts (xy {sx:.2f} {sy:.2f}) (xy {ex:.2f} {ey:.2f})) (stroke (width 0) (type default)) (uuid {U()}))')
            if dx==1: ang,just=0,'left'
            elif dx==-1: ang,just=180,'right'
            elif dy==1: ang,just=90,'left'
            else: ang,just=270,'right'
            s.items.append(f'  (label "{net}" (at {ex:.2f} {ey:.2f} {ang}) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid {U()}))')
        s.comps.append((ref,value,lib,name,fp))
    def text(s,t,at,size=2.0):
        t=t.replace('"','\\"')
        s.items.append(f'  (text "{t}" (at {at[0]} {at[1]} 0) (effects (font (size {size} {size}) bold) (justify left bottom)) (uuid {U()}))')
    def note(s,t,at,size=1.27):
        t=t.replace('"','\\"').replace('\n','\\n')
        s.items.append(f'  (text "{t}" (at {at[0]} {at[1]} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {U()}))')
    def write(s,path,paper='A1',rev='A',date='2026-10-24',comments=()):
        libs='\n'.join('    '+v.replace('\n','\n  ') for v in s.libs.values())
        cm=''.join(f'    (comment {i+1} "{c}")\n' for i,c in enumerate(comments))
        out=f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {s.root})
  (paper "{paper}")
  (title_block
    (title "{s.title}")
    (date "{date}")
    (rev "{rev}")
    (company "ParkFlow - Vishwakarma Awards Stage 2")
{cm}  )
  (lib_symbols
{libs}
  )
''' + '\n'.join(s.items) + '''
  (sheet_instances (path "/" (page "1")))
)
'''
        open(path,'w').write(out)

def _box_symbol(name, ref, desc, w, pins):
    """pins: list of (num, pname, etype, side, offset) side in L,R,T,B"""
    h = max(sum(1 for p in pins if p[3] in 'LR' and p[3]=='L'), sum(1 for p in pins if p[3]=='R'), 2)*2.54+2.54
    H = 7.62
    out = [f'  (symbol "{name}" (in_bom yes) (on_board yes)',
           f'    (property "Reference" "{ref}" (at 0 {H+2.54} 0) (effects (font (size 1.27 1.27))))',
           f'    (property "Value" "{name}" (at 0 {-H-2.54} 0) (effects (font (size 1.27 1.27))))',
           '    (property "Footprint" "Package_TO_SOT_SMD:SOT-23-5" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tps3823.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "ki_description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (symbol "{name}_0_1"',
           f'      (rectangle (start {-w} {H}) (end {w} {-H}) (stroke (width 0.254) (type default)) (fill (type background)))',
           '    )',
           f'    (symbol "{name}_1_1"']
    for num, pn, et, side, off in pins:
        if side == 'L': x, y, a = -w-2.54, off, 0
        elif side == 'R': x, y, a = w+2.54, off, 180
        elif side == 'T': x, y, a = off, H+2.54, 270
        else: x, y, a = off, -H-2.54, 90
        out.append(f'      (pin {et} line (at {x} {y} {a}) (length 2.54) (name "{pn}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    out += ['    )', '  )']
    return '\n'.join(out)

def write_custom_lib(path):
    sym = _box_symbol('TPS3823-33', 'U', 'Supervisor 2.93V with 1.6 s watchdog, push-pull RESET#, SOT-23-5', 7.62,
        [('1', '~{RESET}', 'output', 'R', 0), ('2', 'GND', 'power_in', 'B', 0), ('3', '~{MR}', 'input', 'L', 2.54),
         ('4', 'WDI', 'input', 'L', -2.54), ('5', 'VDD', 'power_in', 'T', 0)])
    open(path, 'w').write('(kicad_symbol_lib (version 20220914) (generator parkflow_gen)\n' + sym + '\n)\n')
    _cache.pop(('ParkFlow', 'TPS3823-33'), None)
