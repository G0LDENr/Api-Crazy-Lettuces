from config import db
from datetime import datetime
import random
import string
import json

class Orden(db.Model):
    __tablename__ = 'ordenes'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_unico = db.Column(db.String(10), unique=True, nullable=False)
    nombre_usuario = db.Column(db.String(100), nullable=False)
    telefono_usuario = db.Column(db.String(20), nullable=False)
    tipo_pedido = db.Column(db.String(20), nullable=False)  # 'especial', 'personalizado' o 'carrito'
    especial_id = db.Column(db.Integer, db.ForeignKey('especiales.id'), nullable=True)    
    direccion_texto = db.Column(db.Text, nullable=True)
    direccion_id = db.Column(db.Integer, db.ForeignKey('direcciones.id'), nullable=True)
    ingredientes_personalizados = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    
    # ===== NUEVOS CAMPOS PARA CARRITO =====
    metodo_pago = db.Column(db.String(20), default='efectivo')  # 'efectivo' o 'tarjeta'
    info_pago_json = db.Column(db.Text, nullable=True)  # Ej: {"tipo": "visa", "ultimos_4": "1234"}
    notas = db.Column(db.Text, nullable=True)  # Notas adicionales del pedido
    # ======================================
    
    pedido_json = db.Column(db.Text, nullable=True)  # Campo para datos estructurados del pedido
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, preparando, listo, entregado, cancelado
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)    
    especial = db.relationship('Especial', backref='ordenes')
    direccion = db.relationship('Direccion', backref='ordenes')
    
    @classmethod
    def generar_codigo_unico(cls):
        """Generar código único de 6 caracteres alfanuméricos"""
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not cls.query.filter_by(codigo_unico=codigo).first():
                return codigo
    
    @classmethod
    def create_orden(cls, orden_data):
        """Crear nueva orden - VERSIÓN SIMPLIFICADA"""
        # Generar código único
        codigo_unico = cls.generar_codigo_unico()
        
        # Preparar datos para tarjeta (solo info básica, sin datos sensibles)
        info_pago_json = None
        if orden_data.get('metodo_pago') == 'tarjeta' and orden_data.get('info_pago'):
            # Solo guardamos información no sensible
            info_pago = orden_data.get('info_pago', {})
            info_segura = {
                'tipo': info_pago.get('tipo', 'tarjeta'),
                'ultimos_4': info_pago.get('ultimos_4_digitos', '****'),
                'titular': info_pago.get('titular', '')[:50]  # Solo nombre
            }
            info_pago_json = json.dumps(info_segura)
        
        orden = cls(
            codigo_unico=codigo_unico,
            nombre_usuario=orden_data.get('nombre_usuario', ''),
            telefono_usuario=orden_data.get('telefono_usuario', ''),
            tipo_pedido=orden_data.get('tipo_pedido', 'especial'),
            especial_id=orden_data.get('especial_id'),
            direccion_texto=orden_data.get('direccion_texto'),
            direccion_id=orden_data.get('direccion_id'),
            ingredientes_personalizados=orden_data.get('ingredientes_personalizados'),
            precio=orden_data.get('precio', 0),
            
            # ===== NUEVOS CAMPOS =====
            metodo_pago=orden_data.get('metodo_pago', 'efectivo'),
            info_pago_json=info_pago_json,
            notas=orden_data.get('notas'),
            # ========================
            
            pedido_json=orden_data.get('pedido_json'),
            estado=orden_data.get('estado', 'pendiente')
        )
        
        db.session.add(orden)
        try:
            db.session.commit()
            return orden.id
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear orden: {str(e)}")
            raise
    
    @classmethod
    def update_orden(cls, orden_id, update_data):
        """Actualizar orden - VERSIÓN ACTUALIZADA"""
        orden = cls.query.get(orden_id)
        if not orden:
            return False
        
        # Campos actualizables (incluyendo nuevos)
        campos_actualizables = [
            'nombre_usuario', 'telefono_usuario', 'estado', 'precio',
            'tipo_pedido', 'especial_id', 'ingredientes_personalizados',
            'direccion_texto', 'direccion_id', 'pedido_json',
            'metodo_pago', 'info_pago_json', 'notas'  # Nuevos campos
        ]
        
        for campo in campos_actualizables:
            if campo in update_data:
                setattr(orden, campo, update_data[campo])
        
        orden.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return True
    
    @classmethod
    def to_dict(cls, orden):
        """Convertir orden a diccionario - VERSIÓN ACTUALIZADA"""
        from Models.Especiales import Especial
        
        especial_info = None
        if orden.especial_id and orden.especial:
            especial_info = {
                'id': orden.especial.id,
                'nombre': orden.especial.nombre,
                'ingredientes': orden.especial.ingredientes,
                'precio': float(orden.especial.precio) if orden.especial.precio else 0.0
            }
        
        # Parsear info de pago
        info_pago = None
        if orden.info_pago_json:
            try:
                info_pago = json.loads(orden.info_pago_json)
            except:
                info_pago = {'error': 'Error al parsear datos de pago'}
        
        return {
            'id': orden.id,
            'codigo_unico': orden.codigo_unico,
            'nombre_usuario': orden.nombre_usuario,
            'telefono_usuario': orden.telefono_usuario,
            'tipo_pedido': orden.tipo_pedido,
            'especial': especial_info,
            'direccion_texto': orden.direccion_texto,
            'direccion_id': orden.direccion_id,
            'ingredientes_personalizados': orden.ingredientes_personalizados,
            'pedido_json': orden.pedido_json,
            'precio': float(orden.precio) if orden.precio else 0.0,
            
            # ===== NUEVOS CAMPOS =====
            'metodo_pago': orden.metodo_pago,
            'info_pago': info_pago,
            'notas': orden.notas,
            # ========================
            
            'estado': orden.estado,
            'fecha_creacion': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
            'fecha_actualizacion': orden.fecha_actualizacion.isoformat() if orden.fecha_actualizacion else None
        }
    
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