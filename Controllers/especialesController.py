from Models.Especiales import Especial
from flask import jsonify, request

def get_all_especiales():
    """
    Obtener todos los especiales
    """
    try:
        # Por defecto solo mostrar activos, pero permitir ver todos si se solicita
        only_active = request.args.get('all', 'false').lower() != 'true'
        especiales = Especial.get_all_especiales(only_active=only_active)
        especiales_dict = [Especial.to_dict(especial) for especial in especiales]
        return jsonify(especiales_dict), 200
    except Exception as error:
        print(f"Error al obtener especiales: {error}")
        return jsonify({"msg": "Error al obtener los especiales"}), 500

def get_single_especial(especial_id):
    """
    Obtener un especial por ID
    """
    try:
        especial = Especial.find_by_id(especial_id)
        if not especial:
            return jsonify({"msg": "Especial no encontrado"}), 404
        
        especial_dict = Especial.to_dict(especial)
        return jsonify(especial_dict), 200
    except Exception as error:
        print(f"Error al obtener el especial: {error}")
        return jsonify({"msg": "Error al obtener el especial"}), 500

def create_especial(nombre, ingredientes, precio, activo=True):
    """
    Crear nuevo especial
    """
    try:
        # Validaciones básicas
        if not nombre or not ingredientes or precio is None:
            return jsonify({"msg": "Nombre, ingredientes y precio son requeridos"}), 400
        
        if precio < 0:
            return jsonify({"msg": "El precio no puede ser negativo"}), 400
        
        # Verificar si ya existe un especial con el mismo nombre
        existing_especial = Especial.find_by_name(nombre)
        if existing_especial:
            return jsonify({"msg": "Ya existe un especial con ese nombre"}), 400
        
        # Crear nuevo especial
        especial_data = {
            'nombre': nombre,
            'ingredientes': ingredientes,
            'precio': precio,
            'activo': activo
        }
        
        especial_id = Especial.create_especial(especial_data)
        especial = Especial.find_by_id(especial_id)
        especial_dict = Especial.to_dict(especial)
        
        return jsonify({
            "msg": "Especial creado exitosamente",
            "especial": especial_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear el especial: {error}")
        return jsonify({"msg": "Error al crear el especial"}), 500

def delete_especial(especial_id):
    """Eliminar un especial por ID"""
    try:
        # Verificar si el especial existe
        existing_especial = Especial.find_by_id(especial_id)
        if not existing_especial:
            return jsonify({"msg": "Especial no encontrado"}), 404
        
        # Eliminar el especial
        result = Especial.delete_especial(especial_id)
        
        if result:
            return jsonify({"msg": "Especial eliminado exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar el especial"}), 500
            
    except Exception as error:
        print(f"Error al eliminar especial {especial_id}: {str(error)}")
        return jsonify({"msg": "Error interno del servidor al eliminar especial"}), 500

def update_especial(especial_id, nombre=None, ingredientes=None, precio=None, activo=None):
    """
    Actualizar un especial por ID
    """
    try:
        # Verificar si el especial existe
        existing_especial = Especial.find_by_id(especial_id)
        if not existing_especial:
            return jsonify({"msg": "Especial no encontrado"}), 404
        
        update_data = {}
        
        if nombre is not None:
            # Verificar si el nombre ya está en uso por otro especial
            nombre_especial = Especial.find_by_name(nombre)
            if nombre_especial and nombre_especial.id != especial_id:
                return jsonify({"msg": "Ya existe un especial con ese nombre"}), 400
            update_data['nombre'] = nombre
            
        if ingredientes is not None:
            update_data['ingredientes'] = ingredientes
            
        if precio is not None:
            if precio < 0:
                return jsonify({"msg": "El precio no puede ser negativo"}), 400
            update_data['precio'] = precio
            
        if activo is not None:
            update_data['activo'] = activo
        
        if update_data:
            if Especial.update_especial(especial_id, update_data):
                # Obtener el especial actualizado
                updated_especial = Especial.find_by_id(especial_id)
                especial_dict = Especial.to_dict(updated_especial)
                
                return jsonify({
                    "msg": "Especial actualizado exitosamente",
                    "especial": especial_dict
                }), 200
            else:
                return jsonify({"msg": "No se realizaron cambios en el especial"}), 200
        else:
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
            
    except Exception as error:
        print(f"Error al actualizar el especial: {error}")
        return jsonify({
            "msg": "Error al actualizar el especial",
            "error": str(error)
        }), 500

def toggle_especial_activo(especial_id):
    """
    Activar/desactivar un especial
    """
    try:
        # Verificar si el especial existe
        existing_especial = Especial.find_by_id(especial_id)
        if not existing_especial:
            return jsonify({"msg": "Especial no encontrado"}), 404
        
        result = Especial.toggle_activo(especial_id)
        if result:
            # Obtener el especial actualizado
            updated_especial = Especial.find_by_id(especial_id)
            especial_dict = Especial.to_dict(updated_especial)
            
            estado = "activado" if updated_especial.activo else "desactivado"
            return jsonify({
                "msg": f"Especial {estado} exitosamente",
                "especial": especial_dict
            }), 200
        else:
            return jsonify({"msg": "Error al cambiar el estado del especial"}), 500
            
    except Exception as error:
        print(f"Error al cambiar estado del especial: {error}")
        return jsonify({"msg": "Error al cambiar el estado del especial"}), 500

def search_especiales(query):
    """Buscar especiales por nombre o ingredientes"""
    try:
        especiales = Especial.search_especiales(query)
        especiales_dict = [Especial.to_dict(especial) for especial in especiales]
        return jsonify(especiales_dict), 200
        
    except Exception as error:
        print(f"Error al buscar especiales: {error}")
        return jsonify({"msg": "Error al buscar especiales"}), 500

def get_active_especiales():
    """
    Obtener solo especiales activos
    """
    try:
        especiales = Especial.get_active_especiales()
        especiales_dict = [Especial.to_dict(especial) for especial in especiales]
        return jsonify(especiales_dict), 200
    except Exception as error:
        print(f"Error al obtener especiales activos: {error}")
        return jsonify({"msg": "Error al obtener los especiales activos"}), 500