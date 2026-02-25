# Models/Backup.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime
import os
import json

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

# ============================================
# CLASE PRINCIPAL - Usa el repositorio según DB_TYPE
# ============================================
class Backup:
    """Clase que maneja backups en ambas bases de datos"""
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.backups
    
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
        except:
            return []
    
    @classmethod
    def find_by_id(cls, backup_id):
        """Buscar respaldo por ID"""
        try:
            if DB_TYPE == 'mysql':
                return BackupSQL.query.get(backup_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(backup_id)})
        except:
            return None
    
    @classmethod
    def delete_backup(cls, backup_id):
        """Eliminar respaldo"""
        try:
            if DB_TYPE == 'mysql':
                backup = BackupSQL.query.get(backup_id)
                if not backup:
                    return False
                
                if os.path.exists(backup.filepath):
                    try:
                        os.remove(backup.filepath)
                    except:
                        pass
                
                db_sql.session.delete(backup)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                backup = cls.find_by_id(backup_id)
                if backup and os.path.exists(backup.get('filepath', '')):
                    try:
                        os.remove(backup['filepath'])
                    except:
                        pass
                
                result = cls._get_collection().delete_one({'_id': ObjectId(backup_id)})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error al eliminar respaldo: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def to_dict(cls, backup):
        """Convertir backup a diccionario"""
        if not backup:
            return None
        
        if DB_TYPE == 'mysql':
            tables = []
            if backup.tables_included:
                try:
                    tables = json.loads(backup.tables_included)
                except:
                    tables = []
            
            return {
                'id': backup.id,
                'filename': backup.filename,
                'filepath': backup.filepath,
                'size_mb': round(backup.size_mb, 2),
                'tables_included': tables,
                'backup_type': backup.backup_type,
                'status': backup.status,
                'created_at': backup.created_at.isoformat() if backup.created_at else None
            }
        else:
            from bson.objectid import ObjectId
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

# Para compatibilidad con código existente
if DB_TYPE == 'mysql':
    BackupSQL = Backup