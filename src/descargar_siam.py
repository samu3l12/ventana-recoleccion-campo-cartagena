"""Descarga la red de estaciones agroclimaticas del IMIDA (SIAM) para una zona.

Fuente: portal de datos abiertos de la CARM (CKAN).
  - Listado de estaciones: IMIDA_estaciones.csv
  - Serie diaria por estacion: IMIDA_Diario_<CODEST>.csv

Columnas de la serie diaria:
  fecha, tmed, tmax, tmin, hrmed, hrmax, hrmin, radmed, vvmed, vvmax, dvmed, prec, eto

LIMITACION CONOCIDA: los CSV abiertos llegan hasta 2018. Para datos recientes hay
que ir al portal SIAM (siam.imida.es), que no expone descarga masiva publica.
Para un modelo fenologico climatologico, 2000-2018 es mas que suficiente.
"""

import csv
import io
import os
import urllib.request

BASE = "https://datosabiertos.carm.es/odata/Agricultura"
ESTACIONES = f"{BASE}/IMIDA_estaciones.csv"

# Municipios del Campo de Cartagena y su entorno agricola inmediato.
ZONA_CAMPO_CARTAGENA = (
    "cartagena",
    "torre pacheco",
    "fuente alamo",
    "san javier",
)


def descargar(url, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return destino
    with urllib.request.urlopen(url, timeout=90) as r, open(destino, "wb") as f:
        f.write(r.read())
    return destino


def estaciones(zona=ZONA_CAMPO_CARTAGENA):
    """Devuelve las estaciones cuyo municipio esta en la zona indicada."""
    descargar(ESTACIONES, "estaciones.csv")
    with io.open("estaciones.csv", encoding="latin-1") as f:
        for fila in csv.DictReader(f):
            municipio = fila["MUNICIPIO"].strip().lower()
            if any(z in municipio for z in zona):
                yield fila


def serie_diaria(codest):
    """Descarga (si hace falta) y devuelve la serie diaria de una estacion."""
    destino = f"diario_{codest}.csv"
    descargar(f"{BASE}/IMIDA_Diario_{codest}.csv", destino)
    with io.open(destino, encoding="latin-1") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    for est in estaciones():
        try:
            filas = serie_diaria(est["CODEST"])
            print(f"{est['CODEST']:6} {est['MUNICIPIO']:16} {est['PARAJE'][:22]:24} "
                  f"{len(filas):>6} dias  {filas[0]['fecha']} -> {filas[-1]['fecha']}")
        except Exception as e:
            print(f"{est['CODEST']:6} {est['MUNICIPIO']:16} ERROR: {e}")
