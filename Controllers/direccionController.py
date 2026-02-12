from Models.Direccion import Direccion
from Models.User import User
from flask import jsonify

def get_all_direcciones():
    """
    Obtener todas las direcciones
    """
    try:
        direcciones = Direccion.get_all_direcciones()
        direcciones_dict = [Direccion.to_dict(dir) for dir in direcciones]
        return jsonify(direcciones_dict), 200
    except Exception as error:
        print(f"Error al obtener direcciones: {error}")
        return jsonify({"msg": "Error al obtener las direcciones"}), 500

def get_single_direccion(direccion_id):
    """
    Obtener una dirección por ID
    """
    try:
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        direccion_dict = Direccion.to_dict(direccion)
        return jsonify(direccion_dict), 200
    except Exception as error:
        print(f"Error al obtener la dirección: {error}")
        return jsonify({"msg": "Error al obtener la dirección"}), 500

def create_direccion(direccion_data):
    """
    Crear nueva dirección
    """
    try:
        # Validar datos requeridos
        campos_requeridos = ['user_id', 'calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']
        for campo in campos_requeridos:
            if not direccion_data.get(campo):
                return jsonify({"msg": f"El campo '{campo}' es requerido"}), 400
        
        # Validar que el usuario exista
        user = User.find_by_id(direccion_data['user_id'])
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Validar código postal
        cp = direccion_data['codigo_postal']
        if not cp.isdigit() or len(cp) != 5:
            return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
        
        # Crear dirección
        direccion_id = Direccion.create_direccion(direccion_data['user_id'], direccion_data)
        direccion = Direccion.get_direccion_by_id(direccion_id)
        
        return jsonify({
            "msg": "Dirección creada exitosamente",
            "direccion": Direccion.to_dict(direccion)
        }), 201
        
    except Exception as error:
        print(f"Error al crear dirección: {error}")
        return jsonify({"msg": "Error al crear la dirección"}), 500

def update_direccion(direccion_id, update_data):
    """
    Actualizar una dirección
    """
    try:
        # Validar que la dirección exista
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        # Validar código postal si se actualiza
        if 'codigo_postal' in update_data:
            cp = update_data['codigo_postal']
            if not cp.isdigit() or len(cp) != 5:
                return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
        
        # Actualizar dirección
        if Direccion.update_direccion(direccion_id, update_data):
            direccion_actualizada = Direccion.get_direccion_by_id(direccion_id)
            return jsonify({
                "msg": "Dirección actualizada exitosamente",
                "direccion": Direccion.to_dict(direccion_actualizada)
            }), 200
        else:
            return jsonify({"msg": "Error al actualizar la dirección"}), 500
            
    except Exception as error:
        print(f"Error al actualizar dirección: {error}")
        return jsonify({"msg": "Error al actualizar la dirección"}), 500

def delete_direccion(direccion_id):
    """
    Eliminar una dirección
    """
    try:
        # Verificar si la dirección existe
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        # Eliminar dirección
        if Direccion.delete_direccion(direccion_id):
            return jsonify({"msg": "Dirección eliminada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar la dirección"}), 500
            
    except Exception as error:
        print(f"Error al eliminar dirección: {error}")
        return jsonify({"msg": "Error al eliminar la dirección"}), 500

def get_direcciones_by_user(user_id):
    """
    Obtener todas las direcciones de un usuario
    """
    try:
        # Verificar que el usuario exista
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        direcciones = Direccion.get_direcciones_by_user(user_id)
        direcciones_dict = [Direccion.to_dict(dir) for dir in direcciones]
        
        return jsonify({
            "direcciones": direcciones_dict,
            "total": len(direcciones_dict),
            "usuario": {
                "id": user.id,
                "nombre": user.nombre,
                "email": user.correo
            }
        }), 200
        
    except Exception as error:
        print(f"Error al obtener direcciones del usuario: {error}")
        return jsonify({"msg": "Error al obtener las direcciones"}), 500

def get_direccion_predeterminada(user_id):
    """
    Obtener dirección predeterminada de un usuario
    """
    try:
        # Verificar que el usuario exista
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        direccion = Direccion.get_direccion_predeterminada(user_id)
        if not direccion:
            return jsonify({"msg": "El usuario no tiene una dirección predeterminada"}), 404
        
        return jsonify({
            "direccion": Direccion.to_dict(direccion),
            "usuario": {
                "id": user.id,
                "nombre": user.nombre,
                "email": user.correo
            }
        }), 200
        
    except Exception as error:
        print(f"Error al obtener dirección predeterminada: {error}")
        return jsonify({"msg": "Error al obtener dirección predeterminada"}), 500

def set_direccion_predeterminada(user_id, direccion_id):
    """
    Establecer dirección como predeterminada
    """
    try:
        # Verificar que el usuario exista
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Verificar que la dirección exista y pertenezca al usuario
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion or direccion.user_id != user_id:
            return jsonify({"msg": "Dirección no encontrada o no pertenece al usuario"}), 404
        
        # Actualizar para que sea predeterminada
        update_data = {'predeterminada': True}
        if Direccion.update_direccion(direccion_id, update_data):
            return jsonify({"msg": "Dirección establecida como predeterminada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al establecer dirección predeterminada"}), 500
            
    except Exception as error:
        print(f"Error al establecer dirección predeterminada: {error}")
        return jsonify({"msg": "Error al establecer dirección predeterminada"}), 500

def search_direcciones(query):
    """
    Buscar direcciones por calle, colonia, ciudad o estado
    """
    try:
        direcciones = Direccion.search_direcciones(query)
        direcciones_dict = [Direccion.to_dict(dir) for dir in direcciones]
        return jsonify(direcciones_dict), 200
        
    except Exception as error:
        print(f"Error al buscar direcciones: {error}")
        return jsonify({"msg": "Error al buscar direcciones"}), 500