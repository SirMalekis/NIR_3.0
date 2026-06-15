"""
plot_results.py — Автоматическое построение графиков из CSV (C++ симулятор).
Запуск: python plot_results.py [путь_к_папке]
Требует: pip install pandas matplotlib
"""
import sys
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# --- Настройки оформления ---
plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.titlesize": 12, 
    "axes.labelsize": 10, "legend.fontsize": 9, "figure.dpi": 120
})
COLORS = {"star": "#e74c3c", "full_mesh": "#3498db", "ring": "#2ecc71", "bus": "#f39c12"}

def safe_read(path):
    try: return pd.read_csv(path)
    except Exception as e:
        print(f"  [!] Ошибка чтения {path}: {e}")
        return None

# 1. Сравнение топологий
def plot_topology(df, out_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(df)); w = 0.25
    ax.bar([i - w for i in x], df['lcc_mean'], w, yerr=df['lcc_ci'], capsize=4, label='LCC', color='#3498db')
    ax.bar(x, df['eff_mean'], w, yerr=df['eff_ci'], capsize=4, label='E_norm', color='#2ecc71')
    ax.bar([i + w for i in x], df['wsurv_mean'], w, yerr=df['wsurv_ci'], capsize=4, label='φ_w', color='#e74c3c')
    ax.set_xticks(x); ax.set_xticklabels(df['topology'].str.upper())
    ax.set_ylabel("Значение метрики"); ax.set_title("Сравнение топологий")
    ax.legend(); ax.grid(axis='y', alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, "plot_topology.png")); plt.close()

# 2. FIFO vs Triage
def plot_strategy(df, out_dir):
    topologies = df['topology'].unique()
    fig, axs = plt.subplots(1, len(topologies), figsize=(6*len(topologies), 5), sharey=True)
    if len(topologies) == 1: axs = [axs]
    for ax, topo in zip(axs, topologies):
        sub = df[df['topology'] == topo]
        for gk, style in zip(['fifo', 'triage'], [{'ls':'--', 'marker':'s', 'color':'gray'}, {'ls':'-', 'marker':'o', 'color':'black'}]):
            gk_data = sub[sub['gatekeeper'] == gk]
            ax.errorbar(gk_data['R'], gk_data['lcc_mean'], yerr=gk_data['lcc_ci'], 
                        label=gk.upper(), fmt=style['marker'], ls=style['ls'], color=style['color'], capsize=3)
        for _, row in sub[sub['sig_direction'].str.contains('triage > fifo', na=False)].iterrows():
            ax.annotate('*', xy=(row['R'], row['lcc_mean']+0.05), fontsize=16, color='red', ha='center')
        ax.set_title(f"Топология: {topo.upper()}"); ax.set_xlabel("Ресурсы R"); ax.grid(alpha=0.3); ax.legend()
    axs[0].set_ylabel("LCC"); plt.suptitle("FIFO vs Triage")
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, "plot_strategy.png")); plt.close()

# 3. Векторы атак
def plot_attack(df, out_dir):
    strategies = df['attack_strategy'].unique(); topologies = df['topology'].unique()
    x = range(len(topologies)); w = 0.8 / len(strategies)
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, strat in enumerate(strategies):
        sub = df[df['attack_strategy'] == strat]
        vals = [sub[sub['topology']==t]['lcc_mean'].values[0] if t in sub['topology'].values else 0 for t in topologies]
        cis  = [sub[sub['topology']==t]['lcc_ci'].values[0] if t in sub['topology'].values else 0 for t in topologies]
        ax.bar([i + (i_pos - len(strategies)/2 + 0.5) * w for i_pos in x], vals, w*0.9, yerr=cis, capsize=3, label=strat)
    ax.set_xticks(x); ax.set_xticklabels([t.upper() for t in topologies])
    ax.set_ylabel("LCC"); ax.set_title("Векторы атак"); ax.legend(); ax.grid(axis='y', alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, "plot_attack.png")); plt.close()

# 4. Временные ряды
def plot_timeseries(out_dir):
    files = glob.glob(os.path.join(out_dir, "timeseries_*.csv"))
    if not files: return
    fig, axs = plt.subplots(len(files), 1, figsize=(10, 4*len(files)), sharex=True)
    if len(files) == 1: axs = [axs]
    for ax, f in zip(axs, files):
        df = pd.read_csv(f)
        topo = os.path.basename(f).replace("timeseries_", "").replace(".csv", "").upper()
        ax.plot(df['time'], df['lcc'], label='LCC', color='#e74c3c')
        ax.plot(df['time'], df['eff_norm'], label='E_norm', color='#3498db', ls='--')
        ax.plot(df['time'], df['weighted_surv'], label='φ_w', color='#2ecc71', ls='-.')
        ax.set_title(topo); ax.set_ylabel("Метрика"); ax.grid(alpha=0.3); ax.legend()
    axs[-1].set_xlabel("Время t"); plt.suptitle("Временные ряды")
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, "plot_timeseries.png")); plt.close()

# 5. Параметрический Sweep
def plot_sweep(out_dir):
    files = glob.glob(os.path.join(out_dir, "sweep_*.csv"))
    if not files: return
    fig, axs = plt.subplots(2, 2, figsize=(14, 10)); axs = axs.flatten()
    for i, f in enumerate(files[:4]):
        df = pd.read_csv(f); param = os.path.basename(f).replace("sweep_", "").replace(".csv", "")
        ax = axs[i]
        cols = [c for c in df.columns if c.endswith('_lcc_mean')]
        for col in cols:
            topo = col.replace('_lcc_mean', '').upper()
            ci_col = col.replace('_mean', '_ci')
            color = COLORS.get(col.replace('_lcc_mean', ''), 'gray')
            ax.plot(df['x_value'], df[col], 'o-', label=topo, color=color)
            ax.fill_between(df['x_value'], df[col]-df[ci_col], df[col]+df[ci_col], color=color, alpha=0.2)
        ax.set_title(f"Sweep: {param}"); ax.set_xlabel(param); ax.set_ylabel("LCC"); ax.grid(alpha=0.3); ax.legend()
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, "plot_sweep.png")); plt.close()

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    if not os.path.exists(out_dir):
        print(f"  [!] Папка {out_dir} не найдена!"); return
    print(f"  Анализ CSV в папке: {out_dir}")
    
    for name, func, csv_name in [
        ("Topology", plot_topology, "topology_comparison.csv"),
        ("Strategy", plot_strategy, "strategy_comparison.csv"),
        ("Attack", plot_attack, "attack_vector_analysis.csv")
    ]:
        f = os.path.join(out_dir, csv_name)
        if os.path.exists(f):
            df = safe_read(f)
            if df is not None: func(df, out_dir)
            
    plot_timeseries(out_dir)
    plot_sweep(out_dir)
    print("  ✓ Все графики сохранены.")

if __name__ == "__main__":
    main()