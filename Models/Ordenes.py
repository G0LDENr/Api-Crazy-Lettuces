# Models/Orden.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime
import random
import string
import json

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class OrdenSQL(db_sql.Model):
    __tablename__ = 'ordenes'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    codigo_unico = db_sql.Column(db_sql.String(10), unique=True, nullable=False)
    nombre_usuario = db_sql.Column(db_sql.String(100), nullable=False)
    telefono_usuario = db_sql.Column(db_sql.String(20), nullable=False)
    tipo_pedido = db_sql.Column(db_sql.String(20), nullable=False)
    suplemento_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('suplementos.id'), nullable=True)    
    tarjeta_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('tarjetas.id'), nullable=True)
    direccion_texto = db_sql.Column(db_sql.Text, nullable=True)
    direccion_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('direcciones.id'), nullable=True)
    cantidad = db_sql.Column(db_sql.Integer, default=1)
    precio_unitario = db_sql.Column(db_sql.Numeric(10, 2), nullable=False)
    precio_total = db_sql.Column(db_sql.Numeric(10, 2), nullable=False)
    metodo_pago = db_sql.Column(db_sql.String(20), default='efectivo')
    info_pago_json = db_sql.Column(db_sql.Text, nullable=True)
    notas = db_sql.Column(db_sql.Text, nullable=True)
    pedido_json = db_sql.Column(db_sql.Text, nullable=True)
    estado = db_sql.Column(db_sql.String(20), default='pendiente')
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)    
    
    def __repr__(self):
        return f'<Orden {self.codigo_unico}>'
    
    def to_dict(self):
        """Convertir objeto SQL a diccionario"""
        return {
            'id': self.id,
            'codigo_unico': self.codigo_unico,
            'nombre_usuario': self.nombre_usuario,
            'telefono_usuario': self.telefono_usuario,
            'tipo_pedido': self.tipo_pedido,
            'suplemento_id': self.suplemento_id,
            'tarjeta_id': self.tarjeta_id,
            'direccion_texto': self.direccion_texto,
            'direccion_id': self.direccion_id,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario) if self.precio_unitario else 0.0,
            'precio_total': float(self.precio_total) if self.precio_total else 0.0,
            'metodo_pago': self.metodo_pago,
            'info_pago_json': self.info_pago_json,
            'notas': self.notas,
            'pedido_json': self.pedido_json,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

# ============================================
# CLASE PRINCIPAL
# ============================================
class Orden:
    """Clase que maneja órdenes de suplementos en ambas bases de datos"""
    
    ESTADOS = {
        'pendiente': 'Pendiente',
        'confirmada': 'Confirmada',
        'pagada': 'Pagada',
        'en_preparacion': 'En Preparación',
        'enviada': 'Enviada',
        'entregada': 'Entregada',
        'cancelada': 'Cancelada',
        'reembolsada': 'Reembolsada'
    }
    
    @classmethod
    def _get_collection(cls):
        return db_mongo.db.ordenes
    
    @classmethod
    def generar_codigo_unico(cls):
        if DB_TYPE == 'mysql':
            while True:
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not OrdenSQL.query.filter_by(codigo_unico=codigo).first():
                    return codigo
        else:
            while True:
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not cls._get_collection().find_one({'codigo_unico': codigo}):
                    return codigo
    
    @classmethod
    def create_orden(cls, orden_data):
        """Crear nueva orden de suplementos"""
        try:
            codigo_unico = cls.generar_codigo_unico()
            
            # Calcular precio total
            cantidad = orden_data.get('cantidad', 1)
            precio_unitario = orden_data.get('precio_unitario', 0)
            precio_total = cantidad * precio_unitario
            
            # LOG IMPORTANTE - Ver qué valores están llegando
            print("="*60)
            print("🔍 DEBUG - create_orden - DATOS RECIBIDOS:")
            print(f"  - cantidad: {cantidad}")
            print(f"  - precio_unitario: {precio_unitario}")
            print(f"  - precio_total calculado: {precio_total}")
            print(f"  - orden_data.get('precio_total'): {orden_data.get('precio_total')}")
            print(f"  - tipo: {type(orden_data.get('precio_total'))}")
            
            # Si viene precio_total en los datos, usarlo
            if 'precio_total' in orden_data and orden_data['precio_total'] is not None:
                try:
                    precio_total = float(orden_data['precio_total'])
                    print(f"  ✅ Usando precio_total del data: {precio_total}")
                except (TypeError, ValueError) as e:
                    print(f"  ❌ Error al convertir precio_total: {e}")
            
            # Asegurar que precio_total sea un número válido
            try:
                precio_total = float(precio_total)
            except (TypeError, ValueError):
                precio_total = 0.0
                print(f"  ⚠️ precio_total inválido, usando 0")
            
            print(f"  💾 precio_total final: {precio_total} (tipo: {type(precio_total)})")
            
            # Procesar información de pago
            info_pago_json = None
            if orden_data.get('metodo_pago') == 'tarjeta' and orden_data.get('info_pago'):
                info_pago = orden_data.get('info_pago', {})
                info_segura = {
                    'tipo': info_pago.get('tipo', 'tarjeta'),
                    'ultimos_4': info_pago.get('ultimos_4_digitos', '****'),
                    'titular': info_pago.get('titular', '')[:50]
                }
                info_pago_json = json.dumps(info_segura)
            
            if DB_TYPE == 'mysql':
                print(f"  💾 Creando orden SQL...")
                
                orden = OrdenSQL(
                    codigo_unico=codigo_unico,
                    nombre_usuario=orden_data.get('nombre_usuario', ''),
                    telefono_usuario=orden_data.get('telefono_usuario', ''),
                    tipo_pedido=orden_data.get('tipo_pedido', 'suplemento'),
                    suplemento_id=orden_data.get('suplemento_id'),
                    tarjeta_id=orden_data.get('tarjeta_id'),
                    direccion_texto=orden_data.get('direccion_texto'),
                    direccion_id=orden_data.get('direccion_id'),
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    precio_total=precio_total,
                    metodo_pago=orden_data.get('metodo_pago', 'efectivo'),
                    info_pago_json=info_pago_json,
                    notas=orden_data.get('notas'),
                    pedido_json=orden_data.get('pedido_json'),
                    estado=orden_data.get('estado', 'pendiente')
                )
                
                db_sql.session.add(orden)
                db_sql.session.commit()
                print(f"  ✅ Orden guardada con ID: {orden.id}")
                print(f"  💰 precio_total guardado: {orden.precio_total}")
                print("="*60)
                return orden.id
                
            else:
                from bson.objectid import ObjectId
                
                orden_doc = {
                    'codigo_unico': codigo_unico,
                    'nombre_usuario': orden_data.get('nombre_usuario', ''),
                    'telefono_usuario': orden_data.get('telefono_usuario', ''),
                    'tipo_pedido': orden_data.get('tipo_pedido', 'suplemento'),
                    'suplemento_id': str(orden_data.get('suplemento_id')) if orden_data.get('suplemento_id') else None,
                    'direccion_texto': orden_data.get('direccion_texto'),
                    'direccion_id': str(orden_data.get('direccion_id')) if orden_data.get('direccion_id') else None,
                    'cantidad': cantidad,
                    'precio_unitario': float(precio_unitario),
                    'precio_total': float(precio_total),
                    'metodo_pago': orden_data.get('metodo_pago', 'efectivo'),
                    'info_pago_json': info_pago_json,
                    'notas': orden_data.get('notas'),
                    'pedido_json': orden_data.get('pedido_json'),
                    'estado': orden_data.get('estado', 'pendiente'),
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(orden_doc)
                print(f"  ✅ Orden guardada en MongoDB con ID: {result.inserted_id}")
                print("="*60)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"❌ Error al crear orden: {str(e)}")
            print("="*60)
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_orden(cls, orden_id, update_data):
        """Actualizar orden"""
        try:
            if DB_TYPE == 'mysql':
                orden = OrdenSQL.query.get(orden_id)
                if not orden:
                    return False
                
                campos = [
                    'nombre_usuario', 'telefono_usuario', 'estado',
                    'tipo_pedido', 'suplemento_id', 'cantidad',
                    'precio_unitario', 'precio_total', 'direccion_texto', 
                    'direccion_id', 'pedido_json', 'metodo_pago', 
                    'info_pago_json', 'notas'
                ]
                
                for campo in campos:
                    if campo in update_data:
                        setattr(orden, campo, update_data[campo])
                
                if 'cantidad' in update_data or 'precio_unitario' in update_data:
                    cantidad = update_data.get('cantidad', orden.cantidad)
                    precio_unitario = update_data.get('precio_unitario', orden.precio_unitario)
                    orden.precio_total = cantidad * precio_unitario
                
                orden.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                
                if 'precio_unitario' in update_data:
                    update_data['precio_unitario'] = float(update_data['precio_unitario'])
                
                if 'cantidad' in update_data or 'precio_unitario' in update_data:
                    orden_actual = cls.find_by_id(orden_id)
                    if orden_actual:
                        cantidad = update_data.get('cantidad', orden_actual.get('cantidad', 1))
                        precio_unitario = update_data.get('precio_unitario', orden_actual.get('precio_unitario', 0))
                        update_data['precio_total'] = float(cantidad * precio_unitario)
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(orden_id)},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_orden: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def find_by_id(cls, orden_id):
        try:
            if DB_TYPE == 'mysql':
                return OrdenSQL.query.get(orden_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(orden_id)})
        except:
            return None
    
    @classmethod
    def find_by_codigo(cls, codigo):
        try:
            if DB_TYPE == 'mysql':
                return OrdenSQL.query.filter_by(codigo_unico=codigo).first()
            else:
                return cls._get_collection().find_one({'codigo_unico': codigo})
        except:
            return None
    
    @classmethod
    def get_all_ordenes(cls):
        try:
            if DB_TYPE == 'mysql':
                return OrdenSQL.query.order_by(OrdenSQL.fecha_creacion.desc()).all()
            else:
                return list(cls._get_collection().find().sort('fecha_creacion', -1))
        except:
            return []
    
    @classmethod
    def get_ordenes_by_estado(cls, estado):
        try:
            if DB_TYPE == 'mysql':
                return OrdenSQL.query.filter_by(estado=estado).order_by(OrdenSQL.fecha_creacion.desc()).all()
            else:
                return list(cls._get_collection().find({'estado': estado}).sort('fecha_creacion', -1))
        except:
            return []
    
    @classmethod
    def get_ordenes_by_usuario(cls, telefono):
        try:
            if DB_TYPE == 'mysql':
                return OrdenSQL.query.filter_by(telefono_usuario=telefono).order_by(OrdenSQL.fecha_creacion.desc()).all()
            else:
                return list(cls._get_collection().find({'telefono_usuario': telefono}).sort('fecha_creacion', -1))
        except:
            return []
    
    @classmethod
    def delete_orden(cls, orden_id):
        try:
            if DB_TYPE == 'mysql':
                orden = OrdenSQL.query.get(orden_id)
                if not orden:
                    return False
                
                db_sql.session.delete(orden)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(orden_id)})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_orden: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def cambiar_estado(cls, orden_id, nuevo_estado):
        try:
            if nuevo_estado not in cls.ESTADOS:
                return False
                
            if DB_TYPE == 'mysql':
                orden = OrdenSQL.query.get(orden_id)
                if not orden:
                    return False
                
                orden.estado = nuevo_estado
                orden.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(orden_id)},
                    {'$set': {'estado': nuevo_estado, 'fecha_actualizacion': datetime.utcnow()}}
                )
                return result.modified_count > 0
        except:
            return False
    
    @classmethod
    def search_ordenes(cls, query):
        try:
            if DB_TYPE == 'mysql':
                if query:
                    return OrdenSQL.query.filter(
                        (OrdenSQL.nombre_usuario.ilike(f'%{query}%')) | 
                        (OrdenSQL.telefono_usuario.ilike(f'%{query}%')) |
                        (OrdenSQL.codigo_unico.ilike(f'%{query}%'))
                    ).order_by(OrdenSQL.fecha_creacion.desc()).all()
                return OrdenSQL.query.order_by(OrdenSQL.fecha_creacion.desc()).all()
                
            else:
                import re
                if query:
                    regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                    return list(cls._get_collection().find({
                        '$or': [
                            {'nombre_usuario': {'$regex': regex}},
                            {'telefono_usuario': {'$regex': regex}},
                            {'codigo_unico': {'$regex': regex}}
                        ]
                    }).sort('fecha_creacion', -1))
                return list(cls._get_collection().find().sort('fecha_creacion', -1))
        except:
            return []
    
    @classmethod
    def get_estadisticas(cls):
        try:
            ordenes = cls.get_all_ordenes()
            
            total_ordenes = len(ordenes)
            total_ingresos = 0
            ordenes_por_estado = {estado: 0 for estado in cls.ESTADOS}
            
            for orden in ordenes:
                if DB_TYPE == 'mysql':
                    total_ingresos += float(orden.precio_total)
                    ordenes_por_estado[orden.estado] = ordenes_por_estado.get(orden.estado, 0) + 1
                else:
                    total_ingresos += orden.get('precio_total', 0)
                    estado = orden.get('estado', 'pendiente')
                    ordenes_por_estado[estado] = ordenes_por_estado.get(estado, 0) + 1
            
            return {
                'total_ordenes': total_ordenes,
                'total_ingresos': round(total_ingresos, 2),
                'ordenes_por_estado': ordenes_por_estado
            }
        except:
            return {
                'total_ordenes': 0,
                'total_ingresos': 0,
                'ordenes_por_estado': {}
            }
    
    @classmethod
    def to_dict(cls, orden):
        if not orden:
            return None
        
        if DB_TYPE == 'mysql':
            from Models.Suplementos import Suplemento
            
            suplemento_info = None
            if orden.suplemento_id:
                suplemento = Suplemento.find_by_id(orden.suplemento_id)
                if suplemento:
                    suplemento_info = Suplemento.to_dict(suplemento)
            
            info_pago = None
            if orden.info_pago_json:
                try:
                    info_pago = json.loads(orden.info_pago_json)
                except:
                    info_pago = {'error': 'Error al parsear datos de pago'}
            
            precio_total_val = float(orden.precio_total) if orden.precio_total else 0.0
            
            return {
                'id': orden.id,
                'codigo_unico': orden.codigo_unico,
                'nombre_usuario': orden.nombre_usuario,
                'telefono_usuario': orden.telefono_usuario,
                'tipo_pedido': orden.tipo_pedido,
                'suplemento': suplemento_info,
                'direccion_texto': orden.direccion_texto,
                'direccion_id': orden.direccion_id,
                'cantidad': orden.cantidad,
                'precio_unitario': float(orden.precio_unitario) if orden.precio_unitario else 0.0,
                'precio_total': precio_total_val,
                'precio': precio_total_val,
                'metodo_pago': orden.metodo_pago,
                'info_pago': info_pago,
                'notas': orden.notas,
                'pedido_json': orden.pedido_json,
                'estado': orden.estado,
                'estado_nombre': cls.ESTADOS.get(orden.estado, orden.estado),
                'fecha_creacion': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
                'fecha_actualizacion': orden.fecha_actualizacion.isoformat() if orden.fecha_actualizacion else None
            }
            
        else:
            from bson.objectid import ObjectId
            from Models.Suplementos import Suplemento
            
            orden_dict = dict(orden)
            orden_dict['id'] = str(orden_dict.pop('_id'))
            
            if 'suplemento_id' in orden_dict and orden_dict['suplemento_id']:
                suplemento = Suplemento.find_by_id(orden_dict['suplemento_id'])
                if suplemento:
                    orden_dict['suplemento'] = Suplemento.to_dict(suplemento)
                else:
                    orden_dict['suplemento'] = None
            
            for campo in ['precio_unitario', 'precio_total']:
                if campo in orden_dict:
                    orden_dict[campo] = float(orden_dict[campo])
            
            if 'precio_total' in orden_dict:
                orden_dict['precio'] = float(orden_dict['precio_total'])
            
            if 'info_pago_json' in orden_dict and orden_dict['info_pago_json']:
                try:
                    orden_dict['info_pago'] = json.loads(orden_dict['info_pago_json'])
                except:
                    orden_dict['info_pago'] = None
            else:
                orden_dict['info_pago'] = None
            
            if 'estado' in orden_dict:
                orden_dict['estado_nombre'] = cls.ESTADOS.get(orden_dict['estado'], orden_dict['estado'])
            
            if 'fecha_creacion' in orden_dict and orden_dict['fecha_creacion']:
                if isinstance(orden_dict['fecha_creacion'], datetime):
                    orden_dict['fecha_creacion'] = orden_dict['fecha_creacion'].isoformat()
            
            if 'fecha_actualizacion' in orden_dict and orden_dict['fecha_actualizacion']:
                if isinstance(orden_dict['fecha_actualizacion'], datetime):
                    orden_dict['fecha_actualizacion'] = orden_dict['fecha_actualizacion'].isoformat()
            
            return orden_dict