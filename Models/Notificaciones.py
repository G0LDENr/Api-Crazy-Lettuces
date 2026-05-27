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
    
    def __init__(self, user_id, user_type, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None, fecha_creacion=None):
        self.user_id = user_id
        self.user_type = user_type
        self.tipo = tipo
        self.titulo = titulo
        self.mensaje = mensaje
        self.datos_adicionales = datos_adicionales or {}
        self.orden_id = orden_id
        # CORREGIDO: aceptar fecha_creacion como parámetro
        if fecha_creacion:
            self.fecha_creacion = fecha_creacion
    
    def __repr__(self):
        return f'<Notificacion {self.id} - {self.titulo}>'


# ============================================
# CLASE PRINCIPAL
# ============================================
class Notificacion:
    """Clase que maneja notificaciones en ambas bases de datos"""
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.notificaciones
    
    # ============ MÉTODO AGREGADO ============
    @classmethod
    def find_by_id(cls, notificacion_id):
        """Buscar una notificación por ID"""
        try:
            print(f"\n🔵 [MODELO] find_by_id - Buscando notificación ID: {notificacion_id}")
            
            if DB_TYPE == 'mysql':
                notificacion = NotificacionSQL.query.get(notificacion_id)
                if notificacion:
                    print(f"✅ Notificación encontrada en MySQL - ID: {notificacion.id}")
                else:
                    print(f"❌ Notificación no encontrada en MySQL")
                return notificacion
                
            else:
                from bson.objectid import ObjectId
                notificacion = cls._get_collection().find_one({'_id': ObjectId(notificacion_id)})
                if notificacion:
                    print(f"✅ Notificación encontrada en MongoDB")
                else:
                    print(f"❌ Notificación no encontrada en MongoDB")
                return notificacion
                
        except Exception as e:
            print(f"❌ Error en find_by_id: {e}")
            return None
    
    @classmethod
    def crear_notificacion(cls, user_id, user_type, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        try:
            if DB_TYPE == 'mysql':
                notificacion = NotificacionSQL(
                    user_id=user_id,
                    user_type=user_type,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=json.dumps(datos_adicionales) if datos_adicionales else None,
                    orden_id=orden_id,
                    fecha_creacion=datetime.utcnow()  # CORREGIDO: pasar fecha_creacion correctamente
                )
                db_sql.session.add(notificacion)
                db_sql.session.commit()
                return notificacion
            else:
                notificacion_doc = {
                    'user_id': user_id,
                    'user_type': user_type,
                    'tipo': tipo,
                    'titulo': titulo,
                    'mensaje': mensaje,
                    'datos_adicionales': datos_adicionales or {},
                    'orden_id': orden_id,
                    'fecha_creacion': datetime.utcnow(),
                    'leida': False
                }
                result = cls._get_collection().insert_one(notificacion_doc)
                notificacion_doc['_id'] = result.inserted_id
                return notificacion_doc
        except Exception as e:
            print(f"Error creando notificación: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @classmethod
    def crear_notificacion_admin(cls, admin_id, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear notificación para un administrador específico"""
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
            print(f"\n🔵 [MODELO] marcar_como_leida - ID: {notificacion_id}")
            
            if DB_TYPE == 'mysql':
                notificacion = NotificacionSQL.query.get(notificacion_id)
                if notificacion and not notificacion.leida:
                    notificacion.leida = True
                    notificacion.fecha_leida = datetime.utcnow()
                    db_sql.session.commit()
                    print(f"✅ Notificación marcada como leída")
                    return True
                print(f"Notificación no encontrada o ya leída")
                return False
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(notificacion_id), 'leida': False},
                    {'$set': {'leida': True, 'fecha_leida': datetime.utcnow()}}
                )
                print(f"Resultado: modified_count={result.modified_count}")
                return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error en marcar_como_leida: {e}")
            import traceback
            traceback.print_exc()
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
    def notificar_cambio_estado(cls, orden, nuevo_estado):
        """Crear notificaciones cuando cambia el estado de un pedido"""
        try:
            from Models.User import user_repo
            orden_dict = orden.to_dict() if hasattr(orden, 'to_dict') else orden
            
            # Obtener todos los administradores
            admins = user_repo.get_users_by_role(1)
            
            notificaciones_creadas = []
            
            # Notificar a todos los administradores
            for admin in admins:
                admin_dict = user_repo.to_dict(admin)
                notif = cls.crear_notificacion_admin(
                    admin_id=admin_dict['id'],
                    tipo='cambio_estado',
                    titulo=f'Pedido {orden_dict.get("codigo_unico")}',
                    mensaje=f'El pedido cambió a estado: {nuevo_estado}',
                    datos_adicionales={'orden_id': orden_dict.get('id')},
                    orden_id=orden_dict.get('id')
                )
                if notif:
                    notificaciones_creadas.append(notif)
            
            # Notificar al cliente si está registrado
            cliente = user_repo.find_by_phone(orden_dict.get('telefono_usuario'))
            if cliente:
                cliente_dict = user_repo.to_dict(cliente)
                notif = cls.crear_notificacion_cliente(
                    cliente_id=cliente_dict['id'],
                    tipo='cambio_estado',
                    titulo=f'Tu pedido {orden_dict.get("codigo_unico")}',
                    mensaje=f'Tu pedido cambió a estado: {nuevo_estado}',
                    datos_adicionales={'orden_id': orden_dict.get('id')},
                    orden_id=orden_dict.get('id')
                )
                if notif:
                    notificaciones_creadas.append(notif)
            
            return notificaciones_creadas
            
        except Exception as e:
            print(f"Error en notificar_cambio_estado: {e}")
            return []
    
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