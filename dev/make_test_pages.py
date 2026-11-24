#!/usr/bin/env python3
"""Génère des copies de tablo.html avec des données de test et une navigation automatique.

Usage : python3 dev/make_test_pages.py <dossier_sortie>
Produit v_kids.html, v_setup.html, v_prog.html, v_game.html, v_result.html dans le dossier de sortie.
"""
import json, os, random, sys

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tablo-test"
os.makedirs(out, exist_ok=True)
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(root, "tablo.html"), encoding="utf-8").read()

random.seed(3)
facts = {}
for t in range(1, 11):
    for b in range(1, 11):
        if t == 9 and b > 5:
            continue  # quelques calculs jamais vus
        p, e = {1: (.98, 2), 2: (.98, 2), 5: (.98, 2), 10: (.98, 2), 3: (.85, 3.5), 4: (.85, 3.5),
                7: (.45, 6), 8: (.45, 6), 9: (.6, 5)}.get(t, (.7, 4.5))
        facts[f"mul:{t}:{b}"] = [[1 if random.random() < p else 0, round(max(1, random.gauss(e, 1)), 1)]
                                 for _ in range(random.randint(2, 8))]
for n in range(1, 16):
    facts[f"double:{n}"] = [[1, 2.0], [1, 2.5]]
for n in (2, 4, 6, 8, 10, 12):
    facts[f"half:{n}"] = [[1, 3.1], [0, 6]]
for v, lv in (("avoir", (1, 2)), ("être", (1, 2.5)), ("aller", (1, 5)), ("faire", (0, 8)), ("vouloir", (1, 3))):
    for p in range(6):
        facts[f"conj:{v}:{p}"] = [list(lv), [1 if p % 3 else 0, lv[1]]]
hist = [{"d": 1763800000000 - i * 86400000, "type": "mul", "mode": "smart" if i % 2 else "random",
         "n": 10, "time": 10, "good": g, "note": g * 2, "pts": g * 70}
        for i, g in enumerate([9, 8, 8, 7, 7, 6, 8, 5, 6, 4, 5, 3])]
settings = {"type": "mul", "mulTables": [3, 4, 7], "count": 10, "time": 10, "mode": "smart"}
KID = 'document.querySelector(".kidcard").click();'
ACT = lambda t: KID + 'document.querySelector(".act[data-type=' + t + ']").click();'
db = {"kids": [{"id": "a1", "name": "Léa", "avatar": "🦊", "history": hist, "facts": facts, "records": {},
                "settings": settings},
               {"id": "b2", "name": "Tom", "avatar": "🦖"}], "currentId": "a1"}

seed = "<script>localStorage.setItem('tablo.v1'," + json.dumps(json.dumps(db)) + ");</script>"
base = src.replace("<style>", seed + "<style>", 1)
nav = {
    "kids": "",
    "menu": KID,
    "setup": ACT("mul"),
    "prog": ACT("mul") + 'document.querySelector("[data-tab=scrProgress]").click();',
    "game": ACT("mul") + 'document.getElementById("btnGo").click();'
            'setTimeout(()=>{["4","2"].forEach(k=>document.dispatchEvent(new KeyboardEvent("keydown",{key:k})))},2400);',
    "csetup": ACT("conj"),
    "cprog": ACT("conj") + 'document.querySelector("[data-tab=scrProgress]").click();',
    "cgame": ACT("conj") + 'document.getElementById("btnGo").click();'
            'setTimeout(()=>{["o","n"].forEach(k=>document.dispatchEvent(new KeyboardEvent("keydown",{key:k})))},2400);',
    # Séance de verbes complète : bonne terminaison (lue dans le catalogue via le texte), 3e fausse, puis écran de fin.
    "cresult": ACT("conj") + 'document.getElementById("btnGo").click();'
               'let last="",n=0;setInterval(()=>{const g=document.getElementById("qGap");'
               'if(!document.querySelector("#scrGame.active")||!g||g===last)return;last=g;n++;'
               'const ty=document.getElementById("qVerb").textContent;'
               'const stem=document.querySelector("#qText .stem").textContent;'
               'const pr=document.getElementById("qText").firstChild.textContent.trim();'
               'const v=window.__tablo.conjAnswer(ty,pr,stem);const a=n===3?"zz":v;'
               '(a+"\\n").split("").forEach(k=>document.dispatchEvent(new KeyboardEvent("keydown",{key:k==="\\n"?"Enter":k})))},300);',
    # Séance complète : répond juste à tout (sauf la 3e question), puis écran de fin.
    "result": ACT("mul") + 'document.getElementById("btnGo").click();'
              'let last="",n=0;setInterval(()=>{const t=document.getElementById("qText").textContent;'
              'if(!document.querySelector("#scrGame.active")||t===last)return;last=t;n++;'
              'const r=String(eval(t.replace("×","*")));const v=n===3?"9".repeat(r.length):r;'
              'v.split("").forEach(k=>document.dispatchEvent(new KeyboardEvent("keydown",{key:k})))},300);',
}
for name, js in nav.items():
    with open(os.path.join(out, f"v_{name}.html"), "w", encoding="utf-8") as f:
        f.write(base.replace("</body>", "<script>" + js + "</script></body>"))
print(out)
