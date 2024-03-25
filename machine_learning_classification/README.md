# Malware Prediction Classificator (wip)

## Descripción del Problema
El dataset consiste en 500.000 observaciones de distintas variables (83) referentes a ordenadores. La columna target es 'HasDetections', y esto significa si está infectado por virus o no. El objetivo será constuir un modelo que consiga predecir el mayor numero de casos de infeccion.

## Resumen operaciones y roadmap
El gran reto de este proyecto son el alto numero de columnas (83) y el volumen de datos. Primeramente hemos explorado un poco el contenido del df, puediendo comprobar por encima lel contenido de las columnas. Posteriormente ideamos una hipotesis inicial que pueda explicar el patron de ordenadores infectados. Para esto rescatamos de internet el significado de cada columna y extraemos una serie de variables que pueden ser interesantes a priori.

Seguido a esto hemos entrado más en materia analizando y entendiendo los datos (EDA uni y bivariable). Notamos que hay ciertas variables que tienen muchos nulos, otras que se distribuyen de forma binaria o un variables donde apenas hay variacion en los datos o existe alta fragmentacion.

Respecto a los nulos eliminamos las variables que tienen más de un 30% de nulos (una decena), por el momento el objetivo es intentar reducir la dimensionalidad.

En el preprocesamiento verificamos el tipo de datos, imputamos los nulos y exploramos correlaciones tanto con Pearson como con Phi-K (biblioteca que permite hacer correlaciones de variables numericas-categoricas). Aqui extraemos una lista de variables(feature_extr) más importantes a priori por identificarlas con mayor correlacion con la variable target.

Disminucion de la dimensionalidad. Eliminamos variables que tienen mucha correlacion entre si y solo aportan ruido al modelo y variables que o son constantes o tienen excesiva fragmentacion (el baremo a seguir es que la dominancia de clase en una variable sea inferior a 90% y superior al 10%). Podriamos hacer un escalado de los datos, pero no es necesario ya que trabajaremos con algoritmos no basados en distancias.

Una vez aqui procedemos al Encoding de las variables categoricas para posteriormente entrenar el modelo con dichos datos. 



Define claramente qué esperas lograr con este proyecto. ¿Cuál es la pregunta específica que estás intentando responder o qué problema específico estás intentando resolver?

## Conjunto de Datos
Descripción del conjunto de datos utilizado, incluyendo:
- Fuente de los datos.
- Tamaño y dimensiones del conjunto de datos.
- Descripción breve de las características principales (variables).

## Análisis Exploratorio de Datos (EDA)
Resumen de tus hallazgos durante el análisis exploratorio de datos. Menciona cualquier tendencia, patrones o anomalías interesantes observadas.

## Preprocesamiento de Datos
Describe los pasos realizados para limpiar y preparar los datos para el modelado, incluyendo:
- Limpieza de datos.
- Codificación de variables categóricas.
- Normalización o estandarización.
- División de datos en conjuntos de entrenamiento y prueba.

## Modelado
Descripción de los modelos de machine learning que has considerado y por qué. Incluye cualquier proceso de selección de características, ajuste de hiperparámetros y validación cruzada.

## Evaluación
Explica cómo evaluaste los modelos y qué métricas utilizaste. Presenta los resultados del modelo, preferiblemente comparando varios modelos si es aplicable.

## Conclusiones y Próximos Pasos
- Conclusiones principales del proyecto.
- Limitaciones del estudio.
- Sugerencias para futuras investigaciones o mejoras en el modelo.

