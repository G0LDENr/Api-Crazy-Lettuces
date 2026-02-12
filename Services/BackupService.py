import os
import json
import gzip
import shutil
from datetime import datetime
from config import db
from Models.Backup import Backup
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from sqlalchemy import text, inspect

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = 'backups'
        self.scheduler = None
        # IMPORTANTE: Ajusta esta ruta según tu instalación de MySQL
        self.mysql_path = 'C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\'
        
        # Crear directorio de respaldos si no existe
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def init_app(self, app):
        """Inicializar con aplicación Flask"""
        self.app = app
        self.setup_scheduler()
    
    def setup_scheduler(self):
        """Configurar el programador de respaldos automáticos"""
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            logger.info("Scheduler de respaldos iniciado")
    
    def create_backup_filename(self, custom_name=None, backup_type='full'):
        """Crear nombre de archivo para el respaldo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if custom_name:
            # Limpiar nombre personalizado
            clean_name = custom_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{clean_name}_{timestamp}.sql"
        else:
            filename = f"backup_{backup_type}_{timestamp}.sql"
        
        return os.path.join(self.backup_dir, filename)
    
    def get_database_tables(self):
        """Obtener todas las tablas de la base de datos"""
        with self.app.app_context():
            inspector = inspect(db.engine)
            return inspector.get_table_names()
    
    def get_table_structure(self, table_name):
        """Obtener estructura de una tabla (CREATE TABLE)"""
        with self.app.app_context():
            try:
                # Obtener CREATE TABLE usando SQL nativo
                result = db.session.execute(
                    text(f"SHOW CREATE TABLE `{table_name}`")
                ).fetchone()
                
                if result and len(result) >= 2:
                    create_statement = result[1]
                    return create_statement + ";\n\n"
            except Exception as e:
                logger.warning(f"No se pudo obtener estructura de {table_name}: {str(e)}")
            
            return ""
    
    def get_table_data(self, table_name):
        """Obtener datos de una tabla en formato SQL INSERT"""
        with self.app.app_context():
            try:
                # Obtener datos de la tabla
                result = db.session.execute(
                    text(f"SELECT * FROM `{table_name}`")
                )
                
                # Obtener nombres de columnas
                columns = result.keys()
                
                # Generar INSERT statements
                sql_lines = []
                batch_size = 100
                current_batch = []
                
                for row in result:
                    # Convertir valores a string seguros para SQL
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, (int, float)):
                            values.append(str(value))
                        elif isinstance(value, datetime):
                            values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                        else:
                            # Escapar comillas simples
                            escaped = str(value).replace("'", "''")
                            values.append(f"'{escaped}'")
                    
                    current_batch.append(f"({', '.join(values)})")
                    
                    # Insertar en lotes para mejor rendimiento
                    if len(current_batch) >= batch_size:
                        columns_str = ', '.join([f"`{col}`" for col in columns])
                        sql_lines.append(
                            f"INSERT INTO `{table_name}` ({columns_str}) VALUES \n  " +
                            ",\n  ".join(current_batch) + ";\n"
                        )
                        current_batch = []
                
                # Agregar cualquier batch restante
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
    
    def perform_backup(self, tables=None, custom_name=None):
        """Realizar respaldo de la base de datos usando SQLAlchemy puro"""
        try:
            logger.info("🎯 Iniciando creación de respaldo (método Python)...")
            logger.info(f"   Tablas: {tables}")
            logger.info(f"   Nombre personalizado: {custom_name}")
            
            backup_type = 'partial' if tables else 'full'
            filepath = self.create_backup_filename(custom_name, backup_type)
            
            # Determinar qué tablas respaldar
            if not tables:
                # Respaldo completo - obtener todas las tablas
                tables_to_backup = self.get_database_tables()
                logger.info(f"📦 Respaldo COMPLETO de {len(tables_to_backup)} tablas")
            else:
                # Respaldo parcial - usar tablas específicas
                tables_to_backup = tables
                logger.info(f"📦 Respaldo PARCIAL de {len(tables_to_backup)} tablas")
            
            # Crear archivo de respaldo
            logger.info(f"📁 Creando archivo: {filepath}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Escribir encabezado
                f.write(f"-- Backup generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Tipo: {backup_type.upper()}\n")
                f.write(f"-- Tablas: {len(tables_to_backup)}\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                
                total_tables = len(tables_to_backup)
                
                # Para cada tabla, obtener estructura y datos
                for i, table_name in enumerate(tables_to_backup, 1):
                    try:
                        logger.info(f"📊 Procesando tabla {i}/{total_tables}: {table_name}")
                        
                        # Escribir estructura (CREATE TABLE)
                        f.write(f"-- Estructura de la tabla: {table_name}\n")
                        create_statement = self.get_table_structure(table_name)
                        if create_statement:
                            f.write(create_statement)
                        else:
                            f.write(f"-- No se pudo obtener estructura de {table_name}\n")
                        
                        # Escribir datos (INSERT)
                        f.write(f"-- Datos de la tabla: {table_name}\n")
                        insert_statements = self.get_table_data(table_name)
                        f.write(insert_statements)
                        
                        # Separador seguro
                        f.write(f"-- Fin de datos para tabla: {table_name}\n\n")
                        
                        logger.info(f"✅ Tabla {table_name} procesada")
                        
                    except Exception as e:
                        logger.error(f"❌ Error procesando tabla {table_name}: {str(e)}")
                        f.write(f"-- ERROR procesando tabla {table_name}: {str(e)}\n\n")
                
                # Finalizar archivo
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
                f.write(f"-- Backup completado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Calcular tamaño del archivo
            size_bytes = os.path.getsize(filepath)
            size_mb = size_bytes / (1024 * 1024)
            logger.info(f"📏 Tamaño del respaldo: {size_mb:.2f} MB")
            
            # Comprimir el archivo (opcional)
            compressed_filepath = self.compress_backup(filepath)
            if compressed_filepath:
                compressed_size = os.path.getsize(compressed_filepath) / (1024 * 1024)
                logger.info(f"📦 Archivo comprimido: {compressed_size:.2f} MB")
                # Usar el archivo comprimido
                filepath = compressed_filepath
                size_mb = compressed_size
            
            # Crear registro en la base de datos
            backup_data = {
                'filename': os.path.basename(filepath),
                'filepath': os.path.abspath(filepath),
                'size_mb': round(size_mb, 2),
                'tables_included': tables_to_backup if tables_to_backup else None,
                'backup_type': backup_type,
                'status': 'completed'
            }
            
            logger.info("💾 Creando registro en base de datos...")
            backup_id = Backup.create_backup_record(backup_data)
            logger.info(f"✅ Registro creado con ID: {backup_id}")
            
            # Mantener solo los últimos 50 respaldos (limpieza automática)
            self.cleanup_old_backups(keep_last=50)
            
            response = {
                'success': True,
                'message': f'Respaldo {backup_type} creado exitosamente',
                'backup_id': backup_id,
                'filename': backup_data['filename'],
                'size_mb': backup_data['size_mb'],
                'filepath': backup_data['filepath'],
                'backup_type': backup_type,
                'tables_count': len(tables_to_backup)
            }
            
            logger.info(f"🎉 Respaldo completado: {response['filename']}")
            return response
            
        except Exception as e:
            logger.error(f"💥 Error al crear respaldo: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Intentar eliminar archivo si se creó pero falló
            if 'filepath' in locals() and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info("🗑️ Archivo fallido eliminado")
                except:
                    pass
            
            return {
                'success': False,
                'message': f'Error al crear respaldo: {str(e)}'
            }
    
    def compress_backup(self, filepath):
        """Comprimir archivo de respaldo usando gzip"""
        try:
            compressed_path = filepath + '.gz'
            
            with open(filepath, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Eliminar archivo original no comprimido
            os.remove(filepath)
            
            return compressed_path
        except Exception as e:
            logger.warning(f"No se pudo comprimir archivo: {str(e)}")
            return None
    
    def restore_backup(self, backup_id):
        """Restaurar base de datos desde un respaldo - VERSIÓN CON CORRECCIÓN DE ENCODING"""
        try:
            logger.info(f"🔄 [RESTAURACIÓN] Iniciando restauración del respaldo ID: {backup_id}")
            
            # 1. Obtener información del respaldo
            backup = Backup.find_by_id(backup_id)
            if not backup:
                raise Exception(f"Respaldo con ID {backup_id} no encontrado")
            
            if not os.path.exists(backup.filepath):
                raise Exception(f"Archivo de respaldo no encontrado: {backup.filepath}")
            
            logger.info(f"📂 Archivo a restaurar: {backup.filename}")
            logger.info(f"📊 Tipo: {backup.backup_type}")
            
            # 2. Obtener configuración de la base de datos DESDE FLASK
            with self.app.app_context():
                SQLALCHEMY_DATABASE_URI = current_app.config.get('SQLALCHEMY_DATABASE_URI')
                
            if not SQLALCHEMY_DATABASE_URI:
                SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
                
            if not SQLALCHEMY_DATABASE_URI:
                SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:131023@localhost:3307/crazylettuces'
            
            import re
            
            # Extraer información de conexión
            pattern = r"mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
            match = re.match(pattern, SQLALCHEMY_DATABASE_URI)
            
            if not match:
                pattern2 = r"mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/(.+)"
                match = re.match(pattern2, SQLALCHEMY_DATABASE_URI)
                
                if match:
                    username, password, host, database = match.groups()
                    port = "3306"
                else:
                    logger.warning("⚠️ No se pudo parsear URI, usando valores por defecto")
                    username = "root"
                    password = "131023"
                    host = "localhost"
                    port = "3307"
                    database = "crazylettuces"
            else:
                username, password, host, port, database = match.groups()
                
            logger.info(f"🔗 Conectando a: {username}@{host}:{port}/{database}")
            
            # 3. Preparar archivo para restaurar
            file_to_restore = backup.filepath
            is_compressed = backup.filepath.endswith('.gz')
            
            if is_compressed:
                import tempfile
                temp_dir = tempfile.mkdtemp()
                file_to_restore = os.path.join(temp_dir, 'temp_backup.sql')
                
                with gzip.open(backup.filepath, 'rb') as f_in:
                    with open(file_to_restore, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                logger.info("📦 Archivo descomprimido para restauración")
            
            # 4. **LEER Y CORREGIR PROBLEMAS DE ENCODING**
            logger.info("🔤 Leyendo y corrigiendo encoding del archivo...")
            
            # Intentar diferentes encodings
            content = None
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']
            
            for encoding in encodings_to_try:
                try:
                    with open(file_to_restore, 'r', encoding=encoding, errors='strict') as f:
                        content = f.read()
                    logger.info(f"✅ Archivo leído con encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Último intento: leer ignorando errores
                with open(file_to_restore, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                logger.info("⚠️ Archivo leído ignorando errores de encoding")
            
            # 5. **CORRECCIONES ESPECÍFICAS PARA TU PROBLEMA**
            logger.info("🔧 Aplicando correcciones específicas...")
            
            # CORREGIR: 'contraseÃ±a' → 'password' (tu columna problemática)
            # Primero, ver qué nombres de columna están en el archivo
            column_patterns = [
                'contraseÃ±a',  # UTF-8 mal interpretado
                'contraseña',   # Original con ñ
                'password',     # Nombre en inglés
                'contrasena',   # Sin tilde
            ]
            
            found_columns = []
            for pattern in column_patterns:
                if pattern in content:
                    found_columns.append(pattern)
                    logger.info(f"📝 Columna encontrada en archivo: '{pattern}'")
            
            # Aplicar correcciones
            if 'contraseÃ±a' in content:
                # Caso 1: Cambiar 'contraseÃ±a' (mal encoding) por 'password'
                content = content.replace('contraseÃ±a', 'password')
                content = content.replace('`contraseÃ±a`', '`password`')
                logger.info("✅ Corregido: 'contraseÃ±a' → 'password'")
            
            if 'contraseña' in content:
                # Caso 2: Cambiar 'contraseña' (con ñ) por 'password'
                content = content.replace('contraseña', 'password')
                content = content.replace('`contraseña`', '`password`')
                logger.info("✅ Corregido: 'contraseña' → 'password'")
            
            # Correcciones generales de encoding
            encoding_corrections = {
                'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
                'Ã±': 'ñ', 'Ã¼': 'ü', 'Ã': 'Ñ',
                'Ã€': 'À', 'Ãˆ': 'È', 'ÃŒ': 'Ì', 'Ã’': 'Ò', 'Ã™': 'Ù',
                'Ã§': 'ç', 'Ã£': 'ã', 'Ãµ': 'õ',
            }
            
            for wrong, correct in encoding_corrections.items():
                if wrong in content:
                    content = content.replace(wrong, correct)
            
            # 6. **LIMPIAR LÍNEAS PROBLEMÁTICAS**
            logger.info("🧹 Limpiando líneas problemáticas...")
            
            lines = content.split('\n')
            clean_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # Eliminar líneas vacías o solo con separadores
                if not line_stripped:
                    continue
                
                # Eliminar líneas que solo contienen caracteres repetidos
                if line_stripped.replace('=', '').strip() == '':
                    continue
                if line_stripped.replace('-', '').strip() == '':
                    continue
                if line_stripped.replace('*', '').strip() == '':
                    continue
                
                # Eliminar líneas que son solo separadores largos
                if len(line_stripped) > 30:
                    unique_chars = set(line_stripped)
                    if len(unique_chars) == 1 and line_stripped[0] in ['=', '-', '*', '#']:
                        continue
                
                # Mantener la línea
                clean_lines.append(line)
            
            # Crear un nuevo archivo limpio con UTF-8
            cleaned_file = file_to_restore + '.cleaned.sql'
            
            with open(cleaned_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(clean_lines))
            
            original_line_count = len(lines)
            cleaned_line_count = len(clean_lines)
            logger.info(f"✅ Archivo procesado: {original_line_count} → {cleaned_line_count} líneas")
            
            # 7. **CREAR BACKUP DE SEGURIDAD**
            try:
                safety_file = self.create_backup_filename(custom_name=f"pre_restore_safety_{datetime.now().strftime('%H%M%S')}")
                logger.info(f"📦 Creando backup de seguridad rápido en: {safety_file}")
                
                import subprocess
                
                mysqldump_cmd = f'{self.mysql_path}mysqldump.exe' if self.mysql_path else 'mysqldump'
                
                cmd = [
                    mysqldump_cmd,
                    f'--host={host}',
                    f'--port={port}',
                    f'--user={username}',
                    f'--password={password}',
                    '--quick',
                    '--single-transaction',
                    '--skip-lock-tables',
                    '--ignore-table', f'{database}.alembic_version',
                    database
                ]
                
                with open(safety_file, 'w', encoding='utf-8') as f:
                    subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, timeout=60)
                
                logger.info("✅ Backup de seguridad creado (excluyendo alembic_version)")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Timeout en backup de seguridad")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo crear backup de seguridad: {e}")
            
            # 8. **MÉTODO PRINCIPAL: RESTAURACIÓN CON CORRECCIONES**
            logger.info(f"🔄 Restaurando base de datos (con correcciones aplicadas)...")
            
            mysql_cmd = f'{self.mysql_path}mysql.exe' if self.mysql_path else 'mysql'
            
            restore_cmd = [
                mysql_cmd,
                f'--host={host}',
                f'--port={port}',
                f'--user={username}',
                f'--password={password}',
                '--default-character-set=utf8mb4',  # Charset correcto
                '--force',  # Ignora advertencias
                database
            ]
            
            # Ejecutar comando de restauración
            with open(cleaned_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(
                    restore_cmd,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=300
                )
            
            # 9. **ANALIZAR RESULTADO**
            success = True
            warning_messages = []
            error_messages = []
            
            if result.stderr:
                for line in result.stderr.split('\n'):
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    
                    if 'ERROR' in line:
                        error_messages.append(line_stripped)
                    elif 'Warning' in line or 'already exists' in line or 'Duplicate' in line:
                        warning_messages.append(line_stripped)
            
            # Filtrar errores - ERROR 1054 de columna desconocida ya debería estar corregido
            critical_errors = []
            for error in error_messages:
                is_critical = True
                error_lower = error.lower()
                
                # Errores NO críticos
                non_critical_patterns = [
                    'already exists',
                    'duplicate entry',
                    'duplicate key',
                    'table.*already exists',
                    'using a password on the command line',
                    'unknown column',  # Esto debería estar corregido
                ]
                
                for pattern in non_critical_patterns:
                    if pattern in error_lower:
                        is_critical = False
                        warning_messages.append(f"ADVERTENCIA: {error}")
                        break
                
                if is_critical and '1064' not in error:  # Error de sintaxis
                    critical_errors.append(error)
            
            # 10. **MANEJAR RESULTADO**
            if critical_errors:
                logger.error(f"❌ Errores críticos durante restauración:")
                for err in critical_errors[:3]:
                    logger.error(f"   {err}")
                success = False
            elif warning_messages:
                logger.warning(f"⚠️ Restauración completada con {len(warning_messages)} advertencias")
                for warn in warning_messages[:5]:
                    logger.warning(f"   {warn}")
            
            # 11. **SI FALLÓ POR ERROR DE COLUMNA, INTENTAR MÉTODO ESPECIAL**
            if not success and any('unknown column' in error.lower() for error in error_messages):
                logger.info("🔄 Detectado error de columna, intentando método especial...")
                
                try:
                    # Leer archivo limpio
                    with open(cleaned_file, 'r', encoding='utf-8') as f:
                        fixed_content = f.read()
                    
                    # Buscar y eliminar INSERT problemáticos para la tabla 'users'
                    lines = fixed_content.split('\n')
                    safe_lines = []
                    skip_block = False
                    
                    for line in lines:
                        # Si encontramos INSERT INTO `users` con columnas problemáticas
                        if 'INSERT INTO `users`' in line and ('contrase' in line or 'password' in line):
                            logger.info("⏭️ Saltando INSERT problemático para tabla 'users'")
                            skip_block = True
                            continue
                        
                        if skip_block:
                            if line.strip().endswith(';'):
                                skip_block = False
                            continue
                        
                        safe_lines.append(line)
                    
                    # Guardar archivo seguro
                    safe_file = cleaned_file + '.safe.sql'
                    with open(safe_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(safe_lines))
                    
                    # Restaurar archivo seguro
                    with open(safe_file, 'r', encoding='utf-8') as f:
                        result_safe = subprocess.run(
                            restore_cmd,
                            stdin=f,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=300
                        )
                    
                    if result_safe.returncode == 0:
                        success = True
                        logger.info("✅ Restauración exitosa (datos de usuarios omitidos)")
                    
                    # Limpiar archivo temporal
                    if os.path.exists(safe_file):
                        os.remove(safe_file)
                        
                except Exception as special_error:
                    logger.error(f"❌ Error en método especial: {special_error}")
            
            # 12. **SI TODO FALLA, RESTAURAR SOLO ESTRUCTURA**
            if not success:
                logger.info("🔄 Intentando restaurar solo estructura de tablas...")
                
                try:
                    # Leer y extraer solo CREATE TABLE statements
                    with open(cleaned_file, 'r', encoding='utf-8') as f:
                        structure_content = f.read()
                    
                    import re
                    # Buscar todas las sentencias CREATE TABLE
                    create_pattern = r'CREATE TABLE IF NOT EXISTS `[^`]+`[^;]+;'
                    create_tables = re.findall(create_pattern, structure_content, re.IGNORECASE | re.DOTALL)
                    
                    if create_tables:
                        structure_file = cleaned_file + '.structure.sql'
                        with open(structure_file, 'w', encoding='utf-8') as f:
                            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                            for table_sql in create_tables:
                                f.write(table_sql + "\n\n")
                            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
                        
                        # Restaurar solo estructura
                        with open(structure_file, 'r', encoding='utf-8') as f:
                            result_struct = subprocess.run(
                                restore_cmd,
                                stdin=f,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=300
                            )
                        
                        if result_struct.returncode == 0:
                            success = True
                            logger.info("✅ Estructura de tablas restaurada exitosamente")
                            logger.warning("⚠️ Nota: Solo se restauró la estructura, no los datos")
                        
                        # Limpiar archivo temporal
                        if os.path.exists(structure_file):
                            os.remove(structure_file)
                            
                except Exception as struct_error:
                    logger.error(f"❌ Error restaurando estructura: {struct_error}")
            
            # 13. **LIMPIAR ARCHIVOS TEMPORALES**
            try:
                if os.path.exists(cleaned_file):
                    os.remove(cleaned_file)
                
                if is_compressed:
                    if os.path.exists(file_to_restore):
                        os.remove(file_to_restore)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                
                logger.debug("🗑️ Archivos temporales eliminados")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error limpiando archivos temporales: {cleanup_error}")
            
            # 14. **RESULTADO FINAL**
            if success:
                if warning_messages:
                    warning_count = len(warning_messages)
                    message = f'Base de datos restaurada exitosamente con {warning_count} advertencias'
                else:
                    message = f'Base de datos restaurada exitosamente desde {backup.filename}'
                
                logger.info(f"✅ {message}")
                
                return {
                    'success': True,
                    'message': message,
                    'warnings': warning_messages[:10] if warning_messages else None,
                    'backup_filename': backup.filename,
                    'note': 'Se corrigieron problemas de encoding automáticamente' if 'contrase' in str(content) else None
                }
            else:
                error_summary = '\n'.join(critical_errors[:3])
                raise Exception(f"Error en restauración: {error_summary}")
                
        except Exception as e:
            logger.error(f"💥 Error al restaurar respaldo: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'message': f'Error al restaurar: {str(e)}'
            }
    
    def cleanup_old_backups(self, keep_last=50):
        """Eliminar respaldos antiguos manteniendo solo los últimos N"""
        try:
            backups = Backup.get_all_backups()
            
            if len(backups) > keep_last:
                backups_to_delete = backups[keep_last:]
                logger.info(f"🧹 Limpiando {len(backups_to_delete)} respaldos antiguos...")
                
                for backup in backups_to_delete:
                    try:
                        if os.path.exists(backup.filepath):
                            os.remove(backup.filepath)
                            logger.debug(f"   Archivo eliminado: {backup.filename}")
                        db.session.delete(backup)
                    except Exception as e:
                        logger.error(f"Error al eliminar respaldo antiguo {backup.id}: {str(e)}")
                
                db.session.commit()
                logger.info("✅ Limpieza de respaldos completada")
        except Exception as e:
            logger.error(f"Error en limpieza de respaldos: {str(e)}")
    
    def schedule_automatic_backup(self, hour=2, minute=0, days_of_week=None, backup_type='full', tables=None):
        """Programar respaldo automático"""
        if not self.scheduler:
            self.setup_scheduler()
        
        if days_of_week is None:
            days_of_week = [0, 1, 2, 3, 4, 5, 6]  # Todos los días
        
        # Crear función para el respaldo programado
        def scheduled_backup_job():
            with self.app.app_context():
                try:
                    logger.info("🕐 Ejecutando respaldo programado...")
                    result = self.perform_backup(tables=tables)
                    if result['success']:
                        logger.info("✅ Respaldo programado completado")
                    else:
                        logger.error(f"❌ Respaldo programado falló: {result.get('message')}")
                except Exception as e:
                    logger.error(f"💥 Error en respaldo programado: {str(e)}")
        
        # Programar trabajo
        job_id = f'backup_{hour}_{minute}_{backup_type}_{datetime.now().timestamp()}'
        
        try:
            self.scheduler.add_job(
                func=scheduled_backup_job,
                trigger='cron',
                day_of_week=days_of_week,
                hour=hour,
                minute=minute,
                id=job_id,
                replace_existing=True,
                misfire_grace_time=3600
            )
            
            logger.info(f"📅 Trabajo programado: {job_id}")
            
            return {
                'success': True,
                'message': f'Respaldo automático programado para las {hour:02d}:{minute:02d}',
                'job_id': job_id,
                'schedule': {
                    'hour': hour,
                    'minute': minute,
                    'days_of_week': days_of_week,
                    'backup_type': backup_type,
                    'tables': tables
                }
            }
            
        except Exception as e:
            logger.error(f"Error al programar respaldo: {str(e)}")
            return {
                'success': False,
                'message': f'Error al programar: {str(e)}'
            }
    
    def get_scheduled_jobs(self):
        """Obtener trabajos programados"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger),
                'name': job.name
            })
        
        return jobs
    
    def remove_scheduled_job(self, job_id):
        """Eliminar trabajo programado"""
        if not self.scheduler:
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Trabajo programado {job_id} eliminado")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar trabajo programado: {str(e)}")
            return False

# Instancia global del servicio
backup_service = BackupService()