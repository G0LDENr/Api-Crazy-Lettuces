from Models.User import User
from Models.Direccion import Direccion
from flask import jsonify, request
from flask_jwt_extended import create_access_token
from datetime import datetime

def login_user(email, password):
    """
    Iniciar sesión de usuario - CON BCRYPT Y MYSQL
    """
    try:
        if not email or not password:
            return jsonify({"msg": "Email y password son requeridos"}), 400
            
        print(f"🎯 Intentando login para: {email}")
        
        # Buscar usuario con la estructura actual
        user = User.find_by_credentials(email, password)
        
        if user:
            print(f"✅ Usuario autenticado: {user.correo}")
            print(f"📝 Datos del usuario - Nombre: {user.nombre}, Teléfono: {user.telefono}")
            
            # CORRECCIÓN: El identity debe ser un string (solo el ID)
            user_identity = str(user.id)  # Solo el ID como string
            
            access_token = create_access_token(identity=user_identity)
            
            # Convertir usuario a formato para frontend CON DIRECCIONES
            user_dict = User.to_dict(user, include_direcciones=True)
            print(f"📋 Diccionario del usuario a enviar: {user_dict}")
            
            return jsonify({
                'access_token': access_token,
                'user': user_dict
            }), 200
        else:
            print(f"❌ Falló autenticación para: {email}")
            return jsonify({"msg": "Credenciales inválidas"}), 401
            
    except Exception as error:
        print(f"💥 Error completo en login: {error}")
        return jsonify({"msg": "Error al iniciar sesión"}), 500

def get_all_users():
    """
    Obtener todos los usuarios
    """
    try:
        users = User.get_all_users()
        users_dict = [User.to_dict(user, include_direcciones=False) for user in users]
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios: {error}")
        return jsonify({"msg": "Error al obtener los usuarios"}), 500

def get_single_user(user_id, include_direcciones=True):
    """
    Obtener un usuario por ID
    """
    try:
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        user_dict = User.to_dict(user, include_direcciones=include_direcciones)
        return jsonify(user_dict), 200
    except Exception as error:
        print(f"Error al obtener el usuario: {error}")
        return jsonify({"msg": "Error al obtener el usuario"}), 500

def create_user(name, email, password, role=2, telefono='', sexo='', direccion_data=None):
    """
    Crear nuevo usuario - CON BCRYPT Y MYSQL
    """
    try:
        # Validar rol
        if not User.is_valid_role(role):
            return jsonify({"msg": "Rol inválido"}), 400
        
        # Verificar si el usuario ya existe
        existing_user = User.find_by_email(email)
        if existing_user:
            return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
        
        # Crear nuevo usuario con estructura actual Y BCRYPT
        user_data = {
            'nombre': name,
            'correo': email.lower().strip(),
            'contraseña': password,  # Se hasheará automáticamente en el modelo
            'rol': role,
            'telefono': telefono,
            'sexo': sexo,
            'fecha_registro': datetime.utcnow()
        }
        
        user_id = User.create_user(user_data)
        user = User.find_by_id(user_id)
        
        # Crear dirección si se proporciona
        if direccion_data:
            try:
                # Validar datos de dirección
                campos_requeridos = ['calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']
                for campo in campos_requeridos:
                    if not direccion_data.get(campo):
                        return jsonify({"msg": f"Para crear dirección, el campo '{campo}' es requerido"}), 400
                
                # Validar código postal
                cp = direccion_data['codigo_postal']
                if not cp.isdigit() or len(cp) != 5:
                    return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
                
                # Crear dirección como predeterminada
                direccion_data['predeterminada'] = True
                Direccion.create_direccion(user_id, direccion_data)
                print(f"✅ Dirección creada para usuario {user_id}")
            except Exception as dir_error:
                print(f"⚠️ Error al crear dirección para usuario nuevo: {dir_error}")
                # No retornar error, solo continuar sin dirección
        
        user_dict = User.to_dict(user, include_direcciones=True)
        
        return jsonify({
            "msg": "Usuario creado exitosamente",
            "user": user_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear el usuario: {error}")
        return jsonify({"msg": "Error al crear el usuario"}), 500

def delete_user(user_id):
    """Eliminar un usuario por ID"""
    try:
        print(f"🔍 DEBUG CONTROLADOR - Solicitando eliminación del usuario ID: {user_id}")
        print(f"🔍 DEBUG CONTROLADOR - Tipo de user_id: {type(user_id)}, Valor: {user_id}")
        
        # Verificar si el usuario existe primero
        existing_user = User.find_by_id(user_id)
        print(f"🔍 DEBUG CONTROLADOR - Usuario encontrado en DB: {existing_user is not None}")
        
        if existing_user:
            print(f"🔍 DEBUG CONTROLADOR - Información del usuario:")
            print(f"   ID: {existing_user.id}")
            print(f"   Nombre: {existing_user.nombre}")
            print(f"   Email: {existing_user.correo}")
            print(f"   Rol: {existing_user.rol}")
        else:
            print(f"❌ DEBUG CONTROLADOR - Usuario {user_id} no existe en la base de datos")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Llamar a la función del modelo para eliminar
        print(f"🔍 DEBUG CONTROLADOR - Llamando a User.delete_user({user_id})...")
        result = User.delete_user(user_id)
        print(f"🔍 DEBUG CONTROLADOR - Resultado de User.delete_user: {result}")
        
        if result:
            print(f"✅ DEBUG CONTROLADOR - Usuario {user_id} eliminado exitosamente")
            return jsonify({"msg": "Usuario eliminado exitosamente"}), 200
        else:
            print(f"❌ DEBUG CONTROLADOR - No se pudo eliminar el usuario {user_id}")
            return jsonify({"msg": "Error al eliminar el usuario"}), 500
            
    except Exception as error:
        print(f"💥 DEBUG CONTROLADOR - Error completo al eliminar usuario {user_id}: {str(error)}")
        print(f"💥 DEBUG CONTROLADOR - Tipo de error: {type(error).__name__}")
        import traceback
        print(f"💥 DEBUG CONTROLADOR - Traceback completo:")
        traceback.print_exc()
        return jsonify({"msg": "Error interno del servidor al eliminar usuario"}), 500

def update_user(user_id, name=None, email=None, password=None, role=None, telefono=None, sexo=None):
    """
    Actualizar un usuario por ID
    """
    try:
        # Verificar si el usuario existe
        existing_user = User.find_by_id(user_id)
        if not existing_user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        update_data = {}
        
        # Solo agregar al diccionario si el valor no es None
        if name is not None:
            update_data['nombre'] = name
        if email is not None:
            # Verificar si el email ya está en uso por otro usuario
            email_user = User.find_by_email(email)
            if email_user and email_user.id != user_id:
                return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
            update_data['correo'] = email.lower().strip()
        if password is not None:
            update_data['contraseña'] = password  # Se hasheará automáticamente
        if role is not None:
            if not User.is_valid_role(role):
                return jsonify({"msg": "Rol inválido"}), 400
            update_data['rol'] = role
        if telefono is not None:
            update_data['telefono'] = telefono
        if sexo is not None:
            update_data['sexo'] = sexo
        
        print(f"🔧 Datos para actualizar usuario {user_id}: {update_data}")
        
        if update_data:
            print(f"🔄 Actualizando usuario {user_id} con datos: {update_data}")
            if User.update_user(user_id, update_data):
                print(f"✅ Usuario {user_id} actualizado exitosamente")
                # Obtener el usuario actualizado
                updated_user = User.find_by_id(user_id)
                if updated_user:
                    user_dict = User.to_dict(updated_user, include_direcciones=True)
                    return jsonify({
                        "msg": "Usuario actualizado exitosamente",
                        "user": user_dict
                    }), 200
                else:
                    print(f"⚠️ Usuario {user_id} no encontrado después de actualizar")
                    return jsonify({"msg": "Usuario actualizado pero no encontrado"}), 500
            else:
                print(f"❌ No se pudieron actualizar los datos del usuario {user_id}")
                return jsonify({"msg": "No se pudieron actualizar los datos"}), 500
        else:
            print(f"⚠️ No se proporcionaron datos para actualizar usuario {user_id}")
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
            
    except Exception as error:
        print(f"💥 Error al actualizar el usuario: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "msg": "Error al actualizar el usuario",
            "error": str(error)
        }), 500

def get_user_profile(user_id):
    """Obtener perfil de usuario CON DIRECCIONES"""
    return get_single_user(user_id, include_direcciones=True)

def create_social_user(name, email, social_id, social_provider):
    """Crear usuario desde red social"""
    try:
        if not name or not email or not social_id or not social_provider:
            return jsonify({"msg": "Datos incompletos para crear usuario social"}), 400
            
        # Crear usuario normal sin contraseña
        user_data = {
            'nombre': name,
            'correo': email.lower().strip(),
            'contraseña': social_id,  # Usar social_id como contraseña temporal
            'rol': 2,
            'telefono': '',
            'sexo': ''
        }
        
        user_id = User.create_user(user_data)
        user = User.find_by_id(user_id)
        user_dict = User.to_dict(user, include_direcciones=True)
        
        # Crear token JWT
        token_data = str(user.id)
        access_token = create_access_token(identity=token_data)
        
        return jsonify({
            'access_token': access_token,
            'user': user_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear usuario social: {error}")
        return jsonify({"msg": "Error al crear usuario desde red social"}), 500

def search_users(query):
    """Buscar usuarios por nombre o email"""
    try:
        users = User.search_users(query)
        users_dict = [User.to_dict(user, include_direcciones=False) for user in users]
        return jsonify(users_dict), 200
        
    except Exception as error:
        print(f"Error al buscar usuarios: {error}")
        return jsonify({"msg": "Error al buscar usuarios"}), 500

def change_password(user_id, current_password, new_password):
    """
    Cambiar contraseña de usuario
    """
    try:
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Verificar contraseña actual
        if not User.find_by_credentials(user.correo, current_password):
            return jsonify({"msg": "Contraseña actual incorrecta"}), 401
        
        # Validar nueva contraseña
        if len(new_password) < 6:
            return jsonify({"msg": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
        
        # Actualizar contraseña
        update_data = {'contraseña': new_password}
        if User.update_user(user_id, update_data):
            return jsonify({"msg": "Contraseña actualizada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al actualizar la contraseña"}), 500
            
    except Exception as error:
        print(f"Error al cambiar contraseña: {error}")
        return jsonify({"msg": "Error al cambiar contraseña"}), 500

def get_users_by_role(role_id):
    """
    Obtener usuarios por rol
    """
    try:
        if not User.is_valid_role(role_id):
            return jsonify({"msg": "Rol inválido"}), 400
            
        users = User.get_users_by_role(role_id)
        users_dict = [User.to_dict(user, include_direcciones=False) for user in users]
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios por rol: {error}")
        return jsonify({"msg": "Error al obtener usuarios"}), 500

def get_available_roles():
    """
    Obtener roles disponibles
    """
    try:
        roles = User.get_roles()
        return jsonify(roles), 200
    except Exception as error:
        print(f"Error al obtener roles: {error}")
        return jsonify({"msg": "Error al obtener los roles"}), 500

# NUEVAS FUNCIONES PARA DIRECCIONES EN USER CONTROLLER

def get_user_with_direcciones(user_id):
    """
    Obtener usuario con todas sus direcciones
    """
    return get_single_user(user_id, include_direcciones=True)

def create_user_with_direccion(name, email, password, role=2, telefono='', sexo='', direccion_data=None):
    """
    Crear usuario con dirección inicial
    """
    return create_user(name, email, password, role, telefono, sexo, direccion_data)

def update_user_with_direccion(user_id, name=None, email=None, password=None, role=None, telefono=None, sexo=None, direccion_data=None):
    """
    Actualizar usuario y/o su dirección predeterminada
    """
    try:
        # Actualizar datos básicos del usuario
        update_data = {}
        if name is not None: update_data['nombre'] = name
        if email is not None: update_data['correo'] = email.lower().strip()
        if password is not None: update_data['contraseña'] = password
        if role is not None: update_data['rol'] = role
        if telefono is not None: update_data['telefono'] = telefono
        if sexo is not None: update_data['sexo'] = sexo
        
        # Actualizar usuario si hay datos
        if update_data:
            User.update_user(user_id, update_data)
        
        # Si se proporciona dirección, actualizarla o crearla
        if direccion_data:
            # Validar datos de dirección
            campos_requeridos = ['calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']
            for campo in campos_requeridos:
                if not direccion_data.get(campo):
                    return jsonify({"msg": f"El campo '{campo}' es requerido para la dirección"}), 400
            
            # Validar código postal
            cp = direccion_data['codigo_postal']
            if not cp.isdigit() or len(cp) != 5:
                return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
            
            # Buscar si el usuario ya tiene una dirección predeterminada
            direccion_predeterminada = Direccion.get_direccion_predeterminada(user_id)
            
            if direccion_predeterminada:
                # Actualizar dirección predeterminada existente
                Direccion.update_direccion(direccion_predeterminada.id, direccion_data)
            else:
                # Crear nueva dirección como predeterminada
                direccion_data['predeterminada'] = True
                Direccion.create_direccion(user_id, direccion_data)
        
        # Obtener usuario actualizado
        user = User.find_by_id(user_id)
        user_dict = User.to_dict(user, include_direcciones=True)
        
        return jsonify({
            "msg": "Usuario actualizado exitosamente",
            "user": user_dict
        }), 200
        
    except Exception as error:
        print(f"Error al actualizar usuario con dirección: {error}")
        return jsonify({"msg": "Error al actualizar usuario"}), 500