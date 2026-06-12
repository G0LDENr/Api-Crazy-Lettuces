# Controllers/diagramaController.py
from flask import jsonify, send_file
from config import DB_TYPE, db_sql
from Models.User import UserSQL
from Models.Direccion import DireccionSQL
from Models.Targetas import TarjetaSQL
from Models.Suplementos import SuplementoSQL
from Models.Ordenes import OrdenSQL
from Models.Notificaciones import NotificacionSQL
from Models.Dietas import DietaSQL, DietaUsuarioSQL, SeguimientoDietaSQL
from Models.Backup import BackupSQL
from datetime import datetime
import os
import json
import tempfile
import traceback

# ============================================
# FUNCIÓN PARA GENERAR DIAGRAMA DE MYSQL
# ============================================

def generar_diagrama_mysql():
    """Generar diagrama entidad-relación de MySQL usando SQLAlchemy"""
    try:
        inspector = db_sql.inspect(db_sql.engine)
        tablas = inspector.get_table_names()
        
        diagrama = {
            'tipo_bd': 'MySQL',
            'fecha_generacion': datetime.now().isoformat(),
            'total_tablas': len(tablas),
            'tablas': [],
            'relaciones': []
        }
        
        modelos = {
            'users': UserSQL,
            'direcciones': DireccionSQL,
            'tarjetas': TarjetaSQL,
            'suplementos': SuplementoSQL,
            'ordenes': OrdenSQL,
            'notificaciones': NotificacionSQL,
            'dietas': DietaSQL,
            'dietas_usuario': DietaUsuarioSQL,
            'seguimiento_dieta': SeguimientoDietaSQL,
            'backups': BackupSQL
        }
        
        for tabla in tablas:
            columnas = inspector.get_columns(tabla)
            pk = inspector.get_pk_constraint(tabla)
            fks = inspector.get_foreign_keys(tabla)
            
            info_tabla = {
                'nombre': tabla,
                'columnas': [],
                'primary_key': pk.get('constrained_columns', []),
                'foreign_keys': []
            }
            
            for col in columnas:
                info_tabla['columnas'].append({
                    'nombre': col['name'],
                    'tipo': str(col['type']),
                    'nullable': col['nullable'],
                    'default': str(col['default']) if col['default'] else None
                })
            
            for fk in fks:
                for i, col in enumerate(fk['constrained_columns']):
                    relacion = {
                        'tabla_origen': tabla,
                        'columna_origen': col,
                        'tabla_destino': fk['referred_table'],
                        'columna_destino': fk['referred_columns'][i] if i < len(fk['referred_columns']) else 'id',
                        'nombre': fk.get('name', '')
                    }
                    info_tabla['foreign_keys'].append(relacion)
                    diagrama['relaciones'].append(relacion)
            
            try:
                modelo = modelos.get(tabla)
                if modelo:
                    info_tabla['total_registros'] = db_sql.session.query(modelo).count()
                else:
                    result = db_sql.session.execute(f"SELECT COUNT(*) FROM {tabla}")
                    info_tabla['total_registros'] = result.scalar() or 0
            except:
                info_tabla['total_registros'] = 0
            
            diagrama['tablas'].append(info_tabla)
        
        return diagrama
        
    except Exception as e:
        print(f"Error generando diagrama MySQL: {e}")
        return {'error': str(e), 'tipo_bd': 'MySQL'}


# ============================================
# FUNCIÓN PARA GENERAR DIAGRAMA DE MONGODB
# ============================================

def generar_diagrama_mongodb():
    """Generar diagrama de MongoDB"""
    try:
        from config import db_mongo
        
        colecciones = db_mongo.db.list_collection_names()
        
        diagrama = {
            'tipo_bd': 'MongoDB',
            'fecha_generacion': datetime.now().isoformat(),
            'total_colecciones': len(colecciones),
            'colecciones': [],
            'relaciones': []
        }
        
        relaciones_vistas = set()
        
        for coleccion in colecciones:
            try:
                stats = db_mongo.db.command('collstats', coleccion)
                tamanio_mb = round(stats.get('size', 0) / (1024 * 1024), 2)
            except:
                tamanio_mb = 0
            
            documento = db_mongo.db[coleccion].find_one()
            total_docs = db_mongo.db[coleccion].count_documents({})
            
            campos = []
            campos_referencia = []
            
            if documento:
                for campo, valor in documento.items():
                    tipo = type(valor).__name__
                    
                    es_referencia = campo.endswith('_id') or campo in [
                        'user_id', 'usuario_id', 'dieta_id', 'orden_id', 
                        'tarjeta_id', 'direccion_id', 'backup_id'
                    ]
                    
                    info_campo = {
                        'nombre': campo,
                        'tipo': tipo,
                        'ejemplo': str(valor)[:50] + '...' if len(str(valor)) > 50 else str(valor),
                        'es_referencia': es_referencia
                    }
                    
                    campos.append(info_campo)
                    
                    if es_referencia:
                        coleccion_destino = None
                        if 'user' in campo.lower() or 'usuario' in campo.lower():
                            coleccion_destino = 'users' if 'users' in colecciones else 'usuarios'
                        elif 'dieta' in campo.lower():
                            coleccion_destino = 'dietas'
                        elif 'orden' in campo.lower():
                            coleccion_destino = 'ordenes'
                        elif 'tarjeta' in campo.lower():
                            coleccion_destino = 'tarjetas'
                        elif 'direccion' in campo.lower():
                            coleccion_destino = 'direcciones'
                        elif 'backup' in campo.lower():
                            coleccion_destino = 'backups'
                        
                        if coleccion_destino and coleccion_destino in colecciones:
                            clave = f"{coleccion}.{campo}->{coleccion_destino}"
                            if clave not in relaciones_vistas:
                                relaciones_vistas.add(clave)
                                diagrama['relaciones'].append({
                                    'coleccion_origen': coleccion,
                                    'campo_origen': campo,
                                    'coleccion_destino': coleccion_destino,
                                    'campo_destino': '_id',
                                    'tipo_relacion': 'implícita'
                                })
                                campos_referencia.append({
                                    'nombre': campo,
                                    'referencia': coleccion_destino
                                })
            
            diagrama['colecciones'].append({
                'nombre': coleccion,
                'total_documentos': total_docs,
                'tamanio_aprox_mb': tamanio_mb,
                'campos': campos,
                'campos_referencia': campos_referencia
            })
        
        return diagrama
        
    except Exception as e:
        print(f"Error generando diagrama MongoDB: {e}")
        return {'error': str(e), 'tipo_bd': 'MongoDB'}


# ============================================
# FUNCIÓN PRINCIPAL - GENERAR DIAGRAMA
# ============================================

def generar_diagrama():
    """Generar diagrama según el tipo de base de datos actual"""
    try:
        print(f"🎨 Generando diagrama para DB_TYPE: {DB_TYPE}")
        
        if DB_TYPE == 'mysql':
            diagrama = generar_diagrama_mysql()
        else:
            diagrama = generar_diagrama_mongodb()
        
        if 'error' in diagrama:
            return jsonify({
                'success': False,
                'message': diagrama['error']
            }), 500
        
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"diagrama_{DB_TYPE}_{timestamp}.json"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(diagrama, f, indent=2, default=str)
            
        except Exception as e:
            print(f"⚠️ No se pudo guardar copia temporal: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Diagrama de {DB_TYPE.upper()} generado',
            'data': diagrama
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================
# EXPORTAR DIAGRAMA COMO JSON
# ============================================

def exportar_diagrama_json():
    """Exportar diagrama como archivo JSON"""
    try:
        if DB_TYPE == 'mysql':
            diagrama = generar_diagrama_mysql()
        else:
            diagrama = generar_diagrama_mongodb()
        
        if 'error' in diagrama:
            return jsonify({
                'success': False,
                'message': diagrama['error']
            }), 500
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(diagrama, f, indent=2, default=str)
            temp_path = f.name
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"diagrama_{DB_TYPE}_{timestamp}.json"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================
# EXPORTAR DIAGRAMA COMO SQL (solo MySQL)
# ============================================

def exportar_diagrama_sql():
    """Exportar diagrama como script SQL"""
    try:
        if DB_TYPE != 'mysql':
            return jsonify({
                'success': False,
                'message': 'SQL solo disponible para MySQL'
            }), 400
        
        diagrama = generar_diagrama_mysql()
        
        if 'error' in diagrama:
            return jsonify({
                'success': False,
                'message': diagrama['error']
            }), 500
        
        sql_lines = [
            "-- ===========================================",
            f"-- DIAGRAMA ENTIDAD-RELACIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-- ===========================================",
            ""
        ]
        
        for tabla in diagrama['tablas']:
            sql_lines.append(f"-- TABLA: {tabla['nombre']} ({tabla['total_registros']} registros)")
            sql_lines.append(f"CREATE TABLE IF NOT EXISTS `{tabla['nombre']}` (")
            
            columnas_sql = []
            for col in tabla['columnas']:
                col_sql = f"  `{col['nombre']}` {col['tipo']}"
                if not col['nullable']:
                    col_sql += " NOT NULL"
                if col['default'] and col['default'] != 'None':
                    col_sql += f" DEFAULT {col['default']}"
                columnas_sql.append(col_sql)
            
            if tabla['primary_key']:
                pk_cols = ', '.join([f"`{pk}`" for pk in tabla['primary_key']])
                columnas_sql.append(f"  PRIMARY KEY ({pk_cols})")
            
            sql_lines.append(',\n'.join(columnas_sql))
            sql_lines.append(");")
            
            if tabla['foreign_keys']:
                sql_lines.append("")
                sql_lines.append(f"-- Relaciones de {tabla['nombre']}:")
                for fk in tabla['foreign_keys']:
                    sql_lines.append(f"--   {fk['columna_origen']} -> {fk['tabla_destino']}.{fk['columna_destino']}")
            
            sql_lines.append("")
            sql_lines.append("-- " + "-"*50)
            sql_lines.append("")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
            temp_path = f.name
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"diagrama_{DB_TYPE}_{timestamp}.sql"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================
# ESTADÍSTICAS DE LA BASE DE DATOS
# ============================================

def get_database_stats():
    """Obtener estadísticas generales de la BD"""
    try:
        stats = {
            'tipo_bd': DB_TYPE,
            'fecha': datetime.now().isoformat(),
            'tablas': [],
            'total_registros': 0,
            'tamanio_aprox_mb': 0
        }
        
        if DB_TYPE == 'mysql':
            inspector = db_sql.inspect(db_sql.engine)
            tablas = inspector.get_table_names()
            
            for tabla in tablas:
                try:
                    result = db_sql.session.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = result.scalar() or 0
                    
                    size_result = db_sql.session.execute(
                        f"SELECT ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) "
                        f"FROM information_schema.TABLES "
                        f"WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{tabla}'"
                    )
                    size = size_result.scalar() or 0
                    
                    stats['tablas'].append({
                        'nombre': tabla,
                        'registros': count,
                        'tamanio_mb': float(size)
                    })
                    
                    stats['total_registros'] += count
                    stats['tamanio_aprox_mb'] += float(size)
                    
                except Exception as e:
                    stats['tablas'].append({
                        'nombre': tabla,
                        'registros': 0,
                        'tamanio_mb': 0,
                        'error': str(e)
                    })
            
        else:
            from config import db_mongo
            colecciones = db_mongo.db.list_collection_names()
            
            for coleccion in colecciones:
                try:
                    count = db_mongo.db[coleccion].count_documents({})
                    coll_stats = db_mongo.db.command('collstats', coleccion)
                    size_mb = round(coll_stats.get('size', 0) / (1024 * 1024), 2)
                    
                    stats['tablas'].append({
                        'nombre': coleccion,
                        'registros': count,
                        'tamanio_mb': size_mb
                    })
                    
                    stats['total_registros'] += count
                    stats['tamanio_aprox_mb'] += size_mb
                    
                except Exception as e:
                    stats['tablas'].append({
                        'nombre': coleccion,
                        'registros': 0,
                        'tamanio_mb': 0,
                        'error': str(e)
                    })
        
        stats['tamanio_aprox_mb'] = round(stats['tamanio_aprox_mb'], 2)
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================
# COMPARAR MYSQL VS MONGODB
# ============================================

def comparar_estructuras():
    """Comparar estructuras de MySQL y MongoDB"""
    try:
        from config import db_mongo
        
        estructura_mysql = None
        estructura_mongo = None
        errores = []
        
        try:
            inspector = db_sql.inspect(db_sql.engine)
            tablas = inspector.get_table_names()
            if tablas:
                estructura_mysql = generar_diagrama_mysql()
        except Exception as e:
            errores.append(f"MySQL: {str(e)}")
        
        try:
            colecciones = db_mongo.db.list_collection_names()
            if colecciones:
                estructura_mongo = generar_diagrama_mongodb()
        except Exception as e:
            errores.append(f"MongoDB: {str(e)}")
        
        comparacion = {
            'fecha': datetime.now().isoformat(),
            'mysql_disponible': estructura_mysql is not None and 'error' not in estructura_mysql,
            'mongodb_disponible': estructura_mongo is not None and 'error' not in estructura_mongo,
            'errores': errores
        }
        
        if estructura_mysql and 'error' not in estructura_mysql:
            comparacion['mysql'] = {
                'total_tablas': estructura_mysql.get('total_tablas', 0),
                'tablas': [t['nombre'] for t in estructura_mysql.get('tablas', [])],
                'total_relaciones': len(estructura_mysql.get('relaciones', []))
            }
        
        if estructura_mongo and 'error' not in estructura_mongo:
            comparacion['mongodb'] = {
                'total_colecciones': estructura_mongo.get('total_colecciones', 0),
                'colecciones': [c['nombre'] for c in estructura_mongo.get('colecciones', [])],
                'total_relaciones': len(estructura_mongo.get('relaciones', []))
            }
        
        return jsonify({
            'success': True,
            'comparacion': comparacion
        }), 200
        
    except Exception as e:
        print(f"❌ Error en comparar_estructuras: {e}")
        return jsonify({
            'success': False,
            'message': f'Error al comparar estructuras: {str(e)}'
        }), 500


# ============================================
# FUNCIONES PARA DIAGRAMA DE COPO DE NIEVE (CORREGIDAS)
# ============================================

def generar_diagrama_copo_nieve():
    """Generar diagrama de copo de nieve (Snowflake Schema)"""
    try:
        print(f"🎨 Generando diagrama de COPO DE NIEVE para DB_TYPE: {DB_TYPE}")
        
        if DB_TYPE == 'mysql':
            diagrama_base = generar_diagrama_mysql()
            diagrama = construir_diagrama_copo_nieve_mysql(diagrama_base)
        else:
            diagrama_base = generar_diagrama_mongodb()
            diagrama = construir_diagrama_copo_nieve_mongodb(diagrama_base)
        
        if 'error' in diagrama:
            return jsonify({
                'success': False,
                'message': diagrama['error']
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Diagrama de COPO DE NIEVE para {DB_TYPE.upper()} generado',
            'data': diagrama
        }), 200
        
    except Exception as e:
        print(f"❌ Error en generar_diagrama_copo_nieve: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


def construir_diagrama_copo_nieve_mysql(diagrama_base):
    """Construir estructura de copo de nieve a partir del diagrama ER MySQL"""
    try:
        # Mapeo de tablas a dimensiones
        dimension_mapping = {
            'users': {
                'nombre': 'dim_usuarios',
                'descripcion': 'Dimensión de usuarios - Información demográfica',
                'atributos': ['id', 'nombre', 'correo', 'telefono', 'sexo', 'edad', 'tipo_cuenta'],
                'jerarquias': {
                    'demografia': ['tipo_cuenta', 'sexo', 'grupo_edad']
                }
            },
            'direcciones': {
                'nombre': 'dim_ubicacion',
                'descripcion': 'Dimensión geográfica - Ubicaciones',
                'atributos': ['id', 'calle', 'colonia', 'ciudad', 'estado', 'codigo_postal'],
                'jerarquias': {
                    'geografia': ['codigo_postal', 'colonia', 'ciudad', 'estado']
                }
            },
            'suplementos': {
                'nombre': 'dim_productos',
                'descripcion': 'Dimensión de productos - Suplementos',
                'atributos': ['id', 'nombre', 'descripcion', 'precio', 'stock', 'categoria'],
                'jerarquias': {
                    'categoria': ['categoria', 'subcategoria', 'producto']
                }
            },
            'tarjetas': {
                'nombre': 'dim_pagos',
                'descripcion': 'Dimensión de pagos - Métodos de pago',
                'atributos': ['id', 'tipo', 'ultimos_digitos', 'nombre_titular'],
                'jerarquias': {
                    'tipo_pago': ['tipo', 'banco']
                }
            },
            'dietas': {
                'nombre': 'dim_dietas',
                'descripcion': 'Dimensión de dietas - Planes nutricionales',
                'atributos': ['id', 'nombre', 'objetivo', 'calorias_totales', 'dificultad'],
                'jerarquias': {
                    'objetivo': ['objetivo', 'dificultad']
                }
            },
            'dietas_usuario': {
                'nombre': 'dim_asignacion_dietas',
                'descripcion': 'Dimensión de asignación de dietas a usuarios',
                'atributos': ['id', 'user_id', 'dieta_id', 'fecha_asignacion'],
                'jerarquias': {}
            },
            'seguimiento_dieta': {
                'nombre': 'dim_seguimiento_dieta',
                'descripcion': 'Sub-dimensión de seguimiento de dietas',
                'atributos': ['id', 'dieta_usuario_id', 'fecha', 'cumplimiento', 'progreso'],
                'jerarquias': {}
            },
            'notificaciones': {
                'nombre': 'dim_notificaciones',
                'descripcion': 'Dimensión de notificaciones',
                'atributos': ['id', 'user_id', 'titulo', 'mensaje', 'fecha_envio'],
                'jerarquias': {
                    'tiempo': ['fecha_envio']
                }
            },
            'backups': {
                'nombre': 'dim_backups',
                'descripcion': 'Dimensión de respaldos',
                'atributos': ['id', 'user_id', 'fecha_creacion', 'tamaño', 'tipo'],
                'jerarquias': {
                    'tiempo': ['fecha_creacion']
                }
            }
        }
        
        # Construir dimensiones
        dimensions = []
        tabla_hechos = None
        
        for tabla in diagrama_base.get('tablas', []):
            nombre_tabla = tabla['nombre']
            
            # Identificar tabla de hechos (fact table)
            if nombre_tabla == 'ordenes':
                tabla_hechos = {
                    'nombre': nombre_tabla,
                    'tipo': 'FACT_TABLE',
                    'descripcion': 'Tabla de hechos - Contiene las transacciones de órdenes',
                    'metricas': ['total', 'cantidad', 'fecha_orden'],
                    'total_registros': tabla.get('total_registros', 0)
                }
            
            # Crear dimensión si está en el mapping
            if nombre_tabla in dimension_mapping:
                dim_info = dimension_mapping[nombre_tabla]
                dimensions.append({
                    'nombre': dim_info['nombre'],
                    'tabla_fisica': nombre_tabla,
                    'tipo': 'DIMENSION',
                    'descripcion': dim_info['descripcion'],
                    'atributos': dim_info['atributos'],
                    'jerarquias': dim_info['jerarquias'],
                    'total_registros': tabla.get('total_registros', 0)
                })
        
        # Construir relaciones
        relaciones = []
        for dim in dimensions:
            relaciones.append({
                'tipo': 'FACT_TO_DIMENSION',
                'origen': 'ordenes',
                'destino': dim['nombre'],
                'cardinalidad': 'N:1',
                'join': f"ordenes.{dim['tabla_fisica']}_id = {dim['tabla_fisica']}.id"
            })
        
        # Sub-dimensiones (para seguimiento_dieta)
        sub_dimensions = []
        for tabla in diagrama_base.get('tablas', []):
            if tabla['nombre'] == 'seguimiento_dieta':
                sub_dimensions.append({
                    'nombre': 'dim_seguimiento',
                    'tabla_fisica': 'seguimiento_dieta',
                    'tipo': 'SUB_DIMENSION',
                    'descripcion': 'Sub-dimensión de seguimiento de dietas',
                    'dimension_padre': 'dim_dietas',
                    'atributos': ['fecha', 'cumplimiento', 'progreso', 'notas'],
                    'total_registros': tabla.get('total_registros', 0)
                })
                relaciones.append({
                    'tipo': 'DIMENSION_TO_SUB_DIMENSION',
                    'origen': 'dim_dietas',
                    'destino': 'dim_seguimiento',
                    'cardinalidad': '1:N',
                    'join': 'dim_dietas.id = dim_seguimiento.dieta_id'
                })
        
        # Construir diagrama final
        diagrama_copo = {
            'tipo_diagrama': 'SNOWFLAKE_SCHEMA',
            'tipo_bd': 'MySQL',
            'fecha_generacion': datetime.now().isoformat(),
            'descripcion': 'Diagrama de Copo de Nieve - Organización de datos en hechos y dimensiones',
            'total_tablas': diagrama_base.get('total_tablas', 0),
            'tablas': diagrama_base.get('tablas', []),
            'estructura': {
                'fact_table': tabla_hechos,
                'dimensions': dimensions,
                'sub_dimensions': sub_dimensions,
                'relaciones': relaciones
            },
            'metricas_sugeridas': {
                'kpi_principales': [
                    {
                        'nombre': 'Total Ventas',
                        'descripcion': 'Suma total de todas las órdenes',
                        'calculo': 'SUM(ordenes.total)',
                        'dimensiones_relacionadas': ['dim_tiempo', 'dim_usuarios']
                    },
                    {
                        'nombre': 'Órdenes por Usuario',
                        'descripcion': 'Promedio de órdenes por usuario',
                        'calculo': 'COUNT(ordenes.id) / COUNT(DISTINCT ordenes.user_id)',
                        'dimensiones_relacionadas': ['dim_usuarios']
                    },
                    {
                        'nombre': 'Productos Más Vendidos',
                        'descripcion': 'Top productos por cantidad vendida',
                        'calculo': 'SUM(ordenes.cantidad) GROUP BY suplemento_id',
                        'dimensiones_relacionadas': ['dim_productos']
                    }
                ]
            },
            'consultas_ejemplo': [
                {
                    'nombre': 'Ventas por tipo de usuario',
                    'sql': """
                        SELECT u.tipo_cuenta, COUNT(o.id) as ordenes, SUM(o.total) as ventas
                        FROM ordenes o
                        JOIN users u ON o.user_id = u.id
                        GROUP BY u.tipo_cuenta
                    """
                },
                {
                    'nombre': 'Productos más vendidos por región',
                    'sql': """
                        SELECT d.estado, s.nombre, SUM(o.cantidad) as unidades
                        FROM ordenes o
                        JOIN suplementos s ON o.suplemento_id = s.id
                        JOIN direcciones d ON o.direccion_id = d.id
                        GROUP BY d.estado, s.id
                    """
                }
            ]
        }
        
        return diagrama_copo
        
    except Exception as e:
        print(f"Error construyendo diagrama copo nieve MySQL: {e}")
        traceback.print_exc()
        return {'error': str(e), 'tipo_diagrama': 'SNOWFLAKE_SCHEMA', 'tipo_bd': 'MySQL'}


def construir_diagrama_copo_nieve_mongodb(diagrama_base):
    """Construir estructura de copo de nieve a partir del diagrama MongoDB"""
    try:
        dimension_mapping = {
            'users': {
                'nombre': 'dim_usuarios',
                'descripcion': 'Dimensión de usuarios',
                'atributos': ['nombre', 'correo', 'tipo_cuenta', 'edad']
            },
            'suplementos': {
                'nombre': 'dim_productos',
                'descripcion': 'Dimensión de productos',
                'atributos': ['nombre', 'precio', 'categoria', 'stock']
            },
            'direcciones': {
                'nombre': 'dim_ubicacion',
                'descripcion': 'Dimensión geográfica',
                'atributos': ['calle', 'colonia', 'ciudad', 'estado', 'codigo_postal']
            }
        }
        
        dimensions = []
        
        for coleccion in diagrama_base.get('colecciones', []):
            nombre_coleccion = coleccion['nombre']
            if nombre_coleccion in dimension_mapping:
                dim_info = dimension_mapping[nombre_coleccion]
                dimensions.append({
                    'nombre': dim_info['nombre'],
                    'coleccion_fisica': nombre_coleccion,
                    'tipo': 'DIMENSION',
                    'descripcion': dim_info['descripcion'],
                    'atributos': dim_info['atributos'],
                    'total_documentos': coleccion.get('total_documentos', 0)
                })
        
        diagrama_copo = {
            'tipo_diagrama': 'SNOWFLAKE_SCHEMA',
            'tipo_bd': 'MongoDB',
            'fecha_generacion': datetime.now().isoformat(),
            'descripcion': 'Diagrama de Copo de Nieve para MongoDB',
            'total_colecciones': diagrama_base.get('total_colecciones', 0),
            'colecciones': diagrama_base.get('colecciones', []),
            'estructura': {
                'fact_collection': {
                    'nombre': 'ordenes',
                    'tipo': 'FACT_COLLECTION',
                    'descripcion': 'Colección de hechos - Transacciones',
                    'metricas': ['total', 'cantidad', 'fecha_orden']
                },
                'dimensions': dimensions,
                'sub_dimensions': [],
                'relaciones': [
                    {
                        'tipo': 'FACT_TO_DIMENSION',
                        'origen': 'ordenes',
                        'destino': dim['nombre'],
                        'cardinalidad': 'N:1',
                        'implementacion': 'Referencia por ObjectId'
                    } for dim in dimensions
                ]
            }
        }
        
        return diagrama_copo
        
    except Exception as e:
        print(f"Error construyendo diagrama copo nieve MongoDB: {e}")
        traceback.print_exc()
        return {'error': str(e), 'tipo_diagrama': 'SNOWFLAKE_SCHEMA', 'tipo_bd': 'MongoDB'}


def exportar_diagrama_copo_nieve_json():
    """Exportar diagrama copo nieve como JSON"""
    try:
        if DB_TYPE == 'mysql':
            diagrama_base = generar_diagrama_mysql()
            diagrama = construir_diagrama_copo_nieve_mysql(diagrama_base)
        else:
            diagrama_base = generar_diagrama_mongodb()
            diagrama = construir_diagrama_copo_nieve_mongodb(diagrama_base)
        
        if 'error' in diagrama:
            return jsonify({
                'success': False,
                'message': diagrama['error']
            }), 500
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(diagrama, f, indent=2, default=str)
            temp_path = f.name
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"diagrama_copo_nieve_{DB_TYPE}_{timestamp}.json"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


def exportar_diagrama_copo_nieve_sql():
    """Exportar diagrama copo nieve como SQL"""
    try:
        if DB_TYPE != 'mysql':
            return jsonify({
                'success': False,
                'message': 'SQL solo disponible para MySQL'
            }), 400
        
        diagrama = construir_diagrama_copo_nieve_mysql(generar_diagrama_mysql())
        
        if 'error' in diagrama:
            return jsonify({
                'success': False,
                'message': diagrama['error']
            }), 500
        
        sql_lines = [
            "-- ===========================================",
            f"-- DIAGRAMA DE COPO DE NIEVE (SNOWFLAKE SCHEMA)",
            f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-- ===========================================",
            "",
            "-- ===========================================",
            "-- TABLA DE HECHOS (FACT TABLE)",
            "-- ===========================================",
            "",
            "CREATE OR REPLACE VIEW vista_hechos_ordenes AS",
            "SELECT ",
            "    id as orden_id,",
            "    user_id,",
            "    suplemento_id,",
            "    direccion_id,",
            "    total,",
            "    cantidad,",
            "    fecha_orden,",
            "    YEAR(fecha_orden) as anio,",
            "    MONTH(fecha_orden) as mes,",
            "    DATE(fecha_orden) as fecha",
            "FROM ordenes;",
            "",
            "-- ===========================================",
            "-- VISTA DE COPO DE NIEVE",
            "-- ===========================================",
            "",
            "CREATE OR REPLACE VIEW vista_copo_nieve AS",
            "SELECT ",
            "    o.orden_id,",
            "    o.total,",
            "    o.cantidad,",
            "    o.fecha_orden,",
            "    o.anio,",
            "    o.mes,",
            "    u.nombre as usuario_nombre,",
            "    u.tipo_cuenta,",
            "    u.edad,",
            "    s.nombre as producto_nombre,",
            "    s.categoria,",
            "    s.precio,",
            "    d.estado,",
            "    d.ciudad",
            "FROM vista_hechos_ordenes o",
            "LEFT JOIN users u ON o.user_id = u.id",
            "LEFT JOIN suplementos s ON o.suplemento_id = s.id",
            "LEFT JOIN direcciones d ON o.direccion_id = d.id;",
            "",
            "-- ===========================================",
            "-- CONSULTAS DE EJEMPLO",
            "-- ===========================================",
            "",
            "-- Ventas por tipo de usuario y mes",
            "SELECT tipo_cuenta, anio, mes, SUM(total) as ventas, COUNT(*) as ordenes",
            "FROM vista_copo_nieve",
            "GROUP BY tipo_cuenta, anio, mes;",
            "",
            "-- Productos más vendidos por región",
            "SELECT estado, producto_nombre, SUM(cantidad) as unidades, SUM(total) as ingresos",
            "FROM vista_copo_nieve",
            "GROUP BY estado, producto_nombre",
            "ORDER BY ingresos DESC;"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
            temp_path = f.name
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"diagrama_copo_nieve_{DB_TYPE}_{timestamp}.sql"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500