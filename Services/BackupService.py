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
                        
                        f.write("\n" + "="*80 + "\n\n")
                        
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
        """Restaurar base de datos desde un respaldo"""
        try:
            logger.info(f"🔄 Iniciando restauración del respaldo ID: {backup_id}")
            
            backup = Backup.find_by_id(backup_id)
            if not backup:
                raise Exception(f"Respaldo con ID {backup_id} no encontrado")
            
            if not os.path.exists(backup.filepath):
                raise Exception(f"Archivo de respaldo no encontrado: {backup.filepath}")
            
            logger.info(f"📂 Archivo a restaurar: {backup.filename}")
            
            # Determinar si está comprimido
            file_to_restore = backup.filepath
            if backup.filepath.endswith('.gz'):
                # Descomprimir temporalmente
                import tempfile
                temp_dir = tempfile.mkdtemp()
                file_to_restore = os.path.join(temp_dir, 'temp_backup.sql')
                
                with gzip.open(backup.filepath, 'rb') as f_in:
                    with open(file_to_restore, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                logger.info("📦 Archivo descomprimido para restauración")
            
            # Leer y ejecutar el archivo SQL
            with open(file_to_restore, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Dividir en sentencias SQL (separadas por punto y coma)
            import re
            
            # Patrón para dividir sentencias SQL, ignorando punto y coma dentro de strings
            pattern = r'''((?:[^;"']|"[^"]*"|'[^']*')+)'''
            statements = re.split(pattern, sql_content)
            
            # Filtrar sentencias vacías y comentarios
            statements = [
                stmt.strip() for stmt in statements 
                if stmt.strip() and not stmt.strip().startswith('--')
            ]
            
            total_statements = len(statements)
            logger.info(f"🔨 Ejecutando {total_statements} sentencias SQL...")
            
            with self.app.app_context():
                # Desactivar verificaciones de clave foránea temporalmente
                db.session.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
                db.session.commit()
                
                executed = 0
                for i, statement in enumerate(statements, 1):
                    try:
                        if statement.strip() and not statement.strip().startswith('--'):
                            db.session.execute(text(statement))
                            executed += 1
                        
                        # Hacer commit cada 100 sentencias
                        if i % 100 == 0:
                            db.session.commit()
                            logger.info(f"  📊 Progreso: {i}/{total_statements} sentencias")
                    
                    except Exception as e:
                        logger.warning(f"  ⚠️ Error en sentencia {i}: {str(e)[:100]}...")
                        # Continuar con el siguiente
                
                # Reactivar verificaciones de clave foránea
                db.session.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
                db.session.commit()
            
            # Limpiar archivo temporal si se descomprimió
            if file_to_restore != backup.filepath:
                os.remove(file_to_restore)
                os.rmdir(os.path.dirname(file_to_restore))
            
            logger.info(f"✅ Base de datos restaurada exitosamente ({executed} sentencias ejecutadas)")
            
            return {
                'success': True,
                'message': f'Base de datos restaurada exitosamente ({executed} sentencias ejecutadas)'
            }
            
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