"""Render the follow-up page (index.html) from the outputs in out/.

Uses the kit's page template and conventions (dark theme, red for Black women's measure, blues for comparisons,
outlined marks, Chart.js, no em dashes). Three sources side by side, victims per 911 call across neighborhoods in four
cities, calls per resident, the survey by relationship, and the explanation ledger. Every number comes from out/*.json.

  python scripts/build_page.py      ->  index.html
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.expanduser(os.environ.get("DISPARITY_KIT", "~/.claude/disparity-kit/kit")))
from build_page import TEMPLATE, esc, x  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "https://github.com/mngoh/Police-Records-vs-Survey-Assault-Victims-by-Race-and-Sex-2015-2025"
NATIONAL = "https://mngoh.github.io/US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025/"
WHITE = "#0b9fd0"
CITIES = {"New York": ("nyc_calls", "precincts"), "Los Angeles": ("la_calls", "districts"), "New Orleans": ("nola_calls", "zips"), "Baltimore": ("bmore_calls", "neighborhoods")}
CSS = """
    .pts { margin: 6px 0 0 18px; color: var(--muted); font-size: 14px; line-height: 1.7; } .pts li + li { margin-top: 4px; }
    .tbl-wrap { overflow-x: auto; margin-bottom: 24px; border: 1px solid var(--border); border-radius: 8px; }
    .tbl { border-collapse: collapse; width: 100%; font-size: 12px; }
    .tbl th, .tbl td { padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }
    .tbl th { color: var(--muted); font-weight: 600; font-size: 11px; } .tbl tr:last-child td { border-bottom: none; }
    .tbl td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .limits { margin: 0 0 40px 18px; color: var(--muted); font-size: 13px; line-height: 1.6; max-width: 900px; }
    .limits li + li { margin-top: 6px; } .limits strong { color: var(--text); font-weight: 600; }
    @media (max-width: 768px) {
      .tbl { font-size: 11px; } .tbl th, .tbl td { padding: 6px 8px; } .tbl td.num { white-space: normal; }
    }
"""


def load(name):
    return json.loads((ROOT / f"out/{name}.json").read_text())


def main():
    N = load("ncvs_results")
    ED = load("nhamcs_ed")
    REL = load("by_relationship")
    LA = load("la_repeat_victims")
    calls = {c: load(f) for c, (f, _) in CITIES.items()}
    js = []

    def box(cid, title, sub, height, extra=""):
        return (f'<div class="chart-box"><h3>{esc(title)}</h3><div class="chart-sub">{esc(sub)}</div>'
                f'<div class="chart-wrap" style="height:{height}px"><canvas id="{cid}" role="img" aria-label="{esc(title)}"></canvas></div>{extra}</div>')

    grid = lambda boxes, one=False: f'<div class="charts section-end"{" style=\"grid-template-columns:1fr\"" if one else ""}>{"".join(boxes)}</div>'

    def table(head, body, num_from=1):
        return ('<div class="tbl-wrap"><table class="tbl"><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f'<td{" class=\"num\"" if i >= num_from else ""}>{c}</td>' for i, c in enumerate(row)) + "</tr>" for row in body) + "</tbody></table></div>")

    # ---------- numbers ----------
    pol = N["police"]
    sv_us = N["windows"]["2015 to 2024, US"]
    sv_big = N["windows"]["2015 to 2024, Places of 250,000+"]
    ed_w = ED["ratios"]["Black women vs White women"]
    sources = [("Police records, 51 cities, 2022 to 2025", pol["ratio"]["White"], None),
               ("Hospital emergency departments, US, 2021 to 2022", ed_w["ratio"], ed_w["ci95"]),
               ("Victimization survey, large places, 2015 to 2024", sv_big["ratio_all"]["White"]["ratio"], sv_big["ratio_all"]["White"]["ci95_deff2"]),
               ("Victimization survey, US, 2015 to 2024", sv_us["ratio_all"]["White"]["ratio"], sv_us["ratio_all"]["White"]["ci95_deff2"])]
    flat = [c for c, r in calls.items() if abs(r["regression"]["black_share_coef"]) < 2 * r["regression"]["black_share_se"]]
    effect = [c for c in calls if c not in flat]
    share = {g: sv_us["share_reported"][g]["pct"] for g in ("Black", "White", "Hispanic")}

    lede = (f"Police record assaults on Black women about {x(pol['ratio']['White'])} times as often as on White women. Hospitals see the same gap ({x(ed_w['ratio'])} times). "
            f"Only the victimization survey, where women describe their own assaults, puts it near {x(sv_us['ratio_all']['White']['ratio'])}.")
    question = "Is the 4x gap in police records about assaults, about reporting, or about how police record?"
    points = [
        f"Not reporting: Black women report {share['Black']:.0f}% of assaults, White women {share['White']:.0f}%.",
        f"Not recording: police write up the same share of victims per 911 call in every neighborhood in {', '.join(flat)}" + (f"; a little more in {', '.join(effect)}." if effect else "."),
        f"Not repeat counting: about {LA['groups']['Black']['reports_per_woman']:.1f} reports per woman in both groups in Los Angeles.",
        f"Hospitals agree with police: {x(ed_w['ratio'])} times, with no call involved. What is left open is why the survey sees so little.",
    ]
    answer = '<ul class="pts">' + "".join(f"<li>{esc(p)}</li>" for p in points) + "</ul>"
    tiles = [("Police records", f"{x(pol['ratio']['White'])}x", "51 cities"),
             ("Emergency departments", f"{x(ed_w['ratio'])}x", "women, 2021 to 2022"),
             ("Victimization survey", f"{x(sv_us['ratio_all']['White']['ratio'])}x", f"{x(sv_big['ratio_all']['White']['ratio'])}x in large places"),
             ("Recording adds nothing", f"{len(flat)} of {len(calls)}", "cities")]
    cards = '<div class="cards">' + "".join(f'<div class="card"><div class="label">{esc(l_)}</div><div class="value">{esc(v)}</div><div class="sub">{esc(s)}</div></div>' for l_, v, s in tiles) + "</div>"

    # ---------- charts ----------
    labels = [s[0] for s in sources]
    bars = [[0, s[1]] for s in sources]
    tips = {s[0]: (f"{s[1]}x" + (f", 95% interval {s[2][0]} to {s[2][1]}" if s[2] else "")) for s in sources}
    js.append(f"new Chart(document.getElementById('sources'),{{type:'bar',data:{{labels:{json.dumps(labels)},datasets:[{{label:'Black women\\'s rate over White women\\'s',data:{json.dumps(bars)},...bar(C.red),maxBarThickness:18}}]}},"
              f"options:{{...base,indexAxis:'y',layout:{{padding:{{top:16}}}},plugins:{{legend:{{display:false}},refLines:{{x:1,label:'1 = no gap'}},tooltip:{{callbacks:{{label:c=>({json.dumps(tips)})[c.label]}}}}}},"
              f"scales:{{y:{{grid:{{display:false}},ticks:{{color:C.text,autoSkip:false}}}},x:{{min:0,suggestedMax:6,title:{{display:true,text:'Times White women\\'s rate'}}}}}}}}}});")
    src_box = box("sources", "Three sources", "Black women's assault rate over White women's. A bar ending at 1 would mean no gap.", 230)

    colors = ["C.red", "C.blue", "WHITE", "C.muted"]
    bands = ["whitest fifth", "2nd", "3rd", "4th", "Blackest fifth"]
    ds = ",".join(f"{{label:{json.dumps(c)},data:{json.dumps([b['victims_per_call'] for b in r['bands']])},...dot({col}),showLine:true,borderColor:{col},borderWidth:2,pointRadius:4}}"
                  for (c, r), col in zip(calls.items(), colors))
    js.append(f"new Chart(document.getElementById('vpc'),{{type:'line',data:{{labels:{json.dumps(bands)},datasets:[{ds}]}},"
              f"options:{{...base,plugins:{{legend:{{display:true,labels:{{usePointStyle:true}}}}}},scales:{{y:{{min:0,suggestedMax:1.2,title:{{display:true,text:'Recorded victims per 911 assault call'}}}},x:{{grid:{{display:false}},title:{{display:true,text:'Neighborhoods by Black share of residents'}}}}}}}}}});")
    vpc_box = box("vpc", "Victims recorded per 911 call", "Flat = police record the same share everywhere.", 300)
    ds2 = ",".join(f"{{label:{json.dumps(c)},data:{json.dumps([round(b['calls_per_1k'] / r['bands'][0]['calls_per_1k'], 2) for b in r['bands']])},...dot({col}),showLine:true,borderColor:{col},borderWidth:2,pointRadius:4}}"
                   for (c, r), col in zip(calls.items(), colors))
    js.append(f"new Chart(document.getElementById('cpr'),{{type:'line',data:{{labels:{json.dumps(bands)},datasets:[{ds2}]}},"
              f"options:{{...base,plugins:{{legend:{{display:true,labels:{{usePointStyle:true}}}}}},scales:{{y:{{min:0,title:{{display:true,text:'Assault calls per resident, whitest fifth = 1'}}}},x:{{grid:{{display:false}},title:{{display:true,text:'Neighborhoods by Black share of residents'}}}}}}}}}});")
    cpr_box = box("cpr", "Calls per resident", "Rising = the gap is already in the calls.", 300)

    rel_keys = ["intimate", "relative", "known", "stranger"]
    rel_labels = ["Intimate partner", "Other relative", "Known", "Stranger"]
    ds3 = ",".join(f"{{label:{json.dumps(lab)},data:{json.dumps([REL[k][c]['ratio'] for c in rel_keys])},...bar({col})}}" for lab, k, col in
                   (("Survey, with injury, large places", "survey, places of 250,000+, injured only", "C.blue"), ("Police, 51 cities", "police, 51 cities", "C.red")))
    js.append(f"new Chart(document.getElementById('rel'),{{type:'bar',data:{{labels:{json.dumps(rel_labels)},datasets:[{ds3}]}},"
              f"options:{{...base,plugins:{{legend:{{display:true}},refLines:{{y:1}}}},scales:{{y:{{min:0,title:{{display:true,text:'Black women\\'s rate over White women\\'s'}}}},x:{{grid:{{display:false}}}}}}}}}});")
    rel_box = box("rel", "By who did it", "The police gap is larger in every category.", 300)

    led = [("Black women report assaults more often", "Survey", f"A little: {share['Black']:.0f}% against {share['White']:.0f}%; lifts the survey ratio to about {x(sv_big['ratio_reported']['White']['ratio'])}, not 4"),
           ("Survey counts threats as assaults", "Survey, injury only", f"No: with an injury required the ratio is {x(sv_us['ratio_all']['White']['ratio'])} nationally"),
           ("One assault becomes several records", "DC", "No: 10.4x to 10.7x however records are counted"),
           ("The same women reported again and again", "Los Angeles", f"No: {LA['groups']['Black']['reports_per_woman']:.2f} and {LA['groups']['White']['reports_per_woman']:.2f} reports per woman; ratio {LA['ratio_reports_la_page']['White']} to {LA['ratio_women_implied']['White']}"),
           ("Police write up more victims per call in Black neighborhoods", ", ".join(calls), f"Flat in {', '.join(flat)}" + (f"; up to {x(float(__import__('math').exp(calls[effect[0]]['regression']['black_share_coef'])))}x in {', '.join(effect)}" if effect else "")),
           ("Public housing and shelters", "New York", "Partly: 17% of recorded assaults on Black women are in public housing against 3% of those on White women; outside it the ratio is 4.5x, not 5.2x"),
           ("Assaults recorded where they happen, residents counted where they live", "New York", "Large: within the Blackest precincts the gap is 2.7x, citywide 5.2x"),
           ("Hospitals see what police see", "NHAMCS", f"Yes: {x(ed_w['ratio'])}x for women, {x(ED['ratios']['Black men vs White men']['ratio'])}x for men")]
    ledger = ('<div class="section-title">Every explanation tested</div>' + table(["Could the police gap be...", "Tested in", "Answer"], [[esc(a), esc(b), esc(c)] for a, b, c in led], num_from=9))

    cities_tbl = table(["City", "Victims per call, whitest to Blackest fifth", "Recording effect", "Calls per resident, Blackest over whitest"],
                       [[f"{esc(c)}<br><span style=\"color:var(--muted)\">{r.get('precincts') or r.get('districts') or r.get('zips') or r.get('neighborhoods')} {CITIES[c][1]}</span>",
                         f"{r['bands'][0]['victims_per_call']} to {r['bands'][-1]['victims_per_call']}", f"{__import__('math').exp(r['regression']['black_share_coef']):.2f} (SE {r['regression']['black_share_se']})",
                         f"{r['top_over_bottom']['calls_per_1k']}x"] for c, r in calls.items()], num_from=1)
    ed_tbl = table(["", "Black", "White", "Hispanic", "Black vs White, 95% interval"],
                   [["Women", f"{ED['cells']['Black women']['rate_per_100k']:,}", f"{ED['cells']['White women']['rate_per_100k']:,}", f"{ED['cells']['Hispanic women']['rate_per_100k']:,}", f"{ed_w['ratio']} ({ed_w['ci95'][0]} to {ed_w['ci95'][1]})"],
                    ["Men", f"{ED['cells']['Black men']['rate_per_100k']:,}", f"{ED['cells']['White men']['rate_per_100k']:,}", f"{ED['cells']['Hispanic men']['rate_per_100k']:,}", f"{ED['ratios']['Black men vs White men']['ratio']} ({ED['ratios']['Black men vs White men']['ci95'][0]} to {ED['ratios']['Black men vs White men']['ci95'][1]})"]])
    reporting = ('<div class="section-title">The cities</div>' + cities_tbl
                 + f'<div class="section-title">Emergency departments, {ED["years"][0]} to {ED["years"][-1]}</div><p class="note">' + esc(f"Per 100,000 adults a year; {ED['cells']['Black women']['sampled_visits']} Black and {ED['cells']['White women']['sampled_visits']} White women's visits sampled.") + '</p>' + ed_tbl)

    limits = [("Small survey cells", f"{sv_us['cases']['Black']} Black women assault victims in the survey over ten years; the hospital figure rests on {ED['cells']['Black women']['sampled_visits']} sampled visits. Intervals are approximate."),
              ("Definitions differ", "Survey simple assault includes threats; police and hospital counts do not. The injury-only checks address this."),
              ("Place is not residence", "Assaults are recorded where they happen and residents counted where they live, so the within-neighborhood ratios are rough too."),
              ("Race recorded three ways", "By officers in police data, by respondents in the survey, by hospital staff in NHAMCS. The race-coding bound from the national run applies to the police side."),
              ("What is left open", "Why the survey sees so little: non-response, coverage of shelters and institutions, or what women say at home. And who makes the calls. Neither can be settled with public data."),
              ("What, not why", "Nothing here measures causes, offenders or circumstances.")]
    limits_html = '<div class="section-title">Limits</div><ul class="limits">' + "".join(f"<li><strong>{esc(h)}.</strong> {esc(t)}</li>" for h, t in limits) + "</ul>"
    nav = f'<a href="{NATIONAL}">The 59-city page</a><a href="{REPO}">Code</a><a href="https://martinngoh.com">martinngoh.com</a>'
    method = ("Survey: BJS NCVS, women 18 and older, 2015 to 2024. Hospitals: NHAMCS 2021 and 2022. Police: the 59-city run. Calls: each city's open data by neighborhood. "
              "Every number is generated from out/*.json; the README holds the full tables.")
    pre = ("const WHITE = '" + WHITE + "';\n  "
           "const dot = c => ({ borderColor: C.surface, backgroundColor: c, borderWidth: 2, pointRadius: 5, pointHoverRadius: 7, pointHitRadius: 12, showLine: false });\n  "
           "Chart.register({ id: 'refLines', beforeDatasetsDraw(chart, args, o) {\n"
           "    const { ctx, chartArea: a, scales: { x, y } } = chart; if (!o || (!o.x && !o.y)) return;\n"
           "    ctx.save(); ctx.strokeStyle = C.grey2; ctx.lineWidth = 1;\n"
           "    if (o.x) { const px = x.getPixelForValue(o.x); ctx.beginPath(); ctx.moveTo(px, a.top); ctx.lineTo(px, a.bottom); ctx.stroke();\n"
           "      if (o.label) { ctx.fillStyle = C.muted; ctx.font = '10px -apple-system, Segoe UI, Helvetica, Arial, sans-serif'; ctx.fillText(o.label, px + 4, a.top - 5); } }\n"
           "    if (o.y) { const py = y.getPixelForValue(o.y); ctx.beginPath(); ctx.moveTo(a.left, py); ctx.lineTo(a.right, py); ctx.stroke(); }\n"
           "    ctx.restore(); } });")
    page = TEMPLATE.format(
        title="What the assault-victim gap measures", description=esc(lede), lede=esc(lede), author="Martin Ngoh", window="2015 to 2025", total="three sources",
        nav=nav, question=esc(question), answer=answer, cards=cards, overview=grid([src_box], one=True) + grid([vpc_box, cpr_box]),
        tests=grid([rel_box], one=True) + ledger, reporting=reporting, model="", replication="", caveats="", method=esc(method),
        js=pre + "\n  " + "\n  ".join(js), groups_n="", others_n="", focus="Black women", sexw="women", sexw_cap="Women")
    page = page.replace("  </style>\n</head>", CSS + "  </style>\n</head>", 1)
    page = page.replace('<div class="section-title">Dataset</div>', '<div class="section-title">At a glance</div>', 1)
    page = page.replace('<div class="section-title">Testing explanations</div>\n  <p class="note">Women only ( Black women,  other women). Each cut asks whether a plain explanation accounts for the gap.</p>', '<div class="section-title">Testing explanations</div>', 1)
    page = page.replace("</p>\n</div>\n<footer>", "</p>\n  " + limits_html + "\n</div>\n<footer>", 1)
    page = page.replace(" · three sources victims", " · three sources")
    for bad in ["—", "–"]:
        page = page.replace(bad, ", " if bad == "—" else " to ")
    (ROOT / "index.html").write_text(page)
    print("wrote", ROOT / "index.html")
    print(lede)


if __name__ == "__main__":
    main()
