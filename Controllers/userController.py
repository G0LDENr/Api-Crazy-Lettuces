# Controllers/userController.py
from Models.User import UserRepository
from Models.Direccion import Direccion
from flask import jsonify
from flask_jwt_extended import create_access_token
from datetime import datetime
import traceback
import json

# Instancia del repositorio
user_repo = UserRepository()

# ============ FUNCIONES DE VALIDACIÓN Y UTILIDAD ============

# 🔴 PUNTO DE NULOS #1: Validación de existencia de usuario
def _validate_user_exists(user_id):
    """
    VALIDACIÓN DE NULOS - PUNTO #1
    Esta función valida que el user_id no sea nulo y que el usuario exista en la BD
    """
    # ✅ VALIDACIÓN DE NULO #1.1: Verifica si el ID es None o está vacío
    if not user_id:
        return None, jsonify({"msg": "ID de usuario no proporcionado"}), 400
    
    # ✅ VALIDACIÓN DE NULO #1.2: find_by_id puede retornar None si no existe
    user = user_repo.find_by_id(user_id)
    if user is None:
        return None, jsonify({"msg": "Usuario no encontrado"}), 404
    
    return user, None, None


# 🔴 PUNTO DE NULOS #2 Y 🔵 PUNTO DE REPETIDOS #1: Validación de email único
def _validate_email_unique(email, exclude_user_id=None):
    """
    VALIDACIÓN DE NULOS - PUNTO #2
    PREVENCIÓN DE REPETIDOS - PUNTO #1
    Esta función valida que el email no sea nulo y que no esté duplicado en la BD
    """
    # ✅ VALIDACIÓN DE NULO #2.1: Verifica si el email es None
    if not email:
        return None, None
    
    # ✅ VALIDACIÓN DE NULO #2.2: find_by_email puede retornar None
    existing_user = user_repo.find_by_email(email)
    
    # 🔵 PREVENCIÓN DE REPETIDOS #1.1: Si existe usuario con ese email
    if existing_user is not None:
        existing_dict = user_repo.to_dict(existing_user)
        # 🔵 PREVENCIÓN DE REPETIDOS #1.2: Verificar si es el mismo usuario (para actualización)
        if not exclude_user_id or str(existing_dict.get('id')) != str(exclude_user_id):
            # 🔵 PREVENCIÓN DE REPETIDOS #1.3: Email duplicado - Retorna error
            return jsonify({"msg": "El correo electrónico ya está en uso"}), 400
    
    return None, None


# 🔴 PUNTO DE NULOS #3: Validación de campos requeridos
def _validate_required_fields(data, required_fields):
    """
    VALIDACIÓN DE NULOS - PUNTO #3
    Esta función valida que los campos requeridos no sean nulos o vacíos
    """
    # ✅ VALIDACIÓN DE NULO #3.1: Verifica si data es None
    if data is None:
        return jsonify({"msg": "No se proporcionaron datos"}), 400
    
    for field in required_fields:
        value = data.get(field)
        # ✅ VALIDACIÓN DE NULO #3.2: Verifica si el valor es None o string vacío
        if value is None or str(value).strip() == '':
            return jsonify({"msg": f"El campo '{field}' es requerido"}), 400
    
    return None, None


# 🔴 PUNTO DE NULOS #4: Validación de cuenta infantil
def _validate_child_account(tipo_cuenta, edad, tutor_nombre, tutor_telefono):
    """
    VALIDACIÓN DE NULOS - PUNTO #4
    Esta función valida que los datos de cuenta infantil no sean nulos
    """
    if tipo_cuenta != 'infantil':
        return None
    
    # ✅ VALIDACIÓN DE NULO #4.1: Verifica si la edad es None
    if edad is None:
        return jsonify({"msg": "La edad es requerida para cuentas infantiles"}), 400
    
    try:
        edad_int = int(edad)
        if edad_int < 3 or edad_int > 17:
            return jsonify({"msg": "La edad para cuentas infantiles debe ser entre 3 y 17 años"}), 400
    except (ValueError, TypeError):
        # ✅ VALIDACIÓN DE NULO #4.2: Captura error de conversión
        return jsonify({"msg": "Edad inválida"}), 400
    
    # ✅ VALIDACIÓN DE NULO #4.3: Verifica si el nombre del tutor es None o vacío
    if not tutor_nombre or str(tutor_nombre).strip() == '':
        return jsonify({"msg": "El nombre del tutor es requerido para cuentas infantiles"}), 400
    
    # ✅ VALIDACIÓN DE NULO #4.4: Verifica si el teléfono del tutor es None o vacío
    if not tutor_telefono or str(tutor_telefono).strip() == '':
        return jsonify({"msg": "El teléfono del tutor es requerido para cuentas infantiles"}), 400
    
    return None


# 🔴 PUNTO DE NULOS #5: Validación de dirección
def _validate_direccion_data(direccion_data):
    """
    VALIDACIÓN DE NULOS - PUNTO #5
    Esta función valida que los datos de dirección no sean nulos
    """
    # ✅ VALIDACIÓN DE NULO #5.1: Si es None, no hay error (es opcional)
    if direccion_data is None:
        return None, None
    
    # ✅ VALIDACIÓN DE NULO #5.2: Verifica que sea un diccionario
    if not isinstance(direccion_data, dict):
        return jsonify({"msg": "Los datos de dirección deben ser un objeto"}), 400
    
    campos_requeridos = ['calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']
    
    for campo in campos_requeridos:
        valor = direccion_data.get(campo)
        # ✅ VALIDACIÓN DE NULO #5.3: Verifica si el campo es None o vacío
        if valor is None or str(valor).strip() == '':
            return jsonify({"msg": f"Para crear dirección, el campo '{campo}' es requerido"}), 400
    
    cp = str(direccion_data.get('codigo_postal', '')).strip()
    if not cp.isdigit() or len(cp) != 5:
        return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
    
    return None, None


# 🔴 PUNTO DE NULOS #6: Preparar respuesta de usuario
def _prepare_user_response(user):
    """
    VALIDACIÓN DE NULOS - PUNTO #6
    Esta función prepara la respuesta del usuario validando que no sea nulo
    """
    # ✅ VALIDACIÓN DE NULO #6.1: Verifica si user es None
    if user is None:
        return None
    
    return user_repo.to_dict(
        user, 
        include_direcciones=True, 
        include_tarjetas=True, 
        include_ninos=True
    )


def _prepare_user_data(name, email, password, role, telefono, sexo,
                       tipo_cuenta, edad, tutor_nombre, tutor_telefono):
    """
    VALIDACIÓN DE NULOS - PUNTO #7 (múltiples validaciones)
    Esta función prepara los datos del usuario validando nulos
    """
    # ✅ VALIDACIÓN DE NULO #7.1: Verifica nombre
    if not name or str(name).strip() == '':
        raise ValueError("El nombre es requerido")
    
    # ✅ VALIDACIÓN DE NULO #7.2: Verifica email
    if not email or str(email).strip() == '':
        raise ValueError("El email es requerido")
    
    # ✅ VALIDACIÓN DE NULO #7.3: Verifica contraseña
    if not password or str(password).strip() == '':
        raise ValueError("La contraseña es requerida")
    
    user_data = {
        'nombre': str(name).strip(),
        'correo': str(email).lower().strip(),
        'contraseña': str(password),
        'rol': role if role is not None else 2,  # ✅ VALIDACIÓN DE NULO #7.4: Valor por defecto si es None
        'telefono': str(telefono).strip() if telefono else '',  # ✅ VALIDACIÓN DE NULO #7.5: Manejo de None
        'sexo': str(sexo).strip() if sexo else '',  # ✅ VALIDACIÓN DE NULO #7.6: Manejo de None
        'fecha_registro': datetime.utcnow(),
        'tipo_cuenta': tipo_cuenta if tipo_cuenta else 'personal',  # ✅ VALIDACIÓN DE NULO #7.7: Valor por defecto
        'edad': int(edad) if edad is not None else None  # ✅ VALIDACIÓN DE NULO #7.8: Manejo de None
    }
    
    if tipo_cuenta == 'infantil':
        user_data['tutor_nombre'] = str(tutor_nombre).strip() if tutor_nombre else None
        user_data['tutor_telefono'] = str(tutor_telefono).strip() if tutor_telefono else None
    
    return user_data


def _prepare_update_data(existing_user, **kwargs):
    """
    VALIDACIÓN DE NULOS - PUNTO #8
    Esta función prepara los datos de actualización filtrando nulos
    """
    # ✅ VALIDACIÓN DE NULO #8.1: Verifica si existing_user es None
    if existing_user is None:
        return {}
    
    field_mapping = {
        'name': 'nombre',
        'email': 'correo',
        'password': 'contraseña',
        'role': 'rol',
        'telefono': 'telefono',
        'sexo': 'sexo',
        'tipo_cuenta': 'tipo_cuenta',
        'edad': 'edad',
        'tutor_nombre': 'tutor_nombre',
        'tutor_telefono': 'tutor_telefono',
        'restricciones_infantiles': 'restricciones_infantiles'
    }
    
    update_data = {}
    
    for key, value in kwargs.items():
        # ✅ VALIDACIÓN DE NULO #8.2: Saltar valores None
        if value is None:
            continue
            
        if key in field_mapping:
            mapped_key = field_mapping[key]
            
            # Procesar según el tipo de campo
            if mapped_key == 'correo' and value:
                value = str(value).lower().strip()
            elif mapped_key == 'edad' and value is not None:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    continue
            elif mapped_key == 'rol' and value is not None:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    continue
            
            update_data[mapped_key] = value
    
    return update_data


def _create_additional_user_data(user_id, tipo_cuenta, direccion_data, tarjeta_data):
    """
    VALIDACIÓN DE NULOS - PUNTO #9
    Esta función crea datos adicionales validando nulos
    """
    # ✅ VALIDACIÓN DE NULO #9.1: Verifica si user_id es None
    if not user_id:
        return
    
    if tipo_cuenta == 'personal':
        # ✅ VALIDACIÓN DE NULO #9.2: Verifica si direccion_data es dict
        if direccion_data is not None and isinstance(direccion_data, dict):
            _create_direccion(user_id, direccion_data)
        
        # ✅ VALIDACIÓN DE NULO #9.3: Verifica si tarjeta_data es dict
        if tarjeta_data is not None and isinstance(tarjeta_data, dict):
            _create_tarjeta(user_id, tarjeta_data)


def _create_direccion(user_id, direccion_data):
    """
    VALIDACIÓN DE NULOS - PUNTO #10
    Esta función crea dirección validando nulos
    """
    try:
        # ✅ VALIDACIÓN DE NULO #10.1: Verifica parámetros
        if not user_id or not direccion_data:
            return
        
        error, _ = _validate_direccion_data(direccion_data)
        if error:
            print(f"⚠️ Dirección inválida")
            return
        
        direccion_data['predeterminada'] = True
        Direccion.create_direccion(user_id, direccion_data)
        print(f"✅ Dirección creada para usuario {user_id}")
    except Exception as e:
        print(f"⚠️ Error al crear dirección: {e}")


def _create_tarjeta(user_id, tarjeta_data):
    """
    VALIDACIÓN DE NULOS - PUNTO #11
    Esta función crea tarjeta validando nulos
    """
    try:
        # ✅ VALIDACIÓN DE NULO #11.1: Verifica parámetros
        if not user_id or not tarjeta_data:
            return
        
        from Controllers.targetasController import create_tarjeta
        result = create_tarjeta(user_id, tarjeta_data)
        
        if result and len(result) >= 2 and result[1] == 201:
            print(f"✅ Tarjeta creada para usuario {user_id}")
    except Exception as e:
        print(f"⚠️ Error al crear tarjeta: {e}")


def _notify_backup_code(user_id, backup_code):
    """
    VALIDACIÓN DE NULOS - PUNTO #12
    Esta función envía notificación validando nulos
    """
    try:
        # ✅ VALIDACIÓN DE NULO #12.1: Verifica parámetros
        if not user_id or not backup_code:
            return
        
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
    except Exception as e:
        print(f"⚠️ Error al enviar notificación: {e}")


def _handle_error(error_msg, status_code=500, log_msg=None):
    """Manejo centralizado de errores"""
    print(f"❌ {log_msg or error_msg}")
    if log_msg:
        traceback.print_exc()
    return jsonify({"msg": error_msg}), status_code


# ============ AUTENTICACIÓN ============

# 🔴 PUNTO DE NULOS #13: Login con validaciones
def login_user(email, password):
    """
    VALIDACIÓN DE NULOS - PUNTO #13
    INICIO DE SESIÓN - Múltiples validaciones de nulos
    """
    try:
        # ✅ VALIDACIÓN DE NULO #13.1: Verifica credenciales
        if not email or not password:
            return jsonify({"msg": "Email y password son requeridos"}), 400
        
        # ✅ VALIDACIÓN DE NULO #13.2: Verifica strings vacíos
        if str(email).strip() == '' or str(password).strip() == '':
            return jsonify({"msg": "Email y password no pueden estar vacíos"}), 400
        
        print(f"🎯 Intentando login para: {email}")
        
        user = user_repo.find_by_credentials(email, password)
        
        # ✅ VALIDACIÓN DE NULO #13.3: Verifica si encontró el usuario
        if user is None:
            print(f"❌ Falló autenticación para: {email}")
            return jsonify({"msg": "Credenciales inválidas"}), 401
        
        print(f"✅ Usuario autenticado")
        
        user_dict = _prepare_user_response(user)
        # ✅ VALIDACIÓN DE NULO #13.4: Verifica si el diccionario es válido
        if user_dict is None:
            return jsonify({"msg": "Error al procesar datos del usuario"}), 500
        
        user_identity = str(user_dict.get('id'))
        # ✅ VALIDACIÓN DE NULO #13.5: Verifica ID
        if not user_identity:
            return jsonify({"msg": "ID de usuario no válido"}), 500
        
        access_token = create_access_token(identity=user_identity)
        
        return jsonify({
            'access_token': access_token,
            'user': user_dict
        }), 200
        
    except Exception as e:
        return _handle_error("Error al iniciar sesión", 500, f"Error en login: {e}")


# ============ CRUD DE USUARIOS ============

# 🔴 PUNTO DE NULOS #14: Obtener todos los usuarios
def get_all_users():
    """
    VALIDACIÓN DE NULOS - PUNTO #14
    OBTENER TODOS - Validación de lista y elementos nulos
    """
    try:
        users = user_repo.get_all_users()
        
        # ✅ VALIDACIÓN DE NULO #14.1: Verifica si la lista es None
        if users is None:
            return jsonify([]), 200
        
        users_dict = []
        
        for user in users:
            # ✅ VALIDACIÓN DE NULO #14.2: Verifica si el elemento es None
            if user is None:
                continue
                
            user_dict = user_repo.to_dict(user, include_direcciones=True, include_tarjetas=False)
            
            # ✅ VALIDACIÓN DE NULO #14.3: Verifica si el diccionario es None
            if user_dict is None:
                continue
            
            # Cargar dirección predeterminada si no viene
            if not user_dict.get('direccion'):
                try:
                    from config import DB_TYPE
                    
                    user_id = None
                    if DB_TYPE == 'mysql':
                        user_id = getattr(user, 'id', None)
                    else:
                        user_id = str(user.get('_id')) if isinstance(user, dict) else None
                    
                    if user_id:
                        direccion_pred = Direccion.get_direccion_predeterminada(user_id)
                        
                        # ✅ VALIDACIÓN DE NULO #14.4: Verifica si existe dirección
                        if direccion_pred is not None:
                            direccion_dict = Direccion.to_dict(direccion_pred)
                            if direccion_dict and direccion_dict.get('direccion_completa'):
                                user_dict['direccion'] = direccion_dict.get('direccion_completa')
                except Exception as e:
                    print(f"Error cargando dirección: {e}")
            
            users_dict.append(user_dict)
        
        print(f"📊 Total usuarios encontrados: {len(users_dict)}")
        return jsonify(users_dict), 200
        
    except Exception as e:
        return _handle_error("Error al obtener los usuarios", 500, f"Error en get_all_users: {e}")


# 🔴 PUNTO DE NULOS #15: Obtener usuario por ID
def get_single_user(user_id, include_direcciones=True, include_tarjetas=True, include_ninos=True):
    """
    VALIDACIÓN DE NULOS - PUNTO #15
    OBTENER UN USUARIO - Validación de existencia
    """
    try:
        # ✅ VALIDACIÓN DE NULO #15.1: Verifica que el usuario existe
        user, error_response, status = _validate_user_exists(user_id)
        if error_response:
            return error_response, status
        
        user_dict = user_repo.to_dict(
            user, 
            include_direcciones=include_direcciones, 
            include_tarjetas=include_tarjetas,
            include_ninos=include_ninos
        )
        
        # ✅ VALIDACIÓN DE NULO #15.2: Verifica si el diccionario es válido
        if user_dict is None:
            return jsonify({"msg": "Error al procesar los datos del usuario"}), 500
        
        return jsonify(user_dict), 200
        
    except Exception as e:
        return _handle_error("Error al obtener el usuario", 500, f"Error en get_single_user: {e}")


# 🔴 PUNTO DE NULOS #16 Y 🔵 PUNTO DE REPETIDOS #2: Crear usuario
def create_user(name, email, password, role=2, telefono='', sexo='', 
                direccion_data=None, tarjeta_data=None, 
                tipo_cuenta='personal', edad=None, 
                tutor_nombre=None, tutor_telefono=None):
    """
    VALIDACIÓN DE NULOS - PUNTO #16
    PREVENCIÓN DE REPETIDOS - PUNTO #2
    CREAR USUARIO - Validaciones completas de nulos y duplicados
    """
    try:
        # ✅ VALIDACIÓN DE NULO #16.1: Validar rol
        if role is not None:
            if not user_repo.is_valid_role(role):
                return jsonify({"msg": "Rol inválido"}), 400
        
        # 🔵 PREVENCIÓN DE REPETIDOS #2.1: Validar email único
        error_response, status = _validate_email_unique(email)
        if error_response:
            return error_response, status
        
        # ✅ VALIDACIÓN DE NULO #16.2: Validar tipo de cuenta
        if tipo_cuenta not in ['personal', 'infantil']:
            return jsonify({"msg": "Tipo de cuenta inválido. Use 'personal' o 'infantil'"}), 400
        
        # ✅ VALIDACIÓN DE NULO #16.3: Validar datos de cuenta infantil
        validation_error = _validate_child_account(tipo_cuenta, edad, tutor_nombre, tutor_telefono)
        if validation_error:
            return validation_error
        
        # ✅ VALIDACIÓN DE NULO #16.4: Validar dirección si se proporciona
        if direccion_data is not None:
            error_response, _ = _validate_direccion_data(direccion_data)
            if error_response:
                return error_response
        
        # ✅ VALIDACIÓN DE NULO #16.5: Preparar datos del usuario (con manejo de nulos)
        try:
            user_data = _prepare_user_data(
                name, email, password, role, telefono, sexo,
                tipo_cuenta, edad, tutor_nombre, tutor_telefono
            )
        except ValueError as ve:
            return jsonify({"msg": str(ve)}), 400
        
        print(f"📝 Creando usuario: {user_data.get('correo')}")
        
        user_id = user_repo.create_user(user_data)
        
        # ✅ VALIDACIÓN DE NULO #16.6: Verifica si se creó el usuario
        if not user_id:
            return jsonify({"msg": "Error al crear el usuario en la base de datos"}), 500
        
        print(f"✅ Usuario creado con ID: {user_id}")
        
        # Crear elementos adicionales
        _create_additional_user_data(user_id, tipo_cuenta, direccion_data, tarjeta_data)
        
        user = user_repo.find_by_id(user_id)
        # ✅ VALIDACIÓN DE NULO #16.7: Verifica si se puede recuperar el usuario
        if user is None:
            return jsonify({"msg": "Usuario creado pero no se pudo recuperar"}), 500
        
        user_dict = _prepare_user_response(user)
        
        return jsonify({
            "msg": "Usuario creado exitosamente",
            "user": user_dict
        }), 201
        
    except Exception as e:
        return _handle_error("Error al crear el usuario", 500, f"Error en create_user: {e}")


# 🔴 PUNTO DE NULOS #17 Y 🔵 PUNTO DE REPETIDOS #3: Actualizar usuario
def update_user(user_id, **kwargs):
    """
    VALIDACIÓN DE NULOS - PUNTO #17
    PREVENCIÓN DE REPETIDOS - PUNTO #3
    ACTUALIZAR USUARIO - Validaciones de nulos y email duplicado
    """
    try:
        # ✅ VALIDACIÓN DE NULO #17.1: Verificar que el usuario existe
        existing_user, error_response, status = _validate_user_exists(user_id)
        if error_response:
            return error_response, status
        
        # ✅ VALIDACIÓN DE NULO #17.2: Preparar datos de actualización (filtra nulos)
        update_data = _prepare_update_data(existing_user, **kwargs)
        
        # ✅ VALIDACIÓN DE NULO #17.3: Verificar si hay datos para actualizar
        if not update_data:
            return jsonify({"msg": "No se proporcionaron datos válidos para actualizar"}), 400
        
        # 🔵 PREVENCIÓN DE REPETIDOS #3.1: Validar email si viene en la actualización
        if 'correo' in update_data:
            error_response, status = _validate_email_unique(update_data['correo'], user_id)
            if error_response:
                return error_response, status
        
        # ✅ VALIDACIÓN DE NULO #17.4: Validar rol si viene
        if 'rol' in update_data:
            if not user_repo.is_valid_role(update_data['rol']):
                return jsonify({"msg": "Rol inválido"}), 400
        
        # ✅ VALIDACIÓN DE NULO #17.5: Validar tipo de cuenta si viene
        if 'tipo_cuenta' in update_data:
            if update_data['tipo_cuenta'] not in ['personal', 'infantil']:
                return jsonify({"msg": "Tipo de cuenta inválido"}), 400
        
        # Actualizar usuario
        if user_repo.update_user(user_id, update_data):
            # Si el rol cambió a administrador, generar código de respaldo
            if 'rol' in update_data and update_data['rol'] == 1:
                existing_code = user_repo.has_valid_backup_code(user_id)
                if not existing_code:
                    backup_code = user_repo.generate_backup_code(user_id)
                    if backup_code:
                        _notify_backup_code(user_id, backup_code)
            
            updated_user = user_repo.find_by_id(user_id)
            # ✅ VALIDACIÓN DE NULO #17.6: Verificar que se puede recuperar
            if updated_user is None:
                return jsonify({"msg": "Usuario actualizado pero no se pudo recuperar"}), 500
            
            user_dict = _prepare_user_response(updated_user)
            
            return jsonify({
                "msg": "Usuario actualizado exitosamente",
                "user": user_dict
            }), 200
        else:
            return jsonify({"msg": "No se pudieron actualizar los datos"}), 500
            
    except Exception as e:
        return _handle_error("Error al actualizar el usuario", 500, f"Error en update_user: {e}")


# 🔴 PUNTO DE NULOS #18: Eliminar usuario
def delete_user(user_id):
    """
    VALIDACIÓN DE NULOS - PUNTO #18
    ELIMINAR USUARIO - Validación de existencia y dependencias
    """
    try:
        # ✅ VALIDACIÓN DE NULO #18.1: Verificar que el usuario existe
        user, error_response, status = _validate_user_exists(user_id)
        if error_response:
            return error_response, status
        
        user_dict = user_repo.to_dict(user)
        
        # ✅ VALIDACIÓN DE NULO #18.2: Verificar si tiene cuentas infantiles
        if user_dict and user_dict.get('telefono'):
            ninos = user_repo.find_children_by_tutor(user_dict['telefono'])
            
            # ✅ VALIDACIÓN DE NULO #18.3: Verificar si tiene hijos
            if ninos and len(ninos) > 0:
                return jsonify({
                    "msg": "No se puede eliminar el usuario porque tiene cuentas infantiles asociadas",
                    "ninos_count": len(ninos)
                }), 400
        
        if user_repo.delete_user(user_id):
            print(f"✅ Usuario {user_id} eliminado exitosamente")
            return jsonify({"msg": "Usuario eliminado exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar el usuario"}), 500
            
    except Exception as e:
        return _handle_error("Error interno del servidor", 500, f"Error en delete_user: {e}")


# ============ FUNCIONES PÚBLICAS ADICIONALES ============

def get_user_profile(user_id):
    """Obtener perfil de usuario completo"""
    return get_single_user(user_id, include_direcciones=True, include_tarjetas=True, include_ninos=True)


# 🔴 PUNTO DE NULOS #19: Buscar usuarios
def search_users(query):
    """
    VALIDACIÓN DE NULOS - PUNTO #19
    BUSCAR USUARIOS - Validación de query y resultados
    """
    try:
        # ✅ VALIDACIÓN DE NULO #19.1: Verificar query
        if not query or str(query).strip() == '':
            return jsonify({"msg": "El término de búsqueda es requerido"}), 400
        
        users = user_repo.search_users(query)
        
        # ✅ VALIDACIÓN DE NULO #19.2: Verificar resultados
        if users is None:
            return jsonify([]), 200
        
        users_dict = []
        for user in users:
            # ✅ VALIDACIÓN DE NULO #19.3: Verificar cada usuario
            if user is not None:
                user_dict = user_repo.to_dict(user, include_direcciones=False, include_tarjetas=False)
                # ✅ VALIDACIÓN DE NULO #19.4: Verificar diccionario
                if user_dict:
                    users_dict.append(user_dict)
        
        return jsonify(users_dict), 200
    except Exception as e:
        return _handle_error("Error al buscar usuarios", 500, f"Error en search_users: {e}")


# 🔴 PUNTO DE NULOS #20: Cambiar contraseña
def change_password(user_id, current_password, new_password):
    """
    VALIDACIÓN DE NULOS - PUNTO #20
    CAMBIAR CONTRASEÑA - Validación de parámetros
    """
    try:
        # ✅ VALIDACIÓN DE NULO #20.1: Verificar parámetros
        if not current_password or not new_password:
            return jsonify({"msg": "Contraseña actual y nueva son requeridas"}), 400
        
        # ✅ VALIDACIÓN DE NULO #20.2: Validar longitud
        if len(new_password) < 6:
            return jsonify({"msg": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
        
        # ✅ VALIDACIÓN DE NULO #20.3: Verificar que el usuario existe
        user, error_response, status = _validate_user_exists(user_id)
        if error_response:
            return error_response, status
        
        user_dict = user_repo.to_dict(user)
        # ✅ VALIDACIÓN DE NULO #20.4: Verificar diccionario
        if user_dict is None:
            return jsonify({"msg": "Error al obtener datos del usuario"}), 500
        
        # ✅ VALIDACIÓN DE NULO #20.5: Verificar contraseña actual
        if not user_repo.find_by_credentials(user_dict.get('correo'), current_password):
            return jsonify({"msg": "Contraseña actual incorrecta"}), 401
        
        if user_repo.update_user(user_id, {'contraseña': new_password}):
            return jsonify({"msg": "Contraseña actualizada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al actualizar la contraseña"}), 500
            
    except Exception as e:
        return _handle_error("Error al cambiar contraseña", 500, f"Error en change_password: {e}")


def get_users_by_role(role_id):
    """
    VALIDACIÓN DE NULOS - PUNTO #21
    OBTENER POR ROL - Validación de rol
    """
    try:
        # ✅ VALIDACIÓN DE NULO #21.1: Verificar role_id
        if role_id is None:
            return jsonify({"msg": "ID de rol es requerido"}), 400
        
        if not user_repo.is_valid_role(role_id):
            return jsonify({"msg": "Rol inválido"}), 400
        
        users = user_repo.get_users_by_role(role_id)
        
        # ✅ VALIDACIÓN DE NULO #21.2: Verificar resultados
        if users is None:
            return jsonify([]), 200
        
        users_dict = []
        for user in users:
            if user is not None:
                user_dict = user_repo.to_dict(user, include_direcciones=False, include_tarjetas=False)
                if user_dict:
                    users_dict.append(user_dict)
        
        return jsonify(users_dict), 200
    except Exception as e:
        return _handle_error("Error al obtener usuarios", 500, f"Error en get_users_by_role: {e}")


def get_available_roles():
    """Obtener roles disponibles"""
    try:
        from config import ROLES
        if ROLES is None:
            return jsonify({"msg": "No hay roles disponibles"}), 404
        return jsonify(ROLES), 200
    except Exception as e:
        return _handle_error("Error al obtener los roles", 500, f"Error en get_available_roles: {e}")


# ============ FUNCIONES PARA CUENTAS INFANTILES ============

def get_users_by_tipo_cuenta(tipo_cuenta):
    """
    VALIDACIÓN DE NULOS - PUNTO #22
    OBTENER POR TIPO - Validación de tipo
    """
    try:
        # ✅ VALIDACIÓN DE NULO #22.1: Verificar tipo_cuenta
        if not tipo_cuenta:
            return jsonify({"msg": "Tipo de cuenta es requerido"}), 400
        
        if tipo_cuenta not in ['personal', 'infantil']:
            return jsonify({"msg": "Tipo de cuenta inválido"}), 400
        
        users = user_repo.get_users_by_tipo_cuenta(tipo_cuenta)
        
        # ✅ VALIDACIÓN DE NULO #22.2: Verificar resultados
        if users is None:
            return jsonify([]), 200
        
        users_dict = []
        for user in users:
            if user is not None:
                user_dict = user_repo.to_dict(user)
                if user_dict:
                    users_dict.append(user_dict)
        
        return jsonify(users_dict), 200
    except Exception as e:
        return _handle_error("Error al obtener usuarios", 500, f"Error en get_users_by_tipo_cuenta: {e}")


# 🔴 PUNTO DE NULOS #23: Obtener hijos por teléfono
def get_children_by_tutor_phone(tutor_telefono):
    """
    VALIDACIÓN DE NULOS - PUNTO #23
    OBTENER HIJOS - Validación de teléfono
    """
    try:
        # ✅ VALIDACIÓN DE NULO #23.1: Verificar teléfono
        if not tutor_telefono or str(tutor_telefono).strip() == '':
            return jsonify({"msg": "Teléfono de tutor requerido"}), 400
        
        children = user_repo.find_children_by_tutor(tutor_telefono)
        
        # ✅ VALIDACIÓN DE NULO #23.2: Verificar resultados
        if children is None:
            return jsonify([]), 200
        
        children_dict = []
        for child in children:
            # ✅ VALIDACIÓN DE NULO #23.3: Verificar cada hijo
            if child is not None:
                child_dict = user_repo.to_dict(child)
                if child_dict:
                    children_dict.append(child_dict)
        
        return jsonify(children_dict), 200
    except Exception as e:
        return _handle_error("Error al obtener cuentas infantiles", 500, f"Error en get_children_by_tutor_phone: {e}")


# 🔵 PUNTO DE REPETIDOS #4: Crear cuenta infantil
def create_child_account(tutor_nombre, tutor_telefono, name, email, password, edad, sexo=''):
    """
    PREVENCIÓN DE REPETIDOS - PUNTO #4
    CREAR CUENTA INFANTIL - Reutiliza create_user que ya tiene validaciones
    """
    # 🔵 PREVENCIÓN DE REPETIDOS #4.1: Reutiliza create_user con todas las validaciones
    return create_user(
        name=name,
        email=email,
        password=password,
        role=2,
        telefono='',
        sexo=sexo,
        tipo_cuenta='infantil',
        edad=edad,
        tutor_nombre=tutor_nombre,
        tutor_telefono=tutor_telefono
    )


# ============ FUNCIONES PARA REDES SOCIALES ============

# 🔴 PUNTO DE NULOS #24 Y 🔵 PUNTO DE REPETIDOS #5: Usuario social
def create_social_user(name, email, social_id, social_provider, tipo_cuenta='personal', edad=None):
    """
    VALIDACIÓN DE NULOS - PUNTO #24
    PREVENCIÓN DE REPETIDOS - PUNTO #5
    USUARIO SOCIAL - Validación de nulos y prevención de duplicados
    """
    try:
        # ✅ VALIDACIÓN DE NULO #24.1: Validar datos requeridos
        if not name or not email or not social_id or not social_provider:
            return jsonify({"msg": "Datos incompletos para crear usuario social"}), 400
        
        # ✅ VALIDACIÓN DE NULO #24.2: Validar tipo de cuenta
        if tipo_cuenta not in ['personal', 'infantil']:
            return jsonify({"msg": "Tipo de cuenta inválido"}), 400
        
        # 🔵 PREVENCIÓN DE REPETIDOS #5.1: Verificar si ya existe
        existing_user = user_repo.find_by_email(email)
        
        # ✅ VALIDACIÓN DE NULO #24.3: Si existe, no crear duplicado
        if existing_user is not None:
            user_dict = _prepare_user_response(existing_user)
            # ✅ VALIDACIÓN DE NULO #24.4: Verificar diccionario
            if user_dict is None:
                return jsonify({"msg": "Error al procesar datos del usuario"}), 500
            
            access_token = create_access_token(identity=str(user_dict.get('id')))
            # 🔵 PREVENCIÓN DE REPETIDOS #5.2: Retorna el usuario existente en lugar de crear duplicado
            return jsonify({
                'access_token': access_token,
                'user': user_dict
            }), 200
        
        # Si no existe, crear nuevo
        return create_user(
            name=name,
            email=email,
            password=social_id,
            role=2,
            tipo_cuenta=tipo_cuenta,
            edad=edad
        )
        
    except Exception as e:
        return _handle_error("Error al crear usuario desde red social", 500, f"Error en create_social_user: {e}")


# ============ FUNCIONES COMBINADAS PARA DIRECCIONES Y TARJETAS ============

def get_user_with_direcciones(user_id):
    """Obtener usuario con todas sus direcciones"""
    return get_single_user(user_id, include_direcciones=True, include_tarjetas=False, include_ninos=False)


def get_user_with_direcciones_y_tarjetas(user_id):
    """Obtener usuario con direcciones y tarjetas"""
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


# 🔴 PUNTO DE NULOS #25: Actualizar usuario con dirección
def update_user_with_direccion(user_id, direccion_data=None, **kwargs):
    """
    VALIDACIÓN DE NULOS - PUNTO #25
    ACTUALIZAR CON DIRECCIÓN - Validaciones completas
    """
    try:
        # ✅ VALIDACIÓN DE NULO #25.1: Validar que el usuario existe
        user, error_response, status = _validate_user_exists(user_id)
        if error_response:
            return error_response, status
        
        # Actualizar usuario primero
        if kwargs:
            result = update_user(user_id, **kwargs)
            if result[1] != 200:
                return result
        
        # ✅ VALIDACIÓN DE NULO #25.2: Actualizar dirección si se proporciona
        if direccion_data is not None:
            # ✅ VALIDACIÓN DE NULO #25.3: Validar dirección
            error_response, _ = _validate_direccion_data(direccion_data)
            if error_response:
                return error_response
            
            from Models.Direccion import Direccion
            direccion_predeterminada = Direccion.get_direccion_predeterminada(user_id)
            
            if direccion_predeterminada:
                Direccion.update_direccion(direccion_predeterminada.id, direccion_data)
            else:
                direccion_data['predeterminada'] = True
                Direccion.create_direccion(user_id, direccion_data)
        
        updated_user = user_repo.find_by_id(user_id)
        # ✅ VALIDACIÓN DE NULO #25.4: Verificar que se puede recuperar
        if updated_user is None:
            return jsonify({"msg": "Usuario actualizado pero no se pudo recuperar"}), 500
        
        user_dict = _prepare_user_response(updated_user)
        
        return jsonify({
            "msg": "Usuario actualizado exitosamente",
            "user": user_dict
        }), 200
        
    except Exception as e:
        return _handle_error("Error al actualizar usuario", 500, f"Error en update_user_with_direccion: {e}")


# 🔴 PUNTO DE NULOS #26: Actualizar usuario con dirección y tarjeta
def update_user_with_direccion_y_tarjeta(user_id, direccion_data=None, tarjeta_data=None, **kwargs):
    """
    VALIDACIÓN DE NULOS - PUNTO #26
    ACTUALIZAR CON DIRECCIÓN Y TARJETA - Validaciones completas
    """
    try:
        # ✅ VALIDACIÓN DE NULO #26.1: Validar que el usuario existe
        user, error_response, status = _validate_user_exists(user_id)
        if error_response:
            return error_response, status
        
        # Actualizar usuario primero
        if kwargs:
            result = update_user(user_id, **kwargs)
            if result[1] != 200:
                return result
        
        # ✅ VALIDACIÓN DE NULO #26.2: Actualizar dirección si se proporciona
        if direccion_data is not None:
            error_response, _ = _validate_direccion_data(direccion_data)
            if error_response:
                return error_response
            
            from Models.Direccion import Direccion
            direccion_predeterminada = Direccion.get_direccion_predeterminada(user_id)
            
            if direccion_predeterminada:
                Direccion.update_direccion(direccion_predeterminada.id, direccion_data)
            else:
                direccion_data['predeterminada'] = True
                Direccion.create_direccion(user_id, direccion_data)
        
        # ✅ VALIDACIÓN DE NULO #26.3: Actualizar tarjeta si se proporciona
        if tarjeta_data is not None:
            user_dict = user_repo.to_dict(user)
            
            # ✅ VALIDACIÓN DE NULO #26.4: Verificar tipo de cuenta
            if user_dict and user_dict.get('tipo_cuenta') != 'personal':
                return jsonify({"msg": "Solo las cuentas personales pueden tener tarjetas"}), 400
            
            from Controllers.targetasController import create_tarjeta, update_tarjeta
            from Models.Targetas import tarjeta_repo
            
            tarjeta_pred = tarjeta_repo.find_predeterminada(user_id)
            
            if tarjeta_pred:
                tarjeta_dict = tarjeta_repo.to_dict(tarjeta_pred)
                if tarjeta_dict:
                    update_tarjeta(tarjeta_dict.get('id'), tarjeta_data)
            else:
                tarjeta_data['predeterminada'] = True
                create_tarjeta(user_id, tarjeta_data)
        
        updated_user = user_repo.find_by_id(user_id)
        # ✅ VALIDACIÓN DE NULO #26.5: Verificar que se puede recuperar
        if updated_user is None:
            return jsonify({"msg": "Usuario actualizado pero no se pudo recuperar"}), 500
        
        user_dict = _prepare_user_response(updated_user)
        
        return jsonify({
            "msg": "Usuario actualizado exitosamente",
            "user": user_dict
        }), 200
        
    except Exception as e:
        return _handle_error("Error al actualizar usuario", 500, f"Error en update_user_with_direccion_y_tarjeta: {e}")