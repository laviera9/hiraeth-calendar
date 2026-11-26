#!/usr/bin/env python3
"""姫咲こはく優先表示＋開場/開演表示のオーバーレイ。index.html更新後に毎回実行すること（冪等）。

データは overlay.json。新しい告知が出たら overlay.json を更新する。
バナーは「公式発表」と最新の確認日だけを先に出し、古い確認メモは折りたたむ。
各イベントの特典・チケット・食い違い注記は <details> に入れ、開場・開演と出欠は見える位置に残す。
"""
import html
import json
import os
import re

D = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(D)
cfg = json.load(open(os.path.join(D, "overlay.json"), encoding="utf-8"))
p = os.path.join(R, "index.html")
s = open(p, encoding="utf-8").read()

s = re.sub(r"<!--HO-->.*?<!--/HO-->", "", s, flags=re.S)

e = html.escape

css = """<!--HO--><style>
.hime{max-width:1080px;margin:10px auto 0;padding:10px 14px;border-radius:14px;background:linear-gradient(90deg,#ffe3f0,#e6f4ff);border:2px solid #ff9cc8;font-size:13px;text-align:left}
.hime b.hh{color:#e0457b;font-size:15px}
.hime ul{margin:4px 0 0;padding-left:18px}
.hime a{color:#2f7cc4}
.hime .hime-hist{margin-top:8px;font-size:12px;color:#6c5f7a}
.hime .hime-hist>summary{cursor:pointer;color:#c2185b;font-weight:bold}
.hime .hime-hist ul{margin-top:6px}
.ev .dt{display:block;font-size:10px;color:#5b4a6b}
.ev .hm{display:block;font-size:10px;color:#c2185b;background:#fff0f7;border-radius:4px;padding:0 3px;margin-top:2px}
.ev .nm{display:block;font-size:10.5px;font-weight:bold;color:#fff;background:#e0457b;border-radius:4px;padding:1px 4px;margin-top:2px}
.ev .ev-more{display:block;margin-top:3px;font-size:11px;color:#6c5f7a}
.ev .ev-more>summary{cursor:pointer;color:#2f7cc4;font-weight:normal}
.ev .ev-more .more-body{margin-top:3px;line-height:1.45;overflow-wrap:anywhere}
.ev.star{border:2px solid #ff4f9a;border-left-width:5px;background:#fff6fb}
@media (max-width:760px){.le .ev .dt,.le .ev .hm,.le .ev .nm{font-size:12px}.le .ev .ev-more{font-size:12px}}
</style><!--/HO-->"""
s = s.replace("</head>", css + "</head>", 1)

ATT_RE = re.compile(r"休演|お休み|出演なし")
DOORS_RE = re.compile(r"開場\s*\d{1,2}:\d{2}\s*／\s*開演\s*\d{1,2}:\d{2}")
SHORT_PAREN_RE = re.compile(r"^（([^）]{1,8})）")
GENERIC_HIME_RE = re.compile(
    r"公式告知(の本文)?に(名前|個人名)なし|公式告知なし|出演者情報に個人名なし|出演についての言及なし"
)
OFFICIAL_HIME_RE = re.compile(r"公式発表|正式発表|お披露目|加入")
ATT_HIME_RE = re.compile(r"休演|お休み")
ROLE_HIME_RE = re.compile(r"担当|出演")
DISC_RE = re.compile(r"以前の告知|表記が変わ|食い違|本文には|画像では|画像は|※")
URL_RE = re.compile(r"https?://[A-Za-z0-9./?#&=_%~:+-]+")


def strip_urls(t: str) -> str:
    t = URL_RE.sub("", t)
    t = re.sub(r"\s+・", "・", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"[（(]\s*[)）]", "", t)
    t = re.sub(r"\s+([）)])", r"\1", t)
    return t.strip(" ・／|")


def hime_visible_part(part: str) -> bool:
    if GENERIC_HIME_RE.search(part):
        return False
    if OFFICIAL_HIME_RE.search(part):
        return True
    if ATT_HIME_RE.search(part):
        return True
    if ROLE_HIME_RE.search(part) and len(part) <= 80:
        return True
    return False


def split_dt(dt: str):
    """開場/開演と出欠を見える位置へ。特典・チケット・注記は折りたたみへ。"""
    vis, hid = [], []
    doors_short = ""
    m = DOORS_RE.search(dt)
    if m:
        doors_short = re.sub(r"\s+", "", m.group(0))
    for raw in dt.split("｜"):
        p_ = raw.strip()
        if not p_:
            continue
        if doors_short and DOORS_RE.search(p_):
            suffix = p_[DOORS_RE.search(p_).end() :].strip()
            shown = doors_short
            if suffix:
                sp = SHORT_PAREN_RE.match(suffix)
                if sp and not DISC_RE.search(suffix):
                    shown = f"{doors_short}（{sp.group(1)}）"
                    extra = suffix[sp.end() :].strip()
                    if extra:
                        hid.append(suffix)
                else:
                    hid.append(suffix if not DISC_RE.search(p_) else p_)
            vis.append(shown)
            continue
        if ATT_RE.search(p_):
            vis.append(strip_urls(p_))
            continue
        if "ソロ出番" in p_:
            vis.append(p_)
            continue
        if re.match(r"(HIRAETH\.Tokyo出番|出番\d)", p_) or p_.startswith("HIRAETH.Tokyo出番"):
            hid.append(p_)
            continue
        hid.append(p_)
    vis_u, seen = [], set()
    for x in vis:
        if x not in seen:
            vis_u.append(x)
            seen.add(x)
    return vis_u, hid


def split_hime(h: str):
    """意味のあるこはく情報だけ先に出し、長い補足は折りたたみへ。"""
    h = h.strip()
    if not h:
        return [], []
    parts = [p_.strip() for p_ in h.split("｜") if p_.strip()]
    important, other = [], []
    for p_ in parts:
        if hime_visible_part(p_):
            important.append(strip_urls(p_))
        else:
            other.append(p_)
    return important, other


def details_html(chunks):
    if not chunks:
        return ""
    body = "｜".join(e(x) for x in chunks)
    return (
        '<!--HO--><details class="ev-more"><summary>特典・チケットなど</summary>'
        f'<div class="more-body">{body}</div></details><!--/HO-->'
    )


b = cfg["banner"]
visible, folded = [], []
seen_check = False
for i, x in enumerate(b):
    is_official = ("【公式発表" in x) or ("正式に発表" in x) or ("正式発表" in x)
    is_check = "【確認日" in x
    if is_official and i < 4:
        visible.append(x)
    elif is_check and not seen_check:
        visible.append(x)
        seen_check = True
    elif (not is_check) and (not is_official) and i == 0:
        visible.append(x)
    else:
        folded.append(x)
if not visible and b:
    visible, folded = b[:1], b[1:]

ban = '<!--HO--><div class="hime"><b class="hh">💗 姫咲こはく</b><ul class="now">'
ban += "".join(f"<li>{x}</li>" for x in visible)
ban += "</ul>"
if folded:
    ban += (
        f'<details class="hime-hist"><summary>これまでの確認メモ（{len(folded)}件）</summary><ul>'
        + "".join(f"<li>{x}</li>" for x in folded)
        + "</ul></details>"
    )
ban += "</div><!--/HO-->"
s = s.replace("<nav>", ban + "<nav>", 1)

for href, v in cfg["events"].items():
    pat = re.compile(
        r'(<a class="ev[^"]*)("\s+href="' + re.escape(href) + r'"[^>]*>)(.*?)(</a>)',
        re.S,
    )

    def rep(m, v=v):
        cls = m.group(1) + (" star" if v.get("star") else "")
        body = m.group(3)
        more = []

        himes, hid_h = split_hime(v.get("hime") or "")
        if himes:
            add = '<!--HO--><span class="hm">💗姫咲: ' + e(" ／ ".join(himes)) + "</span><!--/HO-->"
            if '<span class="t">' in body:
                body = re.sub(r'(<span class="t">)', add + r"\1", body, count=1)
            else:
                body = add + body
        more.extend(hid_h)

        vis_dt, hid_dt = split_dt(v["dt"]) if v.get("dt") else ([], [])
        if vis_dt:
            dt_html = '<!--HO--><span class="dt">' + e("｜".join(vis_dt)) + "</span><!--/HO-->"
            if '<span class="n">' in body:
                body = re.sub(r'(<span class="n">)', dt_html + r"\1", body, count=1)
            else:
                body = dt_html + body
        more.extend(hid_dt)

        if v.get("new"):
            body = re.sub(
                r'(<span class="vn">)',
                '<!--HO--><span class="nm">' + e(v["new"]) + "</span><!--/HO-->" + r"\1",
                body,
                count=1,
            )

        if more:
            if '<span class="ic' in body:
                body = re.sub(r'(<span class="ic)', details_html(more) + r"\1", body, count=1)
            else:
                body += details_html(more)
        return cls + m.group(2) + body + m.group(4)

    s, n = pat.subn(rep, s)
    if n == 0:
        print("WARN not found", href)

s = s.replace(" star star", " star")
open(p, "w", encoding="utf-8").write(s)
print("overlay applied")
