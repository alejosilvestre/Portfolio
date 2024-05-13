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

Tiramos un primer modelo para marcar un baseline desde el que mejorar las metricas. Posteriormente evaluamos en paralelo 4 diferentes modelos para elegir los mejores 2 (XGBoost y Logistic Regression). Para el LR hemos escalado los datos al no tratarse de un modelo basado en arboles. De estos dos ultimos extraeremos las variables más importantes para el modelo.

Pasamos a la mejora del modelo seleccionado (XGBoost) e iterativamente vamos añadiendo Cross-Validation y tuneo de hiperparametros con Randomized Search grid eligiendo el mejor de los modelos 

Evaluacion grafica del performance del modelo: curva ROC-AUC

Conclusiones.




