from flask import Blueprint, request, jsonify
from Controllers.ordenesController import (
    get_all_ordenes,
    create_orden_completa,
    delete_orden,
    update_orden,
    get_single_orden,
    search_ordenes,
    cambiar_estado_orden,
    get_ordenes_by_estado,
    get_orden_by_codigo,
    get_suplementos_activos,
    get_users_by_role,
    get_ordenes_by_usuario,
    get_estadisticas_ordenes
)
from flask_jwt_extended import jwt_required

orden_bp = Blueprint('orden_bp', __name__)

@orden_bp.route('/', methods=['GET'])
@jwt_required()
def index():
    """
    Obtener todas las órdenes
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de órdenes
    """
    return get_all_ordenes()

@orden_bp.route('/search', methods=['GET'])
@jwt_required()
def search_ordenes_route():
    """
    Buscar órdenes por nombre, teléfono o código
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: query
        in: query
        type: string
        required: false
    responses:
      200:
        description: Órdenes encontradas
    """
    query = request.args.get('query', '')
    return search_ordenes(query)

@orden_bp.route('/estado/<string:estado>', methods=['GET'])
@jwt_required()
def get_ordenes_by_estado_route(estado):
    """
    Obtener órdenes por estado
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: estado
        in: path
        type: string
        required: true
        enum: [pendiente, confirmada, pagada, en_preparacion, enviada, entregada, cancelada, reembolsada]
    responses:
      200:
        description: Órdenes del estado especificado
    """
    return get_ordenes_by_estado(estado)

@orden_bp.route('/usuario/<string:telefono>', methods=['GET'])
def get_ordenes_by_usuario_route(telefono):
    """
    Obtener órdenes por teléfono de usuario
    ---
    tags:
      - Órdenes
    parameters:
      - name: telefono
        in: path
        type: string
        required: true
    responses:
      200:
        description: Órdenes del usuario
    """
    return get_ordenes_by_usuario(telefono)

@orden_bp.route('/codigo/<string:codigo>', methods=['GET'])
def get_orden_by_codigo_route(codigo):
    """
    Obtener orden por código único
    ---
    tags:
      - Órdenes
    parameters:
      - name: codigo
        in: path
        type: string
        required: true
    responses:
      200:
        description: Orden encontrada
      404:
        description: Código no encontrado
    """
    return get_orden_by_codigo(codigo)

@orden_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
def get_estadisticas_route():
    """
    Obtener estadísticas de órdenes
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    responses:
      200:
        description: Estadísticas de órdenes
    """
    return get_estadisticas_ordenes()

@orden_bp.route('/suplementos-activos', methods=['GET'])
def get_suplementos_activos_route():
    """
    Obtener suplementos activos para el formulario
    ---
    tags:
      - Órdenes
    responses:
      200:
        description: Lista de suplementos activos
    """
    return get_suplementos_activos()

# CAMBIO IMPORTANTE: Cambiar <int:orden_id> a <string:orden_id>
@orden_bp.route('/<string:orden_id>', methods=['GET'])
@jwt_required()
def get_orden(orden_id):
    """
    Obtener una orden por ID
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: orden_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Orden encontrada
      404:
        description: Orden no encontrada
    """
    return get_single_orden(orden_id)

@orden_bp.route('/', methods=['POST'])
def add_orden():
    """
    Crear una nueva orden de suplementos
    ---
    tags:
      - Órdenes
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nombre_usuario
            - telefono_usuario
            - tipo_pedido
          properties:
            nombre_usuario:
              type: string
              example: "Juan Pérez"
            telefono_usuario:
              type: string
              example: "+525538986602"
            tipo_pedido:
              type: string
              enum: [suplemento, carrito]
              example: "carrito"
            metodo_pago:
              type: string
              enum: [efectivo, tarjeta, transferencia]
              example: "efectivo"
            suplemento_id:
              type: string
              example: "1"
            cantidad:
              type: integer
              example: 2
              default: 1
            direccion_texto:
              type: string
              example: "Calle Principal #123, Colonia Centro, Ciudad, CP: 12345"
            direccion_id:
              type: string
              example: "1"
            pedido_json:
              type: string
              example: '[{"suplemento_id": "1", "nombre": "Quemador de Grasa", "cantidad": 2, "precio_unitario": 499.99}]'
            precio_unitario:
              type: number
              example: 499.99
            precio_total:
              type: number
              example: 999.98
            info_pago:
              type: object
              example: {"tipo": "visa", "ultimos_4_digitos": "1234", "titular": "Juan Pérez"}
            notas:
              type: string
              example: "Dejar en portería"
    responses:
      201:
        description: Orden creada exitosamente
        schema:
          type: object
          properties:
            msg:
              type: string
            orden:
              type: object
            notificaciones_generadas:
              type: boolean
      400:
        description: Error al crear la orden
    """
    return create_orden_completa()

# CAMBIO IMPORTANTE: Cambiar <int:orden_id> a <string:orden_id>
@orden_bp.route('/<string:orden_id>', methods=['DELETE'])
@jwt_required()
def orden_delete(orden_id):
    """
    Eliminar una orden por ID
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: orden_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Orden eliminada
      404:
        description: Orden no encontrada
    """
    return delete_orden(orden_id)

# CAMBIO IMPORTANTE: Cambiar <int:orden_id> a <string:orden_id>
@orden_bp.route('/<string:orden_id>/estado', methods=['PUT'])
@jwt_required()
def cambiar_estado_route(orden_id):
    """
    Cambiar estado de una orden
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: orden_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - estado
          properties:
            estado:
              type: string
              enum: [pendiente, confirmada, pagada, en_preparacion, enviada, entregada, cancelada, reembolsada]
              example: "en_preparacion"
    responses:
      200:
        description: Estado de la orden cambiado
      404:
        description: Orden no encontrada
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
        
    nuevo_estado = data.get('estado')
    return cambiar_estado_orden(orden_id, nuevo_estado)

# CAMBIO IMPORTANTE: Cambiar <int:orden_id> a <string:orden_id>
@orden_bp.route('/<string:orden_id>', methods=['PUT'])
@jwt_required()
def orden_update(orden_id):
    """
    Actualizar una orden por ID
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: orden_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre_usuario:
              type: string
              example: "Juan Pérez Actualizado"
            telefono_usuario:
              type: string
              example: "+525538986603"
            estado:
              type: string
              enum: [pendiente, confirmada, pagada, en_preparacion, enviada, entregada, cancelada, reembolsada]
              example: "entregada"
            precio_unitario:
              type: number
              example: 450.00
            precio_total:
              type: number
              example: 900.00
            cantidad:
              type: integer
              example: 2
            tipo_pedido:
              type: string
              enum: [suplemento, carrito]
              example: "suplemento"
            suplemento_id:
              type: string
              example: "2"
            metodo_pago:
              type: string
              enum: [efectivo, tarjeta, transferencia]
              example: "tarjeta"
            direccion_texto:
              type: string
              example: "Calle Nueva #456, Colonia Nueva"
            direccion_id:
              type: string
              example: "2"
            notas:
              type: string
              example: "Entregar después de las 5pm"
    responses:
      200:
        description: Orden actualizada exitosamente
      404:
        description: Orden no encontrada
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400

    nombre_usuario = data.get('nombre_usuario')
    telefono_usuario = data.get('telefono_usuario')
    estado = data.get('estado')
    precio_unitario = data.get('precio_unitario')
    precio_total = data.get('precio_total')
    cantidad = data.get('cantidad')
    tipo_pedido = data.get('tipo_pedido')
    suplemento_id = data.get('suplemento_id')
    metodo_pago = data.get('metodo_pago')
    direccion_texto = data.get('direccion_texto')
    direccion_id = data.get('direccion_id')
    notas = data.get('notas')

    if (nombre_usuario is None and telefono_usuario is None and estado is None and 
        precio_unitario is None and precio_total is None and cantidad is None and
        tipo_pedido is None and suplemento_id is None and metodo_pago is None and
        direccion_texto is None and direccion_id is None and notas is None):
        return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
      
    return update_orden(
        orden_id=orden_id,
        nombre_usuario=nombre_usuario,
        telefono_usuario=telefono_usuario,
        estado=estado,
        precio_unitario=precio_unitario,
        precio_total=precio_total,
        cantidad=cantidad,
        tipo_pedido=tipo_pedido,
        suplemento_id=suplemento_id,
        metodo_pago=metodo_pago,
        direccion_texto=direccion_texto,
        direccion_id=direccion_id,
        notas=notas
    )

@orden_bp.route('/usuarios/<string:rol>', methods=['GET'])
@jwt_required()
def get_users_by_role_route(rol):
    """
    Obtener usuarios por rol
    ---
    tags:
      - Órdenes
    security:
      - Bearer: []
    parameters:
      - name: rol
        in: path
        type: string
        required: true
    responses:
      200:
        description: Usuarios obtenidos exitosamente
      400:
        description: Rol inválido
      500:
        description: Error al obtener usuarios
    """
    return get_users_by_role(rol)