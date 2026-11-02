# Construye datos/icgmensual.csv desde la base de microdatos del ICG (respaldo público de PolíticaArgentina).
# Uso: python serieicg.py ruta/a/icg.dta
# Descarga de la base: https://raw.githubusercontent.com/PoliticaArgentina/data_warehouse/master/opinAr/data_raw/icg.dta
import sys, pandas as pd
d = pd.read_stata(sys.argv[1], convert_categoricals=False).dropna(subset=['icg', 'ano', 'mes'])
d['ym'] = pd.to_datetime(dict(year=d.ano.astype(int), month=d.mes.astype(int), day=1)).dt.to_period('M')
d = d[d.ym <= pd.Period('2026-08', 'M')]          # versión usada en el paper: 298 olas, noviembre 2001 a agosto 2026
w = d['ponderacion_utdt'].fillna(1)
serie = (d['icg'] * w).groupby(d['ym']).sum() / w.groupby(d['ym']).sum()
print('encuestas con índice:', len(d), 'olas:', len(serie))
serie.round(4).to_csv('../datos/icgmensual.csv', header=['icg'])
