# Reproduce todos los números del paper "La confianza como estimador" a partir de datos/icgmensual.csv y datos/instancias.csv.
# Uso: python replicacion.py   (desde la carpeta codigo)
import itertools, numpy as np, pandas as pd
from scipy import stats

s = pd.read_csv('../datos/icgmensual.csv', index_col=0)['icg']; s.index = pd.PeriodIndex(s.index, freq='M')
I = pd.read_csv('../datos/instancias.csv')
G = I[I.instancia.str.startswith('General')].reset_index(drop=True)
PASO = I[I.instancia.str.startswith('PASO')].reset_index(drop=True)
BAL = I[I.instancia.str.startswith('Balotaje')].reset_index(drop=True)
y = G.voto_oficialista_pct.values; x1 = G.icg_t1.values; x3 = G.icg_t3.values; n = len(y)

def ols(x, y):
    X = np.c_[np.ones(len(x)), x]; b = np.linalg.lstsq(X, y, rcond=None)[0]; return b, y - X @ b, X

def perm_p(x, y):
    r0 = abs(np.corrcoef(x, y)[0, 1]); c = tot = 0
    for p in itertools.permutations(y):
        tot += 1; c += abs(np.corrcoef(x, p)[0, 1]) >= r0 - 1e-12
    return c, tot, c / tot

def intervalo_prediccion(x, y, x0, alpha=0.05):
    """Semiamplitud del intervalo de predicción de la regresión simple de y sobre x, evaluada en x0."""
    b, res, X = ols(x, y); k = len(x); s2 = (res ** 2).sum() / (k - 2); xm = x.mean(); Sxx = ((x - xm) ** 2).sum()
    t = stats.t.ppf(1 - alpha / 2, k - 2)
    return b[0] + b[1] * x0, t * np.sqrt(s2 * (1 + 1 / k + (x0 - xm) ** 2 / Sxx))

# H1a
r = np.corrcoef(x1, y)[0, 1]; b, res, X = ols(x1, y)
print('r t-1', round(r, 4), 'R2', round(r ** 2, 3), 'constante', round(b[0], 4), 'pendiente', round(b[1], 4))
print('p paramétrico', round(stats.pearsonr(x1, y)[1], 4), 'permutación', perm_p(x1, y))
s2 = (res ** 2).sum() / (n - 2); se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X))); t = stats.t.ppf(.975, n - 2)
print('IC constante', np.round(b[0] + np.array([-1, 1]) * t * se[0], 2), 'IC pendiente', np.round(b[1] + np.array([-1, 1]) * t * se[1], 2))
for k_ in (3, 6, 12):
    xm = np.array([float(s[pd.Period(f, 'M') - k_: pd.Period(f, 'M') - 1].mean()) for f in G.fecha.str[:7]])
    print(f'r promedio {k_} meses', round(np.corrcoef(xm, y)[0, 1], 3))
for x0 in (x1.min(), x1.mean(), x1.max()):
    print('IP 95 % en', round(x0, 2), round(intervalo_prediccion(x1, y, x0)[1], 1))
h = np.diag(X @ np.linalg.inv(X.T @ X) @ X.T); cook = res ** 2 / (2 * s2) * h / (1 - h) ** 2
print('Cook', dict(zip(G.instancia, cook.round(2))))
for ex in ('General 2003', 'General 2023'):
    m = G.instancia.values != ex; bb, _, _ = ols(x1[m], y[m])
    print('sin', ex, 'pendiente', round(bb[1], 1), 'r', round(np.corrcoef(x1[m], y[m])[0, 1], 2), 'p param', round(stats.pearsonr(x1[m], y[m])[1], 3), 'perm', perm_p(x1[m], y[m]))
print('primeras diferencias r', round(np.corrcoef(np.diff(x1), np.diff(y))[0, 1], 3))
m = ~G.expectativas_inflacion_t1.isna(); z = np.log(G.expectativas_inflacion_t1[m].values)
resid = lambda a, c: a - np.polyval(np.polyfit(c, a, 1), c)
print('r parcial (log expectativas)', round(np.corrcoef(resid(x1[m], z), resid(y[m], z))[0, 1], 2))

# Validación cruzada y regla por veinte sobre seis generales
loo = np.array([y[i] - np.polyval(np.polyfit(np.delete(x1, i), np.delete(y, i), 1), x1[i]) for i in range(n)])
print('LOO', dict(zip(G.instancia, loo.round(1))), 'MAE', round(abs(loo).mean(), 2), 'RMSE', round(np.sqrt((loo ** 2).mean()), 2))
r20 = y - 20 * x1; print('regla por 20, seis generales, MAE', round(abs(r20).mean(), 2), 'RMSE', round(np.sqrt((r20 ** 2).mean()), 2))

# Validación temporal con ventana expansiva (2011 a 2023)
def expansiva(x):
    e = []
    for i in range(2, n):
        bb, _, _ = ols(x[:i], y[:i]); e.append(y[i] - (bb[0] + bb[1] * x[i]))
    return np.array(e)
def rep(nombre, e): print(nombre, e.round(1), 'MAE', round(abs(e).mean(), 2), 'RMSE', round(np.sqrt((e ** 2).mean()), 2))
rep('expansiva t-1', expansiva(x1)); rep('expansiva t-3', expansiva(x3))
rep('regla por 20 t-1', (y - 20 * x1)[2:]); rep('regla por 20 t-3', (y - 20 * x3)[2:])
rep('referencia media previa', np.array([y[i] - y[:i].mean() for i in range(2, n)]))
rep('referencia general anterior', np.array([y[i] - y[i - 1] for i in range(2, n)]))
rep('referencia primaria', y[2:] - PASO.voto_oficialista_pct.values)
print('media previa 2015 a 2023 MAE', round(abs(np.array([y[i] - y[:i].mean() for i in range(3, n)])).mean(), 2))
x3s = x3.copy(); x3s[G.instancia.values == 'General 2019'] = 1.97; rep('expansiva t-3 con 1,97 en julio 2019', expansiva(x3s))

# Primarias y balotajes
bp, resp, Xp = ols(PASO.icg_t1.values, PASO.voto_oficialista_pct.values)
sep = np.sqrt(np.diag((resp ** 2).sum() / 2 * np.linalg.inv(Xp.T @ Xp))); tp = stats.t.ppf(.975, 2)
print('primarias pendiente', round(bp[1], 2), 'EE', round(sep[1], 2), 'IC', np.round(bp[1] + np.array([-1, 1]) * tp * sep[1], 1))
for _, row in BAL.iterrows():
    pred = b[0] + b[1] * row.icg_t1; print(row.instancia, 'predicho', round(pred, 1), 'error', round(row.voto_oficialista_pct - pred, 1))

# Protocolo 2027: ecuaciones fijadas y función de intervalo
b3, _, _ = ols(x3, y)
print('ecuación t-1: voto =', round(b[0], 4), '+', round(b[1], 4), 'x ICG; rango', round(x1.min(), 2), 'a', round(x1.max(), 2))
print('ecuación t-3: voto =', round(b3[0], 4), '+', round(b3[1], 4), 'x ICG; rango', round(x3.min(), 2), 'a', round(x3.max(), 2))
print('ejemplo: ICG 1,50 en t-1 ->', [round(v, 1) for v in intervalo_prediccion(x1, y, 1.50)], '(predicción, semiamplitud IP 95 %)')
