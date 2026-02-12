from Models.Ingredientes import Ingrediente
from flask import jsonify, request

def get_all_ingredientes():
    """
    Obtener todos los ingredientes
    """
    try:
        only_active = request.args.get('activos', 'true').lower() == 'true'
        categoria = request.args.get('categoria') 
        
        
        ingredientes = Ingrediente.get_all_ingredientes(
            only_active=only_active,
            categoria=categoria
        )
        
        ingredientes_dict = [Ingrediente.to_dict(ingrediente) for ingrediente in ingredientes]
        return jsonify(ingredientes_dict), 200
    except Exception as error:
        print(f"Error al obtener ingredientes: {error}")
        return jsonify({"msg": "Error al obtener los ingredientes"}), 500

def get_single_ingrediente(ingrediente_id):
    """
    Obtener un ingrediente por ID
    """
    try:
        ingrediente = Ingrediente.find_by_id(ingrediente_id)
        if not ingrediente:
            return jsonify({"msg": "Ingrediente no encontrado"}), 404
        
        ingrediente_dict = Ingrediente.to_dict(ingrediente)
        return jsonify(ingrediente_dict), 200
    except Exception as error:
        print(f"Error al obtener el ingrediente: {error}")
        return jsonify({"msg": "Error al obtener el ingrediente"}), 500

def create_ingrediente(nombre, categoria=None, activo=True):
    """
    Crear nuevo ingrediente - nombre, categoría y activo
    """
    try:
        # Validaciones básicas
        if not nombre:
            return jsonify({"msg": "El nombre del ingrediente es requerido"}), 400
        
        # Verificar si ya existe un ingrediente con el mismo nombre
        existing_ingrediente = Ingrediente.find_by_name(nombre)
        if existing_ingrediente:
            return jsonify({"msg": "Ya existe un ingrediente con ese nombre"}), 400
        
        # Crear nuevo ingrediente
        ingrediente_data = {
            'nombre': nombre.strip(),
            'categoria': categoria.strip() if categoria else None,
            'activo': activo
        }
        
        ingrediente_id = Ingrediente.create_ingrediente(ingrediente_data)
        ingrediente = Ingrediente.find_by_id(ingrediente_id)
        ingrediente_dict = Ingrediente.to_dict(ingrediente)
        
        return jsonify({
            "msg": "Ingrediente creado exitosamente",
            "ingrediente": ingrediente_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear el ingrediente: {error}")
        return jsonify({"msg": "Error al crear el ingrediente"}), 500

def delete_ingrediente(ingrediente_id):
    """Eliminar un ingrediente por ID"""
    try:
        existing_ingrediente = Ingrediente.find_by_id(ingrediente_id)
        if not existing_ingrediente:
            return jsonify({"msg": "Ingrediente no encontrado"}), 404
        
        result = Ingrediente.delete_ingrediente(ingrediente_id)
        
        if result:
            return jsonify({"msg": "Ingrediente eliminado exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar el ingrediente"}), 500
            
    except Exception as error:
        print(f"Error al eliminar ingrediente {ingrediente_id}: {str(error)}")
        return jsonify({"msg": "Error interno del servidor al eliminar ingrediente"}), 500

def update_ingrediente(ingrediente_id, nombre=None, categoria=None, activo=None):
    """
    Actualizar un ingrediente por ID - nombre, categoría y activo
    """
    try:
        existing_ingrediente = Ingrediente.find_by_id(ingrediente_id)
        if not existing_ingrediente:
            return jsonify({"msg": "Ingrediente no encontrado"}), 404
        
        update_data = {}
        
        if nombre is not None:
            nombre_ingrediente = Ingrediente.find_by_name(nombre)
            if nombre_ingrediente and nombre_ingrediente.id != ingrediente_id:
                return jsonify({"msg": "Ya existe un ingrediente con ese nombre"}), 400
            update_data['nombre'] = nombre
            
        if categoria is not None:
            update_data['categoria'] = categoria if categoria != "" else None
            
        if activo is not None:
            update_data['activo'] = activo
        
        if update_data:
            if Ingrediente.update_ingrediente(ingrediente_id, update_data):
                updated_ingrediente = Ingrediente.find_by_id(ingrediente_id)
                ingrediente_dict = Ingrediente.to_dict(updated_ingrediente)
                
                mensaje = "Ingrediente actualizado exitosamente"
                
                # Si se desactivó el ingrediente, añadir información
                if 'activo' in update_data and update_data['activo'] == False:
                    mensaje += ". Se han enviado notificaciones automáticamente."
                
                return jsonify({
                    "msg": mensaje,
                    "ingrediente": ingrediente_dict
                }), 200
            else:
                return jsonify({"msg": "No se realizaron cambios en el ingrediente"}), 200
        else:
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
            
    except Exception as error:
        print(f"Error al actualizar el ingrediente: {error}")
        return jsonify({
            "msg": "Error al actualizar el ingrediente",
            "error": str(error)
        }), 500

def toggle_ingrediente_activo(ingrediente_id):
    """
    Activar/desactivar un ingrediente
    """
    try:
        existing_ingrediente = Ingrediente.find_by_id(ingrediente_id)
        if not existing_ingrediente:
            return jsonify({"msg": "Ingrediente no encontrado"}), 404
        
        # Guardar estado anterior para mensaje informativo
        estado_anterior = existing_ingrediente.activo
        
        result = Ingrediente.toggle_activo(ingrediente_id)
        if result:
            updated_ingrediente = Ingrediente.find_by_id(ingrediente_id)
            ingrediente_dict = Ingrediente.to_dict(updated_ingrediente)
            
            estado = "activado" if updated_ingrediente.activo else "desactivado"
            
            # Mensaje adicional si se desactivó
            mensaje = f"Ingrediente {estado} exitosamente"
            if estado_anterior == True and updated_ingrediente.activo == False:
                mensaje += ". Se han enviado notificaciones automáticamente."
            
            return jsonify({
                "msg": mensaje,
                "ingrediente": ingrediente_dict
            }), 200
        else:
            return jsonify({"msg": "Error al cambiar el estado del ingrediente"}), 500
            
    except Exception as error:
        print(f"Error al cambiar estado del ingrediente: {error}")
        return jsonify({"msg": "Error al cambiar el estado del ingrediente"}), 500

def search_ingredientes(query):
    """Buscar ingredientes por nombre o categoría"""
    try:
        ingredientes = Ingrediente.search_ingredientes(query)
        ingredientes_dict = [Ingrediente.to_dict(ingrediente) for ingrediente in ingredientes]
        return jsonify(ingredientes_dict), 200
        
    except Exception as error:
        print(f"Error al buscar ingredientes: {error}")
        return jsonify({"msg": "Error al buscar ingredientes"}), 500

def get_ingredientes_activos():
    """
    Obtener solo ingredientes activos
    """
    try:
        ingredientes = Ingrediente.get_ingredientes_activos()
        ingredientes_dict = [Ingrediente.to_dict(ingrediente) for ingrediente in ingredientes]
        return jsonify(ingredientes_dict), 200
    except Exception as error:
        print(f"Error al obtener ingredientes activos: {error}")
        return jsonify({"msg": "Error al obtener los ingredientes activos"}), 500

def get_ingredientes_by_categoria(categoria):
    """
    Obtener ingredientes por categoría
    """
    try:
        ingredientes = Ingrediente.get_by_categoria(categoria, only_active=True)
        ingredientes_dict = [Ingrediente.to_dict(ingrediente) for ingrediente in ingredientes]
        return jsonify(ingredientes_dict), 200
    except Exception as error:
        print(f"Error al obtener ingredientes por categoría: {error}")
        return jsonify({"msg": "Error al obtener los ingredientes"}), 500

def get_categorias():
    """
    Obtener lista de categorías
    """
    try:
        categorias = Ingrediente.get_categorias()
        return jsonify({"categorias": categorias}), 200
    except Exception as error:
        print(f"Error al obtener categorías: {error}")
        return jsonify({"msg": "Error al obtener las categorías"}), 500

def bulk_create_ingredientes():
    """Crear múltiples ingredientes a la vez"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"msg": "Se requiere una lista de ingredientes"}), 400
        
        ingredientes_creados = Ingrediente.bulk_crear_ingredientes(data)
        
        return jsonify({
            "msg": f"Se crearon {len(ingredientes_creados)} ingredientes exitosamente",
            "creados": ingredientes_creados,
            "total_solicitados": len(data)
        }), 201
        
    except Exception as error:
        print(f"Error al crear ingredientes en lote: {error}")
        return jsonify({"msg": "Error al crear ingredientes en lote"}), 500