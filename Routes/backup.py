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
    upload_backup,
    generate_admin_backup_code,
    regenerate_backup_code,
    verify_backup_code_only
)
from Controllers.diagramaController import (
    exportar_diagrama_sql,
    generar_diagrama,
    get_database_stats,
    comparar_estructuras,
    exportar_diagrama_json
)

from flask_jwt_extended import jwt_required

backup_bp = Blueprint('backup_bp', __name__)

# Agregar manejador CORS
@backup_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept, X-Backup-Code, X-User-Id')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# ============================================
# RUTAS DE RESPALDOS
# ============================================

@backup_bp.route('/', methods=['GET'])
@jwt_required()
def index():
    """
    Obtener todos los respaldos
    ---
    tags:
      - Respaldos
    security:
      - Bearer: []
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
    security:
      - Bearer: []
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
    security:
      - Bearer: []
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
    security:
      - Bearer: []
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
    security:
      - Bearer: []
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

@backup_bp.route('/<string:backup_id>', methods=['GET'])
@jwt_required()
def get_backup(backup_id):
    """
    Obtener un respaldo por ID
    ---
    tags:
      - Respaldos
    security:
      - Bearer: []
    parameters:
      - name: backup_id
        in: path
        type: string
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
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            backup_code:
              type: string
              description: Código único de respaldo
              required: true
            user_id:
              type: string
              description: ID del usuario
              required: true
            tables:
              type: array
              items:
                type: string
              description: Lista de tablas para respaldo parcial (MySQL)
            collections:
              type: array
              items:
                type: string
              description: Lista de colecciones para respaldo parcial (MongoDB)
            custom_name:
              type: string
              description: Nombre personalizado para el respaldo
    responses:
      201:
        description: Respaldo creado exitosamente
      401:
        description: Código inválido o no proporcionado
      500:
        description: Error interno del servidor
    """
    return create_backup()

@backup_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_backup_route():
    """
    Subir/Importar un respaldo existente
    ---
    tags:
      - Respaldos
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - name: backup_file
        in: formData
        type: file
        required: true
        description: Archivo de respaldo (.sql, .sql.gz, .json, .json.gz)
      - name: backup_code
        in: formData
        type: string
        required: true
        description: Código único de respaldo
      - name: user_id
        in: formData
        type: string
        required: true
        description: ID del usuario
    responses:
      201:
        description: Respaldo importado exitosamente
      401:
        description: Código inválido o no proporcionado
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
    security:
      - Bearer: []
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

@backup_bp.route('/<string:backup_id>/download', methods=['GET'])
@jwt_required()
def download_backup_route(backup_id):
    """
    Descargar archivo de respaldo
    ---
    tags:
      - Respaldos
    security:
      - Bearer: []
    parameters:
      - name: backup_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Archivo de respaldo
      404:
        description: Respaldo no encontrado
    """
    return download_backup(backup_id)

@backup_bp.route('/<string:backup_id>/restore', methods=['POST'])
@jwt_required()
def restore_backup_route(backup_id):
    """
    Restaurar base de datos desde respaldo
    ---
    tags:
      - Respaldos
    security:
      - Bearer: []
    parameters:
      - name: backup_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - confirm
            - backup_code
            - user_id
          properties:
            confirm:
              type: boolean
              example: true
            backup_code:
              type: string
              description: Código único de respaldo
            user_id:
              type: string
              description: ID del usuario
    responses:
      200:
        description: Base de datos restaurada
      400:
        description: Confirmación requerida
      401:
        description: Código inválido o no proporcionado
      500:
        description: Error en restauración
    """
    return restore_backup(backup_id)

@backup_bp.route('/<string:backup_id>', methods=['DELETE'])
@jwt_required()
def backup_delete(backup_id):
    """
    Eliminar un respaldo por ID
    ---
    tags:
      - Respaldos
    security:
      - Bearer: []
    parameters:
      - name: backup_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            backup_code:
              type: string
              required: true
            user_id:
              type: string
              required: true
    responses:
      200:
        description: Respaldo eliminado
      401:
        description: Código inválido o no proporcionado
      404:
        description: Respaldo no encontrado
    """
    return delete_backup(backup_id)

# ============================================
# RUTAS PARA CÓDIGO DE RESPALDO
# ============================================

@backup_bp.route('/generate-code', methods=['POST'])
@jwt_required()
def generate_code_route():
    """
    Generar código de respaldo para administrador (solo si no tiene)
    ---
    tags:
      - Respaldos - Código
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
              required: true
    responses:
      200:
        description: Código generado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            backup_code:
              type: string
      400:
        description: Ya tiene un código o ID no proporcionado
      403:
        description: No autorizado (no es administrador)
      404:
        description: Usuario no encontrado
    """
    return generate_admin_backup_code()

@backup_bp.route('/regenerate-code', methods=['POST'])
@jwt_required()
def regenerate_code_route():
    """
    Regenerar código de respaldo para administrador (sobrescribe el anterior)
    ---
    tags:
      - Respaldos - Código
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: string
              required: true
    responses:
      200:
        description: Código regenerado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            backup_code:
              type: string
      400:
        description: ID no proporcionado
      403:
        description: No autorizado (no es administrador)
      404:
        description: Usuario no encontrado
    """
    return regenerate_backup_code()

# ============================================
# RUTAS PARA DIAGRAMAS
# ============================================

@backup_bp.route('/diagrama', methods=['GET'])
@jwt_required()
def get_diagrama_backup():
    """
    Generar diagrama entidad-relación de la base de datos
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Diagrama generado
    """
    return generar_diagrama()

@backup_bp.route('/diagrama/exportar/json', methods=['GET'])
@jwt_required()
def exportar_diagrama_json_backup():
    """
    Exportar diagrama como JSON
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Archivo JSON
    """
    return exportar_diagrama_json()

@backup_bp.route('/diagrama/exportar/sql', methods=['GET'])
@jwt_required()
def exportar_diagrama_sql_backup():
    """
    Exportar diagrama como SQL
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Archivo SQL
    """
    return exportar_diagrama_sql()

# ============================================
# RUTAS DE ESTADÍSTICAS Y COMPARACIÓN
# ============================================

@backup_bp.route('/stats/database', methods=['GET'])
@jwt_required()
def get_stats_backup():
    """
    Obtener estadísticas de la base de datos
    ---
    tags:
      - Backups - Estadísticas
    security:
      - Bearer: []
    responses:
      200:
        description: Estadísticas
    """
    return get_database_stats()

@backup_bp.route('/comparar', methods=['GET'])
@jwt_required()
def comparar_bd_backup():
    """
    Comparar MySQL vs MongoDB
    ---
    tags:
      - Backups - Comparación
    security:
      - Bearer: []
    responses:
      200:
        description: Comparación
    """
    return comparar_estructuras()

@backup_bp.route('/verify-code', methods=['POST'])
@jwt_required()
def verify_code_route():
    """
    Verificar código de respaldo
    ---
    tags:
      - Respaldos - Código
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            backup_code:
              type: string
              required: true
            user_id:
              type: string
              required: true
    responses:
      200:
        description: Código válido
      401:
        description: Código inválido o no proporcionado
    """
    return verify_backup_code_only()