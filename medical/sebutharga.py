"""Jana sebut harga medical card (.numbers) dan rekod kadar ikut umur.

Guna:
    python medical/sebutharga.py input.json
    python medical/sebutharga.py input.json --tanpa-rekod   (jana semula, tak tambah ke kadar.csv)

Contoh input.json:
    {
      "nama": "Ali",
      "umur": 30,               (atau "tahun_lahir": 1996, umur = tahun tarikh - tahun lahir)
      "jantina": "lelaki",
      "merokok": "tidak",
      "tarikh": "2026-10-28",
      "pelan": {
        "PREMIUM":  {"NORMAL CONTRIBUTION": 210.50, "SMART OPTION": 172.30},
        "PLATINUM": {"NORMAL CONTRIBUTION": 245.10, "SMART OPTION": 199.80}
      },
      "hibah": 10000,
      "kematian_kemalangan": 20000
    }

Template dipilih sendiri: ada GOLD -> "3 Pelan"; pilihan SMART BASIC/STARTER/
PREMIER/NEWBORN -> "Bayi"; selain tu -> "2 Pelan". "tarikh" ikut hari ini kalau
tak diisi. "hibah" dan "kematian_kemalangan" ikut nilai template kalau tak diisi.
Pelan atau pilihan caruman tanpa harga dibuang daripada PDF/PNG; dalam fail
Numbers harganya ditukar ke "-".

Output dalam medical/output/: <nama>_<umur>.numbers, dan Sebut_Harga_<nama>_<umur>
.pdf/.png ikut design/quote.html (perlu node + playwright). Setiap harga ditambah
ke medical/kadar.csv bersama tarikh. Nama client tidak disimpan dalam kadar.csv.
"""

import csv
import datetime
import json
import sys
from pathlib import Path

from numbers_parser import Document
from numbers_parser.constants import DOCUMENT_ID

import design

HERE = Path(__file__).parent
TEMPLATE = HERE / "template.numbers"
KADAR = HERE / "kadar.csv"
OUTPUT = HERE / "output"
FIELDS = ["tarikh", "umur", "jantina", "merokok", "pelan", "pilihan", "caruman",
          "hibah", "kematian_kemalangan"]
BAYI = {"SMART BASIC", "SMART STARTER", "SMART PREMIER", "SMART NEWBORN"}


def pilihan_key(label):
    """'SMART OPTION (Diskaun 20%)\\n(Perlu ...)' -> 'SMART OPTION'."""
    return label.split("\n")[0].split("(")[0].strip().upper()


def pilih_sheet(q):
    pilihan = {p.upper() for harga in q["pelan"].values() for p in harga}
    if pilihan & BAYI:
        return "Bayi"
    if "GOLD" in {p.upper() for p in q["pelan"]}:
        return "3 Pelan"
    return "2 Pelan"


def buang_sheet_lain(doc, nama_sheet):
    archive = doc._model.objects[DOCUMENT_ID]
    refs = list(archive.sheets)
    names = [s.name for s in doc.sheets]
    del archive.sheets[:]
    for ref, name in zip(refs, names):
        if name == nama_sheet:
            archive.sheets.append(ref)


def isi(table, q):
    label_col = next(c for c in range(table.num_cols)
                     if table.cell(0, c).value == "RECOMMENDATION MEDICAL PLAN")
    table.write(1, label_col, f"Nama: {q['nama']}")
    table.write(2, label_col, f"Umur: - {q['umur']} tahun")
    table.write(3, label_col, f"Status Merokok/Vape: - {q['merokok']}")

    header = next(r for r in range(table.num_rows)
                  if table.cell(r, label_col).value == "MANFAAT UTAMA")
    plan_cols = {}
    for c in range(label_col + 1, table.num_cols):
        v = table.cell(header, c).value
        if v:
            plan_cols[str(v).upper()] = c

    pelan = {k.upper(): {pilihan_key(p): v for p, v in h.items()} for k, h in q["pelan"].items()}
    salah = set(pelan) - set(plan_cols)
    if salah:
        sys.exit(f"Pelan {sorted(salah)} tiada dalam template (ada: {sorted(plan_cols)})")

    hibah = {}
    for r in range(header, table.num_rows):
        label = str(table.cell(r, label_col).value or "")
        if label.startswith("Hibah Kematian") and "hibah" in q:
            hibah[r] = q["hibah"]
        elif label.startswith("Kematian Kemalangan") and "kematian_kemalangan" in q:
            hibah[r] = q["kematian_kemalangan"]
    for r, nilai in hibah.items():
        for c in plan_cols.values():
            if isinstance(table.cell(r, c).value, (int, float)):
                rm(table, r, c, nilai)

    caruman = next(r for r in range(table.num_rows)
                   if table.cell(r, label_col).value == "PILIHAN CARUMAN")
    rows = {}
    for r in range(caruman + 1, table.num_rows):
        label = table.cell(r, label_col).value
        if not label:
            break
        rows[pilihan_key(label)] = r
    for plan, harga in pelan.items():
        for p in harga:
            if p not in rows:
                sys.exit(f"Pilihan '{p}' tiada dalam template (ada: {sorted(rows)})")
    for plan, c in plan_cols.items():
        for p, r in rows.items():
            nilai = pelan.get(plan, {}).get(p)
            if nilai is None:
                table.write(r, c, "-")  # buang harga contoh daripada template
            else:
                rm(table, r, c, nilai)

    # Nilai hibah sebenar setiap pelan (ikut template kalau tak diisi) untuk rekod kadar.
    def nilai_baris(prefix, c):
        r = next(r for r in range(header, table.num_rows)
                 if str(table.cell(r, label_col).value or "").startswith(prefix))
        v = table.cell(r, c).value
        return f"{v:.0f}" if isinstance(v, (int, float)) else ""
    hibah = {plan: (nilai_baris("Hibah Kematian", plan_cols[plan]),
                    nilai_baris("Kematian Kemalangan", plan_cols[plan])) for plan in pelan}
    return pelan, hibah


def rm(table, r, c, nilai):
    table.write(r, c, float(nilai))
    table.set_cell_formatting(r, c, "currency", currency_code="MYR",
                              decimal_places=2, show_thousands_separator=True)


def rekod(q, pelan, hibah):
    baru = not KADAR.exists()
    with KADAR.open("a", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        if baru:
            w.writeheader()
        for plan, harga in pelan.items():
            for p, nilai in harga.items():
                w.writerow({
                    "tarikh": q["tarikh"], "umur": q["umur"], "jantina": q.get("jantina", ""),
                    "merokok": q["merokok"], "pelan": plan, "pilihan": p,
                    "caruman": f"{float(nilai):.2f}", "hibah": hibah[plan][0],
                    "kematian_kemalangan": hibah[plan][1],
                })


def main():
    q = json.loads(Path(sys.argv[1]).read_text())
    simpan_rekod = "--tanpa-rekod" not in sys.argv[2:]
    q.setdefault("tarikh", datetime.date.today().isoformat())
    if "tahun_lahir" in q:
        q["umur"] = datetime.date.fromisoformat(q["tarikh"]).year - int(q["tahun_lahir"])
    q.setdefault("merokok", "tidak")

    nama_sheet = pilih_sheet(q)
    doc = Document(TEMPLATE)
    buang_sheet_lain(doc, nama_sheet)
    sheet = next(s for s in doc.sheets if s.name == nama_sheet)
    pelan, hibah = isi(sheet.tables[0], q)
    sheet.name = "Medical Plan"

    OUTPUT.mkdir(exist_ok=True)
    nama = f"{q['nama'].replace(' ', '_')}_{q['umur']}"
    out = OUTPUT / f"{nama}.numbers"
    doc.save(out)
    print(f"{out}  ({nama_sheet})")
    for f in design.jana(sheet.tables[0], q, pelan, OUTPUT / f"Sebut_Harga_{nama}"):
        print(f)
    if simpan_rekod:
        rekod(q, pelan, hibah)


if __name__ == "__main__":
    main()
