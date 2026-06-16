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
    "font.family": "DejaVu Sans",
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 120
})

# Стили топологий для ЧБ-совместимости (разные маркеры + стили линий)
TOPO_STYLES = {
    "full_mesh": {"color": "#1f77b4", "marker": "o", "ls": "-",  "hatch": "///", "label": "FULL_MESH"},
    "ring":      {"color": "#2ca02c", "marker": "s", "ls": "--", "hatch": "\\\\", "label": "RING"},
    "star":      {"color": "#d62728", "marker": "^", "ls": "-.", "hatch": "xxx",  "label": "STAR"},
}

# Цвета для атак
ATTACK_COLORS = {
    'targeted': '#e74c3c',    # красный
    'random': '#3498db',      # синий
    'cascading': '#2ecc71'    # зелёный
}

def safe_read(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"  [!] Ошибка чтения {path}: {e}")
        return None

# 1. Сравнение топологий (ЧБ-совместимый с штриховкой)
def plot_topology(df, out_dir):
    """ЧБ-совместимый график: разные паттерны штриховки для баров."""
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(df))
    w = 0.25
    
    # LCC — сплошная штриховка
    ax.bar([i - w for i in x], df['lcc_mean'], w, yerr=df['lcc_ci'], 
           capsize=4, label='LCC', color='#3498db', hatch='///', edgecolor='black', alpha=0.85)
    # E_norm — обратная штриховка
    ax.bar(x, df['eff_mean'], w, yerr=df['eff_ci'], 
           capsize=4, label='E_norm', color='#2ecc71', hatch='\\\\\\', edgecolor='black', alpha=0.85)
    # φ_w — кресты
    ax.bar([i + w for i in x], df['wsurv_mean'], w, yerr=df['wsurv_ci'], 
           capsize=4, label='φ_w', color='#e74c3c', hatch='xxx', edgecolor='black', alpha=0.85)
    
    ax.set_xticks(x)
    ax.set_xticklabels(df['topology'].str.upper())
    ax.set_ylabel("Значение метрики")
    ax.set_title("Сравнение топологий")
    ax.legend(loc='upper right', frameon=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_topology.png"), dpi=150)
    plt.close()
    print("  Сохранено: plot_topology.png")

# 2. FIFO vs Triage (два графика: LCC и φ_w)
def plot_strategy(df, out_dir):
    """Создаёт ДВА графика: по LCC и по взвешенной живучести."""
    topologies = df['topology'].unique()
    
    # Создаём два графика: LCC и Weighted Survivability
    for metric, ylabel, suffix in [
        ('lcc_mean', 'LCC', 'lcc'),
        ('wsurv_mean', 'Взвешенная живучесть φ_w', 'wsurv')
    ]:
        ci_col = metric.replace('_mean', '_ci')
        
        fig, axs = plt.subplots(1, len(topologies), figsize=(6*len(topologies), 5), sharey=True)
        if len(topologies) == 1: 
            axs = [axs]
            
        for ax, topo in zip(axs, topologies):
            sub = df[df['topology'] == topo]
            
            # FIFO
            fifo_data = sub[sub['gatekeeper'] == 'fifo']
            ax.errorbar(fifo_data['R'], fifo_data[metric], yerr=fifo_data[ci_col],
                       label='FIFO', fmt='s', ls='--', color='gray', capsize=3, alpha=0.7, markersize=8)
            
            # Triage
            triage_data = sub[sub['gatekeeper'] == 'triage']
            ax.errorbar(triage_data['R'], triage_data[metric], yerr=triage_data[ci_col],
                       label='Triage', fmt='o', ls='-', color='black', capsize=3, markersize=8)
            
            # Отмечаем значимые точки
            for _, row in sub[sub['sig_direction'].str.contains('triage > fifo', na=False)].iterrows():
                ax.annotate('*', xy=(row['R'], row[metric]+0.05), fontsize=16, color='red', ha='center')
            
            ax.set_title(f"Топология: {topo.upper()}")
            ax.set_xlabel("Ресурсы R")
            ax.grid(alpha=0.3, linestyle='--')
            ax.legend()
            
        if len(axs) > 0:
            axs[0].set_ylabel(ylabel)
        plt.suptitle(f"FIFO vs Triage — {ylabel}")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"plot_strategy_{suffix}.png"), dpi=150)
        plt.close()
        print(f"  Сохранено: plot_strategy_{suffix}.png")

# 3. Векторы атак (исправленная версия с правильной группировкой)
def plot_attack(df, out_dir):
    """Исправленная версия с правильной группировкой."""
    strategies = df['attack_strategy'].unique()
    topologies = df['topology'].unique()
    
    # Создаём фигуру с подграфиками — по одному на топологию
    fig, axs = plt.subplots(1, len(topologies), figsize=(6*len(topologies), 5), sharey=True)
    if len(topologies) == 1:
        axs = [axs]
    
    for ax, topo in zip(axs, topologies):
        sub = df[df['topology'] == topo]
        x = range(len(strategies))
        
        # Для каждой топологии рисуем столбцы по атакам
        vals = [sub[sub['attack_strategy']==s]['lcc_mean'].values[0] 
                for s in strategies]
        cis = [sub[sub['attack_strategy']==s]['lcc_ci'].values[0] 
               for s in strategies]
        colors = [ATTACK_COLORS.get(s, 'gray') for s in strategies]
        
        ax.bar(x, vals, yerr=cis, capsize=5, color=colors, alpha=0.8, edgecolor='black')
        ax.set_xticks(x)
        ax.set_xticklabels([s.upper() for s in strategies], rotation=15)
        ax.set_title(f"Топология: {topo.upper()}")
        ax.set_ylabel("LCC")
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_ylim(0, 1.0)
    
    if len(axs) > 0:
        axs[0].set_ylabel("LCC")
    plt.suptitle("Векторы атак по топологиям")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_attack.png"), dpi=150)
    plt.close()
    print("  Сохранено: plot_attack.png")

# 4. Временные ряды
def plot_timeseries(out_dir):
    files = glob.glob(os.path.join(out_dir, "timeseries_*.csv"))
    if not files:
        return
    
    fig, axs = plt.subplots(len(files), 1, figsize=(10, 4*len(files)), sharex=True)
    if len(files) == 1:
        axs = [axs]
    
    for ax, f in zip(axs, files):
        df = pd.read_csv(f)
        topo = os.path.basename(f).replace("timeseries_", "").replace(".csv", "").upper()
        ax.plot(df['time'], df['lcc'], label='LCC', color='#e74c3c', linewidth=2)
        ax.plot(df['time'], df['eff_norm'], label='E_norm', color='#3498db', ls='--', linewidth=2)
        ax.plot(df['time'], df['weighted_surv'], label='φ_w', color='#2ecc71', ls='-.', linewidth=2)
        ax.set_title(topo)
        ax.set_ylabel("Метрика")
        ax.grid(alpha=0.3, linestyle='--')
        ax.legend()
    
    axs[-1].set_xlabel("Время t")
    plt.suptitle("Временные ряды")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_timeseries.png"), dpi=150)
    plt.close()
    print("  Сохранено: plot_timeseries.png")

# 5. Параметрический Sweep (ЧБ-совместимый с разными маркерами)
def plot_sweep(out_dir):
    files = glob.glob(os.path.join(out_dir, "sweep_*.csv"))
    if not files:
        return
    
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    axs = axs.flatten()
    
    for i, f in enumerate(files[:4]):
        df = pd.read_csv(f)
        param = os.path.basename(f).replace("sweep_", "").replace(".csv", "")
        ax = axs[i]
        
        cols = [c for c in df.columns if c.endswith('_lcc_mean')]
        for col in cols:
            topo = col.replace('_lcc_mean', '').upper()
            ci_col = col.replace('_mean', '_ci')
            style = TOPO_STYLES.get(col.replace('_lcc_mean', ''), 
                                    {"color": "gray", "marker": "o", "ls": "-"})
            
            ax.plot(df['x_value'], df[col], 
                    marker=style['marker'], 
                    linestyle=style['ls'],
                    linewidth=2,
                    markersize=8,
                    label=topo, 
                    color=style['color'],
                    markeredgecolor='black',
                    markeredgewidth=0.5)
            ax.fill_between(df['x_value'], 
                           df[col]-df[ci_col], df[col]+df[ci_col], 
                           color=style['color'], alpha=0.15)
        
        ax.set_title(f"Sweep: {param}", fontsize=12, fontweight='bold')
        ax.set_xlabel(param)
        ax.set_ylabel("LCC")
        ax.grid(alpha=0.3, linestyle='--')
        ax.legend(loc='best', frameon=True, fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_sweep.png"), dpi=150)
    plt.close()
    print("  Сохранено: plot_sweep.png")

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    if not os.path.exists(out_dir):
        print(f"  [!] Папка {out_dir} не найдена!")
        return
    
    print(f"  Анализ CSV в папке: {out_dir}")
    
    for name, func, csv_name in [
        ("Topology", plot_topology, "topology_comparison.csv"),
        ("Strategy", plot_strategy, "strategy_comparison.csv"),
        ("Attack", plot_attack, "attack_vector_analysis.csv")
    ]:
        f = os.path.join(out_dir, csv_name)
        if os.path.exists(f):
            df = safe_read(f)
            if df is not None:
                func(df, out_dir)
    
    plot_timeseries(out_dir)
    plot_sweep(out_dir)
    print("  ✓ Все графики сохранены.")

if __name__ == "__main__":
    main()