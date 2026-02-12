from flask import Blueprint, request, jsonify
from Controllers.ingredientesController import (
    get_all_ingredientes,
    create_ingrediente,
    delete_ingrediente,
    update_ingrediente,
    get_single_ingrediente,
    search_ingredientes,
    toggle_ingrediente_activo,
    get_ingredientes_activos,
    get_ingredientes_by_categoria,
    get_categorias,
    bulk_create_ingredientes
)
from flask_jwt_extended import jwt_required

ingredientes_bp = Blueprint('ingredientes_bp', __name__)

@ingredientes_bp.route('/', methods=['GET'])
def index():
    """
    Obtener todos los ingredientes
    ---
    tags:
      - Ingredientes
    parameters:
      - name: activos
        in: query
        type: boolean
        required: false
        description: Si es true, devuelve solo ingredientes activos (por defecto)
      - name: categoria
        in: query
        type: string
        required: false
        description: Filtrar por categoría
    responses:
      200:
        description: Lista de ingredientes
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              nombre:
                type: string
              categoria:
                type: string
              activo:
                type: boolean
              fecha_creacion:
                type: string
              fecha_actualizacion:
                type: string
      500:
        description: Error al obtener los ingredientes
    """
    return get_all_ingredientes()

@ingredientes_bp.route('/active', methods=['GET'])
def get_active():
    """
    Obtener solo ingredientes activos
    ---
    tags:
      - Ingredientes
    responses:
      200:
        description: Lista de ingredientes activos
    """
    return get_ingredientes_activos()

@ingredientes_bp.route('/categorias', methods=['GET'])
def get_categorias_route():
    """
    Obtener lista de categorías
    ---
    tags:
      - Ingredientes
    responses:
      200:
        description: Lista de categorías
    """
    return get_categorias()

@ingredientes_bp.route('/categoria/<string:categoria>', methods=['GET'])
def get_by_categoria(categoria):
    """
    Obtener ingredientes por categoría
    ---
    tags:
      - Ingredientes
    parameters:
      - name: categoria
        in: path
        type: string
        required: true
    responses:
      200:
        description: Ingredientes encontrados por categoría
    """
    return get_ingredientes_by_categoria(categoria)

@ingredientes_bp.route('/search', methods=['GET'])
def search_ingredientes_route():
    """
    Buscar ingredientes por nombre o categoría
    ---
    tags:
      - Ingredientes
    parameters:
      - name: query
        in: query
        type: string
        required: false
    responses:
      200:
        description: Ingredientes encontrados
    """
    query = request.args.get('query', '')
    return search_ingredientes(query)

@ingredientes_bp.route('/<int:ingrediente_id>', methods=['GET'])
def get_ingrediente(ingrediente_id):
    """
    Obtener un ingrediente por ID
    ---
    tags:
      - Ingredientes
    parameters:
      - name: ingrediente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Ingrediente encontrado
      404:
        description: Ingrediente no encontrado
    """
    return get_single_ingrediente(ingrediente_id)

@ingredientes_bp.route('/', methods=['POST'])
@jwt_required()
def add_ingrediente():
    """
    Crear un nuevo ingrediente
    ---
    tags:
      - Ingredientes
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nombre
          properties:
            nombre:
              type: string
              example: "Lechuga Romana"
            categoria:
              type: string
              example: "vegetales"
            activo:
              type: boolean
              default: true
    responses:
      201:
        description: Ingrediente creado exitosamente
      400:
        description: Error al crear el ingrediente
      500:
        description: Error interno del servidor
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
      
    nombre = data.get('nombre')
    categoria = data.get('categoria')
    activo = data.get('activo', True)

    if not nombre:
        return jsonify({'msg': 'El nombre del ingrediente es requerido'}), 400
    
    return create_ingrediente(nombre, categoria, activo)

@ingredientes_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_add_ingredientes():
    """
    Crear múltiples ingredientes a la vez
    ---
    tags:
      - Ingredientes
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: array
          items:
            type: object
            properties:
              nombre:
                type: string
              categoria:
                type: string
              activo:
                type: boolean
    responses:
      201:
        description: Ingredientes creados exitosamente
    """
    return bulk_create_ingredientes()

@ingredientes_bp.route('/<int:ingrediente_id>', methods=['DELETE'])
@jwt_required()
def ingrediente_delete(ingrediente_id):
    """
    Eliminar un ingrediente por ID
    ---
    tags:
      - Ingredientes
    parameters:
      - name: ingrediente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Ingrediente eliminado
      404:
        description: Ingrediente no encontrado
    """
    return delete_ingrediente(ingrediente_id)

@ingredientes_bp.route('/<int:ingrediente_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_activo_route(ingrediente_id):
    """
    Activar/desactivar un ingrediente
    ---
    tags:
      - Ingredientes
    parameters:
      - name: ingrediente_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Estado del ingrediente cambiado
      404:
        description: Ingrediente no encontrado
    """
    return toggle_ingrediente_activo(ingrediente_id)

@ingredientes_bp.route('/<int:ingrediente_id>', methods=['PUT'])
@jwt_required()
def ingrediente_update(ingrediente_id):
    """
    Actualizar un ingrediente por ID
    ---
    tags:
      - Ingredientes
    parameters:
      - name: ingrediente_id
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
              example: "Lechuga Romana Actualizada"
            categoria:
              type: string
              example: "vegetales"
            activo:
              type: boolean
              example: true
    responses:
      200:
        description: Ingrediente actualizado exitosamente
      404:
        description: Ingrediente no encontrado
      500:
        description: Error al actualizar el ingrediente
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400

    nombre = data.get('nombre')
    categoria = data.get('categoria')
    activo = data.get('activo')

    if nombre is None and categoria is None and activo is None:
        return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
      
    return update_ingrediente(ingrediente_id, nombre, categoria, activo)