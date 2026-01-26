from flask import Blueprint, request, jsonify
from Controllers.notificacionesController import (
    obtener_notificaciones_usuario,
    obtener_notificaciones_no_leidas,
    marcar_como_leida,
    marcar_todas_como_leidas,
    eliminar_notificacion,
    eliminar_todas_leidas,
    enviar_mensaje,
    obtener_analiticas,
    obtener_usuarios_para_mensaje,
    obtener_notificaciones_por_orden,
    obtener_contador_notificaciones,
    notificar_nuevo_pedido,
    notificar_cambio_estado_pedido,
    notificar_pedido_cancelado
)
from flask_jwt_extended import jwt_required

notificaciones_bp = Blueprint('notificaciones_bp', __name__)

@notificaciones_bp.route('/usuario', methods=['GET'])
@jwt_required()
def obtener_notificaciones_usuario_route():
    """
    Obtener notificaciones del usuario actual
    ---
    tags:
      - Notificaciones
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Número de página
      - name: per_page
        in: query
        type: integer
        required: false
        default: 20
        description: Notificaciones por página
      - name: user_type
        in: query
        type: string
        required: false
        default: cliente
        enum: [cliente, admin]
        description: Tipo de usuario
    responses:
      200:
        description: Lista de notificaciones
        schema:
          type: object
          properties:
            notificaciones:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  titulo:
                    type: string
                  mensaje:
                    type: string
                  tipo:
                    type: string
                  leida:
                    type: boolean
                  fecha_creacion:
                    type: string
                  metadata:
                    type: object
            total_notificaciones:
              type: integer
            pagina_actual:
              type: integer
            total_paginas:
              type: integer
      401:
        description: No autorizado
      500:
        description: Error del servidor
    """
    return obtener_notificaciones_usuario()

@notificaciones_bp.route('/no-leidas', methods=['GET'])
@jwt_required()
def obtener_notificaciones_no_leidas_route():
    """
    Obtener notificaciones no leídas
    ---
    tags:
      - Notificaciones
    parameters:
      - name: user_type
        in: query
        type: string
        required: false
        default: cliente
        enum: [cliente, admin]
        description: Tipo de usuario
    responses:
      200:
        description: Notificaciones no leídas
        schema:
          type: object
          properties:
            notificaciones:
              type: array
              items:
                $ref: '#/definitions/Notificacion'
            total_no_leidas:
              type: integer
      401:
        description: No autorizado
      500:
        description: Error del servidor
    """
    return obtener_notificaciones_no_leidas()

@notificaciones_bp.route('/contador', methods=['GET'])
@jwt_required()
def obtener_contador_notificaciones_route():
    """
    Obtener contador de notificaciones no leídas
    ---
    tags:
      - Notificaciones
    parameters:
      - name: user_type
        in: query
        type: string
        required: false
        default: cliente
        enum: [cliente, admin]
        description: Tipo de usuario
    responses:
      200:
        description: Contador de notificaciones
        schema:
          type: object
          properties:
            total_no_leidas:
              type: integer
            notificaciones_recientes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  titulo:
                    type: string
                  mensaje:
                    type: string
                  tipo:
                    type: string
                  fecha_creacion:
                    type: string
      401:
        description: No autorizado
      500:
        description: Error del servidor
    """
    return obtener_contador_notificaciones()

@notificaciones_bp.route('/<int:notificacion_id>/leer', methods=['PUT'])
@jwt_required()
def marcar_como_leida_route(notificacion_id):
    """
    Marcar notificación como leída
    ---
    tags:
      - Notificaciones
    parameters:
      - name: notificacion_id
        in: path
        type: integer
        required: true
        description: ID de la notificación
    responses:
      200:
        description: Notificación marcada como leída
        schema:
          type: object
          properties:
            msg:
              type: string
      401:
        description: No autorizado
      403:
        description: No tiene permisos
      404:
        description: Notificación no encontrada
      500:
        description: Error del servidor
    """
    return marcar_como_leida(notificacion_id)

@notificaciones_bp.route('/leer-todas', methods=['PUT'])
@jwt_required()
def marcar_todas_como_leidas_route():
    """
    Marcar todas las notificaciones como leídas
    ---
    tags:
      - Notificaciones
    parameters:
      - name: user_type
        in: query
        type: string
        required: false
        default: cliente
        enum: [cliente, admin]
        description: Tipo de usuario
    responses:
      200:
        description: Notificaciones marcadas como leídas
        schema:
          type: object
          properties:
            msg:
              type: string
      401:
        description: No autorizado
      500:
        description: Error del servidor
    """
    return marcar_todas_como_leidas()

@notificaciones_bp.route('/<int:notificacion_id>', methods=['DELETE'])
@jwt_required()
def eliminar_notificacion_route(notificacion_id):
    """
    Eliminar una notificación
    ---
    tags:
      - Notificaciones
    parameters:
      - name: notificacion_id
        in: path
        type: integer
        required: true
        description: ID de la notificación
    responses:
      200:
        description: Notificación eliminada
        schema:
          type: object
          properties:
            msg:
              type: string
      401:
        description: No autorizado
      403:
        description: No tiene permisos
      404:
        description: Notificación no encontrada
      500:
        description: Error del servidor
    """
    return eliminar_notificacion(notificacion_id)

@notificaciones_bp.route('/leidas', methods=['DELETE'])
@jwt_required()
def eliminar_todas_leidas_route():
    """
    Eliminar todas las notificaciones leídas
    ---
    tags:
      - Notificaciones
    parameters:
      - name: user_type
        in: query
        type: string
        required: false
        default: cliente
        enum: [cliente, admin]
        description: Tipo de usuario
    responses:
      200:
        description: Notificaciones eliminadas
        schema:
          type: object
          properties:
            msg:
              type: string
      401:
        description: No autorizado
      500:
        description: Error del servidor
    """
    return eliminar_todas_leidas()

@notificaciones_bp.route('/mensaje', methods=['POST'])
@jwt_required()
def enviar_mensaje_route():
    """
    Enviar mensaje a usuarios (solo admin)
    ---
    tags:
      - Notificaciones
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - destinatario_tipo
            - mensaje
          properties:
            destinatario_tipo:
              type: string
              enum: [todos, cliente, admin, todos_admins]
              example: "cliente"
              description: Tipo de destinatario
            destinatario_id:
              type: integer
              example: 123
              description: ID del destinatario (opcional)
            titulo:
              type: string
              example: "Mensaje Importante"
              description: Título del mensaje
            mensaje:
              type: string
              example: "Hoy tenemos promoción especial"
              description: Contenido del mensaje
    responses:
      201:
        description: Mensaje enviado
        schema:
          type: object
          properties:
            msg:
              type: string
            notificaciones_enviadas:
              type: integer
      400:
        description: Datos inválidos
      401:
        description: No autorizado
      403:
        description: Solo administradores pueden enviar mensajes
      500:
        description: Error del servidor
    """
    return enviar_mensaje()

@notificaciones_bp.route('/analiticas', methods=['GET'])
@jwt_required()
def obtener_analiticas_route():
    """
    Obtener analíticas de notificaciones (solo admin)
    ---
    tags:
      - Notificaciones
    parameters:
      - name: dias
        in: query
        type: integer
        required: false
        default: 30
        description: Número de días para analizar
    responses:
      200:
        description: Analíticas de notificaciones
        schema:
          type: object
          properties:
            total_notificaciones:
              type: integer
            distribucion_tipos:
              type: object
            no_leidas:
              type: integer
            tasa_lectura:
              type: number
            estadisticas_diarias:
              type: array
              items:
                type: object
                properties:
                  fecha:
                    type: string
                  count:
                    type: integer
            periodo_analizado:
              type: string
      401:
        description: No autorizado
      403:
        description: Solo administradores pueden ver analíticas
      500:
        description: Error del servidor
    """
    return obtener_analiticas()

@notificaciones_bp.route('/usuarios', methods=['GET'])
@jwt_required()
def obtener_usuarios_para_mensaje_route():
    """
    Obtener lista de usuarios para enviar mensajes (solo admin)
    ---
    tags:
      - Notificaciones
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
              email:
                type: string
              telefono:
                type: string
              role:
                type: integer
              role_nombre:
                type: string
      401:
        description: No autorizado
      403:
        description: Solo administradores pueden ver esta lista
      500:
        description: Error del servidor
    """
    return obtener_usuarios_para_mensaje()

@notificaciones_bp.route('/orden/<int:orden_id>', methods=['GET'])
@jwt_required()
def obtener_notificaciones_por_orden_route(orden_id):
    """
    Obtener notificaciones relacionadas con una orden
    ---
    tags:
      - Notificaciones
    parameters:
      - name: orden_id
        in: path
        type: integer
        required: true
        description: ID de la orden
    responses:
      200:
        description: Notificaciones de la orden
        schema:
          type: object
          properties:
            notificaciones:
              type: array
              items:
                $ref: '#/definitions/Notificacion'
            total:
              type: integer
      401:
        description: No autorizado
      403:
        description: No tiene permisos para ver estas notificaciones
      404:
        description: Orden no encontrada
      500:
        description: Error del servidor
    """
    return obtener_notificaciones_por_orden(orden_id)

@notificaciones_bp.route('/pedido/<int:orden_id>/nuevo', methods=['POST'])
@jwt_required()
def notificar_nuevo_pedido_route(orden_id):
    """
    Notificar nuevo pedido (solo admin/interno)
    ---
    tags:
      - Notificaciones
    parameters:
      - name: orden_id
        in: path
        type: integer
        required: true
        description: ID de la orden
    responses:
      200:
        description: Notificación enviada
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
      401:
        description: No autorizado
      404:
        description: Orden no encontrada
      500:
        description: Error del servidor
    """
    return jsonify({
        "success": notificar_nuevo_pedido(orden_id),
        "msg": "Notificación de nuevo pedido enviada"
    }), 200

@notificaciones_bp.route('/pedido/<int:orden_id>/estado', methods=['POST'])
@jwt_required()
def notificar_cambio_estado_pedido_route(orden_id):
    """
    Notificar cambio de estado de pedido (solo admin/interno)
    ---
    tags:
      - Notificaciones
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: orden_id
        in: path
        type: integer
        required: true
        description: ID de la orden
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nuevo_estado
          properties:
            nuevo_estado:
              type: string
              example: "preparando"
              enum: [pendiente, preparando, listo, entregado, cancelado]
              description: Nuevo estado del pedido
    responses:
      200:
        description: Notificación enviada
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
      400:
        description: Se requiere nuevo_estado
      401:
        description: No autorizado
      404:
        description: Orden no encontrada
      500:
        description: Error del servidor
    """
    data = request.get_json()
    nuevo_estado = data.get('nuevo_estado')
    
    if not nuevo_estado:
        return jsonify({"msg": "Se requiere nuevo_estado"}), 400
    
    return jsonify({
        "success": notificar_cambio_estado_pedido(orden_id, nuevo_estado),
        "msg": f"Notificación de cambio de estado a {nuevo_estado} enviada"
    }), 200

@notificaciones_bp.route('/pedido/<int:orden_id>/cancelar', methods=['POST'])
@jwt_required()
def notificar_pedido_cancelado_route(orden_id):
    """
    Notificar pedido cancelado (solo admin/interno)
    ---
    tags:
      - Notificaciones
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: orden_id
        in: path
        type: integer
        required: true
        description: ID de la orden
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            motivo:
              type: string
              example: "Falta de ingredientes"
              description: Motivo de la cancelación
    responses:
      200:
        description: Notificación enviada
        schema:
          type: object
          properties:
            success:
              type: boolean
            msg:
              type: string
      401:
        description: No autorizado
      404:
        description: Orden no encontrada
      500:
        description: Error del servidor
    """
    data = request.get_json() or {}
    motivo = data.get('motivo')
    
    return jsonify({
        "success": notificar_pedido_cancelado(orden_id, motivo),
        "msg": "Notificación de pedido cancelado enviada"
    }), 200