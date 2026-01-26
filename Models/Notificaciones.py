from config import db
from datetime import datetime

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # ID del usuario (admin o cliente)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin' o 'cliente'
    tipo = db.Column(db.String(50), nullable=False)  # 'nuevo_pedido', 'estado_cambiado', 'estado_pedido', etc.
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leida = db.Column(db.Boolean, default=False)
    datos_adicionales = db.Column(db.JSON, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_leida = db.Column(db.DateTime, nullable=True)
    
    # Relación con orden (opcional)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=True)
    
    @classmethod
    def crear_notificacion(cls, user_id, user_type, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear una nueva notificación"""
        print(f"\n🔔 [MODELO] Creando notificación:")
        print(f"   - user_id: {user_id}")
        print(f"   - user_type: {user_type}")
        print(f"   - tipo: {tipo}")
        print(f"   - titulo: {titulo}")
        
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
        
        print(f"✅ [MODELO] Notificación creada - ID: {notificacion.id}")
        return notificacion
    
    @classmethod
    def crear_notificacion_admin(cls, admin_id, tipo, titulo, mensaje, datos_adicionales=None, orden_id=None):
        """Crear notificación para un administrador específico"""
        print(f"\n📋 [MODELO] Creando notificación para ADMIN ID: {admin_id}")
        return cls.crear_notificacion(
            user_id=admin_id,  # ID del administrador
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
            user_id=cliente_id,  # ID del cliente
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
        clientes = User.query.filter_by(rol=2).all()
        
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
        """Crear notificaciones cuando se hace un nuevo pedido"""
        print(f"\n📦 [MODELO] NOTIFICAR NUEVO PEDIDO - Orden {orden.id}")
        print(f"   - Código: {orden.codigo_unico}")
        print(f"   - Cliente: {orden.nombre_usuario}")
        print(f"   - Teléfono: {orden.telefono_usuario}")
        print(f"   - Precio: ${orden.precio}")
        
        # Extraer ingredientes del pedido
        ingredientes_desc = "Sin detalles"
        if orden.tipo_pedido == 'especial' and orden.especial_nombre:
            ingredientes_desc = f"Especial: {orden.especial_nombre}"
        elif orden.tipo_pedido == 'personalizado' and orden.ingredientes_personalizados:
            ingredientes_desc = f"Personalizado: {orden.ingredientes_personalizados}"
        else:
            ingredientes_desc = "Pedido personalizado"
        
        print(f"   - Ingredientes: {ingredientes_desc}")
        
        # Datos comunes para todas las notificaciones
        datos_comunes = {
            'orden_id': orden.id,
            'codigo_pedido': orden.codigo_unico,
            'cliente_nombre': orden.nombre_usuario,
            'telefono_cliente': orden.telefono_usuario,
            'precio': float(orden.precio) if orden.precio else 0.0,
            'tipo_pedido': orden.tipo_pedido,
            'ingredientes': ingredientes_desc,
            'fecha_pedido': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None
        }
        
        notificaciones_creadas = []
        
        # 1. NOTIFICACIONES PARA TODOS LOS ADMINISTRADORES
        from Models.User import User
        admins = User.query.filter_by(rol=1).all()
        print(f"\n👥 Administradores encontrados: {len(admins)}")
        
        for admin in admins:
            print(f"\n📤 Creando notificación para ADMIN {admin.id}...")
            
            # Mensaje para admin
            mensaje_admin = f"Nuevo pedido de {orden.nombre_usuario} ({orden.telefono_usuario})\n"
            mensaje_admin += f"Pedido: {ingredientes_desc}\n"
            mensaje_admin += f"Total: ${float(orden.precio):.2f}" if orden.precio else "Total: Pendiente"
            
            # Título corto para admin
            titulo_admin = f"Pedido #{orden.codigo_unico}"
            
            notif_admin = cls.crear_notificacion_admin(
                admin_id=admin.id,
                tipo='nuevo_pedido',  # Tipo específico para admin
                titulo=titulo_admin,
                mensaje=mensaje_admin,
                datos_adicionales=datos_comunes,
                orden_id=orden.id
            )
            notificaciones_creadas.append(notif_admin)
            print(f"✅ Notificación admin creada: ID {notif_admin.id}")
        
        # 2. NOTIFICACIÓN PARA EL CLIENTE
        print(f"\n🔍 Buscando usuario CLIENTE con teléfono: {orden.telefono_usuario}")
        usuario_cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
        
        if usuario_cliente:
            print(f"✅ Cliente encontrado:")
            print(f"   - ID: {usuario_cliente.id}")
            print(f"   - Nombre: {usuario_cliente.nombre}")
            print(f"   - Teléfono: {usuario_cliente.telefono}")
            
            # Mensaje para cliente
            mensaje_cliente = f"¡Hola {orden.nombre_usuario}!\n"
            mensaje_cliente += f"Tu pedido ({ingredientes_desc}) ha sido recibido correctamente.\n"
            mensaje_cliente += f"Código de pedido: {orden.codigo_unico}\n"
            mensaje_cliente += f"Total: ${float(orden.precio):.2f}" if orden.precio else ""
            mensaje_cliente += "\n\nTe notificaremos cuando haya actualizaciones."
            
            # Título para cliente
            titulo_cliente = f"Pedido recibido: {ingredientes_desc[:30]}..."
            
            print(f"\n📤 Creando notificación para CLIENTE {usuario_cliente.id}...")
            notif_cliente = cls.crear_notificacion_cliente(
                cliente_id=usuario_cliente.id,
                tipo='estado_pedido',  # Tipo específico para cliente
                titulo=titulo_cliente,
                mensaje=mensaje_cliente,
                datos_adicionales=datos_comunes,
                orden_id=orden.id
            )
            notificaciones_creadas.append(notif_cliente)
            print(f"✅ Notificación cliente creada: ID {notif_cliente.id}")
            print(f"   - user_id asignado: {usuario_cliente.id}")
            print(f"   - user_type: cliente")
            print(f"   - tipo: estado_pedido")
        else:
            print(f"⚠️ No se encontró usuario cliente con teléfono: {orden.telefono_usuario}")
            print("   Se creará notificación con user_id=None para asignación posterior")
            
            # Mensaje para cliente (sin user_id por ahora)
            mensaje_cliente = f"¡Hola {orden.nombre_usuario}!\n"
            mensaje_cliente += f"Tu pedido ({ingredientes_desc}) ha sido recibido correctamente.\n"
            mensaje_cliente += f"Código de pedido: {orden.codigo_unico}\n"
            mensaje_cliente += f"Total: ${float(orden.precio):.2f}" if orden.precio else ""
            mensaje_cliente += "\n\nTe notificaremos cuando haya actualizaciones."
            
            titulo_cliente = f"Pedido recibido: {ingredientes_desc[:30]}..."
            
            # Crear notificación sin user_id (se asignará cuando el usuario inicie sesión)
            notif_cliente = cls.crear_notificacion(
                user_id=None,  # Sin ID por ahora
                user_type='cliente',
                tipo='estado_pedido',
                titulo=titulo_cliente,
                mensaje=mensaje_cliente,
                datos_adicionales={**datos_comunes, 'telefono_cliente': orden.telefono_usuario},
                orden_id=orden.id
            )
            notificaciones_creadas.append(notif_cliente)
            print(f"✅ Notificación cliente creada sin user_id: ID {notif_cliente.id}")
            print(f"   - user_id: None (se asignará por teléfono)")
            print(f"   - user_type: cliente")
            print(f"   - tipo: estado_pedido")
            print(f"   - telefono_cliente guardado: {orden.telefono_usuario}")
        
        print(f"\n✅ [MODELO] TOTAL notificaciones creadas: {len(notificaciones_creadas)}")
        print("   - Para admins: tipo 'nuevo_pedido'")
        print("   - Para cliente: tipo 'estado_pedido'")
        
        return notificaciones_creadas
    
    @classmethod
    def notificar_cambio_estado(cls, orden, nuevo_estado):
        """Crear notificaciones cuando cambia el estado de un pedido"""
        try:
            print(f"\n🔔 [MODELO] NOTIFICAR CAMBIO ESTADO ======")
            print(f"📦 Orden ID: {orden.id}")
            print(f"📦 Código: {orden.codigo_unico}")
            print(f"📦 Cliente: {orden.nombre_usuario}")
            print(f"📦 Teléfono: '{orden.telefono_usuario}'")
            print(f"📦 Estado anterior: {orden.estado}")
            print(f"📦 Estado nuevo: {nuevo_estado}")
            
            estados_espanol = {
                'pendiente': 'Pendiente',
                'preparando': 'En Preparación',
                'listo': 'Listo para Recoger',
                'entregado': 'Entregado',
                'cancelado': 'Cancelado'
            }
            
            titulo_estado = estados_espanol.get(nuevo_estado, nuevo_estado)
            
            # Extraer ingredientes del pedido
            ingredientes_desc = "Sin detalles"
            if orden.tipo_pedido == 'especial' and orden.especial_nombre:
                ingredientes_desc = f"Especial: {orden.especial_nombre}"
            elif orden.tipo_pedido == 'personalizado' and orden.ingredientes_personalizados:
                ingredientes_desc = f"Personalizado: {orden.ingredientes_personalizados}"
            else:
                ingredientes_desc = "Pedido personalizado"
            
            print(f"📦 Ingredientes: {ingredientes_desc}")
            
            # Datos comunes
            datos_comunes = {
                'orden_id': orden.id,
                'codigo_pedido': orden.codigo_unico,
                'cliente_nombre': orden.nombre_usuario,
                'telefono_cliente': orden.telefono_usuario,
                'estado_anterior': orden.estado,
                'estado_nuevo': nuevo_estado,
                'ingredientes': ingredientes_desc,
                'precio': float(orden.precio) if orden.precio else 0.0
            }
            
            notificaciones_creadas = []
            
            # 1. NOTIFICACIONES PARA TODOS LOS ADMINISTRADORES
            from Models.User import User
            admins = User.query.filter_by(rol=1).all()
            
            for admin in admins:
                print(f"\n📤 Creando notificación para ADMIN {admin.id}...")
                
                mensaje_admin = f"Pedido {orden.codigo_unico} de {orden.nombre_usuario}\n"
                mensaje_admin += f"Cambió de '{orden.estado}' a '{titulo_estado}'"
                
                titulo_admin = f"Estado actualizado: {titulo_estado}"
                
                notif_admin = cls.crear_notificacion_admin(
                    admin_id=admin.id,
                    tipo='estado_cambiado',  # Tipo específico para admin
                    titulo=titulo_admin,
                    mensaje=mensaje_admin,
                    datos_adicionales=datos_comunes,
                    orden_id=orden.id
                )
                notificaciones_creadas.append(notif_admin)
                print(f"✅ Notificación admin creada: ID {notif_admin.id}")
            
            # 2. NOTIFICACIÓN PARA EL CLIENTE
            print(f"\n🔍 Buscando usuario CLIENTE con teléfono: '{orden.telefono_usuario}'")
            usuario_cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
            
            if usuario_cliente:
                print(f"✅ Cliente encontrado: ID {usuario_cliente.id}")
                
                # Mensaje para cliente
                mensaje_cliente = f"Hola {orden.nombre_usuario},\n"
                mensaje_cliente += f"Tu pedido ({ingredientes_desc}) ha cambiado de estado:\n\n"
                mensaje_cliente += f"• Estado anterior: {estados_espanol.get(orden.estado, orden.estado)}\n"
                mensaje_cliente += f"• Estado nuevo: {titulo_estado}\n"
                mensaje_cliente += f"• Código: {orden.codigo_unico}\n"
                
                if nuevo_estado == 'listo':
                    mensaje_cliente += "\n¡Tu pedido está listo para ser recogido en el restaurante!"
                elif nuevo_estado == 'entregado':
                    mensaje_cliente += "\n¡Gracias por tu compra! Esperamos verte pronto."
                elif nuevo_estado == 'cancelado':
                    mensaje_cliente += "\nLamentamos los inconvenientes. Si tienes dudas, contáctanos."
                
                titulo_cliente = f"Actualización: {titulo_estado}"
                
                print(f"\n📤 Creando notificación para CLIENTE {usuario_cliente.id}...")
                notif_cliente = cls.crear_notificacion_cliente(
                    cliente_id=usuario_cliente.id,
                    tipo='estado_pedido',  # Tipo específico para cliente
                    titulo=titulo_cliente,
                    mensaje=mensaje_cliente,
                    datos_adicionales=datos_comunes,
                    orden_id=orden.id
                )
                notificaciones_creadas.append(notif_cliente)
                print(f"✅ Notificación cliente creada: ID {notif_cliente.id}")
                print(f"   - user_id: {usuario_cliente.id}")
                print(f"   - user_type: cliente")
                print(f"   - tipo: estado_pedido")
            else:
                print(f"⚠️ Cliente no encontrado, creando notificación sin user_id")
                
                mensaje_cliente = f"Hola {orden.nombre_usuario},\n"
                mensaje_cliente += f"Tu pedido ({ingredientes_desc}) ha cambiado de estado:\n\n"
                mensaje_cliente += f"• Estado anterior: {estados_espanol.get(orden.estado, orden.estado)}\n"
                mensaje_cliente += f"• Estado nuevo: {titulo_estado}\n"
                mensaje_cliente += f"• Código: {orden.codigo_unico}\n"
                
                titulo_cliente = f"Actualización: {titulo_estado}"
                
                notif_cliente = cls.crear_notificacion(
                    user_id=None,
                    user_type='cliente',
                    tipo='estado_pedido',
                    titulo=titulo_cliente,
                    mensaje=mensaje_cliente,
                    datos_adicionales={**datos_comunes, 'telefono_cliente': orden.telefono_usuario},
                    orden_id=orden.id
                )
                notificaciones_creadas.append(notif_cliente)
                print(f"✅ Notificación cliente creada sin user_id: ID {notif_cliente.id}")
                print(f"   - user_id: None (se asignará por teléfono)")
                print(f"   - user_type: cliente")
                print(f"   - tipo: estado_pedido")
            
            print(f"\n✅ [MODELO] TOTAL notificaciones creadas: {len(notificaciones_creadas)}")
            print("   - Para admins: tipo 'estado_cambiado'")
            print("   - Para cliente: tipo 'estado_pedido'")
            
            return notificaciones_creadas
                    
        except Exception as e:
            print(f"\n❌ ERROR en notificar_cambio_estado:")
            print(f"Tipo: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    @classmethod
    def obtener_notificaciones_usuario_query(cls, user_id, user_type, pagina=1, por_pagina=20):
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
            'metadata': notificacion.datos_adicionales or {},
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