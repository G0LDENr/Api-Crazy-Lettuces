from Models.Ordenes import Orden
from Models.Suplementos import Suplemento
from Models.User import User
from flask import jsonify, request
from Controllers.notificacionesController import notificar_nuevo_pedido, notificar_cambio_estado_pedido
from config import db, db_mongo
import json
import traceback

def get_all_ordenes():
    """
    Obtener todas las órdenes
    """
    try:
        ordenes = Orden.get_all_ordenes()
        ordenes_dict = []
        
        for orden in ordenes:
            orden_dict = Orden.to_dict(orden)
            
            # Asegurar que precio_total tenga un valor
            if 'precio_total' not in orden_dict or orden_dict['precio_total'] is None:
                # Intentar obtener de precio_unitario * cantidad
                if 'precio_unitario' in orden_dict and 'cantidad' in orden_dict:
                    orden_dict['precio_total'] = orden_dict['precio_unitario'] * orden_dict['cantidad']
                else:
                    orden_dict['precio_total'] = 0.0
            
            # También asegurar precio para compatibilidad
            orden_dict['precio'] = orden_dict['precio_total']
            
            ordenes_dict.append(orden_dict)
            
        return jsonify(ordenes_dict), 200
    except Exception as error:
        print(f"Error al obtener órdenes: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener las órdenes"}), 500

def get_single_orden(orden_id):
    """
    Obtener una orden por ID
    """
    try:
        orden = Orden.find_by_id(orden_id)
        if not orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        orden_dict = Orden.to_dict(orden)
        
        # Asegurar precio
        if 'precio_total' not in orden_dict or orden_dict['precio_total'] is None:
            if 'precio_unitario' in orden_dict and 'cantidad' in orden_dict:
                orden_dict['precio_total'] = orden_dict['precio_unitario'] * orden_dict['cantidad']
            else:
                orden_dict['precio_total'] = 0.0
        orden_dict['precio'] = orden_dict['precio_total']
        
        return jsonify(orden_dict), 200
    except Exception as error:
        print(f"Error al obtener la orden: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener la orden"}), 500

def get_orden_by_codigo(codigo):
    """
    Obtener orden por código único
    """
    try:
        orden = Orden.find_by_codigo(codigo)
        if not orden:
            return jsonify({"msg": "Código no encontrado"}), 404
        
        orden_dict = Orden.to_dict(orden)
        
        # Asegurar precio
        if 'precio_total' not in orden_dict or orden_dict['precio_total'] is None:
            if 'precio_unitario' in orden_dict and 'cantidad' in orden_dict:
                orden_dict['precio_total'] = orden_dict['precio_unitario'] * orden_dict['cantidad']
            else:
                orden_dict['precio_total'] = 0.0
        orden_dict['precio'] = orden_dict['precio_total']
        
        return jsonify(orden_dict), 200
    except Exception as error:
        print(f"Error al buscar orden por código: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al buscar la orden"}), 500

def create_orden_completa():
    """
    Crear nueva orden de suplementos - VERSIÓN PARA CARRITO
    """
    try:
        data = request.get_json()
        
        print("="*60)
        print("[CONTROLADOR] ===== INICIO CREACIÓN DE ORDEN =====")
        print(f"[CONTROLADOR] Datos completos recibidos:")
        print(json.dumps(data, indent=2, default=str))
        print("="*60)
        
        # Validaciones básicas
        required_fields = ['nombre_usuario', 'telefono_usuario', 'tipo_pedido']
        for field in required_fields:
            if field not in data:
                print(f"[CONTROLADOR] ❌ Campo requerido faltante: {field}")
                return jsonify({"msg": f"Campo requerido: {field}"}), 400
            print(f"[CONTROLADOR] ✅ Campo {field}: {data.get(field)}")
        
        # Validar tipo de pedido
        tipos_validos = ['suplemento', 'carrito']
        if data['tipo_pedido'] not in tipos_validos:
            print(f"[CONTROLADOR] ❌ Tipo de pedido inválido: {data['tipo_pedido']}")
            return jsonify({"msg": f"Tipo de pedido inválido. Use: {', '.join(tipos_validos)}"}), 400
        
        cantidad = data.get('cantidad', 1)
        precio_unitario = 0.0
        precio_total = 0.0
        
        if data['tipo_pedido'] == 'suplemento':
            # Validación para suplemento individual
            suplemento_id = data.get('suplemento_id')
            if not suplemento_id:
                print(f"[CONTROLADOR] ❌ Falta suplemento_id para pedido tipo suplemento")
                return jsonify({"msg": "Debe seleccionar un suplemento"}), 400
            
            suplemento = Suplemento.find_by_id(suplemento_id)
            if not suplemento:
                print(f"[CONTROLADOR] ❌ Suplemento no encontrado: {suplemento_id}")
                return jsonify({"msg": "Suplemento no encontrado"}), 404
            
            # Verificar activo y stock
            if hasattr(suplemento, 'activo'):  # Es objeto SQL
                if not suplemento.activo:
                    return jsonify({"msg": "El suplemento seleccionado no está disponible"}), 400
                if suplemento.stock < cantidad:
                    return jsonify({"msg": f"Stock insuficiente. Disponible: {suplemento.stock}"}), 400
                precio_unitario = float(suplemento.precio)
            elif isinstance(suplemento, dict):  # Es diccionario de MongoDB
                if not suplemento.get('activo', True):
                    return jsonify({"msg": "El suplemento seleccionado no está disponible"}), 400
                if suplemento.get('stock', 0) < cantidad:
                    return jsonify({"msg": f"Stock insuficiente. Disponible: {suplemento.get('stock', 0)}"}), 400
                precio_unitario = float(suplemento.get('precio', 0))
            
            precio_total = precio_unitario * cantidad
            
        elif data['tipo_pedido'] == 'carrito':
            # Validación para carrito con múltiples productos
            if 'pedido_json' not in data:
                print(f"[CONTROLADOR] ❌ Falta pedido_json para carrito")
                return jsonify({"msg": "Falta información del carrito (pedido_json)"}), 400
            
            # Verificar que el pedido_json sea válido
            try:
                pedido_json = data['pedido_json']
                print(f"[CONTROLADOR] pedido_json tipo: {type(pedido_json)}")
                print(f"[CONTROLADOR] pedido_json contenido: {pedido_json}")
                
                carrito_data = json.loads(pedido_json) if isinstance(pedido_json, str) else pedido_json
                print(f"[CONTROLADOR] carrito_data parseado: {json.dumps(carrito_data, indent=2)}")
                
                # Extraer los items del carrito
                if isinstance(carrito_data, dict):
                    items = carrito_data.get('items', [])
                    print(f"[CONTROLADOR] Items extraídos del diccionario: {len(items)} items")
                elif isinstance(carrito_data, list):
                    items = carrito_data
                    print(f"[CONTROLADOR] Items directamente de la lista: {len(items)} items")
                else:
                    print(f"[CONTROLADOR] ❌ Formato de carrito no válido: {type(carrito_data)}")
                    return jsonify({"msg": "Formato de carrito no válido"}), 400
                
                if not isinstance(items, list):
                    print(f"[CONTROLADOR] ❌ items no es una lista, es: {type(items)}")
                    return jsonify({"msg": "Los items del carrito deben ser una lista"}), 400
                
                if len(items) == 0:
                    print(f"[CONTROLADOR] ❌ carrito vacío")
                    return jsonify({"msg": "El carrito está vacío"}), 400
                
                # Calcular precio total y verificar stock de cada producto
                precio_total = 0
                for i, item in enumerate(items):
                    print(f"[CONTROLADOR] Procesando item {i}: {item}")
                    
                    if not item.get('suplemento_id'):
                        print(f"[CONTROLADOR] ❌ Item sin suplemento_id: {item}")
                        return jsonify({"msg": f"Item {i+1} del carrito sin suplemento_id"}), 400
                    
                    suplemento = Suplemento.find_by_id(item['suplemento_id'])
                    if not suplemento:
                        print(f"[CONTROLADOR] ❌ Suplemento no encontrado: {item.get('suplemento_id')}")
                        return jsonify({"msg": f"Suplemento con ID {item.get('suplemento_id')} no encontrado"}), 404
                    
                    # Verificar activo
                    if hasattr(suplemento, 'activo') and not suplemento.activo:
                        return jsonify({"msg": f"Suplemento {item.get('nombre', 'desconocido')} no está disponible"}), 400
                    elif isinstance(suplemento, dict) and not suplemento.get('activo', True):
                        return jsonify({"msg": f"Suplemento {item.get('nombre', 'desconocido')} no está disponible"}), 400
                    
                    # Verificar stock
                    item_cantidad = item.get('cantidad', 1)
                    if hasattr(suplemento, 'stock') and suplemento.stock < item_cantidad:
                        return jsonify({"msg": f"Stock insuficiente para {item.get('nombre')}. Disponible: {suplemento.stock}"}), 400
                    elif isinstance(suplemento, dict) and suplemento.get('stock', 0) < item_cantidad:
                        return jsonify({"msg": f"Stock insuficiente para {item.get('nombre')}. Disponible: {suplemento.get('stock', 0)}"}), 400
                    
                    # Calcular precio del item
                    if hasattr(suplemento, 'precio'):
                        item_precio = float(suplemento.precio) * item_cantidad
                    else:
                        item_precio = float(suplemento.get('precio', 0)) * item_cantidad
                    
                    precio_total += item_precio
                    print(f"[CONTROLADOR] Item {i+1}: precio = {item_precio}, subtotal acumulado = {precio_total}")
                
            except json.JSONDecodeError as e:
                print(f"[CONTROLADOR] ❌ Error parseando JSON: {e}")
                return jsonify({"msg": "Formato de pedido_json inválido"}), 400
        
        # Si viene precio_total en los datos, verificar que coincida (opcional)
        if 'precio_total' in data and data['precio_total']:
            precio_enviado = float(data['precio_total'])
            if abs(precio_enviado - precio_total) > 0.01:
                print(f"[CONTROLADOR] ❌ Precio no coincide: enviado={precio_enviado}, calculado={precio_total}")
                return jsonify({"msg": "El precio calculado no coincide con el proporcionado"}), 400
        
        # Preparar datos para crear la orden
        orden_data = {
            'nombre_usuario': data['nombre_usuario'].strip(),
            'telefono_usuario': data['telefono_usuario'].strip(),
            'tipo_pedido': data['tipo_pedido'],
            'suplemento_id': data.get('suplemento_id'),
            'direccion_texto': data.get('direccion_texto'),
            'direccion_id': data.get('direccion_id'),
            'pedido_json': data.get('pedido_json'),
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'precio_total': precio_total,
            'estado': 'pendiente',
            'metodo_pago': data.get('metodo_pago', 'efectivo'),
            'notas': data.get('notas'),
            'info_pago': data.get('info_pago'),
            'tarjeta_id': data.get('tarjeta_id')
        }
        
        print(f"[CONTROLADOR] ✅ Datos validados correctamente")
        print(f"[CONTROLADOR] Datos de orden a crear:")
        print(json.dumps({k: str(v) if k == 'pedido_json' else v for k, v in orden_data.items()}, indent=2, default=str))
        
        # Crear nueva orden
        orden_id = Orden.create_orden(orden_data)
        print(f"[CONTROLADOR] 🔔 Orden creada con ID: {orden_id} (tipo: {type(orden_id)})")
        
        # Verificar que la orden existe
        orden_verificada = Orden.find_by_id(orden_id)
        if orden_verificada:
            print(f"[CONTROLADOR] ✅ Orden verificada en BD")
            if hasattr(orden_verificada, 'codigo_unico'):
                print(f"[CONTROLADOR] Código único: {orden_verificada.codigo_unico}")
            else:
                print(f"[CONTROLADOR] Código único: {orden_verificada.get('codigo_unico')}")
        else:
            print(f"[CONTROLADOR] ❌ NO se pudo verificar la orden en BD")
        
        orden = Orden.find_by_id(orden_id)
        
        if not orden:
            print(f"[CONTROLADOR] ❌ Error al obtener la orden creada")
            return jsonify({"msg": "Error al obtener la orden creada"}), 500
        
        # Obtener ID y código según el tipo de DB
        if hasattr(orden, 'id'):
            orden_id_val = orden.id
            codigo_val = orden.codigo_unico
        else:
            orden_id_val = orden.get('_id')
            codigo_val = orden.get('codigo_unico')
        
        print(f"[CONTROLADOR] ✅ Orden creada exitosamente: ID={orden_id_val}, Código={codigo_val}")
        
        # ========== GENERAR NOTIFICACIONES ==========
        notificaciones_generadas = False
        try:
            print(f"[CONTROLADOR] 🔔 Intentando generar notificaciones para orden ID: {orden_id}")
            print(f"[CONTROLADOR] 🔔 Tipo de orden_id: {type(orden_id)}")
            
            # Llamar a la función de notificaciones
            resultado = notificar_nuevo_pedido(orden_id)
            
            if resultado:
                notificaciones_generadas = True
                print(f"[CONTROLADOR] ✅ Notificaciones generadas exitosamente")
            else:
                print(f"[CONTROLADOR] ⚠️ notificar_nuevo_pedido devolvió False")
                
        except Exception as notify_error:
            print(f"[CONTROLADOR] ❌ Error al generar notificaciones: {notify_error}")
            traceback.print_exc()
        
        orden_dict = Orden.to_dict(orden)
        
        print("[CONTROLADOR] ===== FIN CREACIÓN DE ORDEN =====")
        print("="*60)
        
        return jsonify({
            "msg": "Orden creada exitosamente",
            "orden": orden_dict,
            "notificaciones_generadas": notificaciones_generadas
        }), 201
        
    except Exception as error:
        print(f"[CONTROLADOR] ❌ Error al crear la orden: {error}")
        traceback.print_exc()
        print("[CONTROLADOR] ===== FIN CON ERROR =====")
        print("="*60)
        return jsonify({"msg": f"Error al crear la orden: {str(error)}"}), 500

def delete_orden(orden_id):
    """Eliminar orden permanentemente"""
    try:
        print(f"\n{'='*50}")
        print(f"[ELIMINAR ORDEN] Procesando eliminación permanente para orden ID: {orden_id}")
        
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        
        if not existing_orden:
            print(f"[ELIMINAR ORDEN] Orden {orden_id} NO encontrada")
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        # Obtener información de la orden
        if hasattr(existing_orden, 'id'):
            orden_info = {
                'id': existing_orden.id,
                'codigo': existing_orden.codigo_unico,
                'cliente': existing_orden.nombre_usuario,
                'estado': existing_orden.estado,
                'suplemento_id': existing_orden.suplemento_id,
                'cantidad': existing_orden.cantidad
            }
        else:
            orden_info = {
                'id': existing_orden.get('_id'),
                'codigo': existing_orden.get('codigo_unico'),
                'cliente': existing_orden.get('nombre_usuario'),
                'estado': existing_orden.get('estado'),
                'suplemento_id': existing_orden.get('suplemento_id'),
                'cantidad': existing_orden.get('cantidad', 1)
            }
        
        print(f"[ELIMINAR ORDEN] Datos de la orden a eliminar:")
        print(f"  - ID: {orden_info['id']}")
        print(f"  - Código único: {orden_info['codigo']}")
        print(f"  - Cliente: {orden_info['cliente']}")
        print(f"  - Estado actual: {orden_info['estado']}")
        
        # Solo permitir eliminar si está en estados que lo permitan
        if orden_info['estado'] not in ['pendiente', 'cancelada']:
            print(f"[ELIMINAR ORDEN] No se puede eliminar una orden en estado '{orden_info['estado']}'")
            return jsonify({
                "msg": f"No se puede eliminar una orden en estado '{orden_info['estado']}'. Solo se pueden eliminar órdenes pendientes o canceladas."
            }), 400
        
        # Restaurar stock si es necesario
        try:
            if orden_info['suplemento_id'] and orden_info['cantidad']:
                suplemento = Suplemento.find_by_id(orden_info['suplemento_id'])
                if suplemento:
                    if hasattr(suplemento, 'stock'):
                        nuevo_stock = suplemento.stock + orden_info['cantidad']
                        Suplemento.update_suplemento(orden_info['suplemento_id'], {'stock': nuevo_stock})
                        print(f"[ELIMINAR ORDEN] Stock restaurado: +{orden_info['cantidad']}")
        except Exception as stock_error:
            print(f"[ELIMINAR ORDEN] Error al restaurar stock: {stock_error}")
        
        # 1. ELIMINAR NOTIFICACIONES RELACIONADAS
        notificaciones_eliminadas = 0
        try:
            from Models.Notificaciones import Notificacion
            from config import DB_TYPE
            
            if DB_TYPE == 'mysql':
                notificaciones = Notificacion.query.filter_by(orden_id=orden_id).all()
                for notificacion in notificaciones:
                    db.session.delete(notificacion)
                    notificaciones_eliminadas += 1
                db.session.commit()
            else:
                # Para MongoDB
                notificaciones_collection = db_mongo.db.notificaciones
                result = notificaciones_collection.delete_many({'orden_id': str(orden_id)})
                notificaciones_eliminadas = result.deleted_count
            
            print(f"[ELIMINAR ORDEN] Notificaciones eliminadas: {notificaciones_eliminadas}")
            
        except Exception as notif_error:
            print(f"[ELIMINAR ORDEN] Error al eliminar notificaciones: {notif_error}")
        
        # 2. ELIMINAR LA ORDEN
        result = Orden.delete_orden(orden_id)
        
        if result:
            print(f"[ELIMINAR ORDEN] Orden {orden_id} ELIMINADA PERMANENTEMENTE")
            print(f"[ELIMINAR ORDEN] Notificaciones eliminadas: {notificaciones_eliminadas}")
            
            return jsonify({
                "msg": "Orden eliminada permanentemente",
                "detalle": f"Se eliminó la orden y {notificaciones_eliminadas} notificación(es) asociada(s)",
                "notificaciones_eliminadas": notificaciones_eliminadas
            }), 200
        else:
            print(f"[ELIMINAR ORDEN] No se pudo eliminar la orden")
            return jsonify({"msg": "Error al eliminar la orden"}), 500
            
    except Exception as error:
        print(f"\n[ELIMINAR ORDEN] ERROR:")
        print(f"Tipo: {type(error).__name__}")
        print(f"Mensaje: {str(error)}")
        traceback.print_exc()
        
        return jsonify({
            "msg": "Error interno del servidor al eliminar la orden",
            "error": str(error)
        }), 500
    finally:
        print(f"{'='*50}\n")

def update_orden(orden_id, nombre_usuario=None, telefono_usuario=None, estado=None, 
                precio_unitario=None, precio_total=None, cantidad=None,
                tipo_pedido=None, suplemento_id=None, metodo_pago=None, 
                notas=None, direccion_texto=None, direccion_id=None):
    """
    Actualizar una orden por ID
    """
    try:
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        if not existing_orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        update_data = {}
        
        # Campos básicos
        if nombre_usuario is not None:
            update_data['nombre_usuario'] = nombre_usuario
        if telefono_usuario is not None:
            update_data['telefono_usuario'] = telefono_usuario
        if estado is not None:
            if estado not in Orden.ESTADOS:
                return jsonify({"msg": f"Estado inválido. Use: {', '.join(Orden.ESTADOS.keys())}"}), 400
            update_data['estado'] = estado
        if tipo_pedido is not None:
            if tipo_pedido not in ['suplemento', 'carrito']:
                return jsonify({"msg": "Tipo de pedido inválido"}), 400
            update_data['tipo_pedido'] = tipo_pedido
        if metodo_pago is not None:
            if metodo_pago not in ['efectivo', 'tarjeta', 'transferencia']:
                return jsonify({"msg": "Método de pago inválido"}), 400
            update_data['metodo_pago'] = metodo_pago
        
        # Campos de cantidad y precio
        if cantidad is not None:
            if cantidad < 1:
                return jsonify({"msg": "La cantidad debe ser al menos 1"}), 400
            update_data['cantidad'] = cantidad
        
        if precio_unitario is not None:
            if precio_unitario < 0:
                return jsonify({"msg": "El precio unitario no puede ser negativo"}), 400
            update_data['precio_unitario'] = precio_unitario
        
        # Si se actualizó cantidad o precio unitario, recalcular total
        if 'cantidad' in update_data or 'precio_unitario' in update_data:
            nueva_cantidad = update_data.get('cantidad', 
                                           existing_orden.cantidad if hasattr(existing_orden, 'cantidad') else 
                                           existing_orden.get('cantidad', 1))
            nuevo_precio_unitario = update_data.get('precio_unitario',
                                                  existing_orden.precio_unitario if hasattr(existing_orden, 'precio_unitario') else
                                                  existing_orden.get('precio_unitario', 0))
            update_data['precio_total'] = nueva_cantidad * nuevo_precio_unitario
        elif precio_total is not None:
            # Si viene precio_total directamente
            if precio_total < 0:
                return jsonify({"msg": "El precio total no puede ser negativo"}), 400
            update_data['precio_total'] = precio_total
        
        # Suplemento
        if suplemento_id is not None:
            if suplemento_id == "":
                update_data['suplemento_id'] = None
            else:
                suplemento = Suplemento.find_by_id(suplemento_id)
                if not suplemento:
                    return jsonify({"msg": "Suplemento no encontrado"}), 404
                
                # Verificar stock si está disponible
                item_cantidad = update_data.get('cantidad', existing_orden.cantidad if hasattr(existing_orden, 'cantidad') else existing_orden.get('cantidad', 1))
                if hasattr(suplemento, 'stock') and suplemento.stock < item_cantidad:
                    return jsonify({"msg": f"Stock insuficiente. Disponible: {suplemento.stock}"}), 400
                elif isinstance(suplemento, dict) and suplemento.get('stock', 0) < item_cantidad:
                    return jsonify({"msg": f"Stock insuficiente. Disponible: {suplemento.get('stock', 0)}"}), 400
                
                update_data['suplemento_id'] = suplemento_id
                
                # Actualizar precio unitario con el precio del suplemento
                if hasattr(suplemento, 'precio'):
                    update_data['precio_unitario'] = float(suplemento.precio)
                else:
                    update_data['precio_unitario'] = float(suplemento.get('precio', 0))
                
                # Recalcular total
                nueva_cantidad = update_data.get('cantidad', existing_orden.cantidad if hasattr(existing_orden, 'cantidad') else existing_orden.get('cantidad', 1))
                update_data['precio_total'] = nueva_cantidad * update_data['precio_unitario']
        
        # Otros campos
        if notas is not None:
            update_data['notas'] = notas
        if direccion_texto is not None:
            update_data['direccion_texto'] = direccion_texto
        if direccion_id is not None:
            update_data['direccion_id'] = direccion_id
        
        if update_data:
            if Orden.update_orden(orden_id, update_data):
                # Obtener la orden actualizada
                updated_orden = Orden.find_by_id(orden_id)
                orden_dict = Orden.to_dict(updated_orden)
                
                # Asegurar precio
                if 'precio_total' not in orden_dict or orden_dict['precio_total'] is None:
                    orden_dict['precio_total'] = orden_dict.get('precio_unitario', 0) * orden_dict.get('cantidad', 1)
                orden_dict['precio'] = orden_dict['precio_total']
                
                # Si cambió el estado, notificar
                if 'estado' in update_data:
                    try:
                        notificar_cambio_estado_pedido(orden_id, update_data['estado'])
                    except:
                        pass
                
                return jsonify({
                    "msg": "Orden actualizada exitosamente",
                    "orden": orden_dict
                }), 200
            else:
                return jsonify({"msg": "No se realizaron cambios en la orden"}), 200
        else:
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
            
    except Exception as error:
        print(f"Error al actualizar la orden: {error}")
        traceback.print_exc()
        return jsonify({
            "msg": "Error al actualizar la orden",
            "error": str(error)
        }), 500

def cambiar_estado_orden(orden_id, nuevo_estado):
    """
    Cambiar estado de una orden
    """
    try:
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        if not existing_orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        # Validar estado
        if nuevo_estado not in Orden.ESTADOS:
            return jsonify({"msg": f"Estado inválido. Use: {', '.join(Orden.ESTADOS.keys())}"}), 400
        
        result = Orden.cambiar_estado(orden_id, nuevo_estado)
        if result:
            # Notificar cambio de estado
            try:
                notificar_cambio_estado_pedido(orden_id, nuevo_estado)
            except:
                pass
            
            updated_orden = Orden.find_by_id(orden_id)
            orden_dict = Orden.to_dict(updated_orden)
            
            return jsonify({
                "msg": f"Orden {nuevo_estado} exitosamente",
                "orden": orden_dict
            }), 200
        else:
            return jsonify({"msg": "Error al cambiar el estado de la orden"}), 500
            
    except Exception as error:
        print(f"Error al cambiar estado de la orden: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al cambiar el estado de la orden"}), 500

def search_ordenes(query):
    """Buscar órdenes por nombre, teléfono o código"""
    try:
        ordenes = Orden.search_ordenes(query)
        ordenes_dict = [Orden.to_dict(orden) for orden in ordenes]
        return jsonify(ordenes_dict), 200
        
    except Exception as error:
        print(f"Error al buscar órdenes: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al buscar órdenes"}), 500

def get_ordenes_by_estado(estado):
    """
    Obtener órdenes por estado
    """
    try:
        if estado not in Orden.ESTADOS:
            return jsonify({"msg": f"Estado inválido. Use: {', '.join(Orden.ESTADOS.keys())}"}), 400
            
        ordenes = Orden.get_ordenes_by_estado(estado)
        ordenes_dict = [Orden.to_dict(orden) for orden in ordenes]
        return jsonify(ordenes_dict), 200
    except Exception as error:
        print(f"Error al obtener órdenes por estado: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener órdenes"}), 500

def get_ordenes_by_usuario(telefono):
    """
    Obtener órdenes por teléfono de usuario
    """
    try:
        ordenes = Orden.get_ordenes_by_usuario(telefono)
        ordenes_dict = [Orden.to_dict(orden) for orden in ordenes]
        return jsonify(ordenes_dict), 200
    except Exception as error:
        print(f"Error al obtener órdenes por usuario: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener órdenes"}), 500

def get_estadisticas_ordenes():
    """
    Obtener estadísticas de órdenes
    """
    try:
        stats = Orden.get_estadisticas()
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    except Exception as error:
        print(f"Error al obtener estadísticas: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener estadísticas"}), 500

def get_suplementos_activos():
    """
    Obtener suplementos activos para el formulario - CORREGIDO (sin ingredientes)
    """
    try:
        suplementos = Suplemento.get_active_suplementos()
        suplementos_dict = []
        
        for suplemento in suplementos:
            if hasattr(suplemento, 'to_dict'):  # Es objeto SQL
                suplementos_dict.append(suplemento.to_dict())
            elif isinstance(suplemento, dict):  # Es diccionario MongoDB
                # Asegurar formato consistente SIN ingredientes
                suplemento_dict = {
                    'id': str(suplemento.get('_id')),
                    'nombre': suplemento.get('nombre'),
                    'descripcion': suplemento.get('descripcion'),
                    'precio': float(suplemento.get('precio', 0)),
                    'stock': suplemento.get('stock', 0),
                    'presentacion': suplemento.get('presentacion'),
                    'presentacion_nombre': Suplemento.PRESENTACIONES.get(suplemento.get('presentacion'), suplemento.get('presentacion')),
                    'categoria': suplemento.get('categoria'),
                    'categoria_nombre': Suplemento.CATEGORIAS.get(suplemento.get('categoria'), suplemento.get('categoria')),
                    'activo': suplemento.get('activo', True)
                }
                suplementos_dict.append(suplemento_dict)
            else:
                # Usar método to_dict de la clase
                suplementos_dict.append(Suplemento.to_dict(suplemento))
        
        print(f"Enviando {len(suplementos_dict)} suplementos activos")
        return jsonify(suplementos_dict), 200
        
    except Exception as error:
        print(f"Error al obtener suplementos activos: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener los suplementos"}), 500
    
def get_users_by_role(role_id):
    """
    Obtener usuarios por rol
    """
    try:
        if not User.is_valid_role(role_id):
            return jsonify({"msg": "Rol inválido"}), 400
            
        users = User.get_users_by_role(role_id)
        users_dict = [User.to_dict(user) for user in users]
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios por rol: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener usuarios"}), 500