# -*- coding: utf-8 -*-
"""Paper 2: aprobación presidencial y voto oficialista en 18 presidencialismos latinoamericanos.
Todos los números del texto salen de este script."""
import pandas as pd, numpy as np, json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
DAT = os.path.join(AQUI, '..', 'datos')
SAL = os.path.join(AQUI, '..', 'tablas')
D = pd.read_csv(os.path.join(DAT, 'elecciones_aprobacion.csv'), parse_dates=['date'])
D['grado'] = D['cat'].map({'P': 3, 'S': 2, 'R': 1, 'C': 0})

# ---------- calibración Latinobarómetro -> EAD (reproducible) ----------
# pares país-año: aprobación anual suavizada de EAD 3.0 y porcentaje que aprueba la gestión del gobierno en Latinobarómetro
# La calibración se estima con la base anual de la Executive Approval Database 3.0 (Carlin et al., 2023),
# que se descarga de executiveapproval.org y no se redistribuye aquí. Si se pasa su ruta como argumento,
# el script la reestima; si no, usa los coeficientes publicados en el paper (17,09 y 0,585).
LBP = pd.read_csv(os.path.join(DAT, 'latinobarometro_aprobacion.csv'))
if len(sys.argv) > 1:
    EA = pd.read_csv(sys.argv[1]); EA['country'] = EA.Country
    CAL = LBP.dropna(subset=['apr_pct']).merge(EA[['country', 'year', 'Approval_Smoothed']], on=['country', 'year']).dropna()
    cal_b = np.polyfit(CAL.apr_pct, CAL.Approval_Smoothed, 1)
    CALIB = {'n': len(CAL), 'r': round(float(np.corrcoef(CAL.apr_pct, CAL.Approval_Smoothed)[0, 1]), 3), 'const': round(float(cal_b[1]), 3), 'pend': round(float(cal_b[0]), 3)}
else:
    cal_b = np.array([0.585, 17.09])
    CALIB = {'n': 285, 'r': 0.78, 'const': 17.09, 'pend': 0.585, 'nota': 'coeficientes publicados'}
# oleada usada para elecciones posteriores a la cobertura de EAD (2022-2024): la más reciente con trabajo de campo terminado antes de la elección
# fechas de campo verificadas en los microdatos (MESREAL, DIAREAL): 2020 fines de 2020; 2023 febrero a abril de 2023 (último día 18/4); 2024 agosto a octubre de 2024 (Uruguay hasta el 8/10)
def ola(fecha):
    if fecha >= pd.Timestamp('2024-10-09'): return 2024
    if fecha >= pd.Timestamp('2023-04-19'): return 2023
    if fecha >= pd.Timestamp('2021-01-01'): return 2020
    return np.nan
post = D.ead_app.isna() & (D.date >= pd.Timestamp('2022-01-01'))
D.loc[post, 'lb_wave_cal'] = D.loc[post, 'date'].map(ola)
LBk = LBP.set_index(['country', 'year'])
D.loc[post, 'lb_apr_cal'] = [LBk.apr_pct.get((c, int(w)), np.nan) for c, w in zip(D.loc[post, 'country'], D.loc[post, 'lb_wave_cal'])]
D['ead_imp'] = D.ead_app
D.loc[post, 'ead_imp'] = cal_b[1] + cal_b[0] * D.loc[post, 'lb_apr_cal']
D['ead_fuente'] = np.where(D.ead_app.notna(), 'EAD', np.where(D.ead_imp.notna(), 'LB calibrado', None))
D.to_csv(os.path.join(SAL, 'base_calibrada.csv'), index=False)
R = {}

# ---------- universo ----------
R['n_total'] = len(D)
R['n_paises'] = D.country.nunique()
R['n_X'] = int((D['cat'] == 'X').sum())
R['n_nocomp'] = int(D.no_competitiva.sum())
R['n_principal'] = int(D.muestra_principal.sum())
M = D[(D.muestra_principal == 1) & D.ead_imp.notna()].sort_values('date').reset_index(drop=True)
R['n_analisis'] = len(M)
R['n_ead'] = int((M.ead_fuente == 'EAD').sum())
R['n_lbcal'] = int((M.ead_fuente == 'LB calibrado').sum())
R['cats'] = M['cat'].value_counts().to_dict()
R['periodo'] = [int(M.year.min()), int(M.year.max())]

def cl_se(X, e, g):
    XtXi = np.linalg.inv(X.T @ X); k = X.shape[1]; n = len(e)
    meat = np.zeros((k, k))
    for gg in np.unique(g):
        u = X[g == gg].T @ e[g == gg]; meat += np.outer(u, u)
    G = len(np.unique(g))
    return np.sqrt(np.diag(G / (G - 1) * (n - 1) / (n - k) * XtXi @ meat @ XtXi))

def ols(df, cols, fe=False):
    X = np.c_[np.ones(len(df))] if not cols else np.c_[np.ones(len(df)), df[cols].values.astype(float)]
    if fe:
        X = np.c_[X, pd.get_dummies(df.country, drop_first=True).values.astype(float)]
    y = df.vote_pct.values
    b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X @ b
    se = cl_se(X, e, df.country.values)
    r2 = 1 - (e @ e) / ((y - y.mean()) @ (y - y.mean()))
    sig = np.sqrt((e @ e) / (len(y) - X.shape[1]))
    k = len(cols) + 1
    return {'b': b[:k].round(3).tolist(), 'se': se[:k].round(3).tolist(), 't': (b[:k] / se[:k]).round(2).tolist(),
            'r2': round(r2, 3), 'sigma': round(sig, 2), 'n': len(y), 'cols': ['const'] + cols}

M['apr_x_cont'] = M.ead_imp * M.continuity
M['apr_x_grado'] = M.ead_imp * M.grado
R['m1'] = ols(M, ['ead_imp'])
R['m2'] = ols(M, ['ead_imp', 'continuity', 'apr_x_cont'])
R['m3'] = ols(M, ['ead_imp', 'grado', 'apr_x_grado'])
R['m4'] = ols(M, ['ead_imp', 'grado', 'apr_x_grado'], fe=True)
R['m3_sinR'] = ols(M[M['cat'] != 'R'], ['ead_imp', 'grado', 'apr_x_grado'])

# pendientes por categoría
pc = {}
for c in ['P', 'S', 'R', 'C']:
    t = M[M['cat'] == c]
    b = np.polyfit(t.ead_imp, t.vote_pct, 1)
    pc[c] = {'n': len(t), 'pend': round(b[0], 3), 'r': round(np.corrcoef(t.ead_imp, t.vote_pct)[0, 1], 3),
             'voto_medio': round(t.vote_pct.mean(), 1), 'aprob_media': round(t.ead_imp.mean(), 1)}
R['por_cat'] = pc
for c in [1, 0]:
    t = M[M.continuity == c]
    R[f'cont{c}'] = {'n': len(t), 'r': round(np.corrcoef(t.ead_imp, t.vote_pct)[0, 1], 3),
                     'pend': round(np.polyfit(t.ead_imp, t.vote_pct, 1)[0], 3)}
R['r_global'] = round(np.corrcoef(M.ead_imp, M.vote_pct)[0, 1], 3)

# bootstrap diferencia de pendientes continuidad binaria
rng = np.random.default_rng(1); d = []
for _ in range(2000):
    s = M.sample(len(M), replace=True, random_state=int(rng.integers(1e9)))
    a1, a0 = s[s.continuity == 1], s[s.continuity == 0]
    if len(a0) > 3:
        d.append(np.polyfit(a1.ead_imp, a1.vote_pct, 1)[0] - np.polyfit(a0.ead_imp, a0.vote_pct, 1)[0])
R['boot_dif'] = np.round(np.percentile(d, [2.5, 97.5]), 2).tolist()

# ---------- validación fuera de muestra (ventana expansiva regional) ----------
# referencias: voto oficialista anterior del mismo país; media histórica del voto oficialista del país; media regional
prev = {}
rows = []
DD = D.sort_values('date')
for i, r in M.iterrows():
    tr = M[M.date < r.date]
    hist = DD[(DD.country == r.country) & (DD.date < r.date) & DD.vote_pct.notna()]
    rec = {'country': r.country, 'year': r.year, 'cat': r['cat'], 'y': r.vote_pct,
           'ref_prev': hist.vote_pct.iloc[-1] if len(hist) else np.nan,
           'ref_hist': hist.vote_pct.mean() if len(hist) else np.nan}
    if len(tr) >= 20:
        X = np.c_[np.ones(len(tr)), tr.ead_imp, tr.grado, tr.ead_imp * tr.grado]
        b = np.linalg.lstsq(X, tr.vote_pct.values, rcond=None)[0]
        rec['pred_grado'] = b @ [1, r.ead_imp, r.grado, r.ead_imp * r.grado]
        b1 = np.polyfit(tr.ead_imp, tr.vote_pct, 1); rec['pred_simple'] = np.polyval(b1, r.ead_imp)
        rec['ref_reg'] = tr.vote_pct.mean()
    rows.append(rec)
V = pd.DataFrame(rows).dropna(subset=['pred_grado'])
V = V.dropna(subset=['ref_prev', 'ref_hist'])
def mae(a): return round(float(np.mean(np.abs(a))), 2)
def rmse(a): return round(float(np.sqrt(np.mean(np.square(a)))), 2)
R['oos_n'] = len(V)
R['oos'] = {k: [mae(V.y - V[k]), rmse(V.y - V[k])] for k in ['pred_grado', 'pred_simple', 'ref_prev', 'ref_hist', 'ref_reg']}
R['oos_cat'] = {c: {'n': int((V['cat'] == c).sum()), 'grado': mae((V.y - V.pred_grado)[V['cat'] == c]),
                    'simple': mae((V.y - V.pred_simple)[V['cat'] == c]),
                    'prev': mae((V.y - V.ref_prev)[V['cat'] == c]),
                    'hist': mae((V.y - V.ref_hist)[V['cat'] == c])} for c in ['P', 'S', 'R', 'C']}
# cobertura del intervalo de predicción 95% fuera de muestra (modelo grado, sigma del entrenamiento)
cov = []
for i, r in M.iterrows():
    tr = M[M.date < r.date]
    if len(tr) < 20: continue
    if not len(DD[(DD.country == r.country) & (DD.date < r.date) & DD.vote_pct.notna()]): continue  # mismos casos que la Tabla 3
    X = np.c_[np.ones(len(tr)), tr.ead_imp, tr.grado, tr.ead_imp * tr.grado]
    b = np.linalg.lstsq(X, tr.vote_pct.values, rcond=None)[0]; e = tr.vote_pct.values - X @ b
    s = np.sqrt(e @ e / (len(e) - 4)); x0 = np.array([1, r.ead_imp, r.grado, r.ead_imp * r.grado])
    h = x0 @ np.linalg.inv(X.T @ X) @ x0
    half = 1.97 * s * np.sqrt(1 + h); p = b @ x0
    cov.append({'cat': r['cat'], 'in': abs(r.vote_pct - p) <= half, 'half': half})
C = pd.DataFrame(cov)
R['cobertura'] = round(100 * C['in'].mean(), 1); R['cobertura_n'] = len(C); R['cobertura_in'] = int(C['in'].sum())
R['ip_semiancho_medio'] = round(C.half.mean(), 1)
R['cobertura_cat'] = (100 * C.groupby('cat')['in'].mean()).round(1).to_dict()

# ---------- robustez ----------
def m3_on(df):
    df = df.copy(); df['apr_x_grado'] = df.ead_imp * df.grado
    return ols(df, ['ead_imp', 'grado', 'apr_x_grado'])
rob = {}
rob['sin_interinos'] = m3_on(M[M.interino == 0])
rob['sin_reel_judicial'] = m3_on(M[M.reeleccion_judicial == 0])
rob['solo_EAD'] = m3_on(M[M.ead_fuente == 'EAD'])
rob['sin_dudosos'] = m3_on(M[M.doubt == 0])
A = D[(D['cat'] != 'X') & D.vote_pct.notna() & D.ead_imp.notna()].copy()
rob['con_no_competitivas'] = m3_on(A)
# Latinobarómetro confianza en el gobierno como predictor alternativo
L = D[(D.muestra_principal == 1) & D.lb_conf.notna()].copy(); L['ead_imp'] = L.lb_conf
rob['lb_confianza'] = m3_on(L)
R['rob'] = {k: {'int': v['b'][3], 'se': v['se'][3], 't': v['t'][3], 'n': v['n']} for k, v in rob.items()}

# ---------- contrastes entre pares de categorías ----------
def par_cat(a, b):
    t = M[M['cat'].isin([a, b])].copy(); t['dd'] = (t['cat'] == a).astype(float); t['ax'] = t.ead_imp * t.dd
    o = ols(t, ['ead_imp', 'dd', 'ax']); return {'dif': o['b'][3], 'se': o['se'][3], 't': o['t'][3], 'n': o['n']}
R['P_vs_S'] = par_cat('P', 'S'); R['S_vs_C'] = par_cat('S', 'C')

# ---------- robustez adicional ----------
def recod(ch, drop=()):
    t = M.copy()
    for (c, y), v in ch.items(): t.loc[(t.country == c) & (t.year == y), 'cat'] = v
    for c, y in drop: t = t[~((t.country == c) & (t.year == y))]
    t['grado'] = t['cat'].map({'P': 3, 'S': 2, 'R': 1, 'C': 0}); return m3_on(t)
sens = {'arg2023_C': recod({('Argentina', 2023): 'C'}),
        'par2018_C': recod({('Paraguay', 2018): 'C'}),
        'nic2006_C': recod({('Nicaragua', 2006): 'C'}),
        'col_R': recod({('Colombia', 2018): 'R', ('Colombia', 2022): 'R'}),
        'interinos_X': recod({}, drop=[('Venezuela', 1993), ('Guatemala', 2015)]),
        'sin_par2003': recod({}, drop=[('Paraguay', 2003)]),
        'par2023_S': recod({('Paraguay', 2023): 'S'}),
        'ps_dudosos_C': recod({('Costa Rica', 2006): 'C', ('Paraguay', 2013): 'C', ('Peru', 2021): 'C'})}
R['sens'] = {k: {'int': v['b'][3], 'se': v['se'][3], 't': v['t'][3], 'n': v['n']} for k, v in sens.items()}
per = {'1982-1999': (1982, 1999), '2000-2009': (2000, 2009), '2010-2024': (2010, 2024)}
R['periodos'] = {}
for k, (a, b) in per.items():
    sub = M[(M.year >= a) & (M.year <= b)]; sin = M[~((M.year >= a) & (M.year <= b))]
    o1 = m3_on(sub); o2 = m3_on(sin)
    R['periodos'][k] = {'n_solo': o1['n'], 'nC_solo': int((sub.continuity == 0).sum()), 'int_solo': o1['b'][3], 't_solo': o1['t'][3],
                        'n_sin': o2['n'], 'int_sin': o2['b'][3], 't_sin': o2['t'][3]}
loo = {}
for c in sorted(M.country.unique()):
    o = m3_on(M[M.country != c]); loo[c] = {'int': o['b'][3], 't': o['t'][3], 'n': o['n']}
R['loo'] = loo
R['loo_rango'] = {'int_min': min(v['int'] for v in loo.values()), 'int_max': max(v['int'] for v in loo.values()),
                  't_min': min(v['t'] for v in loo.values()), 't_max': max(v['t'] for v in loo.values()),
                  'pais_tmin': min(loo, key=lambda c: loo[c]['t']), 'pais_tmax': max(loo, key=lambda c: loo[c]['t'])}
R['oos_ncat'] = V['cat'].value_counts().to_dict()

# ---------- Argentina ----------
Aar = M[M.country == 'Argentina']
X = np.c_[np.ones(len(M)), M.ead_imp, M.grado, M.ead_imp * M.grado]
b3 = np.linalg.lstsq(X, M.vote_pct.values, rcond=None)[0]
arg = []
for _, r in Aar.iterrows():
    p = b3 @ [1, r.ead_imp, r.grado, r.ead_imp * r.grado]
    arg.append({'year': int(r.year), 'cat': r['cat'], 'aprob': round(r.ead_imp, 1), 'voto': r.vote_pct,
                'pred_regional': round(p, 1), 'error': round(r.vote_pct - p, 1)})
R['argentina'] = arg
R['arg_mae'] = mae(pd.DataFrame(arg).error)
# calibración LB->EAD
R['calib'] = CALIB
R['sin_medicion'] = D[(D.muestra_principal == 1) & D.ead_imp.isna()][['country', 'year']].values.tolist()
R['lbcal_casos'] = D[D.ead_fuente == 'LB calibrado'][['country', 'year', 'lb_wave_cal', 'muestra_principal']].values.tolist()

json.dump(R, open(os.path.join(SAL, 'resultados.json'), 'w', encoding='utf-8'), indent=1, default=str, ensure_ascii=False)
M.to_csv(os.path.join(SAL, 'muestra_118.csv'), index=False)
V.to_csv(os.path.join(SAL, 'validacion_fuera_de_muestra.csv'), index=False)
print(json.dumps(R, indent=1, default=str, ensure_ascii=False))
