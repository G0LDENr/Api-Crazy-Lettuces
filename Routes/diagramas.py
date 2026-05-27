from flask import Blueprint
from Controllers.diagramaController import (
    generar_diagrama,
    exportar_diagrama_json,
    exportar_diagrama_sql,
    get_database_stats,
    comparar_estructuras
)
from flask_jwt_extended import jwt_required

diagrama_bp = Blueprint('diagrama_bp', __name__)

# ============================================
# RUTAS PARA DIAGRAMAS
# ============================================

@diagrama_bp.route('/', methods=['GET'])
@jwt_required()
def get_diagrama():
    """
    Generar diagrama entidad-relación de la base de datos actual
    ---
    tags:
      - Diagramas
    responses:
      200:
        description: Diagrama generado exitosamente
      500:
        description: Error al generar diagrama
    """
    return generar_diagrama()

@diagrama_bp.route('/exportar/json', methods=['GET'])
@jwt_required()
def exportar_json():
    """
    Exportar diagrama como archivo JSON descargable
    ---
    tags:
      - Diagramas
    responses:
      200:
        description: Archivo JSON descargado
      500:
        description: Error al exportar
    """
    return exportar_diagrama_json()

@diagrama_bp.route('/exportar/sql', methods=['GET'])
@jwt_required()
def exportar_sql():
    """
    Exportar diagrama como script SQL (solo MySQL)
    ---
    tags:
      - Diagramas
    responses:
      200:
        description: Archivo SQL descargado
      400:
        description: No disponible para MongoDB
      500:
        description: Error al exportar
    """
    return exportar_diagrama_sql()

@diagrama_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Obtener estadísticas generales de la base de datos
    ---
    tags:
      - Diagramas
    responses:
      200:
        description: Estadísticas obtenidas
      500:
        description: Error al obtener estadísticas
    """
    return get_database_stats()

@diagrama_bp.route('/comparar', methods=['GET'])
@jwt_required()
def comparar():
    """
    Comparar estructura de MySQL y MongoDB (si ambos están disponibles)
    ---
    tags:
      - Diagramas
    responses:
      200:
        description: Comparación generada
      500:
        description: Error al comparar
    """
    return comparar_estructuras()