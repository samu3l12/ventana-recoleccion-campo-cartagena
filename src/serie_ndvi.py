"""Serie temporal de verdor (NDVI) de una parcela, vista desde Sentinel-2.

Para que sirve: el NDVI sube mientras el cultivo crece y CAE DE GOLPE el dia que
se recolecta. Esa caida es la fecha real de corte, y es la "verdad de campo" que
al modelo de prediccion le falta.

Todo gratis y sin credenciales: catalogo STAC publico de Element84 sobre AWS.
"""

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from pystac_client import Client

CATALOGO = "https://earth-search.aws.element84.com/v1"

# Clases de la banda SCL que hay que descartar (nubes, sombras, nieve, sin dato).
SCL_MALAS = {0, 1, 3, 8, 9, 10, 11}

OPCIONES_GDAL = dict(
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    AWS_NO_SIGN_REQUEST="YES",
    GDAL_HTTP_MAX_RETRY="3",
    GDAL_HTTP_RETRY_DELAY="1",
)


def _leer(url, bounds_wgs84):
    with rasterio.open(url) as src:
        b = transform_bounds("EPSG:4326", src.crs, *bounds_wgs84)
        return src.read(1, window=from_bounds(*b, transform=src.transform))


def serie(lat, lon, desde, hasta, lado_m=150, nubes_max=60, verbose=True):
    """Devuelve [(fecha, ndvi_medio, % pixeles validos), ...] ordenado por fecha."""
    d = lado_m / 111_320 / 2  # grados aproximados
    bounds = (lon - d, lat - d, lon + d, lat + d)

    items = sorted(
        Client.open(CATALOGO).search(
            collections=["sentinel-2-l2a"],
            intersects={"type": "Point", "coordinates": [lon, lat]},
            datetime=f"{desde}/{hasta}",
            query={"eo:cloud_cover": {"lt": nubes_max}},
        ).items(),
        key=lambda i: i.datetime,
    )
    if verbose:
        print(f"  {len(items)} escenas candidatas")

    out = []
    with rasterio.Env(**OPCIONES_GDAL):
        for it in items:
            try:
                red = _leer(it.assets["red"].href, bounds).astype("float32")
                nir = _leer(it.assets["nir"].href, bounds).astype("float32")
                scl = _leer(it.assets["scl"].href, bounds)
            except Exception:
                continue

            # SCL viene a 20 m: se replica para igualar la rejilla de 10 m.
            factor = max(1, round(red.shape[0] / max(1, scl.shape[0])))
            scl_10m = np.kron(scl, np.ones((factor, factor), dtype=scl.dtype))
            scl_10m = scl_10m[: red.shape[0], : red.shape[1]]
            if scl_10m.shape != red.shape:
                continue

            valido = ~np.isin(scl_10m, list(SCL_MALAS)) & (red + nir > 0)
            pct = 100 * valido.mean()
            if pct < 60:
                continue

            ndvi = (nir - red) / (nir + red + 1e-6)
            out.append((it.datetime.date(), float(np.nanmean(ndvi[valido])), pct))

    return out


if __name__ == "__main__":
    # Puntos candidatos en zona agricola del Campo de Cartagena.
    CANDIDATOS = {
        "Torre Pacheco oeste": (37.7550, -0.9450),
        "Los Infiernos":       (37.8100, -0.9000),
        "La Palma":            (37.7200, -0.9800),
    }
    for nombre, (lat, lon) in CANDIDATOS.items():
        print(f"\n=== {nombre}  ({lat}, {lon}) ===")
        s = serie(lat, lon, "2023-09-01", "2024-06-30")
        print(f"  {len(s)} fechas utiles")
        for fecha, v, pct in s:
            barra = "#" * int(max(0, v) * 50)
            print(f"  {fecha}  {v:5.2f} |{barra}")
