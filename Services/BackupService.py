import os
import gzip
import shutil
from datetime import datetime
from config import db
from Models.Backup import Backup
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from sqlalchemy import text, inspect
import subprocess
import re
import traceback

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
    
    def init_app(self, app):
        self.app = app
        self.setup_scheduler()
    
    def setup_scheduler(self):
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            logger.info("Scheduler de respaldos iniciado")
    
    def create_backup_filename(self, custom_name=None, backup_type='full'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if custom_name:
            clean_name = custom_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{clean_name}_{timestamp}.sql"
        else:
            filename = f"backup_{backup_type}_{timestamp}.sql"
        
        return os.path.join(self.backup_dir, filename)
    
    def get_database_tables(self):
        with self.app.app_context():
            inspector = inspect(db.engine)
            return inspector.get_table_names()
    
    def get_table_columns(self, table_name):
        """Obtener las columnas actuales de una tabla"""
        with self.app.app_context():
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                return columns
            except Exception as e:
                logger.warning(f"No se pudo obtener columnas de {table_name}: {e}")
                return []
    
    def get_table_structure(self, table_name):
        with self.app.app_context():
            try:
                result = db.session.execute(
                    text(f"SHOW CREATE TABLE `{table_name}`")
                ).fetchone()
                
                if result and len(result) >= 2:
                    return result[1] + ";\n\n"
            except Exception as e:
                logger.warning(f"No se pudo obtener estructura de {table_name}: {str(e)}")
            return ""
    
    def get_table_data(self, table_name):
        with self.app.app_context():
            try:
                result = db.session.execute(text(f"SELECT * FROM `{table_name}`"))
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
                            import json
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
    
    def perform_backup(self, tables=None, custom_name=None):
        try:
            logger.info(f"🎯 Iniciando creación de respaldo...")
            
            backup_type = 'partial' if tables else 'full'
            filepath = self.create_backup_filename(custom_name, backup_type)
            
            if not tables:
                tables_to_backup = self.get_database_tables()
                logger.info(f"📦 Respaldo COMPLETO de {len(tables_to_backup)} tablas")
            else:
                tables_to_backup = tables
                logger.info(f"📦 Respaldo PARCIAL de {len(tables_to_backup)} tablas")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"-- Backup generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Tipo: {backup_type.upper()}\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                
                for i, table_name in enumerate(tables_to_backup, 1):
                    try:
                        logger.info(f"📊 Procesando tabla {i}/{len(tables_to_backup)}: {table_name}")
                        
                        f.write(f"-- Estructura de la tabla: {table_name}\n")
                        create_statement = self.get_table_structure(table_name)
                        if create_statement:
                            f.write(create_statement)
                        
                        f.write(f"-- Datos de la tabla: {table_name}\n")
                        insert_statements = self.get_table_data(table_name)
                        f.write(insert_statements)
                        
                        f.write(f"-- Fin de datos para tabla: {table_name}\n\n")
                        
                    except Exception as e:
                        logger.error(f"❌ Error procesando tabla {table_name}: {str(e)}")
                        f.write(f"-- ERROR procesando tabla {table_name}: {str(e)}\n\n")
                
                f.write("SET FOREIGN_KEY_CHECKS=1;\n")
            
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"📏 Tamaño: {size_mb:.2f} MB")
            
            compressed_path = self.compress_backup(filepath)
            if compressed_path:
                filepath = compressed_path
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            backup_data = {
                'filename': os.path.basename(filepath),
                'filepath': os.path.abspath(filepath),
                'size_mb': round(size_mb, 2),
                'tables_included': tables_to_backup,
                'backup_type': backup_type,
                'status': 'completed'
            }
            
            backup_id = Backup.create_backup_record(backup_data)
            logger.info(f"✅ Registro creado ID: {backup_id}")
            
            return {
                'success': True,
                'message': f'Respaldo {backup_type} creado exitosamente',
                'backup_id': backup_id,
                'filename': backup_data['filename']
            }
            
        except Exception as e:
            logger.error(f"💥 Error: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': f'Error al crear respaldo: {str(e)}'}
    
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
        RESTAURACIÓN CORREGIDA - ADAPTATIVA A LA ESTRUCTURA ACTUAL
        """
        try:
            logger.info(f"🔄 Iniciando restauración ID: {backup_id}")
            
            # 1. Obtener respaldo
            backup = Backup.find_by_id(backup_id)
            if not backup:
                return {'success': False, 'message': 'Respaldo no encontrado'}
            
            if not os.path.exists(backup.filepath):
                return {'success': False, 'message': 'Archivo no encontrado'}
            
            logger.info(f"📄 Respaldo encontrado: {backup.filename}")
            
            # 2. Obtener configuración de BD
            db_uri = os.getenv('DATABASE_URL')
            if not db_uri:
                with self.app.app_context():
                    db_uri = current_app.config.get('DATABASE_URL')
            
            if not db_uri:
                logger.error("❌ No se encontró DATABASE_URL")
                return {'success': False, 'message': 'Error: No se encontró DATABASE_URL'}
            
            # 3. Extraer credenciales
            match = re.search(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):?(\d*)/(.+)', db_uri)
            
            if not match:
                logger.error(f"❌ No se pudo parsear DATABASE_URL")
                return {'success': False, 'message': 'Error parseando DATABASE_URL'}
            
            username = match.group(1)
            password = match.group(2)
            host = match.group(3)
            port = match.group(4) or '3306'
            database = match.group(5)
            
            logger.info(f"✅ Conectando a: {username}@{host}:{port}/{database}")
            
            # 4. PREPARAR ARCHIVO
            file_to_restore = backup.filepath
            
            # Si es .gz, descomprimimos
            if backup.filepath.endswith('.gz'):
                logger.info("📦 Descomprimiendo archivo...")
                decompressed_path = backup.filepath.replace('.gz', '')
                
                try:
                    with gzip.open(backup.filepath, 'rb') as f_in:
                        with open(decompressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    file_to_restore = decompressed_path
                    logger.info(f"✅ Archivo descomprimido en: {decompressed_path}")
                except Exception as e:
                    logger.error(f"Error descomprimiendo: {e}")
                    return {'success': False, 'message': f'Error descomprimiendo: {str(e)}'}
            
            # 5. OBTENER ESTRUCTURA ACTUAL DE LA BD
            with self.app.app_context():
                # Obtener columnas actuales de users
                current_user_columns = self.get_table_columns('users')
                logger.info(f"📊 Columnas actuales en users: {current_user_columns}")
                
                # Verificar qué columnas existen
                has_email = 'email' in current_user_columns
                has_username = 'username' in current_user_columns
                
                logger.info(f"   - Tiene email: {has_email}")
                logger.info(f"   - Tiene username: {has_username}")
            
            # 6. BUSCAR MYSQL.EXE
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
                    logger.info(f"✅ MySQL encontrado en: {mysql_exe}")
                    break
            
            if not mysql_exe:
                import shutil as shutil_path
                mysql_exe = shutil_path.which('mysql')
                if mysql_exe:
                    logger.info(f"✅ MySQL encontrado en PATH: {mysql_exe}")
                else:
                    logger.error("❌ No se encontró mysql.exe")
                    return {'success': False, 'message': 'No se encontró mysql.exe'}
            
            # 7. CONTAR REGISTROS ANTES
            try:
                with self.app.app_context():
                    before_users = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
                    logger.info(f"📊 Usuarios ANTES: {before_users}")
                    
                    current_version = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar()
                    logger.info(f"📊 Versión migración ANTES: {current_version}")
            except Exception as e:
                logger.warning(f"No se pudo contar usuarios antes: {e}")
                before_users = 0
                current_version = None
            
            # 8. CREAR ARCHIVO SQL CORREGIDO
            logger.info("📝 Preparando archivo SQL para restauración...")
            
            modified_file = file_to_restore + '_modified.sql'
            data_only_file = file_to_restore + '_data_only.sql'
            
            with open(file_to_restore, 'r', encoding='utf-8', errors='ignore') as f_in:
                lines = f_in.readlines()
            
            # Separar estructura de datos
            structure_lines = []
            data_lines = []
            in_data_section = False
            
            for line in lines:
                if line.strip().startswith('-- Datos de la tabla:'):
                    in_data_section = True
                    data_lines.append(line)
                elif line.strip().startswith('-- Estructura de la tabla:'):
                    in_data_section = False
                    structure_lines.append(line)
                elif in_data_section:
                    data_lines.append(line)
                else:
                    structure_lines.append(line)
            
            # 9. CORREGIR JSON EN notificaciones
            logger.info("🔧 Corrigiendo datos JSON...")
            fixed_data_lines = []
            
            for line in data_lines:
                if 'notificaciones' in line and 'datos_adicionales' in line:
                    # Corregir JSON mal formado
                    line = re.sub(r"'([^']*)'", lambda m: "'" + m.group(1).replace('"', '\\"') + "'", line)
                fixed_data_lines.append(line)
            
            # 10. CREAR ARCHIVO SOLO CON DATOS (SIN ESTRUCTURA)
            with open(data_only_file, 'w', encoding='utf-8') as f_out:
                f_out.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
                
                # Solo escribir datos, no estructura
                in_data = False
                for line in fixed_data_lines:
                    if line.strip().startswith('-- Datos de la tabla:'):
                        in_data = True
                        f_out.write(line)
                    elif line.strip().startswith('-- Estructura de la tabla:'):
                        in_data = False
                    elif in_data:
                        # Modificar INSERTS
                        if line.strip().upper().startswith('INSERT INTO'):
                            if 'alembic_version' in line:
                                # Para alembic_version, IGNORE
                                modified_line = line.replace('INSERT INTO', 'INSERT IGNORE INTO')
                                f_out.write(modified_line)
                            elif 'users' in line and not has_email:
                                # Para users sin email, adaptar
                                logger.warning("⚠️ Adaptando INSERT de users (sin columna email)")
                                # Simplificar: solo insertar lo que existe
                                modified_line = line.replace('INSERT INTO', 'REPLACE INTO')
                                f_out.write(modified_line)
                            else:
                                modified_line = line.replace('INSERT INTO', 'REPLACE INTO')
                                f_out.write(modified_line)
                        else:
                            f_out.write(line)
                
                f_out.write("SET FOREIGN_KEY_CHECKS=1;\n")
            
            logger.info(f"✅ Archivo de datos creado: {data_only_file}")
            
            # 11. EJECUTAR RESTAURACIÓN SOLO DATOS
            logger.info(f"🚀 Ejecutando restauración de datos...")
            
            cmd = [
                'cmd', '/c', 
                f'"{mysql_exe}"',
                f'--host={host}',
                f'--port={port}',
                f'--user={username}',
                f'--password={password}',
                '--default-character-set=utf8mb4',
                '--force',
                database,
                '<',
                f'"{data_only_file}"'
            ]
            
            cmd_str = ' '.join(cmd)
            
            try:
                process = subprocess.run(
                    cmd_str,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if process.returncode != 0:
                    logger.warning(f"⚠️ MySQL terminó con código {process.returncode}")
                
                if process.stderr:
                    # Filtrar warnings
                    filtered_stderr = '\n'.join([
                        line for line in process.stderr.split('\n')
                        if 'Warning' not in line and 'Using a password' not in line
                    ])
                    if filtered_stderr.strip():
                        logger.warning(f"⚠️ Errores/advertencias: {filtered_stderr[:500]}")
                
                # 12. CONTAR REGISTROS DESPUÉS
                with self.app.app_context():
                    after_users = db.session.execute(text("SELECT COUNT(*) FROM users")).scalar()
                    logger.info(f"📊 Usuarios DESPUÉS: {after_users}")
                    
                    users_added = after_users - before_users
                    
                    after_version = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar()
                    logger.info(f"📊 Versión migración DESPUÉS: {after_version}")
                    
                    if users_added > 0:
                        logger.info(f"✅ Usuarios insertados: {users_added}")
                        
                        # Consulta adaptativa
                        if has_email and has_username:
                            query = "SELECT id, email, username FROM users ORDER BY id DESC LIMIT 5"
                        elif has_username:
                            query = "SELECT id, username FROM users ORDER BY id DESC LIMIT 5"
                        else:
                            query = "SELECT id FROM users ORDER BY id DESC LIMIT 5"
                        
                        try:
                            new_users = db.session.execute(text(query)).fetchall()
                            for user in new_users:
                                logger.info(f"   - {dict(user)}")
                        except Exception as e:
                            logger.warning(f"No se pudieron mostrar usuarios: {e}")
                
                # 13. LIMPIAR
                try:
                    os.remove(modified_file)
                    os.remove(data_only_file)
                except:
                    pass
                
                return {
                    'success': True,
                    'message': f'Restauración completada. Usuarios insertados: {users_added}',
                    'users_before': before_users,
                    'users_after': after_users,
                    'users_added': users_added,
                    'migration_version': after_version
                }
                    
            except subprocess.TimeoutExpired:
                logger.error("⏰ Timeout en restauración")
                return {'success': False, 'message': 'Timeout en restauración'}
            except Exception as e:
                logger.error(f"💥 Error ejecutando mysql: {e}")
                logger.error(traceback.format_exc())
                return {'success': False, 'message': f'Error: {str(e)}'}
            
        except Exception as e:
            logger.error(f"💥 ERROR FATAL: {e}")
            logger.error(traceback.format_exc())
            return {'success': False, 'message': f'Error en restauración: {str(e)}'}
    
    def cleanup_old_backups(self, keep_last=50):
        try:
            backups = Backup.get_all_backups()
            if len(backups) > keep_last:
                for backup in backups[keep_last:]:
                    try:
                        if os.path.exists(backup.filepath):
                            os.remove(backup.filepath)
                        db.session.delete(backup)
                    except:
                        pass
                db.session.commit()
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
    
    def schedule_automatic_backup(self, hour=2, minute=0, days_of_week=None, backup_type='full', tables=None):
        if not self.scheduler:
            self.setup_scheduler()
        
        if days_of_week is None:
            days_of_week = [0, 1, 2, 3, 4, 5, 6]
        
        def scheduled_backup_job():
            with self.app.app_context():
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
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_scheduled_jobs(self):
        if not self.scheduler:
            return []
        return [{'id': job.id, 'next_run_time': str(job.next_run_time)} for job in self.scheduler.get_jobs()]
    
    def remove_scheduled_job(self, job_id):
        if not self.scheduler:
            return False
        try:
            self.scheduler.remove_job(job_id)
            return True
        except:
            return False

backup_service = BackupService()