"""Tukar table sebut harga yang dah diisi kepada PDF dan PNG ikut design/quote.html.

Semua manfaat dibaca terus daripada table Numbers, jadi design ikut apa sahaja
template yang dipilih (2 pelan, 3 pelan atau bayi).
"""

import datetime
import html
import shutil
import subprocess
from pathlib import Path

DESIGN = Path(__file__).parent / "design"
BULAN = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai", "Ogos",
         "September", "Oktober", "November", "Disember"]
SEKSYEN = {"MANFAAT UTAMA", "MANFAAT TAMBAHAN", "PERLINDUNGAN TAMBAHAN"}
SOROT = ("Annual Limit", "Lifetime Limit", "Room & Board")
CARUMAN = {
    "NORMAL CONTRIBUTION": ("Normal Contribution", "", "Terus ke hospital panel"),
    "SMART OPTION": ("SMART Option", "DISKAUN 20%", "Perlu melalui SMART Journey"),
}

e = html.escape


def label_html(label):
    """'Co-Takaful (Outpatient Only)' -> tajuk + sub kecil di bawah."""
    lines = label.split("\n")
    main, sub = lines[0], " ".join(l.lstrip("- ").strip() for l in lines[1:])
    if not sub and main.endswith(")") and " (" in main:
        main, sub = main[:-1].split(" (", 1)
    return e(main) + (f'<span class="sub">{e(sub)}</span>' if sub else "")


def nilai_html(v, sorot=False):
    if v is None or v == "":
        return ""
    if isinstance(v, (int, float)):
        return f"RM {v:,.0f}"
    v = str(v).strip()
    if v == "-":
        return '<span class="dash">—</span>'
    if v == "✓":
        return '<span class="tick">✓</span>'
    main, *rest = v.split("\n")
    sub = " ".join(r.strip().strip("()") for r in rest)
    main = f'<span class="hl">{e(main)}</span>' if sorot else e(main)
    return main + (f'<span class="sub">{e(sub)}</span>' if sub else "")


def baris(label, cells, cls=""):
    cls = f' class="row {cls}"' if cls else ' class="row"'
    return f"      <div{cls}><div>{label}</div>" + "".join(f"<div>{c}</div>" for c in cells) + "</div>"


def jadual(table, label_col, plan_cols, header, caruman):
    out = ['      <div class="row plans"><div>Manfaat</div>']
    for plan, _ in plan_cols:
        tag = '<span class="tag">PERLINDUNGAN TERTINGGI</span>' if plan == "PLATINUM" and len(plan_cols) > 1 else ""
        out[0] += f'<div class="{plan.lower()}"><span class="pname">{e(plan)}</span>{tag}</div>'
    out[0] += "</div>"

    for r in range(header, caruman):
        label = table.cell(r, label_col).value
        if not label:
            continue
        label = str(label)
        if label.upper() in SEKSYEN:
            out.append(f'      <div class="section">{e(label.title())}</div>')
            continue
        values = [table.cell(r, c).value for _, c in plan_cols]
        lines = label.split("\n")
        bullets = [l.lstrip("•").strip() for l in lines[1:] if l.strip().startswith("•")]
        if bullets:
            # Contoh: Medical Follow-Up Coverage -> satu baris tajuk + satu baris setiap item.
            out.append(baris(e(lines[0]), [""] * len(plan_cols), "group"))
            per_plan = [str(v or "").split("\n") for v in values]
            for i, b in enumerate(bullets):
                cells = [nilai_html(p[i].strip() if i < len(p) and p[i].strip() else "-") for p in per_plan]
                out.append(baris(e(b), cells, "child"))
            continue
        sorot = label.startswith(SOROT)
        out.append(baris(label_html(label), [nilai_html(v, sorot) for v in values]))
    return "\n".join(out)


def caruman_html(table, label_col, plan_cols, caruman, pelan):
    out = []
    for r in range(caruman + 1, table.num_rows):
        label = table.cell(r, label_col).value
        if not label:
            break
        first, *rest = str(label).split("\n")
        key = first.split("(")[0].strip().upper()
        if not any(key in pelan[p] for p, _ in plan_cols):
            continue  # pilihan tanpa harga tak ditunjuk
        tajuk, badge, sub = CARUMAN.get(key, (
            "SMART " + key.removeprefix("SMART ").title() if key.startswith("SMART ") else key.title(),
            "",
            " ".join(x.strip().strip("()") for x in rest),
        ))
        badge = f' <span class="badge">{e(badge)}</span>' if badge else ""
        cells = []
        for _, c in plan_cols:
            v = table.cell(r, c).value
            cells.append(f'<div class="amt"><small>RM</small>{v:,.2f}<em>sebulan</em></div>'
                         if isinstance(v, (int, float)) else '<div class="amt"><span class="dash">—</span></div>')
        cls = "price-row smart" if badge else "price-row"
        out.append(f'      <div class="{cls}"><div class="lbl"><b>{e(tajuk)}{badge}</b><span>{e(sub)}</span></div>'
                   + "".join(cells) + "</div>")
    return "\n".join(out)


def jana(table, q, pelan, out_base):
    """Tulis <out_base>.html, kemudian render ke .pdf dan .png. Pulangkan senarai fail.

    pelan: {PELAN: {PILIHAN: harga}}. Pelan dan pilihan tanpa harga tak ditunjuk.
    """
    label_col = next(c for c in range(table.num_cols)
                     if table.cell(0, c).value == "RECOMMENDATION MEDICAL PLAN")
    header = next(r for r in range(table.num_rows) if table.cell(r, label_col).value == "MANFAAT UTAMA")
    caruman = next(r for r in range(table.num_rows) if table.cell(r, label_col).value == "PILIHAN CARUMAN")
    plan_cols = [(str(table.cell(header, c).value).upper(), c)
                 for c in range(label_col + 1, table.num_cols)
                 if str(table.cell(header, c).value or "").upper() in pelan]

    t = datetime.date.fromisoformat(q["tarikh"])
    isi = {
        "COLS": "1.25fr " + " ".join(["1fr"] * len(plan_cols)),
        "TARIKH": f"{t.day} {BULAN[t.month - 1]} {t.year}",
        "NAMA": e(q["nama"]),
        "UMUR": f"{q['umur']} tahun",
        "MEROKOK": e(str(q["merokok"]).capitalize()),
        "JADUAL": jadual(table, label_col, plan_cols, header, caruman),
        "CARUMAN": caruman_html(table, label_col, plan_cols, caruman, pelan),
    }
    page = (DESIGN / "quote.html").read_text()
    for k, v in isi.items():
        page = page.replace("{{" + k + "}}", v)

    out_html = Path(f"{out_base}.html")
    out_html.write_text(page)
    if not shutil.which("node"):
        print("Amaran: node tiada, PDF/PNG tidak dijana (HTML ada di", out_html, ")")
        return [out_html]
    subprocess.run(["node", str(DESIGN / "render.js"), str(out_html), str(out_base)], check=True)
    return [Path(f"{out_base}.pdf"), Path(f"{out_base}.png")]
