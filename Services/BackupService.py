import os
import gzip
import shutil
import json
from datetime import datetime
from config import DB_TYPE, db_sql, db_mongo
from Models.Backup import Backup
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
import subprocess
import re
import traceback
from bson import json_util
from bson.objectid import ObjectId

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = 'backups'
        self.scheduler = None
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
        
        # Si se pasó una app, inicializar
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self.setup_scheduler()
        logger.info("BackupService inicializado con la aplicación Flask")
    
    def setup_scheduler(self):
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            logger.info("Scheduler de respaldos iniciado")
    
    def _get_app(self):
        """Obtener la aplicación actual (de self o de current_app)"""
        if self.app is not None:
            return self.app
        try:
            return current_app._get_current_object()
        except:
            logger.error("No se pudo obtener la aplicación Flask")
            return None
    
    def create_backup_filename(self, custom_name=None, backup_type='full'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if custom_name:
            clean_name = custom_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{clean_name}_{timestamp}"
        else:
            filename = f"backup_{backup_type}_{timestamp}"
        
        # Extensión según tipo de BD
        if DB_TYPE == 'mysql':
            filename += ".sql"
        else:
            filename += ".json"
        
        return os.path.join(self.backup_dir, filename)
    
    # ==================== MÉTODOS PARA MYSQL ====================
    def get_mysql_tables(self):
        """Obtener tablas de MySQL"""
        app = self._get_app()
        if app is None:
            logger.error("No se pudo obtener la aplicación Flask para get_mysql_tables")
            return []
        
        with app.app_context():
            try:
                from sqlalchemy import inspect
                inspector = inspect(db_sql.engine)
                tables = inspector.get_table_names()
                logger.info(f"Tablas encontradas: {tables}")
                return tables
            except Exception as e:
                logger.error(f"Error obteniendo tablas MySQL: {e}")
                return []
    
    def get_mysql_table_structure(self, table_name):
        """Obtener estructura CREATE TABLE de MySQL"""
        app = self._get_app()
        if app is None:
            logger.error("No se pudo obtener la aplicación Flask")
            return ""
        
        with app.app_context():
            try:
                from sqlalchemy import text
                result = db_sql.session.execute(
                    text(f"SHOW CREATE TABLE `{table_name}`")
                ).fetchone()
                
                if result and len(result) >= 2:
                    return result[1] + ";\n\n"
            except Exception as e:
                logger.warning(f"No se pudo obtener estructura de {table_name}: {str(e)}")
            return ""
    
    def get_mysql_table_data(self, table_name):
        """Obtener datos INSERT de MySQL"""
        app = self._get_app()
        if app is None:
            logger.error("No se pudo obtener la aplicación Flask")
            return f"-- Error: No se pudo obtener la aplicación para {table_name}\n"
        
        with app.app_context():
            try:
                from sqlalchemy import text
                result = db_sql.session.execute(text(f"SELECT * FROM `{table_name}`"))
                columns = result.keys()
                sql_lines = []
                batch_size = 100
                current_batch = []
                
                for row in result:
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, (int, float)):
                            values.append(str(value))
                        elif isinstance(value, datetime):
                            values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                        elif isinstance(value, (dict, list)):
                            # Convertir JSON a string escapado
                            json_str = json.dumps(value, ensure_ascii=False)
                            escaped = json_str.replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            escaped = str(value).replace("'", "''")
                            values.append(f"'{escaped}'")
                    
                    current_batch.append(f"({', '.join(values)})")
                    
                    if len(current_batch) >= batch_size:
                        columns_str = ', '.join([f"`{col}`" for col in columns])
                        sql_lines.append(
                            f"INSERT INTO `{table_name}` ({columns_str}) VALUES \n  " +
                            ",\n  ".join(current_batch) + ";\n"
                        )
                        current_batch = []
                
                if current_batch:
                    columns_str = ', '.join([f"`{col}`" for col in columns])
                    sql_lines.append(
                        f"INSERT INTO `{table_name}` ({columns_str}) VALUES \n  " +
                        ",\n  ".join(current_batch) + ";\n"
                    )
                
                return "\n".join(sql_lines) if sql_lines else f"-- Tabla `{table_name}` está vacía\n"
                
            except Exception as e:
                logger.error(f"Error al obtener datos de {table_name}: {str(e)}")
                return f"-- Error al obtener datos de {table_name}: {str(e)}\n"
    
    # ==================== MÉTODOS PARA MONGODB ====================
    def get_mongo_collections(self):
        """Obtener colecciones de MongoDB (no necesita app_context)"""
        try:
            return db_mongo.db.list_collection_names()
        except Exception as e:
            logger.error(f"Error obteniendo colecciones MongoDB: {e}")
            return []
    
    def get_mongo_collection_data(self, collection_name):
        """Obtener datos de una colección MongoDB"""
        try:
            collection = db_mongo.db[collection_name]
            documents = list(collection.find())
            
            # Convertir ObjectId a string para JSON
            for doc in documents:
                if '_id' in doc and isinstance(doc['_id'], ObjectId):
                    doc['_id'] = str(doc['_id'])
                
                # Asegurar que todos los strings sean cadenas normales
                for key, value in doc.items():
                    if isinstance(value, str):
                        # Mantener el string como está, el escape se hará al serializar
                        pass
                    elif isinstance(value, datetime):
                        doc[key] = value.isoformat()
                    elif isinstance(value, ObjectId):
                        doc[key] = str(value)
            
            return documents
        except Exception as e:
            logger.error(f"Error al obtener datos de {collection_name}: {e}")
            return []
    
    def export_mongo_collection(self, collection_name, f, is_last=False):
        """Exportar una colección de MongoDB al archivo con JSON válido - MANTIENE IDs ORIGINALES"""
        try:
            documents = self.get_mongo_collection_data(collection_name)
            
            # Escribir solo JSON válido, sin comentarios
            f.write(f"  {{\n")
            f.write(f'    "collection": "{collection_name}",\n')
            f.write(f'    "documents": [\n')
            
            for i, doc in enumerate(documents):
                # Procesar el documento para asegurar JSON válido
                processed_doc = {}
                for key, value in doc.items():
                    if isinstance(value, str):
                        # Escapar caracteres especiales para JSON
                        processed_doc[key] = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    elif isinstance(value, (datetime, ObjectId)):
                        processed_doc[key] = str(value)  # Mantener como string para preservar ID
                    else:
                        processed_doc[key] = value
                
                # Convertir a JSON con indentación
                json_str = json.dumps(processed_doc, ensure_ascii=False, indent=2)
                
                # Escribir el documento
                f.write(json_str)
                
                if i < len(documents) - 1:
                    f.write(",\n")
                else:
                    f.write("\n")
            
            f.write(f"    ]\n")
            f.write(f"  }}")
            
            logger.info(f"  ✅ {collection_name}: {len(documents)} documentos (IDs preservados)")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error exportando {collection_name}: {e}")
            return 0
    
    # ==================== MÉTODO PRINCIPAL DE BACKUP ====================
    def perform_backup(self, tables=None, collections=None, custom_name=None, **kwargs):
        """
        Realizar backup según DB_TYPE
        Acepta 'tables' (para MySQL) o 'collections' (para MongoDB)
        """
        try:
            logger.info(f"Iniciando creación de respaldo...")
            
            # Determinar qué items respaldar
            items_to_backup = None
            
            # IMPORTANTE: Para MongoDB, usar 'collections'
            # Para MySQL, usar 'tables'
            if DB_TYPE == 'mysql':
                if tables is not None:
                    items_to_backup = tables
                    logger.info(f"Usando 'tables' para backup MySQL")
                elif 'items' in kwargs:
                    items_to_backup = kwargs['items']
                    logger.info(f"Usando 'items' para backup")
                else:
                    logger.info(f"Backup completo MySQL (sin filtros)")
            else:  # MongoDB
                if collections is not None:
                    items_to_backup = collections
                    logger.info(f"Usando 'collections' para backup MongoDB")
                elif tables is not None:
                    # Si viene como 'tables' desde el frontend, convertirlo
                    items_to_backup = tables
                    logger.info(f"Usando 'tables' como colecciones para backup MongoDB")
                elif 'items' in kwargs:
                    items_to_backup = kwargs['items']
                    logger.info(f"Usando 'items' para backup")
                else:
                    logger.info(f"Backup completo MongoDB (sin filtros)")
            
            # Backup según tipo de BD
            if DB_TYPE == 'mysql':
                logger.info(f"Ejecutando backup MySQL")
                return self._perform_mysql_backup(items_to_backup, custom_name)
            else:
                logger.info(f"Ejecutando backup MongoDB")
                return self._perform_mongo_backup(items_to_backup, custom_name)
                
        except Exception as e:
            logger.error(f"Error en perform_backup: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': f'Error al crear respaldo: {str(e)}'}
    
    def _perform_mysql_backup(self, tables=None, custom_name=None):
        """Backup para MySQL"""
        try:
            backup_type = 'partial' if tables else 'full'
            filepath = self.create_backup_filename(custom_name, backup_type)
            
            if not tables:
                tables_to_backup = self.get_mysql_tables()
                logger.info(f"Respaldo COMPLETO de {len(tables_to_backup)} tablas")
            else:
                tables_to_backup = tables
                logger.info(f"Respaldo PARCIAL de {len(tables_to_backup)} tablas")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"-- Backup generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Tipo: {backup_type.upper()}\n")
                f.write(f"-- DB_TYPE: mysql\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                
                for i, table_name in enumerate(tables_to_backup, 1):
                    try:
                        logger.info(f"Procesando tabla {i}/{len(tables_to_backup)}: {table_name}")
                        
                        f.write(f"-- Estructura de la tabla: {table_name}\n")
                        create_statement = self.get_mysql_table_structure(table_name)
                        if create_statement:
                            f.write(create_statement)
                        
                        f.write(f"-- Datos de la tabla: {table_name}\n")
                        insert_statements = self.get_mysql_table_data(table_name)
                        f.write(insert_statements)
                        
                        f.write(f"-- Fin de datos para tabla: {table_name}\n\n")
                        
                    except Exception as e:
                        logger.error(f"Error procesando tabla {table_name}: {str(e)}")
                        f.write(f"-- ERROR procesando tabla {table_name}: {str(e)}\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
            
            # Comprimir
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"Tamaño: {size_mb:.2f} MB")
            
            compressed_path = self.compress_backup(filepath)
            if compressed_path:
                filepath = compressed_path
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            # Guardar registro
            backup_data = {
                'filename': os.path.basename(filepath),
                'filepath': os.path.abspath(filepath),
                'size_mb': round(size_mb, 2),
                'tables_included': tables_to_backup,
                'backup_type': backup_type,
                'status': 'completed'
            }
            
            backup_id = Backup.create_backup_record(backup_data)
            logger.info(f"Registro creado ID: {backup_id}")
            
            return {
                'success': True,
                'message': f'Respaldo {backup_type} creado exitosamente',
                'backup_id': backup_id,
                'filename': backup_data['filename'],
                'db_type': 'mysql'
            }
            
        except Exception as e:
            logger.error(f"Error en backup MySQL: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': f'Error en backup MySQL: {str(e)}'}
    
    def _perform_mongo_backup(self, collections=None, custom_name=None):
        """Backup para MongoDB - Maneja colecciones seleccionadas"""
        try:
            backup_type = 'partial' if collections else 'full'
            filepath = self.create_backup_filename(custom_name, backup_type)
            
            if not collections:
                # Backup completo: obtener TODAS las colecciones
                all_collections = self.get_mongo_collections()
                # Excluir la colección 'backups' para no respaldarla (opcional)
                # collections_to_backup = [c for c in all_collections if c != 'backups']
                collections_to_backup = all_collections
                logger.info(f"Respaldo COMPLETO de {len(collections_to_backup)} colecciones")
            else:
                # Backup parcial: usar las colecciones seleccionadas
                # Asegurarse de que collections sea una lista
                if isinstance(collections, str):
                    collections_to_backup = [collections]
                else:
                    collections_to_backup = collections
                logger.info(f"Respaldo PARCIAL de {len(collections_to_backup)} colecciones: {collections_to_backup}")
            
            if not collections_to_backup:
                logger.warning("⚠️ No hay colecciones para respaldar")
                return {'success': False, 'message': 'No hay colecciones seleccionadas para respaldar'}
            
            stats = {
                'total_collections': 0,
                'total_documents': 0,
                'collections': {}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("{\n")
                f.write(f'  "backup_info": {{\n')
                f.write(f'    "fecha": "{datetime.now().isoformat()}",\n')
                f.write(f'    "tipo": "{backup_type}",\n')
                f.write(f'    "db_type": "mongodb",\n')
                f.write(f'    "version": "1.0",\n')
                f.write(f'    "restore_mode": "upsert"\n')
                f.write(f'  }},\n\n')
                f.write(f'  "collections": [\n')
                
                for i, collection_name in enumerate(collections_to_backup):
                    try:
                        logger.info(f"Procesando colección {i+1}/{len(collections_to_backup)}: {collection_name}")
                        
                        # Verificar que la colección existe
                        if collection_name not in db_mongo.db.list_collection_names():
                            logger.warning(f"⚠️ Colección {collection_name} no existe, omitiendo...")
                            continue
                        
                        doc_count = self.export_mongo_collection(collection_name, f)
                        
                        stats['total_collections'] += 1
                        stats['total_documents'] += doc_count
                        stats['collections'][collection_name] = doc_count
                        
                        # Agregar coma después de cada colección excepto la última
                        if i < len(collections_to_backup) - 1:
                            f.write(",\n")
                        else:
                            f.write("\n")
                        
                    except Exception as e:
                        logger.error(f"Error procesando colección {collection_name}: {str(e)}")
                        f.write(f'    {{ "error": "Error procesando {collection_name}: {str(e)}" }}\n')
                        if i < len(collections_to_backup) - 1:
                            f.write(",\n")
                
                f.write(f'  ]\n')
                f.write(f'}}\n')
            
            # Comprimir
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"Tamaño: {size_mb:.2f} MB")
            logger.info(f"Total documentos: {stats['total_documents']}")
            
            compressed_path = self.compress_backup(filepath)
            if compressed_path:
                filepath = compressed_path
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            # Guardar registro
            backup_data = {
                'filename': os.path.basename(filepath),
                'filepath': os.path.abspath(filepath),
                'size_mb': round(size_mb, 2),
                'tables_included': collections_to_backup,
                'backup_type': backup_type,
                'status': 'completed'
            }
            
            backup_id = Backup.create_backup_record(backup_data)
            logger.info(f"Registro creado ID: {backup_id}")
            
            return {
                'success': True,
                'message': f'Respaldo {backup_type} creado exitosamente',
                'backup_id': backup_id,
                'filename': backup_data['filename'],
                'db_type': 'mongodb',
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error en backup MongoDB: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': f'Error en backup MongoDB: {str(e)}'}
    
    def compress_backup(self, filepath):
        try:
            compressed_path = filepath + '.gz'
            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(filepath)
            return compressed_path
        except Exception as e:
            logger.warning(f"No se pudo comprimir: {e}")
            return None
    
    # ==================== MÉTODO RESTORE CORREGIDO ====================
    def restore_backup(self, backup_id):
        """
        Restaurar backup - CON PROTECCIÓN para evitar eliminación accidental
        """
        try:
            logger.info(f"🔄 Iniciando restauración ID: {backup_id}")
            
            # ACTIVAR PROTECCIÓN - Evita que se elimine durante la restauración
            Backup.protect_backup(backup_id)
            
            try:
                # Obtener respaldo
                backup = Backup.find_by_id(backup_id)
                if not backup:
                    logger.error(f"❌ Respaldo no encontrado: {backup_id}")
                    return {'success': False, 'message': 'Respaldo no encontrado'}
                
                # Verificar si backup es un objeto SQLAlchemy o un dict de MongoDB
                if isinstance(backup, dict):
                    filepath = backup.get('filepath')
                    filename = backup.get('filename', '')
                    logger.info(f"📄 Respaldo MongoDB encontrado: {filename}")
                else:
                    filepath = getattr(backup, 'filepath', None)
                    filename = getattr(backup, 'filename', '')
                    logger.info(f"📄 Respaldo MySQL encontrado: {filename}")
                
                if not filepath or not os.path.exists(filepath):
                    logger.error(f"❌ Archivo no encontrado: {filepath}")
                    return {'success': False, 'message': 'Archivo no encontrado'}
                
                # Detectar tipo de backup
                if filename.endswith('.sql') or filename.endswith('.sql.gz'):
                    result = self._restore_mysql_backup(backup, filepath, filename)
                else:
                    result = self._restore_mongo_backup(backup, filepath, filename)
                
                return result
                
            finally:
                # DESACTIVAR PROTECCIÓN - Siempre se ejecuta incluso si hay error
                Backup.unprotect_backup(backup_id)
                
        except Exception as e:
            logger.error(f"💥 ERROR FATAL: {e}")
            logger.error(traceback.format_exc())
            Backup.unprotect_backup(backup_id)  # Asegurar limpieza
            return {'success': False, 'message': f'Error en restauración: {str(e)}'}
    
    def _restore_mysql_backup(self, backup, filepath, filename):
        """Restaurar backup de MySQL - REEMPLAZA completamente las tablas"""
        try:
            # Extraer credenciales
            db_uri = os.getenv('DATABASE_URL')
            if not db_uri:
                app = self._get_app()
                if app:
                    with app.app_context():
                        db_uri = app.config.get('DATABASE_URL')
            
            if not db_uri:
                logger.error("❌ No se encontró DATABASE_URL")
                return {'success': False, 'message': 'Error: No se encontró DATABASE_URL'}
            
            match = re.search(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):?(\d*)/(.+)', db_uri)
            
            if not match:
                logger.error(f"❌ No se pudo parsear DATABASE_URL")
                return {'success': False, 'message': 'Error parseando DATABASE_URL'}
            
            username = match.group(1)
            password = match.group(2)
            host = match.group(3)
            port = match.group(4) or '3306'
            database = match.group(5)
            
            # Preparar archivo
            file_to_restore = filepath
            
            if filepath.endswith('.gz'):
                logger.info("📦 Descomprimiendo archivo...")
                decompressed_path = filepath.replace('.gz', '')
                with gzip.open(filepath, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                file_to_restore = decompressed_path
            
            # Crear archivo SQL modificado para REEMPLAZAR datos
            logger.info("📝 Preparando archivo SQL para restauración...")
            modified_file = file_to_restore + '_modified.sql'
            
            with open(file_to_restore, 'r', encoding='utf-8', errors='ignore') as f_in:
                content = f_in.read()
            
            # Modificar el contenido para REEMPLAZAR en lugar de IGNORAR
            # 1. Cambiar CREATE TABLE por CREATE TABLE IF NOT EXISTS
            content = re.sub(
                r'CREATE TABLE `(alembic_version|backups|direcciones|especiales|ingredientes|notificaciones|ordenes|tarjetas|users)`',
                r'CREATE TABLE IF NOT EXISTS `\1`',
                content,
                flags=re.IGNORECASE
            )
            
            # 2. CAMBIO IMPORTANTE: Usar REPLACE INTO en lugar de INSERT IGNORE
            # Esto eliminará los registros existentes y los reemplazará con los del backup
            content = re.sub(
                r'INSERT INTO `(\w+)`',
                r'REPLACE INTO `\1`',
                content,
                flags=re.IGNORECASE
            )
            
            # 3. Para alembic_version, manejarlo especialmente (no reemplazar)
            content = re.sub(
                r'REPLACE INTO `alembic_version`.*?;',
                '-- Versión de migración preservada\n',
                content,
                flags=re.IGNORECASE | re.DOTALL
            )
            
            # 4. Agregar TRUNCATE TABLE antes de cada REPLACE para asegurar limpieza completa
            # (opcional, REPLACE ya maneja el reemplazo)
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.strip().startswith('REPLACE INTO'):
                    table_match = re.search(r'REPLACE INTO `(\w+)`', line)
                    if table_match and table_match.group(1) != 'alembic_version':
                        new_lines.append(f"DELETE FROM `{table_match.group(1)}`;")
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
            
            # Guardar archivo modificado
            with open(modified_file, 'w', encoding='utf-8') as f_out:
                f_out.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                f_out.write(content)
                f_out.write("\nSET FOREIGN_KEY_CHECKS=1;\n")
            
            logger.info(f"✅ Archivo SQL preparado: {modified_file}")
            
            # Buscar mysql.exe
            mysql_paths = [
                'C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysql.exe',
                'C:\\Program Files\\MySQL\\MySQL Server 5.7\\bin\\mysql.exe',
                'C:\\xampp\\mysql\\bin\\mysql.exe',
                'C:\\wamp64\\bin\\mysql\\mysql8.0.31\\bin\\mysql.exe',
                'mysql.exe'
            ]
            
            mysql_exe = None
            for path in mysql_paths:
                if os.path.exists(path):
                    mysql_exe = path
                    break
            
            if not mysql_exe:
                import shutil as shutil_path
                mysql_exe = shutil_path.which('mysql')
            
            if not mysql_exe:
                return {'success': False, 'message': 'No se encontró mysql.exe'}
            
            # Ejecutar restauración con el archivo modificado
            logger.info(f"🚀 Ejecutando restauración...")
            
            cmd = [
                'cmd', '/c', 
                f'"{mysql_exe}"',
                f'--host={host}',
                f'--port={port}',
                f'--user={username}',
                f'--password={password}',
                '--default-character-set=utf8mb4',
                '--force',  # Continuar incluso si hay errores
                database,
                '<',
                f'"{modified_file}"'
            ]
            
            cmd_str = ' '.join(cmd)
            
            process = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Limpiar archivos temporales
            if filepath.endswith('.gz') and os.path.exists(file_to_restore):
                os.remove(file_to_restore)
            if os.path.exists(modified_file):
                os.remove(modified_file)
            
            # Verificar resultado
            if process.returncode == 0:
                logger.info("✅ Restauración completada exitosamente")
                
                # Verificar que la tabla alembic_version tenga un registro
                try:
                    app = self._get_app()
                    if app:
                        with app.app_context():
                            from sqlalchemy import text
                            result = db_sql.session.execute(
                                text("SELECT COUNT(*) FROM alembic_version")
                            ).scalar()
                            
                            if result == 0:
                                logger.warning("⚠️ Tabla alembic_version vacía, insertando versión por defecto")
                                db_sql.session.execute(
                                    text("INSERT INTO alembic_version (version_num) VALUES ('base')")
                                )
                                db_sql.session.commit()
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo verificar alembic_version: {e}")
                
                return {'success': True, 'message': 'Restauración completada'}
            else:
                error_msg = process.stderr[:500] if process.stderr else 'Error desconocido'
                
                # Filtrar errores conocidos que no son críticos
                if "Table 'alembic_version' already exists" in error_msg:
                    logger.warning("⚠️ Tabla alembic_version ya existía (esto es normal)")
                    return {
                        'success': True, 
                        'message': 'Restauración completada (tablas existentes preservadas)'
                    }
                else:
                    logger.error(f"❌ Error en restauración: {error_msg}")
                    return {'success': False, 'message': f'Error: {error_msg}'}
                    
        except Exception as e:
            logger.error(f"Error en restore MySQL: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': str(e)}
    
    def _restore_mongo_backup(self, backup, filepath, filename):
        """Restaurar backup de MongoDB - MANTIENE LOS IDs ORIGINALES como en MySQL"""
        try:
            logger.info("=" * 60)
            logger.info(f"🔍 RESTAURACIÓN MONGODB (modo REPLACE INTO con IDs originales)")
            logger.info(f"📁 Filepath: {filepath}")
            logger.info(f"📄 Filename: {filename}")
            
            # Verificar archivo físico
            if not os.path.exists(filepath):
                logger.error(f"❌ Archivo no encontrado: {filepath}")
                return {'success': False, 'message': 'Archivo no encontrado'}
            
            # Procesar el archivo (comprimido o no)
            is_compressed = filepath.endswith('.gz')
            temp_file_path = None
            file_to_read = filepath
            
            if is_compressed:
                import uuid
                temp_dir = os.path.dirname(filepath)
                temp_filename = f"temp_restore_{uuid.uuid4().hex}_{os.path.basename(filepath).replace('.gz', '')}"
                temp_file_path = os.path.join(temp_dir, temp_filename)
                
                logger.info(f"📦 Descomprimiendo a: {temp_file_path}")
                try:
                    with gzip.open(filepath, 'rb') as f_in:
                        with open(temp_file_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    file_to_read = temp_file_path
                    logger.info("✅ Descompresión exitosa")
                except Exception as e:
                    logger.error(f"❌ Error descomprimiendo: {e}")
                    return {'success': False, 'message': f'Error descomprimiendo: {e}'}
            
            # Leer JSON
            try:
                with open(file_to_read, 'r', encoding='utf-8') as f:
                    content = f.read()
                    data = json.loads(content, object_hook=json_util.object_hook)
                    logger.info("✅ JSON parseado correctamente")
            except Exception as e:
                logger.error(f"❌ Error leyendo JSON: {e}")
                return {'success': False, 'message': f'Error leyendo JSON: {e}'}
            
            # Restaurar datos - Modo REPLACE con IDs originales
            collections_updated = 0
            documents_updated = 0
            documents_inserted = 0
            collections_skipped = 0
            
            collections_data = data.get('collections', [])
            logger.info(f"📚 Encontradas {len(collections_data)} colecciones en el backup")
            
            # Colecciones que NO deben ser restauradas (para preservar los registros)
            EXCLUDED_COLLECTIONS = ['backups']
            
            for collection_data in collections_data:
                try:
                    collection_name = collection_data.get('collection')
                    documents = collection_data.get('documents', [])
                    
                    if not collection_name:
                        continue
                    
                    # SALTAR la colección backups para no perder los registros existentes
                    if collection_name in EXCLUDED_COLLECTIONS:
                        logger.info(f"⏭️ SALTANDO colección {collection_name} (para preservar registros de backups)")
                        collections_skipped += 1
                        continue
                    
                    logger.info(f"🔄 Procesando {collection_name}: {len(documents)} documentos")
                    collection = db_mongo.db[collection_name]
                    
                    updated_in_collection = 0
                    inserted_in_collection = 0
                    
                    for doc in documents:
                        try:
                            # PRESERVAR EL ID ORIGINAL
                            original_id = doc.get('_id')
                            
                            if original_id:
                                # Convertir el ID string a ObjectId si es necesario
                                if isinstance(original_id, str):
                                    try:
                                        doc['_id'] = ObjectId(original_id)
                                    except:
                                        # Si no es un ObjectId válido, mantener como string
                                        doc['_id'] = original_id
                                elif isinstance(original_id, ObjectId):
                                    doc['_id'] = original_id
                                
                                # Buscar si el documento ya existe por su ID original
                                existing = collection.find_one({'_id': doc['_id']})
                                
                                if existing:
                                    # Actualizar documento existente (mantiene el mismo ID)
                                    update_doc = {k: v for k, v in doc.items() if k != '_id'}
                                    result = collection.update_one(
                                        {'_id': doc['_id']},
                                        {'$set': update_doc}
                                    )
                                    if result.modified_count > 0:
                                        updated_in_collection += 1
                                        logger.debug(f"    ✏️ Actualizado documento con ID {doc['_id']}")
                                    else:
                                        logger.debug(f"    ℹ️ Documento con ID {doc['_id']} no cambió")
                                else:
                                    # Insertar nuevo documento con el ID ORIGINAL del backup
                                    collection.insert_one(doc)
                                    inserted_in_collection += 1
                                    logger.debug(f"    ➕ Insertado nuevo documento con ID {doc['_id']}")
                            else:
                                # Sin _id, insertar sin ID (MongoDB generará uno nuevo)
                                result = collection.insert_one(doc)
                                inserted_in_collection += 1
                                logger.debug(f"    ➕ Insertado documento sin ID (nuevo: {result.inserted_id})")
                                
                        except Exception as doc_error:
                            logger.error(f"    ❌ Error procesando documento: {doc_error}")
                            continue
                    
                    documents_updated += updated_in_collection
                    documents_inserted += inserted_in_collection
                    collections_updated += 1
                    
                    logger.info(f"  ✅ {collection_name}: {updated_in_collection} actualizados, {inserted_in_collection} insertados")
                    
                except Exception as e:
                    logger.error(f"❌ Error en colección {collection_name}: {e}")
                    continue
            
            # Limpiar archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"🗑️ Temporal eliminado: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo eliminar temporal: {e}")
            
            logger.info("=" * 60)
            logger.info(f"✅ RESTAURACIÓN COMPLETADA (modo REPLACE INTO con IDs originales)")
            logger.info(f"   - Colecciones procesadas: {collections_updated}")
            logger.info(f"   - Documentos actualizados: {documents_updated}")
            logger.info(f"   - Documentos insertados: {documents_inserted}")
            logger.info(f"   - Colecciones omitidas: {collections_skipped} (backups)")
            logger.info(f"✅ Los IDs originales se mantienen como en MySQL")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'message': f'Restauración completada: {collections_updated} colecciones, {documents_updated} actualizados, {documents_inserted} insertados',
                'updated': documents_updated,
                'inserted': documents_inserted,
                'collections': collections_updated
            }
            
        except Exception as e:
            logger.error(f"❌ Error en restore MongoDB: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def cleanup_old_backups(self, keep_last=50):
        try:
            backups = Backup.get_all_backups()
            if len(backups) > keep_last:
                for backup in backups[keep_last:]:
                    try:
                        if isinstance(backup, dict):
                            filepath = backup.get('filepath')
                            backup_id = backup.get('_id')
                        else:
                            filepath = getattr(backup, 'filepath', None)
                            backup_id = getattr(backup, 'id', None)
                        
                        if filepath and os.path.exists(filepath):
                            os.remove(filepath)
                        
                        # Eliminar registro según DB_TYPE
                        if DB_TYPE == 'mysql':
                            from Models.Backup import BackupSQL
                            db_sql.session.delete(backup)
                        else:
                            backup_collection = Backup._get_collection()
                            if backup_id:
                                backup_collection.delete_one({'_id': backup_id})
                            
                    except Exception as e:
                        logger.error(f"Error eliminando backup: {e}")
                
                if DB_TYPE == 'mysql':
                    db_sql.session.commit()
                    
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
    
    # ==================== MÉTODOS PARA PROGRAMACIÓN ====================
    def schedule_automatic_backup(self, hour=2, minute=0, days_of_week=None, backup_type='full', tables=None):
        """Programar un respaldo automático"""
        if not self.scheduler:
            self.setup_scheduler()
        
        if days_of_week is None:
            days_of_week = [0, 1, 2, 3, 4, 5, 6]
        
        def scheduled_backup_job():
            app = self._get_app()
            if app:
                with app.app_context():
                    self.perform_backup(tables=tables)
        
        job_id = f'backup_{hour}_{minute}_{backup_type}_{datetime.now().timestamp()}'
        
        try:
            self.scheduler.add_job(
                func=scheduled_backup_job,
                trigger='cron',
                day_of_week=days_of_week,
                hour=hour,
                minute=minute,
                id=job_id,
                replace_existing=True
            )
            
            return {
                'success': True,
                'message': f'Respaldo programado para las {hour:02d}:{minute:02d}',
                'job_id': job_id
            }
        except Exception as e:
            logger.error(f"Error programando respaldo: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_scheduled_jobs(self):
        """Obtener todos los trabajos programados"""
        if not self.scheduler:
            return []
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'name': job.name,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def remove_scheduled_job(self, job_id):
        """Eliminar un trabajo programado"""
        if not self.scheduler:
            return False
        try:
            self.scheduler.remove_job(job_id)
            return True
        except:
            return False

# Instancia global
backup_service = BackupService()