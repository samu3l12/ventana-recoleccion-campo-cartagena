# Ventana de recolección en el Campo de Cartagena

Quería saber cuánto se mueve la fecha de corte del brócoli y de la lechuga de un año a otro en el Campo de Cartagena, y si se puede ver ese corte desde satélite. Esto es lo que he sacado hasta ahora con datos públicos. Todavía no es un modelo de predicción.

## De dónde sale la pregunta

Muchas comercializadoras planifican con un calendario fijo: si trasplantas la semana 44, recolectas a los 108 días. Pero el cultivo no mira el calendario, mira el calor que acumula. Así que quise medir cuánto se separa la realidad del calendario según el año.

## El calendario falla en los trasplantes de otoño

Usé las series diarias de temperatura de 5 estaciones de la red SIAM del IMIDA, de 2000 a 2018 (19 campañas). Para cada semana de trasplante sumo los grados-día, `max(0, (tmax + tmin) / 2 - T_base)`, hasta llegar a lo que necesita el cultivo, y cuento cuántos días han hecho falta.

Brócoli, con temperatura base de 4,4 °C y 850 grados-día, juntando las 5 estaciones:

| Semana de trasplante | Días de media | Caso más rápido | Caso más lento | Diferencia |
|---|---|---|---|---|
| 35 (finales de agosto) | 47 | 40 | 56 | 16 días |
| 38 | 58 | 48 | 77 | 29 días |
| 41 | 83 | 61 | 119 | 58 días |
| 44 (principios de noviembre) | 108 | 83 | 148 | 65 días |
| 47 | 116 | 95 | 142 | 47 días |

Ojo con cómo se lee: esa tabla junta estaciones distintas. En la semana 44, el caso más rápido (83 días) es de Los Infiernos en 2006 y el más lento (148) de Torre Blanca en 2004, así que la diferencia de 65 días mezcla el año con la zona. Si miro cada estación por separado, solo por el año la diferencia va de 37 a 49 días. Sigue siendo mucho para planificar con calendario. Con la lechuga pasa algo parecido: hasta 52 días de diferencia en la semana 47, juntando estaciones.

En los trasplantes de finales de verano el calendario aguanta bastante bien. A partir de octubre ya no, y es justo la parte de la campaña que va al mercado europeo de invierno.

## Desde satélite se ve el corte, cuando no hay nubes

![Verdor de tres parcelas del Campo de Cartagena](figuras/curva_ndvi_campo_cartagena.png)

Saqué el verdor (NDVI) de Sentinel-2 para tres parcelas, del catálogo STAC público de Element84 en AWS, que no pide cuenta ni cuesta nada. Para cada parcela uso un cuadrado de 150 m y quito los píxeles con nubes usando la banda SCL.

Mientras el cultivo crece el verdor sube, y cuando se corta baja de golpe. En la parcela de La Palma bajó de 0,77 a 0,17 (el máximo de la campaña fue 0,81).

El problema es que entre el 21 de diciembre y el 25 de enero no hay ninguna imagen útil por las nubes. Sé que la parcela se cortó en ese tiempo, pero no qué semana: hay 35 días de margen. Para comprobar una predicción a 5 días vista eso no me sirve.

![Foto en color y mapa de verdor antes y después del corte](figuras/como_se_calcula_ndvi.png)

## Cosas que me encontré por el camino

- El portal del SIAM (`siam.imida.es`) no deja descargar las series de forma automática. Al final encontré los CSV en el catálogo de datos abiertos de la CARM, pero solo llegan hasta 2018. Para lo más reciente habrá que tirar de Open-Meteo.
- Las tres parcelas las elegí a ojo sobre el mapa, y una de ellas (Los Infiernos) resultó no ser una parcela cultivada: su verdor sale plano todo el año. Por eso quiero pasar a elegirlas con SIGPAC.
- En la imagen de diciembre se ve que mi cuadrado de 150 m en La Palma cae entre dos parcelas distintas. Hay que recortar por el contorno real de cada una.
- El hueco de nubes cae justo en invierno, que es cuando más interesa ver el corte.

## Qué falta para que esto prediga algo

1. Tapar los huecos de nubes. Quiero probar Sentinel-1, que es radar y ve a través de ellas.
2. Calibrar los parámetros: la temperatura base y los grados-día los he sacado de bibliografía, no de datos de campo de esta zona.
3. Elegir las parcelas con SIGPAC y recortarlas por su contorno.
4. Contrastar con fechas de corte reales de alguna campaña. Sin eso no puedo saber cuánto me equivoco.

## Datos

- Temperaturas: red SIAM del IMIDA, desde el catálogo de datos abiertos de la CARM (CKAN), 2000-2018.
- Verdor: Copernicus Sentinel-2 L2A, una imagen cada 5 días más o menos.
- Clima posterior a 2018: archivo histórico de Open-Meteo (todavía no lo uso).

## Archivos

```
src/descargar_siam.py   Descarga las estaciones del Campo de Cartagena y sus series diarias
src/analisis_gdd.py     Grados-día por semana de trasplante (la tabla de arriba)
src/serie_ndvi.py       Serie de verdor de una parcela en Sentinel-2, quitando nubes
src/grafico_ndvi.py     Gráfico de las tres parcelas y detección de la caída del corte
src/ver_ndvi.py         Foto en color y mapa de verdor, antes y después del corte
datos/estaciones.csv    Estaciones de la red SIAM
datos/series_ndvi.csv   Series de verdor ya calculadas, para no descargarlas otra vez
```

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
cd src
python descargar_siam.py   # baja las series diarias del SIAM (no están en el repo)
python analisis_gdd.py     # tabla de días por semana de trasplante
python grafico_ndvi.py     # gráfico de verdor y detección del corte
```

## Si trabajas en esto

Si planificas recolecciones en el Campo de Cartagena y esto se parece a lo que ves cada campaña, o no se parece en nada, me interesa mucho saberlo. Escríbeme por LinkedIn: [linkedin.com/in/samuel-escribano-garcia](https://www.linkedin.com/in/samuel-escribano-garcia/)

---

Datos climáticos: IMIDA, red SIAM, portal de datos abiertos de la Región de Murcia. Imágenes: Copernicus Sentinel-2.
