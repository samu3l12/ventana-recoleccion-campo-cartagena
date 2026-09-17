"""Dibuja la serie de verdor de varias parcelas y detecta la fecha de corte.

Genera: curva_ndvi_campo_cartagena.png
Cachea las series en series_ndvi.csv para no volver a descargar.
"""

import csv
import io
import os
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator

from serie_ndvi import serie

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RAIZ, "datos", "series_ndvi.csv")
DESDE, HASTA = "2023-09-01", "2024-06-30"

PARCELAS = {
    "La Palma (Cartagena)":   (37.7200, -0.9800),
    "Torre Pacheco oeste":    (37.7550, -0.9450),
    "Los Infiernos":          (37.8100, -0.9000),
}

# Una caida asi de brusca desde un cultivo crecido solo la produce la recoleccion.
PICO_MINIMO = 0.50
CAIDA_MINIMA = 0.25


def cargar():
    if os.path.exists(CACHE):
        datos = {}
        with io.open(CACHE, encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                datos.setdefault(fila["parcela"], []).append(
                    (date.fromisoformat(fila["fecha"]), float(fila["ndvi"]))
                )
        return datos

    datos = {}
    for nombre, (lat, lon) in PARCELAS.items():
        print(f"descargando {nombre}...")
        datos[nombre] = [(f, v) for f, v, _ in serie(lat, lon, DESDE, HASTA)]
    with io.open(CACHE, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["parcela", "fecha", "ndvi"])
        for nombre, s in datos.items():
            for f_, v in s:
                w.writerow([nombre, f_.isoformat(), f"{v:.4f}"])
    return datos


def detectar_cortes(s):
    """Devuelve [(fecha_anterior, fecha_posterior, caida), ...]."""
    cortes = []
    for (f1, v1), (f2, v2) in zip(s, s[1:]):
        if v1 >= PICO_MINIMO and (v1 - v2) >= CAIDA_MINIMA:
            cortes.append((f1, f2, v1 - v2))
    return cortes


def main():
    datos = cargar()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    colores = {"La Palma (Cartagena)": "#1b7f4f",
               "Torre Pacheco oeste": "#b07a2a",
               "Los Infiernos": "#8a8a8a"}

    for nombre, s in datos.items():
        xs = [f for f, _ in s]
        ys = [v for _, v in s]
        principal = nombre.startswith("La Palma")
        ax.plot(xs, ys, marker="o", ms=4,
                lw=2.6 if principal else 1.4,
                color=colores[nombre],
                alpha=1.0 if principal else 0.55,
                label=nombre, zorder=3 if principal else 2)

        if principal:
            for f1, f2, caida in detectar_cortes(s):
                ax.axvspan(f1, f2, color="#d23b3b", alpha=0.13, zorder=1)
                medio = f1 + (f2 - f1) / 2
                ax.annotate(
                    f"CORTE\nentre {f1.strftime('%d/%m')} y {f2.strftime('%d/%m')}\n"
                    f"(caída {caida:.2f})",
                    xy=(medio, 0.50), ha="center", va="center", fontsize=8.5,
                    color="#8a1f1f", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.35", fc="white",
                              ec="#d23b3b", lw=1),
                    zorder=5)

    ax.axhspan(0.0, 0.20, color="#c8a06a", alpha=0.18, zorder=0)
    ax.text(date(2023, 9, 10), 0.045, "suelo desnudo", fontsize=8.5,
            color="#7a5a2a", style="italic")
    ax.axhspan(0.60, 0.90, color="#2f9e63", alpha=0.10, zorder=0)
    ax.text(date(2023, 9, 10), 0.845, "cultivo crecido", fontsize=8.5,
            color="#1b7f4f", style="italic")

    ax.set_title("Verdor (NDVI) de tres parcelas del Campo de Cartagena\n"
                 "Sentinel-2, campaña 2023-2024 · la caída brusca es la recolección",
                 fontsize=13, fontweight="bold", loc="left")
    ax.set_ylabel("NDVI  (0 = tierra desnuda,  0,9 = cultivo pleno)")
    ax.set_ylim(0, 0.92)
    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter("%b\n%Y"))
    ax.grid(alpha=0.25, ls=":")
    ax.legend(loc="upper right", framealpha=0.95)
    fig.text(0.01, 0.015,
             "Datos: Sentinel-2 L2A (Copernicus) vía catálogo STAC público. "
             "Sin coste ni credenciales. Ventana de 150 m por parcela; "
             "píxeles con nube descartados con la banda SCL.",
             fontsize=7.5, color="#555")
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    salida = os.path.join(RAIZ, "figuras", "curva_ndvi_campo_cartagena.png")
    fig.savefig(salida, dpi=160)
    print(f"guardado: {salida}")

    for nombre, s in datos.items():
        cortes = detectar_cortes(s)
        print(f"\n{nombre}: {len(s)} observaciones, {len(cortes)} corte(s)")
        for f1, f2, caida in cortes:
            print(f"   corte entre {f1} y {f2}  ({(f2-f1).days} dias de "
                  f"incertidumbre, caida {caida:.2f})")


if __name__ == "__main__":
    main()
