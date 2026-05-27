from flask import Blueprint, request, jsonify
from Controllers.dietasController import (
    get_all_dietas,
    get_single_dieta,
    create_dieta,
    update_dieta,
    delete_dieta,
    search_dietas,
    get_dietas_by_objetivo,
    get_dietas_by_restriccion,
    get_objetivos,
    get_niveles_actividad,
    get_restricciones,
    get_tipos_comida,    
    get_dietas_usuario,
    get_dieta_activa_usuario,
    get_single_dieta_usuario,
    crear_dieta_usuario,
    update_dieta_usuario,
    desactivar_dieta_usuario,    
    get_seguimiento_dieta,
    get_seguimiento_dia,
    actualizar_seguimiento,
    marcar_comida,
    registrar_agua,
    get_progreso_dieta,    
    generar_plan_dieta
)
from flask_jwt_extended import jwt_required

dieta_bp = Blueprint('dieta_bp', __name__)

# ============================================
# RUTAS PÚBLICAS (sin autenticación)
# ============================================

@dieta_bp.route('/objetivos', methods=['GET'])
def get_objetivos_route():
    """
    Obtener lista de objetivos disponibles
    ---
    tags:
      - Dietas
    responses:
      200:
        description: Lista de objetivos
    """
    return get_objetivos()

@dieta_bp.route('/niveles-actividad', methods=['GET'])
def get_niveles_actividad_route():
    """
    Obtener lista de niveles de actividad
    ---
    tags:
      - Dietas
    responses:
      200:
        description: Lista de niveles de actividad
    """
    return get_niveles_actividad()

@dieta_bp.route('/restricciones', methods=['GET'])
def get_restricciones_route():
    """
    Obtener lista de restricciones alimenticias
    ---
    tags:
      - Dietas
    responses:
      200:
        description: Lista de restricciones
    """
    return get_restricciones()

@dieta_bp.route('/tipos-comida', methods=['GET'])
def get_tipos_comida_route():
    """
    Obtener lista de tipos de comida
    ---
    tags:
      - Dietas
    responses:
      200:
        description: Lista de tipos de comida
    """
    return get_tipos_comida()

@dieta_bp.route('/generar-plan', methods=['POST'])
def generar_plan_route():
    """
    Generar un plan de dieta basado en perfil (sin guardar)
    ---
    tags:
      - Dietas
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            perfil:
              type: object
              properties:
                nombre:
                  type: string
                edad:
                  type: number
                peso:
                  type: number
                altura:
                  type: number
                objetivo:
                  type: string
                nivelActividad:
                  type: string
                comidasPorDia:
                  type: number
                restricciones:
                  type: array
                  items:
                    type: string
                enfermedades:
                  type: string
                alergias:
                  type: string
                noGusta:
                  type: string
    responses:
      200:
        description: Plan generado exitosamente
      400:
        description: Error en la solicitud
    """
    return generar_plan_dieta()

# ============================================
# RUTAS PARA DIETAS BASE (protegidas)
# ============================================

@dieta_bp.route('/', methods=['GET'])
@jwt_required()
def index():
    """
    Obtener todas las dietas base
    ---
    tags:
      - Dietas
    parameters:
      - name: only_active
        in: query
        type: boolean
        required: false
        default: true
    responses:
      200:
        description: Lista de dietas base
    """
    return get_all_dietas()

@dieta_bp.route('/search', methods=['GET'])
@jwt_required()
def search_dietas_route():
    """
    Buscar dietas por nombre o descripción
    ---
    tags:
      - Dietas
    parameters:
      - name: query
        in: query
        type: string
        required: false
    responses:
      200:
        description: Dietas encontradas
    """
    return search_dietas()

@dieta_bp.route('/objetivo/<string:objetivo>', methods=['GET'])
@jwt_required()
def get_dietas_by_objetivo_route(objetivo):
    """
    Obtener dietas por objetivo
    ---
    tags:
      - Dietas
    parameters:
      - name: objetivo
        in: path
        type: string
        required: true
    responses:
      200:
        description: Dietas del objetivo especificado
    """
    return get_dietas_by_objetivo(objetivo)

@dieta_bp.route('/restriccion/<string:restriccion>', methods=['GET'])
@jwt_required()
def get_dietas_by_restriccion_route(restriccion):
    """
    Obtener dietas por restricción alimenticia
    ---
    tags:
      - Dietas
    parameters:
      - name: restriccion
        in: path
        type: string
        required: true
    responses:
      200:
        description: Dietas que cumplen la restricción
    """
    return get_dietas_by_restriccion(restriccion)

@dieta_bp.route('/<int:dieta_id>', methods=['GET'])
@jwt_required()
def get_dieta(dieta_id):
    """
    Obtener una dieta base por ID
    ---
    tags:
      - Dietas
    parameters:
      - name: dieta_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dieta encontrada
      404:
        description: Dieta no encontrada
    """
    return get_single_dieta(dieta_id)

@dieta_bp.route('/', methods=['POST'])
@jwt_required()
def add_dieta():
    """
    Crear una nueva dieta base
    ---
    tags:
      - Dietas
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
              example: "Dieta para Perder Peso"
            descripcion:
              type: string
              example: "Plan de 7 días para pérdida de peso saludable"
            objetivo:
              type: string
              enum: [perder_peso, mantener, ganar_musculo, definicion, volumen, saludable]
              default: perder_peso
            duracion_dias:
              type: integer
              default: 7
            calorias_diarias:
              type: integer
              default: 2000
            nivel_actividad:
              type: string
              enum: [sedentario, ligero, moderado, activo, muy_activo]
              default: moderado
            restricciones:
              type: array
              items:
                type: string
              example: ["sin_gluten", "vegetariano"]
            comidas_por_dia:
              type: integer
              default: 3
            plan_alimentacion:
              type: object
            activo:
              type: boolean
              default: true
    responses:
      201:
        description: Dieta creada exitosamente
      400:
        description: Error al crear la dieta
    """
    return create_dieta()

@dieta_bp.route('/<int:dieta_id>', methods=['PUT'])
@jwt_required()
def dieta_update(dieta_id):
    """
    Actualizar una dieta base por ID
    ---
    tags:
      - Dietas
    parameters:
      - name: dieta_id
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
            descripcion:
              type: string
            objetivo:
              type: string
            duracion_dias:
              type: integer
            calorias_diarias:
              type: integer
            nivel_actividad:
              type: string
            restricciones:
              type: array
            comidas_por_dia:
              type: integer
            plan_alimentacion:
              type: object
            activo:
              type: boolean
    responses:
      200:
        description: Dieta actualizada exitosamente
      404:
        description: Dieta no encontrada
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    return update_dieta(dieta_id)

@dieta_bp.route('/<int:dieta_id>', methods=['DELETE'])
@jwt_required()
def dieta_delete(dieta_id):
    """
    Eliminar una dieta base por ID
    ---
    tags:
      - Dietas
    parameters:
      - name: dieta_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dieta eliminada
      404:
        description: Dieta no encontrada
    """
    return delete_dieta(dieta_id)

# ============================================
# RUTAS PARA DIETAS DE USUARIO
# ============================================

@dieta_bp.route('/usuario', methods=['GET'])
@jwt_required()
def get_mis_dietas():
    """
    Obtener todas las dietas del usuario actual
    ---
    tags:
      - Dietas - Usuario
    responses:
      200:
        description: Lista de dietas del usuario
    """
    return get_dietas_usuario()

@dieta_bp.route('/usuario/activa', methods=['GET'])
@jwt_required()
def get_mi_dieta_activa():
    """
    Obtener la dieta activa del usuario actual
    ---
    tags:
      - Dietas - Usuario
    responses:
      200:
        description: Dieta activa del usuario
      404:
        description: No hay dieta activa
    """
    return get_dieta_activa_usuario()

@dieta_bp.route('/usuario', methods=['POST'])
@jwt_required()
def crear_mi_dieta():
    """
    Crear una nueva dieta personalizada para el usuario actual
    ---
    tags:
      - Dietas - Usuario
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - plan_generado
          properties:
            nombre:
              type: string
              example: "Mi Plan de Pérdida de Peso"
            descripcion:
              type: string
            dieta_base_id:
              type: integer
            fecha_fin:
              type: string
              format: date-time
            perfil_usuario:
              type: object
            plan_generado:
              type: object
            mantener_anterior:
              type: boolean
              description: Si es true, mantiene la dieta anterior activa
    responses:
      201:
        description: Dieta creada exitosamente
      400:
        description: Error al crear la dieta
    """
    return crear_dieta_usuario()

@dieta_bp.route('/usuario/<int:dieta_usuario_id>', methods=['GET'])
@jwt_required()
def get_mi_dieta(dieta_usuario_id):
    """
    Obtener una dieta específica del usuario
    ---
    tags:
      - Dietas - Usuario
    parameters:
      - name: dieta_usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dieta encontrada
      404:
        description: Dieta no encontrada
    """
    return get_single_dieta_usuario(dieta_usuario_id)

@dieta_bp.route('/usuario/<int:dieta_usuario_id>', methods=['PUT'])
@jwt_required()
def update_mi_dieta(dieta_usuario_id):
    """
    Actualizar una dieta del usuario
    ---
    tags:
      - Dietas - Usuario
    parameters:
      - name: dieta_usuario_id
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
            descripcion:
              type: string
            fecha_fin:
              type: string
            perfil_usuario:
              type: object
            plan_generado:
              type: object
    responses:
      200:
        description: Dieta actualizada
      404:
        description: Dieta no encontrada
    """
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No se proporcionaron datos'}), 400
    return update_dieta_usuario(dieta_usuario_id, data)

@dieta_bp.route('/usuario/<int:dieta_usuario_id>/desactivar', methods=['PUT'])
@jwt_required()
def desactivar_mi_dieta(dieta_usuario_id):
    """
    Desactivar una dieta del usuario
    ---
    tags:
      - Dietas - Usuario
    parameters:
      - name: dieta_usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Dieta desactivada
      404:
        description: Dieta no encontrada
    """
    return desactivar_dieta_usuario(dieta_usuario_id)

# ============================================
# RUTAS PARA SEGUIMIENTO
# ============================================

@dieta_bp.route('/usuario/<int:dieta_usuario_id>/seguimiento', methods=['GET'])
@jwt_required()
def get_seguimiento(dieta_usuario_id):
    """
    Obtener todo el seguimiento de una dieta
    ---
    tags:
      - Dietas - Seguimiento
    parameters:
      - name: dieta_usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de seguimiento
    """
    return get_seguimiento_dieta(dieta_usuario_id)

@dieta_bp.route('/usuario/<int:dieta_usuario_id>/seguimiento/dia/<int:dia_numero>', methods=['GET'])
@jwt_required()
def get_seguimiento_dia_route(dieta_usuario_id, dia_numero):
    """
    Obtener seguimiento de un día específico
    ---
    tags:
      - Dietas - Seguimiento
    parameters:
      - name: dieta_usuario_id
        in: path
        type: integer
        required: true
      - name: dia_numero
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Seguimiento del día
      404:
        description: Día no encontrado
    """
    return get_seguimiento_dia(dieta_usuario_id, dia_numero)

@dieta_bp.route('/seguimiento/<int:seguimiento_id>', methods=['PUT'])
@jwt_required()
def update_seguimiento(seguimiento_id):
    """
    Actualizar seguimiento de un día
    ---
    tags:
      - Dietas - Seguimiento
    parameters:
      - name: seguimiento_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            completado:
              type: boolean
            comidas_completadas:
              type: array
              items:
                type: integer
            calorias_consumidas:
              type: integer
            agua_consumida:
              type: number
            notas:
              type: string
    responses:
      200:
        description: Seguimiento actualizado
    """
    return actualizar_seguimiento(seguimiento_id)

@dieta_bp.route('/seguimiento/<int:seguimiento_id>/comida', methods=['POST'])
@jwt_required()
def marcar_comida_route(seguimiento_id):
    """
    Marcar una comida como completada/no completada
    ---
    tags:
      - Dietas - Seguimiento
    parameters:
      - name: seguimiento_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - comida_id
          properties:
            comida_id:
              type: integer
            completado:
              type: boolean
              default: true
    responses:
      200:
        description: Comida marcada exitosamente
    """
    return marcar_comida(seguimiento_id)

@dieta_bp.route('/seguimiento/<int:seguimiento_id>/agua', methods=['POST'])
@jwt_required()
def registrar_agua_route(seguimiento_id):
    """
    Registrar consumo de agua
    ---
    tags:
      - Dietas - Seguimiento
    parameters:
      - name: seguimiento_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - litros
          properties:
            litros:
              type: number
              example: 0.5
    responses:
      200:
        description: Agua registrada exitosamente
    """
    return registrar_agua(seguimiento_id)

@dieta_bp.route('/usuario/<int:dieta_usuario_id>/progreso', methods=['GET'])
@jwt_required()
def get_progreso(dieta_usuario_id):
    """
    Obtener el progreso de una dieta
    ---
    tags:
      - Dietas - Seguimiento
    parameters:
      - name: dieta_usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Progreso de la dieta
    """
    return get_progreso_dieta(dieta_usuario_id)

# ============================================
# RUTAS PARA ADMIN (por ID de usuario)
# ============================================

@dieta_bp.route('/admin/usuario/<int:usuario_id>', methods=['GET'])
@jwt_required()
def get_dietas_by_usuario(usuario_id):
    """
    [ADMIN] Obtener dietas de un usuario específico
    ---
    tags:
      - Dietas - Admin
    parameters:
      - name: usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Lista de dietas del usuario
    """
    return get_dietas_usuario(usuario_id)