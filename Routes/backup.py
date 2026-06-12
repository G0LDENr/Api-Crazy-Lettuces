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
    exportar_diagrama_json,
    generar_diagrama_copo_nieve,
    exportar_diagrama_copo_nieve_json,
    exportar_diagrama_copo_nieve_sql
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            backups:
              type: array
              items:
                type: object
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            stats:
              type: object
      500:
        description: Error al obtener estadísticas
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            tables:
              type: array
              items:
                type: string
      500:
        description: Error al obtener tablas
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            scheduled_jobs:
              type: array
              items:
                type: object
      500:
        description: Error al obtener respaldos programados
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
        description: ID del trabajo programado
    responses:
      200:
        description: Respaldo cancelado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: Error al cancelar el respaldo
      404:
        description: Trabajo no encontrado
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
        description: ID del respaldo
    responses:
      200:
        description: Respaldo encontrado
        schema:
          type: object
          properties:
            success:
              type: boolean
            backup:
              type: object
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            backup:
              type: object
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            backup:
              type: object
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
              description: Hora del día (0-23)
            minute:
              type: integer
              example: 0
              description: Minuto de la hora (0-59)
            days_of_week:
              type: array
              items:
                type: integer
              example: [0, 1, 2, 3, 4, 5, 6]
              description: Días de la semana (0=domingo, 6=sábado)
            backup_type:
              type: string
              enum: [full, partial]
              description: Tipo de respaldo (completo o parcial)
            tables:
              type: array
              items:
                type: string
              description: Tablas para respaldo parcial
    responses:
      200:
        description: Respaldo programado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            job_id:
              type: string
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
        description: ID del respaldo
    responses:
      200:
        description: Archivo de respaldo
        schema:
          type: file
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
        description: ID del respaldo
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
              description: Confirmación de restauración
            backup_code:
              type: string
              description: Código único de respaldo
            user_id:
              type: string
              description: ID del usuario
    responses:
      200:
        description: Base de datos restaurada exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
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
        description: ID del respaldo
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
        description: Respaldo eliminado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
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
              description: ID del usuario
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
              description: ID del usuario
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
              description: Código de respaldo a verificar
            user_id:
              type: string
              required: true
              description: ID del usuario
    responses:
      200:
        description: Código válido
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            valid:
              type: boolean
      401:
        description: Código inválido o no proporcionado
    """
    return verify_backup_code_only()


# ============================================
# RUTAS PARA DIAGRAMAS ENTIDAD-RELACIÓN (ER)
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
        description: Diagrama ER generado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: object
              description: Estructura del diagrama ER
      401:
        description: No autorizado
      500:
        description: Error al generar el diagrama
    """
    return generar_diagrama()


@backup_bp.route('/diagrama/exportar/json', methods=['GET'])
@jwt_required()
def exportar_diagrama_json_backup():
    """
    Exportar diagrama ER como archivo JSON
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Archivo JSON descargado
        schema:
          type: file
          format: json
      401:
        description: No autorizado
      500:
        description: Error al exportar
    """
    return exportar_diagrama_json()


@backup_bp.route('/diagrama/exportar/sql', methods=['GET'])
@jwt_required()
def exportar_diagrama_sql_backup():
    """
    Exportar diagrama ER como script SQL (solo MySQL)
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Archivo SQL descargado
        schema:
          type: file
          format: sql
      400:
        description: SQL solo disponible para MySQL
      401:
        description: No autorizado
      500:
        description: Error al exportar
    """
    return exportar_diagrama_sql()


# ============================================
# RUTAS PARA DIAGRAMAS DE COPO DE NIEVE (SNOWFLAKE)
# ============================================

@backup_bp.route('/diagrama/copo-nieve', methods=['GET'])
@jwt_required()
def get_diagrama_copo_nieve_backup():
    """
    Generar diagrama de copo de nieve (Snowflake Schema)
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Diagrama de copo de nieve generado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: object
              properties:
                tipo_diagrama:
                  type: string
                  example: SNOWFLAKE_SCHEMA
                tipo_bd:
                  type: string
                  example: MySQL
                fecha_generacion:
                  type: string
                  format: date-time
                descripcion:
                  type: string
                estructura:
                  type: object
                  properties:
                    fact_table:
                      type: object
                    dimensions:
                      type: array
                    sub_dimensions:
                      type: array
                    relaciones:
                      type: array
      401:
        description: No autorizado
      500:
        description: Error al generar el diagrama
    """
    return generar_diagrama_copo_nieve()


@backup_bp.route('/diagrama/copo-nieve/exportar/json', methods=['GET'])
@jwt_required()
def exportar_diagrama_copo_nieve_json_backup():
    """
    Exportar diagrama de copo de nieve como archivo JSON
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Archivo JSON descargado
        schema:
          type: file
          format: json
        examples:
          application/json:
            description: Diagrama de copo de nieve en formato JSON
      401:
        description: No autorizado
      500:
        description: Error al exportar
    """
    return exportar_diagrama_copo_nieve_json()


@backup_bp.route('/diagrama/copo-nieve/exportar/sql', methods=['GET'])
@jwt_required()
def exportar_diagrama_copo_nieve_sql_backup():
    """
    Exportar diagrama de copo de nieve como script SQL (solo MySQL)
    ---
    tags:
      - Backups - Diagramas
    security:
      - Bearer: []
    responses:
      200:
        description: Archivo SQL descargado
        schema:
          type: file
          format: sql
        examples:
          application/sql:
            description: Script SQL con vistas materializadas y consultas de ejemplo
      400:
        description: SQL solo disponible para MySQL
      401:
        description: No autorizado
      500:
        description: Error al exportar
    """
    return exportar_diagrama_copo_nieve_sql()


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
        description: Estadísticas de la base de datos
        schema:
          type: object
          properties:
            success:
              type: boolean
            stats:
              type: object
              properties:
                tipo_bd:
                  type: string
                fecha:
                  type: string
                total_registros:
                  type: integer
                tamanio_aprox_mb:
                  type: number
                tablas:
                  type: array
      401:
        description: No autorizado
      500:
        description: Error al obtener estadísticas
    """
    return get_database_stats()


@backup_bp.route('/comparar', methods=['GET'])
@jwt_required()
def comparar_bd_backup():
    """
    Comparar estructuras de MySQL vs MongoDB
    ---
    tags:
      - Backups - Comparación
    security:
      - Bearer: []
    responses:
      200:
        description: Comparación entre MySQL y MongoDB
        schema:
          type: object
          properties:
            success:
              type: boolean
            comparacion:
              type: object
              properties:
                fecha:
                  type: string
                mysql_disponible:
                  type: boolean
                mongodb_disponible:
                  type: boolean
                mysql:
                  type: object
                mongodb:
                  type: object
                errores:
                  type: array
      401:
        description: No autorizado
      500:
        description: Error al comparar estructuras
    """
    return comparar_estructuras()