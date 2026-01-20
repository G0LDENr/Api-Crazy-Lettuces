from config import db
from datetime import datetime
import random
import string

class Orden(db.Model):
    __tablename__ = 'ordenes'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_unico = db.Column(db.String(10), unique=True, nullable=False)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    telefono_usuario = db.Column(db.String(20), nullable=False)
    tipo_pedido = db.Column(db.String(20), nullable=False)  # 'especial' o 'personalizado'
    especial_id = db.Column(db.Integer, db.ForeignKey('especiales.id'), nullable=True)
    ingredientes_personalizados = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, preparando, listo, entregado, cancelado
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con especial
    especial = db.relationship('Especial', backref='ordenes')
    
    @classmethod
    def generar_codigo_unico(cls):
        """Generar código único de 6 caracteres alfanuméricos"""
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not cls.query.filter_by(codigo_unico=codigo).first():
                return codigo
    
    @classmethod
    def find_by_id(cls, orden_id):
        """Buscar orden por ID"""
        return cls.query.get(orden_id)
    
    @classmethod
    def find_by_codigo(cls, codigo):
        """Buscar orden por código único"""
        return cls.query.filter_by(codigo_unico=codigo).first()
    
    @classmethod
    def get_all_ordenes(cls):
        """Obtener todas las órdenes"""
        return cls.query.order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def get_ordenes_by_estado(cls, estado):
        """Obtener órdenes por estado"""
        return cls.query.filter_by(estado=estado).order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def create_orden(cls, orden_data):
        """Crear nueva orden"""
        # Generar código único
        codigo_unico = cls.generar_codigo_unico()
        
        orden = cls(
            codigo_unico=codigo_unico,
            nombre_usuario=orden_data['nombre_usuario'],
            telefono_usuario=orden_data['telefono_usuario'],
            tipo_pedido=orden_data['tipo_pedido'],
            especial_id=orden_data.get('especial_id'),
            ingredientes_personalizados=orden_data.get('ingredientes_personalizados'),
            precio=orden_data['precio'],
            estado=orden_data.get('estado', 'pendiente')
        )
        
        db.session.add(orden)
        db.session.commit()
        return orden.id
    
    @classmethod
    def update_orden(cls, orden_id, update_data):
        """Actualizar orden"""
        orden = cls.query.get(orden_id)
        if not orden:
            return False
        
        if 'nombre_usuario' in update_data:
            orden.nombre_usuario = update_data['nombre_usuario']
        if 'telefono_usuario' in update_data:
            orden.telefono_usuario = update_data['telefono_usuario']
        if 'estado' in update_data:
            orden.estado = update_data['estado']
        if 'precio' in update_data:
            orden.precio = update_data['precio']
        if 'tipo_pedido' in update_data:
            orden.tipo_pedido = update_data['tipo_pedido']
        if 'especial_id' in update_data:
            orden.especial_id = update_data['especial_id']
        if 'ingredientes_personalizados' in update_data:
            orden.ingredientes_personalizados = update_data['ingredientes_personalizados']
        
        orden.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return True
    
    @classmethod
    def delete_orden(cls, orden_id):
        """Eliminar orden"""
        try:
            orden = cls.query.get(orden_id)
            if not orden:
                return False
            
            db.session.delete(orden)
            db.session.commit()
            return True
            
        except Exception as error:
            print(f"Error al eliminar orden {orden_id}: {str(error)}")
            db.session.rollback()
            return False
    
    @classmethod
    def cambiar_estado(cls, orden_id, nuevo_estado):
        """Cambiar estado de una orden"""
        orden = cls.query.get(orden_id)
        if not orden:
            return False
        
        orden.estado = nuevo_estado
        orden.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return True
    
    @classmethod
    def search_ordenes(cls, query):
        """Buscar órdenes por nombre, teléfono o código"""
        if query:
            return cls.query.filter(
                (cls.nombre_usuario.ilike(f'%{query}%')) | 
                (cls.telefono_usuario.ilike(f'%{query}%')) |
                (cls.codigo_unico.ilike(f'%{query}%'))
            ).order_by(cls.fecha_creacion.desc()).all()
        return cls.query.order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def calcular_precio_personalizado(cls, num_ingredientes):
        """Calcular precio basado en número de ingredientes"""
        if num_ingredientes <= 3:
            return 30.0
        elif num_ingredientes <= 5:
            return 35.0
        else:
            return 40.0
    
    @classmethod
    def to_dict(cls, orden):
        """Convertir orden a diccionario"""
        from Models.Especiales import Especial
        
        especial_info = None
        if orden.especial_id and orden.especial:
            especial_info = {
                'id': orden.especial.id,
                'nombre': orden.especial.nombre,
                'precio': float(orden.especial.precio) if orden.especial.precio else 0.0
            }
        
        return {
            'id': orden.id,
            'codigo_unico': orden.codigo_unico,
            'nombre_usuario': orden.nombre_usuario,
            'telefono_usuario': orden.telefono_usuario,
            'tipo_pedido': orden.tipo_pedido,
            'especial': especial_info,
            'ingredientes_personalizados': orden.ingredientes_personalizados,
            'precio': float(orden.precio) if orden.precio else 0.0,
            'estado': orden.estado,
            'fecha_creacion': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
            'fecha_actualizacion': orden.fecha_actualizacion.isoformat() if orden.fecha_actualizacion else None
        }