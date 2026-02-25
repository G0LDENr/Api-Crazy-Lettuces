# Models/Notificaciones.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime, timedelta
import json

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class NotificacionSQL(db_sql.Model):
    __tablename__ = 'notificaciones'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    user_id = db_sql.Column(db_sql.Integer, nullable=True)
    user_type = db_sql.Column(db_sql.String(20), nullable=False)
    tipo = db_sql.Column(db_sql.String(50), nullable=False)
    titulo = db_sql.Column(db_sql.String(200), nullable=False)
    mensaje = db_sql.Column(db_sql.Text, nullable=False)
    leida = db_sql.Column(db_sql.Boolean, default=False)
    datos_adicionales = db_sql.Column(db_sql.JSON, nullable=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_leida = db_sql.Column(db_sql.DateTime, nullable=True)
    orden_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('ordenes.id'), nullable=True)
    
    def __repr__(self):
        return f'<Notificacion {self.id} - {self.titulo}>'

# ============================================
# CLASE PRINCIPAL - Usa el repositorio según DB_TYPE
# ============================================
class Notificacion:
    """Clase que maneja notificaciones en ambas bases de datos"""
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.notificaciones
    
    @classmethod
    def crear_notificacion(cls, user_id, user_type, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear una nueva notificación"""
        try:
            print(f"\n[MODELO] Creando notificación:")
            print(f"   - user_id: {user_id}")
            print(f"   - user_type: {user_type}")
            print(f"   - tipo: {tipo}")
            print(f"   - titulo: {titulo}")
            
            if DB_TYPE == 'mysql':
                notificacion = NotificacionSQL(
                    user_id=user_id,
                    user_type=user_type,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=datos_adicionales or {},
                    orden_id=orden_id
                )
                
                db_sql.session.add(notificacion)
                db_sql.session.commit()
                
                print(f"[MODELO] Notificación creada - ID: {notificacion.id}")
                return notificacion
                
            else:
                from bson.objectid import ObjectId
                
                notificacion_doc = {
                    'user_id': str(user_id) if user_id else None,
                    'user_type': user_type,
                    'tipo': tipo,
                    'titulo': titulo,
                    'mensaje': mensaje,
                    'leida': False,
                    'datos_adicionales': datos_adicionales or {},
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_leida': None,
                    'orden_id': str(orden_id) if orden_id else None
                }
                
                result = cls._get_collection().insert_one(notificacion_doc)
                notificacion_doc['id'] = str(result.inserted_id)
                
                print(f"[MODELO] Notificación creada - ID: {notificacion_doc['id']}")
                return notificacion_doc
                
        except Exception as e:
            print(f"Error en crear_notificacion: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def crear_notificacion_admin(cls, admin_id, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear notificación para un administrador específico"""
        print(f"\n[MODELO] Creando notificación para ADMIN ID: {admin_id}")
        return cls.crear_notificacion(
            user_id=admin_id,
            user_type='admin',
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_adicionales=datos_adicionales,
            orden_id=orden_id
        )
    
    @classmethod
    def crear_notificacion_cliente(cls, cliente_id, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear notificación para un cliente específico"""
        print(f"\n👤 [MODELO] Creando notificación para CLIENTE ID: {cliente_id}")
        return cls.crear_notificacion(
            user_id=cliente_id,
            user_type='cliente',
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_adicionales=datos_adicionales,
            orden_id=orden_id
        )
    
    @classmethod
    def crear_notificacion_todos_usuarios(cls, tipo, titulo, mensaje, datos_adicionales=None):
        """Crear notificación para todos los clientes"""
        from Models.User import User
        clientes = User.get_users_by_role(2)
        
        notificaciones = []
        for cliente in clientes:
            cliente_dict = User.to_dict(cliente)
            notificacion = cls.crear_notificacion(
                user_id=cliente_dict['id'],
                user_type='cliente',
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
            notificaciones.append(notificacion)
        
        return notificaciones
    
    @classmethod
    def notificar_nuevo_pedido(cls, orden):
        """Crear notificaciones cuando se hace un nuevo pedido"""
        from Models.User import User
        
        orden_dict = orden.to_dict() if hasattr(orden, 'to_dict') else orden
        
        print(f"\n[MODELO] NOTIFICAR NUEVO PEDIDO - Orden {orden_dict.get('id')}")
        
        # Extraer ingredientes
        ingredientes_desc = "Sin detalles"
        if orden_dict.get('tipo_pedido') == 'especial' and orden_dict.get('especial'):
            especial = orden_dict['especial']
            ingredientes_desc = f"Especial '{especial.get('nombre')}': {especial.get('ingredientes', '')}"
        elif orden_dict.get('ingredientes_personalizados'):
            ingredientes_desc = f"Personalizado: {orden_dict['ingredientes_personalizados']}"
        
        # Datos comunes
        datos_comunes = {
            'orden_id': orden_dict.get('id'),
            'codigo_pedido': orden_dict.get('codigo_unico'),
            'cliente_nombre': orden_dict.get('nombre_usuario'),
            'telefono_cliente': orden_dict.get('telefono_usuario'),
            'precio': float(orden_dict.get('precio', 0)),
            'tipo_pedido': orden_dict.get('tipo_pedido'),
            'ingredientes': ingredientes_desc,
            'fecha_pedido': orden_dict.get('fecha_creacion')
        }
        
        notificaciones_creadas = []
        
        # 1. Notificaciones para administradores
        admins = User.get_users_by_role(1)
        print(f"\n👥 Administradores encontrados: {len(admins)}")
        
        for admin in admins:
            admin_dict = User.to_dict(admin)
            
            mensaje_admin = f"Nuevo pedido de {orden_dict.get('nombre_usuario')}\n"
            mensaje_admin += f"Pedido: {ingredientes_desc}\n"
            
            titulo_admin = f"Pedido #{orden_dict.get('codigo_unico')}"
            
            notif_admin = cls.crear_notificacion_admin(
                admin_id=admin_dict['id'],
                tipo='nuevo_pedido',
                titulo=titulo_admin,
                mensaje=mensaje_admin,
                datos_adicionales=datos_comunes,
                orden_id=orden_dict.get('id')
            )
            notificaciones_creadas.append(notif_admin)
        
        # 2. Notificación para el cliente
        clientes = User.get_users_by_role(2)
        usuario_cliente = None
        for cliente in clientes:
            cliente_dict = User.to_dict(cliente)
            if cliente_dict.get('telefono') == orden_dict.get('telefono_usuario'):
                usuario_cliente = cliente_dict
                break
        
        if usuario_cliente:
            mensaje_cliente = f"¡Hola {orden_dict.get('nombre_usuario')}!\n"
            mensaje_cliente += f"Tu pedido ({ingredientes_desc}) ha sido recibido.\n"
            mensaje_cliente += f"Código: {orden_dict.get('codigo_unico')}"
            
            notif_cliente = cls.crear_notificacion_cliente(
                cliente_id=usuario_cliente['id'],
                tipo='estado_pedido',
                titulo="Pedido recibido",
                mensaje=mensaje_cliente,
                datos_adicionales=datos_comunes,
                orden_id=orden_dict.get('id')
            )
            notificaciones_creadas.append(notif_cliente)
        
        return notificaciones_creadas
    
    @classmethod
    def notificar_cambio_estado(cls, orden, nuevo_estado):
        """Crear notificaciones cuando cambia el estado de un pedido"""
        from Models.User import User
        
        orden_dict = orden.to_dict() if hasattr(orden, 'to_dict') else orden
        
        estados_espanol = {
            'pendiente': 'Pendiente',
            'preparando': 'En Preparación',
            'listo': 'Listo para Recoger',
            'entregado': 'Entregado',
            'cancelado': 'Cancelado'
        }
        
        titulo_estado = estados_espanol.get(nuevo_estado, nuevo_estado)
        
        # Extraer ingredientes
        ingredientes_desc = "Sin detalles"
        if orden_dict.get('tipo_pedido') == 'especial' and orden_dict.get('especial'):
            especial = orden_dict['especial']
            ingredientes_desc = f"Especial '{especial.get('nombre')}': {especial.get('ingredientes', '')}"
        elif orden_dict.get('ingredientes_personalizados'):
            ingredientes_desc = f"Personalizado: {orden_dict['ingredientes_personalizados']}"
        
        datos_comunes = {
            'orden_id': orden_dict.get('id'),
            'codigo_pedido': orden_dict.get('codigo_unico'),
            'cliente_nombre': orden_dict.get('nombre_usuario'),
            'telefono_cliente': orden_dict.get('telefono_usuario'),
            'estado_anterior': orden_dict.get('estado'),
            'estado_nuevo': nuevo_estado,
            'ingredientes': ingredientes_desc
        }
        
        notificaciones_creadas = []
        
        # 1. Notificaciones para administradores
        admins = User.get_users_by_role(1)
        for admin in admins:
            admin_dict = User.to_dict(admin)
            
            mensaje_admin = f"Pedido {orden_dict.get('codigo_unico')} cambió a '{titulo_estado}'"
            
            notif_admin = cls.crear_notificacion_admin(
                admin_id=admin_dict['id'],
                tipo='estado_cambiado',
                titulo=f"Estado: {titulo_estado}",
                mensaje=mensaje_admin,
                datos_adicionales=datos_comunes,
                orden_id=orden_dict.get('id')
            )
            notificaciones_creadas.append(notif_admin)
        
        # 2. Notificación para el cliente
        clientes = User.get_users_by_role(2)
        usuario_cliente = None
        for cliente in clientes:
            cliente_dict = User.to_dict(cliente)
            if cliente_dict.get('telefono') == orden_dict.get('telefono_usuario'):
                usuario_cliente = cliente_dict
                break
        
        if usuario_cliente:
            mensaje_cliente = f"Hola {orden_dict.get('nombre_usuario')},\n"
            mensaje_cliente += f"Tu pedido cambió a: {titulo_estado}"
            
            notif_cliente = cls.crear_notificacion_cliente(
                cliente_id=usuario_cliente['id'],
                tipo='estado_pedido',
                titulo=f"Actualización: {titulo_estado}",
                mensaje=mensaje_cliente,
                datos_adicionales=datos_comunes,
                orden_id=orden_dict.get('id')
            )
            notificaciones_creadas.append(notif_cliente)
        
        return notificaciones_creadas
    
    @classmethod
    def obtener_notificaciones_usuario_query(cls, user_id, user_type, pagina=1, por_pagina=20):
        """Obtener notificaciones de un usuario con paginación"""
        try:
            offset = (pagina - 1) * por_pagina
            
            if DB_TYPE == 'mysql':
                query = NotificacionSQL.query.filter_by(
                    user_id=user_id,
                    user_type=user_type
                ).order_by(NotificacionSQL.fecha_creacion.desc())
                
                total = query.count()
                notificaciones = query.offset(offset).limit(por_pagina).all()
                
            else:
                cursor = cls._get_collection().find({
                    'user_id': str(user_id),
                    'user_type': user_type
                }).sort('fecha_creacion', -1).skip(offset).limit(por_pagina)
                
                notificaciones = list(cursor)
                total = cls._get_collection().count_documents({
                    'user_id': str(user_id),
                    'user_type': user_type
                })
            
            return {
                'notificaciones': notificaciones,
                'total': total,
                'pagina_actual': pagina,
                'total_paginas': (total + por_pagina - 1) // por_pagina,
                'por_pagina': por_pagina
            }
        except Exception as e:
            print(f"Error en obtener_notificaciones_usuario_query: {e}")
            return {'notificaciones': [], 'total': 0, 'pagina_actual': pagina, 'total_paginas': 0, 'por_pagina': por_pagina}
    
    @classmethod
    def obtener_notificaciones_no_leidas(cls, user_id, user_type):
        """Obtener notificaciones no leídas de un usuario"""
        try:
            if DB_TYPE == 'mysql':
                return NotificacionSQL.query.filter_by(
                    user_id=user_id,
                    user_type=user_type,
                    leida=False
                ).order_by(NotificacionSQL.fecha_creacion.desc()).all()
                
            else:
                return list(cls._get_collection().find({
                    'user_id': str(user_id),
                    'user_type': user_type,
                    'leida': False
                }).sort('fecha_creacion', -1))
        except:
            return []
    
    @classmethod
    def marcar_como_leida(cls, notificacion_id):
        """Marcar una notificación como leída"""
        try:
            if DB_TYPE == 'mysql':
                notificacion = NotificacionSQL.query.get(notificacion_id)
                if notificacion and not notificacion.leida:
                    notificacion.leida = True
                    notificacion.fecha_leida = datetime.utcnow()
                    db_sql.session.commit()
                    return True
                return False
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(notificacion_id), 'leida': False},
                    {'$set': {'leida': True, 'fecha_leida': datetime.utcnow()}}
                )
                return result.modified_count > 0
        except:
            return False
    
    @classmethod
    def marcar_todas_como_leidas(cls, user_id, user_type):
        """Marcar todas las notificaciones de un usuario como leídas"""
        try:
            if DB_TYPE == 'mysql':
                result = NotificacionSQL.query.filter_by(
                    user_id=user_id,
                    user_type=user_type,
                    leida=False
                ).update({
                    'leida': True,
                    'fecha_leida': datetime.utcnow()
                })
                db_sql.session.commit()
                return result
                
            else:
                result = cls._get_collection().update_many(
                    {'user_id': str(user_id), 'user_type': user_type, 'leida': False},
                    {'$set': {'leida': True, 'fecha_leida': datetime.utcnow()}}
                )
                return result.modified_count
        except:
            return 0
    
    @classmethod
    def eliminar_notificacion(cls, notificacion_id):
        """Eliminar una notificación"""
        try:
            if DB_TYPE == 'mysql':
                notificacion = NotificacionSQL.query.get(notificacion_id)
                if notificacion:
                    db_sql.session.delete(notificacion)
                    db_sql.session.commit()
                    return True
                return False
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(notificacion_id)})
                return result.deleted_count > 0
        except:
            return False
    
    @classmethod
    def eliminar_todas_leidas(cls, user_id, user_type):
        """Eliminar todas las notificaciones leídas de un usuario"""
        try:
            if DB_TYPE == 'mysql':
                result = NotificacionSQL.query.filter_by(
                    user_id=user_id,
                    user_type=user_type,
                    leida=True
                ).delete()
                db_sql.session.commit()
                return result
                
            else:
                result = cls._get_collection().delete_many({
                    'user_id': str(user_id),
                    'user_type': user_type,
                    'leida': True
                })
                return result.deleted_count
        except:
            return 0
    
    @classmethod
    def obtener_analiticas(cls, dias=30):
        """Obtener analíticas de notificaciones"""
        try:
            fecha_limite = datetime.utcnow() - timedelta(days=dias)
            
            if DB_TYPE == 'mysql':
                total = NotificacionSQL.query.filter(NotificacionSQL.fecha_creacion >= fecha_limite).count()
                
                tipos = db_sql.session.query(
                    NotificacionSQL.tipo,
                    db_sql.func.count(NotificacionSQL.id).label('count')
                ).filter(NotificacionSQL.fecha_creacion >= fecha_limite).group_by(NotificacionSQL.tipo).all()
                
                distribucion_tipos = {tipo: count for tipo, count in tipos}
                
                no_leidas = NotificacionSQL.query.filter(
                    NotificacionSQL.fecha_creacion >= fecha_limite,
                    NotificacionSQL.leida == False
                ).count()
                
            else:
                pipeline = [
                    {'$match': {'fecha_creacion': {'$gte': fecha_limite}}},
                    {'$group': {
                        '_id': '$tipo',
                        'count': {'$sum': 1}
                    }}
                ]
                result = list(cls._get_collection().aggregate(pipeline))
                distribucion_tipos = {r['_id']: r['count'] for r in result}
                
                total = sum(distribucion_tipos.values())
                
                no_leidas = cls._get_collection().count_documents({
                    'fecha_creacion': {'$gte': fecha_limite},
                    'leida': False
                })
            
            return {
                'total_notificaciones': total,
                'distribucion_tipos': distribucion_tipos,
                'no_leidas': no_leidas,
                'tasa_lectura': ((total - no_leidas) / total * 100) if total > 0 else 0,
                'periodo_analizado': f'Últimos {dias} días'
            }
        except Exception as e:
            print(f"Error en obtener_analiticas: {e}")
            return {}
    
    @classmethod
    def to_dict(cls, notificacion):
        """Convertir notificación a diccionario"""
        if not notificacion:
            return None
        
        if DB_TYPE == 'mysql':
            return {
                'id': notificacion.id,
                'user_id': notificacion.user_id,
                'user_type': notificacion.user_type,
                'tipo': notificacion.tipo,
                'titulo': notificacion.titulo,
                'mensaje': notificacion.mensaje,
                'leida': notificacion.leida,
                'metadata': notificacion.datos_adicionales or {},
                'orden_id': notificacion.orden_id,
                'fecha_creacion': notificacion.fecha_creacion.isoformat() if notificacion.fecha_creacion else None,
                'fecha_leida': notificacion.fecha_leida.isoformat() if notificacion.fecha_leida else None,
                'hace_cuanto': cls.calcular_tiempo_transcurrido(notificacion.fecha_creacion)
            }
        else:
            from bson.objectid import ObjectId
            notif_dict = dict(notificacion)
            notif_dict['id'] = str(notif_dict.pop('_id'))
            
            if 'user_id' in notif_dict and notif_dict['user_id']:
                try:
                    notif_dict['user_id'] = int(notif_dict['user_id'])
                except:
                    pass
            
            if 'fecha_creacion' in notif_dict and notif_dict['fecha_creacion']:
                if isinstance(notif_dict['fecha_creacion'], datetime):
                    notif_dict['fecha_creacion'] = notif_dict['fecha_creacion'].isoformat()
                    notif_dict['hace_cuanto'] = cls.calcular_tiempo_transcurrido(notificacion['fecha_creacion'])
            
            if 'fecha_leida' in notif_dict and notif_dict['fecha_leida']:
                if isinstance(notif_dict['fecha_leida'], datetime):
                    notif_dict['fecha_leida'] = notif_dict['fecha_leida'].isoformat()
            
            return notif_dict
    
    @staticmethod
    def calcular_tiempo_transcurrido(fecha):
        """Calcular tiempo transcurrido desde la creación"""
        if not fecha:
            return ""
        
        ahora = datetime.utcnow()
        diferencia = ahora - fecha
        
        if diferencia.days > 0:
            return f"Hace {diferencia.days} día{'s' if diferencia.days > 1 else ''}"
        elif diferencia.seconds >= 3600:
            horas = diferencia.seconds // 3600
            return f"Hace {horas} hora{'s' if horas > 1 else ''}"
        elif diferencia.seconds >= 60:
            minutos = diferencia.seconds // 60
            return f"Hace {minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            return "Hace unos segundos"

# Para compatibilidad con código existente
if DB_TYPE == 'mysql':
    NotificacionSQL = Notificacion