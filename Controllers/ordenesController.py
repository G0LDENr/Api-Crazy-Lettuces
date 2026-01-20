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
    """Eliminar una orden por ID"""
    try:
        # Verificar si la orden existe
        existing_orden = Orden.find_by_id(orden_id)
        if not existing_orden:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        # Eliminar la orden
        result = Orden.delete_orden(orden_id)
        
        if result:
            return jsonify({"msg": "Orden eliminada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar la orden"}), 500
            
    except Exception as error:
        print(f"Error al eliminar orden {orden_id}: {str(error)}")
        return jsonify({"msg": "Error interno del servidor al eliminar orden"}), 500

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