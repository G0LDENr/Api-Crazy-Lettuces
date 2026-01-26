from flask import jsonify, request, send_file
from flask_jwt_extended import jwt_required
from Models.Backup import Backup
from Services.BackupService import backup_service
import os
import json
from datetime import datetime
import shutil
import gzip
import re

def get_all_backups():
    """
    Obtener todos los respaldos
    """
    try:
        backups = Backup.get_all_backups()
        backups_list = [backup.to_dict() for backup in backups]
        return jsonify({
            'success': True,
            'backups': backups_list,
            'count': len(backups_list)
        }), 200
        
    except Exception as error:
        print(f"Error al obtener respaldos: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener los respaldos'
        }), 500

def get_single_backup(backup_id):
    """
    Obtener un respaldo por ID
    """
    try:
        backup = Backup.find_by_id(backup_id)
        if not backup:
            return jsonify({
                'success': False,
                'message': 'Respaldo no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'backup': backup.to_dict()
        }), 200
        
    except Exception as error:
        print(f"Error al obtener el respaldo: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener el respaldo'
        }), 500

def create_backup():
    """
    Crear nuevo respaldo
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron datos'
            }), 400
        
        tables = data.get('tables', None)
        custom_name = data.get('custom_name', None)
        
        # Validar si es respaldo parcial
        if tables and isinstance(tables, str):
            tables = [t.strip() for t in tables.split(',')]
        
        print(f"🎯 Creando respaldo - Tipo: {'Parcial' if tables else 'Completo'}")
        
        result = backup_service.perform_backup(tables=tables, custom_name=custom_name)
        
        if result['success']:
            print(f"✅ Respaldo creado exitosamente: {result.get('filename')}")
            return jsonify(result), 201
        else:
            print(f"❌ Error al crear respaldo: {result.get('message')}")
            return jsonify(result), 500
            
    except Exception as error:
        print(f"💥 Error completo al crear respaldo: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al crear el respaldo'
        }), 500

def upload_backup():
    """
    Subir/Importar un respaldo existente a la base de datos
    """
    try:
        print(f"📤 Iniciando importación de respaldo...")
        
        # Verificar si se envió archivo
        if 'backup_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó archivo de respaldo'
            }), 400
        
        backup_file = request.files['backup_file']
        
        # Verificar que se seleccionó un archivo
        if backup_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        # Verificar extensión
        allowed_extensions = {'.sql', '.sql.gz', '.gz', '.backup'}
        filename = backup_file.filename.lower()
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return jsonify({
                'success': False,
                'message': 'Formato de archivo no válido. Use .sql, .sql.gz o .gz'
            }), 400
        
        # Crear directorio de respaldos si no existe
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Limpiar nombre del archivo
        original_name = os.path.splitext(backup_file.filename)[0]
        # Remover extensión .gz si existe
        if original_name.endswith('.sql'):
            original_name = original_name[:-4]
        
        # Crear nombre seguro
        safe_name = ''.join(c for c in original_name if c.isalnum() or c in ['_', '-', ' '])
        safe_name = safe_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Mantener la extensión original
        if backup_file.filename.endswith('.sql.gz'):
            file_extension = '.sql.gz'
        elif backup_file.filename.endswith('.gz'):
            file_extension = '.gz'
        else:
            file_extension = '.sql'
        
        new_filename = f"imported_{timestamp}_{safe_name}{file_extension}"
        filepath = os.path.join(backup_dir, new_filename)
        
        # Guardar el archivo
        backup_file.save(filepath)
        print(f"💾 Archivo guardado en: {filepath}")
        
        # Calcular tamaño
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        
        # Determinar tipo de respaldo
        backup_type = 'full'
        tables_included = None
        
        # Intentar analizar el archivo para determinar tipo y tablas
        try:
            content = ""
            if filepath.endswith('.gz'):
                # Descomprimir para leer
                with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
                    content = f.read(20000)  # Leer primeros 20KB
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(20000)
            
            # Buscar indicios de tipo
            if '-- Tipo: PARTIAL' in content.upper() or 'partial' in content.upper():
                backup_type = 'partial'
            
            # Buscar tablas en el contenido
            # Patrones para encontrar nombres de tablas
            patterns = [
                r'CREATE TABLE `([^`]+)`',
                r'INSERT INTO `([^`]+)`',
                r'DROP TABLE IF EXISTS `([^`]+)`',
                r'-- Tabla: ([^\n]+)',
                r'-- Estructura de la tabla: ([^\n]+)'
            ]
            
            found_tables = set()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match and len(match.strip()) > 0:
                        found_tables.add(match.strip())
            
            if found_tables:
                tables_included = list(found_tables)
                if len(tables_included) < 5:  # Si tiene pocas tablas, probablemente es parcial
                    backup_type = 'partial'
                    
        except Exception as e:
            print(f"⚠️ No se pudo analizar archivo: {e}")
        
        print(f"📊 Respaldo importado: {new_filename}")
        print(f"   Tamaño: {size_mb:.2f} MB")
        print(f"   Tipo: {backup_type}")
        print(f"   Tablas detectadas: {len(tables_included) if tables_included else 0}")
        
        # Crear registro en base de datos
        backup_data = {
            'filename': new_filename,
            'filepath': os.path.abspath(filepath),
            'size_mb': round(size_mb, 2),
            'tables_included': json.dumps(tables_included) if tables_included else None,
            'backup_type': backup_type,
            'status': 'completed'
        }
        
        backup_id = Backup.create_backup_record(backup_data)
        
        return jsonify({
            'success': True,
            'message': 'Respaldo importado exitosamente',
            'backup_id': backup_id,
            'filename': new_filename,
            'size_mb': round(size_mb, 2),
            'backup_type': backup_type,
            'tables_included': tables_included,
            'filepath': filepath
        }), 201
        
    except Exception as error:
        print(f"💥 Error al importar respaldo: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al importar respaldo: {str(error)}'
        }), 500

def delete_backup(backup_id):
    """
    Eliminar un respaldo por ID
    """
    try:
        print(f"🔍 DEBUG - Solicitando eliminación del respaldo ID: {backup_id}")
        
        # Verificar si el respaldo existe
        existing_backup = Backup.find_by_id(backup_id)
        if not existing_backup:
            print(f"❌ Respaldo {backup_id} no encontrado")
            return jsonify({
                'success': False,
                'message': 'Respaldo no encontrado'
            }), 404
        
        print(f"🔍 Respaldo encontrado: {existing_backup.filename}")
        
        # Eliminar respaldo
        success = Backup.delete_backup(backup_id)
        
        if success:
            print(f"✅ Respaldo {backup_id} eliminado exitosamente")
            return jsonify({
                'success': True,
                'message': 'Respaldo eliminado exitosamente'
            }), 200
        else:
            print(f"❌ No se pudo eliminar el respaldo {backup_id}")
            return jsonify({
                'success': False,
                'message': 'Error al eliminar el respaldo'
            }), 500
            
    except Exception as error:
        print(f"💥 Error completo al eliminar respaldo: {error}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al eliminar respaldo'
        }), 500

def download_backup(backup_id):
    """
    Descargar archivo de respaldo
    """
    try:
        backup = Backup.find_by_id(backup_id)
        
        if not backup:
            return jsonify({
                'success': False,
                'message': 'Respaldo no encontrado'
            }), 404
        
        if not os.path.exists(backup.filepath):
            return jsonify({
                'success': False,
                'message': 'Archivo de respaldo no encontrado'
            }), 404
        
        print(f"📥 Descargando respaldo: {backup.filename}")
        
        # Determinar mimetype basado en extensión
        if backup.filepath.endswith('.gz'):
            mimetype = 'application/gzip'
            # Asegurar que el nombre tenga .gz
            if not backup.filename.endswith('.gz'):
                download_name = f"{backup.filename}.gz"
            else:
                download_name = backup.filename
        else:
            mimetype = 'application/sql'
            download_name = backup.filename
        
        return send_file(
            backup.filepath,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
        
    except Exception as error:
        print(f"💥 Error al descargar respaldo: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al descargar el respaldo'
        }), 500

def restore_backup(backup_id):
    """
    Restaurar base de datos desde respaldo
    """
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'success': False,
                'message': 'Se requiere confirmación para restaurar'
            }), 400
        
        print(f"🔄 Iniciando restauración del respaldo ID: {backup_id}")
        
        result = backup_service.restore_backup(backup_id)
        
        if result['success']:
            print(f"✅ Base de datos restaurada exitosamente")
            return jsonify(result), 200
        else:
            print(f"❌ Error en restauración: {result.get('message')}")
            return jsonify(result), 500
            
    except Exception as error:
        print(f"💥 Error al restaurar respaldo: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al restaurar el respaldo'
        }), 500

def schedule_backup():
    """
    Programar respaldo automático
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron datos'
            }), 400
        
        hour = data.get('hour', 2)
        minute = data.get('minute', 0)
        days_of_week = data.get('days_of_week', [0, 1, 2, 3, 4, 5, 6])
        backup_type = data.get('backup_type', 'full')
        tables = data.get('tables', None)
        
        if backup_type == 'partial' and not tables:
            return jsonify({
                'success': False,
                'message': 'Para respaldo parcial debe especificar tablas'
            }), 400
        
        print(f"📅 Programando respaldo automático para {hour}:{minute}")
        
        result = backup_service.schedule_automatic_backup(
            hour=hour,
            minute=minute,
            days_of_week=days_of_week,
            backup_type=backup_type,
            tables=tables
        )
        
        return jsonify(result), 200
        
    except Exception as error:
        print(f"💥 Error al programar respaldo: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al programar el respaldo automático'
        }), 500

def get_scheduled_backups():
    """
    Obtener respaldos programados
    """
    try:
        jobs = backup_service.get_scheduled_jobs()
        
        return jsonify({
            'success': True,
            'scheduled_jobs': jobs,
            'count': len(jobs)
        }), 200
        
    except Exception as error:
        print(f"Error al obtener respaldos programados: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener los respaldos programados'
        }), 500

def cancel_scheduled_backup(job_id):
    """
    Cancelar respaldo programado
    """
    try:
        success = backup_service.remove_scheduled_job(job_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Respaldo programado cancelado exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No se pudo cancelar el respaldo programado'
            }), 400
            
    except Exception as error:
        print(f"Error al cancelar respaldo programado: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al cancelar el respaldo programado'
        }), 500

def get_database_tables():
    """
    Obtener lista de tablas de la base de datos
    """
    try:
        from config import db
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        return jsonify({
            'success': True,
            'tables': tables,
            'count': len(tables)
        }), 200
        
    except Exception as error:
        print(f"Error al obtener tablas: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener las tablas de la base de datos'
        }), 500

def get_backup_stats():
    """
    Obtener estadísticas de respaldos
    """
    try:
        backups = Backup.get_all_backups()
        
        if not backups:
            return jsonify({
                'success': True,
                'stats': {
                    'total_backups': 0,
                    'total_size_mb': 0,
                    'full_backups': 0,
                    'partial_backups': 0,
                    'last_backup': None
                }
            }), 200
        
        total_size = sum(b.size_mb for b in backups)
        full_backups = sum(1 for b in backups if b.backup_type == 'full')
        partial_backups = sum(1 for b in backups if b.backup_type == 'partial')
        last_backup = max(backups, key=lambda x: x.created_at) if backups else None
        
        stats = {
            'total_backups': len(backups),
            'total_size_mb': round(total_size, 2),
            'full_backups': full_backups,
            'partial_backups': partial_backups,
            'last_backup': last_backup.to_dict() if last_backup else None
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as error:
        print(f"Error al obtener estadísticas: {error}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener estadísticas'
        }), 500