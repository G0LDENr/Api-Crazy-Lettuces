# Controllers/userController.py
from Models.User import UserRepository
from Models.Direccion import Direccion
from flask import jsonify, request
from flask_jwt_extended import create_access_token
from datetime import datetime
import traceback

# Instancia del repositorio
user_repo = UserRepository()

def login_user(email, password):
    """
    Iniciar sesión de usuario - CON BCRYPT Y MYSQL
    """
    try:
        if not email or not password:
            return jsonify({"msg": "Email y password son requeridos"}), 400
            
        print(f"🎯 Intentando login para: {email}")
        
        user = user_repo.find_by_credentials(email, password)
        
        if user:
            print(f"✅ Usuario autenticado")
            
            user_identity = str(user_repo.to_dict(user)['id'])
            access_token = create_access_token(identity=user_identity)
            
            user_dict = user_repo.to_dict(user, include_direcciones=True)
            
            return jsonify({
                'access_token': access_token,
                'user': user_dict
            }), 200
        else:
            print(f"❌ Falló autenticación para: {email}")
            return jsonify({"msg": "Credenciales inválidas"}), 401
            
    except Exception as error:
        print(f"💥 Error en login: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al iniciar sesión"}), 500

def get_all_users():
    """
    Obtener todos los usuarios
    """
    try:
        users = user_repo.get_all_users()
        users_dict = []
        
        for user in users:
            # Convertir a diccionario usando el repositorio
            user_dict = user_repo.to_dict(user, include_direcciones=False)
            
            # Si no viene dirección, intentar obtenerla directamente (compatible con ambas DBs)
            if not user_dict.get('direccion'):
                try:
                    from Models.Direccion import Direccion
                    from config import DB_TYPE
                    
                    # Obtener ID según el tipo de DB
                    user_id = None
                    if DB_TYPE == 'mysql':
                        if hasattr(user, 'id'):
                            user_id = user.id
                    else:  # MongoDB
                        if isinstance(user, dict) and '_id' in user:
                            from bson.objectid import ObjectId
                            user_id = str(user['_id'])
                        elif isinstance(user, dict) and 'id' in user:
                            user_id = user['id']
                    
                    if user_id:
                        print(f"Buscando dirección para usuario ID: {user_id}")
                        direccion_pred = Direccion.get_direccion_predeterminada(user_id)
                        if direccion_pred:
                            direccion_dict = Direccion.to_dict(direccion_pred)
                            user_dict['direccion'] = direccion_dict.get('direccion_completa')
                            print(f"Dirección encontrada: {user_dict['direccion']}")
                        else:
                            print(f"No hay dirección predeterminada para usuario {user_id}")
                    else:
                        print(f"No se pudo obtener ID del usuario")
                        
                except Exception as e:
                    print(f"Error forzando dirección: {e}")
                    import traceback
                    traceback.print_exc()
            
            users_dict.append(user_dict)
        
        print(f"Enviando {len(users_dict)} usuarios al frontend")
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener los usuarios"}), 500

def get_single_user(user_id, include_direcciones=True):
    """
    Obtener un usuario por ID
    """
    try:
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        user_dict = user_repo.to_dict(user, include_direcciones=include_direcciones)
        return jsonify(user_dict), 200
    except Exception as error:
        print(f"Error al obtener el usuario: {error}")
        return jsonify({"msg": "Error al obtener el usuario"}), 500

def create_user(name, email, password, role=2, telefono='', sexo='', direccion_data=None):
    """
    Crear nuevo usuario - CON BCRYPT
    """
    try:
        # Validar rol
        if not user_repo.is_valid_role(role):
            return jsonify({"msg": "Rol inválido"}), 400
        
        # Verificar si el usuario ya existe
        existing_user = user_repo.find_by_email(email)
        if existing_user:
            return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
        
        # Crear nuevo usuario
        user_data = {
            'nombre': name,
            'correo': email.lower().strip(),
            'contraseña': password,
            'rol': role,
            'telefono': telefono,
            'sexo': sexo,
            'fecha_registro': datetime.utcnow()
        }
        
        user_id = user_repo.create_user(user_data)
        user = user_repo.find_by_id(user_id)
        
        # Crear dirección si se proporciona
        if direccion_data:
            try:
                campos_requeridos = ['calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']
                for campo in campos_requeridos:
                    if not direccion_data.get(campo):
                        return jsonify({"msg": f"Para crear dirección, el campo '{campo}' es requerido"}), 400
                
                cp = direccion_data['codigo_postal']
                if not cp.isdigit() or len(cp) != 5:
                    return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
                
                direccion_data['predeterminada'] = True
                Direccion.create_direccion(user_id, direccion_data)
                print(f"✅ Dirección creada para usuario {user_id}")
            except Exception as dir_error:
                print(f"⚠️ Error al crear dirección: {dir_error}")
        
        user_dict = user_repo.to_dict(user, include_direcciones=True)
        
        return jsonify({
            "msg": "Usuario creado exitosamente",
            "user": user_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear el usuario: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al crear el usuario"}), 500

def delete_user(user_id):
    """
    Eliminar un usuario por ID
    """
    try:
        print(f"🔍 DEBUG CONTROLADOR - Solicitando eliminación del usuario ID: {user_id}")
        
        existing_user = user_repo.find_by_id(user_id)
        if not existing_user:
            print(f"❌ DEBUG CONTROLADOR - Usuario {user_id} no existe")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        result = user_repo.delete_user(user_id)
        
        if result:
            print(f"✅ DEBUG CONTROLADOR - Usuario {user_id} eliminado exitosamente")
            return jsonify({"msg": "Usuario eliminado exitosamente"}), 200
        else:
            print(f"❌ DEBUG CONTROLADOR - No se pudo eliminar el usuario {user_id}")
            return jsonify({"msg": "Error al eliminar el usuario"}), 500
            
    except Exception as error:
        print(f"💥 DEBUG CONTROLADOR - Error al eliminar usuario: {str(error)}")
        traceback.print_exc()
        return jsonify({"msg": "Error interno del servidor"}), 500

def update_user(user_id, name=None, email=None, password=None, role=None, telefono=None, sexo=None):
    """
    Actualizar un usuario por ID
    """
    try:
        existing_user = user_repo.find_by_id(user_id)
        if not existing_user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        update_data = {}
        
        if name is not None:
            update_data['nombre'] = name
        if email is not None:
            email_user = user_repo.find_by_email(email)
            if email_user:
                email_user_dict = user_repo.to_dict(email_user)
                if email_user_dict and str(email_user_dict['id']) != str(user_id):
                    return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
            update_data['correo'] = email.lower().strip()
        if password is not None:
            update_data['contraseña'] = password
        if role is not None:
            if not user_repo.is_valid_role(role):
                return jsonify({"msg": "Rol inválido"}), 400
            update_data['rol'] = role
        if telefono is not None:
            update_data['telefono'] = telefono
        if sexo is not None:
            update_data['sexo'] = sexo
        
        if update_data:
            if user_repo.update_user(user_id, update_data):
                updated_user = user_repo.find_by_id(user_id)
                user_dict = user_repo.to_dict(updated_user, include_direcciones=True)
                return jsonify({
                    "msg": "Usuario actualizado exitosamente",
                    "user": user_dict
                }), 200
            else:
                return jsonify({"msg": "No se pudieron actualizar los datos"}), 500
        else:
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
            
    except Exception as error:
        print(f"Error al actualizar el usuario: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al actualizar el usuario"}), 500

def get_user_profile(user_id):
    """Obtener perfil de usuario CON DIRECCIONES"""
    return get_single_user(user_id, include_direcciones=True)

def create_social_user(name, email, social_id, social_provider):
    """Crear usuario desde red social"""
    try:
        if not name or not email or not social_id or not social_provider:
            return jsonify({"msg": "Datos incompletos para crear usuario social"}), 400
        
        existing_user = user_repo.find_by_email(email)
        if existing_user:
            user_dict = user_repo.to_dict(existing_user, include_direcciones=True)
            access_token = create_access_token(identity=str(user_dict['id']))
            return jsonify({
                'access_token': access_token,
                'user': user_dict
            }), 200
        
        user_data = {
            'nombre': name,
            'correo': email.lower().strip(),
            'contraseña': social_id,
            'rol': 2,
            'telefono': '',
            'sexo': '',
            'fecha_registro': datetime.utcnow()
        }
        
        user_id = user_repo.create_user(user_data)
        user = user_repo.find_by_id(user_id)
        user_dict = user_repo.to_dict(user, include_direcciones=True)
        
        access_token = create_access_token(identity=str(user_dict['id']))
        
        return jsonify({
            'access_token': access_token,
            'user': user_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear usuario social: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al crear usuario desde red social"}), 500

def search_users(query):
    """Buscar usuarios por nombre o email"""
    try:
        users = user_repo.search_users(query)
        users_dict = [user_repo.to_dict(user, include_direcciones=False) for user in users]
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al buscar usuarios: {error}")
        return jsonify({"msg": "Error al buscar usuarios"}), 500

def change_password(user_id, current_password, new_password):
    """
    Cambiar contraseña de usuario
    """
    try:
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        user_dict = user_repo.to_dict(user)
        if not user_repo.find_by_credentials(user_dict['correo'], current_password):
            return jsonify({"msg": "Contraseña actual incorrecta"}), 401
        
        if len(new_password) < 6:
            return jsonify({"msg": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
        
        update_data = {'contraseña': new_password}
        if user_repo.update_user(user_id, update_data):
            return jsonify({"msg": "Contraseña actualizada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al actualizar la contraseña"}), 500
            
    except Exception as error:
        print(f"Error al cambiar contraseña: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al cambiar contraseña"}), 500

def get_users_by_role(role_id):
    """
    Obtener usuarios por rol
    """
    try:
        if not user_repo.is_valid_role(role_id):
            return jsonify({"msg": "Rol inválido"}), 400
            
        users = user_repo.get_users_by_role(role_id)
        users_dict = [user_repo.to_dict(user, include_direcciones=False) for user in users]
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios por rol: {error}")
        return jsonify({"msg": "Error al obtener usuarios"}), 500

def get_available_roles():
    """
    Obtener roles disponibles
    """
    try:
        from config import ROLES
        return jsonify(ROLES), 200
    except Exception as error:
        print(f"Error al obtener roles: {error}")
        return jsonify({"msg": "Error al obtener los roles"}), 500

# Funciones para direcciones
def get_user_with_direcciones(user_id):
    """Obtener usuario con todas sus direcciones"""
    return get_single_user(user_id, include_direcciones=True)

def create_user_with_direccion(name, email, password, role=2, telefono='', sexo='', direccion_data=None):
    """Crear usuario con dirección inicial"""
    return create_user(name, email, password, role, telefono, sexo, direccion_data)

def update_user_with_direccion(user_id, name=None, email=None, password=None, role=None, telefono=None, sexo=None, direccion_data=None):
    """
    Actualizar usuario y/o su dirección predeterminada
    """
    try:
        update_data = {}
        if name is not None: update_data['nombre'] = name
        if email is not None: update_data['correo'] = email.lower().strip()
        if password is not None: update_data['contraseña'] = password
        if role is not None: update_data['rol'] = role
        if telefono is not None: update_data['telefono'] = telefono
        if sexo is not None: update_data['sexo'] = sexo
        
        if update_data:
            user_repo.update_user(user_id, update_data)
        
        if direccion_data:
            campos_requeridos = ['calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']
            for campo in campos_requeridos:
                if not direccion_data.get(campo):
                    return jsonify({"msg": f"El campo '{campo}' es requerido para la dirección"}), 400
            
            cp = direccion_data['codigo_postal']
            if not cp.isdigit() or len(cp) != 5:
                return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
            
            from Models.Direccion import Direccion
            direccion_predeterminada = Direccion.get_direccion_predeterminada(user_id)
            
            if direccion_predeterminada:
                Direccion.update_direccion(direccion_predeterminada.id, direccion_data)
            else:
                direccion_data['predeterminada'] = True
                Direccion.create_direccion(user_id, direccion_data)
        
        user = user_repo.find_by_id(user_id)
        user_dict = user_repo.to_dict(user, include_direcciones=True)
        
        return jsonify({
            "msg": "Usuario actualizado exitosamente",
            "user": user_dict
        }), 200
        
    except Exception as error:
        print(f"Error al actualizar usuario con dirección: {error}")
        return jsonify({"msg": "Error al actualizar usuario"}), 500