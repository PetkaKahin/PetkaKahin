#!/usr/bin/env python3
"""Generate GitHub-native SVG panels and the README from profile.json.

Requires python3-cairo and installed Rajdhani/Play fonts to rebuild artwork.
Ready-made SVGs need no fonts or dependencies. Animations are self-contained
CSS inside SVG images; README interaction uses native links.
"""
from html import escape
from datetime import date
import json
import math
from pathlib import Path
import cairo

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'profile.json').read_text())
BG, SURFACE, RED, WHITE, MUTED, BORDER = '#0a0608', '#150c10', '#d9182e', '#f4efe6', '#a3969b', '#522028'
GUTTER_DESKTOP, GUTTER_MOBILE = (40, 24), (24, 18)
ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
MOTION = '''<style>
.packet{stroke-dasharray:12 388;animation:transmit 7s linear infinite}
.led{animation:signal 4s steps(1,end) infinite}
.trace{animation:trace 6s ease-in-out infinite}
.wire{stroke-dasharray:16 224;animation:wire 5s linear infinite}
.wire-reverse{stroke-dasharray:10 230;animation:wire 8s linear infinite reverse}
.node-late{animation:signal 5s steps(1,end) 1.4s infinite}
@keyframes transmit{to{stroke-dashoffset:-400}}
@keyframes signal{0%,85%,100%{opacity:1}90%,95%{opacity:.35}}
@keyframes trace{0%,100%{opacity:.25}50%{opacity:.8}}
@keyframes wire{to{stroke-dashoffset:-240}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
</style>'''


def typepath(text, x, y, size, color=WHITE, font='Rajdhani', bold=True):
    ctx.new_path()
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ctx.move_to(0, 0)
    ctx.text_path(text)
    parts = []
    for kind, points in ctx.copy_path():
        command = {cairo.PATH_MOVE_TO: 'M', cairo.PATH_LINE_TO: 'L', cairo.PATH_CURVE_TO: 'C', cairo.PATH_CLOSE_PATH: 'Z'}[kind]
        parts.append(command + ' '.join(f'{p:.2f}'.rstrip('0').rstrip('.') for p in points))
    ctx.new_path()
    return f'<path aria-label="{escape(text, quote=True)}" fill="{color}" transform="translate({x} {y})" d="{"".join(parts)}"/>'


def label(text, x, y, size=12, color=MUTED, spacing=1, anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Consolas,DejaVu Sans Mono,monospace" font-size="{size}" letter-spacing="{spacing}" text-anchor="{anchor}">{escape(text)}</text>'


def path(d, color=RED, width=1, fill='none', extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}" {extra}/>'


def rect(x, y, w, h, fill, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


def save(name, w, h, title, body, desc='', gutter=True):
    # Padding belongs to the image itself, so GitHub's page colour cannot
    # show through the spaces between panels. All slices share one canvas.
    if gutter:
        horizontal, vertical = GUTTER_MOBILE if w == 640 else GUTTER_DESKTOP
        body = [rect(0, 0, w+2*horizontal, h+2*vertical, BG),
                f'<g transform="translate({horizontal} {vertical})">', *body, '</g>']
        w, h = w+2*horizontal, h+2*vertical
    dest = ROOT / 'assets' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">\n'
                    f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc or title)}</desc>\n'
                    + MOTION + '\n' + '\n'.join(body) + '\n</svg>\n')


def shell(w, h):
    return [rect(0, 0, w, h, BG), path(f'M18 0H{w-18}L{w} 18V{h}H0V18Z', BORDER), rect(0, 18, 4, h-18, RED)]


def heading(b, w, num, title):
    b += [rect(24, 26, 38, 28, RED), label(num, 33, 45, 13, WHITE, .5), typepath(title, 78, 50, 31),
          path(f'M430 40H{w-28}', BORDER), rect(w-32, 60, 5, 5, RED, 'class="led"')]


def key(x, y, scale=1):
    return (f'<g transform="translate({x} {y}) scale({scale}) rotate(-38 135 100)">'
            + path('M34 26H108L140 58V132L108 164H34L2 132V58Z', WHITE, 13)
            + path('M52 70H90V108H52Z', WHITE, 10)
            + path('M143 95H260V120H233V151H205V120H178', WHITE, 16) + '</g>')


def technical_motif(kind, x, y, scale=1):
    """Decorative circuit illustrations; none encode activity or skill levels."""
    b = [f'<g transform="translate({x} {y}) scale({scale})" aria-hidden="true">']
    if kind == 'redis':
        # Three cache layers, a branched inlet and two return traces.
        b += [path('M20 66H66L91 41H147M66 66L91 91H147', BORDER, 1.5),
              path('M20 66H66L91 41H147', RED, 1.8, extra='class="wire"'),
              rect(14, 60, 12, 12, RED), rect(140, 36, 8, 8, BG, f'stroke="{RED}"')]
        for cy in (35, 57, 79):
            b += [path(f'M157 {cy}L201 {cy-17}L245 {cy}L201 {cy+17}Z', RED if cy == 57 else BORDER, 1.5)]
        b += [path('M247 57H268V20H280M247 79H269V111H280', BORDER),
              rect(277, 16, 8, 8, BG, f'stroke="{RED}"'), rect(277, 107, 8, 8, RED, 'class="node-late"')]
    elif kind == 'tasks':
        # A kanban board: three rails with different card arrangements.
        for col, heights in enumerate(((24, 14), (15, 32), (39,))):
            ox = 28+col*88
            b += [rect(ox, 14, 54, 4, RED if col == 1 else BORDER), path(f'M{ox} 26V102H{ox+54}V26Z', BORDER)]
            cy = 34
            for j, height in enumerate(heights):
                b += [rect(ox+8, cy, 38, height, SURFACE, f'stroke="{RED if col == 1 and j == 0 else BORDER}"')]
                cy += height+8
        b += [path('M55 105V122H232V108', BORDER, 1.5), path('M55 105V122H232V108', RED, 1.5, extra='class="wire-reverse"'),
              rect(51, 106, 8, 8, RED), path('M226 112L232 106L238 112', RED, 1.5)]
    elif kind == 'docker':
        # Three separate containers joined by a shared bus.
        for cx, cy in ((45, 31), (140, 47), (235, 31)):
            b += [path(f'M{cx-30} {cy}L{cx} {cy-16}L{cx+30} {cy}V{cy+35}L{cx} {cy+51}L{cx-30} {cy+35}Z', BORDER, 1.5),
                  path(f'M{cx-30} {cy}L{cx} {cy+16}L{cx+30} {cy}M{cx} {cy+16}V{cy+51}', RED, 1.4),
                  path(f'M{cx} {cy+54}V116', BORDER)]
        b += [path('M24 116H257', BORDER, 1.5), path('M24 116H257', RED, 1.8, extra='class="wire"'),
              rect(20, 112, 8, 8, RED), rect(254, 112, 8, 8, BG, f'stroke="{RED}"')]
    elif kind == 'cyberpunk':
        # A roleplaying hub with four angular satellite nodes.
        b += [path('M35 23H72L108 52M245 23H209L172 52M35 108H72L108 78M245 108H209L172 78', BORDER, 1.5),
              path('M35 23H72L108 52', RED, 1.8, extra='class="wire"'),
              path('M245 108H209L172 78', RED, 1.5, extra='class="wire-reverse"'),
              path('M140 27L174 46V84L140 103L106 84V46Z', RED, 1.5),
              path('M140 38L163 52V78L140 91L117 78V52Z', BORDER),
              typepath('R', 126, 80, 42, RED)]
        for nx, ny in ((35, 23), (245, 23), (35, 108), (245, 108)):
            b += [path(f'M{nx-11} {ny-7}L{nx-4} {ny-14}H{nx+11}V{ny+7}L{nx+4} {ny+14}H{nx-11}Z', RED if nx == 35 else BORDER)]
        b += [rect(242, 20, 6, 6, RED, 'class="node-late"')]
    elif kind == 'backend':
        b += [path('M16 64H72L101 35H181L211 64H269M72 64L101 94H181L211 64', BORDER, 1.5),
              path('M16 64H72L101 35H181L211 64H269', RED, 1.7, extra='class="wire"'),
              rect(10, 58, 12, 12, RED), rect(130, 23, 25, 25, BG, f'stroke="{RED}"'),
              rect(130, 81, 25, 25, BG, f'stroke="{BORDER}"'), path('M142 50V78', BORDER),
              rect(264, 59, 10, 10, BG, f'stroke="{RED}"')]
    elif kind == 'frontend':
        b += [path('M21 16H214L228 30V108H21Z', BORDER, 1.5), path('M21 37H228', BORDER),
              rect(33, 25, 6, 4, RED), rect(45, 25, 6, 4, BORDER), rect(57, 25, 6, 4, BORDER),
              path('M62 53L45 70L62 87M106 53L123 70L106 87M91 48L77 92', RED, 1.5),
              path('M143 57H205M143 70H184M143 83H199', BORDER),
              path('M214 56H265L274 65V120H214Z', RED, 1.2), path('M224 69H263M224 78H250M224 87H258', BORDER),
              path('M143 57H205', RED, 1.5, extra='class="wire"')]
    elif kind == 'infra':
        for cy in (20, 54, 88):
            b += [path(f'M43 {cy}H196L207 {cy+11}V{cy+24}H43Z', BORDER, 1.5),
                  rect(55, cy+9, 7, 7, RED, 'class="node-late"' if cy == 54 else ''),
                  path(f'M78 {cy+12}H137M158 {cy+8}V{cy+17}M169 {cy+8}V{cy+17}M180 {cy+8}V{cy+17}', BORDER)]
        b += [path('M28 32H15V100H28M212 32H256V100H212', RED, 1.3),
              path('M212 32H256V100H212', RED, 1.5, extra='class="wire-reverse"'), rect(251, 61, 10, 10, BG, f'stroke="{RED}"')]
    else:
        # Offset index rails; also used as a quiet footer signature.
        for i in range(4):
            ox, oy = 16+i*64, 26+i*18
            b += [rect(ox, oy, 8, 8, RED if i in (0, 3) else BG, f'stroke="{RED}"'),
                  path(f'M{ox+9} {oy+4}H{ox+35}L{ox+52} {oy+21}H{ox+61}', BORDER, 1.4)]
        b += [path('M25 30H51L68 47H77', RED, 1.5, extra='class="wire"')]
    b += ['</g>']
    return b


def header(mobile):
    w, h = (640, 550) if mobile else (1200, 460)
    b = shell(w, h) + [label('PERSONNEL FILE / SG', 32, 34, 12, RED), label('BACKEND / WEB SYSTEMS', w-32, 34, 11, anchor='end'), path(f'M32 52H{w-32}', BORDER)]
    b += [rect(32, 77, 190, 25, RED), label('BACKEND DEVELOPER', 43, 94, 11, WHITE, 1.2)]
    if mobile:
        b += [typepath('STANISLAV', 28, 191, 116), typepath('GRADOV', 28, 285, 136),
              typepath(DATA['name'], 34, 330, 25, WHITE, 'Play', False), path('M34 355H606', BORDER),
              label('PHP / LARAVEL', 34, 398, 19, WHITE, .5), label('LINUX / DOCKER', 34, 432, 15),
              path('M466 375H583L607 399V500H466Z', RED, 0, RED), key(474, 394, .41),
              path('M34 480H430', BORDER), label('BUILD. BREAK. UNDERSTAND.', 34, 520, 13, MUTED, .6)]
    else:
        b += [typepath('STANISLAV', 27, 207, 138), typepath('GRADOV', 27, 317, 154),
              label('PHP / LARAVEL / WEB SYSTEMS', 36, 358, 16, WHITE, .8), typepath(DATA['name'], 36, 395, 20, MUTED, 'Play', False),
              path('M797 77H1136L1166 107V354L1136 384H797Z', RED, 0, RED),
              label('SYSTEMS / ENGINEERING', 818, 105, 11, WHITE, .8), path('M818 118H1144', WHITE, 1, extra='opacity=".3"'),
              key(853, 143, .83), label('NO LOCK IS A DEAD END.', 818, 361, 12, WHITE), path('M755 77V384', BORDER),
              path('M34 417H1166', BORDER), label('01 / BACKEND DEVELOPMENT', 36, 444, 11, WHITE, .4),
              label('02 / LINUX & INFRASTRUCTURE', 434, 444, 11, MUTED, .4), label('03 / WEB APPLICATIONS', 926, 444, 11, MUTED, .4)]
    b += [path(f'M32 52H{w-32}', RED, 1.5, extra='class="packet"')]
    save('header-mobile.svg' if mobile else 'header.svg', w, h, f"{DATA['name']} — PHP / Laravel developer", b)


for mobile in (False, True):
    header(mobile)

for i, (name, num, text) in enumerate([('stack', '01', 'TECH INVENTORY'), ('projects', '02', 'SELECTED WORK'), ('stats', '03', 'TELEMETRY')]):
    for mobile in (False, True):
        inset, top = GUTTER_MOBILE if mobile else GUTTER_DESKTOP
        width = ((640 if mobile else 1200)+2*inset)/3
        height = (54 if mobile else 76)+2*top
        left = inset if i == 0 else (8 if mobile else 12)
        right = inset if i == 2 else (8 if mobile else 12)
        inner = width-left-right
        b = [rect(0, 0, width, height, BG), f'<g transform="translate({left} {top})">',
             path(f'M0 0H{inner-15}L{inner} 15V{height-2*top}H0Z', BORDER, 1, BG),
             label(num, 12, 34 if mobile else 45, 12 if mobile else 18, RED),
             typepath({'stack':'STACK', 'projects':'PROJECTS', 'stats':'STATS'}[name] if mobile else text,
                      37 if mobile else 50, 35 if mobile else 47, 24 if mobile else 28)]
        if not mobile:
            b += [path(f'M{inner-24} 30V48M{inner-33} 39L{inner-24} 48L{inner-15} 39', RED, 2)]
        b += ['</g>']
        save(f'nav-{name}{"-mobile" if mobile else ""}.svg', width, height, f'{num} / {text}', b, gutter=False)

for mobile in (False, True):
    w, h = (640, 740) if mobile else (1200, 370)
    b = shell(w, h)
    heading(b, w, '01', 'TECH INVENTORY')
    for i, group in enumerate(DATA['stack']):
        x, y = (36, 112+i*224) if mobile else (38+i*400, 118)
        b += [label(f'{i+1:02} / {group["name"]}', x, y, 13, RED, .6), typepath(group['primary'], x, y+48, 31),
              typepath(' · '.join(group['items'][2:]), x, y+82, 19 if mobile else 17, MUTED, 'Play', False),
              path(f'M{x} {y+110}H{x+(260 if mobile else 310)}', BORDER)]
        b += technical_motif(('backend', 'frontend', 'infra')[i], 350 if mobile else x+15, y+27 if mobile else 245, .75)
        if not mobile and i:
            b += [path(f'M{x-22} 104V342', BORDER)]
    save('stack-mobile.svg' if mobile else 'stack.svg', w, h, 'Стек: '+', '.join(s for g in DATA['stack'] for s in g['items']), b)

for mobile in (False, True):
    w = 640 if mobile else 1200
    b = shell(w, 104)
    heading(b, w, '02', 'SELECTED WORK')
    b += [label('PROJECT INDEX / 004', 28, 83, 12, MUTED, .7)]
    b += technical_motif('index', w-245, 1, .65)
    save('projects-mobile.svg' if mobile else 'projects.svg', w, 104, '02 / Selected work', b)

for i, project in enumerate(DATA['projects']):
    for mobile in (False, True):
        w, h = (640, 430) if mobile else (1200, 340)
        b = shell(w, h)
        b += [label(f'PROJECT / {i+1:02}', 36, 38, 13, RED, .7),
              label(project['kind'], w-36, 38, 11, MUTED, .7, 'end'),
              typepath(project['title'], 34, 103, 35 if mobile else 43)]
        for j, line in enumerate(project['description']):
            b += [typepath(line, 36, 154+j*34, 23 if mobile else 24, MUTED, 'Play', False)]
        x = 36
        for tag in project['tags']:
            tw = len(tag)*10+24
            b += [rect(x, 220, tw, 30, '#1f0f15', f'stroke="{BORDER}"'), label(tag, x+12, 240, 15, WHITE, 0)]
            x += tw+10
        cta = 'ПЕРЕЙТИ НА САЙТ' if project['slug'] == 'cyberpunk' else 'ОТКРЫТЬ РЕПОЗИТОРИЙ'
        b += [label(' / '.join(project['flow']), 36, 290 if mobile else 300, 16 if mobile else 15, MUTED, .6)]
        b += technical_motif(project['slug'], 366 if mobile else 844, 258 if mobile else 105, .8 if mobile else 1)
        if mobile:
            b += [path('M36 358H604', BORDER), typepath(cta, 36, 402, 23, RED, 'Play', False),
                  path('M570 382H592V404M592 382L570 404', RED, 2)]
        else:
            b += [typepath(cta, 770, 300, 22, RED, 'Play', False), path('M1131 280H1153V302M1153 280L1131 302', RED, 2)]
        save(f'projects/{project["slug"]}-{"mobile" if mobile else "wide"}.svg', w, h,
             f'{project["title"]}: '+ ' '.join(project['description'])+' '+cta+'.', b)

for mobile in (False, True):
    w, h = (640, 560) if mobile else (1200, 370)
    b = shell(w, h)
    heading(b, w, '03', 'TELEMETRY')
    metrics = [(DATA['public_repositories'], 'PUBLIC REPOSITORIES'), (len(DATA['projects']), 'SELECTED PROJECTS'),
               (len({s for g in DATA['stack'] for s in g['items']}), 'TECHNOLOGIES'), (len(DATA['stack']), 'STACK DOMAINS')]
    for i, (value, title) in enumerate(metrics):
        x, y = (36+(i%2)*310, 156+(i//2)*180) if mobile else (38+i*300, 164)
        b += [typepath(f'{value:02}', x, y, 88 if mobile else 86), label(title, x+2, y+32, 13, MUTED, .5),
              path(f'M{x} {y+54}H{x+245}', BORDER), rect(x, y+52, 28, 3, RED)]
        b += technical_motif(('backend', 'frontend', 'infra', 'index')[i], x+5, y+66, .35 if mobile else .45)
    b += [path(f'M28 {h-55}H{w-28}', BORDER), label('SNAPSHOT / '+DATA['statistics_date'], 30, h-25, 12, RED, .6),
          label('PUBLIC DATA ONLY', w-30, h-25, 12, MUTED, .6, 'end')]
    save('stats-mobile.svg' if mobile else 'stats.svg', w, h, 'Статистика: '+', '.join(f'{v} {t.lower()}' for v,t in metrics)+'. Снимок на '+DATA['statistics_date'], b)

# Both charts are computed from an actual public GitHub calendar snapshot.
ACTIVITY = json.loads((ROOT/'activity.json').read_text())
days = ACTIVITY['days']
total = sum(day['count'] for day in days)
active = sum(day['count'] > 0 for day in days)
max_count = max(day['count'] for day in days)
streak = best_streak = 0
for day in days:
    streak = streak+1 if day['count'] else 0
    best_streak = max(best_streak, streak)

for mobile in (False, True):
    w, h = (640, 650) if mobile else (1200, 536)
    b = shell(w, h)
    heading(b, w, '04', 'ACTIVITY TRACE')
    b += [label(ACTIVITY['from']+' / '+ACTIVITY['to'], 28, 91, 13, MUTED, .4)]
    # Draw far rows first, using the same scale for every date.
    offset = (date.fromisoformat(days[0]['date']).weekday()+1) % 7
    scale = .54 if mobile else 1
    ox, oy = (33, 237) if mobile else (60, 265)
    palette = ['#241019', '#6b1524', '#a91a2e', '#d9182e', '#ff475a']
    draw_order = sorted(enumerate(days), key=lambda item: ((offset+item[0]) % 7)*9-((offset+item[0])//7)*1.4)
    for i, day in draw_order:
        col, row = divmod(offset+i, 7)
        x, y = ox+(col*19+row*10)*scale, oy+(-col*1.4+row*9)*scale
        height = (2+64*math.sqrt(day['count']/max_count)) * scale if max_count else 2*scale
        dx, dy, rx, ry = 15*scale, -1.1*scale, 7*scale, 6*scale
        color = palette[day['level']]
        cube = [path(f'M{x+rx} {y+ry-height}l{dx} {dy}v{height}l{-dx} {-dy}Z', '#6c1726', .4, '#571322'),
                path(f'M{x} {y-height}v{height}l{rx} {ry}v{-height}Z', '#5d1522', .4, '#3a0b16'),
                path(f'M{x} {y-height}l{dx} {dy}l{rx} {ry}l{-dx} {-dy}Z', color, .5, color)]
        b += [f'<g><title>{day["date"]}: {day["count"]} contributions</title>'+''.join(cube)+'</g>']
    # A restrained scanning edge runs under the entire chart.
    line_y = 324 if mobile else 361
    b += [path(f'M28 {line_y}H{w-28}', BORDER), path(f'M28 {line_y}H{w-28}', RED, 1.5, extra='class="packet"')]
    metrics = [(total, 'CONTRIBUTIONS'), (active, 'ACTIVE DAYS'), (best_streak, 'BEST STREAK / DAYS')]
    for i, (value, title) in enumerate(metrics):
        if mobile:
            x, y = 28+(i%2)*310, 392+(i//2)*125
        else:
            x, y = 30+i*400, 433
        b += [typepath(str(value), x, y, 65), label(title, x+2, y+32, 13, MUTED, .4)]
    b += [label('GITHUB CALENDAR / SNAPSHOT '+ACTIVITY['to'], 28, h-26, 12, RED, .4)]
    save('activity-mobile.svg' if mobile else 'activity.svg', w, h,
         f'Карта активности: {total} contributions, {active} активных дней, максимальная серия {best_streak} дней. '+ACTIVITY['from']+' — '+ACTIVITY['to'], b)

    w, h = (640, 380) if mobile else (1200, 340)
    b = shell(w, h) + [typepath('LAST 30 DAYS', 28, 47, 31), label('DAILY CONTRIBUTIONS', w-28, 43, 11, MUTED, .4, 'end')]
    recent = days[-30:]
    peak = max(day['count'] for day in recent) or 1
    left, right, top, bottom = 60, w-35, 100, h-100
    for tick in range(4):
        y = bottom-(bottom-top)*tick/3
        b += [path(f'M{left} {y}H{right}', BORDER), label(str(round(peak*tick/3)), left-12, y+5, 12, MUTED, 0, 'end')]
    points = [(left+i*(right-left)/29, bottom-day['count']/peak*(bottom-top)) for i, day in enumerate(recent)]
    line = 'M'+'L'.join(f'{x:.2f} {y:.2f}' for x,y in points)
    b += [path(line+f'L{right} {bottom}H{left}Z', 'none', 0, '#38101b'), path(line, RED, 2.5)]
    for x,y in points:
        b += [rect(x-2, y-2, 4, 4, WHITE)]
    b += [label(recent[0]['date'], left, bottom+27, 12, MUTED, .4), label(recent[-1]['date'], right, bottom+27, 12, MUTED, .4, 'end'),
          label('SOURCE / GITHUB CONTRIBUTION CALENDAR', 28, h-25, 11, RED, .4)]
    save('timeline-mobile.svg' if mobile else 'timeline.svg', w, h,
         f'Дневная активность GitHub за 30 дней: {recent[0]["date"]} — {recent[-1]["date"]}. Сумма {sum(day["count"] for day in recent)} contributions.', b)

for mobile in (False, True):
    w, h = (640, 142) if mobile else (1200, 134)
    b = shell(w, h) + [typepath('BUILD SYSTEMS. PICK LOCKS.', 26, 62, 34 if mobile else 38),
        label('PHP / LARAVEL / WEB SYSTEMS', 28, 101, 12, MUTED, .5), label('EOF / 001', w-28, h-15, 11, RED, anchor='end'),
        path(f'M28 {h-20}H{w-180}', BORDER), path(f'M28 {h-20}H{w-180}', RED, 1.5, extra='class="packet"')]
    if not mobile:
        b += technical_motif('index', 860, 10, .6)
    save('footer-mobile.svg' if mobile else 'footer.svg', w, h, 'Build systems. Pick locks.', b)


def picture(name, alt, width='100%'):
    return f'<picture><source media="(max-width: 640px)" srcset="./assets/{name}-mobile.svg" /><img src="./assets/{name}.svg" width="{width}" align="top" alt="{escape(alt, quote=True)}" /></picture>'


readme = [picture('header', DATA['name']+' / PHP · Laravel · Web systems')]
for section, title in [('stack', 'Стек'), ('projects', 'Проекты'), ('stats', 'Статистика')]:
    readme += [f'<a href="#{section}">'+picture(f'nav-{section}', f'{title} ↓', '33.333%')+'</a>']
readme += ['<a name="stack"></a>', picture('stack', 'Стек: '+', '.join(s for g in DATA['stack'] for s in g['items'])),
           '<a name="projects"></a>', picture('projects', '02 / Проекты. Карточки ведут на репозитории и сайт проекта.')]
for project in DATA['projects']:
    slug, url = project['slug'], project['url']
    readme += [f'<a href="{escape(url, quote=True)}">',
               f'<picture><source media="(max-width: 640px)" srcset="./assets/projects/{slug}-mobile.svg" /><img src="./assets/projects/{slug}-wide.svg" width="100%" align="top" alt="{escape(project["title"])}: {escape(" ".join(project["description"]), quote=True)} Открыть проект ↗" /></picture>', '</a>']
readme += ['<a name="stats"></a>', f'<a href="{DATA["statistics_source"]}">',
           picture('stats', f'{DATA["public_repositories"]} публичных репозиториев · {len(DATA["projects"])} избранных проекта · {len({s for g in DATA["stack"] for s in g["items"]})} технологий · {len(DATA["stack"])} направления. Снимок на '+DATA['statistics_date']),
           '</a>', '<a name="activity"></a>',
           '<a href="https://github.com/PetkaKahin?tab=overview">', picture('activity', f'Карта активности GitHub: {total} contributions за 365 дней, {active} активных дней.'),
           picture('timeline', 'Дневная активность за последние 30 дней. Реальные данные GitHub.'), '</a>',
           picture('footer', 'Build systems. Pick locks.')]
# No whitespace or paragraph/break nodes between image slices: align=top
# removes the inline-image baseline gap using a GitHub-supported attribute.
(ROOT/'README.md').write_text('<!-- Generated by scripts/build-assets.py from profile.json + activity.json. -->\n<p align="center">'+''.join(readme)+'</p>\n')
print('GitHub-native dossier rebuilt: SVG panels + README.md.')
