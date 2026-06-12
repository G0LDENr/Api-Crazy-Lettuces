from Models.Suplementos import Suplemento
from flask import jsonify
import traceback
import numpy as np
import pandas as pd
from datetime import datetime
import os
import json

from config import get_spark_session, pyspark_disponible, kill_pyspark_workers

def convertir_a_nativo(obj):
    """Convierte tipos numpy a tipos nativos de Python"""
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    if isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: convertir_a_nativo(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convertir_a_nativo(i) for i in obj]
    return obj

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
                },
                "limpieza_datos": {
                    "nulos_originales": {},
                    "nulos_despues": {},
                    "duplicados_eliminados": 0,
                    "precios_fuera_rango": 0,
                    "stocks_fuera_rango": 0,
                    "registros_iniciales": 0,
                    "registros_finales": 0,
                    "calidad_datos": "Sin datos"
                },
                "data_house": {
                    "almacenado": False,
                    "estructura": None,
                    "mensaje": "No hay datos para almacenar"
                }
            }), 200

        print(f"Datos obtenidos: {len(suplementos)} suplementos")

        # Convertir a lista de diccionarios para pandas
        suplementos_data = []
        for sup in suplementos:
            sup_dict = Suplemento.to_dict(sup)
            suplementos_data.append({
                'id': sup_dict['id'],
                'nombre': sup_dict['nombre'],
                'precio': float(sup_dict['precio']) if sup_dict.get('precio') else None,
                'categoria': sup_dict.get('categoria', 'quemadores'),
                'presentacion': sup_dict.get('presentacion', 'polvo'),
                'stock': sup_dict.get('stock', 0) if sup_dict.get('stock') is not None else None,
                'activo': bool(sup_dict.get('activo', True)) if sup_dict.get('activo') is not None else None,
                'fecha_creacion': sup_dict.get('fecha_creacion'),
                'fecha_actualizacion': sup_dict.get('fecha_actualizacion')
            })
        
        # ========== PROCESO DE LIMPIEZA DE DATOS CON PANDAS ==========
        print("\n" + "="*60)
        print("FASE 2: PRE-PROCESAMIENTO DE DATOS (KDD)")
        print("="*60)
        
        resultado_limpieza = limpiar_datos_con_pandas(suplementos_data)
        datos_limpios = resultado_limpieza['datos_limpios']
        
        # ========== DATA HOUSE - SNOWFLAKE SCHEMA ==========
        print("\n" + "="*60)
        print("DATA HOUSE - MODELO COPO DE NIEVE (SNOWFLAKE SCHEMA)")
        print("="*60)
        
        data_house_result = almacenar_data_house_snowflake(datos_limpios, resultado_limpieza['resumen'])
        
        print("\n=== VERIFICANDO STOCKS (DATOS LIMPIOS) ===")
        for s in datos_limpios[:10]:
            print(f"Nombre: {s['nombre']}, Stock: {s['stock']}, Precio: {s['precio']}")
        print(f"Total productos limpios: {len(datos_limpios)}")
        print("==========================================\n")

        if pyspark_available and len(datos_limpios) >= 10:
            try:
                print("Iniciando analisis con PySpark y regresion lineal...")
                resultado = analizar_con_pyspark(datos_limpios)
                print("Analisis con PySpark completado")
                
                print("Ejecutando KMeans clustering...")
                resultado_kmeans = ejecutar_kmeans(datos_limpios)
                resultado["kmeans"] = resultado_kmeans
                
                resultado["limpieza_datos"] = convertir_a_nativo(resultado_limpieza['resumen'])
                resultado["data_house"] = convertir_a_nativo(data_house_result)
                
                return jsonify(convertir_a_nativo(resultado)), 200
            except Exception as e:
                print(f"Error en PySpark: {e}")
                traceback.print_exc()
                print("Usando analisis basico como fallback...")
                resultado = analizar_basico_con_regresion(datos_limpios)
                resultado["kmeans"] = ejecutar_kmeans(datos_limpios)
                resultado["limpieza_datos"] = convertir_a_nativo(resultado_limpieza['resumen'])
                resultado["data_house"] = convertir_a_nativo(data_house_result)
                return jsonify(convertir_a_nativo(resultado)), 200
        else:
            print("Usando analisis basico con regresion lineal...")
            resultado = analizar_basico_con_regresion(datos_limpios)
            resultado["kmeans"] = ejecutar_kmeans(datos_limpios)
            resultado["limpieza_datos"] = convertir_a_nativo(resultado_limpieza['resumen'])
            resultado["data_house"] = convertir_a_nativo(data_house_result)
            return jsonify(convertir_a_nativo(resultado)), 200

    except Exception as e:
        print(f"Error general en analisis: {e}")
        traceback.print_exc()
        return jsonify({
            "msg": f"Error al analizar suplementos: {str(e)}",
            "error": str(e)
        }), 500


def limpiar_datos_con_pandas(suplementos_data):
    """
    3.1 Limpieza de datos - DataFrame con Pandas
    Según la guía de entrega: corrección de nulos, duplicados y formatos
    """
    try:
        # Cargar DataFrame
        df = pd.DataFrame(suplementos_data)
        registros_iniciales = len(df)
        
        print(f"\n DataFrame cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
        print("\n--- Inspección inicial del DataFrame ---")
        print(df.info())
        print(f"\nEstadisticas descriptivas:\n{df.describe()}")
        print(f"\nPrimeras 5 filas:\n{df.head()}")
        print(f"\nShape: {df.shape}")
        
        # ========== 3.1.1 Corrección de valores nulos ==========
        print("\n" + "-"*40)
        print("3.1.1 Corrección de valores nulos")
        print("-"*40)
        
        # Verificar porcentaje de nulos por columna
        nulos_originales = (df.isnull().sum() / len(df) * 100).to_dict()
        print(f"Porcentaje de nulos por columna:\n{pd.Series(nulos_originales)}")
        
        # PRECIO: rellenar nulos con la mediana por categoria
        print("\nRellenando nulos en PRECIO con mediana por categoría...")
        df["precio"] = df.groupby("categoria")["precio"].transform(
            lambda x: x.fillna(x.median())
        )
        if df["precio"].isnull().any():
            df["precio"] = df["precio"].fillna(df["precio"].median())
        print(f"  Nulos en precio: {df['precio'].isnull().sum()}")
        
        # STOCK: nulos -> 0
        print("\nRellenando nulos en STOCK con 0...")
        df["stock"] = df["stock"].fillna(0).astype(int)
        print(f"  Nulos en stock: {df['stock'].isnull().sum()}")
        
        # ACTIVO: nulos -> True
        print("\nRellenando nulos en ACTIVO con True...")
        df["activo"] = df["activo"].fillna(True).astype(bool)
        print(f"  Nulos en activo: {df['activo'].isnull().sum()}")
        
        # CATEGORIA: nulos -> 'otros'
        print("\nRellenando nulos en CATEGORIA con 'otros'...")
        df["categoria"] = df["categoria"].fillna("otros")
        print(f"  Nulos en categoria: {df['categoria'].isnull().sum()}")
        
        # PRESENTACION: nulos -> 'polvo'
        print("\nRellenando nulos en PRESENTACION con 'polvo'...")
        df["presentacion"] = df["presentacion"].fillna("polvo")
        print(f"  Nulos en presentacion: {df['presentacion'].isnull().sum()}")
        
        nulos_despues = df.isnull().sum().sum()
        if nulos_despues == 0:
            print("\n SIN VALORES NULOS - Limpieza completada")
        
        # ========== 3.1.2 Corrección de duplicados ==========
        print("\n" + "-"*40)
        print("3.1.2 Corrección de duplicados")
        print("-"*40)
        
        duplicados = df.duplicated(subset=["nombre", "categoria", "presentacion"], keep=False)
        duplicados_count = int(duplicados.sum())
        print(f"Registros duplicados detectados: {duplicados_count}")
        
        df = df.drop_duplicates(subset=["nombre", "categoria", "presentacion"], keep="first")
        print(f"Registros tras deduplicación: {len(df)}")
        
        # ========== 3.1.3 Corrección de formatos incorrectos ==========
        print("\n" + "-"*40)
        print("3.1.3 Corrección de formatos incorrectos")
        print("-"*40)
        
        # Estandarizar texto
        print("\nEstandarizando texto...")
        df["categoria"] = df["categoria"].str.strip().str.lower()
        df["presentacion"] = df["presentacion"].str.strip().str.lower()
        df["nombre"] = df["nombre"].str.strip().str.title()
        print("  Texto estandarizado")
        
        # Validar rangos de precio (ajustado a tus datos reales: 15-500 MXN)
        print("\nValidando rangos de precio (15 - 500 MXN)...")
        precio_min_real = df["precio"].min()
        precio_max_real = df["precio"].max()
        print(f"Rango real de precios: {precio_min_real:.2f} - {precio_max_real:.2f} MXN")
        
        # Usar rangos basados en los datos reales (percentiles)
        precio_inferior = max(df["precio"].quantile(0.05), 10)
        precio_superior = min(df["precio"].quantile(0.95), 500)
        
        precios_invalidos = df[(df["precio"] < precio_inferior) | (df["precio"] > precio_superior)]
        precios_fuera_rango = int(len(precios_invalidos))
        print(f"Precios fuera de rango ({precio_inferior:.0f}-{precio_superior:.0f}): {precios_fuera_rango}")
        
        if precios_fuera_rango > 0:
            # En lugar de eliminar, limitamos los precios
            df["precio"] = df["precio"].clip(lower=precio_inferior, upper=precio_superior)
            print(f"  Precios ajustados al rango permitido")
        
        # Validar rangos de stock
        print("\nValidando rangos de stock...")
        stock_min = df["stock"].min()
        stock_max = df["stock"].max()
        print(f"Rango de stock: {stock_min} - {stock_max}")
        
        # No eliminamos stocks fuera de rango, solo los limitamos si es necesario
        df["stock"] = df["stock"].clip(lower=0, upper=999)
        stocks_fuera_rango = int(len(df[(df["stock"] < 0) | (df["stock"] > 999)]))
        
        registros_finales = int(len(df))
        
        # Calcular calidad de datos
        retention_rate = registros_finales / registros_iniciales if registros_iniciales > 0 else 0
        if retention_rate > 0.9:
            calidad = "Excelente"
        elif retention_rate > 0.7:
            calidad = "Buena"
        elif retention_rate > 0.5:
            calidad = "Regular"
        else:
            calidad = "Mala"
        
        print(f"\n DataFrame limpio: {registros_finales} registros, {df.shape[1]} columnas")
        print(f" Calidad de datos: {calidad}")
        
        # Guardar DataFrame limpio
        try:
            csv_filename = f"suplementos_limpio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_filename, index=False)
            print(f" DataFrame guardado en: {csv_filename}")
        except Exception as e:
            print(f" No se pudo guardar CSV: {e}")
        
        # Convertir a lista de diccionarios con tipos nativos
        datos_limpios = []
        for _, row in df.iterrows():
            datos_limpios.append({
                'id': int(row['id']),
                'nombre': str(row['nombre']),
                'precio': float(row['precio']),
                'categoria': str(row['categoria']),
                'presentacion': str(row['presentacion']),
                'stock': int(row['stock']),
                'activo': bool(row['activo']),
                'fecha_creacion': str(row['fecha_creacion']) if pd.notna(row.get('fecha_creacion')) else None,
                'fecha_actualizacion': str(row['fecha_actualizacion']) if pd.notna(row.get('fecha_actualizacion')) else None
            })
        
        return {
            'datos_limpios': datos_limpios,
            'resumen': {
                'nulos_originales': {k: float(v) for k, v in nulos_originales.items()},
                'nulos_despues': {k: int(v) for k, v in df.isnull().sum().to_dict().items()},
                'duplicados_eliminados': duplicados_count,
                'precios_fuera_rango': precios_fuera_rango,
                'stocks_fuera_rango': stocks_fuera_rango,
                'registros_iniciales': registros_iniciales,
                'registros_finales': registros_finales,
                'calidad_datos': calidad
            }
        }
        
    except Exception as e:
        print(f"Error en limpieza de datos: {e}")
        traceback.print_exc()
        return {
            'datos_limpios': suplementos_data,
            'resumen': {
                'nulos_originales': {},
                'nulos_despues': {},
                'duplicados_eliminados': 0,
                'precios_fuera_rango': 0,
                'stocks_fuera_rango': 0,
                'registros_iniciales': len(suplementos_data),
                'registros_finales': len(suplementos_data),
                'calidad_datos': "Sin procesar"
            }
        }


def almacenar_data_house_snowflake(datos_limpios, resumen_limpieza):
    """
    2.2 Modelo Copo de Nieve (Snowflake Schema) - Data House
    """
    try:
        data_house_dir = "data_house"
        if not os.path.exists(data_house_dir):
            os.makedirs(data_house_dir)
            print(f" Creado directorio: {data_house_dir}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Obtener categorías y presentaciones únicas
        categorias_unicas = list(set([item['categoria'] for item in datos_limpios]))
        presentaciones_unicas = list(set([item['presentacion'] for item in datos_limpios]))
        
        # Tabla de hechos
        fact_table = {
            'nombre': 'VENTAS_HECHOS',
            'tipo': 'FACT_TABLE',
            'descripcion': 'Tabla central de hechos',
            'registros': len(datos_limpios)
        }
        
        # Dimensiones
        dimensiones = [
            {
                'nombre': 'DIM_PRODUCTO',
                'tipo': 'DIMENSION',
                'descripcion': 'Dimension de productos',
                'total_registros': len(datos_limpios)
            },
            {
                'nombre': 'DIM_CATEGORIA',
                'tipo': 'SUB_DIMENSION',
                'descripcion': 'Subdimension de categorias',
                'dimension_padre': 'DIM_PRODUCTO',
                'total_registros': len(categorias_unicas)
            },
            {
                'nombre': 'DIM_PRESENTACION',
                'tipo': 'SUB_DIMENSION',
                'descripcion': 'Subdimension de presentaciones',
                'dimension_padre': 'DIM_PRODUCTO',
                'total_registros': len(presentaciones_unicas)
            }
        ]
        
        snowflake_schema = {
            'nombre': 'Balancea_Data_House',
            'version': '1.0',
            'fecha_generacion': datetime.now().isoformat(),
            'descripcion': 'Data House con modelo Copo de Nieve',
            'estructura': {
                'tabla_hechos': fact_table,
                'dimensiones': dimensiones
            },
            'estadisticas': {
                'total_tablas': 1 + len(dimensiones),
                'total_dimensiones': len([d for d in dimensiones if d['tipo'] == 'DIMENSION']),
                'total_subdimensiones': len([d for d in dimensiones if d['tipo'] == 'SUB_DIMENSION']),
                'registros_totales': len(datos_limpios)
            },
            'limpieza_referencia': resumen_limpieza
        }
        
        # Guardar esquema
        archivo_esquema = f"{data_house_dir}/snowflake_schema_{timestamp}.json"
        with open(archivo_esquema, 'w', encoding='utf-8') as f:
            json.dump(snowflake_schema, f, ensure_ascii=False, indent=2, default=str)
        print(f" Esquema Snowflake guardado: {archivo_esquema}")
        
        # Historial
        historial_file = f"{data_house_dir}/historial_data_house.json"
        historial = []
        if os.path.exists(historial_file):
            with open(historial_file, 'r', encoding='utf-8') as f:
                historial = json.load(f)
        
        historial.append({
            'timestamp': timestamp,
            'fecha': datetime.now().isoformat(),
            'archivo': archivo_esquema,
            'total_registros': len(datos_limpios),
            'calidad_datos': resumen_limpieza.get('calidad_datos', 'No definida')
        })
        
        if len(historial) > 100:
            historial = historial[-100:]
        
        with open(historial_file, 'w', encoding='utf-8') as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        
        print(f" Historial actualizado: {len(historial)} analisis")
        
        return {
            'almacenado': True,
            'mensaje': 'Data House actualizado con modelo Copo de Nieve',
            'estructura': {
                'tabla_hechos': fact_table['nombre'],
                'dimensiones': [d['nombre'] for d in dimensiones],
                'total_tablas': snowflake_schema['estadisticas']['total_tablas'],
                'total_registros': snowflake_schema['estadisticas']['registros_totales']
            },
            'archivo': archivo_esquema,
            'timestamp': timestamp,
            'consultas_ejemplo': [
                "SELECT dp.nombre, SUM(vh.total) as ventas FROM VENTAS_HECHOS vh JOIN DIM_PRODUCTO dp ON vh.producto_id = dp.producto_id GROUP BY dp.nombre",
                "SELECT dc.nombre_categoria, COUNT(*) as total FROM VENTAS_HECHOS vh JOIN DIM_CATEGORIA dc ON vh.categoria_id = dc.categoria_id GROUP BY dc.nombre_categoria"
            ]
        }
        
    except Exception as e:
        print(f"Error en Data House: {e}")
        traceback.print_exc()
        return {
            'almacenado': False,
            'mensaje': f'Error: {str(e)}',
            'estructura': None
        }


def ejecutar_kmeans(suplementos_data):
    """KMEANS CLUSTERING"""
    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
        import pandas as pd
        
        if len(suplementos_data) < 3:
            return {"clusters": [], "silhouette_score": 0, "mensaje": "Se necesitan al menos 3 productos"}
        
        df = pd.DataFrame(suplementos_data)
        X = df[['precio', 'stock']].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        sil_score = silhouette_score(X_scaled, clusters)
        
        df['cluster'] = clusters
        clusters_info = []
        
        for i in range(3):
            cluster_df = df[df['cluster'] == i]
            if len(cluster_df) > 0:
                precio_prom = cluster_df['precio'].mean()
                
                if precio_prom > 400:
                    tipo = "Premium"
                    descripcion = "Productos de alta gama"
                    recomendacion = "Stock controlado, enfoque en calidad"
                elif precio_prom > 250:
                    tipo = "Intermedio"
                    descripcion = "Productos calidad media"
                    recomendacion = "Stock moderado"
                else:
                    tipo = "Economico"
                    descripcion = "Productos accesibles"
                    recomendacion = "Alto volumen de stock"
                
                clusters_info.append({
                    "id": int(i),
                    "tipo": tipo,
                    "descripcion": descripcion,
                    "recomendacion": recomendacion,
                    "cantidad": int(len(cluster_df)),
                    "porcentaje": round(float(len(cluster_df) / len(df) * 100), 1),
                    "precio_promedio": round(float(precio_prom), 2),
                    "precio_minimo": round(float(cluster_df['precio'].min()), 2),
                    "precio_maximo": round(float(cluster_df['precio'].max()), 2),
                    "stock_promedio": round(float(cluster_df['stock'].mean()), 2),
                    "productos": cluster_df['nombre'].head(3).tolist()
                })
        
        clusters_info.sort(key=lambda x: x['precio_promedio'], reverse=True)
        
        return {
            "clusters": clusters_info,
            "silhouette_score": round(float(sil_score), 4),
            "interpretacion": "Excelente" if sil_score > 0.7 else "Bueno" if sil_score > 0.5 else "Regular",
            "total_productos": int(len(df))
        }
        
    except Exception as e:
        print(f"Error en KMeans: {e}")
        return {"clusters": [], "silhouette_score": 0, "error": str(e)}


def analizar_basico_con_regresion(suplementos_data):
    """Analisis basico con regresion lineal"""
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import r2_score, mean_squared_error
        from sklearn.model_selection import train_test_split
        import numpy as np
        
        total = len(suplementos_data)
        
        if total == 0:
            return {
                "msg": "Analisis completado (sin datos)",
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
                    "datos_grafica": {"reales": [], "predichos": []}
                }
            }
        
        precios = [float(s['precio']) for s in suplementos_data]
        stock_total = sum(int(s['stock']) for s in suplementos_data)
        
        precio_promedio = sum(precios) / len(precios)
        precio_minimo = min(precios)
        precio_maximo = max(precios)
        stock_promedio = stock_total / total
        
        categorias = {}
        presentaciones = {}
        for s in suplementos_data:
            cat = s['categoria']
            pres = s['presentacion']
            categorias[cat] = categorias.get(cat, 0) + 1
            presentaciones[pres] = presentaciones.get(pres, 0) + 1
        
        activos = sum(1 for s in suplementos_data if s['activo'])
        sin_stock = sum(1 for s in suplementos_data if s['stock'] == 0)
        inactivos = total - activos
        
        stocks_list = [s['stock'] for s in suplementos_data]
        if stocks_list:
            min_stock = min(stocks_list)
            max_stock = max(stocks_list)
            rango = max_stock - min_stock
            umbral_bajo = min_stock + (rango * 0.3)
            bajo_stock = sum(1 for s in suplementos_data if s['stock'] <= umbral_bajo)
        else:
            bajo_stock = 0
        
        destacados = []
        for s in suplementos_data:
            if s['precio'] > precio_promedio:
                destacados.append({
                    "nombre": s['nombre'],
                    "precio": float(s['precio']),
                    "categoria": s['categoria'],
                    "stock": int(s['stock'])
                })
        destacados.sort(key=lambda x: x['precio'], reverse=True)
        destacados = destacados[:5]
        
        regresion_lineal = {
            "coeficientes": {},
            "r2_score": 0,
            "mse": 0,
            "rmse": 0,
            "predicciones": [],
            "datos_grafica": {"reales": [], "predichos": []}
        }
        
        if total >= 5:
            try:
                le_categoria = LabelEncoder()
                le_presentacion = LabelEncoder()
                
                all_categorias = [s['categoria'] for s in suplementos_data]
                all_presentaciones = [s['presentacion'] for s in suplementos_data]
                
                categorias_encoded = le_categoria.fit_transform(all_categorias)
                presentaciones_encoded = le_presentacion.fit_transform(all_presentaciones)
                stocks = [float(s['stock']) for s in suplementos_data]
                
                X = np.column_stack([categorias_encoded, presentaciones_encoded, stocks])
                y = np.array(precios)
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = LinearRegression()
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                r2 = r2_score(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                
                coeficientes = model.coef_
                
                predicciones = []
                for i in range(min(10, len(X_test))):
                    predicciones.append({
                        "nombre": suplementos_data[i]['nombre'] if i < len(suplementos_data) else f"Muestra {i+1}",
                        "precio_real": round(float(y_test[i]), 2),
                        "precio_predicho": round(float(y_pred[i]), 2),
                        "diferencia": round(float(y_pred[i] - y_test[i]), 2)
                    })
                
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
                        "reales": [float(x) for x in y_test[:10]],
                        "predichos": [float(x) for x in y_pred[:10]]
                    }
                }
                
                print(f"Regresion lineal completada - R2: {r2:.4f}, RMSE: {rmse:.2f}")
                
            except Exception as e:
                print(f"Error en regresion lineal: {e}")
                traceback.print_exc()
        
        return {
            "msg": "Analisis completado",
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
        print(f"Error en analisis: {e}")
        traceback.print_exc()
        return {
            "msg": f"Error: {str(e)}",
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
                "datos_grafica": {"reales": [], "predichos": []}
            }
        }


def analizar_con_pyspark(suplementos_data):
    """Analisis usando PySpark (placeholder - igual que analizar_basico_con_regresion por ahora)"""
    return analizar_basico_con_regresion(suplementos_data)