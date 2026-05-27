from Models.Targetas import tarjeta_repo
from Models.User import user_repo
from flask import jsonify
import traceback

def get_tarjetas_usuario(user_id):
    """
    Obtener todas las tarjetas de un usuario
    """
    try:
        print(f"Obteniendo tarjetas para usuario ID: {user_id} (tipo: {type(user_id)})")
        
        # Verificar que el usuario existe
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # find_by_user manejará la conversión según DB_TYPE
        tarjetas = tarjeta_repo.find_by_user(user_id)
        tarjetas_dict = [tarjeta_repo.to_dict(t) for t in tarjetas]
        
        return jsonify({
            "tarjetas": tarjetas_dict,
            "total": len(tarjetas_dict)
        }), 200
        
    except Exception as e:
        print(f"Error en get_tarjetas_usuario: {e}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener tarjetas", "error": str(e)}), 500

def get_tarjeta_by_id(tarjeta_id):
    """
    Obtener una tarjeta por ID
    """
    try:
        tarjeta = tarjeta_repo.find_by_id(tarjeta_id)
        if not tarjeta:
            return jsonify({"msg": "Tarjeta no encontrada"}), 404
        
        return jsonify(tarjeta_repo.to_dict(tarjeta)), 200
        
    except Exception as e:
        print(f"Error en get_tarjeta_by_id: {e}")
        return jsonify({"msg": "Error al obtener tarjeta"}), 500

def get_tarjeta_predeterminada(user_id):
    """
    Obtener tarjeta predeterminada del usuario
    """
    try:
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        tarjeta = tarjeta_repo.find_predeterminada(user_id)
        if not tarjeta:
            return jsonify({"msg": "No hay tarjeta predeterminada"}), 404
        
        return jsonify(tarjeta_repo.to_dict(tarjeta)), 200
        
    except Exception as e:
        print(f"Error en get_tarjeta_predeterminada: {e}")
        return jsonify({"msg": "Error al obtener tarjeta predeterminada"}), 500

def create_tarjeta(user_id, tarjeta_data):
    """
    Crear nueva tarjeta para un usuario
    """
    try:
        # Verificar que el usuario existe
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Crear tarjeta
        tarjeta_id = tarjeta_repo.create_tarjeta(user_id, tarjeta_data)
        tarjeta = tarjeta_repo.find_by_id(tarjeta_id)
        
        return jsonify({
            "msg": "Tarjeta agregada exitosamente",
            "tarjeta": tarjeta_repo.to_dict(tarjeta)
        }), 201
        
    except ValueError as ve:
        return jsonify({"msg": str(ve)}), 400
    except Exception as e:
        print(f"Error en create_tarjeta: {e}")
        traceback.print_exc()
        return jsonify({"msg": "Error al crear tarjeta"}), 500

def update_tarjeta(tarjeta_id, update_data):
    """
    Actualizar una tarjeta
    """
    try:
        tarjeta = tarjeta_repo.find_by_id(tarjeta_id)
        if not tarjeta:
            return jsonify({"msg": "Tarjeta no encontrada"}), 404
        
        # Validar datos si se proporcionan
        if 'mes_expiracion' in update_data:
            mes = str(update_data['mes_expiracion'])
            if not mes.isdigit() or int(mes) < 1 or int(mes) > 12:
                return jsonify({"msg": "Mes de expiración inválido"}), 400
        
        if 'anio_expiracion' in update_data:
            anio = str(update_data['anio_expiracion'])
            if not anio.isdigit() or len(anio) != 4:
                return jsonify({"msg": "Año de expiración inválido"}), 400
        
        result = tarjeta_repo.update_tarjeta(tarjeta_id, update_data)
        
        if result:
            tarjeta_actualizada = tarjeta_repo.find_by_id(tarjeta_id)
            return jsonify({
                "msg": "Tarjeta actualizada exitosamente",
                "tarjeta": tarjeta_repo.to_dict(tarjeta_actualizada)
            }), 200
        else:
            return jsonify({"msg": "No se pudo actualizar la tarjeta"}), 500
            
    except Exception as e:
        print(f"Error en update_tarjeta: {e}")
        return jsonify({"msg": "Error al actualizar tarjeta"}), 500

def delete_tarjeta(tarjeta_id):
    """
    Eliminar tarjeta
    """
    try:
        tarjeta = tarjeta_repo.find_by_id(tarjeta_id)
        if not tarjeta:
            return jsonify({"msg": "Tarjeta no encontrada"}), 404
        
        # Obtener user_id antes de eliminar
        tarjeta_dict = tarjeta_repo.to_dict(tarjeta)
        user_id = tarjeta_dict['user_id']
        
        result = tarjeta_repo.delete_tarjeta(tarjeta_id)
        
        if result:
            # Si había otra tarjeta, establecer una como predeterminada
            otras_tarjetas = tarjeta_repo.find_by_user(user_id)
            if otras_tarjetas and len(otras_tarjetas) > 0:
                primera_tarjeta = otras_tarjetas[0]
                primera_id = primera_tarjeta.id if tarjeta_repo.db_type == 'mysql' else str(primera_tarjeta['_id'])
                tarjeta_repo.update_tarjeta(primera_id, {'predeterminada': True})
            
            return jsonify({"msg": "Tarjeta eliminada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar tarjeta"}), 500
            
    except Exception as e:
        print(f"Error en delete_tarjeta: {e}")
        return jsonify({"msg": "Error al eliminar tarjeta"}), 500

def set_tarjeta_predeterminada(user_id, tarjeta_id):
    """
    Establecer una tarjeta como predeterminada
    """
    try:
        tarjeta = tarjeta_repo.find_by_id(tarjeta_id)
        if not tarjeta:
            return jsonify({"msg": "Tarjeta no encontrada"}), 404
        
        # Verificar que la tarjeta pertenece al usuario
        tarjeta_dict = tarjeta_repo.to_dict(tarjeta)
        if str(tarjeta_dict['user_id']) != str(user_id):
            return jsonify({"msg": "La tarjeta no pertenece al usuario"}), 403
        
        # Quitar predeterminada de todas y establecer esta
        tarjeta_repo.remove_default_from_all(user_id)
        
        result = tarjeta_repo.update_tarjeta(tarjeta_id, {'predeterminada': True})
        
        if result:
            return jsonify({"msg": "Tarjeta predeterminada actualizada"}), 200
        else:
            return jsonify({"msg": "Error al establecer tarjeta predeterminada"}), 500
            
    except Exception as e:
        print(f"Error en set_tarjeta_predeterminada: {e}")
        return jsonify({"msg": "Error al establecer tarjeta predeterminada"}), 500