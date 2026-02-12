from Models.Notificaciones import Notificacion
from Models.Ordenes import Orden
from Models.Especiales import Especial
from Models.User import User
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import config
from config import db

def notificar_nuevo_pedido(orden_id):
    """Función para notificar nuevo pedido - VERSIÓN PARA CARRITO"""
    try:
        print(f"[NOTIFICACIONES] Iniciando notificación para orden {orden_id}")
        orden = Orden.query.get(orden_id)
        if not orden:
            print(f"[NOTIFICACIONES] Orden {orden_id} no encontrada")
            return False
        
        print(f"[NOTIFICACIONES] Orden encontrada: {orden.codigo_unico}")
        print(f"Tipo pedido: {orden.tipo_pedido}")
        print(f"Método pago: {orden.metodo_pago}")
        
        # 1. Obtener detalles del pedido según tipo
        detalles_pedido = ""
        producto_nombre = ""
        items_info = []
        
        if orden.tipo_pedido == 'especial':
            print(f"Pedido ESPECIAL detectado")
            if orden.especial_id:
                especial = Especial.query.get(orden.especial_id)
                if especial:
                    producto_nombre = especial.nombre
                    detalles_pedido = f"{especial.nombre}"
                else:
                    detalles_pedido = "Producto Especial"
            else:
                detalles_pedido = "Producto Especial"
                
        elif orden.tipo_pedido == 'personalizado':
            print(f"Pedido PERSONALIZADO detectado")
            producto_nombre = "Pedido Personalizado"
            if orden.ingredientes_personalizados:
                ingredientes = orden.ingredientes_personalizados.split(',')
                primeros_ingredientes = ingredientes[:3]
                detalles_pedido = f"Personalizado: {', '.join(primeros_ingredientes).strip()}"
                if len(ingredientes) > 3:
                    detalles_pedido += " y más..."
            else:
                detalles_pedido = "Pedido Personalizado"
        
        elif orden.tipo_pedido == 'carrito':
            print(f"Pedido CARRITO detectado")
            producto_nombre = "Pedido del Carrito"
            
            # Intentar obtener items del pedido_json
            if orden.pedido_json:
                try:
                    pedido_data = json.loads(orden.pedido_json)
                    if isinstance(pedido_data, dict) and 'items' in pedido_data:
                        items = pedido_data['items']
                        for item in items[:3]:  # Mostrar solo primeros 3 items
                            items_info.append(f"{item.get('nombre', 'Producto')} x{item.get('cantidad', 1)}")
                        
                        if items_info:
                            detalles_pedido = ", ".join(items_info)
                            if len(items) > 3:
                                detalles_pedido += f" y {len(items) - 3} más"
                        else:
                            detalles_pedido = "Varios productos del carrito"
                    else:
                        detalles_pedido = "Compra del carrito"
                except:
                    detalles_pedido = "Pedido del carrito"
            else:
                detalles_pedido = "Pedido del carrito"
        
        print(f"Detalles del pedido: {detalles_pedido}")
        
        # 2. Información de pago para la notificación
        info_pago_texto = ""
        if orden.metodo_pago == 'tarjeta':
            info_pago_texto = "💳 Pago con tarjeta"
            if orden.info_pago_json:
                try:
                    info_pago = json.loads(orden.info_pago_json)
                    if info_pago.get('ultimos_4'):
                        info_pago_texto += f" (****{info_pago['ultimos_4']})"
                except:
                    pass
        else:
            info_pago_texto = "Pago en efectivo"
        
        # 3. MENSAJES PARA ADMINISTRADORES
        mensaje_admin = f"NUEVO PEDIDO #{orden.codigo_unico}\n"
        mensaje_admin += f"Cliente: {orden.nombre_usuario}\n"
        mensaje_admin += f"Tel: {orden.telefono_usuario}\n"
        mensaje_admin += f"Pedido: {detalles_pedido}\n"
        mensaje_admin += f"Método pago: {info_pago_texto}\n"
        mensaje_admin += f"Total: ${float(orden.precio):.2f}"
        
        if orden.notas:
            mensaje_admin += f"\nNotas: {orden.notas[:100]}..."
        
        titulo_admin = f"Pedido #{orden.codigo_unico}"
        
        # 4. MENSAJES PARA CLIENTES
        mensaje_cliente = f"Tu pedido #{orden.codigo_unico} ha sido recibido.\n"
        mensaje_cliente += f"Total: ${float(orden.precio):.2f}\n"
        mensaje_cliente += f"Método pago: {info_pago_texto}\n"
        mensaje_cliente += "Te notificaremos cuando esté en proceso."
        
        titulo_cliente = f"Pedido recibido #{orden.codigo_unico}"
        
        # 5. Datos completos para mostrar al hacer clic
        datos_completos = {
            'orden_id': orden.id,
            'codigo_pedido': orden.codigo_unico,
            'cliente_nombre': orden.nombre_usuario,
            'telefono_cliente': orden.telefono_usuario,
            'tipo_pedido': orden.tipo_pedido,
            'producto_nombre': producto_nombre,
            'detalles_completos': detalles_pedido,
            'ingredientes_completos': orden.ingredientes_personalizados if orden.tipo_pedido == 'personalizado' else None,
            'precio': float(orden.precio) if orden.precio else 0.0,
            'direccion_completa': orden.direccion_texto,
            'metodo_pago': orden.metodo_pago,
            'info_pago': orden.info_pago_json,
            'notas': orden.notas,
            'estado': orden.estado,
            'fecha_pedido': orden.fecha_creacion.isoformat() if orden.fecha_creacion else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Agregar items del carrito si existen
        if orden.tipo_pedido == 'carrito' and orden.pedido_json:
            try:
                pedido_data = json.loads(orden.pedido_json)
                datos_completos['items_carrito'] = pedido_data.get('items', [])
                datos_completos['total_items'] = len(pedido_data.get('items', []))
            except:
                pass
        
        # 6. Notificar a TODOS los administradores
        from Models.User import User
        admins = User.query.filter_by(rol=1).all()
        notificaciones_creadas = 0
        
        print(f"Administradores encontrados: {len(admins)}")
        
        for admin in admins:
            try:
                print(f"Creando notificación para admin: {admin.nombre}")
                
                notificacion = Notificacion.crear_notificacion(
                    user_id=admin.id,
                    user_type='admin',
                    tipo='nuevo_pedido',
                    titulo=titulo_admin,
                    mensaje=mensaje_admin,
                    datos_adicionales=datos_completos,
                    orden_id=orden.id
                )
                
                if notificacion:
                    notificaciones_creadas += 1
                    print(f"Notificación creada para admin {admin.nombre}")
                    
            except Exception as admin_error:
                print(f"Error con admin {admin.id}: {admin_error}")
        
        # 7. Notificación para el cliente si está registrado
        try:
            cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
            if cliente:
                print(f"Cliente registrado encontrado: {cliente.nombre}")
                
                notificacion_cliente = Notificacion.crear_notificacion(
                    user_id=cliente.id,
                    user_type='cliente',
                    tipo='confirmacion_pedido',
                    titulo=titulo_cliente,
                    mensaje=mensaje_cliente,
                    datos_adicionales=datos_completos,
                    orden_id=orden.id
                )
                
                if notificacion_cliente:
                    print(f"Notificación creada para el cliente")
            else:
                print(f"Cliente no registrado, solo notificaciones a admin")
        except Exception as cliente_error:
            print(f"⚠️ Error creando notificación para cliente: {cliente_error}")
        
        print(f"[NOTIFICACIONES] Proceso completado: {notificaciones_creadas} notificaciones creadas")
        return True
        
    except Exception as error:
        print(f"[NOTIFICACIONES] Error crítico: {error}")
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
        
        # 1. Crear notificaciones usando el método del modelo
        notificaciones_creadas = Notificacion.notificar_cambio_estado(orden, nuevo_estado)
        
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
                        'telefono_cliente': orden.telefono_usuario,
                        'motivo': motivo,
                        'direccion': orden.direccion_texto,
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
                        'motivo': motivo,
                        'direccion': orden.direccion_texto
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

def notificar_ingrediente_no_disponible(ingrediente_id, fecha=None, motivo=None, es_inactivo=False):
    """
    Notificar a los usuarios que tienen pedidos con un ingrediente no disponible
    o inactivo
    
    Args:
        ingrediente_id: ID del ingrediente
        fecha: Fecha específica de no disponibilidad (si es temporal)
        motivo: Razón de la no disponibilidad
        es_inactivo: True si es inactivación permanente, False si es temporal
    """
    try:
        tipo_notificacion = 'ingrediente_inactivo' if es_inactivo else 'ingrediente_no_disponible'
        
        print(f"[NOTIFICACIONES] ========== {'INGREDIENTE INACTIVO' if es_inactivo else 'INGREDIENTE NO DISPONIBLE'} ==========")
        print(f"Ingrediente ID: {ingrediente_id}")
        print(f"Fecha afectada: {fecha}")
        print(f"Motivo: {motivo}")
        print(f"Tipo notificación: {tipo_notificacion}")
        print(f"Es inactivo (permanente): {es_inactivo}")
        
        # Obtener el ingrediente
        from Models.Ingredientes import Ingrediente
        ingrediente = Ingrediente.find_by_id(ingrediente_id)
        
        if not ingrediente:
            print(f"ERROR: Ingrediente {ingrediente_id} no encontrado")
            return {'success': False, 'error': 'Ingrediente no encontrado'}
        
        ingrediente_nombre = ingrediente.nombre
        ingrediente_categoria = ingrediente.categoria
        
        if es_inactivo:
            fecha_descripcion = "permanentemente"
            titulo_base_cliente = f'Ingrediente Desactivado: {ingrediente_nombre}'
            titulo_base_admin = f'INGREDIENTE INACTIVO: {ingrediente_nombre}'
            mensaje_cliente_base = f"El ingrediente '{ingrediente_nombre}' ha sido marcado como INACTIVO y ya no estará disponible."
        else:
            fecha_descripcion = fecha if fecha else "hoy"
            titulo_base_cliente = f'⚠️ Ingrediente no disponible - Pedido'
            titulo_base_admin = f'⚠️ INGREDIENTE NO DISPONIBLE: {ingrediente_nombre}'
            mensaje_cliente_base = f"El ingrediente '{ingrediente_nombre}' no está disponible {fecha_descripcion}."
        
        print(f"Ingrediente encontrado: {ingrediente_nombre} ({ingrediente_categoria})")
        
        # Buscar órdenes PENDIENTES o EN PROCESO que contengan este ingrediente
        from Models.Ordenes import Orden
        
        # Estados de órdenes que pueden ser afectadas
        estados_activos = ['pendiente', 'recibido', 'en_preparacion', 'en_proceso', 'preparando']
        
        todas_ordenes = Orden.query.filter(
            Orden.estado.in_(estados_activos)
        ).all()
        
        print(f"Total órdenes en estado activo: {len(todas_ordenes)}")
        
        usuarios_notificados = set()
        ordenes_afectadas = []
        
        for orden in todas_ordenes:
            try:
                contiene_ingrediente = False
                detalles_pedido = ""
                
                # Verificar en pedido_json (estructurado)
                if orden.pedido_json:
                    try:
                        pedido_data = json.loads(orden.pedido_json)
                        
                        if isinstance(pedido_data, dict):
                            items = pedido_data.get('items', [])
                            for item in items:
                                nombre_item = item.get('nombre', '').lower()
                                if ingrediente_nombre.lower() in nombre_item.lower():
                                    contiene_ingrediente = True
                                    cantidad = item.get('cantidad', 1)
                                    detalles_pedido = f"Contiene: {nombre_item} x{cantidad}"
                                    break
                        
                        elif isinstance(pedido_data, list):
                            for item in pedido_data:
                                if isinstance(item, dict):
                                    nombre_item = item.get('nombre', '').lower()
                                    if ingrediente_nombre.lower() in nombre_item.lower():
                                        contiene_ingrediente = True
                                        cantidad = item.get('cantidad', 1)
                                        detalles_pedido = f"Contiene: {nombre_item} x{cantidad}"
                                        break
                    
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Error parseando JSON de orden {orden.id}: {e}")
                
                # Verificar en campo pedido (texto plano) si no se encontró en JSON
                if not contiene_ingrediente and orden.pedido:
                    if ingrediente_nombre.lower() in orden.pedido.lower():
                        contiene_ingrediente = True
                        detalles_pedido = f"Pedido: {orden.pedido[:50]}..."
                
                # Verificar en tipo de pedido personalizado
                if not contiene_ingrediente and orden.tipo_pedido == 'personalizado':
                    if orden.ingredientes_personalizados and ingrediente_nombre.lower() in orden.ingredientes_personalizados.lower():
                        contiene_ingrediente = True
                        detalles_pedido = f"Ingredientes: {orden.ingredientes_personalizados[:50]}..."
                
                if contiene_ingrediente:
                    print(f"📌 Orden afectada: #{orden.codigo_unico} - Cliente: {orden.nombre_usuario}")
                    ordenes_afectadas.append({
                        'id': orden.id,
                        'codigo': orden.codigo_unico,
                        'cliente': orden.nombre_usuario,
                        'telefono': orden.telefono_usuario,
                        'detalles': detalles_pedido,
                        'estado': orden.estado,
                        'direccion': orden.direccion_texto
                    })
                    
                    # Buscar usuario por teléfono
                    usuario_cliente = None
                    if orden.telefono_usuario:
                        usuario_cliente = User.query.filter_by(telefono=orden.telefono_usuario).first()
                    
                    # Si encontramos usuario, crear notificación
                    if usuario_cliente:
                        user_id_cliente = usuario_cliente.id
                        
                        # Mensaje personalizado para el cliente
                        if es_inactivo:
                            mensaje_cliente = f"El ingrediente '{ingrediente_nombre}' ha sido marcado como INACTIVO y ya no estará disponible."
                            if motivo:
                                mensaje_cliente += f" Motivo: {motivo}"
                            mensaje_cliente += f" Esto afecta tu pedido #{orden.codigo_unico}. Por favor contáctanos si necesitas realizar cambios."
                        else:
                            mensaje_cliente = f"El ingrediente '{ingrediente_nombre}' no está disponible {fecha_descripcion}."
                            if motivo:
                                mensaje_cliente += f" Motivo: {motivo}"
                            mensaje_cliente += f" Esto afecta tu pedido #{orden.codigo_unico}. Por favor contáctanos para realizar ajustes."
                        
                        try:
                            notif_cliente = Notificacion.crear_notificacion(
                                user_id=user_id_cliente,
                                user_type='cliente',
                                tipo=tipo_notificacion,  # ¡USAR EL TIPO CORRECTO!
                                titulo=titulo_base_cliente,
                                mensaje=mensaje_cliente,
                                datos_adicionales={
                                    'orden_id': orden.id,
                                    'codigo_pedido': orden.codigo_unico,
                                    'ingrediente_no_disponible': ingrediente_nombre,
                                    'ingrediente_id': ingrediente_id,
                                    'fecha_afectada': fecha_descripcion,
                                    'motivo': motivo,
                                    'estado_orden': orden.estado,
                                    'cliente_telefono': orden.telefono_usuario,
                                    'cliente_nombre': orden.nombre_usuario,
                                    'es_inactivo': es_inactivo,
                                    'detalles_pedido': detalles_pedido,
                                    'direccion': orden.direccion_texto,
                                    'precio_orden': float(orden.precio) if orden.precio else 0.0
                                },
                                orden_id=orden.id
                            )
                            
                            usuarios_notificados.add(user_id_cliente)
                            print(f"Notificación {tipo_notificacion} enviada al cliente ID: {user_id_cliente}")
                            
                        except Exception as cliente_error:
                            print(f"Error notificando cliente {user_id_cliente}: {cliente_error}")
                    else:
                        print(f"⚠️ Usuario no encontrado para teléfono: {orden.telefono_usuario}")
            
            except Exception as orden_error:
                print(f"Error procesando orden {orden.id}: {orden_error}")
                import traceback
                traceback.print_exc()
                continue
        
        # Buscar cuántos especiales están afectados (solo para inactivos)
        from Models.Especiales import Especial
        especiales_afectados = []
        if es_inactivo:
            especiales_afectados = Especial.query.filter(
                Especial.ingredientes.contains(ingrediente_nombre)
            ).all()
        
        # Notificar a TODOS los administradores
        admins = User.query.filter_by(rol=1).all()
        notificaciones_admin = 0
        
        if es_inactivo:
            mensaje_admin = f"INGREDIENTE MARCADO COMO INACTIVO: '{ingrediente_nombre}' ({ingrediente_categoria})"
            if motivo:
                mensaje_admin += f"\nMOTIVO: {motivo}"
            mensaje_admin += f"\n\nIMPACTO:"
            mensaje_admin += f"\n• Órdenes afectadas: {len(ordenes_afectadas)}"
            mensaje_admin += f"\n• Especiales afectados: {len(especiales_afectados)}"
            mensaje_admin += f"\n• Clientes notificados: {len(usuarios_notificados)}"
            
            if especiales_afectados:
                mensaje_admin += "\n\nESPECIALES AFECTADOS:"
                for i, especial in enumerate(especiales_afectados[:10], 1):
                    mensaje_admin += f"\n{i}. {especial.nombre}"
                    if especial.descripcion:
                        mensaje_admin += f" - {especial.descripcion[:50]}..."
        else:
            mensaje_admin = f"⚠️ INGREDIENTE NO DISPONIBLE: '{ingrediente_nombre}' ({ingrediente_categoria})"
            if motivo:
                mensaje_admin += f"\nMOTIVO: {motivo}"
            mensaje_admin += f"\n\nIMPACTO:"
            mensaje_admin += f"\n• Órdenes afectadas: {len(ordenes_afectadas)}"
            mensaje_admin += f"\n• Clientes notificados: {len(usuarios_notificados)}"
            mensaje_admin += f"\n• Fecha: {fecha_descripcion}"
        
        if ordenes_afectadas:
            mensaje_admin += "\n\nÓRDENES AFECTADAS:"
            for i, orden in enumerate(ordenes_afectadas[:10], 1):
                mensaje_admin += f"\n{i}. #{orden['codigo']} - {orden['cliente']} ({orden['telefono']})"
                if orden['direccion']:
                    direccion_corta = orden['direccion'][:50] + "..." if len(orden['direccion']) > 50 else orden['direccion']
                    mensaje_admin += f"\n{direccion_corta}"
                if orden['detalles']:
                    mensaje_admin += f"\n{orden['detalles']}"
        
        for admin in admins:
            try:
                Notificacion.crear_notificacion(
                    user_id=admin.id,
                    user_type='admin',
                    tipo=tipo_notificacion,  # ¡USAR EL TIPO CORRECTO!
                    titulo=titulo_base_admin,
                    mensaje=mensaje_admin,
                    datos_adicionales={
                        'ingrediente_id': ingrediente_id,
                        'ingrediente_nombre': ingrediente_nombre,
                        'ingrediente_categoria': ingrediente_categoria,
                        'fecha_afectada': fecha_descripcion,
                        'motivo': motivo,
                        'es_inactivo': es_inactivo,
                        'ordenes_afectadas': [o['id'] for o in ordenes_afectadas],
                        'ordenes_detalles': ordenes_afectadas,
                        'total_afectadas': len(ordenes_afectadas),
                        'especiales_afectados': len(especiales_afectados) if es_inactivo else 0,
                        'especiales_lista': [esp.nombre for esp in especiales_afectados] if es_inactivo else [],
                        'usuarios_notificados': list(usuarios_notificados),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                notificaciones_admin += 1
                print(f"Notificación {tipo_notificacion} enviada al admin ID: {admin.id}")
            except Exception as admin_error:
                print(f"Error notificando admin {admin.id}: {admin_error}")
        
        print(f"\n RESUMEN FINAL:")
        print(f"   • Ingrediente: {ingrediente_nombre}")
        print(f"   • Tipo: {'INACTIVO (permanente)' if es_inactivo else 'NO DISPONIBLE (temporal)'}")
        print(f"   • Fecha: {fecha_descripcion}")
        print(f"   • Órdenes afectadas: {len(ordenes_afectadas)}")
        print(f"   • Clientes notificados: {len(usuarios_notificados)}")
        print(f"   • Admins notificados: {notificaciones_admin}")
        if es_inactivo:
            print(f"   • Especiales afectados: {len(especiales_afectados)}")
        print(f"[NOTIFICACIONES] ========== FIN ==========\n")
        
        resultado = {
            'success': True,
            'ingrediente': {
                'id': ingrediente_id,
                'nombre': ingrediente_nombre,
                'categoria': ingrediente_categoria
            },
            'tipo_notificacion': tipo_notificacion,
            'es_inactivo': es_inactivo,
            'fecha_afectada': fecha_descripcion,
            'motivo': motivo,
            'ordenes_afectadas': ordenes_afectadas,
            'total_ordenes_afectadas': len(ordenes_afectadas),
            'usuarios_notificados': list(usuarios_notificados),
            'total_usuarios_notificados': len(usuarios_notificados),
            'notificaciones_admin_enviadas': notificaciones_admin,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if es_inactivo:
            resultado['especiales_afectados'] = len(especiales_afectados)
            resultado['especiales_lista'] = [esp.nombre for esp in especiales_afectados]
        
        return resultado
        
    except Exception as error:
        print(f"ERROR CRÍTICO en notificar_ingrediente_no_disponible: {error}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(error)}

@jwt_required()
def obtener_notificaciones_usuario():
    """Obtener notificaciones del usuario actual - CORREGIDO"""
    try:
        # Obtener usuario del token JWT
        user_id = get_jwt_identity()
        
        print(f"\n[API DEBUG] ========== OBTENER NOTIFICACIONES ==========")
        print(f"User ID del token: {user_id}")
        
        # Obtener información COMPLETA del usuario
        usuario = User.query.get(user_id)
        if not usuario:
            print(f"Usuario con ID {user_id} NO encontrado en la base de datos!")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        print(f"Usuario encontrado:")
        print(f"   - ID: {usuario.id}")
        print(f"   - Nombre: {usuario.nombre}")
        print(f"   - Teléfono: '{usuario.telefono}'")
        print(f"   - Rol: {usuario.rol} ({'Admin' if usuario.rol == 1 else 'Cliente'})")
        print(f"   - Email: {usuario.correo}")
        
        # ¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡!
        # CORRECCIÓN CRÍTICA: Determinar user_type por ROL, no por parámetro
        # ¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡!
        user_type = 'admin' if usuario.rol == 1 else 'cliente'
        print(f"User_type determinado por rol: {user_type}")
        
        # Obtener parámetros
        pagina = request.args.get('page', 1, type=int)
        por_pagina = request.args.get('per_page', 20, type=int)
        
        print(f"Parámetros de consulta:")
        print(f"   - user_type (ignorado, usando rol): {user_type}")
        print(f"   - página: {pagina}")
        print(f"   - por página: {por_pagina}")
        
        # Buscar notificaciones DIRECTAMENTE con user_id y user_type según rol
        print(f"\nBuscando notificaciones con user_id={user_id}, user_type={user_type}")
        
        notificaciones_directas = Notificacion.query.filter_by(
            user_id=user_id,
            user_type=user_type  # ← Usar el user_type determinado por rol
        ).all()
        
        print(f"Notificaciones directas encontradas: {len(notificaciones_directas)}")
        
        for notif in notificaciones_directas[:5]:  # Mostrar primeras 5
            print(f"   - ID: {notif.id}, Tipo: '{notif.tipo}', Título: '{notif.titulo[:50]}...'")
        
        # Buscar notificaciones con user_id=None por teléfono (solo para clientes)
        if user_type == 'cliente':
            telefono_usuario = usuario.telefono
            print(f"\nBuscando notificaciones sin user_id por teléfono: '{telefono_usuario}'")
            
            notificaciones_sin_usuario = Notificacion.query.filter(
                Notificacion.user_id.is_(None),
                Notificacion.user_type == 'cliente'
            ).all()
            
            print(f"Notificaciones sin user_id encontradas: {len(notificaciones_sin_usuario)}")
            
            # Verificar cada una
            coincidencias_telefono = 0
            for notif in notificaciones_sin_usuario:
                if notif.datos_adicionales:
                    tel_notif = notif.datos_adicionales.get('telefono_cliente') or notif.datos_adicionales.get('telefono')
                    if tel_notif:
                        tel_notif_str = str(tel_notif)
                        telefono_usuario_str = str(telefono_usuario)
                        
                        # Comparar teléfonos
                        if tel_notif_str == telefono_usuario_str:
                            print(f"¡COINCIDE EXACTO! Actualizando user_id a {user_id}")
                            notif.user_id = user_id
                            coincidencias_telefono += 1
                        else:
                            # Comparar últimos 8 dígitos
                            tel_notif_limpio = ''.join(filter(str.isdigit, tel_notif_str))
                            telefono_usuario_limpio = ''.join(filter(str.isdigit, telefono_usuario_str))
                            
                            if (len(tel_notif_limpio) >= 8 and len(telefono_usuario_limpio) >= 8 and
                                tel_notif_limpio[-8:] == telefono_usuario_limpio[-8:]):
                                print(f"¡COINCIDE (últimos 8 dígitos)! Actualizando user_id a {user_id}")
                                notif.user_id = user_id
                                coincidencias_telefono += 1
            
            if coincidencias_telefono > 0:
                db.session.commit()
                print(f"Se actualizaron {coincidencias_telefono} notificaciones con user_id={user_id}")
        
        # Obtener notificaciones FINALES
        offset = (pagina - 1) * por_pagina
        notificaciones_finales = Notificacion.query.filter_by(
            user_id=user_id,
            user_type=user_type
        ).order_by(Notificacion.fecha_creacion.desc()).offset(offset).limit(por_pagina).all()
        
        total_final = Notificacion.query.filter_by(
            user_id=user_id, 
            user_type=user_type
        ).count()
        
        print(f"\nRESULTADO FINAL:")
        print(f"   - Total notificaciones: {total_final}")
        print(f"   - Mostrando: {len(notificaciones_finales)}")
        
        # Debug: Mostrar todos los tipos de notificaciones encontradas
        tipos_encontrados = {}
        for notif in notificaciones_finales:
            tipo = notif.tipo
            tipos_encontrados[tipo] = tipos_encontrados.get(tipo, 0) + 1
            
        print(f"Tipos de notificaciones encontradas:")
        for tipo, cantidad in tipos_encontrados.items():
            print(f"   - {tipo}: {cantidad}")
        
        # Convertir a diccionario
        notificaciones_dict = []
        for notif in notificaciones_finales:
            notif_dict = Notificacion.to_dict(notif)
            notificaciones_dict.append(notif_dict)
        
        print(f"[API DEBUG] ========== FIN ==========\n")
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total_notificaciones': total_final,
            'pagina_actual': pagina,
            'total_paginas': (total_final + por_pagina - 1) // por_pagina,
            'por_pagina': por_pagina,
            'user_type_utilizado': user_type,
            'tipos_notificaciones': tipos_encontrados
        }), 200
        
    except Exception as error:
        print(f"ERROR CRÍTICO en obtener_notificaciones_usuario: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error al obtener notificaciones: {str(error)}"}), 500

@jwt_required()
def obtener_notificaciones_no_leidas():
    """Obtener notificaciones no leídas del usuario"""
    try:
        user_id = get_jwt_identity()
        usuario = User.query.get(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Determinar user_type por rol
        user_type = 'admin' if usuario.rol == 1 else 'cliente'
        
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
        usuario = User.query.get(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Determinar user_type por rol
        user_type = 'admin' if usuario.rol == 1 else 'cliente'
        
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
        usuario = User.query.get(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Determinar user_type por rol
        user_type = 'admin' if usuario.rol == 1 else 'cliente'
        
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
        usuario = User.query.get(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Determinar user_type por rol
        user_type = 'admin' if usuario.rol == 1 else 'cliente'
        
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
                for n in notificaciones[:5]
            ]
        }), 200
        
    except Exception as error:
        print(f"Error al obtener contador de notificaciones: {error}")
        return jsonify({"msg": "Error al obtener contador de notificaciones"}), 500