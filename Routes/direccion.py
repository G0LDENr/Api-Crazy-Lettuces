from flask import Blueprint, request, jsonify
from Controllers.direccionController import (
    get_all_direcciones,
    get_single_direccion,
    create_direccion,
    update_direccion,
    delete_direccion,
    get_direcciones_by_user,
    get_direccion_predeterminada,
    set_direccion_predeterminada,
    search_direcciones
)
from flask_jwt_extended import jwt_required, get_jwt_identity

direccion_bp = Blueprint('direccion_bp', __name__)

@direccion_bp.route('/', methods=['GET'])
@jwt_required()
def index():
    """
    Obtener todas las direcciones
    ---
    tags:
      - Direcciones
    responses:
      200:
        description: Lista de direcciones
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              user_id:
                type: integer
              calle:
                type: string
              numero_exterior:
                type: string
              numero_interior:
                type: string
              colonia:
                type: string
              ciudad:
                type: string
              estado:
                type: string
              codigo_postal:
                type: string
              referencias:
                type: string
              tipo:
                type: string
              predeterminada:
                type: boolean
              activa:
                type: boolean
              fecha_creacion:
                type: string
              fecha_actualizacion:
                type: string
              direccion_completa:
                type: string
      500:
        description: Error al obtener las direcciones
    """
    return get_all_direcciones()

@direccion_bp.route('/search', methods=['GET'])
@jwt_required()
def search_direcciones_route():
    """
    Buscar direcciones por calle, colonia, ciudad o estado
    ---
    tags:
      - Direcciones
    parameters:
      - name: query
        in: query
        type: string
        required: false
    responses:
      200:
        description: Direcciones encontradas
    """
    query = request.args.get('query', '')
    return search_direcciones(query)

@direccion_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_direcciones_usuario_route(user_id):
    """
    Obtener direcciones de un usuario
    ---
    tags:
      - Direcciones
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Direcciones del usuario
    """
    return get_direcciones_by_user(user_id)

@direccion_bp.route('/user/<int:user_id>/predeterminada', methods=['GET'])
@jwt_required()
def get_direccion_predeterminada_route(user_id):
    """
    Obtener dirección predeterminada de un usuario
    ---
    tags:
      - Direcciones
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dirección predeterminada del usuario
      404:
        description: No hay dirección predeterminada
    """
    return get_direccion_predeterminada(user_id)

@direccion_bp.route('/<int:direccion_id>/predeterminada', methods=['PUT'])
@jwt_required()
def set_direccion_predeterminada_route(direccion_id):
    """
    Establecer dirección como predeterminada
    ---
    tags:
      - Direcciones
    parameters:
      - name: direccion_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
    responses:
      200:
        description: Dirección establecida como predeterminada
      404:
        description: Dirección o usuario no encontrado
    """
    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({'msg': 'Se requiere user_id'}), 400
    
    return set_direccion_predeterminada(data['user_id'], direccion_id)

@direccion_bp.route('/<int:direccion_id>', methods=['GET'])
@jwt_required()
def get_direccion(direccion_id):
    """
    Obtener una dirección por ID
    ---
    tags:
      - Direcciones
    parameters:
      - name: direccion_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dirección encontrada
      404:
        description: Dirección no encontrada
    """
    return get_single_direccion(direccion_id)

@direccion_bp.route('/add_direccion', methods=['POST'])
@jwt_required()
def add_direccion():
    """
    Crear una nueva dirección
    ---
    tags:
      - Direcciones
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - calle
            - numero_exterior
            - colonia
            - ciudad
            - estado
            - codigo_postal
          properties:
            user_id:
              type: integer
              example: 1
            calle:
              type: string
              example: "Av. Principal"
            numero_exterior:
              type: string
              example: "123"
            numero_interior:
              type: string
              example: "A"
            colonia:
              type: string
              example: "Centro"
            ciudad:
              type: string
              example: "Ciudad de México"
            estado:
              type: string
              example: "CDMX"
            codigo_postal:
              type: string
              example: "01000"
            referencias:
              type: string
              example: "Entre calles 1 y 2"
            tipo:
              type: string
              example: "casa"
            predeterminada:
              type: boolean
              example: true
            activa:
              type: boolean
              example: true
    responses:
      201:
        description: Dirección creada exitosamente
      400:
        description: Error al crear la dirección
      500:
        description: Error interno del servidor
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    
    return create_direccion(data)

@direccion_bp.route('/<int:direccion_id>', methods=['PUT'])
@jwt_required()
def direccion_update(direccion_id):
    """
    Actualizar una dirección por ID
    ---
    tags:
      - Direcciones
    parameters:
      - name: direccion_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            calle:
              type: string
              example: "Av. Principal Actualizada"
            numero_exterior:
              type: string
              example: "456"
            numero_interior:
              type: string
              example: "B"
            colonia:
              type: string
              example: "Centro Norte"
            ciudad:
              type: string
              example: "Ciudad de México"
            estado:
              type: string
              example: "CDMX"
            codigo_postal:
              type: string
              example: "01001"
            referencias:
              type: string
              example: "Nuevas referencias"
            tipo:
              type: string
              example: "trabajo"
            predeterminada:
              type: boolean
              example: false
            activa:
              type: boolean
              example: true
    responses:
      200:
        description: Dirección actualizada exitosamente
      404:
        description: Dirección no encontrada
      500:
        description: Error al actualizar la dirección
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    
    return update_direccion(direccion_id, data)

@direccion_bp.route('/<int:direccion_id>', methods=['DELETE'])
@jwt_required()
def direccion_delete(direccion_id):
    """
    Eliminar una dirección por ID
    ---
    tags:
      - Direcciones
    parameters:
      - name: direccion_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dirección eliminada
      404:
        description: Dirección no encontrada
    """
    return delete_direccion(direccion_id)

# RUTAS ESPECIALES PARA EL USUARIO ACTUAL
@direccion_bp.route('/me/direcciones', methods=['GET'])
@jwt_required()
def get_my_direcciones():
    """
    Obtener mis direcciones
    ---
    tags:
      - Direcciones
    responses:
      200:
        description: Lista de mis direcciones
      401:
        description: No autorizado
    """
    try:
        current_user_id = int(get_jwt_identity())
        return get_direcciones_by_user(current_user_id)
    except Exception as e:
        print(f"Error en /me/direcciones endpoint: {e}")
        return jsonify({"msg": "Error al obtener direcciones"}), 500

@direccion_bp.route('/me/predeterminada', methods=['GET'])
@jwt_required()
def get_my_predeterminada():
    """
    Obtener mi dirección predeterminada
    ---
    tags:
      - Direcciones
    responses:
      200:
        description: Mi dirección predeterminada
      404:
        description: No tengo dirección predeterminada
      401:
        description: No autorizado
    """
    try:
        current_user_id = int(get_jwt_identity())
        return get_direccion_predeterminada(current_user_id)
    except Exception as e:
        print(f"Error en /me/predeterminada endpoint: {e}")
        return jsonify({"msg": "Error al obtener dirección predeterminada"}), 500

@direccion_bp.route('/me/add_direccion', methods=['POST'])
@jwt_required()
def add_my_direccion():
    """
    Crear nueva dirección para mí
    ---
    tags:
      - Direcciones
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - calle
            - numero_exterior
            - colonia
            - ciudad
            - estado
            - codigo_postal
          properties:
            calle:
              type: string
              example: "Av. Principal"
            numero_exterior:
              type: string
              example: "123"
            numero_interior:
              type: string
              example: "A"
            colonia:
              type: string
              example: "Centro"
            ciudad:
              type: string
              example: "Ciudad de México"
            estado:
              type: string
              example: "CDMX"
            codigo_postal:
              type: string
              example: "01000"
            referencias:
              type: string
              example: "Entre calles 1 y 2"
            tipo:
              type: string
              example: "casa"
            predeterminada:
              type: boolean
              example: true
    responses:
      201:
        description: Dirección creada exitosamente
      400:
        description: Error al crear la dirección
      401:
        description: No autorizado
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data:
            return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
        # Agregar user_id automáticamente
        data['user_id'] = current_user_id
        
        return create_direccion(data)
    except Exception as e:
        print(f"Error en /me/add_direccion endpoint: {e}")
        return jsonify({"msg": "Error al crear dirección"}), 500