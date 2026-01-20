from config import db
from datetime import datetime

class Especial(db.Model):
    __tablename__ = 'especiales'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ingredientes = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def find_by_id(cls, especial_id):
        """Buscar especial por ID"""
        return cls.query.get(especial_id)
    
    @classmethod
    def find_by_name(cls, nombre):
        """Buscar especial por nombre"""
        return cls.query.filter_by(nombre=nombre).first()
    
    @classmethod
    def get_all_especiales(cls, only_active=True):
        """Obtener todos los especiales"""
        if only_active:
            return cls.query.filter_by(activo=True).all()
        return cls.query.all()
    
    @classmethod
    def get_active_especiales(cls):
        """Obtener solo especiales activos"""
        return cls.query.filter_by(activo=True).all()
    
    @classmethod
    def create_especial(cls, especial_data):
        """Crear nuevo especial"""
        especial = cls(
            nombre=especial_data['nombre'],
            ingredientes=especial_data['ingredientes'],
            precio=especial_data['precio'],
            activo=especial_data.get('activo', True)
        )
        
        db.session.add(especial)
        db.session.commit()
        return especial.id
    
    @classmethod
    def update_especial(cls, especial_id, update_data):
        """Actualizar especial"""
        especial = cls.query.get(especial_id)
        if not especial:
            return False
        
        if 'nombre' in update_data:
            especial.nombre = update_data['nombre']
        if 'ingredientes' in update_data:
            especial.ingredientes = update_data['ingredientes']
        if 'precio' in update_data:
            especial.precio = update_data['precio']
        if 'activo' in update_data:
            especial.activo = update_data['activo']
        
        especial.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return True
    
    @classmethod
    def delete_especial(cls, especial_id):
        """Eliminar especial (eliminación física)"""
        try:
            especial = cls.query.get(especial_id)
            if not especial:
                return False
            
            db.session.delete(especial)
            db.session.commit()
            return True
            
        except Exception as error:
            print(f"Error al eliminar especial {especial_id}: {str(error)}")
            db.session.rollback()
            return False
    
    @classmethod
    def toggle_activo(cls, especial_id):
        """Activar/desactivar especial"""
        especial = cls.query.get(especial_id)
        if not especial:
            return False
        
        especial.activo = not especial.activo
        especial.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return True
    
    @classmethod
    def search_especiales(cls, query):
        """Buscar especiales por nombre o ingredientes"""
        if query:
            return cls.query.filter(
                (cls.nombre.ilike(f'%{query}%')) | 
                (cls.ingredientes.ilike(f'%{query}%'))
            ).all()
        return cls.query.all()
    
    @classmethod
    def to_dict(cls, especial):
        """Convertir especial a diccionario"""
        return {
            'id': especial.id,
            'nombre': especial.nombre,
            'ingredientes': especial.ingredientes,
            'precio': float(especial.precio) if especial.precio else 0.0,
            'activo': especial.activo,
            'fecha_creacion': especial.fecha_creacion.isoformat() if especial.fecha_creacion else None,
            'fecha_actualizacion': especial.fecha_actualizacion.isoformat() if especial.fecha_actualizacion else None
        }