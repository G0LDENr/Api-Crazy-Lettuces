from flask import Blueprint, request, jsonify
from Controllers.userController import (
    get_all_users,
    create_user,
    login_user,
    delete_user,
    update_user,
    get_single_user,
    get_user_profile,
    create_social_user,
    search_users,
    change_password,
    get_users_by_role,
    get_available_roles,
    get_user_with_direcciones,
    create_user_with_direccion,
    update_user_with_direccion,
    get_user_with_direcciones_y_tarjetas,
    create_user_with_direccion_y_tarjeta,
    update_user_with_direccion_y_tarjeta,
    get_users_by_tipo_cuenta,
    get_children_by_tutor_phone,
    create_child_account
)
from flask_jwt_extended import jwt_required, get_jwt_identity

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/', methods=['GET'])
@jwt_required()
def index():
    """
    Obtener todos los usuarios
    ---
    tags:
      - Usuarios
    responses:
      200:
        description: Lista de usuarios
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nombre:
                type: string
              correo:
                type: string
              rol:
                type: integer
              rol_texto:
                type: string
              telefono:
                type: string
              sexo:
                type: string
              fecha_registro:
                type: string
              tipo_cuenta:
                type: string
              edad:
                type: integer
      500:
        description: Error al obtener los usuarios
    """
    return get_all_users()

@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users_route():
    """
    Buscar usuarios por nombre o email
    ---
    tags:
      - Usuarios
    parameters:
      - name: query
        in: query
        type: string
        required: false
    responses:
      200:
        description: Usuarios encontrados
    """
    query = request.args.get('query', '')
    return search_users(query)

@user_bp.route('/roles', methods=['GET'])
def get_roles_route():
    """
    Obtener roles disponibles
    ---
    tags:
      - Usuarios
    responses:
      200:
        description: Diccionario de roles
    """
    return get_available_roles()

@user_bp.route('/roles/<int:role_id>', methods=['GET'])
@jwt_required()
def get_users_by_role_route(role_id):
    """
    Obtener usuarios por rol
    ---
    tags:
      - Usuarios
    parameters:
      - name: role_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Usuarios del rol especificado
    """
    return get_users_by_role(role_id)

# ============ RUTAS PARA TIPOS DE CUENTA ============

@user_bp.route('/tipo/<string:tipo_cuenta>', methods=['GET'])
@jwt_required()
def get_users_by_tipo_cuenta_route(tipo_cuenta):
    """
    Obtener usuarios por tipo de cuenta (personal/infantil)
    ---
    tags:
      - Usuarios
      - Cuentas Infantiles
    parameters:
      - name: tipo_cuenta
        in: path
        type: string
        required: true
        enum: ['personal', 'infantil']
    responses:
      200:
        description: Usuarios del tipo de cuenta especificado
      400:
        description: Tipo de cuenta inválido
    """
    return get_users_by_tipo_cuenta(tipo_cuenta)

@user_bp.route('/tutor/<string:tutor_telefono>/children', methods=['GET'])
@jwt_required()
def get_children_by_tutor_phone_route(tutor_telefono):
    """
    Obtener cuentas infantiles vinculadas a un tutor por teléfono
    ---
    tags:
      - Usuarios
      - Cuentas Infantiles
    parameters:
      - name: tutor_telefono
        in: path
        type: string
        required: true
    responses:
      200:
        description: Lista de cuentas infantiles del tutor
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nombre:
                type: string
              correo:
                type: string
              edad:
                type: integer
              sexo:
                type: string
              tutor_nombre:
                type: string
              tutor_telefono:
                type: string
      404:
        description: No se encontraron cuentas
    """
    return get_children_by_tutor_phone(tutor_telefono)

@user_bp.route('/children/create', methods=['POST'])
def create_child_account_route():
    """
    Crear una cuenta infantil (el tutor se identifica por nombre y teléfono)
    ---
    tags:
      - Usuarios
      - Cuentas Infantiles
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - tutor_nombre
            - tutor_telefono
            - name
            - email
            - password
            - edad
          properties:
            tutor_nombre:
              type: string
              example: "Juan Pérez"
              description: "Nombre completo del tutor"
            tutor_telefono:
              type: string
              example: "5512345678"
              description: "Teléfono del tutor"
            name:
              type: string
              example: "Juanito Pérez"
              description: "Nombre del niño"
            email:
              type: string
              example: "juanito@gmail.com"
            password:
              type: string
              example: "contraseña123"
            edad:
              type: integer
              example: 10
            sexo:
              type: string
              example: "Masculino"
    responses:
      201:
        description: Cuenta infantil creada exitosamente
      400:
        description: Datos inválidos
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
        tutor_nombre = data.get('tutor_nombre')
        tutor_telefono = data.get('tutor_telefono')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        edad = data.get('edad')
        sexo = data.get('sexo', '')
        
        if not all([tutor_nombre, tutor_telefono, name, email, password, edad]):
            return jsonify({'msg': 'Faltan datos requeridos'}), 400
        
        return create_child_account(tutor_nombre, tutor_telefono, name, email, password, edad, sexo)
        
    except Exception as e:
        print(f"Error en create_child_account_route: {e}")
        return jsonify({"msg": "Error al crear cuenta infantil"}), 500

# ============ RUTAS EXISTENTES ACTUALIZADAS ============

# CAMBIO IMPORTANTE: Cambiar <int:user_id> a <string:user_id>
@user_bp.route('/<string:user_id>/with-direcciones', methods=['GET'])
@jwt_required()
def get_user_with_direcciones_route(user_id):
    """
    Obtener usuario con todas sus direcciones
    ---
    tags:
      - Usuarios
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Usuario con direcciones
        schema:
          type: object
          properties:
            id:
              type: integer
            nombre:
              type: string
            correo:
              type: string
            rol:
              type: integer
            rol_texto:
              type: string
            telefono:
              type: string
            sexo:
              type: string
            fecha_registro:
              type: string
            tipo_cuenta:
              type: string
            edad:
              type: integer
            direcciones:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  calle:
                    type: string
                  numero_exterior:
                    type: string
                  colonia:
                    type: string
                  ciudad:
                    type: string
                  estado:
                    type: string
                  codigo_postal:
                    type: string
                  tipo:
                    type: string
                  predeterminada:
                    type: boolean
            total_direcciones:
              type: integer
            direccion_predeterminada:
              type: object
      404:
        description: Usuario no encontrado
    """
    return get_user_with_direcciones(user_id)

# CAMBIO IMPORTANTE: Cambiar <int:user_id> a <string:user_id>
@user_bp.route('/<string:user_id>/with-all', methods=['GET'])
@jwt_required()
def get_user_with_all_route(user_id):
    """
    Obtener usuario con todas sus direcciones y tarjetas
    ---
    tags:
      - Usuarios
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Usuario con direcciones y tarjetas
        schema:
          type: object
          properties:
            id:
              type: integer
            nombre:
              type: string
            correo:
              type: string
            rol:
              type: integer
            rol_texto:
              type: string
            telefono:
              type: string
            sexo:
              type: string
            fecha_registro:
              type: string
            tipo_cuenta:
              type: string
            edad:
              type: integer
            direcciones:
              type: array
              items:
                type: object
            total_direcciones:
              type: integer
            direccion_predeterminada:
              type: object
            tarjetas:
              type: array
              items:
                type: object
            total_tarjetas:
              type: integer
            tarjeta_predeterminada:
              type: object
      404:
        description: Usuario no encontrado
    """
    return get_user_with_direcciones_y_tarjetas(user_id)

# Ruta para obtener usuario actual desde token JWT
@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtener información del usuario actual (desde token JWT)
    ---
    tags:
      - Usuarios
    responses:
      200:
        description: Información del usuario autenticado
        schema:
          type: object
          properties:
            id:
              type: integer
            nombre:
              type: string
            correo:
              type: string
            rol:
              type: integer
            rol_texto:
              type: string
            telefono:
              type: string
            sexo:
              type: string
            fecha_registro:
              type: string
            tipo_cuenta:
              type: string
            edad:
              type: integer
            tutor_nombre:
              type: string
            tutor_telefono:
              type: string
            direcciones:
              type: array
              items:
                type: object
            total_direcciones:
              type: integer
            direccion_predeterminada:
              type: object
            tarjetas:
              type: array
              items:
                type: object
            total_tarjetas:
              type: integer
            tarjeta_predeterminada:
              type: object
            ninos:
              type: array
              items:
                type: object
            total_ninos:
              type: integer
      401:
        description: No autorizado
    """
    try:
        current_user_id = get_jwt_identity()
        return get_user_with_direcciones_y_tarjetas(current_user_id)
    except Exception as e:
        print(f"Error en /me endpoint: {e}")
        return jsonify({"msg": "Error al obtener datos del usuario"}), 500

# CAMBIO IMPORTANTE: Cambiar <int:user_id> a <string:user_id>
@user_bp.route('/<string:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Obtener un usuario por ID
    ---
    tags:
      - Usuarios
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Usuario encontrado
      404:
        description: Usuario no encontrado
    """
    return get_single_user(user_id, include_direcciones=True, include_tarjetas=True, include_ninos=True)

# CAMBIO IMPORTANTE: Cambiar <int:user_id> a <string:user_id>
@user_bp.route('/profile/<string:user_id>', methods=['GET'])
@jwt_required()
def get_profile_route(user_id):
    """
    Obtener perfil de usuario
    ---
    tags:
      - Usuarios
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Perfil del usuario
      404:
        description: Usuario no encontrado
    """
    return get_user_profile(user_id)

# Ruta para actualizar usuario actual
@user_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_current_user():
    """
    Actualizar perfil del usuario actual (desde token JWT)
    ---
    tags:
      - Usuarios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: Juan Pérez
            telefono:
              type: string
              example: "5512345678"
            sexo:
              type: string
              example: "Masculino"
            correo:
              type: string
              example: juan@ejemplo.com
            tipo_cuenta:
              type: string
              enum: ['personal', 'infantil']
              example: personal
            edad:
              type: integer
              example: 30
            direccion:
              type: object
              properties:
                calle:
                  type: string
                  example: "Av. Principal"
                numero_exterior:
                  type: string
                  example: "123"
                colonia:
                  type: string
                  example: "Centro"
                ciudad:
                  type: string
                  example: "CDMX"
                estado:
                  type: string
                  example: "Ciudad de México"
                codigo_postal:
                  type: string
                  example: "01000"
                referencias:
                  type: string
                  example: "Entre calles"
                tipo:
                  type: string
                  example: "casa"
            tarjeta:
              type: object
              description: Tarjeta de crédito opcional
              properties:
                nombre_titular:
                  type: string
                  example: "Juan Pérez"
                numero_tarjeta:
                  type: string
                  example: "4111111111111111"
                mes_expiracion:
                  type: string
                  example: "12"
                anio_expiracion:
                  type: string
                  example: "2025"
                predeterminada:
                  type: boolean
                  example: true
    responses:
      200:
        description: Perfil actualizado exitosamente
      400:
        description: Datos inválidos
      401:
        description: No autorizado
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
        user_data = {}
        direccion_data = data.get('direccion')
        tarjeta_data = data.get('tarjeta')
        
        if 'nombre' in data:
            user_data['nombre'] = data.get('nombre')
        if 'correo' in data:
            user_data['correo'] = data.get('correo')
        if 'telefono' in data:
            user_data['telefono'] = data.get('telefono')
        if 'sexo' in data:
            user_data['sexo'] = data.get('sexo')
        if 'tipo_cuenta' in data:
            user_data['tipo_cuenta'] = data.get('tipo_cuenta')
        if 'edad' in data:
            user_data['edad'] = data.get('edad')
        
        if direccion_data or tarjeta_data:
            return update_user_with_direccion_y_tarjeta(
                user_id=current_user_id,
                name=user_data.get('nombre'),
                email=user_data.get('correo'),
                telefono=user_data.get('telefono'),
                sexo=user_data.get('sexo'),
                tipo_cuenta=user_data.get('tipo_cuenta'),
                edad=user_data.get('edad'),
                password=None,
                role=None,
                direccion_data=direccion_data,
                tarjeta_data=tarjeta_data
            )
        else:
            return update_user(
                user_id=current_user_id,
                name=user_data.get('nombre'),
                email=user_data.get('correo'),
                telefono=user_data.get('telefono'),
                sexo=user_data.get('sexo'),
                tipo_cuenta=user_data.get('tipo_cuenta'),
                edad=user_data.get('edad'),
                password=None,
                role=None
            )
        
    except Exception as e:
        print(f"Error en /update endpoint: {e}")
        return jsonify({"msg": "Error al actualizar el perfil"}), 500

@user_bp.route('/add_user', methods=['POST'])
def add_user():
    """
    Crear un nuevo usuario (CON TIPO DE CUENTA, DIRECCIÓN Y TARJETA OPCIONAL)
    ---
    tags:
      - Usuarios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - name
            - password
          properties:
            email:
              type: string
              example: carlos@gmail.com
            name:
              type: string
              example: Juan Carlos
            password:
              type: string
              example: contraseña123
            role:
              type: integer
              description: 1=Admin, 2=Usuario
              default: 2
            telefono:
              type: string
              example: "7294030702"
            sexo:
              type: string
              example: "M"
            tipo_cuenta:
              type: string
              enum: ['personal', 'infantil']
              default: 'personal'
              example: personal
            edad:
              type: integer
              description: Requerido si tipo_cuenta es infantil
              example: 10
            tutor_nombre:
              type: string
              description: Nombre del tutor (requerido si tipo_cuenta es infantil)
              example: "Juan Pérez"
            tutor_telefono:
              type: string
              description: Teléfono del tutor (requerido si tipo_cuenta es infantil)
              example: "5512345678"
            direccion:
              type: object
              description: Dirección opcional (solo para cuentas personales)
              properties:
                calle:
                  type: string
                  example: "Av. Principal"
                numero_exterior:
                  type: string
                  example: "123"
                colonia:
                  type: string
                  example: "Centro"
                ciudad:
                  type: string
                  example: "CDMX"
                estado:
                  type: string
                  example: "Ciudad de México"
                codigo_postal:
                  type: string
                  example: "01000"
                referencias:
                  type: string
                  example: "Entre calles"
                tipo:
                  type: string
                  example: "casa"
            tarjeta:
              type: object
              description: Tarjeta de crédito opcional (solo para cuentas personales)
              properties:
                nombre_titular:
                  type: string
                  example: "Juan Carlos"
                numero_tarjeta:
                  type: string
                  example: "4111111111111111"
                mes_expiracion:
                  type: string
                  example: "12"
                anio_expiracion:
                  type: string
                  example: "2025"
                predeterminada:
                  type: boolean
                  example: true
    responses:
      201:
        description: Usuario creado exitosamente
      400:
        description: Error al crear el usuario
      500:
        description: Error interno del servidor
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
      
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    role = data.get('role', 2)
    telefono = data.get('telefono', '')
    sexo = data.get('sexo', '')
    tipo_cuenta = data.get('tipo_cuenta', 'personal')
    edad = data.get('edad')
    tutor_nombre = data.get('tutor_nombre')
    tutor_telefono = data.get('tutor_telefono')
    direccion_data = data.get('direccion')
    tarjeta_data = data.get('tarjeta')

    if not email or not name or not password:
        return jsonify({'msg': 'Faltan datos requeridos'}), 400
    
    return create_user_with_direccion_y_tarjeta(
        name, email, password, role, telefono, sexo, 
        direccion_data, tarjeta_data, tipo_cuenta, edad, 
        tutor_nombre, tutor_telefono
    )

@user_bp.route('/social', methods=['POST'])
def create_social_user_route():
    """
    Crear usuario desde red social
    ---
    tags:
      - Autenticación
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - social_id
            - social_provider
          properties:
            name:
              type: string
            email:
              type: string
            social_id:
              type: string
            social_provider:
              type: string
            tipo_cuenta:
              type: string
              enum: ['personal', 'infantil']
              default: 'personal'
            edad:
              type: integer
    responses:
      201:
        description: Usuario social creado
      400:
        description: Datos incompletos
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
    name = data.get('name')
    email = data.get('email')
    social_id = data.get('social_id')
    social_provider = data.get('social_provider')
    tipo_cuenta = data.get('tipo_cuenta', 'personal')
    edad = data.get('edad')
    
    return create_social_user(name, email, social_id, social_provider, tipo_cuenta, edad)
  
@user_bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión de usuario
    ---
    tags:
      - Autenticación
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: carlos@gmail.com
            password:
              type: string
              example: contraseña123
    responses:
      200:
        description: Inicio de sesión exitoso
        schema:
          type: object
          properties:
            access_token:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                nombre:
                  type: string
                correo:
                  type: string
                rol:
                  type: integer
                rol_texto:
                  type: string
                telefono:
                  type: string
                sexo:
                  type: string
                fecha_registro:
                  type: string
                tipo_cuenta:
                  type: string
                edad:
                  type: integer
                tutor_nombre:
                  type: string
                tutor_telefono:
                  type: string
                direcciones:
                  type: array
                  items:
                    type: object
                total_direcciones:
                  type: integer
                direccion_predeterminada:
                  type: object
                tarjetas:
                  type: array
                  items:
                    type: object
                total_tarjetas:
                  type: integer
                tarjeta_predeterminada:
                  type: object
                ninos:
                  type: array
                  items:
                    type: object
                total_ninos:
                  type: integer
      401:
        description: Credenciales inválidas
      500:
        description: Error interno del servidor
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Faltan datos requeridos'}), 400
    return login_user(email, password)

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password_route():
    """
    Cambiar contraseña del usuario actual
    ---
    tags:
      - Usuarios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Contraseña cambiada
      401:
        description: Contraseña actual incorrecta
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    user_id = get_jwt_identity()
    
    return change_password(user_id, current_password, new_password)
  
# CAMBIO IMPORTANTE: Cambiar <int:user_id> a <string:user_id>
@user_bp.route('/<string:user_id>', methods=['DELETE'])
@jwt_required()
def user_delete(user_id):
    """
    Eliminar un usuario por ID
    ---
    tags:
      - Usuarios
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Usuario eliminado
      400:
        description: No se puede eliminar porque tiene cuentas infantiles asociadas
      404:
        description: Usuario no encontrado
    """
    return delete_user(user_id)
  
# CAMBIO IMPORTANTE: Cambiar <int:user_id> a <string:user_id>
@user_bp.route('/<string:user_id>', methods=['PUT'])
@jwt_required()
def user_update(user_id):
    """
    Actualizar un usuario por ID
    ---
    tags:
      - Usuarios
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            password:
              type: string
            role:
              type: integer
            telefono:
              type: string
            sexo:
              type: string
            tipo_cuenta:
              type: string
              enum: ['personal', 'infantil']
            edad:
              type: integer
            tutor_nombre:
              type: string
            tutor_telefono:
              type: string
            restricciones_infantiles:
              type: object
            direccion:
              type: object
            tarjeta:
              type: object
    responses:
      200:
        description: Usuario actualizado exitosamente
      404:
        description: Usuario no encontrado
      500:
        description: Error al actualizar el usuario
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400

    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    role = data.get('role')
    telefono = data.get('telefono')
    sexo = data.get('sexo')
    tipo_cuenta = data.get('tipo_cuenta')
    edad = data.get('edad')
    tutor_nombre = data.get('tutor_nombre')
    tutor_telefono = data.get('tutor_telefono')
    restricciones_infantiles = data.get('restricciones_infantiles')
    direccion_data = data.get('direccion')
    tarjeta_data = data.get('tarjeta')

    if direccion_data or tarjeta_data:
        return update_user_with_direccion_y_tarjeta(
            user_id=user_id,
            name=name,
            email=email,
            password=password,
            role=role,
            telefono=telefono,
            sexo=sexo,
            tipo_cuenta=tipo_cuenta,
            edad=edad,
            tutor_nombre=tutor_nombre,
            tutor_telefono=tutor_telefono,
            direccion_data=direccion_data,
            tarjeta_data=tarjeta_data
        )
    else:
        if (name is None and email is None and password is None and role is None and 
            telefono is None and sexo is None and tipo_cuenta is None and 
            edad is None and tutor_nombre is None and tutor_telefono is None and 
            restricciones_infantiles is None):
            return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
          
        return update_user(
            user_id, name, email, password, role, telefono, sexo, 
            tipo_cuenta, edad, tutor_nombre, tutor_telefono, restricciones_infantiles
        )