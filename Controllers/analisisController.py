from Models.Suplementos import Suplemento
from flask import jsonify
import traceback
import numpy as np

from config import get_spark_session, pyspark_disponible, kill_pyspark_workers

def analizar_suplementos():
    """
    Endpoint para analizar suplementos con PySpark
    """
    try:
        print("="*50)
        print("Iniciando analisis de suplementos...")
        print("="*50)
        
        kill_pyspark_workers()
        
        pyspark_available = pyspark_disponible()
        if pyspark_available:
            import pyspark
            print(f"PySpark {pyspark.__version__} disponible")
        else:
            print("PySpark no disponible, usando analisis basico")

        print("Obteniendo suplementos...")
        suplementos = Suplemento.get_all_suplementos(only_active=False)
        
        if not suplementos:
            print("No hay suplementos para analizar")
            return jsonify({
                "msg": "No hay suplementos para analizar",
                "total_suplementos": 0,
                "precio_promedio": 0,
                "precio_minimo": 0,
                "precio_maximo": 0,
                "distribucion_categorias": {},
                "distribucion_presentaciones": {},
                "stock_total": 0,
                "stock_promedio": 0,
                "suplementos_activos": 0,
                "suplementos_inactivos": 0,
                "suplementos_sin_stock": 0,
                "suplementos_bajo_stock": 0,
                "suplementos_destacados": [],
                "regresion_lineal": {
                    "coeficientes": {},
                    "r2_score": 0,
                    "mse": 0,
                    "rmse": 0,
                    "predicciones": [],
                    "datos_grafica": {
                        "reales": [],
                        "predichos": []
                    }
                },
                "kmeans": {
                    "clusters": [],
                    "silhouette_score": 0
                }
            }), 200

        print(f"Datos obtenidos: {len(suplementos)} suplementos")

        suplementos_data = []
        for sup in suplementos:
            sup_dict = Suplemento.to_dict(sup)
            suplementos_data.append({
                'id': sup_dict['id'],
                'nombre': sup_dict['nombre'],
                'precio': float(sup_dict['precio']),
                'categoria': sup_dict.get('categoria', 'quemadores'),
                'presentacion': sup_dict.get('presentacion', 'polvo'),
                'stock': sup_dict.get('stock', 0),
                'activo': bool(sup_dict.get('activo', True))
            })
        
        # VERIFICACION DE STOCKS - Corregido (fuera del for)
        print("\n=== VERIFICANDO STOCKS ===")
        for s in suplementos_data[:10]:
            print(f"Nombre: {s['nombre']}, Stock: {s['stock']}, Precio: {s['precio']}")
        print(f"Total productos: {len(suplementos_data)}")
        print("==========================\n")

        if pyspark_available and len(suplementos_data) >= 10:
            try:
                print("Iniciando analisis con PySpark y regresion lineal...")
                resultado = analizar_con_pyspark(suplementos_data)
                print("Analisis con PySpark completado")
                
                # Agregar KMeans al resultado
                print("Ejecutando KMeans clustering...")
                resultado_kmeans = ejecutar_kmeans(suplementos_data)
                resultado["kmeans"] = resultado_kmeans
                
                return jsonify(resultado), 200
            except Exception as e:
                print(f"Error en PySpark: {e}")
                traceback.print_exc()
                print("Usando analisis basico como fallback...")
                resultado = analizar_basico_con_regresion(suplementos_data)
                resultado["kmeans"] = ejecutar_kmeans(suplementos_data)
                return jsonify(resultado), 200
        else:
            print("Usando analisis basico con regresion lineal...")
            resultado = analizar_basico_con_regresion(suplementos_data)
            resultado["kmeans"] = ejecutar_kmeans(suplementos_data)
            return jsonify(resultado), 200

    except Exception as e:
        print(f"Error general en analisis: {e}")
        traceback.print_exc()
        return jsonify({
            "msg": f"Error al analizar suplementos: {str(e)}",
            "error": str(e)
        }), 500


def ejecutar_kmeans(suplementos_data):
    """
    KMEANS CLUSTERING - Agrupa productos por precio y stock
    Identifica segmentos: Premium, Intermedio, Economico
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
        import pandas as pd
        
        if len(suplementos_data) < 3:
            return {
                "clusters": [],
                "silhouette_score": 0,
                "mensaje": "Se necesitan al menos 3 productos para KMeans"
            }
        
        # Preparar datos
        df = pd.DataFrame(suplementos_data)
        X = df[['precio', 'stock']].values
        
        # Escalar datos
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # KMeans con 3 clusters
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Calcular silhouette score
        sil_score = silhouette_score(X_scaled, clusters)
        
        # Agregar clusters al dataframe
        df['cluster'] = clusters
        
        # Analizar cada cluster
        clusters_info = []
        
        for i in range(3):
            cluster_df = df[df['cluster'] == i]
            if len(cluster_df) > 0:
                precio_prom = cluster_df['precio'].mean()
                stock_prom = cluster_df['stock'].mean()
                
                # Determinar tipo de cluster
                if precio_prom > 800:
                    tipo = "Premium"
                    descripcion = "Productos de alta gama con precios elevados"
                    recomendacion = "Mantener stock controlado, enfocar en calidad"
                elif precio_prom > 400:
                    tipo = "Intermedio"
                    descripcion = "Productos de calidad media con buen precio"
                    recomendacion = "Stock moderado, promociones frecuentes"
                else:
                    tipo = "Economico"
                    descripcion = "Productos accesibles para todo publico"
                    recomendacion = "Alto volumen de stock, rotacion rapida"
                
                clusters_info.append({
                    "id": int(i),
                    "tipo": tipo,
                    "descripcion": descripcion,
                    "recomendacion": recomendacion,
                    "cantidad": int(len(cluster_df)),
                    "porcentaje": round(len(cluster_df) / len(df) * 100, 1),
                    "precio_promedio": round(float(precio_prom), 2),
                    "precio_minimo": round(float(cluster_df['precio'].min()), 2),
                    "precio_maximo": round(float(cluster_df['precio'].max()), 2),
                    "stock_promedio": round(float(stock_prom), 2),
                    "productos": cluster_df['nombre'].head(3).tolist()
                })
        
        # Ordenar clusters por precio (Premium primero)
        clusters_info.sort(key=lambda x: x['precio_promedio'], reverse=True)
        
        return {
            "clusters": clusters_info,
            "silhouette_score": round(sil_score, 4),
            "interpretacion": "Excelente" if sil_score > 0.7 else "Bueno" if sil_score > 0.5 else "Regular" if sil_score > 0.3 else "Debil",
            "total_productos": len(df)
        }
        
    except Exception as e:
        print(f"Error en KMeans: {e}")
        return {
            "clusters": [],
            "silhouette_score": 0,
            "error": str(e)
        }


def analizar_con_pyspark(suplementos_data):
    """Analisis usando PySpark con regresion lineal"""
    try:
        from pyspark.sql.functions import col, avg, min, max, count, desc, sum as spark_sum
        from pyspark.ml.feature import VectorAssembler, StringIndexer
        from pyspark.ml.regression import LinearRegression
        from pyspark.ml.evaluation import RegressionEvaluator
        from pyspark.ml import Pipeline
        
        spark = get_spark_session()
        
        if spark is None:
            print("No se pudo crear SparkSession, usando analisis basico")
            return analizar_basico_con_regresion(suplementos_data)
        
        print("Creando DataFrame de suplementos...")
        df = spark.createDataFrame(suplementos_data)
        print(f"DataFrame creado con {df.count()} filas")
        
        stats = df.select(
            count("*").alias("total_suplementos"),
            avg("precio").alias("precio_promedio"),
            min("precio").alias("precio_minimo"),
            max("precio").alias("precio_maximo"),
            spark_sum("stock").alias("stock_total"),
            avg("stock").alias("stock_promedio")
        ).collect()[0]
        
        categoria_counts = df.groupBy("categoria") \
            .count() \
            .orderBy(desc("count")) \
            .collect()
        
        distribucion_categorias = {}
        for row in categoria_counts:
            distribucion_categorias[row["categoria"]] = row["count"]
        
        presentacion_counts = df.groupBy("presentacion") \
            .count() \
            .orderBy(desc("count")) \
            .collect()
        
        distribucion_presentaciones = {}
        for row in presentacion_counts:
            distribucion_presentaciones[row["presentacion"]] = row["count"]
        
        activos = df.filter(col("activo") == True).count()
        inactivos = df.filter(col("activo") == False).count()
        sin_stock = df.filter(col("stock") == 0).count()
        
        # Stock bajo: menos del 30% del rango
        stocks_list = [s['stock'] for s in suplementos_data]
        if stocks_list:
            min_stock = min(stocks_list)
            max_stock = max(stocks_list)
            rango = max_stock - min_stock
            umbral_bajo = min_stock + (rango * 0.3)
            bajo_stock = df.filter(col("stock") <= umbral_bajo).count()
        else:
            bajo_stock = 0
        
        precio_promedio = stats["precio_promedio"]
        destacados_df = df.filter(col("precio") > precio_promedio) \
            .select("nombre", "precio", "categoria", "stock") \
            .orderBy(desc("precio")) \
            .limit(5)
        
        destacados = []
        for row in destacados_df.collect():
            destacados.append({
                "nombre": row["nombre"],
                "precio": float(row["precio"]),
                "categoria": row["categoria"],
                "stock": row["stock"]
            })
        
        print("Preparando datos para regresion lineal...")
        
        categoria_indexer = StringIndexer(inputCol="categoria", outputCol="categoria_index")
        presentacion_indexer = StringIndexer(inputCol="presentacion", outputCol="presentacion_index")
        
        assembler = VectorAssembler(
            inputCols=["categoria_index", "presentacion_index", "stock"],
            outputCol="features"
        )
        
        pipeline = Pipeline(stages=[
            categoria_indexer,
            presentacion_indexer,
            assembler
        ])
        
        transformed_df = pipeline.fit(df).transform(df)
        train_df, test_df = transformed_df.randomSplit([0.8, 0.2], seed=42)
        
        print(f"Entrenamiento: {train_df.count()} muestras")
        print(f"Prueba: {test_df.count()} muestras")
        
        lr = LinearRegression(featuresCol="features", labelCol="precio")
        lr_model = lr.fit(train_df)
        
        test_predictions = lr_model.transform(test_df)
        
        evaluator = RegressionEvaluator(labelCol="precio", predictionCol="prediction", metricName="r2")
        r2_score = evaluator.evaluate(test_predictions)
        
        coeficientes = lr_model.coefficients.tolist()
        
        predicciones = []
        predictions_df = lr_model.transform(transformed_df).select("nombre", "precio", "prediction").limit(10).collect()
        
        for row in predictions_df:
            predicciones.append({
                "nombre": row["nombre"],
                "precio_real": float(row["precio"]),
                "precio_predicho": float(row["prediction"]),
                "diferencia": float(row["prediction"] - row["precio"])
            })
        
        mse = evaluator.evaluate(test_predictions, {evaluator.metricName: "mse"})
        rmse = evaluator.evaluate(test_predictions, {evaluator.metricName: "rmse"})
        
        print(f"Modelo entrenado. R2: {r2_score:.4f}, RMSE: {rmse:.2f}")
        
        return {
            "msg": "Analisis completado con PySpark y Regresion Lineal",
            "total_suplementos": stats["total_suplementos"],
            "precio_promedio": round(float(stats["precio_promedio"]), 2),
            "precio_minimo": float(stats["precio_minimo"]),
            "precio_maximo": float(stats["precio_maximo"]),
            "distribucion_categorias": distribucion_categorias,
            "distribucion_presentaciones": distribucion_presentaciones,
            "stock_total": int(stats["stock_total"]),
            "stock_promedio": round(float(stats["stock_promedio"]), 2),
            "suplementos_activos": activos,
            "suplementos_inactivos": inactivos,
            "suplementos_sin_stock": sin_stock,
            "suplementos_bajo_stock": bajo_stock,
            "suplementos_destacados": destacados,
            "regresion_lineal": {
                "coeficientes": {
                    "categoria": round(coeficientes[0], 4) if len(coeficientes) > 0 else 0,
                    "presentacion": round(coeficientes[1], 4) if len(coeficientes) > 1 else 0,
                    "stock": round(coeficientes[2], 4) if len(coeficientes) > 2 else 0
                },
                "r2_score": round(r2_score, 4),
                "mse": round(mse, 2),
                "rmse": round(rmse, 2),
                "predicciones": predicciones,
                "interpretacion": {
                    "categoria": "Impacto de la categoria en el precio",
                    "presentacion": "Impacto de la presentacion en el precio",
                    "stock": "Impacto del stock en el precio (negativo indica que mayor stock reduce el precio)"
                }
            }
        }
        
    except Exception as e:
        print(f"Error en analizar_con_pyspark: {e}")
        traceback.print_exc()
        return analizar_basico_con_regresion(suplementos_data)


def analizar_basico_con_regresion(suplementos_data):
    """Analisis basico con regresion lineal usando scikit-learn"""
    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import r2_score, mean_squared_error
        
        print("Realizando analisis basico con regresion lineal...")
        
        total = len(suplementos_data)
        
        if total == 0:
            return {
                "msg": "Analisis basico completado (sin datos)",
                "total_suplementos": 0,
                "precio_promedio": 0,
                "precio_minimo": 0,
                "precio_maximo": 0,
                "distribucion_categorias": {},
                "distribucion_presentaciones": {},
                "stock_total": 0,
                "stock_promedio": 0,
                "suplementos_activos": 0,
                "suplementos_inactivos": 0,
                "suplementos_sin_stock": 0,
                "suplementos_bajo_stock": 0,
                "suplementos_destacados": [],
                "regresion_lineal": {
                    "coeficientes": {},
                    "r2_score": 0,
                    "mse": 0,
                    "rmse": 0,
                    "predicciones": [],
                    "datos_grafica": {
                        "reales": [],
                        "predichos": []
                    }
                }
            }
        
        precios = []
        stock_total = 0
        for s in suplementos_data:
            precios.append(s['precio'])
            stock_total += s['stock']
        
        precio_promedio = sum(precios) / len(precios)
        precio_minimo = min(precios)
        precio_maximo = max(precios)
        stock_promedio = stock_total / total
        
        categorias = {}
        for s in suplementos_data:
            cat = s['categoria']
            if cat in categorias:
                categorias[cat] += 1
            else:
                categorias[cat] = 1
        
        presentaciones = {}
        for s in suplementos_data:
            pres = s['presentacion']
            if pres in presentaciones:
                presentaciones[pres] += 1
            else:
                presentaciones[pres] = 1
        
        activos = 0
        sin_stock = 0
        for s in suplementos_data:
            if s['activo']:
                activos += 1
            if s['stock'] == 0:
                sin_stock += 1
        
        inactivos = total - activos
        
        # Calcular bajo_stock dinámicamente
        stocks_list = [s['stock'] for s in suplementos_data]
        if stocks_list:
            min_stock = min(stocks_list)
            max_stock = max(stocks_list)
            rango = max_stock - min_stock
            umbral_bajo = min_stock + (rango * 0.3)
            bajo_stock = sum(1 for s in suplementos_data if s['stock'] <= umbral_bajo)
        else:
            bajo_stock = 0
        
        destacados_temp = []
        for s in suplementos_data:
            if s['precio'] > precio_promedio:
                destacados_temp.append({
                    "nombre": s['nombre'],
                    "precio": s['precio'],
                    "categoria": s['categoria'],
                    "stock": s['stock']
                })
        
        destacados_temp.sort(key=lambda x: x['precio'], reverse=True)
        destacados = destacados_temp[:5]
        
        regresion_lineal = {
            "coeficientes": {},
            "r2_score": 0,
            "mse": 0,
            "rmse": 0,
            "predicciones": [],
            "datos_grafica": {
                "reales": [],
                "predichos": []
            }
        }
        
        if total >= 5:
            try:
                le_categoria = LabelEncoder()
                le_presentacion = LabelEncoder()
                
                all_categorias = [s['categoria'] for s in suplementos_data]
                all_presentaciones = [s['presentacion'] for s in suplementos_data]
                
                categorias_encoded = le_categoria.fit_transform(all_categorias)
                presentaciones_encoded = le_presentacion.fit_transform(all_presentaciones)
                stocks = [s['stock'] for s in suplementos_data]
                precios_target = precios
                
                X = np.column_stack([categorias_encoded, presentaciones_encoded, stocks])
                y = np.array(precios_target)
                
                from sklearn.model_selection import train_test_split
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = LinearRegression()
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                
                r2 = r2_score(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                
                coeficientes = model.coef_
                
                predicciones = []
                datos_reales = []
                datos_predichos = []
                
                for i in range(min(10, len(X_test))):
                    real = y_test[i]
                    predicho = y_pred[i]
                    # Buscar el nombre del producto correspondiente
                    nombre_producto = "Muestra"
                    if i < len(suplementos_data):
                        nombre_producto = suplementos_data[i]['nombre']
                    predicciones.append({
                        "nombre": nombre_producto,
                        "precio_real": round(float(real), 2),
                        "precio_predicho": round(float(predicho), 2),
                        "diferencia": round(float(predicho - real), 2)
                    })
                    datos_reales.append(float(real))
                    datos_predichos.append(float(predicho))
                
                regresion_lineal = {
                    "coeficientes": {
                        "categoria": round(float(coeficientes[0]), 4),
                        "presentacion": round(float(coeficientes[1]), 4),
                        "stock": round(float(coeficientes[2]), 4)
                    },
                    "r2_score": round(float(r2), 4),
                    "mse": round(float(mse), 2),
                    "rmse": round(float(rmse), 2),
                    "predicciones": predicciones,
                    "datos_grafica": {
                        "reales": datos_reales,
                        "predichos": datos_predichos
                    },
                    "interpretacion": {
                        "categoria": "Impacto de la categoria en el precio",
                        "presentacion": "Impacto de la presentacion en el precio",
                        "stock": "Impacto del stock en el precio (negativo indica que mayor stock reduce el precio)"
                    }
                }
                
                print(f"Regresion lineal completada - R2: {r2:.4f}, RMSE: {rmse:.2f}")
                
            except Exception as e:
                print(f"Error en regresion lineal: {e}")
                traceback.print_exc()
                regresion_lineal = {
                    "coeficientes": {},
                    "r2_score": 0,
                    "mse": 0,
                    "rmse": 0,
                    "predicciones": [],
                    "datos_grafica": {
                        "reales": [],
                        "predichos": []
                    },
                    "error": str(e)
                }
        else:
            regresion_lineal = {
                "coeficientes": {},
                "r2_score": 0,
                "mse": 0,
                "rmse": 0,
                "predicciones": [],
                "datos_grafica": {
                    "reales": [],
                    "predichos": []
                },
                "mensaje": f"No hay suficientes datos para regresion lineal (minimo 5, actual: {total})"
            }
        
        return {
            "msg": "Analisis basico completado",
            "total_suplementos": total,
            "precio_promedio": round(precio_promedio, 2),
            "precio_minimo": round(precio_minimo, 2),
            "precio_maximo": round(precio_maximo, 2),
            "distribucion_categorias": categorias,
            "distribucion_presentaciones": presentaciones,
            "stock_total": int(stock_total),
            "stock_promedio": round(stock_promedio, 2),
            "suplementos_activos": int(activos),
            "suplementos_inactivos": int(inactivos),
            "suplementos_sin_stock": int(sin_stock),
            "suplementos_bajo_stock": int(bajo_stock),
            "suplementos_destacados": destacados,
            "regresion_lineal": regresion_lineal
        }
        
    except Exception as e:
        print(f"Error en analisis basico: {e}")
        traceback.print_exc()
        return {
            "msg": f"Error en analisis basico: {str(e)}",
            "total_suplementos": len(suplementos_data) if suplementos_data else 0,
            "precio_promedio": 0,
            "precio_minimo": 0,
            "precio_maximo": 0,
            "distribucion_categorias": {},
            "distribucion_presentaciones": {},
            "stock_total": 0,
            "stock_promedio": 0,
            "suplementos_activos": 0,
            "suplementos_inactivos": 0,
            "suplementos_sin_stock": 0,
            "suplementos_bajo_stock": 0,
            "suplementos_destacados": [],
            "regresion_lineal": {
                "coeficientes": {},
                "r2_score": 0,
                "mse": 0,
                "rmse": 0,
                "predicciones": [],
                "datos_grafica": {
                    "reales": [],
                    "predichos": []
                }
            }
        }