# -*- coding: utf-8 -*-
import zipfile, os
base = r"C:\Users\Carlos\Desktop\artigo_20260914"
dest = os.path.join(base, "overleaf", "artigo_20260914_overleaf.zip")
arquivos = ["main.tex", "references.bib"]
figs = [os.path.join("figures", f) for f in sorted(os.listdir(os.path.join(base, "figures")))
        if f.endswith(".pdf") and "fig6" not in f]
arquivos += figs
supl = [("tabela_ic95.csv", "supplementary/tabela_ic95.csv"),
        ("tabela_sensibilidade.csv", "supplementary/tabela_sensibilidade.csv")]
os.makedirs(os.path.dirname(dest), exist_ok=True)
with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
    for a in arquivos:
        z.write(os.path.join(base, a), a)
    for nome, arc in supl:
        z.write(os.path.join(base, "reproducao", "supplementary", nome), arc)
print("zip regenerado:", dest)
for i in zipfile.ZipFile(dest).infolist():
    print("  ", i.filename, i.file_size)