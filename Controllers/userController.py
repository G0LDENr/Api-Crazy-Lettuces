from Models.User import UserRepository
from Models.Direccion import Direccion
from flask import jsonify, request
from flask_jwt_extended import create_access_token
from datetime import datetime
import traceback
import json

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
            
            # Incluir niños en la respuesta si es una cuenta personal con hijos
            user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
            
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
    Obtener todos los usuarios - INCLUYE EDAD
    """
    try:
        users = user_repo.get_all_users()
        users_dict = []
        
        for user in users:
            # IMPORTANTE: Incluir edad en la respuesta
            user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=False)
            
            # Log para verificar que la edad está presente
            print(f"👤 Usuario {user_dict.get('nombre')} - Edad: {user_dict.get('edad')}")
            
            # Si no viene dirección, intentar obtenerla directamente
            if not user_dict.get('direccion'):
                try:
                    from Models.Direccion import Direccion
                    from config import DB_TYPE
                    
                    user_id = None
                    if DB_TYPE == 'mysql':
                        if hasattr(user, 'id'):
                            user_id = user.id
                    else:
                        if isinstance(user, dict) and '_id' in user:
                            from bson.objectid import ObjectId
                            user_id = str(user['_id'])
                        elif isinstance(user, dict) and 'id' in user:
                            user_id = user['id']
                    
                    if user_id:
                        direccion_pred = Direccion.get_direccion_predeterminada(user_id)
                        if direccion_pred:
                            direccion_dict = Direccion.to_dict(direccion_pred)
                            user_dict['direccion'] = direccion_dict.get('direccion_completa')
                except Exception as e:
                    print(f"Error forzando dirección: {e}")
            
            users_dict.append(user_dict)
        
        print(f"📊 Total usuarios: {len(users_dict)}")
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener los usuarios"}), 500

def get_single_user(user_id, include_direcciones=True, include_tarjetas=True, include_ninos=True):
    """
    Obtener un usuario por ID
    """
    try:
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        user_dict = user_repo.to_dict(
            user, 
            include_direcciones=include_direcciones, 
            include_tarjetas=include_tarjetas,
            include_ninos=include_ninos
        )
        return jsonify(user_dict), 200
    except Exception as error:
        print(f"Error al obtener el usuario: {error}")
        return jsonify({"msg": "Error al obtener el usuario"}), 500

def create_user(name, email, password, role=2, telefono='', sexo='', 
                direccion_data=None, tarjeta_data=None, 
                tipo_cuenta='personal', edad=None, 
                tutor_nombre=None, tutor_telefono=None):
    """
    Crear nuevo usuario - CON EDAD INCLUIDA
    """
    try:
        # Validar rol
        if not user_repo.is_valid_role(role):
            return jsonify({"msg": "Rol inválido"}), 400
        
        # Verificar si el usuario ya existe
        existing_user = user_repo.find_by_email(email)
        if existing_user:
            return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
        
        # Validar tipo de cuenta
        if tipo_cuenta not in ['personal', 'infantil']:
            return jsonify({"msg": "Tipo de cuenta inválido. Use 'personal' o 'infantil'"}), 400
        
        # Validar edad según tipo de cuenta
        if tipo_cuenta == 'infantil':
            if not edad:
                return jsonify({"msg": "La edad es requerida para cuentas infantiles"}), 400
            try:
                edad_int = int(edad)
                if edad_int < 3 or edad_int > 17:
                    return jsonify({"msg": "La edad para cuentas infantiles debe ser entre 3 y 17 años"}), 400
            except ValueError:
                return jsonify({"msg": "Edad inválida"}), 400
            
            # Validar datos del tutor para cuenta infantil
            if not tutor_nombre or not tutor_telefono:
                return jsonify({"msg": "El nombre y teléfono del tutor son requeridos para cuentas infantiles"}), 400
        
        # LOG IMPORTANTE - Ver qué edad está llegando
        print(f"📝 EDAD RECIBIDA: {edad} (tipo: {type(edad)})")
        
        # Crear nuevo usuario - INCLUYENDO EDAD
        user_data = {
            'nombre': name,
            'correo': email.lower().strip(),
            'contraseña': password,
            'rol': role,
            'telefono': telefono,
            'sexo': sexo,
            'fecha_registro': datetime.utcnow(),
            'tipo_cuenta': tipo_cuenta,
            'edad': edad,  # <-- EDAD INCLUIDA
            'tutor_nombre': tutor_nombre if tipo_cuenta == 'infantil' else None,
            'tutor_telefono': tutor_telefono if tipo_cuenta == 'infantil' else None
        }
        
        print(f"📦 DATOS COMPLETOS A GUARDAR: {user_data}")
        
        user_id = user_repo.create_user(user_data)
        print(f"✅ Usuario creado con ID: {user_id}")
        
        user = user_repo.find_by_id(user_id)
        
        # Crear dirección si se proporciona (solo para cuentas personales)
        if direccion_data and tipo_cuenta == 'personal':
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
        
        # Crear tarjeta si se proporciona (solo para cuentas personales)
        if tarjeta_data and tipo_cuenta == 'personal':
            try:
                from Controllers.targetasController import create_tarjeta
                result = create_tarjeta(user_id, tarjeta_data)
                if result[1] == 201:
                    print(f"✅ Tarjeta creada para usuario {user_id}")
                else:
                    print(f"⚠️ Error al crear tarjeta: {result[0].get_json()}")
            except Exception as tarjeta_error:
                print(f"⚠️ Error al crear tarjeta: {tarjeta_error}")
        
        user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
        
        # Verificar que la edad está en la respuesta
        print(f"📤 RESPUESTA FINAL - Edad: {user_dict.get('edad')}")
        
        return jsonify({
            "msg": "Usuario creado exitosamente",
            "user": user_dict
        }), 201
        
    except Exception as error:
        print(f"❌ Error al crear el usuario: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al crear el usuario"}), 500

def delete_user(user_id):
    """
    Eliminar un usuario por ID
    """
    try:
        print(f"🔍 Solicitando eliminación del usuario ID: {user_id}")
        
        existing_user = user_repo.find_by_id(user_id)
        if not existing_user:
            print(f"❌ Usuario {user_id} no existe")
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Obtener usuario para verificar si tiene teléfono
        user_dict = user_repo.to_dict(existing_user)
        
        # Verificar si tiene cuentas infantiles asociadas por teléfono
        if user_dict.get('telefono'):
            ninos = user_repo.find_children_by_tutor(user_dict['telefono'])
            if ninos:
                return jsonify({
                    "msg": "No se puede eliminar el usuario porque tiene cuentas infantiles asociadas",
                    "ninos_count": len(ninos)
                }), 400
        
        result = user_repo.delete_user(user_id)
        
        if result:
            print(f"✅ Usuario {user_id} eliminado exitosamente")
            return jsonify({"msg": "Usuario eliminado exitosamente"}), 200
        else:
            print(f"❌ No se pudo eliminar el usuario {user_id}")
            return jsonify({"msg": "Error al eliminar el usuario"}), 500
            
    except Exception as error:
        print(f"💥 Error al eliminar usuario: {str(error)}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Error interno del servidor"}), 500

def update_user(user_id, name=None, email=None, password=None, role=None, 
                telefono=None, sexo=None, tipo_cuenta=None, edad=None, 
                tutor_nombre=None, tutor_telefono=None, restricciones_infantiles=None):
    try:
        existing_user = user_repo.find_by_id(user_id)
        if not existing_user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        update_data = {}
        old_role = None
        
        if isinstance(existing_user, dict):
            old_role = existing_user.get('rol')
        else:
            old_role = existing_user.rol
        
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
        if tipo_cuenta is not None:
            if tipo_cuenta not in ['personal', 'infantil']:
                return jsonify({"msg": "Tipo de cuenta inválido"}), 400
            update_data['tipo_cuenta'] = tipo_cuenta
        if edad is not None:
            try:
                edad_int = int(edad)
                if tipo_cuenta == 'infantil' and (edad_int < 3 or edad_int > 17):
                    return jsonify({"msg": "La edad para cuentas infantiles debe ser entre 3 y 17 años"}), 400
                update_data['edad'] = edad_int
            except ValueError:
                return jsonify({"msg": "Edad inválida"}), 400
        if tutor_nombre is not None:
            update_data['tutor_nombre'] = tutor_nombre
        if tutor_telefono is not None:
            update_data['tutor_telefono'] = tutor_telefono
        if restricciones_infantiles is not None:
            try:
                if isinstance(restricciones_infantiles, str):
                    json.loads(restricciones_infantiles)
                update_data['restricciones_infantiles'] = restricciones_infantiles
            except:
                return jsonify({"msg": "Formato de restricciones inválido"}), 400
        
        if update_data:
            if user_repo.update_user(user_id, update_data):
                # Si el rol cambió a administrador (rol 1) y antes no lo era
                if role is not None and role == 1 and old_role != 1:
                    # Verificar si ya tiene código
                    existing_code = user_repo.has_valid_backup_code(user_id)
                    
                    if not existing_code:
                        backup_code = user_repo.generate_backup_code(user_id)
                        if backup_code:
                            from Controllers.notificacionesController import create_notification
                            create_notification(
                                user_id=user_id,
                                titulo="🔐 Código de Respaldo Único",
                                mensaje=f"Tu código único para realizar respaldos es: **{backup_code}**\n\n"
                                        f"⚠️ Este código es PERMANENTE. Guárdalo en un lugar seguro.\n"
                                        f"Se usará para autenticar todas tus operaciones de respaldo.",
                                tipo="backup_code"
                            )
                            print(f"✅ Notificación enviada con código: {backup_code}")
                    else:
                        print(f"ℹ️ El usuario ya tiene un código de respaldo")
                
                updated_user = user_repo.find_by_id(user_id)
                user_dict = user_repo.to_dict(updated_user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
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
    """Obtener perfil de usuario CON DIRECCIONES, TARJETAS Y NIÑOS"""
    return get_single_user(user_id, include_direcciones=True, include_tarjetas=True, include_ninos=True)

def create_social_user(name, email, social_id, social_provider, tipo_cuenta='personal', edad=None):
    """Crear usuario desde red social"""
    try:
        if not name or not email or not social_id or not social_provider:
            return jsonify({"msg": "Datos incompletos para crear usuario social"}), 400
        
        # Validar tipo de cuenta
        if tipo_cuenta not in ['personal', 'infantil']:
            return jsonify({"msg": "Tipo de cuenta inválido"}), 400
        
        # Validar edad para cuentas infantiles
        if tipo_cuenta == 'infantil' and not edad:
            return jsonify({"msg": "La edad es requerida para cuentas infantiles"}), 400
        
        existing_user = user_repo.find_by_email(email)
        if existing_user:
            user_dict = user_repo.to_dict(existing_user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
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
            'fecha_registro': datetime.utcnow(),
            'tipo_cuenta': tipo_cuenta,
            'edad': edad
        }
        
        user_id = user_repo.create_user(user_data)
        user = user_repo.find_by_id(user_id)
        user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
        
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
        users_dict = [user_repo.to_dict(user, include_direcciones=False, include_tarjetas=False) for user in users]
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
        users_dict = [user_repo.to_dict(user, include_direcciones=False, include_tarjetas=False) for user in users]
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

# ============ FUNCIONES PARA CUENTAS INFANTILES ============

def get_users_by_tipo_cuenta(tipo_cuenta):
    """Obtener usuarios por tipo de cuenta"""
    try:
        if tipo_cuenta not in ['personal', 'infantil']:
            return jsonify({"msg": "Tipo de cuenta inválido"}), 400
        
        users = user_repo.get_users_by_tipo_cuenta(tipo_cuenta)
        users_dict = [user_repo.to_dict(user) for user in users]
        return jsonify(users_dict), 200
    except Exception as error:
        print(f"Error al obtener usuarios por tipo de cuenta: {error}")
        return jsonify({"msg": "Error al obtener usuarios"}), 500

def get_children_by_tutor_phone(tutor_telefono):
    """Obtener cuentas infantiles vinculadas a un tutor por teléfono"""
    try:
        if not tutor_telefono:
            return jsonify({"msg": "Teléfono de tutor requerido"}), 400
        
        children = user_repo.find_children_by_tutor(tutor_telefono)
        children_dict = [user_repo.to_dict(child) for child in children]
        return jsonify(children_dict), 200
    except Exception as error:
        print(f"Error al obtener hijos del tutor: {error}")
        return jsonify({"msg": "Error al obtener cuentas infantiles"}), 500

def create_child_account(tutor_nombre, tutor_telefono, name, email, password, edad, sexo=''):
    """Crear una cuenta infantil vinculada a un tutor por nombre y teléfono"""
    try:
        # Validar edad
        try:
            edad_int = int(edad)
            if edad_int < 3 or edad_int > 17:
                return jsonify({"msg": "La edad debe ser entre 3 y 17 años"}), 400
        except ValueError:
            return jsonify({"msg": "Edad inválida"}), 400
        
        # Verificar si el email ya existe
        existing_user = user_repo.find_by_email(email)
        if existing_user:
            return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
        
        # Crear usuario infantil
        user_data = {
            'nombre': name,
            'correo': email.lower().strip(),
            'contraseña': password,
            'rol': 2,
            'telefono': '',
            'sexo': sexo,
            'fecha_registro': datetime.utcnow(),
            'tipo_cuenta': 'infantil',
            'edad': edad_int,
            'tutor_nombre': tutor_nombre,
            'tutor_telefono': tutor_telefono
        }
        
        user_id = user_repo.create_user(user_data)
        user = user_repo.find_by_id(user_id)
        user_dict = user_repo.to_dict(user)
        
        return jsonify({
            "msg": "Cuenta infantil creada exitosamente",
            "user": user_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear cuenta infantil: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al crear cuenta infantil"}), 500

# Funciones para direcciones y tarjetas (actualizadas)
def get_user_with_direcciones(user_id):
    """Obtener usuario con todas sus direcciones"""
    return get_single_user(user_id, include_direcciones=True, include_tarjetas=False, include_ninos=False)

def get_user_with_direcciones_y_tarjetas(user_id):
    """Obtener usuario con direcciones y tarjetas (solo personal)"""
    return get_single_user(user_id, include_direcciones=True, include_tarjetas=True, include_ninos=True)

def create_user_with_direccion(name, email, password, role=2, telefono='', sexo='', 
                               direccion_data=None, tipo_cuenta='personal', edad=None):
    """Crear usuario con dirección inicial"""
    return create_user(name, email, password, role, telefono, sexo, 
                      direccion_data, tarjeta_data=None, 
                      tipo_cuenta=tipo_cuenta, edad=edad)

def create_user_with_direccion_y_tarjeta(name, email, password, role=2, telefono='', sexo='', 
                                         direccion_data=None, tarjeta_data=None,
                                         tipo_cuenta='personal', edad=None, 
                                         tutor_nombre=None, tutor_telefono=None):
    """Crear usuario con dirección y tarjeta"""
    return create_user(name, email, password, role, telefono, sexo, 
                      direccion_data, tarjeta_data,
                      tipo_cuenta=tipo_cuenta, edad=edad, 
                      tutor_nombre=tutor_nombre, tutor_telefono=tutor_telefono)

def update_user_with_direccion(user_id, name=None, email=None, password=None, role=None, 
                               telefono=None, sexo=None, direccion_data=None,
                               tipo_cuenta=None, edad=None):
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
        if tipo_cuenta is not None: update_data['tipo_cuenta'] = tipo_cuenta
        if edad is not None: update_data['edad'] = edad
        
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
        user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
        
        return jsonify({
            "msg": "Usuario actualizado exitosamente",
            "user": user_dict
        }), 200
        
    except Exception as error:
        print(f"Error al actualizar usuario con dirección: {error}")
        return jsonify({"msg": "Error al actualizar usuario"}), 500

def update_user_with_direccion_y_tarjeta(user_id, name=None, email=None, password=None, role=None, 
                                         telefono=None, sexo=None, direccion_data=None, tarjeta_data=None,
                                         tipo_cuenta=None, edad=None, tutor_nombre=None, tutor_telefono=None):
    """
    Actualizar usuario, dirección y/o tarjeta
    """
    try:
        update_data = {}
        if name is not None: update_data['nombre'] = name
        if email is not None: update_data['correo'] = email.lower().strip()
        if password is not None: update_data['contraseña'] = password
        if role is not None: update_data['rol'] = role
        if telefono is not None: update_data['telefono'] = telefono
        if sexo is not None: update_data['sexo'] = sexo
        if tipo_cuenta is not None: update_data['tipo_cuenta'] = tipo_cuenta
        if edad is not None: update_data['edad'] = edad
        if tutor_nombre is not None: update_data['tutor_nombre'] = tutor_nombre
        if tutor_telefono is not None: update_data['tutor_telefono'] = tutor_telefono
        
        if update_data:
            user_repo.update_user(user_id, update_data)
        
        # Actualizar dirección si se proporciona
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
        
        # Actualizar tarjeta si se proporciona (solo para cuentas personales)
        if tarjeta_data:
            user = user_repo.find_by_id(user_id)
            user_dict = user_repo.to_dict(user)
            if user_dict.get('tipo_cuenta') != 'personal':
                return jsonify({"msg": "Solo las cuentas personales pueden tener tarjetas"}), 400
            
            from Controllers.targetasController import create_tarjeta, update_tarjeta
            from Models.Targetas import tarjeta_repo
            
            tarjeta_pred = tarjeta_repo.find_predeterminada(user_id)
            
            if tarjeta_pred:
                tarjeta_dict = tarjeta_repo.to_dict(tarjeta_pred)
                update_tarjeta(tarjeta_dict['id'], tarjeta_data)
            else:
                tarjeta_data['predeterminada'] = True
                create_tarjeta(user_id, tarjeta_data)
        
        user = user_repo.find_by_id(user_id)
        user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=True, include_ninos=True)
        
        return jsonify({
            "msg": "Usuario actualizado exitosamente",
            "user": user_dict
        }), 200
        
    except Exception as error:
        print(f"Error al actualizar usuario con dirección y tarjeta: {error}")
        return jsonify({"msg": "Error al actualizar usuario"}), 500