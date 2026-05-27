# Controllers/notificacionesController.py
from Models.Notificaciones import Notificacion
from Models.Ordenes import Orden
from Models.Suplementos import Suplemento
from Models.User import UserRepository
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import traceback
from config import db_sql

# Instancia del repositorio de usuarios
user_repo = UserRepository()

def notificar_nuevo_pedido(orden_id):
    """Función para notificar nuevo pedido - VERSIÓN COMPLETA CON LOGS"""
    try:
        print(f"\n{'='*60}")
        print(f"🔔 [NOTIFICACIONES] notificar_nuevo_pedido - INICIANDO")
        print(f"📦 Orden ID recibido: {orden_id} (tipo: {type(orden_id)})")
        print(f"{'='*60}")
        
        # Buscar la orden usando el método del modelo
        from Models.Ordenes import Orden
        
        orden = None
        try:
            orden = Orden.find_by_id(orden_id)
            if orden:
                print(f"✅ Orden encontrada con ID original")
        except Exception as e:
            print(f"⚠️ Error buscando con ID original: {e}")
        
        if not orden and isinstance(orden_id, str) and len(orden_id) == 24:
            try:
                from bson.objectid import ObjectId
                orden = Orden.find_by_id(ObjectId(orden_id))
                if orden:
                    print(f"✅ Orden encontrada como ObjectId")
            except:
                pass
        
        if not orden and str(orden_id).isdigit():
            try:
                orden = Orden.find_by_id(int(orden_id))
                if orden:
                    print(f"✅ Orden encontrada como entero")
            except:
                pass
        
        if not orden:
            print(f"❌ [NOTIFICACIONES] Orden {orden_id} NO encontrada")
            return False
        
        # Convertir orden a diccionario
        if hasattr(orden, 'to_dict'):
            orden_dict = orden.to_dict()
        else:
            from bson.objectid import ObjectId
            orden_dict = dict(orden)
            if '_id' in orden_dict:
                orden_dict['id'] = str(orden_dict.pop('_id'))
        
        if not orden_dict.get('info_pago_json') and orden_dict.get('info_pago'):
            orden_dict['info_pago_json'] = json.dumps(orden_dict['info_pago'])
        
        print(f"✅ [NOTIFICACIONES] Orden encontrada:")
        print(f"   - ID: {orden_dict.get('id')}")
        print(f"   - Código: {orden_dict.get('codigo_unico')}")
        print(f"   - Cliente: {orden_dict.get('nombre_usuario')}")
        print(f"   - Teléfono: {orden_dict.get('telefono_usuario')}")
        
        # 1. Obtener detalles del pedido según tipo
        detalles_pedido = ""
        producto_nombre = ""
        items_info = []
        
        if orden_dict.get('tipo_pedido') == 'suplemento':
            print(f"   📋 Pedido SUPLEMENTO detectado")
            suplemento_id = orden_dict.get('suplemento_id')
            cantidad = orden_dict.get('cantidad', 1)
            
            if suplemento_id:
                from Models.Suplementos import Suplemento
                suplemento = Suplemento.find_by_id(suplemento_id)
                if suplemento:
                    if hasattr(suplemento, 'to_dict'):
                        suplemento_dict = suplemento.to_dict()
                    else:
                        suplemento_dict = dict(suplemento)
                    producto_nombre = suplemento_dict.get('nombre')
                    detalles_pedido = f"{producto_nombre} x{cantidad}"
                    print(f"      Suplemento: {producto_nombre} x{cantidad}")
                else:
                    detalles_pedido = "Producto Suplemento"
            else:
                detalles_pedido = "Producto Suplemento"
                
        elif orden_dict.get('tipo_pedido') == 'carrito':
            print(f"   📋 Pedido CARRITO detectado")
            producto_nombre = "Pedido del Carrito"
            
            if orden_dict.get('pedido_json'):
                try:
                    pedido_data = json.loads(orden_dict['pedido_json']) if isinstance(orden_dict['pedido_json'], str) else orden_dict['pedido_json']
                    if isinstance(pedido_data, list):
                        items = pedido_data
                        total_items = len(items)
                        print(f"      Total items en carrito: {total_items}")
                        
                        for item in items[:3]:
                            items_info.append(f"{item.get('nombre', 'Producto')} x{item.get('cantidad', 1)}")
                        
                        if items_info:
                            detalles_pedido = ", ".join(items_info)
                            if total_items > 3:
                                detalles_pedido += f" y {total_items - 3} más"
                        else:
                            detalles_pedido = "Varios productos del carrito"
                    else:
                        detalles_pedido = "Compra del carrito"
                except Exception as e:
                    print(f"      Error parseando pedido_json: {e}")
                    detalles_pedido = "Pedido del carrito"
            else:
                detalles_pedido = "Pedido del carrito"
        
        print(f"   📝 Detalles del pedido: {detalles_pedido}")
        
        # 2. Información de pago
        info_pago_texto = ""
        if orden_dict.get('metodo_pago') == 'tarjeta':
            info_pago_texto = "💳 Pago con tarjeta"
            if orden_dict.get('info_pago_json'):
                try:
                    info_pago = json.loads(orden_dict['info_pago_json']) if isinstance(orden_dict['info_pago_json'], str) else orden_dict['info_pago_json']
                    if info_pago.get('ultimos_4_digitos'):
                        info_pago_texto += f" (****{info_pago['ultimos_4_digitos']})"
                except:
                    pass
        else:
            info_pago_texto = "Pago en efectivo"
        
        print(f"   💰 Información pago: {info_pago_texto}")
        
        # 3. MENSAJES PARA ADMINISTRADORES
        codigo_pedido = orden_dict.get('codigo_unico', '')
        nombre_cliente = orden_dict.get('nombre_usuario', '')
        telefono_cliente = orden_dict.get('telefono_usuario', '')
        precio_total = float(orden_dict.get('precio_total', 0))
        
        mensaje_admin = f"NUEVO PEDIDO #{codigo_pedido}\n"
        mensaje_admin += f"Cliente: {nombre_cliente}\n"
        mensaje_admin += f"Tel: {telefono_cliente}\n"
        mensaje_admin += f"Pedido: {detalles_pedido}\n"
        mensaje_admin += f"Método pago: {info_pago_texto}\n"
        mensaje_admin += f"Total: ${precio_total:.2f}"
        
        if orden_dict.get('notas'):
            mensaje_admin += f"\nNotas: {orden_dict['notas'][:100]}..."
        
        titulo_admin = f"Pedido #{codigo_pedido}"
        
        print(f"\n📧 Mensaje para admin:")
        print(f"   Título: {titulo_admin}")
        print(f"   Mensaje: {mensaje_admin[:100]}...")
        
        # 4. Notificar a TODOS los administradores
        from Models.User import UserRepository
        user_repo = UserRepository()
        
        admins = user_repo.get_users_by_role(1)
        print(f"\n👥 Administradores encontrados: {len(admins)}")
        
        notificaciones_creadas = 0
        
        if len(admins) == 0:
            print(f"⚠️ No hay administradores registrados en el sistema")
        
        for admin in admins:
            try:
                admin_dict = user_repo.to_dict(admin)
                admin_id = admin_dict.get('id')
                admin_nombre = admin_dict.get('nombre', 'Admin')
                
                print(f"\n   → Creando notificación para admin: {admin_nombre} (ID: {admin_id})")
                
                from Models.Notificaciones import Notificacion
                notificacion = Notificacion.crear_notificacion(
                    user_id=admin_id,
                    user_type='admin',
                    tipo='nuevo_pedido',
                    titulo=titulo_admin,
                    mensaje=mensaje_admin,
                    datos_adicionales={
                        'orden_id': orden_dict.get('id'),
                        'codigo_pedido': codigo_pedido,
                        'cliente_nombre': nombre_cliente,
                        'telefono_cliente': telefono_cliente,
                        'detalles_pedido': detalles_pedido,
                        'precio_total': precio_total,
                        'metodo_pago': orden_dict.get('metodo_pago'),
                        'direccion': orden_dict.get('direccion_texto')
                    },
                    orden_id=orden_dict.get('id')
                )
                
                if notificacion:
                    notificaciones_creadas += 1
                    if hasattr(notificacion, 'id'):
                        notif_id = notificacion.id
                    else:
                        notif_id = notificacion.get('id')
                    print(f"      ✅ Notificación creada para admin {admin_nombre} - ID: {notif_id}")
                    
            except Exception as admin_error:
                print(f"      ❌ Error con admin {admin_nombre}: {admin_error}")
                traceback.print_exc()
        
        print(f"\n📊 Notificaciones a admin creadas: {notificaciones_creadas}")
        
        # 5. Notificación para el cliente si está registrado
        try:
            print(f"\n🔍 Buscando cliente con teléfono: {telefono_cliente}")
            
            cliente = None
            if telefono_cliente:
                cliente = user_repo.find_by_phone(telefono_cliente)
            
            if cliente:
                cliente_dict = user_repo.to_dict(cliente)
                print(f"✅ Cliente registrado encontrado: {cliente_dict.get('nombre')} (ID: {cliente_dict.get('id')})")
                
                mensaje_cliente = f"Tu pedido #{codigo_pedido} ha sido recibido.\n"
                mensaje_cliente += f"Total: ${precio_total:.2f}\n"
                mensaje_cliente += f"Método pago: {info_pago_texto}\n"
                mensaje_cliente += "Te notificaremos cuando esté en proceso."
                
                titulo_cliente = f"Pedido recibido #{codigo_pedido}"
                
                from Models.Notificaciones import Notificacion
                notificacion_cliente = Notificacion.crear_notificacion(
                    user_id=cliente_dict.get('id'),
                    user_type='cliente',
                    tipo='confirmacion_pedido',
                    titulo=titulo_cliente,
                    mensaje=mensaje_cliente,
                    datos_adicionales={
                        'orden_id': orden_dict.get('id'),
                        'codigo_pedido': codigo_pedido,
                        'precio_total': precio_total
                    },
                    orden_id=orden_dict.get('id')
                )
                
                if notificacion_cliente:
                    if hasattr(notificacion_cliente, 'id'):
                        notif_id = notificacion_cliente.id
                    else:
                        notif_id = notificacion_cliente.get('id')
                    print(f"      ✅ Notificación creada para el cliente - ID: {notif_id}")
                else:
                    print(f"      ⚠️ No se pudo crear notificación para cliente")
            else:
                print(f"⚠️ Cliente no registrado con teléfono {telefono_cliente}")
        except Exception as cliente_error:
            print(f"❌ Error creando notificación para cliente: {cliente_error}")
            traceback.print_exc()
        
        print(f"\n✅ [NOTIFICACIONES] Proceso completado: {notificaciones_creadas} notificaciones a admin")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as error:
        print(f"❌ [NOTIFICACIONES] Error crítico: {error}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return False

def notificar_cambio_estado_pedido(orden_id, nuevo_estado):
    """Función para notificar cambio de estado de pedido"""
    try:
        print(f"DEBUG: Ejecutando notificar_cambio_estado_pedido para orden {orden_id}, estado: {nuevo_estado}")
        
        orden = Orden.find_by_id(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación de estado")
            return False
        
        if hasattr(orden, 'to_dict'):
            orden_dict = orden.to_dict()
        else:
            from bson.objectid import ObjectId
            orden_dict = dict(orden)
            if '_id' in orden_dict:
                orden_dict['id'] = str(orden_dict.pop('_id'))
        
        codigo = orden_dict.get('codigo_unico')
        print(f"DEBUG: Notificando cambio de estado del pedido {codigo} a {nuevo_estado}")
        
        notificaciones_creadas = Notificacion.notificar_cambio_estado(orden, nuevo_estado)
        
        print(f"DEBUG: Notificaciones de cambio de estado creadas exitosamente")
        return True
        
    except Exception as error:
        print(f"ERROR al notificar cambio de estado: {error}")
        traceback.print_exc()
        return False

def notificar_pedido_cancelado(orden_id, motivo=None):
    """Notificar cuando un pedido es cancelado"""
    try:
        print(f"DEBUG: Ejecutando notificar_pedido_cancelado para orden {orden_id}")
        
        orden = Orden.find_by_id(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación de cancelación")
            return False
        
        if hasattr(orden, 'to_dict'):
            orden_dict = orden.to_dict()
        else:
            from bson.objectid import ObjectId
            orden_dict = dict(orden)
            if '_id' in orden_dict:
                orden_dict['id'] = str(orden_dict.pop('_id'))
        
        codigo = orden_dict.get('codigo_unico')
        print(f"DEBUG: Notificando cancelación del pedido {codigo}")
        
        mensaje_admin = f"Pedido {codigo} cancelado"
        if motivo:
            mensaje_admin += f"\nMotivo: {motivo}"
        
        from Models.User import UserRepository
        user_repo = UserRepository()
        admins = user_repo.get_users_by_role(1)
        
        for admin in admins:
            try:
                admin_dict = user_repo.to_dict(admin)
                Notificacion.crear_notificacion(
                    user_id=admin_dict['id'],
                    user_type='admin',
                    tipo='pedido_cancelado',
                    titulo='Pedido Cancelado',
                    mensaje=mensaje_admin,
                    datos_adicionales={
                        'orden_id': orden_dict.get('id'),
                        'codigo_pedido': codigo,
                        'cliente': orden_dict.get('nombre_usuario'),
                        'telefono_cliente': orden_dict.get('telefono_usuario'),
                        'motivo': motivo,
                        'direccion': orden_dict.get('direccion_texto'),
                        'precio_total': float(orden_dict.get('precio_total', 0)),
                        'cantidad': orden_dict.get('cantidad', 1),
                        'suplemento_id': orden_dict.get('suplemento_id')
                    },
                    orden_id=orden_dict.get('id')
                )
            except Exception as admin_error:
                print(f"ERROR al crear notificación de cancelación para admin: {admin_error}")
        
        telefono_cliente = orden_dict.get('telefono_usuario')
        if telefono_cliente:
            cliente = user_repo.find_by_phone(telefono_cliente)
            
            if cliente:
                try:
                    cliente_dict = user_repo.to_dict(cliente)
                    mensaje_cliente = f"Tu pedido {codigo} ha sido cancelado"
                    if motivo:
                        mensaje_cliente += f"\nMotivo: {motivo}"
                    
                    Notificacion.crear_notificacion(
                        user_id=cliente_dict['id'],
                        user_type='cliente',
                        tipo='pedido_cancelado',
                        titulo='Pedido Cancelado',
                        mensaje=mensaje_cliente,
                        datos_adicionales={
                            'orden_id': orden_dict.get('id'),
                            'codigo_pedido': codigo,
                            'motivo': motivo,
                            'direccion': orden_dict.get('direccion_texto')
                        },
                        orden_id=orden_dict.get('id')
                    )
                except Exception as cliente_error:
                    print(f"ERROR al crear notificación de cancelación para cliente: {cliente_error}")
            else:
                print(f"DEBUG: No se encontró usuario cliente con teléfono {telefono_cliente}")
        
        print(f"DEBUG: Notificaciones de cancelación creadas exitosamente")
        return True
        
    except Exception as error:
        print(f"ERROR al notificar pedido cancelado: {error}")
        traceback.print_exc()
        return False

def notificar_suplemento_no_disponible(suplemento_id, fecha=None, motivo=None, es_inactivo=False):
    """Notificar a los usuarios que tienen pedidos con un suplemento no disponible o inactivo"""
    try:
        tipo_notificacion = 'suplemento_inactivo' if es_inactivo else 'suplemento_no_disponible'
        
        print(f"[NOTIFICACIONES] ========== {'SUPLEMENTO INACTIVO' if es_inactivo else 'SUPLEMENTO NO DISPONIBLE'} ==========")
        print(f"Suplemento ID: {suplemento_id}")
        print(f"Fecha afectada: {fecha}")
        print(f"Motivo: {motivo}")
        print(f"Tipo notificación: {tipo_notificacion}")
        print(f"Es inactivo (permanente): {es_inactivo}")
        
        # Obtener el suplemento
        suplemento = Suplemento.find_by_id(suplemento_id)
        
        if not suplemento:
            print(f"ERROR: Suplemento {suplemento_id} no encontrado")
            return {'success': False, 'error': 'Suplemento no encontrado'}
        
        suplemento_nombre = suplemento.nombre if hasattr(suplemento, 'nombre') else suplemento.get('nombre')
        suplemento_categoria = suplemento.categoria if hasattr(suplemento, 'categoria') else suplemento.get('categoria')
        
        if es_inactivo:
            fecha_descripcion = "permanentemente"
            titulo_base_cliente = f'Suplemento Desactivado: {suplemento_nombre}'
            titulo_base_admin = f'SUPLEMENTO INACTIVO: {suplemento_nombre}'
        else:
            fecha_descripcion = fecha if fecha else "hoy"
            titulo_base_cliente = f'⚠️ Suplemento no disponible'
            titulo_base_admin = f'⚠️ SUPLEMENTO NO DISPONIBLE: {suplemento_nombre}'
        
        print(f"Suplemento encontrado: {suplemento_nombre} ({suplemento_categoria})")
        
        # Buscar órdenes PENDIENTES o EN PROCESO que contengan este suplemento
        from Models.Ordenes import Orden
        
        estados_activos = ['pendiente', 'confirmada', 'pagada', 'en_preparacion']
        todas_ordenes = Orden.get_all_ordenes()
        
        print(f"Total órdenes: {len(todas_ordenes)}")
        
        usuarios_notificados = set()
        ordenes_afectadas = []
        
        for orden in todas_ordenes:
            try:
                if hasattr(orden, 'estado'):
                    estado_orden = orden.estado
                    suplemento_id_orden = orden.suplemento_id
                    tipo_pedido = orden.tipo_pedido
                    pedido_json = orden.pedido_json
                else:
                    estado_orden = orden.get('estado')
                    suplemento_id_orden = orden.get('suplemento_id')
                    tipo_pedido = orden.get('tipo_pedido')
                    pedido_json = orden.get('pedido_json')
                
                if estado_orden not in estados_activos:
                    continue
                
                contiene_suplemento = False
                detalles_pedido = ""
                
                if suplemento_id_orden and str(suplemento_id_orden) == str(suplemento_id):
                    contiene_suplemento = True
                    if hasattr(orden, 'cantidad'):
                        cantidad = orden.cantidad
                    else:
                        cantidad = orden.get('cantidad', 1)
                    detalles_pedido = f"Pedido directo x{cantidad}"
                
                if not contiene_suplemento and pedido_json and tipo_pedido == 'carrito':
                    try:
                        pedido_data = json.loads(pedido_json) if isinstance(pedido_json, str) else pedido_json
                        
                        if isinstance(pedido_data, list):
                            for item in pedido_data:
                                item_id = item.get('suplemento_id')
                                if item_id and str(item_id) == str(suplemento_id):
                                    contiene_suplemento = True
                                    item_cantidad = item.get('cantidad', 1)
                                    detalles_pedido = f"Carrito: {item.get('nombre', 'Suplemento')} x{item_cantidad}"
                                    break
                    except json.JSONDecodeError:
                        pass
                
                if contiene_suplemento:
                    if hasattr(orden, 'codigo_unico'):
                        codigo = orden.codigo_unico
                        cliente_nombre = orden.nombre_usuario
                        cliente_telefono = orden.telefono_usuario
                        direccion = orden.direccion_texto
                        estado = orden.estado
                    else:
                        codigo = orden.get('codigo_unico')
                        cliente_nombre = orden.get('nombre_usuario')
                        cliente_telefono = orden.get('telefono_usuario')
                        direccion = orden.get('direccion_texto')
                        estado = orden.get('estado')
                    
                    print(f"📌 Orden afectada: #{codigo} - Cliente: {cliente_nombre}")
                    ordenes_afectadas.append({
                        'id': str(getattr(orden, 'id', orden.get('id'))),
                        'codigo': codigo,
                        'cliente': cliente_nombre,
                        'telefono': cliente_telefono,
                        'detalles': detalles_pedido,
                        'estado': estado,
                        'direccion': direccion
                    })
                    
                    from Models.User import UserRepository
                    user_repo = UserRepository()
                    usuario_cliente = None
                    if cliente_telefono:
                        usuario_cliente = user_repo.find_by_phone(cliente_telefono)
                    
                    if usuario_cliente:
                        cliente_dict = user_repo.to_dict(usuario_cliente)
                        user_id_cliente = cliente_dict.get('id')
                        
                        if es_inactivo:
                            mensaje_cliente = f"El suplemento '{suplemento_nombre}' ha sido marcado como INACTIVO y ya no estará disponible."
                            if motivo:
                                mensaje_cliente += f" Motivo: {motivo}"
                            mensaje_cliente += f" Esto afecta tu pedido #{codigo}. Por favor contáctanos si necesitas realizar cambios."
                        else:
                            mensaje_cliente = f"El suplemento '{suplemento_nombre}' no está disponible {fecha_descripcion}."
                            if motivo:
                                mensaje_cliente += f" Motivo: {motivo}"
                            mensaje_cliente += f" Esto afecta tu pedido #{codigo}. Por favor contáctanos para realizar ajustes."
                        
                        try:
                            notif_cliente = Notificacion.crear_notificacion(
                                user_id=user_id_cliente,
                                user_type='cliente',
                                tipo=tipo_notificacion,
                                titulo=titulo_base_cliente,
                                mensaje=mensaje_cliente,
                                datos_adicionales={
                                    'orden_id': str(getattr(orden, 'id', orden.get('id'))),
                                    'codigo_pedido': codigo,
                                    'suplemento_no_disponible': suplemento_nombre,
                                    'suplemento_id': suplemento_id,
                                    'fecha_afectada': fecha_descripcion,
                                    'motivo': motivo,
                                    'estado_orden': estado,
                                    'cliente_telefono': cliente_telefono,
                                    'cliente_nombre': cliente_nombre,
                                    'es_inactivo': es_inactivo,
                                    'detalles_pedido': detalles_pedido,
                                    'direccion': direccion,
                                    'precio_orden': float(orden.precio_total if hasattr(orden, 'precio_total') else orden.get('precio_total', 0))
                                },
                                orden_id=str(getattr(orden, 'id', orden.get('id')))
                            )
                            
                            usuarios_notificados.add(user_id_cliente)
                            print(f"Notificación {tipo_notificacion} enviada al cliente ID: {user_id_cliente}")
                            
                        except Exception as cliente_error:
                            print(f"Error notificando cliente {user_id_cliente}: {cliente_error}")
                    else:
                        print(f"⚠️ Usuario no encontrado para teléfono: {cliente_telefono}")
            
            except Exception as orden_error:
                print(f"Error procesando orden: {orden_error}")
                continue
        
        from Models.User import UserRepository
        user_repo = UserRepository()
        admins = user_repo.get_users_by_role(1)
        notificaciones_admin = 0
        
        mensaje_admin = f"{'SUPLEMENTO MARCADO COMO INACTIVO' if es_inactivo else 'SUPLEMENTO NO DISPONIBLE'}: '{suplemento_nombre}' ({suplemento_categoria})"
        if motivo:
            mensaje_admin += f"\nMOTIVO: {motivo}"
        mensaje_admin += f"\n\nIMPACTO:"
        mensaje_admin += f"\n• Órdenes afectadas: {len(ordenes_afectadas)}"
        mensaje_admin += f"\n• Clientes notificados: {len(usuarios_notificados)}"
        if not es_inactivo:
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
                admin_dict = user_repo.to_dict(admin)
                Notificacion.crear_notificacion(
                    user_id=admin_dict['id'],
                    user_type='admin',
                    tipo=tipo_notificacion,
                    titulo=titulo_base_admin,
                    mensaje=mensaje_admin,
                    datos_adicionales={
                        'suplemento_id': suplemento_id,
                        'suplemento_nombre': suplemento_nombre,
                        'suplemento_categoria': suplemento_categoria,
                        'fecha_afectada': fecha_descripcion,
                        'motivo': motivo,
                        'es_inactivo': es_inactivo,
                        'ordenes_afectadas': [o['id'] for o in ordenes_afectadas],
                        'ordenes_detalles': ordenes_afectadas,
                        'total_afectadas': len(ordenes_afectadas),
                        'usuarios_notificados': list(usuarios_notificados),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                notificaciones_admin += 1
                print(f"Notificación {tipo_notificacion} enviada al admin ID: {admin_dict['id']}")
            except Exception as admin_error:
                print(f"Error notificando admin: {admin_error}")
        
        print(f"\n📊 RESUMEN FINAL:")
        print(f"   • Suplemento: {suplemento_nombre}")
        print(f"   • Tipo: {'INACTIVO (permanente)' if es_inactivo else 'NO DISPONIBLE (temporal)'}")
        print(f"   • Fecha: {fecha_descripcion}")
        print(f"   • Órdenes afectadas: {len(ordenes_afectadas)}")
        print(f"   • Clientes notificados: {len(usuarios_notificados)}")
        print(f"   • Admins notificados: {notificaciones_admin}")
        print(f"[NOTIFICACIONES] ========== FIN ==========\n")
        
        resultado = {
            'success': True,
            'suplemento': {
                'id': suplemento_id,
                'nombre': suplemento_nombre,
                'categoria': suplemento_categoria
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
        
        return resultado
        
    except Exception as error:
        print(f"ERROR CRÍTICO en notificar_suplemento_no_disponible: {error}")
        traceback.print_exc()
        return {'success': False, 'error': str(error)}

# ===== FUNCIONES API =====

@jwt_required()
def obtener_notificaciones_usuario():
    """Obtener notificaciones del usuario actual"""
    try:
        print(f"\n🔵 [API] obtener_notificaciones_usuario - INICIANDO")
        
        user_id = get_jwt_identity()
        print(f"👤 user_id: {user_id}")
        
        usuario = user_repo.find_by_id(user_id)
        if not usuario:
            print(f"❌ Usuario no encontrado")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        print(f"📊 user_type: {user_type}")
        
        pagina = request.args.get('page', 1, type=int)
        por_pagina = request.args.get('per_page', 20, type=int)
        print(f"📄 página: {pagina}, por_página: {por_pagina}")
        
        resultado = Notificacion.obtener_notificaciones_usuario_query(
            user_id=user_id,
            user_type=user_type,
            pagina=pagina,
            por_pagina=por_pagina
        )
        
        print(f"📊 Total notificaciones: {resultado['total']}")
        
        notificaciones_dict = [Notificacion.to_dict(notif) for notif in resultado['notificaciones']]
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total': resultado['total'],
            'pagina_actual': resultado['pagina_actual'],
            'total_paginas': resultado['total_paginas']
        }), 200
        
    except Exception as error:
        print(f"❌ Error en obtener_notificaciones_usuario: {error}")
        traceback.print_exc()
        return jsonify({"msg": f"Error al obtener notificaciones: {str(error)}"}), 500

@jwt_required()
def obtener_notificaciones_no_leidas():
    """Obtener notificaciones no leídas del usuario"""
    try:
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        
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
        print(f"\n🔵 [CONTROLADOR] marcar_como_leida - INICIANDO")
        print(f"📌 notificacion_id: {notificacion_id} (tipo: {type(notificacion_id)})")
        
        user_id = get_jwt_identity()
        print(f"👤 user_id del token: {user_id} (tipo: {type(user_id)})")
        
        notificacion = Notificacion.find_by_id(notificacion_id)
        if not notificacion:
            print(f"❌ Notificación {notificacion_id} NO encontrada")
            return jsonify({"msg": "Notificación no encontrada"}), 404
        
        print(f"✅ Notificación encontrada")
        
        if hasattr(notificacion, 'user_id'):
            notif_user_id = notificacion.user_id
            print(f"📊 Notificación.user_id (SQL): {notif_user_id} (tipo: {type(notif_user_id)})")
        else:
            notif_user_id = notificacion.get('user_id')
            print(f"📊 Notificación.user_id (Mongo): {notif_user_id} (tipo: {type(notif_user_id)})")
        
        if str(notif_user_id) != str(user_id):
            print(f"❌ No tienes permiso: tu user_id={user_id}, notif_user_id={notif_user_id}")
            return jsonify({"msg": "No tienes permiso para marcar esta notificación"}), 403
        
        print(f"🔄 Llamando a Notificacion.marcar_como_leida({notificacion_id})")
        resultado = Notificacion.marcar_como_leida(notificacion_id)
        print(f"📝 Resultado de marcar_como_leida: {resultado}")
        
        if resultado:
            print(f"✅ Notificación {notificacion_id} marcada como leída exitosamente")
            return jsonify({"msg": "Notificación marcada como leída"}), 200
        else:
            print(f"ℹ️ La notificación {notificacion_id} ya estaba leída")
            return jsonify({"msg": "La notificación ya estaba leída"}), 200
            
    except Exception as error:
        print(f"❌ Error al marcar notificación como leída: {error}")
        traceback.print_exc()
        return jsonify({"msg": f"Error al marcar notificación como leída: {str(error)}"}), 500

@jwt_required()
def marcar_todas_como_leidas():
    """Marcar todas las notificaciones del usuario como leídas"""
    try:
        print(f"\n🔵 [CONTROLADOR] marcar_todas_como_leidas - INICIANDO")
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        print(f"👤 user_id: {user_id}, user_type: {user_type}")
        
        cantidad = Notificacion.marcar_todas_como_leidas(user_id, user_type)
        print(f"📝 Notificaciones marcadas: {cantidad}")
        
        return jsonify({
            "msg": f"Se marcaron {cantidad} notificaciones como leídas"
        }), 200
        
    except Exception as error:
        print(f"Error al marcar todas las notificaciones como leídas: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al marcar notificaciones como leídas"}), 500

@jwt_required()
def eliminar_notificacion(notificacion_id):
    """Eliminar una notificación (solo el propietario puede hacerlo)"""
    try:
        print(f"\n🔵 [CONTROLADOR] eliminar_notificacion - INICIANDO")
        print(f"📌 notificacion_id: {notificacion_id}")
        
        user_id = get_jwt_identity()
        print(f"👤 user_id del token: {user_id}")
        
        notificacion = Notificacion.find_by_id(notificacion_id)
        if not notificacion:
            return jsonify({"msg": "Notificación no encontrada"}), 404
        
        if hasattr(notificacion, 'user_id'):
            notif_user_id = notificacion.user_id
        else:
            notif_user_id = notificacion.get('user_id')
        
        if str(notif_user_id) != str(user_id):
            print(f"❌ No tienes permiso: tu user_id={user_id}, notif_user_id={notif_user_id}")
            return jsonify({"msg": "No tienes permiso para eliminar esta notificación"}), 403
        
        if Notificacion.eliminar_notificacion(notificacion_id):
            print(f"✅ Notificación {notificacion_id} eliminada correctamente")
            return jsonify({"msg": "Notificación eliminada correctamente"}), 200
        else:
            print(f"❌ Error al eliminar notificación {notificacion_id}")
            return jsonify({"msg": "Error al eliminar la notificación"}), 500
            
    except Exception as error:
        print(f"Error al eliminar notificación: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al eliminar notificación"}), 500

@jwt_required()
def eliminar_todas_leidas():
    """Eliminar todas las notificaciones leídas del usuario"""
    try:
        print(f"\n🔵 [CONTROLADOR] eliminar_todas_leidas - INICIANDO")
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        
        cantidad = Notificacion.eliminar_todas_leidas(user_id, user_type)
        print(f"📝 Notificaciones eliminadas: {cantidad}")
        
        return jsonify({
            "msg": f"Se eliminaron {cantidad} notificaciones leídas"
        }), 200
        
    except Exception as error:
        print(f"Error al eliminar notificaciones leídas: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al eliminar notificaciones"}), 500

@jwt_required()
def enviar_mensaje():
    """Enviar mensaje/notificación a usuarios (solo admin)"""
    try:
        print(f"\n🔵 [CONTROLADOR] enviar_mensaje - INICIANDO")
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No se proporcionaron datos"}), 400
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        if usuario_dict.get('rol') != 1:
            return jsonify({"msg": "Solo los administradores pueden enviar mensajes"}), 403
        
        destinatario_tipo = data.get('destinatario_tipo', 'todos')
        destinatario_id = data.get('destinatario_id')
        titulo = data.get('titulo', 'Mensaje del Administrador')
        mensaje = data.get('mensaje')
        
        if not mensaje or not mensaje.strip():
            return jsonify({"msg": "El mensaje es requerido"}), 400
        
        datos_adicionales = {'remitente': usuario_dict.get('nombre')}
        
        notificaciones_creadas = []
        
        if destinatario_tipo == 'todos':
            clientes = user_repo.get_users_by_role(2)
            for cliente in clientes:
                cliente_dict = user_repo.to_dict(cliente)
                notificacion = Notificacion.crear_notificacion(
                    user_id=cliente_dict['id'],
                    user_type='cliente',
                    tipo='mensaje_admin',
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=datos_adicionales
                )
                if notificacion:
                    notif_id = notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id')
                    notificaciones_creadas.append(notif_id)
                
        elif destinatario_tipo == 'cliente' and destinatario_id:
            cliente = user_repo.find_by_id(destinatario_id)
            if not cliente:
                return jsonify({"msg": "Cliente no encontrado"}), 404
            
            cliente_dict = user_repo.to_dict(cliente)
            notificacion = Notificacion.crear_notificacion(
                user_id=cliente_dict['id'],
                user_type='cliente',
                tipo='mensaje_admin',
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
            if notificacion:
                notif_id = notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id')
                notificaciones_creadas.append(notif_id)
            
        elif destinatario_tipo == 'admin' and destinatario_id:
            admin = user_repo.find_by_id(destinatario_id)
            if not admin:
                return jsonify({"msg": "Administrador no encontrado"}), 404
            
            admin_dict = user_repo.to_dict(admin)
            if admin_dict.get('rol') != 1:
                return jsonify({"msg": "El usuario seleccionado no es administrador"}), 400
            
            notificacion = Notificacion.crear_notificacion(
                user_id=admin_dict['id'],
                user_type='admin',
                tipo='mensaje_admin',
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
            if notificacion:
                notif_id = notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id')
                notificaciones_creadas.append(notif_id)
            
        elif destinatario_tipo == 'todos_admins':
            admins = user_repo.get_users_by_role(1)
            for admin in admins:
                admin_dict = user_repo.to_dict(admin)
                notificacion = Notificacion.crear_notificacion(
                    user_id=admin_dict['id'],
                    user_type='admin',
                    tipo='mensaje_admin',
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=datos_adicionales
                )
                if notificacion:
                    notif_id = notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id')
                    notificaciones_creadas.append(notif_id)
        
        return jsonify({
            "msg": f"Mensaje enviado correctamente a {len(notificaciones_creadas)} usuarios",
            "notificaciones_enviadas": len(notificaciones_creadas)
        }), 201
        
    except Exception as error:
        print(f"Error al enviar mensaje: {error}")
        traceback.print_exc()
        return jsonify({"msg": f"Error al enviar mensaje: {str(error)}"}), 500

@jwt_required()
def obtener_analiticas():
    """Obtener analíticas de notificaciones (solo admin)"""
    try:
        print(f"\n🔵 [CONTROLADOR] obtener_analiticas - INICIANDO")
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        if usuario_dict.get('rol') != 1:
            return jsonify({"msg": "Solo los administradores pueden ver analíticas"}), 403
        
        dias = request.args.get('dias', 30, type=int)
        analiticas = Notificacion.obtener_analiticas(dias)
        
        return jsonify(analiticas), 200
        
    except Exception as error:
        print(f"Error al obtener analíticas: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener analíticas"}), 500

@jwt_required()
def obtener_usuarios_para_mensaje():
    """Obtener lista de usuarios para enviar mensajes (solo admin)"""
    try:
        print(f"\n🔵 [CONTROLADOR] obtener_usuarios_para_mensaje - INICIANDO")
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        if usuario_dict.get('rol') != 1:
            return jsonify({"msg": "Solo los administradores pueden ver esta lista"}), 403
        
        usuarios = user_repo.get_all_users()
        
        usuarios_dict = []
        for user in usuarios:
            user_dict = user_repo.to_dict(user)
            usuarios_dict.append({
                'id': user_dict.get('id'),
                'nombre': user_dict.get('nombre'),
                'email': user_dict.get('correo'),
                'telefono': user_dict.get('telefono'),
                'rol': user_dict.get('rol'),
                'rol_nombre': 'Administrador' if user_dict.get('rol') == 1 else 'Cliente'
            })
        
        print(f"📊 Usuarios encontrados: {len(usuarios_dict)}")
        return jsonify(usuarios_dict), 200
        
    except Exception as error:
        print(f"Error al obtener usuarios: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener usuarios"}), 500

@jwt_required()
def obtener_notificaciones_por_orden(orden_id):
    """Obtener notificaciones relacionadas con una orden específica"""
    try:
        print(f"\n🔵 [CONTROLADOR] obtener_notificaciones_por_orden - INICIANDO")
        print(f"📌 orden_id: {orden_id}")
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        
        orden = Orden.find_by_id(orden_id)
        if not orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        if hasattr(orden, 'telefono_usuario'):
            orden_telefono = orden.telefono_usuario
        else:
            orden_telefono = orden.get('telefono_usuario')
        
        es_admin = usuario_dict.get('rol') == 1
        es_dueño = orden_telefono == usuario_dict.get('telefono') if usuario_dict.get('telefono') else False
        
        if not es_admin and not es_dueño:
            return jsonify({"msg": "No tienes permisos para ver estas notificaciones"}), 403
        
        if hasattr(Notificacion, 'query'):
            notificaciones = Notificacion.query.filter_by(orden_id=orden_id).order_by(
                Notificacion.fecha_creacion.desc()
            ).all()
        else:
            notificaciones = list(Notificacion._get_collection().find(
                {'orden_id': str(orden_id)}
            ).sort('fecha_creacion', -1))
        
        notificaciones_dict = [Notificacion.to_dict(notif) for notif in notificaciones]
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total': len(notificaciones_dict)
        }), 200
        
    except Exception as error:
        print(f"Error al obtener notificaciones por orden: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener notificaciones"}), 500

@jwt_required()
def obtener_contador_notificaciones():
    """Obtener contador de notificaciones no leídas"""
    try:
        print(f"\n🔵 [CONTROLADOR] obtener_contador_notificaciones - INICIANDO")
        
        user_id = get_jwt_identity()
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        
        notificaciones = Notificacion.obtener_notificaciones_no_leidas(user_id, user_type)
        
        notificaciones_recientes = []
        for n in notificaciones[:5]:
            n_dict = Notificacion.to_dict(n)
            notificaciones_recientes.append({
                'id': n_dict.get('id'),
                'titulo': n_dict.get('titulo'),
                'mensaje': n_dict.get('mensaje')[:100] + '...' if len(n_dict.get('mensaje', '')) > 100 else n_dict.get('mensaje'),
                'tipo': n_dict.get('tipo'),
                'fecha_creacion': n_dict.get('fecha_creacion')
            })
        
        return jsonify({
            'total_no_leidas': len(notificaciones),
            'notificaciones_recientes': notificaciones_recientes
        }), 200
        
    except Exception as error:
        print(f"Error al obtener contador de notificaciones: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener contador de notificaciones"}), 500

def create_notification(user_id, titulo, mensaje, tipo='info', datos_adicionales=None):
    """Crear notificación para un usuario"""
    try:
        from Models.Notificaciones import Notificacion
        from Models.User import user_repo
        
        user = user_repo.find_by_id(user_id)
        if not user:
            print(f"Usuario {user_id} no encontrado")
            return None
        
        user_dict = user_repo.to_dict(user)
        user_type = 'admin' if user_dict.get('rol') == 1 else 'cliente'
        
        if tipo == 'backup_code':
            if datos_adicionales is None:
                datos_adicionales = {}
            datos_adicionales['permanent'] = True
            datos_adicionales['warning'] = 'Este código es permanente. Guárdalo en un lugar seguro. No se mostrará nuevamente después de cerrar esta notificación.'
        
        notificacion = Notificacion.crear_notificacion(
            user_id=user_id,
            user_type=user_type,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_adicionales=datos_adicionales or {}
        )
        return notificacion
    except Exception as e:
        print(f"Error creando notificación: {e}")
        import traceback
        traceback.print_exc()
        return None