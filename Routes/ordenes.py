from flask import Blueprint, request, jsonify
from Controllers.ordenesController import (
    get_all_ordenes,
    create_orden_completa,  # ✅ Cambiado a la nueva función
    delete_orden,
    update_orden,
    get_single_orden,
    search_ordenes,
    cambiar_estado_orden,
    get_ordenes_by_estado,
    get_orden_by_codigo,
    get_especiales_activos,
    get_users_by_role
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
    parameters:
      - name: estado
        in: path
        type: string
        required: true
        enum: [pendiente, preparando, listo, entregado, cancelado]
    responses:
      200:
        description: Órdenes del estado especificado
    """
    return get_ordenes_by_estado(estado)

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

@orden_bp.route('/especiales-activos', methods=['GET'])
def get_especiales_activos_route():
    """
    Obtener especiales activos
    ---
    tags:
      - Órdenes
    responses:
      200:
        description: Lista de especiales activos
    """
    return get_especiales_activos()

@orden_bp.route('/<int:orden_id>', methods=['GET'])
@jwt_required()
def get_orden(orden_id):
    """
    Obtener una orden por ID
    ---
    tags:
      - Órdenes
    parameters:
      - name: orden_id
        in: path
        type: integer
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
    Crear una nueva orden - VERSIÓN ACTUALIZADA CON CARRITO
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
              enum: [especial, personalizado, carrito]
              example: "carrito"
            metodo_pago:
              type: string
              enum: [efectivo, tarjeta]
              example: "efectivo"
            especial_id:
              type: integer
              example: 1
            direccion_texto:
              type: string
              example: "Calle Principal #123, Colonia Centro, Ciudad, Estado, CP: 12345"
            direccion_id:
              type: integer
              example: 1
            pedido_json:
              type: string
              example: '{"tipo": "carrito", "items": [{"nombre": "Hamburguesa", "cantidad": 2, "precio": 50}], "total": 100}'
            ingredientes_personalizados:
              type: string
              example: "Carne, Queso, Lechuga, Tomate"
            cantidad:
              type: integer
              example: 2
            precio:
              type: number
              example: 100.00
            info_pago:
              type: object
              example: {"tipo": "visa", "ultimos_4_digitos": "1234", "titular": "Juan Pérez"}
            notas:
              type: string
              example: "Sin cebolla, entregar en puerta"
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
    # ✅ Ahora llama a la nueva función que maneja todos los campos
    return create_orden_completa()

@orden_bp.route('/<int:orden_id>', methods=['DELETE'])
@jwt_required()
def orden_delete(orden_id):
    """
    Eliminar una orden por ID
    ---
    tags:
      - Órdenes
    parameters:
      - name: orden_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Orden eliminada
      404:
        description: Orden no encontrada
    """
    return delete_orden(orden_id)

@orden_bp.route('/<int:orden_id>/estado', methods=['PUT'])
@jwt_required()
def cambiar_estado_route(orden_id):
    """
    Cambiar estado de una orden
    ---
    tags:
      - Órdenes
    parameters:
      - name: orden_id
        in: path
        type: integer
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
              enum: [pendiente, preparando, listo, entregado, cancelado]
              example: "preparando"
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

@orden_bp.route('/<int:orden_id>', methods=['PUT'])
@jwt_required()
def orden_update(orden_id):
    """
    Actualizar una orden por ID
    ---
    tags:
      - Órdenes
    parameters:
      - name: orden_id
        in: path
        type: integer
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
              example: "entregado"
            precio:
              type: number
              example: 35.50
            tipo_pedido:
              type: string
              enum: [especial, personalizado]
              example: "especial"
            especial_id:
              type: integer
              example: 2
            direccion_texto:
              type: string
              example: "Calle Nueva #456, Colonia Nueva"
            direccion_id:
              type: integer
              example: 2
            ingredientes_personalizados:
              type: string
              example: "Carne, Queso, Lechuga"
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
    precio = data.get('precio')
    tipo_pedido = data.get('tipo_pedido')
    especial_id = data.get('especial_id')
    direccion_texto = data.get('direccion_texto')
    direccion_id = data.get('direccion_id')
    ingredientes_personalizados = data.get('ingredientes_personalizados')

    if (nombre_usuario is None and telefono_usuario is None and estado is None and 
        precio is None and tipo_pedido is None and especial_id is None and 
        direccion_texto is None and direccion_id is None and 
        ingredientes_personalizados is None):
        return jsonify({'msg': 'No se proporcionaron datos para actualizar'}), 400
      
    return update_orden(
        orden_id=orden_id,
        nombre_usuario=nombre_usuario,
        telefono_usuario=telefono_usuario,
        estado=estado,
        precio=precio,
        tipo_pedido=tipo_pedido,
        especial_id=especial_id,
        ingredientes_personalizados=ingredientes_personalizados
    )

@orden_bp.route('/usuarios/<string:rol>', methods=['GET'])
@jwt_required()
def get_users_by_role_route(rol):
    """
    Obtener usuarios por rol
    ---
    tags:
      - Órdenes
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