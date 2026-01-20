from flask import Blueprint, request, jsonify
from Controllers.especialesController import (
    get_all_especiales,
    create_especial,
    delete_especial,
    update_especial,
    get_single_especial,
    search_especiales,
    toggle_especial_activo,
    get_active_especiales
)
from flask_jwt_extended import jwt_required

especiales_bp = Blueprint('especiales_bp', __name__)

@especiales_bp.route('/', methods=['GET'])
def index():
    """
    Obtener todos los especiales
    ---
    tags:
      - Especiales
    parameters:
      - name: all
        in: query
        type: boolean
        required: false
        description: Si es true, devuelve todos los especiales (incluyendo inactivos)
    responses:
      200:
        description: Lista de especiales
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nombre:
                type: string
              ingredientes:
                type: string
              precio:
                type: number
                format: float
              activo:
                type: boolean
              fecha_creacion:
                type: string
              fecha_actualizacion:
                type: string
      500:
        description: Error al obtener los especiales
    """
    return get_all_especiales()

@especiales_bp.route('/active', methods=['GET'])
def get_active():
    """
    Obtener solo especiales activos
    ---
    tags:
      - Especiales
    responses:
      200:
        description: Lista de especiales activos
    """
    return get_active_especiales()

@especiales_bp.route('/search', methods=['GET'])
def search_especiales_route():
    """
    Buscar especiales por nombre o ingredientes
    ---
    tags:
      - Especiales
    parameters:
      - name: query
        in: query
        type: string
        required: false
    responses:
      200:
        description: Especiales encontrados
    """
    query = request.args.get('query', '')
    return search_especiales(query)

@especiales_bp.route('/<int:especial_id>', methods=['GET'])
def get_especial(especial_id):
    """
    Obtener un especial por ID
    ---
    tags:
      - Especiales
    parameters:
      - name: especial_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Especial encontrado
      404:
        description: Especial no encontrado
    """
    return get_single_especial(especial_id)

@especiales_bp.route('/', methods=['POST'])
@jwt_required()
def add_especial():
    """
    Crear un nuevo especial
    ---
    tags:
      - Especiales
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - ingredientes
            - precio
          properties:
            nombre:
              type: string
              example: "Especial de la Casa"
            ingredientes:
              type: string
              example: "Carne, queso, lechuga, tomate, salsa especial"
            precio:
              type: number
              format: float
              example: 99.50
            activo:
              type: boolean
              default: true
    responses:
      201:
        description: Especial creado exitosamente
      400:
        description: Error al crear el especial
      500:
        description: Error interno del servidor
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
      
    nombre = data.get('nombre')
    ingredientes = data.get('ingredientes')
    precio = data.get('precio')
    activo = data.get('activo', True)

    if not nombre or not ingredientes or precio is None:
        return jsonify({'msg': 'Nombre, ingredientes y precio son requeridos'}), 400
    
    return create_especial(nombre, ingredientes, precio, activo)

@especiales_bp.route('/<int:especial_id>', methods=['DELETE'])
@jwt_required()
def especial_delete(especial_id):
    """
    Eliminar un especial por ID
    ---
    tags:
      - Especiales
    parameters:
      - name: especial_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Especial eliminado
      404:
        description: Especial no encontrado
    """
    return delete_especial(especial_id)

@especiales_bp.route('/<int:especial_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_activo_route(especial_id):
    """
    Activar/desactivar un especial
    ---
    tags:
      - Especiales
    parameters:
      - name: especial_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Estado del especial cambiado
      404:
        description: Especial no encontrado
    """
    return toggle_especial_activo(especial_id)

@especiales_bp.route('/<int:especial_id>', methods=['PUT'])
@jwt_required()
def especial_update(especial_id):
    """
    Actualizar un especial por ID
    ---
    tags:
      - Especiales
    parameters:
      - name: especial_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Especial de la Casa Actualizado"
            ingredientes:
              type: string
              example: "Carne, queso, lechuga, tomate, salsa especial, cebolla"
            precio:
              type: number
              format: float
              example: 109.50
            activo:
              type: boolean
              example: true
    responses:
      200:
        description: Especial actualizado exitosamente
      404:
        description: Especial no encontrado
      500:
        description: Error al actualizar el especial
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400

    nombre = data.get('nombre')
    ingredientes = data.get('ingredientes')
    precio = data.get('precio')
    activo = data.get('activo')

    if nombre is None and ingredientes is None and precio is None and activo is None:
        return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
      
    return update_especial(especial_id, nombre, ingredientes, precio, activo)