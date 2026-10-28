# sebutharga

Sebut harga takaful: masukkan umur, jantina dan status merokok, pelan yang
layak terus keluar dengan manfaat dan caruman bulanan.

Pelan dan kadar ada dalam `PLANS` di `index.html`, ikut profil
`<jantina>-<merokok>` (cth. `m-smoker`) dan umur.

## Medical card

`medical/` ada template sebut harga medical card dan rekod kadar.

- `template.numbers`: template dengan 3 sheet, iaitu `2 Pelan` (Premium, Platinum),
  `3 Pelan` (Gold, Premium, Platinum) dan `Bayi` (pilihan SMART Basic/Starter/
  Premier/Newborn).
- `kadar.csv`: setiap harga yang pernah dimasukkan, ikut umur, pelan dan pilihan
  caruman, bersama tarikh rekod. Kadar lama tak dipadam; harga baru untuk umur
  yang sama ditambah sebagai baris baru dengan tarikh baru. Nama client tidak
  disimpan. Backup di Google Sheet "Kadar Medical Card", tab `Kadar`
  (https://docs.google.com/spreadsheets/d/1_2sQar3nvtLK3f80jzNPBmN5hCSwBS0fkvmoR63TJjM).
  Setiap kali `kadar.csv` ditambah, tambah baris yang sama ke sheet tu.
- `sebutharga.py`: isi template, jana PDF/PNG untuk client, dan tambah rekod ke
  `kadar.csv`.
- `design.py`, `design/quote.html`, `design/render.js`: design sebut harga untuk
  client (A4, satu muka surat). Semua manfaat dibaca daripada table Numbers yang
  dah diisi, jadi design yang sama digunakan untuk 2 pelan, 3 pelan dan bayi.
  Kalau kandungan terlebih A4, saiz tulisan dikecilkan sedikit secara automatik.

```
pip install numbers-parser
npm install -g playwright   # untuk PDF/PNG; perlu Chromium
python medical/sebutharga.py input.json
python medical/sebutharga.py input.json --tanpa-rekod   # jana semula sahaja
```

Format `input.json` ada di bahagian atas `sebutharga.py`. Fail keluar di
`medical/output/`: `<nama>_<umur>.numbers` dan `Sebut_Harga_<nama>_<umur>.pdf/.png`
(tidak di-commit sebab ada nama client).
