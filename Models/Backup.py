# Models/Backup.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime
import os
import json
import logging

logger = logging.getLogger(__name__)

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class BackupSQL(db_sql.Model):
    __tablename__ = 'backups'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    filename = db_sql.Column(db_sql.String(255), nullable=False)
    filepath = db_sql.Column(db_sql.String(500), nullable=False)
    size_mb = db_sql.Column(db_sql.Float, default=0.0)
    tables_included = db_sql.Column(db_sql.Text, nullable=True)
    backup_type = db_sql.Column(db_sql.String(50), default='full')
    status = db_sql.Column(db_sql.String(50), default='completed')
    created_at = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Backup {self.filename}>'
    
    def to_dict(self):
        tables = []
        if self.tables_included:
            try:
                tables = json.loads(self.tables_included)
            except:
                tables = []
        
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'size_mb': round(self.size_mb, 2),
            'tables_included': tables,
            'backup_type': self.backup_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ============================================
# CLASE PRINCIPAL
# ============================================
class Backup:
    """Clase que maneja backups en ambas bases de datos"""
    
    # Variable de clase para proteger backups en restauración
    _restoring_backup_ids = set()
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.backups
    
    @classmethod
    def protect_backup(cls, backup_id):
        """Proteger un backup para que no se pueda eliminar"""
        cls._restoring_backup_ids.add(str(backup_id))
        logger.info(f"🛡️ Backup {backup_id} protegido (en restauración)")
    
    @classmethod
    def unprotect_backup(cls, backup_id):
        """Quitar protección de un backup"""
        cls._restoring_backup_ids.discard(str(backup_id))
        logger.info(f"🔓 Backup {backup_id} desprotegido")
    
    @classmethod
    def is_protected(cls, backup_id):
        """Verificar si un backup está protegido"""
        return str(backup_id) in cls._restoring_backup_ids
    
    @classmethod
    def create_backup_record(cls, backup_data):
        """Crear un nuevo registro de respaldo"""
        try:
            if DB_TYPE == 'mysql':
                backup = BackupSQL(
                    filename=backup_data.get('filename'),
                    filepath=backup_data.get('filepath'),
                    size_mb=backup_data.get('size_mb', 0.0),
                    backup_type=backup_data.get('backup_type', 'full'),
                    status=backup_data.get('status', 'completed')
                )
                
                tables = backup_data.get('tables_included')
                if tables:
                    if isinstance(tables, list):
                        backup.tables_included = json.dumps(tables)
                    else:
                        backup.tables_included = str(tables)
                
                db_sql.session.add(backup)
                db_sql.session.commit()
                return backup.id
                
            else:
                from bson.objectid import ObjectId
                
                tables_included = backup_data.get('tables_included')
                if isinstance(tables_included, list):
                    tables_included = json.dumps(tables_included)
                
                backup_doc = {
                    'filename': backup_data.get('filename'),
                    'filepath': backup_data.get('filepath'),
                    'size_mb': float(backup_data.get('size_mb', 0.0)),
                    'tables_included': tables_included,
                    'backup_type': backup_data.get('backup_type', 'full'),
                    'status': backup_data.get('status', 'completed'),
                    'created_at': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(backup_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error al crear registro de respaldo: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def get_all_backups(cls):
        """Obtener todos los respaldos ordenados por fecha"""
        try:
            if DB_TYPE == 'mysql':
                return BackupSQL.query.order_by(BackupSQL.created_at.desc()).all()
            else:
                return list(cls._get_collection().find().sort('created_at', -1))
        except Exception as e:
            print(f"Error al obtener respaldos: {e}")
            return []
    
    @classmethod
    def find_by_id(cls, backup_id):
        """Buscar respaldo por ID"""
        try:
            if DB_TYPE == 'mysql':
                return BackupSQL.query.get(backup_id)
            else:
                from bson.objectid import ObjectId
                try:
                    obj_id = ObjectId(backup_id)
                    return cls._get_collection().find_one({'_id': obj_id})
                except:
                    return None
        except Exception as e:
            print(f"Error al buscar respaldo {backup_id}: {e}")
            return None
    
    @classmethod
    def delete_backup(cls, backup_id):
        """Eliminar respaldo - CON PROTECCIÓN"""
        try:
            # VERIFICAR PROTECCIÓN
            if cls.is_protected(backup_id):
                logger.error(f"🚫 ¡BLOQUEADO! No se puede eliminar backup {backup_id} porque está protegido (en restauración)")
                import traceback
                traceback.print_stack()
                return False
            
            if DB_TYPE == 'mysql':
                # MySQL
                backup = BackupSQL.query.get(backup_id)
                if not backup:
                    logger.warning(f"⚠️ Backup no encontrado: {backup_id}")
                    return False
                
                # Eliminar archivo físico
                filepath = backup.filepath
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        logger.info(f"✅ Archivo MySQL eliminado: {filepath}")
                    except Exception as e:
                        logger.error(f"❌ Error eliminando archivo MySQL: {e}")
                else:
                    logger.warning(f"⚠️ Archivo no encontrado: {filepath}")
                
                db_sql.session.delete(backup)
                db_sql.session.commit()
                logger.info(f"✅ Backup {backup_id} eliminado de MySQL")
                return True
                
            else:
                # MongoDB
                from bson.objectid import ObjectId
                
                try:
                    obj_id = ObjectId(backup_id)
                except:
                    logger.error(f"❌ ID inválido para MongoDB: {backup_id}")
                    return False
                
                # Buscar el backup
                backup = cls._get_collection().find_one({'_id': obj_id})
                if not backup:
                    logger.warning(f"⚠️ Backup no encontrado: {backup_id}")
                    return False
                
                # Eliminar archivo físico
                filepath = backup.get('filepath')
                if filepath:
                    # Convertir a ruta absoluta si es necesario
                    if not os.path.isabs(filepath):
                        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        filepath = os.path.join(base_dir, filepath)
                        logger.info(f"📁 Ruta convertida: {filepath}")
                    
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            logger.info(f"✅ Archivo MongoDB eliminado: {filepath}")
                        except Exception as e:
                            logger.error(f"❌ Error eliminando archivo: {e}")
                    else:
                        logger.warning(f"⚠️ Archivo no encontrado: {filepath}")
                else:
                    logger.warning(f"⚠️ No hay ruta de archivo en el backup")
                
                # Eliminar registro
                result = cls._get_collection().delete_one({'_id': obj_id})
                
                if result.deleted_count > 0:
                    logger.info(f"✅ Backup {backup_id} eliminado de MongoDB")
                    return True
                else:
                    logger.error(f"❌ No se pudo eliminar backup: {backup_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error al eliminar respaldo: {e}")
            import traceback
            traceback.print_exc()
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def to_dict(cls, backup):
        """Convertir backup a diccionario"""
        if not backup:
            return None
        
        if DB_TYPE == 'mysql':
            return backup.to_dict()
        else:
            backup_dict = dict(backup)
            backup_dict['id'] = str(backup_dict.pop('_id'))
            
            if 'tables_included' in backup_dict and backup_dict['tables_included']:
                try:
                    backup_dict['tables_included'] = json.loads(backup_dict['tables_included'])
                except:
                    backup_dict['tables_included'] = []
            
            if 'size_mb' in backup_dict:
                backup_dict['size_mb'] = round(float(backup_dict['size_mb']), 2)
            
            if 'created_at' in backup_dict and backup_dict['created_at']:
                if isinstance(backup_dict['created_at'], datetime):
                    backup_dict['created_at'] = backup_dict['created_at'].isoformat()
            
            return backup_dict