"""Cómo 've' el satélite el verdor: foto en color y mapa NDVI, antes y después del corte.

Genera como_se_calcula_ndvi.png con 4 paneles para la parcela de La Palma:
  arriba   foto en color (lo que vería una persona)
  abajo    NDVI píxel a píxel (lo que usa el análisis)
  izquierda 11/12/2023 (cultivo crecido) · derecha 25/01/2024 (ya cortado)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from pystac_client import Client

from serie_ndvi import CATALOGO, OPCIONES_GDAL

LAT, LON = 37.7200, -0.9800
LADO_VISTA_M = 1200      # zona que se enseña
LADO_PARCELA_M = 150     # ventana que usa el análisis
FECHAS = ["2023-12-11", "2024-01-25"]


def bounds(lado_m):
    d = lado_m / 111_320 / 2
    return (LON - d, LAT - d, LON + d, LAT + d)


def leer(url, b):
    with rasterio.open(url) as src:
        bb = transform_bounds("EPSG:4326", src.crs, *b)
        return src.read(1, window=from_bounds(*bb, transform=src.transform)).astype("float32")


def escena(fecha):
    items = list(Client.open(CATALOGO).search(
        collections=["sentinel-2-l2a"],
        intersects={"type": "Point", "coordinates": [LON, LAT]},
        datetime=f"{fecha}T00:00:00Z/{fecha}T23:59:59Z",
    ).items())
    return min(items, key=lambda i: i.properties.get("eo:cloud_cover", 100))


def main():
    b = bounds(LADO_VISTA_M)
    datos = []
    with rasterio.Env(**OPCIONES_GDAL):
        for f in FECHAS:
            it = escena(f)
            bandas = {k: leer(it.assets[k].href, b) for k in ("red", "green", "blue", "nir")}
            h = min(x.shape[0] for x in bandas.values())
            w = min(x.shape[1] for x in bandas.values())
            bandas = {k: v[:h, :w] for k, v in bandas.items()}
            rgb = np.dstack([bandas["red"], bandas["green"], bandas["blue"]])
            rgb = np.clip(rgb / 2500.0, 0, 1) ** 0.8
            ndvi = (bandas["nir"] - bandas["red"]) / (bandas["nir"] + bandas["red"] + 1e-6)
            c0, c1 = h // 2, w // 2
            r = int(LADO_PARCELA_M / 10 / 2)
            centro = ndvi[c0 - r:c0 + r, c1 - r:c1 + r]
            px = (bandas["red"][c0, c1], bandas["nir"][c0, c1], ndvi[c0, c1])
            datos.append((f, rgb, ndvi, float(np.nanmean(centro)), px, r))
            print(f, "escena", it.id, "| NDVI ventana 150 m:", round(float(np.nanmean(centro)), 2),
                  "| píxel central rojo/NIR/NDVI:", [round(float(v), 2) for v in px])

    fig, axs = plt.subplots(2, 2, figsize=(12, 12.6))
    fig.patch.set_facecolor("#F1F3EE")
    titulos = {"2023-12-11": "11 dic 2023 · cultivo crecido", "2024-01-25": "25 ene 2024 · ya cortado"}
    for col, (f, rgb, ndvi, media, px, r) in enumerate(datos):
        h, w = ndvi.shape
        for fila, img in enumerate((rgb, ndvi)):
            ax = axs[fila, col]
            if fila == 0:
                ax.imshow(rgb)
            else:
                im = ax.imshow(ndvi, cmap="RdYlGn", vmin=-0.1, vmax=0.9)
            ax.add_patch(plt.Rectangle((w // 2 - r, h // 2 - r), 2 * r, 2 * r,
                                       fill=False, ec="white" if fila == 0 else "black", lw=2.5))
            ax.set_xticks([]); ax.set_yticks([])
            if fila == 0:
                ax.set_title(titulos[f], fontsize=16, fontweight="bold", color="#151E19", pad=10)
            else:
                ax.set_title(f"NDVI medio en el recuadro: {media:.2f}".replace(".", ","),
                             fontsize=15, color="#151E19", pad=10)
    axs[0, 0].set_ylabel("Foto en color", fontsize=15, color="#5B6A61")
    axs[1, 0].set_ylabel("Mapa de verdor (NDVI)", fontsize=15, color="#5B6A61")
    cb = fig.colorbar(im, ax=axs[1, :], orientation="horizontal", fraction=0.05, pad=0.04)
    cb.set_label("NDVI:  0 = tierra o camino   ·   0,8 = cultivo denso y sano", fontsize=13)
    fig.suptitle("Lo que ve Sentinel-2 en una parcela de La Palma (Cartagena)",
                 fontsize=19, fontweight="bold", color="#151E19", y=0.985)
    fig.text(0.5, 0.945, "Zona de 1,2 km · píxeles de 10 m · recuadro = los 150 m que usa el análisis",
             ha="center", fontsize=13, color="#5B6A61")
    import os
    salida = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "figuras", "como_se_calcula_ndvi.png")
    fig.savefig(salida, dpi=110, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"guardado: {salida}")


if __name__ == "__main__":
    main()
