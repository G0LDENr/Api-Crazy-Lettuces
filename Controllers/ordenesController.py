from Models.Ordenes import Orden
from Models.Especiales import Especial
from Models.User import User
from flask import jsonify, request
from Controllers.notificacionesController import notificar_nuevo_pedido, notificar_cambio_estado_pedido

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

def create_orden(nombre_usuario, telefono_usuario, tipo_pedido, especial_id=None, ingredientes_personalizados=None):
    """
    Crear nueva orden
    """
    try:
        # Validaciones básicas
        if not nombre_usuario or not telefono_usuario or not tipo_pedido:
            return jsonify({"msg": "Nombre, teléfono y tipo de pedido son requeridos"}), 400
        
        if tipo_pedido not in ['especial', 'personalizado']:
            return jsonify({"msg": "Tipo de pedido inválido"}), 400
        
        precio = 0.0
        
        if tipo_pedido == 'especial':
            if not especial_id:
                return jsonify({"msg": "Debe seleccionar un especial"}), 400
            
            # Verificar que el especial existe y está activo
            especial = Especial.find_by_id(especial_id)
            if not especial:
                return jsonify({"msg": "Especial no encontrado"}), 404
            
            if not especial.activo:
                return jsonify({"msg": "El especial seleccionado no está disponible"}), 400
            
            precio = float(especial.precio) if especial.precio else 0.0
            
        elif tipo_pedido == 'personalizado':
            if not ingredientes_personalizados:
                return jsonify({"msg": "Debe ingresar los ingredientes personalizados"}), 400
            
            # Calcular precio basado en número de ingredientes
            ingredientes_lista = [ing.strip() for ing in ingredientes_personalizados.split(',') if ing.strip()]
            num_ingredientes = len(ingredientes_lista)
            
            if num_ingredientes == 0:
                return jsonify({"msg": "Debe ingresar al menos un ingrediente"}), 400
            
            precio = Orden.calcular_precio_personalizado(num_ingredientes)
        
        # Crear nueva orden
        orden_data = {
            'nombre_usuario': nombre_usuario.strip(),
            'telefono_usuario': telefono_usuario.strip(),
            'tipo_pedido': tipo_pedido,
            'especial_id': especial_id,
            'ingredientes_personalizados': ingredientes_personalizados.strip() if ingredientes_personalizados else None,
            'precio': precio,
            'estado': 'pendiente'
        }
        
        orden_id = Orden.create_orden(orden_data)
        orden = Orden.find_by_id(orden_id)
        notificar_nuevo_pedido(orden_id)
        orden_dict = Orden.to_dict(orden)
        
        return jsonify({
            "msg": "Orden creada exitosamente",
            "orden": orden_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear la orden: {error}")
        return jsonify({"msg": "Error al crear la orden"}), 500

def delete_orden(orden_id):
    """Eliminar orden - solo permitido si está en estado 'entregado'"""
    try:
        print(f"\n{'='*50}")
        print(f"[ELIMINAR ORDEN] Procesando orden ID: {orden_id}")
        
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        
        if not existing_orden:
            print(f"[ELIMINAR ORDEN] Orden {orden_id} NO encontrada")
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        print(f"[ELIMINAR ORDEN] Datos de la orden:")
        print(f"  - ID: {existing_orden.id}")
        print(f"  - Código único: {existing_orden.codigo_unico}")
        print(f"  - Cliente: {existing_orden.nombre_usuario}")
        print(f"  - Estado actual: {existing_orden.estado}")
        print(f"  - Fecha creación: {existing_orden.fecha_creacion}")
        
        # REGLA: Solo se puede eliminar si está en estado 'entregado'
        if existing_orden.estado != 'entregado':
            print(f"[ELIMINAR ORDEN] Orden NO está entregada (estado: {existing_orden.estado})")
            
            # Opciones según el estado
            if existing_orden.estado == 'pendiente':
                sugerencia = "Primero debe marcar la orden como 'Entregado' antes de poder eliminarla"
                accion_recomendada = "marcar_entregado"
            elif existing_orden.estado == 'preparando':
                sugerencia = "La orden está en preparación. Complete el proceso marcándola como 'Entregado' primero"
                accion_recomendada = "continuar_proceso"
            elif existing_orden.estado == 'listo':
                sugerencia = "La orden está lista para entregar. Márquela como 'Entregado' primero"
                accion_recomendada = "marcar_entregado"
            elif existing_orden.estado == 'cancelado':
                sugerencia = "Las órdenes canceladas no pueden ser eliminadas"
                accion_recomendada = "no_permitido"
            else:
                sugerencia = f"Las órdenes en estado '{existing_orden.estado}' no pueden ser eliminadas"
                accion_recomendada = "no_permitido"
            
            return jsonify({
                "msg": f"No se puede eliminar una orden en estado '{existing_orden.estado}'",
                "detalle": sugerencia,
                "estado_actual": existing_orden.estado,
                "accion_recomendada": accion_recomendada,
                "tipo": "estado_no_permitido"
            }), 400
        
        # Verificar si han pasado al menos 24 horas desde la entrega
        from datetime import datetime, timedelta
        fecha_actualizacion = existing_orden.fecha_actualizacion or existing_orden.fecha_creacion
        
        if fecha_actualizacion:
            tiempo_transcurrido = datetime.utcnow() - fecha_actualizacion
            horas_transcurridas = tiempo_transcurrido.total_seconds() / 3600
            
            print(f"[ELIMINAR ORDEN] Horas desde actualización: {horas_transcurridas:.1f}")
            
            if horas_transcurridas < 1:  # Menos de 1 hora
                return jsonify({
                    "msg": "No se puede eliminar una orden recién entregada",
                    "detalle": "Espere al menos 1 hora después de la entrega para poder eliminar la orden",
                    "horas_transcurridas": round(horas_transcurridas, 1),
                    "tipo": "tiempo_insuficiente"
                }), 400
        
        print(f"[ELIMINAR ORDEN] Orden está entregada, intentando eliminación...")
        
        # Primero intentar eliminar notificaciones relacionadas
        notificaciones_eliminadas = 0
        try:
            from Models.Notificaciones import Notificacion
            notificaciones_eliminadas = Notificacion.delete_by_orden_id(orden_id)
            print(f"[ELIMINAR ORDEN] Notificaciones eliminadas: {notificaciones_eliminadas}")
        except Exception as notif_error:
            print(f"[ELIMINAR ORDEN] Error al eliminar notificaciones: {notif_error}")
            # Continuar de todos modos
        
        # Intentar eliminar físicamente la orden
        result = Orden.delete_orden(orden_id)
        
        if result:
            print(f"[ELIMINAR ORDEN] ✅ Orden {orden_id} eliminada exitosamente")
            print(f"[ELIMINAR ORDEN] Notificaciones eliminadas: {notificaciones_eliminadas}")
            
            return jsonify({
                "msg": "✅ Orden eliminada exitosamente",
                "detalle": f"Se eliminó la orden y {notificaciones_eliminadas} notificación(es) asociada(s)",
                "notificaciones_eliminadas": notificaciones_eliminadas,
                "tipo": "eliminacion_exitosa"
            }), 200
        else:
            print(f"[ELIMINAR ORDEN] ❌ Error al eliminar orden físicamente")
            
            # Intentar como última opción: marcar como "eliminada" en lugar de borrar
            try:
                from datetime import datetime
                # Agregar sufijo al nombre para indicar que está "eliminada"
                nuevo_nombre = f"{existing_orden.nombre_usuario} [ELIMINADO]"
                Orden.update_orden(orden_id, {
                    'nombre_usuario': nuevo_nombre,
                    'estado': 'cancelado',
                    'telefono_usuario': '0000000000'  # Anonimizar
                })
                
                return jsonify({
                    "msg": "⚠️ No se pudo eliminar físicamente la orden",
                    "detalle": "Se marcó la orden como 'Eliminada' en el sistema",
                    "tipo": "marcada_como_eliminada",
                    "estado": "cancelado"
                }), 200
                
            except Exception as fallback_error:
                print(f"[ELIMINAR ORDEN] Error en fallback: {fallback_error}")
                
                return jsonify({
                    "msg": "❌ Error crítico al eliminar la orden",
                    "detalle": "No se pudo eliminar ni modificar la orden",
                    "tipo": "error_critico"
                }), 500
            
    except Exception as error:
        print(f"\n[ELIMINAR ORDEN] ⚠️ ERROR EXCEPCIÓN:")
        print(f"Tipo: {type(error).__name__}")
        print(f"Mensaje: {str(error)}")
        
        # Detectar error de clave foránea
        error_str = str(error)
        if "foreign key constraint" in error_str.lower():
            return jsonify({
                "msg": "⚠️ No se puede eliminar esta orden porque tiene notificaciones activas",
                "detalle": "Las notificaciones asociadas deben ser procesadas primero",
                "tipo": "notificaciones_activas"
            }), 400
        
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "msg": "❌ Error interno del servidor",
            "error": str(error),
            "tipo": "error_interno"
        }), 500
    finally:
        print(f"{'='*50}\n")

def update_orden(orden_id, nombre_usuario=None, telefono_usuario=None, estado=None, 
                precio=None, tipo_pedido=None, especial_id=None, ingredientes_personalizados=None):
    """
    Actualizar una orden por ID
    """
    try:
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        if not existing_orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        update_data = {}
        
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
            if tipo_pedido not in ['especial', 'personalizado']:
                return jsonify({"msg": "Tipo de pedido inválido"}), 400
            update_data['tipo_pedido'] = tipo_pedido
        if especial_id is not None:
            # Si especial_id es una cadena vacía, establecerlo como None
            if especial_id == "":
                update_data['especial_id'] = None
            else:
                # Verificar que el especial existe
                especial = Especial.find_by_id(especial_id)
                if not especial:
                    return jsonify({"msg": "Especial no encontrado"}), 404
                update_data['especial_id'] = especial_id
        if ingredientes_personalizados is not None:
            # Si ingredientes_personalizados es una cadena vacía, establecerlo como None
            if ingredientes_personalizados == "":
                update_data['ingredientes_personalizados'] = None
            else:
                update_data['ingredientes_personalizados'] = ingredientes_personalizados
        
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