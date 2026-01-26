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
    get_available_roles
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

# NUEVA RUTA: Obtener usuario actual desde token JWT
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
      401:
        description: No autorizado
    """
    try:
        # Obtener el ID del usuario desde el token JWT
        current_user_id = int(get_jwt_identity())
        return get_single_user(current_user_id)
    except Exception as e:
        print(f"Error en /me endpoint: {e}")
        return jsonify({"msg": "Error al obtener datos del usuario"}), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
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
        type: integer
        required: true
    responses:
      200:
        description: Usuario encontrado
      404:
        description: Usuario no encontrado
    """
    return get_single_user(user_id)

@user_bp.route('/profile/<int:user_id>', methods=['GET'])
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
        type: integer
        required: true
    responses:
      200:
        description: Perfil del usuario
      404:
        description: Usuario no encontrado
    """
    return get_user_profile(user_id)

# NUEVA RUTA: Actualizar usuario actual desde token JWT
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
    responses:
      200:
        description: Perfil actualizado exitosamente
      400:
        description: Datos inválidos
      401:
        description: No autorizado
    """
    try:
        # Obtener el ID del usuario desde el token JWT
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data:
            return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
        # Mapear los nombres de campos del frontend al backend
        # El frontend envía: nombre, telefono, sexo, correo
        # El backend espera: name, email, telefono, sexo
        
        return update_user(
            user_id=current_user_id,
            name=data.get('nombre'),
            email=data.get('correo'),
            telefono=data.get('telefono'),
            sexo=data.get('sexo'),
            password=None,  # No actualizar contraseña aquí
            role=None       # No actualizar rol aquí
        )
        
    except Exception as e:
        print(f"Error en /update endpoint: {e}")
        return jsonify({"msg": "Error al actualizar el perfil"}), 500

@user_bp.route('/add_user', methods=['POST'])
def add_user():
    """
    Crear un nuevo usuario
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

    if not email or not name or not password:
        return jsonify({'msg': 'Faltan datos requeridos'}), 400
    
    return create_user(name, email, password, role, telefono, sexo)

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
    
    return create_social_user(name, email, social_id, social_provider)
  
@user_bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión de usuario
    ---
    tags:
      - Autenticación
    # Sin seguridad - este endpoint es público
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
    
    # Obtener el ID del usuario del token JWT
    user_id = int(get_jwt_identity())  # Convertir de string a int
    
    return change_password(user_id, current_password, new_password)
  
@user_bp.route('/<int:user_id>', methods=['DELETE'])
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
        type: integer
        required: true
    responses:
      200:
        description: Usuario eliminado
      404:
        description: Usuario no encontrado
    """
    return delete_user(user_id)
  
@user_bp.route('/<int:user_id>', methods=['PUT'])
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
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Juan Carlos Actualizado
            email:
              type: string
              example: carlos@gmail.com
            password:
              type: string
              example: nueva_contraseña123
            role:
              type: integer
              example: 1
            telefono:
              type: string
              example: "7294030702"
            sexo:
              type: string
              example: "M"
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

    if name is None and email is None and password is None and role is None and telefono is None and sexo is None:
        return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
      
    return update_user(user_id, name, email, password, role, telefono, sexo)