from Models.Notificaciones import Notificacion
from Models.Ordenes import Orden
from Models.Especiales import Especial
from Models.User import UserRepository
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
import config
from config import db

# Instancia del repositorio de usuarios
user_repo = UserRepository()

def notificar_nuevo_pedido(orden_id):
    """Función para notificar nuevo pedido - VERSIÓN PARA CARRITO (COMPATIBLE CON AMBAS DBs)"""
    try:
        print(f"\n{'='*60}")
        print(f"🔔 [NOTIFICACIONES] notificar_nuevo_pedido - INICIANDO")
        print(f"📦 Orden ID recibido: {orden_id}")
        print(f"{'='*60}")
        
        # Buscar la orden usando el método del modelo (compatible con ambas DBs)
        from Models.Ordenes import Orden
        orden = Orden.find_by_id(orden_id)
        
        if not orden:
            print(f"❌ [NOTIFICACIONES] Orden {orden_id} NO encontrada en la base de datos")
            return False
        
        # Convertir a diccionario según el tipo
        if hasattr(orden, 'to_dict'):
            orden_dict = orden.to_dict()
        else:
            from bson.objectid import ObjectId
            orden_dict = dict(orden)
            if '_id' in orden_dict:
                orden_dict['id'] = str(orden_dict.pop('_id'))
        
        print(f"✅ [NOTIFICACIONES] Orden encontrada:")
        print(f"   - ID: {orden_dict.get('id')}")
        print(f"   - Código: {orden_dict.get('codigo_unico')}")
        print(f"   - Cliente: {orden_dict.get('nombre_usuario')}")
        print(f"   - Teléfono: {orden_dict.get('telefono_usuario')}")
        print(f"   - Tipo pedido: {orden_dict.get('tipo_pedido')}")
        print(f"   - Método pago: {orden_dict.get('metodo_pago', 'efectivo')}")
        
        # 1. Obtener detalles del pedido según tipo
        detalles_pedido = ""
        producto_nombre = ""
        items_info = []
        
        if orden_dict.get('tipo_pedido') == 'especial':
            print(f"   📋 Pedido ESPECIAL detectado")
            if orden_dict.get('especial_id'):
                from Models.Especiales import Especial
                especial = Especial.find_by_id(orden_dict['especial_id'])
                if especial:
                    if hasattr(especial, 'to_dict'):
                        especial_dict = especial.to_dict()
                    else:
                        especial_dict = dict(especial)
                    producto_nombre = especial_dict.get('nombre')
                    detalles_pedido = f"{especial_dict.get('nombre')}"
                    print(f"      Especial: {producto_nombre}")
                else:
                    detalles_pedido = "Producto Especial"
            else:
                detalles_pedido = "Producto Especial"
                
        elif orden_dict.get('tipo_pedido') == 'personalizado':
            print(f"   📋 Pedido PERSONALIZADO detectado")
            producto_nombre = "Pedido Personalizado"
            if orden_dict.get('ingredientes_personalizados'):
                ingredientes = orden_dict['ingredientes_personalizados'].split(',')
                primeros_ingredientes = ingredientes[:3]
                detalles_pedido = f"Personalizado: {', '.join(primeros_ingredientes).strip()}"
                if len(ingredientes) > 3:
                    detalles_pedido += " y más..."
                print(f"      Ingredientes: {len(ingredientes)} seleccionados")
            else:
                detalles_pedido = "Pedido Personalizado"
        
        elif orden_dict.get('tipo_pedido') == 'carrito':
            print(f"   📋 Pedido CARRITO detectado")
            producto_nombre = "Pedido del Carrito"
            
            if orden_dict.get('pedido_json'):
                try:
                    pedido_data = json.loads(orden_dict['pedido_json'])
                    if isinstance(pedido_data, dict) and 'items' in pedido_data:
                        items = pedido_data['items']
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
                    info_pago = json.loads(orden_dict['info_pago_json'])
                    if info_pago.get('ultimos_4'):
                        info_pago_texto += f" (****{info_pago['ultimos_4']})"
                except:
                    pass
        else:
            info_pago_texto = "Pago en efectivo"
        
        print(f"   💰 Información pago: {info_pago_texto}")
        
        # 3. MENSAJES PARA ADMINISTRADORES
        codigo_pedido = orden_dict.get('codigo_unico', '')
        nombre_cliente = orden_dict.get('nombre_usuario', '')
        telefono_cliente = orden_dict.get('telefono_usuario', '')
        precio = float(orden_dict.get('precio', 0))
        
        mensaje_admin = f"NUEVO PEDIDO #{codigo_pedido}\n"
        mensaje_admin += f"Cliente: {nombre_cliente}\n"
        mensaje_admin += f"Tel: {telefono_cliente}\n"
        mensaje_admin += f"Pedido: {detalles_pedido}\n"
        mensaje_admin += f"Método pago: {info_pago_texto}\n"
        mensaje_admin += f"Total: ${precio:.2f}"
        
        if orden_dict.get('notas'):
            mensaje_admin += f"\nNotas: {orden_dict['notas'][:100]}..."
        
        titulo_admin = f"Pedido #{codigo_pedido}"
        
        print(f"\n📧 Mensaje para admin:")
        print(f"   Título: {titulo_admin}")
        print(f"   Mensaje: {mensaje_admin[:100]}...")
        
        # 4. MENSAJES PARA CLIENTES
        mensaje_cliente = f"Tu pedido #{codigo_pedido} ha sido recibido.\n"
        mensaje_cliente += f"Total: ${precio:.2f}\n"
        mensaje_cliente += f"Método pago: {info_pago_texto}\n"
        mensaje_cliente += "Te notificaremos cuando esté en proceso."
        
        titulo_cliente = f"Pedido recibido #{codigo_pedido}"
        
        print(f"\n📧 Mensaje para cliente:")
        print(f"   Título: {titulo_cliente}")
        print(f"   Mensaje: {mensaje_cliente[:100]}...")
        
        # 5. Datos completos
        datos_completos = {
            'orden_id': orden_dict.get('id'),
            'codigo_pedido': codigo_pedido,
            'cliente_nombre': nombre_cliente,
            'telefono_cliente': telefono_cliente,
            'tipo_pedido': orden_dict.get('tipo_pedido'),
            'producto_nombre': producto_nombre,
            'detalles_completos': detalles_pedido,
            'ingredientes_completos': orden_dict.get('ingredientes_personalizados'),
            'precio': precio,
            'direccion_completa': orden_dict.get('direccion_texto'),
            'metodo_pago': orden_dict.get('metodo_pago'),
            'info_pago': orden_dict.get('info_pago_json'),
            'notas': orden_dict.get('notas'),
            'estado': orden_dict.get('estado', 'pendiente'),
            'fecha_pedido': datetime.utcnow().isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Agregar items del carrito si existen
        if orden_dict.get('tipo_pedido') == 'carrito' and orden_dict.get('pedido_json'):
            try:
                pedido_data = json.loads(orden_dict['pedido_json'])
                datos_completos['items_carrito'] = pedido_data.get('items', [])
                datos_completos['total_items'] = len(pedido_data.get('items', []))
            except:
                pass
        
        # 6. Notificar a TODOS los administradores usando el repositorio
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
                    datos_adicionales=datos_completos,
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
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Notificaciones a admin creadas: {notificaciones_creadas}")
        
        # 7. Notificación para el cliente si está registrado
        try:
            print(f"\n🔍 Buscando cliente con teléfono: {telefono_cliente}")
            
            # Buscar cliente por teléfono usando el repositorio si tiene el método
            cliente = None
            if telefono_cliente:
                if hasattr(user_repo, 'find_by_phone'):
                    cliente = user_repo.find_by_phone(telefono_cliente)
                else:
                    # Fallback a consulta directa (solo funciona en MySQL)
                    from Models.User import UserSQL
                    cliente = UserSQL.query.filter_by(telefono=telefono_cliente).first()
            
            if cliente:
                cliente_dict = user_repo.to_dict(cliente) if hasattr(user_repo, 'to_dict') else {'id': cliente.id, 'nombre': cliente.nombre}
                print(f"✅ Cliente registrado encontrado: {cliente_dict.get('nombre')} (ID: {cliente_dict.get('id')})")
                
                from Models.Notificaciones import Notificacion
                notificacion_cliente = Notificacion.crear_notificacion(
                    user_id=cliente_dict.get('id'),
                    user_type='cliente',
                    tipo='confirmacion_pedido',
                    titulo=titulo_cliente,
                    mensaje=mensaje_cliente,
                    datos_adicionales=datos_completos,
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
                print(f"⚠️ Cliente no registrado con teléfono {telefono_cliente}, solo notificaciones a admin")
        except Exception as cliente_error:
            print(f"❌ Error creando notificación para cliente: {cliente_error}")
            import traceback
            traceback.print_exc()
        
        print(f"\n✅ [NOTIFICACIONES] Proceso completado: {notificaciones_creadas} notificaciones a admin")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as error:
        print(f"❌ [NOTIFICACIONES] Error crítico: {error}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return False

def notificar_cambio_estado_pedido(orden_id, nuevo_estado):
    """Función para notificar cambio de estado de pedido"""
    try:
        print(f"DEBUG: Ejecutando notificar_cambio_estado_pedido para orden {orden_id}, estado: {nuevo_estado}")
        
        # Usar find_by_id en lugar de query.get
        orden = Orden.find_by_id(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación de estado")
            return False
        
        codigo = orden.codigo_unico if hasattr(orden, 'codigo_unico') else orden.get('codigo_unico')
        print(f"DEBUG: Notificando cambio de estado del pedido {codigo} a {nuevo_estado}")
        
        # Crear notificaciones usando el método del modelo
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
        
        # Usar find_by_id en lugar de query.get
        orden = Orden.find_by_id(orden_id)
        if not orden:
            print(f"ERROR: Orden {orden_id} no encontrada para notificación de cancelación")
            return False
        
        # Convertir a diccionario
        if hasattr(orden, 'to_dict'):
            orden_dict = orden.to_dict()
        else:
            orden_dict = dict(orden)
        
        codigo = orden_dict.get('codigo_unico')
        print(f"DEBUG: Notificando cancelación del pedido {codigo}")
        
        mensaje_admin = f"Pedido {codigo} cancelado"
        if motivo:
            mensaje_admin += f"\nMotivo: {motivo}"
        
        # Notificar a administradores usando el repositorio
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
                        'precio': float(orden_dict.get('precio', 0))
                    },
                    orden_id=orden_dict.get('id')
                )
            except Exception as admin_error:
                print(f"ERROR al crear notificación de cancelación para admin: {admin_error}")
        
        # Notificación para el cliente
        telefono_cliente = orden_dict.get('telefono_usuario')
        if telefono_cliente:
            # Buscar cliente por teléfono
            from Models.User import UserSQL
            usuario_cliente = UserSQL.query.filter_by(telefono=telefono_cliente).first()
            
            if usuario_cliente:
                try:
                    mensaje_cliente = f"Tu pedido {codigo} ha sido cancelado"
                    if motivo:
                        mensaje_cliente += f"\nMotivo: {motivo}"
                    
                    Notificacion.crear_notificacion_cliente(
                        cliente_id=usuario_cliente.id,
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
                    from Models.User import UserSQL
                    usuario_cliente = None
                    if orden.telefono_usuario:
                        usuario_cliente = UserSQL.query.filter_by(telefono=orden.telefono_usuario).first()
                    
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
                                tipo=tipo_notificacion,
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
        
        # Notificar a TODOS los administradores usando el repositorio
        admins = user_repo.get_users_by_role(1)
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
                admin_dict = user_repo.to_dict(admin)
                Notificacion.crear_notificacion(
                    user_id=admin_dict['id'],
                    user_type='admin',
                    tipo=tipo_notificacion,
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
                print(f"Notificación {tipo_notificacion} enviada al admin ID: {admin_dict['id']}")
            except Exception as admin_error:
                print(f"Error notificando admin: {admin_error}")
        
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
    """Obtener notificaciones del usuario actual usando UserRepository"""
    try:
        # Obtener usuario del token JWT
        user_id = get_jwt_identity()
        
        print(f"\n[API DEBUG] ========== OBTENER NOTIFICACIONES ==========")
        print(f"User ID del token: {user_id}")
        
        # Obtener información del usuario usando el repositorio
        usuario = user_repo.find_by_id(user_id)
        if not usuario:
            print(f"Usuario con ID {user_id} NO encontrado en la base de datos!")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        
        print(f"Usuario encontrado:")
        print(f"   - ID: {usuario_dict.get('id')}")
        print(f"   - Nombre: {usuario_dict.get('nombre')}")
        print(f"   - Teléfono: '{usuario_dict.get('telefono')}'")
        print(f"   - Rol: {usuario_dict.get('rol')} ({'Admin' if usuario_dict.get('rol') == 1 else 'Cliente'})")
        
        # Determinar user_type por ROL
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        print(f"User_type determinado por rol: {user_type}")
        
        # Obtener parámetros
        pagina = request.args.get('page', 1, type=int)
        por_pagina = request.args.get('per_page', 20, type=int)
        
        print(f"Parámetros de consulta:")
        print(f"   - página: {pagina}")
        print(f"   - por página: {por_pagina}")
        
        # Buscar notificaciones
        resultado = Notificacion.obtener_notificaciones_usuario_query(
            user_id=user_id,
            user_type=user_type,
            pagina=pagina,
            por_pagina=por_pagina
        )
        
        print(f"Notificaciones encontradas: {resultado['total']}")
        
        # Convertir a diccionario
        notificaciones_dict = []
        for notif in resultado['notificaciones']:
            notif_dict = Notificacion.to_dict(notif)
            notificaciones_dict.append(notif_dict)
        
        print(f"RESULTADO FINAL:")
        print(f"   - Total notificaciones: {resultado['total']}")
        print(f"   - Mostrando: {len(notificaciones_dict)}")
        print(f"[API DEBUG] ========== FIN ==========\n")
        
        return jsonify({
            'notificaciones': notificaciones_dict,
            'total': resultado['total'],
            'pagina_actual': resultado['pagina_actual'],
            'total_paginas': resultado['total_paginas']
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
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        
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
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        user_type = 'admin' if usuario_dict.get('rol') == 1 else 'cliente'
        
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
        
        # Verificar que el usuario es admin usando el repositorio
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
            # Enviar a todos los clientes
            clientes = user_repo.get_users_by_role(2)
            for cliente in clientes:
                cliente_dict = user_repo.to_dict(cliente)
                notificacion = Notificacion.crear_notificacion_cliente(
                    cliente_id=cliente_dict['id'],
                    tipo='mensaje_admin',
                    titulo=titulo,
                    mensaje=mensaje,
                    datos_adicionales=datos_adicionales
                )
                notificaciones_creadas.append(notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id'))
                
        elif destinatario_tipo == 'cliente' and destinatario_id:
            # Enviar a un cliente específico
            cliente = user_repo.find_by_id(destinatario_id)
            if not cliente:
                return jsonify({"msg": "Cliente no encontrado"}), 404
            
            cliente_dict = user_repo.to_dict(cliente)
            notificacion = Notificacion.crear_notificacion_cliente(
                cliente_id=cliente_dict['id'],
                tipo='mensaje_admin',
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=datos_adicionales
            )
            notificaciones_creadas.append(notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id'))
            
        elif destinatario_tipo == 'admin' and destinatario_id:
            # Enviar a otro administrador
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
            notificaciones_creadas.append(notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id'))
            
        elif destinatario_tipo == 'todos_admins':
            # Enviar a todos los administradores
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
                notificaciones_creadas.append(notificacion.id if hasattr(notificacion, 'id') else notificacion.get('id'))
        
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
        usuario = user_repo.find_by_id(user_id)
        
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
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        if usuario_dict.get('rol') != 1:
            return jsonify({"msg": "Solo los administradores pueden ver esta lista"}), 403
        
        # Obtener todos los usuarios
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
        usuario = user_repo.find_by_id(user_id)
        
        if not usuario:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        usuario_dict = user_repo.to_dict(usuario)
        
        orden = Orden.query.get(orden_id)
        if not orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        # Solo el admin o el dueño de la orden pueden ver sus notificaciones
        es_admin = usuario_dict.get('rol') == 1
        es_dueño = orden.telefono_usuario == usuario_dict.get('telefono') if usuario_dict.get('telefono') else False
        
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
        return jsonify({"msg": "Error al obtener contador de notificaciones"}), 500