#!/usr/bin/env python3
"""姫咲こはく優先表示＋開場/開演表示のオーバーレイ。index.html更新後に毎回実行すること（冪等）。
データは overlay.json。新しい告知が出たら overlay.json を更新する。"""
import json, re, html, os
D=os.path.dirname(os.path.abspath(__file__)); R=os.path.dirname(D)
cfg=json.load(open(os.path.join(D,'overlay.json'),encoding='utf-8'))
p=os.path.join(R,'index.html'); s=open(p,encoding='utf-8').read()
# 既存オーバーレイ除去
s=re.sub(r'<!--HO-->.*?<!--/HO-->','',s,flags=re.S)
e=html.escape
css='''<!--HO--><style>
.hime{max-width:1080px;margin:10px auto 0;padding:10px 14px;border-radius:14px;background:linear-gradient(90deg,#ffe3f0,#e6f4ff);border:2px solid #ff9cc8;font-size:13px;text-align:left}
.hime b.hh{color:#e0457b;font-size:15px}.hime ul{margin:4px 0 0;padding-left:18px}.hime a{color:#2f7cc4}
.ev .dt{display:block;font-size:10px;color:#5b4a6b}
.ev .hm{display:block;font-size:10px;color:#c2185b;background:#fff0f7;border-radius:4px;padding:0 3px;margin-top:2px}
.ev .nm{display:block;font-size:10.5px;font-weight:bold;color:#fff;background:#e0457b;border-radius:4px;padding:1px 4px;margin-top:2px}
.ev.star{border:2px solid #ff4f9a;border-left-width:5px;background:#fff6fb}
@media (max-width:760px){.le .ev .dt,.le .ev .hm,.le .ev .nm{font-size:11.5px}}
</style><!--/HO-->'''
s=s.replace('</head>',css+'</head>',1)
b=cfg['banner']
ban='<!--HO--><div class="hime"><b class="hh">💗 姫咲こはく 情報（最優先）</b><ul>'+''.join(f'<li>{x}</li>' for x in b)+'</ul></div><!--/HO-->'
s=s.replace('<nav>',ban+'<nav>',1)
for href,v in cfg['events'].items():
    pat=re.compile(r'(<a class="ev[^"]*)("\s+href="'+re.escape(href)+r'"[^>]*>)(.*?)(</a>)',re.S)
    def rep(m):
        cls=m.group(1)+(' star' if v.get('star') else '')
        body=m.group(3)
        add=''
        if v.get('hime'): add='<!--HO--><span class="hm">💗姫咲: '+e(v['hime'])+'</span><!--/HO-->'
        body=re.sub(r'(<span class="t">)',add+r'\1',body,count=1) if '<span class="t">' in body else add+body
        if v.get('dt'): body=re.sub(r'(<span class="n">)','<!--HO--><span class="dt">'+e(v['dt'])+'</span><!--/HO-->'+r'\1',body,count=1)
        if v.get('new'): body=re.sub(r'(<span class="vn">)','<!--HO--><span class="nm">'+e(v['new'])+'</span><!--/HO-->'+r'\1',body,count=1)
        return cls+m.group(2)+body+m.group(4)
    s,n=pat.subn(rep,s)
    if n==0: print('WARN not found',href)
s=s.replace(' star star',' star')
open(p,'w',encoding='utf-8').write(s); print('overlay applied')
