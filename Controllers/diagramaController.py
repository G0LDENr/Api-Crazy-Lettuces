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
        
        # Mapeo de modelos SQLAlchemy
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
            
            # Columnas
            for col in columnas:
                info_tabla['columnas'].append({
                    'nombre': col['name'],
                    'tipo': str(col['type']),
                    'nullable': col['nullable'],
                    'default': str(col['default']) if col['default'] else None
                })
            
            # Foreign Keys
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
            
            # Total registros
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
            # Estadísticas
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
            import tempfile
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
            
        else:  # MongoDB
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
        
        # Intentar MySQL
        try:
            inspector = db_sql.inspect(db_sql.engine)
            tablas = inspector.get_table_names()
            if tablas:
                estructura_mysql = generar_diagrama_mysql()
        except Exception as e:
            errores.append(f"MySQL: {str(e)}")
        
        # Intentar MongoDB
        try:
            colecciones = db_mongo.db.list_collection_names()
            if colecciones:
                estructura_mongo = generar_diagrama_mongodb()
        except Exception as e:
            errores.append(f"MongoDB: {str(e)}")
        
        comparacion = {
            'fecha': datetime.now().isoformat(),
            'mysql_disponible': estructura_mysql is not None,
            'mongodb_disponible': estructura_mongo is not None,
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
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500