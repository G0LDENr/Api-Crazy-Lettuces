from flask import Blueprint, request, jsonify
from Controllers.suplementosController import (
    get_all_suplementos,
    create_suplemento,
    delete_suplemento,
    update_suplemento,
    get_single_suplemento,
    search_suplementos,
    toggle_suplemento_activo,
    get_active_suplementos,
    get_suplementos_by_categoria,
    get_suplementos_by_presentacion,
    get_bajo_stock,
    get_categorias,
    get_presentaciones
)
from flask_jwt_extended import jwt_required

suplementos_bp = Blueprint('suplementos_bp', __name__)

@suplementos_bp.route('/', methods=['GET'])
def index():
    """
    Obtener todos los suplementos
    ---
    tags:
      - Suplementos
    parameters:
      - name: all
        in: query
        type: boolean
        required: false
        description: Si es true, devuelve todos (incluyendo inactivos)
    responses:
      200:
        description: Lista de suplementos
    """
    return get_all_suplementos()

@suplementos_bp.route('/active', methods=['GET'])
def get_active():
    """
    Obtener solo suplementos activos
    ---
    tags:
      - Suplementos
    """
    return get_active_suplementos()

@suplementos_bp.route('/categorias', methods=['GET'])
def get_categorias_route():
    """
    Obtener todas las categorías disponibles
    ---
    tags:
      - Suplementos
    """
    return get_categorias()

@suplementos_bp.route('/presentaciones', methods=['GET'])
def get_presentaciones_route():
    """
    Obtener todas las presentaciones disponibles
    ---
    tags:
      - Suplementos
    """
    return get_presentaciones()

@suplementos_bp.route('/categoria/<string:categoria>', methods=['GET'])
def get_by_categoria(categoria):
    """
    Obtener suplementos por categoría
    ---
    tags:
      - Suplementos
    parameters:
      - name: categoria
        in: path
        type: string
        required: true
        enum: [quemadores, proteinas, fibras, detox, termogenicos, control_apetito, energeticos, vitaminas]
    """
    return get_suplementos_by_categoria(categoria)

@suplementos_bp.route('/presentacion/<string:presentacion>', methods=['GET'])
def get_by_presentacion(presentacion):
    """
    Obtener suplementos por presentación
    ---
    tags:
      - Suplementos
    parameters:
      - name: presentacion
        in: path
        type: string
        required: true
        enum: [polvo, capsulas, tabletas, liquido, gomitas, barritas]
    """
    return get_suplementos_by_presentacion(presentacion)

@suplementos_bp.route('/bajo-stock', methods=['GET'])
def get_bajo_stock_route():
    """
    Obtener suplementos con stock bajo
    ---
    tags:
      - Suplementos
    parameters:
      - name: limite
        in: query
        type: integer
        required: false
        default: 10
    """
    return get_bajo_stock()

@suplementos_bp.route('/search', methods=['GET'])
def search_suplementos_route():
    """
    Buscar suplementos
    ---
    tags:
      - Suplementos
    parameters:
      - name: query
        in: query
        type: string
        required: false
    """
    query = request.args.get('query', '')
    return search_suplementos(query)

@suplementos_bp.route('/<int:suplemento_id>', methods=['GET'])
def get_suplemento(suplemento_id):
    """
    Obtener un suplemento por ID
    ---
    tags:
      - Suplementos
    """
    return get_single_suplemento(suplemento_id)

@suplementos_bp.route('/', methods=['POST'])
@jwt_required()
def add_suplemento():
    """
    Crear un nuevo suplemento
    ---
    tags:
      - Suplementos
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - descripcion
            - precio
          properties:
            nombre:
              type: string
              example: "Quemador de Grasa Extreme"
            descripcion:
              type: string
              example: "Suplemento termogénico avanzado"
            precio:
              type: number
              format: float
              example: 499.99
            categoria:
              type: string
              enum: [quemadores, proteinas, fibras, detox, termogenicos, control_apetito, energeticos, vitaminas]
              default: quemadores
            presentacion:
              type: string
              enum: [polvo, capsulas, tabletas, liquido, gomitas, barritas]
              default: polvo
            beneficios:
              type: string
              example: "Acelera metabolismo, reduce apetito"
            modo_uso:
              type: string
              example: "Tomar 2 cápsulas antes del desayuno"
            stock:
              type: integer
              default: 0
            activo:
              type: boolean
              default: true
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
      
    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')
    precio = data.get('precio')
    categoria = data.get('categoria', 'quemadores')
    presentacion = data.get('presentacion', 'polvo')
    beneficios = data.get('beneficios', '')
    modo_uso = data.get('modo_uso', '')
    stock = data.get('stock', 0)
    activo = data.get('activo', True)

    if not nombre or not descripcion or precio is None:
        return jsonify({'msg': 'Nombre, descripción y precio son requeridos'}), 400
    
    return create_suplemento(nombre, descripcion, precio, categoria, presentacion, 
                            beneficios, modo_uso, stock, activo)

@suplementos_bp.route('/<int:suplemento_id>', methods=['DELETE'])
@jwt_required()
def suplemento_delete(suplemento_id):
    """
    Eliminar un suplemento por ID
    ---
    tags:
      - Suplementos
    """
    return delete_suplemento(suplemento_id)

@suplementos_bp.route('/<int:suplemento_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_activo_route(suplemento_id):
    """
    Activar/desactivar un suplemento
    ---
    tags:
      - Suplementos
    """
    return toggle_suplemento_activo(suplemento_id)

@suplementos_bp.route('/<int:suplemento_id>', methods=['PUT'])
@jwt_required()
def suplemento_update(suplemento_id):
    """
    Actualizar un suplemento por ID
    ---
    tags:
      - Suplementos
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            descripcion:
              type: string
            precio:
              type: number
            categoria:
              type: string
            presentacion:
              type: string
            beneficios:
              type: string
            modo_uso:
              type: string
            stock:
              type: integer
            activo:
              type: boolean
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400

    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    categoria = data.get('categoria')
    presentacion = data.get('presentacion')
    beneficios = data.get('beneficios')
    modo_uso = data.get('modo_uso')
    stock = data.get('stock')
    activo = data.get('activo')

    if all(v is None for v in [nombre, descripcion, precio, categoria, presentacion, 
                               beneficios, modo_uso, stock, activo]):
        return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
      
    return update_suplemento(suplemento_id, nombre, descripcion, precio, categoria, 
                            presentacion, beneficios, modo_uso, stock, activo)

@suplementos_bp.route('/analisis', methods=['GET'])
@jwt_required()
def analisis_suplementos():
    """
    Analizar suplementos
    ---
    tags:
      - Análisis
    """
    from Controllers.analisisController import analizar_suplementos
    return analizar_suplementos()