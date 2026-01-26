from config import db
from datetime import datetime
import os
import json

class Backup(db.Model):
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    size_mb = db.Column(db.Float, default=0.0)
    tables_included = db.Column(db.Text, nullable=True)
    backup_type = db.Column(db.String(50), default='full')
    status = db.Column(db.String(50), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, filename, filepath, size_mb, backup_type='full', tables_included=None, status='completed'):
        self.filename = filename
        self.filepath = filepath
        self.size_mb = size_mb
        self.backup_type = backup_type
        self.tables_included = tables_included
        self.status = status
    
    def to_dict(self):
        """Convertir backup a diccionario"""
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
    
    @classmethod
    def get_all_backups(cls):
        """Obtener todos los respaldos ordenados por fecha"""
        return cls.query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def find_by_id(cls, backup_id):
        """Buscar respaldo por ID"""
        return cls.query.get(backup_id)
    
    @classmethod
    def delete_backup(cls, backup_id):
        """Eliminar respaldo"""
        try:
            backup = cls.query.get(backup_id)
            if not backup:
                return False
            
            # Eliminar archivo físico
            if os.path.exists(backup.filepath):
                try:
                    os.remove(backup.filepath)
                except:
                    pass
            
            db.session.delete(backup)
            db.session.commit()
            return True
            
        except Exception as error:
            print(f"Error al eliminar respaldo: {error}")
            db.session.rollback()
            return False
    
    @classmethod
    def create_backup_record(cls, backup_data):
        """Crear un nuevo registro de respaldo"""
        try:
            # Crear nueva instancia
            backup = cls(
                filename=backup_data.get('filename'),
                filepath=backup_data.get('filepath'),
                size_mb=backup_data.get('size_mb', 0.0),
                backup_type=backup_data.get('backup_type', 'full'),
                status=backup_data.get('status', 'completed')
            )
            
            # Manejar tables_included como JSON string
            tables = backup_data.get('tables_included')
            if tables:
                if isinstance(tables, list):
                    backup.tables_included = json.dumps(tables)
                else:
                    backup.tables_included = str(tables)
            
            # Guardar en la base de datos
            db.session.add(backup)
            db.session.commit()
            
            return backup.id
            
        except Exception as error:
            print(f"Error al crear registro de respaldo: {error}")
            db.session.rollback()
            raise Exception(f"No se pudo crear el registro: {str(error)}")