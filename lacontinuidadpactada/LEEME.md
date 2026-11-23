# La continuidad pactada: bases de cálculo del pronóstico

Esta carpeta publica las bases, el código y las tablas con que el libro "La continuidad pactada. Un acuerdo para que la Argentina sobreviva a sus elecciones" (Andy Spinelli, 2026) estima el voto oficialista de la primera vuelta presidencial argentina de 2027. Se publica antes de la elección para que el pronóstico se pueda controlar después con los mismos datos.

## Primera regla: el Índice de Confianza en el Gobierno

Usa la serie y el código de la carpeta principal de este repositorio: datos/icgmensual.csv, datos/instancias.csv y codigo/replicacion.py. Las ecuaciones están fijadas y no se reestiman:

Con el índice de tres meses antes de la elección: voto = 11,0692 + 16,2205 x índice.
Con el índice del mes anterior: voto = 14,2291 + 14,8679 x índice.

El libro las redondea a 11,07 + 16,22 y 14,23 + 14,87. La serie de microdatos llega a agosto de 2026; los valores de septiembre (1,94), octubre (1,95) y noviembre de 2026 (2,04, intervalo de confianza de 1,91 a 2,16) son los publicados por la Escuela de Gobierno de la Universidad Torcuato Di Tella en sus informes mensuales.

## Segunda regla: la aprobación presidencial en América Latina

datos/elecciones_aprobacion.csv: las 148 elecciones presidenciales de primera vuelta de 18 países entre 1982 y 2024, con candidato, partido, categoría de la candidatura (P presidente, S sucesor, R respaldo, C candidato distanciado, X sin candidatura oficialista), continuidad, voto, fuente del resultado, notas de codificación y casos dudosos, aprobación de la Executive Approval Database y de Latinobarómetro, y las marcas de muestra (no competitiva, interinato, reelección habilitada por fallo judicial, muestra principal). La muestra principal tiene 123 elecciones y 118 con medición de aprobación.

datos/latinobarometro_aprobacion.csv: aprobación de la gestión del gobierno y confianza en el gobierno de Latinobarómetro por país y año.

codigo/regla_regional.py: reproduce los números que usa el libro. Requiere Python 3 con pandas y numpy. La calibración entre Latinobarómetro y la Executive Approval Database se estima con la base anual de la Executive Approval Database 3.0 (Carlin et al., 2023), que se descarga de executiveapproval.org y no se redistribuye aquí; si se pasa su ruta como argumento, el script la reestima, y si no, usa los coeficientes publicados (aprobación calibrada = 17,09 + 0,585 x porcentaje que aprueba). Escribe en tablas/ la base calibrada, la muestra de 118 elecciones, la validación fuera de la muestra y resultados.json.

Con los coeficientes publicados el script da: 118 elecciones, 106 con continuidad; para un presidente que busca su reelección, voto = 1,017 x aprobación menos 1,73 (el libro dice 1,018, con la calibración sin redondear); pendiente simple de 0,78 en los 24 casos de presidente candidato (r = 0,72); error medio fuera de la muestra de 7,2 puntos en esos casos y semiancho medio del intervalo de predicción al 95% de 27 puntos.

## Tablas

tablas/pronostico_noviembre_2026.csv: las dos tablas del anexo de datos perecederos del libro, con los valores de entrada de noviembre de 2026.

## Criterio de control

Cada regla acierta si yerra menos de 7 puntos en el voto oficialista de la primera vuelta de octubre de 2027 y, además, menos que repetir el promedio histórico del voto oficialista en las presidenciales de la serie, calculado sobre el mismo denominador. La primera regla se controla con el índice de julio y de septiembre de 2027 contra votos afirmativos; la segunda, con la aprobación del tercer trimestre de 2027 contra votos válidos. Las predicciones se agregan a esta carpeta con fecha antes de la elección.
