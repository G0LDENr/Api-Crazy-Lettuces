from Models.Notificaciones import Notificacion
from Models.Ordenes import Orden
from Models.User import User
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

def obtener_notificaciones_usuario():
    """Obtener notificaciones del usuario actual"""
    try:
        # Obtener usuario del token JWT
        user_id = get_jwt_identity()
        
        # Obtener parámetros de paginación
        pagina = request.args.get('page', 1, type=int)
        por_pagina = request.args.get('per_page', 20, type=int)
        user_type = request.args.get('user_type', 'cliente')
        
        # Obtener notificaciones
        resultado = Notificacion.obtener_notificaciones_usuario(
            user_id=user_id,
            user_type=user_type,
            pagina=pagina,
            por_pagina=por_pagina
        )
        
        # Convertir a diccionario
        notificaciones_dict = [
            Notificacion.to_dict(notif) for notif in resultado['notificaciones']
        ]
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total_notificaciones': resultado['total'],
            'pagina_actual': resultado['pagina_actual'],
            'total_paginas': resultado['total_paginas'],
            'por_pagina': resultado['por_pagina']
        }), 200
        
    except Exception as error:
        print(f"Error al obtener notificaciones: {error}")
        return jsonify({"msg": "Error al obtener notificaciones"}), 500

def obtener_notificaciones_no_leidas():
    """Obtener notificaciones no leídas del usuario"""
    try:
        user_id = get_jwt_identity()
        user_type = request.args.get('user_type', 'cliente')
        
        notificaciones = Notificacion.obtener_notificaciones_no_leidas(user_id, user_type)
        notificaciones_dict = [Notificacion.to_dict(notif) for notif in notificaciones]
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total_no_leidas': len(notificaciones_dict)
        }), 200
        
    except Exception as error:
        print(f"Error al obtener notificaciones no leídas: {error}")
        return jsonify({"msg": "Error al obtener notificaciones no leídas"}), 500

def marcar_como_leida(notificacion_id):
    """Marcar una notificación como leída"""
    try:
        user_id = get_jwt_identity()
        
        # Verificar que la notificación pertenece al usuario
        notificacion = Notificacion.query.get(notificacion_id)
        if not notificacion:
            return jsonify({"msg": "Notificación no encontrada"}), 404
        
        if notificacion.user_id != user_id:
            return jsonify({"msg": "No tienes permiso para marcar esta notificación"}), 403
        
        if Notificacion.marcar_como_leida(notificacion_id):
            return jsonify({"msg": "Notificación marcada como leída"}), 200
        else:
            return jsonify({"msg": "La notificación ya estaba leída"}), 200
            
    except Exception as error:
        print(f"Error al marcar notificación como leída: {error}")
        return jsonify({"msg": "Error al marcar notificación como leída"}), 500

def marcar_todas_como_leidas():
    """Marcar todas las notificaciones del usuario como leídas"""
    try:
        user_id = get_jwt_identity()
        user_type = request.args.get('user_type', 'cliente')
        
        cantidad = Notificacion.marcar_todas_como_leidas(user_id, user_type)
        
        return jsonify({
            "msg": f"Se marcaron {cantidad} notificaciones como leídas"
        }), 200
        
    except Exception as error:
        print(f"Error al marcar todas las notificaciones como leídas: {error}")
        return jsonify({"msg": "Error al marcar notificaciones como leídas"}), 500

def eliminar_notificacion(notificacion_id):
    """Eliminar una notificación"""
    try:
        user_id = get_jwt_identity()
        
        # Verificar que la notificación pertenece al usuario
        notificacion = Notificacion.query.get(notificacion_id)
        if not notificacion:
            return jsonify({"msg": "Notificación no encontrada"}), 404
        
        if notificacion.user_id != user_id:
            return jsonify({"msg": "No tienes permiso para eliminar esta notificación"}), 403
        
        if Notificacion.eliminar_notificacion(notificacion_id):
            return jsonify({"msg": "Notificación eliminada correctamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar la notificación"}), 500
            
    except Exception as error:
        print(f"Error al eliminar notificación: {error}")
        return jsonify({"msg": "Error al eliminar notificación"}), 500

def eliminar_todas_leidas():
    """Eliminar todas las notificaciones leídas del usuario"""
    try:
        user_id = get_jwt_identity()
        user_type = request.args.get('user_type', 'cliente')
        
        cantidad = Notificacion.eliminar_todas_leidas(user_id, user_type)
        
        return jsonify({
            "msg": f"Se eliminaron {cantidad} notificaciones leídas"
        }), 200
        
    except Exception as error:
        print(f"Error al eliminar notificaciones leídas: {error}")
        return jsonify({"msg": "Error al eliminar notificaciones"}), 500

def enviar_mensaje():
    """Enviar mensaje/notificación a usuarios (solo admin)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No se proporcionaron datos"}), 400
        
        # Verificar que el usuario es admin
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        
        if not usuario or usuario.role != 1:
            return jsonify({"msg": "Solo los administradores pueden enviar mensajes"}), 403
        
        destinatario_tipo = data.get('destinatario_tipo')  # 'cliente', 'admin', 'todos'
        destinatario_id = data.get('destinatario_id')
        titulo = data.get('titulo', '📢 Mensaje del Administrador')
        mensaje = data.get('mensaje')
        
        if not mensaje:
            return jsonify({"msg": "El mensaje es requerido"}), 400
        
        datos_adicionales = {'remitente': usuario.nombre}
        
        notificaciones_creadas = []
        
        if destinatario_tipo == 'todos':
            # Enviar a todos los clientes
            clientes = User.query.filter_by(role=2).all()
            for cliente in clientes:
                notificacion = Notificacion.crear_notificacion_cliente(
                    cliente_id=cliente.id,
                    tipo='mensaje_admin',
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=datos_adicionales
                )
                notificaciones_creadas.append(notificacion.id)
                
        elif destinatario_tipo == 'cliente' and destinatario_id:
            # Enviar a un cliente específico
            cliente = User.query.get(destinatario_id)
            if not cliente:
                return jsonify({"msg": "Cliente no encontrado"}), 404
            
            notificacion = Notificacion.crear_notificacion_cliente(
                cliente_id=cliente.id,
                tipo='mensaje_admin',
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
            notificaciones_creadas.append(notificacion.id)
            
        elif destinatario_tipo == 'admin' and destinatario_id:
            # Enviar a otro administrador
            admin = User.query.get(destinatario_id)
            if not admin or admin.role != 1:
                return jsonify({"msg": "Administrador no encontrado"}), 404
            
            notificacion = Notificacion.crear_notificacion(
                user_id=admin.id,
                user_type='admin',
                tipo='mensaje_admin',
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
            notificaciones_creadas.append(notificacion.id)
        elif destinatario_tipo == 'admin':
            # Enviar a todos los administradores
            admins = User.query.filter_by(role=1).all()
            for admin in admins:
                notificacion = Notificacion.crear_notificacion(
                    user_id=admin.id,
                    user_type='admin',
                    tipo='mensaje_admin',
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=datos_adicionales
                )
                notificaciones_creadas.append(notificacion.id)
        
        return jsonify({
            "msg": "Mensaje enviado correctamente",
            "notificaciones_enviadas": len(notificaciones_creadas)
        }), 201
        
    except Exception as error:
        print(f"Error al enviar mensaje: {error}")
        return jsonify({"msg": "Error al enviar mensaje"}), 500

def obtener_analiticas():
    """Obtener analíticas de notificaciones (solo admin)"""
    try:
        # Verificar que el usuario es admin
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        
        if not usuario or usuario.role != 1:
            return jsonify({"msg": "Solo los administradores pueden ver analíticas"}), 403
        
        dias = request.args.get('dias', 30, type=int)
        analiticas = Notificacion.obtener_analiticas(dias)
        
        return jsonify(analiticas), 200
        
    except Exception as error:
        print(f"Error al obtener analíticas: {error}")
        return jsonify({"msg": "Error al obtener analíticas"}), 500

def obtener_usuarios_para_mensaje():
    """Obtener lista de usuarios para enviar mensajes (solo admin)"""
    try:
        # Verificar que el usuario es admin
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        
        if not usuario or usuario.rol != 1:
            return jsonify({"msg": "Solo los administradores pueden ver esta lista"}), 403
        
        # Obtener todos los usuarios
        usuarios = User.query.all()
        usuarios_dict = [
            {
                'id': user.id,
                'nombre': user.nombre,
                'email': user.correo,
                'telefono': user.telefono,
                'role': user.rol,
                'role_nombre': 'Administrador' if user.rol == 1 else 'Cliente'
            }
            for user in usuarios
        ]
        
        return jsonify(usuarios_dict), 200
        
    except Exception as error:
        print(f"Error al obtener usuarios: {error}")
        return jsonify({"msg": "Error al obtener usuarios"}), 500

def obtener_notificaciones_por_orden(orden_id):
    """Obtener notificaciones relacionadas con una orden específica"""
    try:
        # Verificar permisos
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        orden = Orden.query.get(orden_id)
        
        if not orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        # Solo el admin o el dueño de la orden pueden ver sus notificaciones
        es_admin = usuario and usuario.role == 1
        es_dueño = orden.telefono_usuario == usuario.telefono if usuario else False
        
        if not es_admin and not es_dueño:
            return jsonify({"msg": "No tienes permisos para ver estas notificaciones"}), 403
        
        notificaciones = Notificacion.query.filter_by(orden_id=orden_id).order_by(
            Notificacion.fecha_creacion.desc()
        ).all()
        
        notificaciones_dict = [Notificacion.to_dict(notif) for notif in notificaciones]
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total': len(notificaciones_dict)
        }), 200
        
    except Exception as error:
        print(f"Error al obtener notificaciones por orden: {error}")
        return jsonify({"msg": "Error al obtener notificaciones"}), 500

def obtener_contador_notificaciones():
    """Obtener contador de notificaciones no leídas"""
    try:
        user_id = get_jwt_identity()
        user_type = request.args.get('user_type', 'cliente')
        
        notificaciones = Notificacion.obtener_notificaciones_no_leidas(user_id, user_type)
        
        return jsonify({
            'total_no_leidas': len(notificaciones),
            'notificaciones_recientes': [
                {
                    'id': n.id,
                    'titulo': n.titulo,
                    'mensaje': n.mensaje[:100] + '...' if len(n.mensaje) > 100 else n.mensaje,
                    'tipo': n.tipo,
                    'fecha_creacion': n.fecha_creacion.isoformat() if n.fecha_creacion else None
                }
                for n in notificaciones[:5]  # Solo las 5 más recientes
            ]
        }), 200
        
    except Exception as error:
        print(f"Error al obtener contador de notificaciones: {error}")
        return jsonify({"msg": "Error al obtener contador de notificaciones"}), 500

# Funciones para integrar con el sistema de pedidos

def notificar_nuevo_pedido(orden_id):
    """Función para ser llamada cuando se crea un nuevo pedido"""
    try:
        orden = Orden.query.get(orden_id)
        if not orden:
            return False
        
        notificacion = Notificacion.notificar_nuevo_pedido(orden)
        
        # Aquí podrías agregar notificaciones en tiempo real con WebSockets
        # enviar_notificacion_tiempo_real(notificacion)
        
        return True
        
    except Exception as error:
        print(f"Error al notificar nuevo pedido: {error}")
        return False

def notificar_cambio_estado_pedido(orden_id, nuevo_estado):
    """Función para ser llamada cuando cambia el estado de un pedido"""
    try:
        orden = Orden.query.get(orden_id)
        if not orden:
            return False
        
        Notificacion.notificar_cambio_estado(orden, nuevo_estado)
        
        # Aquí podrías agregar notificaciones en tiempo real con WebSockets
        
        return True
        
    except Exception as error:
        print(f"Error al notificar cambio de estado: {error}")
        return False

def notificar_pedido_cancelado(orden_id, motivo=None):
    """Notificar cuando un pedido es cancelado"""
    try:
        orden = Orden.query.get(orden_id)
        if not orden:
            return False
        
        mensaje_admin = f"❌ Pedido {orden.codigo_unico} cancelado"
        if motivo:
            mensaje_admin += f"\nMotivo: {motivo}"
        
        # Notificación para el administrador
        Notificacion.crear_notificacion_admin(
            tipo='pedido_cancelado',
            titulo='❌ Pedido Cancelado',
            mensaje=mensaje_admin,
            datos_adicionales={
                'orden_id': orden.id,
                'codigo_pedido': orden.codigo_unico,
                'cliente': orden.nombre_usuario,
                'motivo': motivo,
                'precio': float(orden.precio) if orden.precio else 0.0
            },
            orden_id=orden.id
        )
        
        # Notificación para el cliente
        mensaje_cliente = f"Tu pedido {orden.codigo_unico} ha sido cancelado"
        if motivo:
            mensaje_cliente += f"\nMotivo: {motivo}"
        
        # Buscar usuario por teléfono
        from Models.User import User
        usuario = User.query.filter_by(telefono=orden.telefono_usuario).first()
        
        if usuario:
            Notificacion.crear_notificacion_cliente(
                cliente_id=usuario.id,
                tipo='pedido_cancelado',
                titulo='❌ Pedido Cancelado',
                mensaje=mensaje_cliente,
                datos_adicionales={
                    'orden_id': orden.id,
                    'codigo_pedido': orden.codigo_unico,
                    'motivo': motivo
                },
                orden_id=orden.id
            )
        
        return True
        
    except Exception as error:
        print(f"Error al notificar pedido cancelado: {error}")
        return False