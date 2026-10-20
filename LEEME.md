# La confianza como estimador

Depósito de datos, fichas de codificación y código de replicación del paper "La confianza como estimador. Índice de Confianza en el Gobierno y voto oficialista en elecciones generales presidenciales argentinas, 2003-2023" (Abril Guajardo y Claudio Andrés Spinelli, Universidad Católica de La Plata, 2026), con el protocolo prospectivo para la elección presidencial de 2027.

## Contenido

datos/icgmensual.csv: serie mensual del Índice de Confianza en el Gobierno (ICG), 298 olas de noviembre de 2001 a agosto de 2026, calculada desde la base pública de microdatos de la Universidad Torcuato Di Tella con el ponderador oficial, a cuatro decimales. La base de microdatos se tomó del respaldo público del repositorio data_warehouse de PolíticaArgentina (github.com/PoliticaArgentina/data_warehouse, carpeta opinAr/data_raw). Es la versión de la base que fija el protocolo 2027.

datos/instancias.csv: las doce instancias electorales (seis generales, cuatro primarias, dos balotajes) con el voto oficialista sobre votos afirmativos, el ICG en t-1 y t-3, la continuidad, el número de candidaturas del espacio oficialista, la mediana de expectativas de inflación y la fuente de cada resultado electoral.

fichas/fichas de codificacion.docx y .pdf: las diez fichas de codificación de continuidad y concentración de la oferta, una por instancia, con las fuentes leídas y las codificaciones alternativas de 2015 y 2023.

codigo/serieicg.py: construye icgmensual.csv desde la base de microdatos.

codigo/replicacion.py: reproduce todos los números del paper (correlaciones, test de permutación, regresión, intervalos de predicción, distancia de Cook, validación cruzada, validación temporal con ventana expansiva, referencias, regla por veinte, primarias, balotajes) y fija las dos ecuaciones del protocolo 2027 y la función que calcula sus intervalos de predicción.

## Protocolo 2027

Ecuación t-1 (mes previo a la general): voto = 14,2291 + 14,8679 x ICG. Ecuación t-3 (tres meses antes, previo a la primaria): voto = 11,0692 + 16,2205 x ICG. Ambas ajustadas sobre las seis generales con la serie de este depósito, sin reestimación posterior. Criterio de éxito: error absoluto menor o igual a siete puntos, por predicción y por separado. Las predicciones se publican en este repositorio antes de cada votación, con fecha, versión de la base y fecha de corte.

## Requisitos

Python 3 con pandas, numpy y scipy.
