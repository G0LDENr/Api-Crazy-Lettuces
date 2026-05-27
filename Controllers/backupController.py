# Controllers/backupController.py
from flask import jsonify, request, send_file
from config import DB_TYPE
from Models.Backup import Backup
from Models.User import user_repo
from Services.BackupService import backup_service
import os
import json
from datetime import datetime
import gzip
import re
import traceback

# ============================================
# FUNCIÓN DE VERIFICACIÓN DE CÓDIGO
# ============================================

def verify_backup_code(user_id, code):
    """Verificar código de respaldo PERMANENTE"""
    if not code:
        return False
    return user_repo.verify_backup_code(user_id, code)

# ============================================
# CRUD DE RESPALDOS
# ============================================

def get_all_backups():
    """Obtener todos los respaldos"""
    try:
        backups = Backup.get_all_backups()
        backups_list = [Backup.to_dict(backup) for backup in backups]
        return jsonify({
            'success': True,
            'backups': backups_list,
            'count': len(backups_list)
        }), 200
    except Exception as error:
        print(f"Error al obtener respaldos: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al obtener los respaldos'  
        }), 500

def get_single_backup(backup_id):
    """Obtener un respaldo por ID"""
    try:
        backup = Backup.find_by_id(backup_id)
        if not backup:
            return jsonify({
                'success': False,
                'message': 'Respaldo no encontrado'
            }), 404
        return jsonify({
            'success': True,
            'backup': Backup.to_dict(backup)
        }), 200
    except Exception as error:
        print(f"Error al obtener el respaldo: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al obtener el respaldo'
        }), 500

def create_backup():
    """Crear nuevo respaldo - Requiere código único PERMANENTE"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionaron datos'
            }), 400
        
        # Obtener código de respaldo
        backup_code = data.get('backup_code')
        user_id = data.get('user_id')
        
        if not backup_code:
            return jsonify({
                'success': False,
                'message': 'Se requiere el código de respaldo único',
                'code_required': True
            }), 401
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'ID de usuario no proporcionado'
            }), 400
        
        if not verify_backup_code(user_id, backup_code):
            return jsonify({
                'success': False,
                'message': 'Código de respaldo inválido'
            }), 401
        
        tables = data.get('tables', None)
        collections = data.get('collections', None)
        custom_name = data.get('custom_name', None)
        
        print(f"🎯 Creando respaldo - DB_TYPE: {DB_TYPE}")
        print(f"   tables: {tables}")
        print(f"   collections: {collections}")
        
        if DB_TYPE == 'mysql':
            if tables and isinstance(tables, str):
                tables = [t.strip() for t in tables.split(',')]
            result = backup_service.perform_backup(tables=tables, custom_name=custom_name)
        else:
            if collections and isinstance(collections, str):
                collections = [c.strip() for c in collections.split(',')]
            elif tables:
                collections = tables
                if isinstance(collections, str):
                    collections = [c.strip() for c in collections.split(',')]
            result = backup_service.perform_backup(collections=collections, custom_name=custom_name)
        
        if result['success']:
            print(f"✅ Respaldo creado exitosamente: {result.get('filename')}")
            return jsonify(result), 201
        else:
            return jsonify(result), 500
            
    except Exception as error:
        print(f"💥 Error: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al crear el respaldo: {str(error)}'
        }), 500

def upload_backup():
    """Subir/Importar un respaldo existente - Requiere código PERMANENTE"""
    try:
        print(f"📤 Iniciando importación de respaldo...")
        
        if 'backup_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó archivo de respaldo'
            }), 400
        
        backup_file = request.files['backup_file']
        
        if backup_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        # Obtener código de respaldo del form data
        backup_code = request.form.get('backup_code')
        user_id = request.form.get('user_id')
        
        print(f"🔑 Código recibido: {backup_code}")
        print(f"👤 User ID recibido: {user_id}")
        
        if not backup_code:
            return jsonify({
                'success': False,
                'message': 'Se requiere el código de respaldo único',
                'code_required': True
            }), 401
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'ID de usuario no proporcionado'
            }), 400
        
        if not verify_backup_code(user_id, backup_code):
            return jsonify({
                'success': False,
                'message': 'Código de respaldo inválido'
            }), 401
        
        allowed_extensions = {'.sql', '.sql.gz', '.gz', '.backup', '.json', '.json.gz'}
        filename = backup_file.filename.lower()
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return jsonify({
                'success': False,
                'message': 'Formato de archivo no válido. Use .sql, .sql.gz, .json o .json.gz'
            }), 400
        
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        original_name = os.path.splitext(backup_file.filename)[0]
        if original_name.endswith('.sql') or original_name.endswith('.json'):
            original_name = original_name[:-4]
        
        safe_name = ''.join(c for c in original_name if c.isalnum() or c in ['_', '-', ' '])
        safe_name = safe_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        if backup_file.filename.endswith('.sql.gz'):
            file_extension = '.sql.gz'
        elif backup_file.filename.endswith('.json.gz'):
            file_extension = '.json.gz'
        elif backup_file.filename.endswith('.gz'):
            file_extension = '.gz'
        elif backup_file.filename.endswith('.json'):
            file_extension = '.json'
        else:
            file_extension = '.sql'
        
        new_filename = f"imported_{timestamp}_{safe_name}{file_extension}"
        filepath = os.path.join(backup_dir, new_filename)
        
        backup_file.save(filepath)
        print(f"💾 Archivo guardado en: {filepath}")
        
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        
        backup_type = 'full'
        tables_included = None
        
        try:
            content = ""
            if filepath.endswith('.gz'):
                with gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore') as f:
                    content = f.read(20000)
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(20000)
            
            if '-- Tipo: PARTIAL' in content.upper() or 'partial' in content.upper():
                backup_type = 'partial'
            
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
            
            if 'backup_info' in content and 'collections' in content:
                try:
                    json_data = json.loads(content)
                    if 'collections' in json_data:
                        found_tables = [c.get('collection') for c in json_data['collections'] if c.get('collection')]
                        backup_type = json_data.get('backup_info', {}).get('tipo', 'full')
                except:
                    pass
            
            if found_tables:
                tables_included = list(found_tables)
                if len(tables_included) < 5:
                    backup_type = 'partial'
        except Exception as e:
            print(f"⚠️ No se pudo analizar archivo: {e}")
        
        print(f"📊 Respaldo importado: {new_filename}")
        print(f"   Tamaño: {size_mb:.2f} MB")
        print(f"   Tipo: {backup_type}")
        print(f"   Tablas detectadas: {len(tables_included) if tables_included else 0}")
        
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
            'tables_included': tables_included
        }), 201
        
    except Exception as error:
        print(f"💥 Error al importar respaldo: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al importar respaldo: {str(error)}'
        }), 500

def delete_backup(backup_id):
    """Eliminar un respaldo por ID - Requiere código de respaldo"""
    try:
        data = request.get_json() or {}
        backup_code = data.get('backup_code')
        user_id = data.get('user_id')
        
        print(f"🔍 Solicitando eliminación del respaldo ID: {backup_id}")
        print(f"📝 Datos recibidos: backup_code={backup_code}, user_id={user_id}")
        
        if not backup_code:
            return jsonify({
                'success': False,
                'message': 'Se requiere el código de respaldo único',
                'code_required': True
            }), 401
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'ID de usuario no proporcionado'
            }), 400
        
        if not verify_backup_code(user_id, backup_code):
            return jsonify({
                'success': False,
                'message': 'Código de respaldo inválido'
            }), 401
        
        existing_backup = Backup.find_by_id(backup_id)
        if not existing_backup:
            print(f"❌ Respaldo {backup_id} no encontrado")
            return jsonify({
                'success': False,
                'message': 'Respaldo no encontrado'
            }), 404
        
        # Convertir backup_id a entero si es necesario
        try:
            backup_id_int = int(backup_id) if DB_TYPE == 'mysql' else backup_id
        except:
            backup_id_int = backup_id
        
        success = Backup.delete_backup(backup_id_int)
        
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
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(error)}'
        }), 500

def download_backup(backup_id):
    """Descargar archivo de respaldo - Requiere código de respaldo"""
    try:
        # Obtener código de los query parameters
        backup_code = request.args.get('backup_code')
        user_id = request.args.get('user_id')
        
        print(f"📥 Descargando respaldo ID: {backup_id}")
        print(f"🔑 Código recibido: {backup_code}")
        print(f"👤 User ID: {user_id}")
        
        if not backup_code:
            return jsonify({
                'success': False,
                'message': 'Se requiere el código de respaldo único'
            }), 401
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'ID de usuario no proporcionado'
            }), 400
        
        if not verify_backup_code(user_id, backup_code):
            return jsonify({
                'success': False,
                'message': 'Código de respaldo inválido'
            }), 401
        
        backup = Backup.find_by_id(backup_id)
        
        if not backup:
            return jsonify({
                'success': False,
                'message': 'Respaldo no encontrado'
            }), 404
        
        filepath = backup.filepath if hasattr(backup, 'filepath') else backup.get('filepath')
        filename = backup.filename if hasattr(backup, 'filename') else backup.get('filename')
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': 'Archivo de respaldo no encontrado'
            }), 404
        
        print(f"📥 Descargando respaldo: {filename}")
        
        if filepath.endswith('.gz'):
            mimetype = 'application/gzip'
            download_name = filename
        elif filepath.endswith('.json'):
            mimetype = 'application/json'
            download_name = filename
        else:
            mimetype = 'application/sql'
            download_name = filename
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
    except Exception as error:
        print(f"💥 Error al descargar respaldo: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al descargar el respaldo'
        }), 500

def restore_backup(backup_id):
    """Restaurar base de datos - Requiere código PERMANENTE"""
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        backup_code = data.get('backup_code')
        user_id = data.get('user_id')
        
        if not confirm:
            return jsonify({
                'success': False,
                'message': 'Se requiere confirmación para restaurar'
            }), 400
        
        if not backup_code:
            return jsonify({
                'success': False,
                'message': 'Se requiere el código de respaldo único',
                'code_required': True
            }), 401
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'ID de usuario no proporcionado'
            }), 400
        
        if not verify_backup_code(user_id, backup_code):
            return jsonify({
                'success': False,
                'message': 'Código de respaldo inválido'
            }), 401
        
        print(f"🔄 Iniciando restauración del respaldo ID: {backup_id}")
        
        result = backup_service.restore_backup(backup_id)
        
        if result['success']:
            print(f"✅ Base de datos restaurada exitosamente")
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as error:
        print(f"💥 Error: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al restaurar el respaldo',
            'error_detail': str(error)
        }), 500

# ============================================
# PROGRAMACIÓN DE RESPALDOS
# ============================================

def schedule_backup():
    """Programar respaldo automático"""
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
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al programar el respaldo automático'
        }), 500

def get_scheduled_backups():
    """Obtener respaldos programados"""
    try:
        jobs = backup_service.get_scheduled_jobs()
        return jsonify({
            'success': True,
            'scheduled_jobs': jobs,
            'count': len(jobs)
        }), 200
    except Exception as error:
        print(f"Error al obtener respaldos programados: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al obtener los respaldos programados'
        }), 500

def cancel_scheduled_backup(job_id):
    """Cancelar respaldo programado"""
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
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al cancelar el respaldo programado'
        }), 500

# ============================================
# UTILIDADES
# ============================================

def get_database_tables():
    """Obtener lista de tablas/colecciones de la base de datos"""
    try:
        from config import DB_TYPE
        
        print(f"🔍 get_database_tables - DB_TYPE: {DB_TYPE}")
        
        if DB_TYPE == 'mysql':
            from sqlalchemy import inspect
            from config import db_sql
            from flask import current_app
            
            with current_app.app_context():
                inspector = inspect(db_sql.engine)
                tables = inspector.get_table_names()
                
                print(f"📊 Tablas MySQL encontradas: {tables}")
                
                return jsonify({
                    'success': True,
                    'tables': tables,
                    'count': len(tables)
                }), 200
                
        else:
            from config import db_mongo
            
            all_collections = db_mongo.db.list_collection_names()
            collections = [c for c in all_collections if not c.startswith('system.')]
            
            print(f"📊 Colecciones MongoDB encontradas: {collections}")
            
            return jsonify({
                'success': True,
                'tables': collections,
                'count': len(collections)
            }), 200
            
    except Exception as error:
        print(f"Error al obtener tablas/colecciones: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al obtener las tablas/colecciones: {str(error)}'
        }), 500

def get_backup_stats():
    """Obtener estadísticas de respaldos"""
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
        
        total_size = 0
        full_backups = 0
        partial_backups = 0
        
        for backup in backups:
            if DB_TYPE == 'mysql':
                total_size += backup.size_mb
                if backup.backup_type == 'full':
                    full_backups += 1
                else:
                    partial_backups += 1
            else:
                total_size += backup.get('size_mb', 0)
                if backup.get('backup_type') == 'full':
                    full_backups += 1
                else:
                    partial_backups += 1
        
        last_backup = backups[0] if backups else None
        last_backup_dict = Backup.to_dict(last_backup) if last_backup else None
        
        stats = {
            'total_backups': len(backups),
            'total_size_mb': round(total_size, 2),
            'full_backups': full_backups,
            'partial_backups': partial_backups,
            'last_backup': last_backup_dict
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as error:
        print(f"Error al obtener estadísticas: {error}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error al obtener estadísticas'
        }), 500

# ============================================
# CÓDIGO DE RESPALDO
# ============================================

def generate_admin_backup_code():
    """Generar código de respaldo para administrador (solo si no tiene)"""
    try:
        from flask import request
        from Controllers.notificacionesController import create_notification
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'ID de usuario requerido'}), 400
        
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        user_dict = user_repo.to_dict(user)
        
        if user_dict.get('rol') != 1:
            return jsonify({'success': False, 'message': 'Solo administradores pueden generar código'}), 403
        
        if user_repo.has_valid_backup_code(user_id):
            return jsonify({
                'success': False,
                'message': 'Ya tienes un código de respaldo. Usa /regenerate-code si quieres cambiarlo.'
            }), 400
        
        backup_code = user_repo.generate_backup_code(user_id)
        
        if backup_code:
            # Crear notificación con el código
            create_notification(
                user_id=user_id,
                titulo="🔐 Código de Respaldo Único",
                mensaje=f"Tu código único para realizar respaldos es: **{backup_code}**\n\n"
                        f"Este código te permitirá realizar operaciones de respaldo y restauración.\n\n"
                        f"⚠️ **IMPORTANTE:** Este código es PERMANENTE. Guárdalo en un lugar seguro.\n"
                        f"Una vez que cierres esta notificación, no podrás verlo nuevamente.\n"
                        f"Si lo pierdes, puedes generar uno nuevo desde el panel de administración.",
                tipo="backup_code",
                datos_adicionales={
                    'backup_code': backup_code,
                    'permanent': True,
                    'warning': '⚠️ Este código es permanente. Guárdalo en un lugar seguro. No se mostrará nuevamente después de cerrar esta notificación.'
                }
            )
            return jsonify({
                'success': True, 
                'message': 'Código generado exitosamente',
                'backup_code': backup_code
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Error al generar código'}), 500
            
    except Exception as error:
        print(f"Error: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(error)}), 500

def regenerate_backup_code():
    """Regenerar código de respaldo (sobrescribe el anterior)"""
    try:
        from flask import request
        from Controllers.notificacionesController import create_notification
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'ID de usuario requerido'}), 400
        
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        user_dict = user_repo.to_dict(user)
        
        if user_dict.get('rol') != 1:
            return jsonify({'success': False, 'message': 'Solo administradores pueden regenerar código'}), 403
        
        backup_code = user_repo.generate_backup_code(user_id)
        
        if backup_code:
            create_notification(
                user_id=user_id,
                titulo="🔄 Nuevo Código de Respaldo",
                mensaje=f"Se ha generado un NUEVO código de respaldo: **{backup_code}**\n\n"
                        f"Este código reemplaza al anterior.\n\n"
                        f"⚠️ **IMPORTANTE:** Guarda este nuevo código. El anterior ya no funcionará.\n"
                        f"Si pierdes este código, puedes generar otro desde el panel de administración.",
                tipo="backup_code",
                datos_adicionales={
                    'backup_code': backup_code,
                    'permanent': True,
                    'replaced': True,
                    'warning': '⚠️ Este es tu NUEVO código de respaldo. El anterior ya no es válido.'
                }
            )
            return jsonify({
                'success': True,
                'message': 'Código regenerado exitosamente',
                'backup_code': backup_code
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Error al regenerar código'}), 500
            
    except Exception as error:
        print(f"Error: {error}")
        return jsonify({'success': False, 'message': str(error)}), 500
    
def verify_backup_code_only():
    """Verificar código de respaldo sin realizar ninguna acción"""
    try:
        data = request.get_json()
        backup_code = data.get('backup_code')
        user_id = data.get('user_id')
        
        print("=" * 60)
        print("🔍 VERIFICANDO CÓDIGO DE RESPALDO")
        print(f"🔑 Código recibido: {backup_code}")
        print(f"👤 User ID: {user_id}")
        print("=" * 60)
        
        if not backup_code:
            return jsonify({
                'success': False,
                'message': 'Se requiere el código de respaldo único'
            }), 401
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'ID de usuario no proporcionado'
            }), 400
        
        if verify_backup_code(user_id, backup_code):
            print("✅ Código válido")
            return jsonify({'success': True, 'message': 'Código válido'}), 200
        else:
            print("❌ Código inválido")
            return jsonify({'success': False, 'message': 'Código inválido'}), 401
            
    except Exception as error:
        print(f"Error: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(error)}), 500