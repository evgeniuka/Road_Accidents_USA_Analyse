import matplotlib
import os

if os.getenv("MPLBACKEND"):
    matplotlib.use(os.environ["MPLBACKEND"])

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def plot_corr(corr: pd.DataFrame) -> None:
    plt.figure(figsize=(12, 9), dpi=200)
    plt.imshow(corr, vmin=-1, vmax=1)
    plt.xticks(range(len(corr)), corr.columns, rotation=90, fontsize=6)
    plt.yticks(range(len(corr)), corr.index, fontsize=6)
    plt.colorbar()
    plt.tight_layout()
    plt.show()


def bar_plot(df: pd.DataFrame, x_col: str, y_col: str, plot_title=None, filename: str = 'temp/barplot.png') -> None:
    t = df[[x_col, y_col]].copy()
    t[y_col] = pd.to_numeric(t[y_col], errors="coerce").fillna(0)
    TOP_N = 15
    t = t.sort_values(y_col, ascending=False).head(TOP_N)
    plt.figure(figsize=(12, 6), dpi=120)
    plt.bar(t[x_col].astype(str), t[y_col].values)
    plt.title(plot_title or y_col)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()



def multi_bar_plot(df, x_col, y_cols, title="KPIs by year"):
    data = df.copy()
    x = data[x_col].astype(str).tolist()
    n = len(y_cols)
    idx = np.arange(len(x))
    total_width = 0.8
    width = total_width / max(n, 1)
    fig, ax = plt.subplots()
    for i, col in enumerate(y_cols):
        y = pd.to_numeric(data[col], errors="coerce").fillna(0.0).values
        offset = (i - (n - 1) / 2) * width
        ax.bar(idx + offset, y, width, label=col)
    ax.set_xticks(idx)
    ax.set_xticklabels(x, rotation=45, ha="right")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    plt.show()



def line_plot(df: pd.DataFrame, x_col: str, y_col: str, plot_title = None, filename: str = 'temp/lineplot.png') -> None:
    plt.figure(figsize=(12, 9))
    plt.title(plot_title)
    for x, y in zip(df[x_col], df[y_col]):
        plt.text(x, y+2, f'{y}', ha='center', va='bottom', fontsize=12)
    sns.lineplot(data=df, x=x_col, y=y_col, marker="o")
    plt.show()



def stacked_components_bar(df, x_col, stack_cols, title=None, ylabel=None):
    x = df[x_col].astype(str).tolist()
    idx = np.arange(len(x))
    bottom = np.zeros(len(x))
    for col in stack_cols:
        y = pd.to_numeric(df[col], errors="coerce").fillna(0).values
        plt.bar(idx, y, bottom=bottom, label=col)
        bottom += y
    plt.xticks(idx, x, rotation=45, ha="right")
    if title: plt.title(title)
    if ylabel: plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.show()
