from flask import Blueprint, request, jsonify
from Controllers.backupController import (
    get_all_backups,
    get_single_backup,
    create_backup,
    delete_backup,
    download_backup,
    restore_backup,
    schedule_backup,
    get_scheduled_backups,
    cancel_scheduled_backup,
    get_database_tables,
    get_backup_stats,
    upload_backup  # <-- IMPORTAR LA NUEVA FUNCIÓN
)
from flask_jwt_extended import jwt_required

backup_bp = Blueprint('backup_bp', __name__)

@backup_bp.route('/', methods=['GET'])
@jwt_required()
def index():
    """
    Obtener todos los respaldos
    ---
    tags:
      - Respaldos
    responses:
      200:
        description: Lista de respaldos
      500:
        description: Error al obtener los respaldos
    """
    return get_all_backups()

@backup_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats_route():
    """
    Obtener estadísticas de respaldos
    ---
    tags:
      - Respaldos
    responses:
      200:
        description: Estadísticas de respaldos
    """
    return get_backup_stats()

@backup_bp.route('/tables', methods=['GET'])
@jwt_required()
def tables_route():
    """
    Obtener lista de tablas de la base de datos
    ---
    tags:
      - Respaldos
    responses:
      200:
        description: Lista de tablas
    """
    return get_database_tables()

@backup_bp.route('/scheduled', methods=['GET'])
@jwt_required()
def scheduled_backups_route():
    """
    Obtener respaldos programados
    ---
    tags:
      - Respaldos
    responses:
      200:
        description: Lista de respaldos programados
    """
    return get_scheduled_backups()

@backup_bp.route('/scheduled/<string:job_id>', methods=['DELETE'])
@jwt_required()
def cancel_scheduled_route(job_id):
    """
    Cancelar respaldo programado
    ---
    tags:
      - Respaldos
    parameters:
      - name: job_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Respaldo cancelado
      400:
        description: Error al cancelar
    """
    return cancel_scheduled_backup(job_id)

@backup_bp.route('/<int:backup_id>', methods=['GET'])
@jwt_required()
def get_backup(backup_id):
    """
    Obtener un respaldo por ID
    ---
    tags:
      - Respaldos
    parameters:
      - name: backup_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Respaldo encontrado
      404:
        description: Respaldo no encontrado
    """
    return get_single_backup(backup_id)

@backup_bp.route('/create', methods=['POST'])
@jwt_required()
def backup_create():
    """
    Crear un nuevo respaldo
    ---
    tags:
      - Respaldos
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            tables:
              type: array
              items:
                type: string
              description: Lista de tablas para respaldo parcial
            custom_name:
              type: string
              description: Nombre personalizado para el respaldo
    responses:
      201:
        description: Respaldo creado exitosamente
      400:
        description: Error al crear el respaldo
      500:
        description: Error interno del servidor
    """
    return create_backup()

# NUEVO ENDPOINT: UPLOAD BACKUP
@backup_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_backup_route():
    """
    Subir/Importar un respaldo existente
    ---
    tags:
      - Respaldos
    consumes:
      - multipart/form-data
    parameters:
      - name: backup_file
        in: formData
        type: file
        required: true
        description: Archivo de respaldo (.sql, .sql.gz, .gz)
    responses:
      201:
        description: Respaldo importado exitosamente
      400:
        description: Error en el archivo
      500:
        description: Error interno del servidor
    """
    return upload_backup()

@backup_bp.route('/schedule', methods=['POST'])
@jwt_required()
def schedule_route():
    """
    Programar respaldo automático
    ---
    tags:
      - Respaldos
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            hour:
              type: integer
              example: 2
            minute:
              type: integer
              example: 0
            days_of_week:
              type: array
              items:
                type: integer
              example: [0, 1, 2, 3, 4, 5, 6]
            backup_type:
              type: string
              enum: [full, partial]
            tables:
              type: array
              items:
                type: string
    responses:
      200:
        description: Respaldo programado
      400:
        description: Error en los datos
    """
    return schedule_backup()

@backup_bp.route('/<int:backup_id>/download', methods=['GET'])
@jwt_required()
def download_backup_route(backup_id):
    """
    Descargar archivo de respaldo
    ---
    tags:
      - Respaldos
    parameters:
      - name: backup_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Archivo de respaldo
      404:
        description: Respaldo no encontrado
    """
    return download_backup(backup_id)

@backup_bp.route('/<int:backup_id>/restore', methods=['POST'])
@jwt_required()
def restore_backup_route(backup_id):
    """
    Restaurar base de datos desde respaldo
    ---
    tags:
      - Respaldos
    parameters:
      - name: backup_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - confirm
          properties:
            confirm:
              type: boolean
              example: true
    responses:
      200:
        description: Base de datos restaurada
      400:
        description: Confirmación requerida
      500:
        description: Error en restauración
    """
    return restore_backup(backup_id)

@backup_bp.route('/<int:backup_id>', methods=['DELETE'])
@jwt_required()
def backup_delete(backup_id):
    """
    Eliminar un respaldo por ID
    ---
    tags:
      - Respaldos
    parameters:
      - name: backup_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Respaldo eliminado
      404:
        description: Respaldo no encontrado
    """
    return delete_backup(backup_id)