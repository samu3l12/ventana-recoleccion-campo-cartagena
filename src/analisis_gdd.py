"""Cuanto se mueve la ventana de recoleccion en el Campo de Cartagena.

Pregunta de negocio: una comercializadora planifica siembras con un calendario
fijo ("trasplanto la semana 38, recolecto a los 90 dias"). ¿Cuanto se desvia la
realidad termica de ese calendario, ano a ano?

Metodo: integral termica (grados-dia de crecimiento, GDD) sobre 19 campanas
reales de la red SIAM del IMIDA.

    GDD_dia = max(0, (tmax + tmin) / 2 - T_base)

Se acumula desde la fecha de trasplante hasta alcanzar el requerimiento del
cultivo, y se anota cuantos dias han hecho falta.

PARAMETROS A CALIBRAR (no son verdades absolutas, son puntos de partida de
literatura; con datos reales de una empresa se ajustan y es ahi donde el modelo
pasa de orientativo a util):
    brocoli  T_base 4.4 C, ~850 GDD de trasplante a corte
    lechuga  T_base 4.0 C, ~600 GDD de trasplante a corte
"""

import csv
import io
import statistics
from datetime import datetime

CULTIVOS = {
    "brocoli": {"t_base": 4.4, "gdd_objetivo": 850},
    "lechuga": {"t_base": 4.0, "gdd_objetivo": 600},
}

ESTACIONES = ["CA42", "CA52", "CA91", "TP42", "TP73"]  # series largas y completas


def cargar(codest):
    """Serie diaria -> {fecha: (tmax, tmin)}, descartando dias incompletos."""
    serie = {}
    with io.open(f"diario_{codest}.csv", encoding="latin-1") as f:
        for fila in csv.DictReader(f):
            try:
                fecha = datetime.strptime(fila["fecha"].strip(), "%d/%m/%Y").date()
                serie[fecha] = (float(fila["tmax"]), float(fila["tmin"]))
            except (ValueError, KeyError):
                continue
    return serie


def dias_hasta_objetivo(serie, inicio, t_base, gdd_objetivo, tope=200):
    """Dias desde 'inicio' hasta acumular gdd_objetivo. None si la serie se corta."""
    acumulado = 0.0
    fecha = inicio
    for dia in range(1, tope + 1):
        fecha = fecha.replace() if False else fecha
        fecha = inicio.fromordinal(inicio.toordinal() + dia)
        if fecha not in serie:
            return None
        tmax, tmin = serie[fecha]
        acumulado += max(0.0, (tmax + tmin) / 2 - t_base)
        if acumulado >= gdd_objetivo:
            return dia
    return None


def semana_a_fecha(ano, semana):
    """Lunes de la semana ISO indicada."""
    return datetime.strptime(f"{ano}-W{semana:02d}-1", "%G-W%V-%u").date()


def analizar(cultivo, semanas_trasplante):
    par = CULTIVOS[cultivo]
    series = {c: cargar(c) for c in ESTACIONES}

    print(f"\n{'='*78}")
    print(f"CULTIVO: {cultivo.upper()}   T_base={par['t_base']} C   "
          f"objetivo={par['gdd_objetivo']} GDD")
    print(f"Estaciones: {', '.join(ESTACIONES)}   Campanas: 2000-2018")
    print(f"{'='*78}")
    print(f"{'Semana':>7} {'n':>4} {'media':>7} {'min':>5} {'max':>5} "
          f"{'rango':>6} {'desv':>6}   ciclo en dias hasta corte")
    print("-" * 78)

    resumen = []
    for semana in semanas_trasplante:
        duraciones = []
        for ano in range(2000, 2019):
            inicio = semana_a_fecha(ano, semana)
            for serie in series.values():
                d = dias_hasta_objetivo(serie, inicio, par["t_base"],
                                        par["gdd_objetivo"])
                if d is not None:
                    duraciones.append(d)
        if len(duraciones) < 10:
            continue
        media = statistics.mean(duraciones)
        rango = max(duraciones) - min(duraciones)
        resumen.append((semana, media, rango))
        print(f"{semana:>7} {len(duraciones):>4} {media:>7.1f} {min(duraciones):>5} "
              f"{max(duraciones):>5} {rango:>6} {statistics.stdev(duraciones):>6.1f}")

    if resumen:
        peor = max(resumen, key=lambda x: x[2])
        print("-" * 78)
        print(f"LECTURA: para un trasplante en la semana {peor[0]}, el mismo cultivo "
              f"ha tardado\n         entre el minimo y el maximo observados "
              f"{peor[2]} dias de diferencia segun el ano.")
        print(f"         Un calendario fijo de {peor[1]:.0f} dias se equivoca en "
              f"ambos sentidos.")


if __name__ == "__main__":
    analizar("brocoli", semanas_trasplante=[35, 38, 41, 44, 47])
    analizar("lechuga", semanas_trasplante=[38, 41, 44, 47, 50])
