from config import db
from datetime import datetime

class Direccion(db.Model):
    __tablename__ = 'direcciones'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    calle = db.Column(db.String(200), nullable=False)
    numero_exterior = db.Column(db.String(20), nullable=False)
    numero_interior = db.Column(db.String(20), nullable=True)
    colonia = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    codigo_postal = db.Column(db.String(10), nullable=False)
    referencias = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='casa')  # casa, trabajo, otro
    predeterminada = db.Column(db.Boolean, default=False)
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuario
    usuario = db.relationship('User', backref=db.backref('direcciones', lazy=True))
    
    @classmethod
    def create_direccion(cls, user_id, direccion_data):
        """Crear nueva dirección"""
        # Si esta es la primera dirección del usuario o se marca como predeterminada,
        # debemos asegurarnos de que solo haya una predeterminada
        if direccion_data.get('predeterminada', False):
            # Quitar predeterminada de otras direcciones del usuario
            cls.query.filter_by(user_id=user_id, predeterminada=True).update({'predeterminada': False})
        
        direccion = cls(
            user_id=user_id,
            calle=direccion_data['calle'],
            numero_exterior=direccion_data['numero_exterior'],
            numero_interior=direccion_data.get('numero_interior'),
            colonia=direccion_data['colonia'],
            ciudad=direccion_data['ciudad'],
            estado=direccion_data['estado'],
            codigo_postal=direccion_data['codigo_postal'],
            referencias=direccion_data.get('referencias'),
            tipo=direccion_data.get('tipo', 'casa'),
            predeterminada=direccion_data.get('predeterminada', False),
            activa=direccion_data.get('activa', True)
        )
        
        db.session.add(direccion)
        db.session.commit()
        return direccion.id
    
    @classmethod
    def update_direccion(cls, direccion_id, update_data):
        """Actualizar dirección"""
        direccion = cls.query.get(direccion_id)
        if not direccion:
            return False
        
        # Si se va a marcar como predeterminada
        if 'predeterminada' in update_data and update_data['predeterminada']:
            # Quitar predeterminada de otras direcciones del mismo usuario
            cls.query.filter_by(user_id=direccion.user_id, predeterminada=True).update({'predeterminada': False})
        
        # Actualizar campos
        campos = ['calle', 'numero_exterior', 'numero_interior', 'colonia', 
                 'ciudad', 'estado', 'codigo_postal', 'referencias', 
                 'tipo', 'predeterminada', 'activa']
        
        for campo in campos:
            if campo in update_data:
                setattr(direccion, campo, update_data[campo])
        
        direccion.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return True
    
    @classmethod
    def delete_direccion(cls, direccion_id):
        """Eliminar dirección"""
        try:
            direccion = cls.query.get(direccion_id)
            if not direccion:
                return False
            
            db.session.delete(direccion)
            db.session.commit()
            return True
        except Exception as error:
            print(f"Error al eliminar dirección: {error}")
            db.session.rollback()
            return False
    
    @classmethod
    def get_direccion_by_id(cls, direccion_id):
        """Obtener dirección por ID"""
        return cls.query.get(direccion_id)
    
    @classmethod
    def get_direcciones_by_user(cls, user_id):
        """Obtener todas las direcciones de un usuario"""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_direccion_predeterminada(cls, user_id):
        """Obtener dirección predeterminada de un usuario"""
        return cls.query.filter_by(user_id=user_id, predeterminada=True).first()
    
    @classmethod
    def to_dict(cls, direccion):
        """Convertir dirección a diccionario"""
        if not direccion:
            return None
        
        return {
            'id': direccion.id,
            'user_id': direccion.user_id,
            'calle': direccion.calle,
            'numero_exterior': direccion.numero_exterior,
            'numero_interior': direccion.numero_interior,
            'colonia': direccion.colonia,
            'ciudad': direccion.ciudad,
            'estado': direccion.estado,
            'codigo_postal': direccion.codigo_postal,
            'referencias': direccion.referencias,
            'tipo': direccion.tipo,
            'predeterminada': direccion.predeterminada,
            'activa': direccion.activa,
            'fecha_creacion': direccion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if direccion.fecha_creacion else None,
            'fecha_actualizacion': direccion.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if direccion.fecha_actualizacion else None,
            'direccion_completa': f"{direccion.calle} #{direccion.numero_exterior}" + 
                                  (f" Int. {direccion.numero_interior}" if direccion.numero_interior else "") +
                                  f", {direccion.colonia}, {direccion.ciudad}, {direccion.estado}. CP: {direccion.codigo_postal}"
        }