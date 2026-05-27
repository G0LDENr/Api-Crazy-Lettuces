from flask import Blueprint, request, jsonify
from Controllers.targetasController import (
    get_tarjetas_usuario,
    get_tarjeta_by_id,
    get_tarjeta_predeterminada,
    create_tarjeta,
    update_tarjeta,
    delete_tarjeta,
    set_tarjeta_predeterminada
)
from flask_jwt_extended import jwt_required, get_jwt_identity

tarjeta_bp = Blueprint('tarjeta_bp', __name__)

@tarjeta_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_tarjetas(user_id):
    """
    Obtener todas las tarjetas de un usuario
    ---
    tags:
      - Tarjetas
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de tarjetas del usuario
      404:
        description: Usuario no encontrado
    """
    return get_tarjetas_usuario(user_id)

@tarjeta_bp.route('/<int:tarjeta_id>', methods=['GET'])
@jwt_required()
def get_tarjeta(tarjeta_id):
    """
    Obtener una tarjeta por ID
    ---
    tags:
      - Tarjetas
    parameters:
      - name: tarjeta_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Tarjeta encontrada
      404:
        description: Tarjeta no encontrada
    """
    return get_tarjeta_by_id(tarjeta_id)

@tarjeta_bp.route('/user/<int:user_id>/predeterminada', methods=['GET'])
@jwt_required()
def get_user_tarjeta_predeterminada(user_id):
    """
    Obtener tarjeta predeterminada del usuario
    ---
    tags:
      - Tarjetas
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Tarjeta predeterminada
      404:
        description: No hay tarjeta predeterminada
    """
    return get_tarjeta_predeterminada(user_id)

@tarjeta_bp.route('/user/<int:user_id>', methods=['POST'])
@jwt_required()
def create_user_tarjeta(user_id):
    """
    Agregar una tarjeta a un usuario
    ---
    tags:
      - Tarjetas
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
          required:
            - nombre_titular
            - numero_tarjeta
            - mes_expiracion
            - anio_expiracion
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
      201:
        description: Tarjeta creada exitosamente
      400:
        description: Datos inválidos
      404:
        description: Usuario no encontrado
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    return create_tarjeta(user_id, data)

@tarjeta_bp.route('/<int:tarjeta_id>', methods=['PUT'])
@jwt_required()
def update_tarjeta_route(tarjeta_id):
    """
    Actualizar una tarjeta
    ---
    tags:
      - Tarjetas
    parameters:
      - name: tarjeta_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre_titular:
              type: string
              example: "Juan Pérez Actualizado"
            mes_expiracion:
              type: string
              example: "11"
            anio_expiracion:
              type: string
              example: "2026"
            predeterminada:
              type: boolean
              example: true
    responses:
      200:
        description: Tarjeta actualizada exitosamente
      404:
        description: Tarjeta no encontrada
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    return update_tarjeta(tarjeta_id, data)

@tarjeta_bp.route('/<int:tarjeta_id>', methods=['DELETE'])
@jwt_required()
def delete_tarjeta_route(tarjeta_id):
    """
    Eliminar una tarjeta
    ---
    tags:
      - Tarjetas
    parameters:
      - name: tarjeta_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Tarjeta eliminada exitosamente
      404:
        description: Tarjeta no encontrada
    """
    return delete_tarjeta(tarjeta_id)

@tarjeta_bp.route('/user/<int:user_id>/predeterminada/<int:tarjeta_id>', methods=['PUT'])
@jwt_required()
def set_tarjeta_predeterminada_route(user_id, tarjeta_id):
    """
    Establecer una tarjeta como predeterminada
    ---
    tags:
      - Tarjetas
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: tarjeta_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Tarjeta predeterminada actualizada
      403:
        description: La tarjeta no pertenece al usuario
      404:
        description: Tarjeta no encontrada
    """
    return set_tarjeta_predeterminada(user_id, tarjeta_id)

# Ruta para obtener tarjetas del usuario actual (desde token)
@tarjeta_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_tarjetas():
    """
    Obtener todas las tarjetas del usuario actual
    ---
    tags:
      - Tarjetas
    responses:
      200:
        description: Lista de tarjetas del usuario actual
    """
    try:
        # Obtener el user_id del token SIN convertir a int
        current_user_id = get_jwt_identity()
        print(f"Usuario autenticado ID: {current_user_id} (tipo: {type(current_user_id)})")
        
        # Pasar el ID directamente - el controlador manejará la conversión
        return get_tarjetas_usuario(current_user_id)
    except Exception as e:
        print(f"Error en /me tarjetas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener tarjetas", "error": str(e)}), 500