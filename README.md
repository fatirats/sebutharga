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
  disimpan.
- `sebutharga.py`: isi template dan tambah rekod ke `kadar.csv`.

```
pip install numbers-parser
python medical/sebutharga.py input.json
```

Format `input.json` ada di bahagian atas `sebutharga.py`. Fail keluar di
`medical/output/` (tidak di-commit sebab ada nama client).
