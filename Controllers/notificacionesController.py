from Models.Notificaciones import Notificacion
from Models.Ordenes import Orden
from Models.User import User
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import config
from config import db

def notificar_nuevo_pedido(orden_id):
    """Función para notificar nuevo pedido"""
    try:
        print(f"DEBUG: Ejecutando notificar_nuevo_pedido para orden {orden_id}")
        orden = Orden.query.get(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación")
            return False
        
        print(f"DEBUG: Notificando nuevo pedido {orden.codigo_unico}")
        
        # 1. Crear notificación usando el método del modelo (para admin ID 1)
        notificacion_principal = Notificacion.notificar_nuevo_pedido(orden)
        print(f"DEBUG: Notificación principal creada: {notificacion_principal.id}")
        
        # OBTENER LOS INGREDIENTES DEL PEDIDO
        ingredientes = "Sin ingredientes especificados"
        if orden.pedido_json:
            try:
                # Parsear el JSON del pedido
                pedido_data = json.loads(orden.pedido_json)
                print(f"DEBUG: Pedido JSON: {pedido_data}")
                
                # Extraer ingredientes del pedido
                if isinstance(pedido_data, dict):
                    items = pedido_data.get('items', [])
                    if items:
                        ingredientes_lista = []
                        for item in items:
                            nombre = item.get('nombre', '')
                            cantidad = item.get('cantidad', 1)
                            if nombre:
                                ingredientes_lista.append(f"{nombre} x{cantidad}")
                        
                        if ingredientes_lista:
                            ingredientes = ", ".join(ingredientes_lista)
                            print(f"DEBUG: Ingredientes extraídos: {ingredientes}")
                
                elif isinstance(pedido_data, list):
                    ingredientes_lista = []
                    for item in pedido_data:
                        if isinstance(item, dict):
                            nombre = item.get('nombre', '')
                            cantidad = item.get('cantidad', 1)
                            if nombre:
                                ingredientes_lista.append(f"{nombre} x{cantidad}")
                    
                    if ingredientes_lista:
                        ingredientes = ", ".join(ingredientes_lista)
                        print(f"DEBUG: Ingredientes extraídos de lista: {ingredientes}")
                        
            except json.JSONDecodeError as e:
                print(f"ERROR al parsear JSON del pedido: {e}")
                if orden.pedido:
                    ingredientes = orden.pedido[:100]
        elif orden.pedido:
            ingredientes = orden.pedido[:100]
        
        print(f"DEBUG: Ingredientes finales: {ingredientes}")
        
        # 2. CORRECCIÓN: Crear notificaciones para TODOS los administradores
        admins = User.query.filter_by(rol=1).all()
        print(f"DEBUG: Administradores encontrados: {len(admins)}")
        
        for admin in admins:
            try:
                notif = Notificacion.crear_notificacion(
                    user_id=admin.id,  # ← ID del administrador
                    user_type='admin',  # ← Tipo: admin
                    tipo='nuevo_pedido',
                    titulo=f'Nuevo Pedido #{orden.codigo_unico}',
                    mensaje=f'Nuevo pedido de {orden.nombre_usuario} por ${float(orden.precio):.2f}' if orden.precio else f'Nuevo pedido de {orden.nombre_usuario}',
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'cliente_nombre': orden.nombre_usuario,
                        'precio': float(orden.precio) if orden.precio else 0.0,
                        'telefono': orden.telefono_usuario,
                        'ingredientes': ingredientes,
                        'direccion': orden.direccion_usuario
                    },
                    orden_id=orden.id
                )
                print(f"DEBUG: Notificación creada para admin {admin.id}: {notif.id}")
            except Exception as admin_error:
                print(f"ERROR al crear notificación para admin {admin.id}: {admin_error}")
        
        # 3. CORRECCIÓN CRÍTICA: Crear notificación para el cliente
        usuario_cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
        if usuario_cliente:
            try:
                # ¡IMPORTANTE! Usar el ID del CLIENTE, no del admin
                notif_cliente = Notificacion.crear_notificacion(
                    user_id=usuario_cliente.id,  # ← ID del CLIENTE
                    user_type='cliente',  # ← Tipo: cliente
                    tipo='estado_pedido',
                    titulo=f'Pedido: {ingredientes}',
                    mensaje=f'Tu pedido ha sido recibido y está siendo procesado',
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'estado': 'Recibido',
                        'ingredientes': ingredientes,
                        'precio': float(orden.precio) if orden.precio else 0.0,
                        'direccion': orden.direccion_usuario,
                        'telefono_cliente': orden.telefono_usuario  # Para búsqueda por teléfono
                    },
                    orden_id=orden.id
                )
                print(f"DEBUG: Notificación creada para cliente ID {usuario_cliente.id}")
                print(f"DEBUG: user_type asignado: cliente")
            except Exception as cliente_error:
                print(f"ERROR al crear notificación para cliente: {cliente_error}")
                import traceback
                traceback.print_exc()
        else:
            print(f"DEBUG: No se encontró usuario cliente con teléfono {orden.telefono_usuario}")
            # Si no existe usuario, crear notificación con user_id=None
            try:
                notif_cliente = Notificacion.crear_notificacion(
                    user_id=None,  # Sin user_id por ahora
                    user_type='cliente',
                    tipo='estado_pedido',
                    titulo=f'Pedido: {ingredientes}',
                    mensaje=f'Tu pedido ha sido recibido y está siendo procesado',
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'estado': 'Recibido',
                        'ingredientes': ingredientes,
                        'precio': float(orden.precio) if orden.precio else 0.0,
                        'direccion': orden.direccion_usuario,
                        'telefono_cliente': orden.telefono_usuario  # Para asignación posterior
                    },
                    orden_id=orden.id
                )
                print(f"DEBUG: Notificación creada sin user_id (se asignará por teléfono)")
            except Exception as error_sin_usuario:
                print(f"ERROR al crear notificación sin usuario: {error_sin_usuario}")
        
        print(f"DEBUG: Notificaciones de nuevo pedido creadas exitosamente")
        return True
        
    except Exception as error:
        print(f"ERROR al notificar nuevo pedido: {error}")
        import traceback
        traceback.print_exc()
        return False

def notificar_cambio_estado_pedido(orden_id, nuevo_estado):
    """Función para notificar cambio de estado de pedido"""
    try:
        print(f"DEBUG: Ejecutando notificar_cambio_estado_pedido para orden {orden_id}, estado: {nuevo_estado}")
        orden = Orden.query.get(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación de estado")
            return False
        
        print(f"DEBUG: Notificando cambio de estado del pedido {orden.codigo_unico} a {nuevo_estado}")
        
        # OBTENER LOS INGREDIENTES DEL PEDIDO
        ingredientes = "Sin ingredientes especificados"
        if orden.pedido_json:
            try:
                pedido_data = json.loads(orden.pedido_json)
                if isinstance(pedido_data, dict):
                    items = pedido_data.get('items', [])
                    if items:
                        ingredientes_lista = []
                        for item in items:
                            nombre = item.get('nombre', '')
                            cantidad = item.get('cantidad', 1)
                            if nombre:
                                ingredientes_lista.append(f"{nombre} x{cantidad}")
                        
                        if ingredientes_lista:
                            ingredientes = ", ".join(ingredientes_lista)
                elif isinstance(pedido_data, list):
                    ingredientes_lista = []
                    for item in pedido_data:
                        if isinstance(item, dict):
                            nombre = item.get('nombre', '')
                            cantidad = item.get('cantidad', 1)
                            if nombre:
                                ingredientes_lista.append(f"{nombre} x{cantidad}")
                    
                    if ingredientes_lista:
                        ingredientes = ", ".join(ingredientes_lista)
                        
            except json.JSONDecodeError as e:
                print(f"ERROR al parsear JSON del pedido: {e}")
                if orden.pedido:
                    ingredientes = orden.pedido[:100]
        elif orden.pedido:
            ingredientes = orden.pedido[:100]
        
        # 1. CORRECCIÓN: Usar el método del modelo asegurando user_id correcto
        # Revisar el método Notificacion.notificar_cambio_estado en tu modelo
        Notificacion.notificar_cambio_estado(orden, nuevo_estado)
        
        # 2. Crear notificaciones para TODOS los administradores
        admins = User.query.filter_by(rol=1).all()
        for admin in admins:
            try:
                Notificacion.crear_notificacion(
                    user_id=admin.id,  # ← ID del admin
                    user_type='admin',  # ← Tipo admin
                    tipo='estado_cambiado',
                    titulo=f'Estado Cambiado #{orden.codigo_unico}',
                    mensaje=f'El pedido de {orden.nombre_usuario} cambió a: {nuevo_estado}',
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'cliente_nombre': orden.nombre_usuario,
                        'estado_nuevo': nuevo_estado,
                        'estado_anterior': orden.estado,
                        'ingredientes': ingredientes,
                        'precio': float(orden.precio) if orden.precio else 0.0
                    },
                    orden_id=orden.id
                )
            except Exception as admin_error:
                print(f"ERROR al crear notificación de estado para admin {admin.id}: {admin_error}")
        
        # 3. CORRECCIÓN: Crear notificación para el cliente
        usuario_cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
        if usuario_cliente:
            try:
                notif_cliente = Notificacion.crear_notificacion(
                    user_id=usuario_cliente.id,  # ← ID del CLIENTE
                    user_type='cliente',  # ← Tipo cliente
                    tipo='estado_cambiado',
                    titulo=f'Pedido: {ingredientes}',
                    mensaje=f'Tu pedido ha cambiado a: {nuevo_estado}',
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'estado': nuevo_estado,
                        'ingredientes': ingredientes,
                        'precio': float(orden.precio) if orden.precio else 0.0,
                        'telefono_cliente': orden.telefono_usuario
                    },
                    orden_id=orden.id
                )
                print(f"DEBUG: Notificación de estado creada para cliente ID {usuario_cliente.id}")
            except Exception as cliente_error:
                print(f"ERROR al crear notificación de estado para cliente: {cliente_error}")
        else:
            # Crear sin user_id si no se encuentra usuario
            try:
                Notificacion.crear_notificacion(
                    user_id=None,
                    user_type='cliente',
                    tipo='estado_cambiado',
                    titulo=f'Pedido: {ingredientes}',
                    mensaje=f'Tu pedido ha cambiado a: {nuevo_estado}',
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'estado': nuevo_estado,
                        'ingredientes': ingredientes,
                        'precio': float(orden.precio) if orden.precio else 0.0,
                        'telefono_cliente': orden.telefono_usuario
                    },
                    orden_id=orden.id
                )
                print(f"DEBUG: Notificación de estado creada sin user_id")
            except Exception as error:
                print(f"ERROR al crear notificación sin usuario: {error}")
        
        print(f"DEBUG: Notificaciones de cambio de estado creadas exitosamente")
        return True
        
    except Exception as error:
        print(f"ERROR al notificar cambio de estado: {error}")
        import traceback
        traceback.print_exc()
        return False

def notificar_pedido_cancelado(orden_id, motivo=None):
    """Notificar cuando un pedido es cancelado"""
    try:
        print(f"DEBUG: Ejecutando notificar_pedido_cancelado para orden {orden_id}")
        orden = Orden.query.get(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación de cancelación")
            return False
        
        print(f"DEBUG: Notificando cancelación del pedido {orden.codigo_unico}")
        
        mensaje_admin = f"Pedido {orden.codigo_unico} cancelado"
        if motivo:
            mensaje_admin += f"\nMotivo: {motivo}"
        
        # 1. Notificación para TODOS los administradores
        admins = User.query.filter_by(rol=1).all()
        for admin in admins:
            try:
                Notificacion.crear_notificacion(
                    user_id=admin.id,
                    user_type='admin',
                    tipo='pedido_cancelado',
                    titulo='Pedido Cancelado',
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
            except Exception as admin_error:
                print(f"ERROR al crear notificación de cancelación para admin {admin.id}: {admin_error}")
        
        # 2. Notificación para el cliente
        usuario_cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
        if usuario_cliente:
            try:
                mensaje_cliente = f"Tu pedido {orden.codigo_unico} ha sido cancelado"
                if motivo:
                    mensaje_cliente += f"\nMotivo: {motivo}"
                
                Notificacion.crear_notificacion_cliente(
                    cliente_id=usuario_cliente.id,
                    tipo='pedido_cancelado',
                    titulo='Pedido Cancelado',
                    mensaje=mensaje_cliente,
                    datos_adicionales={
                        'orden_id': orden.id,
                        'codigo_pedido': orden.codigo_unico,
                        'motivo': motivo
                    },
                    orden_id=orden.id
                )
            except Exception as cliente_error:
                print(f"ERROR al crear notificación de cancelación para cliente: {cliente_error}")
        else:
            print(f"DEBUG: No se encontró usuario cliente con teléfono {orden.telefono_usuario}")
        
        print(f"DEBUG: Notificaciones de cancelación creadas exitosamente")
        return True
        
    except Exception as error:
        print(f"ERROR al notificar pedido cancelado: {error}")
        import traceback
        traceback.print_exc()
        return False

@jwt_required()
def obtener_notificaciones_usuario():
    """Obtener notificaciones del usuario actual"""
    try:
        # Obtener usuario del token JWT
        user_id = get_jwt_identity()
        
        print(f"\n🔔 [API DEBUG] ========== OBTENER NOTIFICACIONES ==========")
        print(f"📱 User ID del token: {user_id}")
        
        # Obtener información COMPLETA del usuario
        usuario = User.query.get(user_id)
        if not usuario:
            print(f"❌ Usuario con ID {user_id} NO encontrado en la base de datos!")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        print(f"👤 Usuario encontrado:")
        print(f"   - ID: {usuario.id}")
        print(f"   - Nombre: {usuario.nombre}")
        print(f"   - Teléfono: '{usuario.telefono}'")
        print(f"   - Rol: {usuario.rol} ({'Admin' if usuario.rol == 1 else 'Cliente'})")
        print(f"   - Email: {usuario.correo}")
        
        # Obtener parámetros
        pagina = request.args.get('page', 1, type=int)
        por_pagina = request.args.get('per_page', 20, type=int)
        user_type = request.args.get('user_type', 'cliente')
        
        print(f"📋 Parámetros de consulta:")
        print(f"   - user_type: {user_type}")
        print(f"   - página: {pagina}")
        print(f"   - por página: {por_pagina}")
        
        # Buscar notificaciones DIRECTAMENTE con user_id
        print(f"\n🔍 Buscando notificaciones con user_id={user_id}, user_type={user_type}")
        
        notificaciones_directas = Notificacion.query.filter_by(
            user_id=user_id,
            user_type=user_type
        ).all()
        
        print(f"✅ Notificaciones directas encontradas: {len(notificaciones_directas)}")
        
        for notif in notificaciones_directas[:5]:  # Mostrar primeras 5
            print(f"   - ID: {notif.id}, Tipo: {notif.tipo}, Título: {notif.titulo}")
            if notif.datos_adicionales:
                print(f"     Metadata: {notif.datos_adicionales}")
        
        # Buscar notificaciones con user_id=None por teléfono
        telefono_usuario = usuario.telefono
        print(f"\n🔍 Buscando notificaciones sin user_id por teléfono: '{telefono_usuario}'")
        
        notificaciones_sin_usuario = Notificacion.query.filter(
            Notificacion.user_id.is_(None),
            Notificacion.user_type == 'cliente'
        ).all()
        
        print(f"📞 Notificaciones sin user_id encontradas: {len(notificaciones_sin_usuario)}")
        
        # Verificar cada una
        coincidencias_telefono = 0
        for notif in notificaciones_sin_usuario:
            if notif.datos_adicionales:
                tel_notif = notif.datos_adicionales.get('telefono_cliente') or notif.datos_adicionales.get('telefono')
                if tel_notif:
                    print(f"   - Notif {notif.id}: Teléfono en datos: '{tel_notif}'")
                    tel_notif_str = str(tel_notif)
                    telefono_usuario_str = str(telefono_usuario)
                    
                    # Comparar teléfonos
                    if tel_notif_str == telefono_usuario_str:
                        print(f"     ✅ ¡COINCIDE EXACTO! Actualizando user_id a {user_id}")
                        notif.user_id = user_id
                        coincidencias_telefono += 1
                    else:
                        # Comparar últimos 8 dígitos
                        tel_notif_limpio = ''.join(filter(str.isdigit, tel_notif_str))
                        telefono_usuario_limpio = ''.join(filter(str.isdigit, telefono_usuario_str))
                        
                        if (len(tel_notif_limpio) >= 8 and len(telefono_usuario_limpio) >= 8 and
                            tel_notif_limpio[-8:] == telefono_usuario_limpio[-8:]):
                            print(f"     ✅ ¡COINCIDE (últimos 8 dígitos)! Actualizando user_id a {user_id}")
                            notif.user_id = user_id
                            coincidencias_telefono += 1
        
        if coincidencias_telefono > 0:
            db.session.commit()
            print(f"✅ Se actualizaron {coincidencias_telefono} notificaciones con user_id={user_id}")
        
        # Obtener notificaciones FINALES
        offset = (pagina - 1) * por_pagina
        notificaciones_finales = Notificacion.query.filter_by(
            user_id=user_id,
            user_type=user_type
        ).order_by(Notificacion.fecha_creacion.desc()).offset(offset).limit(por_pagina).all()
        
        total_final = Notificacion.query.filter_by(user_id=user_id, user_type=user_type).count()
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   - Total notificaciones: {total_final}")
        print(f"   - Mostrando: {len(notificaciones_finales)}")
        
        # Convertir a diccionario
        notificaciones_dict = []
        for notif in notificaciones_finales:
            notif_dict = Notificacion.to_dict(notif)
            notificaciones_dict.append(notif_dict)
            
            # Debug de cada notificación
            print(f"   - Notif {notif.id}: {notif.tipo} - {notif.titulo}")
            if notif.datos_adicionales:
                print(f"     Metadata: {notif.datos_adicionales}")
        
        print(f"🔔 [API DEBUG] ========== FIN ==========\n")
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total_notificaciones': total_final,
            'pagina_actual': pagina,
            'total_paginas': (total_final + por_pagina - 1) // por_pagina,
            'por_pagina': por_pagina
        }), 200
        
    except Exception as error:
        print(f"❌ ERROR CRÍTICO en obtener_notificaciones_usuario: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error al obtener notificaciones: {str(error)}"}), 500

@jwt_required()
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

@jwt_required()
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

@jwt_required()
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

@jwt_required()
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

@jwt_required()
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

@jwt_required()
def enviar_mensaje():
    """Enviar mensaje/notificación a usuarios (solo admin)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No se proporcionaron datos"}), 400
        
        # Verificar que el usuario es admin
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        
        if not usuario or usuario.rol != 1:
            return jsonify({"msg": "Solo los administradores pueden enviar mensajes"}), 403
        
        destinatario_tipo = data.get('destinatario_tipo', 'todos')
        destinatario_id = data.get('destinatario_id')
        titulo = data.get('titulo', 'Mensaje del Administrador')
        mensaje = data.get('mensaje')
        
        if not mensaje or not mensaje.strip():
            return jsonify({"msg": "El mensaje es requerido"}), 400
        
        datos_adicionales = {'remitente': usuario.nombre}
        
        notificaciones_creadas = []
        
        if destinatario_tipo == 'todos':
            # Enviar a todos los clientes
            clientes = User.query.filter_by(rol=2).all()
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
            if not admin or admin.rol != 1:
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
            
        elif destinatario_tipo == 'todos_admins':
            # Enviar a todos los administradores
            admins = User.query.filter_by(rol=1).all()
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
            "msg": f"Mensaje enviado correctamente a {len(notificaciones_creadas)} usuarios",
            "notificaciones_enviadas": len(notificaciones_creadas)
        }), 201
        
    except Exception as error:
        print(f"Error al enviar mensaje: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error al enviar mensaje: {str(error)}"}), 500

@jwt_required()
def obtener_analiticas():
    """Obtener analíticas de notificaciones (solo admin)"""
    try:
        # Verificar que el usuario es admin
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        
        if not usuario or usuario.rol != 1:
            return jsonify({"msg": "Solo los administradores pueden ver analíticas"}), 403
        
        dias = request.args.get('dias', 30, type=int)
        analiticas = Notificacion.obtener_analiticas(dias)
        
        return jsonify(analiticas), 200
        
    except Exception as error:
        print(f"Error al obtener analíticas: {error}")
        return jsonify({"msg": "Error al obtener analíticas"}), 500

@jwt_required()
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
                'rol': user.rol,
                'rol_nombre': 'Administrador' if user.rol == 1 else 'Cliente'
            }
            for user in usuarios
        ]
        
        return jsonify(usuarios_dict), 200
        
    except Exception as error:
        print(f"Error al obtener usuarios: {error}")
        return jsonify({"msg": "Error al obtener usuarios"}), 500

@jwt_required()
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
        es_admin = usuario and usuario.rol == 1
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

@jwt_required()
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