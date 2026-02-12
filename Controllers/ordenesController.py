from Models.Ordenes import Orden
from Models.Especiales import Especial
from Models.User import User
from flask import jsonify, request
from Controllers.notificacionesController import notificar_nuevo_pedido, notificar_cambio_estado_pedido
from config import db
import json

def get_all_ordenes():
    """
    Obtener todas las órdenes
    """
    try:
        ordenes = Orden.get_all_ordenes()
        ordenes_dict = [Orden.to_dict(orden) for orden in ordenes]
        return jsonify(ordenes_dict), 200
    except Exception as error:
        print(f"Error al obtener órdenes: {error}")
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
        return jsonify(orden_dict), 200
    except Exception as error:
        print(f"Error al obtener la orden: {error}")
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
        return jsonify(orden_dict), 200
    except Exception as error:
        print(f"Error al buscar orden por código: {error}")
        return jsonify({"msg": "Error al buscar la orden"}), 500

def create_orden_completa():
    """
    Crear nueva orden - VERSIÓN PARA CARRITO Y PEDIDOS NORMALES
    """
    try:
        data = request.get_json()
        
        print(f"📦 [CONTROLADOR] Datos recibidos para crear orden:")
        print(f"   - Tipo: {data.get('tipo_pedido')}")
        print(f"   - Nombre: {data.get('nombre_usuario')}")
        print(f"   - Método pago: {data.get('metodo_pago', 'efectivo')}")
        
        # Validaciones básicas
        required_fields = ['nombre_usuario', 'telefono_usuario', 'tipo_pedido']
        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"Campo requerido: {field}"}), 400
        
        # Validar tipo de pedido (ahora incluye 'carrito')
        tipos_validos = ['especial', 'personalizado', 'carrito']
        if data['tipo_pedido'] not in tipos_validos:
            return jsonify({"msg": f"Tipo de pedido inválido. Use: {', '.join(tipos_validos)}"}), 400
        
        precio = 0.0
        cantidad = data.get('cantidad', 1)
        
        if data['tipo_pedido'] == 'especial':
            # Validación para especial
            especial_id = data.get('especial_id')
            if not especial_id:
                return jsonify({"msg": "Debe seleccionar un especial"}), 400
            
            especial = Especial.find_by_id(especial_id)
            if not especial:
                return jsonify({"msg": "Especial no encontrado"}), 404
            
            if not especial.activo:
                return jsonify({"msg": "El especial seleccionado no está disponible"}), 400
            
            precio_base = float(especial.precio) if especial.precio else 0.0
            precio = precio_base * cantidad
            
        elif data['tipo_pedido'] == 'personalizado':
            # Validación para personalizado
            ingredientes_personalizados = data.get('ingredientes_personalizados')
            if not ingredientes_personalizados:
                return jsonify({"msg": "Debe ingresar los ingredientes personalizados"}), 400
            
            ingredientes_lista = [ing.strip() for ing in ingredientes_personalizados.split(',') if ing.strip()]
            num_ingredientes = len(ingredientes_lista)
            
            if num_ingredientes == 0:
                return jsonify({"msg": "Debe ingresar al menos un ingrediente"}), 400
            
            precio_base = Orden.calcular_precio_personalizado(num_ingredientes)
            precio = precio_base * cantidad
            
        elif data['tipo_pedido'] == 'carrito':
            # Validación simplificada para carrito
            # Solo verificar que viene el precio total
            if 'precio' not in data or data['precio'] <= 0:
                return jsonify({"msg": "Precio total del carrito inválido"}), 400
            precio = data['precio']
            
            # Verificar que viene información del carrito
            if 'pedido_json' not in data:
                return jsonify({"msg": "Falta información del carrito (pedido_json)"}), 400
        
        # Si viene precio en los datos, usar ese (para carrito ya viene el total)
        if 'precio' in data and data['precio']:
            try:
                precio = float(data['precio'])
            except:
                pass  # Mantener el precio calculado
        
        # ✅ Preparar datos para crear la orden CON NUEVOS CAMPOS
        orden_data = {
            'nombre_usuario': data['nombre_usuario'].strip(),
            'telefono_usuario': data['telefono_usuario'].strip(),
            'tipo_pedido': data['tipo_pedido'],
            'especial_id': data.get('especial_id'),
            'direccion_texto': data.get('direccion_texto'),
            'direccion_id': data.get('direccion_id'),
            'pedido_json': data.get('pedido_json'),
            'ingredientes_personalizados': data.get('ingredientes_personalizados'),
            'precio': precio,
            'estado': 'pendiente',
            
            # ===== NUEVOS CAMPOS DEL CARRITO =====
            'metodo_pago': data.get('metodo_pago', 'efectivo'),
            'notas': data.get('notas'),
            'info_pago': data.get('info_pago')  # Solo info básica para tarjeta
        }
        
        print(f"📊 [CONTROLADOR] Creando orden tipo: {data['tipo_pedido']}")
        print(f"   Método pago: {orden_data.get('metodo_pago')}")
        print(f"   Precio: {precio}")
        
        # Crear nueva orden
        orden_id = Orden.create_orden(orden_data)
        orden = Orden.find_by_id(orden_id)
        
        if not orden:
            return jsonify({"msg": "Error al obtener la orden creada"}), 500
        
        print(f"✅ [CONTROLADOR] Orden creada: ID={orden.id}, Código={orden.codigo_unico}")
        
        # ✅ Generar notificaciones automáticamente
        notificaciones_generadas = False
        try:
            notificar_nuevo_pedido(orden_id)
            notificaciones_generadas = True
            print(f"✅ [CONTROLADOR] Notificaciones generadas para orden {orden_id}")
        except Exception as notify_error:
            print(f"⚠️ [CONTROLADOR] Error al generar notificaciones: {notify_error}")
            import traceback
            traceback.print_exc()
            # No fallar la creación por error en notificaciones
        
        orden_dict = Orden.to_dict(orden)
        
        return jsonify({
            "msg": "Orden creada exitosamente",
            "orden": orden_dict,
            "notificaciones_generadas": notificaciones_generadas
        }), 201
        
    except Exception as error:
        print(f"❌ [CONTROLADOR] Error al crear la orden: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error al crear la orden: {str(error)}"}), 500

def delete_orden(orden_id):
    """Eliminar orden permanentemente - sin validación de tiempo de espera"""
    try:
        print(f"\n{'='*50}")
        print(f"[ELIMINAR ORDEN] Procesando eliminación permanente para orden ID: {orden_id}")
        
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        
        if not existing_orden:
            print(f"[ELIMINAR ORDEN] Orden {orden_id} NO encontrada")
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        print(f"[ELIMINAR ORDEN] Datos de la orden a eliminar:")
        print(f"  - ID: {existing_orden.id}")
        print(f"  - Código único: {existing_orden.codigo_unico}")
        print(f"  - Cliente: {existing_orden.nombre_usuario}")
        print(f"  - Estado actual: {existing_orden.estado}")
        print(f"  - Fecha creación: {existing_orden.fecha_creacion}")
        print(f"  - Dirección: {existing_orden.direccion_texto[:50] if existing_orden.direccion_texto else 'No especificada'}")
        
        # **MODIFICACIÓN: PERMITIR ELIMINACIÓN SIN IMPORTAR EL ESTADO**
        # Solo informar el estado, pero permitir eliminar
        if existing_orden.estado != 'entregado':
            print(f"[ELIMINAR ORDEN] ADVERTENCIA: Orden NO está en estado 'entregado' (estado: {existing_orden.estado})")
            print(f"[ELIMINAR ORDEN] Procediendo con eliminación permanente de todos modos...")
        
        # 1. ELIMINAR NOTIFICACIONES RELACIONADAS PRIMERO
        notificaciones_eliminadas = 0
        try:
            from Models.Notificaciones import Notificacion
            # Método para eliminar todas las notificaciones de una orden
            notificaciones = Notificacion.query.filter_by(orden_id=orden_id).all()
            for notificacion in notificaciones:
                db.session.delete(notificacion)
                notificaciones_eliminadas += 1
            
            db.session.commit()
            print(f"[ELIMINAR ORDEN] Notificaciones eliminadas: {notificaciones_eliminadas}")
            
        except Exception as notif_error:
            print(f"[ELIMINAR ORDEN] Error al eliminar notificaciones: {notif_error}")
            # Continuar intentando eliminar la orden de todos modos
        
        # 2. INTENTAR ELIMINAR LA ORDEN FÍSICAMENTE
        print(f"[ELIMINAR ORDEN] Intentando eliminar orden físicamente...")
        
        try:
            # Intentar eliminar directamente usando SQLAlchemy
            orden_a_eliminar = Orden.query.get(orden_id)
            if orden_a_eliminar:
                db.session.delete(orden_a_eliminar)
                db.session.commit()
                
                print(f"[ELIMINAR ORDEN] ✅ Orden {orden_id} ELIMINADA PERMANENTEMENTE")
                print(f"[ELIMINAR ORDEN] Notificaciones eliminadas: {notificaciones_eliminadas}")
                
                return jsonify({
                    "msg": "✅ Orden eliminada permanentemente",
                    "detalle": f"Se eliminó la orden y {notificaciones_eliminadas} notificación(es) asociada(s)",
                    "notificaciones_eliminadas": notificaciones_eliminadas,
                    "eliminacion_fisica": True,
                    "tipo": "eliminacion_exitosa"
                }), 200
            else:
                print(f"[ELIMINAR ORDEN] ❌ No se pudo encontrar la orden para eliminar")
                return jsonify({
                    "msg": "Error al encontrar la orden para eliminar",
                    "tipo": "error_encontrar"
                }), 500
                
        except Exception as delete_error:
            print(f"[ELIMINAR ORDEN] ❌ Error al eliminar orden físicamente: {delete_error}")
            
            # Si hay error de clave foránea, intentar eliminar manualmente
            error_str = str(delete_error)
            if "foreign key constraint" in error_str.lower():
                print(f"[ELIMINAR ORDEN] Intentando eliminar con eliminación en cascada...")
                
                try:
                    # Revertir cambios primero
                    db.session.rollback()
                    
                    # Intentar eliminar manualmente con SQL directo si es necesario
                    # (dependiendo de tu base de datos)
                    print(f"[ELIMINAR ORDEN] Revisar restricciones de clave foránea...")
                    
                except Exception as cascade_error:
                    print(f"[ELIMINAR ORDEN] Error en eliminación en cascada: {cascade_error}")
            
            # INTENTO FINAL: Usar el método del modelo si existe
            try:
                print(f"[ELIMINAR ORDEN] Intentando con método del modelo...")
                result = Orden.delete_orden(orden_id)
                
                if result:
                    print(f"[ELIMINAR ORDEN] ✅ Orden eliminada mediante método del modelo")
                    return jsonify({
                        "msg": "✅ Orden eliminada permanentemente",
                        "detalle": f"Se eliminó la orden y {notificaciones_eliminadas} notificación(es) asociada(s)",
                        "notificaciones_eliminadas": notificaciones_eliminadas,
                        "eliminacion_fisica": True,
                        "tipo": "eliminacion_exitosa"
                    }), 200
                else:
                    raise Exception("Método del modelo retornó False")
                    
            except Exception as model_error:
                print(f"[ELIMINAR ORDEN] Error en método del modelo: {model_error}")
                
                # ÚLTIMO RECURSO: Actualizar estado y marcar como eliminada
                print(f"[ELIMINAR ORDEN] ❌ No se pudo eliminar físicamente, marcando como eliminada...")
                try:
                    nuevo_nombre = f"{existing_orden.nombre_usuario} [ELIMINADO]"
                    Orden.update_orden(orden_id, {
                        'nombre_usuario': nuevo_nombre,
                        'estado': 'cancelado',
                        'telefono_usuario': '0000000000',
                        'especial_id': None,
                        'ingredientes_personalizados': '[ELIMINADO]',
                        'direccion_texto': '[ELIMINADA]' if existing_orden.direccion_texto else None
                    })
                    
                    print(f"[ELIMINAR ORDEN] ⚠️ Orden marcada como 'Eliminada' (no se pudo borrar físicamente)")
                    return jsonify({
                        "msg": "⚠️ No se pudo eliminar físicamente la orden",
                        "detalle": "Se marcó la orden como 'Eliminada' en el sistema",
                        "tipo": "marcada_como_eliminada",
                        "estado": "cancelado"
                    }), 200
                    
                except Exception as fallback_error:
                    print(f"[ELIMINAR ORDEN] Error crítico en fallback: {fallback_error}")
                    return jsonify({
                        "msg": "❌ Error crítico al eliminar la orden",
                        "detalle": "No se pudo eliminar ni modificar la orden",
                        "tipo": "error_critico"
                    }), 500
            
    except Exception as error:
        print(f"\n[ELIMINAR ORDEN] ⚠️ ERROR EXCEPCIÓN GENERAL:")
        print(f"Tipo: {type(error).__name__}")
        print(f"Mensaje: {str(error)}")
        
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "msg": "❌ Error interno del servidor al eliminar la orden",
            "error": str(error),
            "tipo": "error_interno"
        }), 500
    finally:
        print(f"{'='*50}\n")

def update_orden(orden_id, nombre_usuario=None, telefono_usuario=None, estado=None, 
                precio=None, tipo_pedido=None, especial_id=None, ingredientes_personalizados=None,
                metodo_pago=None, notas=None, direccion_texto=None, direccion_id=None):
    """
    Actualizar una orden por ID - VERSIÓN ACTUALIZADA
    """
    try:
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        if not existing_orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        update_data = {}
        
        # Campos originales
        if nombre_usuario is not None:
            update_data['nombre_usuario'] = nombre_usuario
        if telefono_usuario is not None:
            update_data['telefono_usuario'] = telefono_usuario
        if estado is not None:
            if estado not in ['pendiente', 'preparando', 'listo', 'entregado', 'cancelado']:
                return jsonify({"msg": "Estado inválido"}), 400
            update_data['estado'] = estado
        if precio is not None:
            if precio < 0:
                return jsonify({"msg": "El precio no puede ser negativo"}), 400
            update_data['precio'] = precio
        if tipo_pedido is not None:
            if tipo_pedido not in ['especial', 'personalizado', 'carrito']:
                return jsonify({"msg": "Tipo de pedido inválido"}), 400
            update_data['tipo_pedido'] = tipo_pedido
        if especial_id is not None:
            if especial_id == "":
                update_data['especial_id'] = None
            else:
                especial = Especial.find_by_id(especial_id)
                if not especial:
                    return jsonify({"msg": "Especial no encontrado"}), 404
                update_data['especial_id'] = especial_id
        if ingredientes_personalizados is not None:
            if ingredientes_personalizados == "":
                update_data['ingredientes_personalizados'] = None
            else:
                update_data['ingredientes_personalizados'] = ingredientes_personalizados
        
        # Nuevos campos
        if metodo_pago is not None:
            if metodo_pago not in ['efectivo', 'tarjeta']:
                return jsonify({"msg": "Método de pago inválido"}), 400
            update_data['metodo_pago'] = metodo_pago
        if notas is not None:
            update_data['notas'] = notas
        if direccion_texto is not None:
            update_data['direccion_texto'] = direccion_texto
        if direccion_id is not None:
            update_data['direccion_id'] = direccion_id
        
        # Recalcular precio si se cambió el tipo de pedido, especial o ingredientes
        if 'tipo_pedido' in update_data or 'especial_id' in update_data or 'ingredientes_personalizados' in update_data:
            if update_data.get('tipo_pedido') == 'especial' and update_data.get('especial_id'):
                especial = Especial.find_by_id(update_data['especial_id'])
                if especial:
                    update_data['precio'] = float(especial.precio) if especial.precio else 0.0
            elif update_data.get('tipo_pedido') == 'personalizado' and update_data.get('ingredientes_personalizados'):
                ingredientes_lista = [ing.strip() for ing in update_data['ingredientes_personalizados'].split(',') if ing.strip()]
                num_ingredientes = len(ingredientes_lista)
                update_data['precio'] = Orden.calcular_precio_personalizado(num_ingredientes)
        
        if update_data:
            if Orden.update_orden(orden_id, update_data):
                # Obtener la orden actualizada
                updated_orden = Orden.find_by_id(orden_id)
                orden_dict = Orden.to_dict(updated_orden)
                
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
        estados_validos = ['pendiente', 'preparando', 'listo', 'entregado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return jsonify({"msg": "Estado inválido"}), 400
        
        result = Orden.cambiar_estado(orden_id, nuevo_estado)
        if result:
            # Obtener la orden actualizada
            notificar_cambio_estado_pedido(orden_id, nuevo_estado)
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
        return jsonify({"msg": "Error al cambiar el estado de la orden"}), 500

def search_ordenes(query):
    """Buscar órdenes por nombre, teléfono o código"""
    try:
        ordenes = Orden.search_ordenes(query)
        ordenes_dict = [Orden.to_dict(orden) for orden in ordenes]
        return jsonify(ordenes_dict), 200
        
    except Exception as error:
        print(f"Error al buscar órdenes: {error}")
        return jsonify({"msg": "Error al buscar órdenes"}), 500

def get_ordenes_by_estado(estado):
    """
    Obtener órdenes por estado
    """
    try:
        estados_validos = ['pendiente', 'preparando', 'listo', 'entregado', 'cancelado']
        if estado not in estados_validos:
            return jsonify({"msg": "Estado inválido"}), 400
            
        ordenes = Orden.get_ordenes_by_estado(estado)
        ordenes_dict = [Orden.to_dict(orden) for orden in ordenes]
        return jsonify(ordenes_dict), 200
    except Exception as error:
        print(f"Error al obtener órdenes por estado: {error}")
        return jsonify({"msg": "Error al obtener órdenes"}), 500

def get_especiales_activos():
    """
    Obtener especiales activos para el formulario
    """
    try:
        especiales = Especial.get_active_especiales()
        especiales_dict = [Especial.to_dict(especial) for especial in especiales]
        return jsonify(especiales_dict), 200
    except Exception as error:
        print(f"Error al obtener especiales activos: {error}")
        return jsonify({"msg": "Error al obtener los especiales"}), 500
    
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
        return jsonify({"msg": "Error al obtener usuarios"}), 500