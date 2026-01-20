from config import db
from datetime import datetime

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # ID del usuario (admin o cliente)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin' o 'cliente'
    tipo = db.Column(db.String(50), nullable=False)  # 'nuevo_pedido', 'estado_cambiado', 'mensaje', etc.
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leida = db.Column(db.Boolean, default=False)
    datos_adicionales = db.Column(db.JSON, nullable=True)  # Cambiado de 'metadata' a 'datos_adicionales'
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_leida = db.Column(db.DateTime, nullable=True)
    
    # Relación con orden (opcional)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=True)
    
    @classmethod
    def crear_notificacion(cls, user_id, user_type, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear una nueva notificación"""
        notificacion = cls(
            user_id=user_id,
            user_type=user_type,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_adicionales=datos_adicionales or {},
            orden_id=orden_id
        )
        
        db.session.add(notificacion)
        db.session.commit()
        return notificacion
    
    @classmethod
    def crear_notificacion_admin(cls, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear notificación para el administrador (user_id=1)"""
        return cls.crear_notificacion(
            user_id=1,  # Suponiendo que el admin tiene ID 1
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
    def crear_notificacion_todos_usuarios(cls, tipo, titulo, mensaje, datos_adicionales=None):
        """Crear notificación para todos los clientes"""
        # Esta función necesitaría obtener todos los IDs de clientes
        from Models.User import User
        clientes = User.query.filter_by(role=2).all()
        
        notificaciones = []
        for cliente in clientes:
            notificacion = cls.crear_notificacion(
                user_id=cliente.id,
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
        """Crear notificación cuando se hace un nuevo pedido"""
        if orden.tipo_pedido == 'especial':
            mensaje = f"📦 Nuevo pedido especial: {orden.especial.nombre if orden.especial else 'Especial'} - ${orden.precio}"
        else:
            mensaje = f"📦 Nuevo pedido personalizado con {len(orden.ingredientes_personalizados.split(',')) if orden.ingredientes_personalizados else 0} ingredientes - ${orden.precio}"
        
        datos_adicionales = {
            'orden_id': orden.id,
            'codigo_pedido': orden.codigo_unico,
            'cliente_nombre': orden.nombre_usuario,
            'cliente_telefono': orden.telefono_usuario,
            'precio': float(orden.precio),
            'tipo_pedido': orden.tipo_pedido,
            'fecha_pedido': orden.fecha_creacion.isoformat()
        }
        
        return cls.crear_notificacion_admin(
            tipo='nuevo_pedido',
            titulo='🎯 Nuevo Pedido Recibido',
            mensaje=mensaje,
            datos_adicionales=datos_adicionales,
            orden_id=orden.id
        )
    
    @classmethod
    def notificar_cambio_estado(cls, orden, nuevo_estado):
        """Crear notificación cuando cambia el estado de un pedido"""
        estados_espanol = {
            'pendiente': '🔄 Pendiente',
            'preparando': '👨‍🍳 En Preparación',
            'listo': '✅ Listo para Recoger',
            'entregado': '🚚 Entregado',
            'cancelado': '❌ Cancelado'
        }
        
        titulo_estado = estados_espanol.get(nuevo_estado, nuevo_estado)
        
        # Notificación para el administrador
        cls.crear_notificacion_admin(
            tipo='estado_cambiado',
            titulo=f'🔄 Estado Actualizado',
            mensaje=f"Pedido {orden.codigo_unico} ahora está: {titulo_estado}",
            datos_adicionales={
                'orden_id': orden.id,
                'codigo_pedido': orden.codigo_unico,
                'estado_anterior': orden.estado,
                'estado_nuevo': nuevo_estado,
                'cliente': orden.nombre_usuario
            },
            orden_id=orden.id
        )
        
        # Notificación para el cliente
        mensaje_cliente = f"Tu pedido {orden.codigo_unico} ahora está: {titulo_estado}"
        
        if nuevo_estado == 'listo':
            mensaje_cliente += "\n¡Tu pedido está listo para ser recogido!"
        elif nuevo_estado == 'entregado':
            mensaje_cliente += "\n¡Gracias por tu compra!"
        elif nuevo_estado == 'cancelado':
            mensaje_cliente += "\nLamentamos los inconvenientes."
        
        # Buscar usuario por teléfono o crear notificación sin usuario específico
        from Models.User import User
        usuario = User.query.filter_by(telefono=orden.telefono_usuario).first()
        
        if usuario:
            cls.crear_notificacion_cliente(
                cliente_id=usuario.id,
                tipo='estado_pedido',
                titulo=f'📦 Actualización de tu Pedido',
                mensaje=mensaje_cliente,
                datos_adicionales={
                    'orden_id': orden.id,
                    'codigo_pedido': orden.codigo_unico,
                    'estado': nuevo_estado
                },
                orden_id=orden.id
            )
    
    @classmethod
    def obtener_notificaciones_usuario(cls, user_id, user_type, pagina=1, por_pagina=20):
        """Obtener notificaciones de un usuario con paginación"""
        offset = (pagina - 1) * por_pagina
        
        notificaciones = cls.query.filter_by(
            user_id=user_id,
            user_type=user_type
        ).order_by(cls.fecha_creacion.desc()).offset(offset).limit(por_pagina).all()
        
        total = cls.query.filter_by(user_id=user_id, user_type=user_type).count()
        
        return {
            'notificaciones': notificaciones,
            'total': total,
            'pagina_actual': pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina,
            'por_pagina': por_pagina
        }
    
    @classmethod
    def obtener_notificaciones_no_leidas(cls, user_id, user_type):
        """Obtener notificaciones no leídas de un usuario"""
        return cls.query.filter_by(
            user_id=user_id,
            user_type=user_type,
            leida=False
        ).order_by(cls.fecha_creacion.desc()).all()
    
    @classmethod
    def marcar_como_leida(cls, notificacion_id):
        """Marcar una notificación como leída"""
        notificacion = cls.query.get(notificacion_id)
        if notificacion and not notificacion.leida:
            notificacion.leida = True
            notificacion.fecha_leida = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @classmethod
    def marcar_todas_como_leidas(cls, user_id, user_type):
        """Marcar todas las notificaciones de un usuario como leídas"""
        notificaciones = cls.query.filter_by(
            user_id=user_id,
            user_type=user_type,
            leida=False
        ).all()
        
        for notificacion in notificaciones:
            notificacion.leida = True
            notificacion.fecha_leida = datetime.utcnow()
        
        db.session.commit()
        return len(notificaciones)
    
    @classmethod
    def eliminar_notificacion(cls, notificacion_id):
        """Eliminar una notificación"""
        notificacion = cls.query.get(notificacion_id)
        if notificacion:
            db.session.delete(notificacion)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def eliminar_todas_leidas(cls, user_id, user_type):
        """Eliminar todas las notificaciones leídas de un usuario"""
        notificaciones = cls.query.filter_by(
            user_id=user_id,
            user_type=user_type,
            leida=True
        ).all()
        
        count = 0
        for notificacion in notificaciones:
            db.session.delete(notificacion)
            count += 1
        
        db.session.commit()
        return count
    
    @classmethod
    def obtener_analiticas(cls, dias=30):
        """Obtener analíticas de notificaciones"""
        from datetime import datetime, timedelta
        import json
        
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        # Total notificaciones
        total = cls.query.filter(cls.fecha_creacion >= fecha_limite).count()
        
        # Notificaciones por tipo
        tipos = db.session.query(
            cls.tipo,
            db.func.count(cls.id).label('count')
        ).filter(cls.fecha_creacion >= fecha_limite).group_by(cls.tipo).all()
        
        distribucion_tipos = {tipo: count for tipo, count in tipos}
        
        # Notificaciones no leídas
        no_leidas = cls.query.filter(
            cls.fecha_creacion >= fecha_limite,
            cls.leida == False
        ).count()
        
        # Estadísticas por día (últimos 7 días)
        estadisticas_diarias = []
        for i in range(7):
            fecha = datetime.utcnow() - timedelta(days=i)
            fecha_inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            count = cls.query.filter(
                cls.fecha_creacion >= fecha_inicio,
                cls.fecha_creacion <= fecha_fin
            ).count()
            
            estadisticas_diarias.append({
                'fecha': fecha_inicio.strftime('%Y-%m-%d'),
                'count': count
            })
        
        estadisticas_diarias.reverse()
        
        return {
            'total_notificaciones': total,
            'distribucion_tipos': distribucion_tipos,
            'no_leidas': no_leidas,
            'tasa_lectura': ((total - no_leidas) / total * 100) if total > 0 else 0,
            'estadisticas_diarias': estadisticas_diarias,
            'periodo_analizado': f'Últimos {dias} días'
        }
    
    @classmethod
    def to_dict(cls, notificacion):
        """Convertir notificación a diccionario"""
        return {
            'id': notificacion.id,
            'user_id': notificacion.user_id,
            'user_type': notificacion.user_type,
            'tipo': notificacion.tipo,
            'titulo': notificacion.titulo,
            'mensaje': notificacion.mensaje,
            'leida': notificacion.leida,
            'metadata': notificacion.datos_adicionales or {},  # Mantenemos 'metadata' en la API
            'orden_id': notificacion.orden_id,
            'fecha_creacion': notificacion.fecha_creacion.isoformat() if notificacion.fecha_creacion else None,
            'fecha_leida': notificacion.fecha_leida.isoformat() if notificacion.fecha_leida else None,
            'hace_cuanto': cls.calcular_tiempo_transcurrido(notificacion.fecha_creacion)
        }
    
    @staticmethod
    def calcular_tiempo_transcurrido(fecha):
        """Calcular tiempo transcurrido desde la creación"""
        from datetime import datetime
        
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