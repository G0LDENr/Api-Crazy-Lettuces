from Models.Dietas import Dieta, DietaSQL, DietaUsuarioSQL, SeguimientoDietaSQL
from Models.User import User
from config import DB_TYPE, db_sql
from flask import jsonify, request
from datetime import datetime
import json
from bson.objectid import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity

def get_all_dietas():
    """Obtener todas las dietas base"""
    try:
        only_active = request.args.get('only_active', 'true').lower() == 'true'
        dietas = Dieta.get_all_dietas(only_active=only_active)
        
        dietas_list = []
        for dieta in dietas:
            if DB_TYPE == 'mysql':
                dietas_list.append(dieta.to_dict())
            else:
                dietas_list.append(Dieta.to_dict(dieta, tipo='base'))
        
        return jsonify({
            'success': True,
            'data': dietas_list,
            'total': len(dietas_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dietas: {str(e)}'
        }), 500

def get_single_dieta(dieta_id):
    """Obtener una dieta base por ID"""
    try:
        dieta = Dieta.find_by_id(dieta_id)
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        if DB_TYPE == 'mysql':
            return jsonify({
                'success': True,
                'data': dieta.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': Dieta.to_dict(dieta, tipo='base')
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dieta: {str(e)}'
        }), 500

def create_dieta():
    """Crear una nueva dieta base"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        # Validar campos requeridos
        required_fields = ['nombre']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'msg': f'El campo {field} es requerido'
                }), 400
        
        # Crear la dieta
        dieta_id = Dieta.create_dieta(data)
        
        return jsonify({
            'success': True,
            'msg': 'Dieta creada exitosamente',
            'id': dieta_id
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al crear dieta: {str(e)}'
        }), 500

def update_dieta(dieta_id):
    """Actualizar una dieta base"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        # Verificar que la dieta existe
        dieta = Dieta.find_by_id(dieta_id)
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        # Actualizar
        result = Dieta.update_dieta(dieta_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Dieta actualizada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo actualizar la dieta'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al actualizar dieta: {str(e)}'
        }), 500

def delete_dieta(dieta_id):
    """Eliminar una dieta base"""
    try:
        # Verificar que la dieta existe
        dieta = Dieta.find_by_id(dieta_id)
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        result = Dieta.delete_dieta(dieta_id)
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Dieta eliminada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo eliminar la dieta'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al eliminar dieta: {str(e)}'
        }), 500

def search_dietas():
    """Buscar dietas por nombre o descripción"""
    try:
        query = request.args.get('query', '')
        dietas = Dieta.search_dietas(query)
        
        dietas_list = []
        for dieta in dietas:
            if DB_TYPE == 'mysql':
                dietas_list.append(dieta.to_dict())
            else:
                dietas_list.append(Dieta.to_dict(dieta, tipo='base'))
        
        return jsonify({
            'success': True,
            'data': dietas_list,
            'total': len(dietas_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al buscar dietas: {str(e)}'
        }), 500

def get_dietas_by_objetivo(objetivo):
    """Obtener dietas por objetivo"""
    try:
        dietas = Dieta.get_by_objetivo(objetivo)
        
        dietas_list = []
        for dieta in dietas:
            if DB_TYPE == 'mysql':
                dietas_list.append(dieta.to_dict())
            else:
                dietas_list.append(Dieta.to_dict(dieta, tipo='base'))
        
        return jsonify({
            'success': True,
            'data': dietas_list,
            'total': len(dietas_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dietas por objetivo: {str(e)}'
        }), 500

def get_dietas_by_restriccion(restriccion):
    """Obtener dietas por restricción"""
    try:
        dietas = Dieta.get_by_restriccion(restriccion)
        
        dietas_list = []
        for dieta in dietas:
            if DB_TYPE == 'mysql':
                dietas_list.append(dieta.to_dict())
            else:
                dietas_list.append(Dieta.to_dict(dieta, tipo='base'))
        
        return jsonify({
            'success': True,
            'data': dietas_list,
            'total': len(dietas_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dietas por restricción: {str(e)}'
        }), 500

def get_objetivos():
    """Obtener lista de objetivos disponibles"""
    return jsonify({
        'success': True,
        'data': Dieta.OBJETIVOS
    }), 200

def get_niveles_actividad():
    """Obtener lista de niveles de actividad"""
    return jsonify({
        'success': True,
        'data': Dieta.NIVELES_ACTIVIDAD
    }), 200

def get_restricciones():
    """Obtener lista de restricciones alimenticias"""
    return jsonify({
        'success': True,
        'data': Dieta.RESTRICCIONES
    }), 200

def get_tipos_comida():
    """Obtener lista de tipos de comida"""
    return jsonify({
        'success': True,
        'data': Dieta.TIPOS_COMIDA
    }), 200

# ============================================
# DIETAS DE USUARIO
# ============================================

def get_dietas_usuario(usuario_id=None):
    """Obtener dietas de un usuario (si no se especifica, usa el token)"""
    try:
        if not usuario_id:
            # Obtener usuario del token
            current_user = get_jwt_identity()
            if isinstance(current_user, dict) and 'id' in current_user:
                usuario_id = current_user['id']
            elif isinstance(current_user, (int, str)):
                usuario_id = current_user
            else:
                return jsonify({
                    'success': False,
                    'msg': 'No se pudo identificar al usuario'
                }), 401
        
        dietas = Dieta.get_dietas_by_usuario(usuario_id)
        
        dietas_list = []
        for dieta in dietas:
            if DB_TYPE == 'mysql':
                dietas_list.append(dieta.to_dict())
            else:
                dietas_list.append(Dieta.to_dict(dieta, tipo='usuario'))
        
        return jsonify({
            'success': True,
            'data': dietas_list,
            'total': len(dietas_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dietas del usuario: {str(e)}'
        }), 500

def get_dieta_activa_usuario():
    """Obtener la dieta activa del usuario actual"""
    try:
        # Obtener usuario del token
        current_user = get_jwt_identity()
        if isinstance(current_user, dict) and 'id' in current_user:
            usuario_id = current_user['id']
        elif isinstance(current_user, (int, str)):
            usuario_id = current_user
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo identificar al usuario'
            }), 401
        
        dieta = Dieta.get_dieta_activa_usuario(usuario_id)
        
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'No tienes una dieta activa'
            }), 404
        
        if DB_TYPE == 'mysql':
            return jsonify({
                'success': True,
                'data': dieta.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': Dieta.to_dict(dieta, tipo='usuario')
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dieta activa: {str(e)}'
        }), 500

def get_single_dieta_usuario(dieta_usuario_id):
    """Obtener una dieta de usuario por ID"""
    try:
        # Obtener usuario del token
        current_user = get_jwt_identity()
        if isinstance(current_user, dict) and 'id' in current_user:
            usuario_id_actual = current_user['id']
        elif isinstance(current_user, (int, str)):
            usuario_id_actual = current_user
        else:
            usuario_id_actual = None
        
        dieta = Dieta.find_usuario_dieta_by_id(dieta_usuario_id)
        
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        # Verificar que la dieta pertenece al usuario (a menos que sea admin)
        if DB_TYPE == 'mysql':
            if dieta.usuario_id != usuario_id_actual:
                # Verificar si es admin (esto depende de cómo manejes roles)
                # Por ahora, permitimos acceso
                pass
        else:
            if dieta.get('usuario_id') != usuario_id_actual:
                pass
        
        if DB_TYPE == 'mysql':
            return jsonify({
                'success': True,
                'data': dieta.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': Dieta.to_dict(dieta, tipo='usuario')
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener dieta: {str(e)}'
        }), 500

def crear_dieta_usuario():
    """Crear una nueva dieta personalizada para el usuario"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        # Obtener usuario del token
        current_user = get_jwt_identity()
        if isinstance(current_user, dict) and 'id' in current_user:
            usuario_id = current_user['id']
        elif isinstance(current_user, (int, str)):
            usuario_id = current_user
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo identificar al usuario'
            }), 401
        
        # Validar campos requeridos
        if 'nombre' not in data:
            return jsonify({
                'success': False,
                'msg': 'El campo nombre es requerido'
            }), 400
        
        if 'plan_generado' not in data:
            return jsonify({
                'success': False,
                'msg': 'El campo plan_generado es requerido'
            }), 400
        
        # Verificar si ya tiene una dieta activa
        dieta_activa = Dieta.get_dieta_activa_usuario(usuario_id)
        if dieta_activa:
            # Desactivar la dieta anterior si se pide
            if not data.get('mantener_anterior', False):
                if DB_TYPE == 'mysql':
                    dieta_activa.activo = False
                    db_sql.session.commit()
                else:
                    Dieta.update_dieta_usuario(dieta_activa['_id'], {'activo': False})
        
        # Crear la dieta
        dieta_id = Dieta.crear_dieta_usuario(usuario_id, data)
        
        return jsonify({
            'success': True,
            'msg': 'Dieta personalizada creada exitosamente',
            'id': dieta_id
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al crear dieta personalizada: {str(e)}'
        }), 500

def update_dieta_usuario(dieta_usuario_id):
    """Actualizar una dieta de usuario"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        # Verificar que la dieta existe
        dieta = Dieta.find_usuario_dieta_by_id(dieta_usuario_id)
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        # Actualizar
        result = Dieta.update_dieta_usuario(dieta_usuario_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Dieta actualizada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo actualizar la dieta'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al actualizar dieta: {str(e)}'
        }), 500

def desactivar_dieta_usuario(dieta_usuario_id):
    """Desactivar una dieta de usuario"""
    try:
        # Verificar que la dieta existe
        dieta = Dieta.find_usuario_dieta_by_id(dieta_usuario_id)
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        result = Dieta.update_dieta_usuario(dieta_usuario_id, {'activo': False})
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Dieta desactivada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo desactivar la dieta'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al desactivar dieta: {str(e)}'
        }), 500

# ============================================
# SEGUIMIENTO DE DIETA
# ============================================

def get_seguimiento_dieta(dieta_usuario_id):
    """Obtener todo el seguimiento de una dieta"""
    try:
        seguimientos = Dieta.get_seguimiento_by_dieta(dieta_usuario_id)
        
        seguimientos_list = []
        for seg in seguimientos:
            if DB_TYPE == 'mysql':
                seguimientos_list.append(seg.to_dict())
            else:
                seguimientos_list.append(Dieta.to_dict(seg, tipo='seguimiento'))
        
        return jsonify({
            'success': True,
            'data': seguimientos_list,
            'total': len(seguimientos_list)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener seguimiento: {str(e)}'
        }), 500

def get_seguimiento_dia(dieta_usuario_id, dia_numero):
    """Obtener seguimiento de un día específico"""
    try:
        seguimiento = Dieta.get_seguimiento_dia(dieta_usuario_id, dia_numero)
        
        if not seguimiento:
            return jsonify({
                'success': False,
                'msg': f'Seguimiento para el día {dia_numero} no encontrado'
            }), 404
        
        if DB_TYPE == 'mysql':
            return jsonify({
                'success': True,
                'data': seguimiento.to_dict()
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': Dieta.to_dict(seguimiento, tipo='seguimiento')
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener seguimiento: {str(e)}'
        }), 500

def actualizar_seguimiento(seguimiento_id):
    """Actualizar seguimiento de un día"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        result = Dieta.actualizar_seguimiento(seguimiento_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Seguimiento actualizado exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo actualizar el seguimiento'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al actualizar seguimiento: {str(e)}'
        }), 500

def marcar_comida(seguimiento_id):
    """Marcar una comida como completada/no completada"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        comida_id = data.get('comida_id')
        completado = data.get('completado', True)
        
        if comida_id is None:
            return jsonify({
                'success': False,
                'msg': 'El campo comida_id es requerido'
            }), 400
        
        result = Dieta.marcar_comida_completada(seguimiento_id, comida_id, completado)
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Comida marcada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo marcar la comida'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al marcar comida: {str(e)}'
        }), 500

def registrar_agua(seguimiento_id):
    """Registrar consumo de agua"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        litros = data.get('litros')
        if litros is None:
            return jsonify({
                'success': False,
                'msg': 'El campo litros es requerido'
            }), 400
        
        result = Dieta.registrar_agua(seguimiento_id, float(litros))
        
        if result:
            return jsonify({
                'success': True,
                'msg': 'Agua registrada exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'msg': 'No se pudo registrar el agua'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al registrar agua: {str(e)}'
        }), 500

def get_progreso_dieta(dieta_usuario_id):
    """Obtener el progreso de una dieta"""
    try:
        dieta = Dieta.find_usuario_dieta_by_id(dieta_usuario_id)
        if not dieta:
            return jsonify({
                'success': False,
                'msg': 'Dieta no encontrada'
            }), 404
        
        seguimientos = Dieta.get_seguimiento_by_dieta(dieta_usuario_id)
        
        total_dias = len(seguimientos)
        dias_completados = 0
        calorias_totales = 0
        agua_total = 0
        
        for seg in seguimientos:
            if DB_TYPE == 'mysql':
                if seg.completado:
                    dias_completados += 1
                calorias_totales += seg.calorias_consumidas
                agua_total += seg.agua_consumida
            else:
                if seg.get('completado', False):
                    dias_completados += 1
                calorias_totales += seg.get('calorias_consumidas', 0)
                agua_total += seg.get('agua_consumida', 0)
        
        progreso = int((dias_completados / total_dias) * 100) if total_dias > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'progreso': progreso,
                'dias_completados': dias_completados,
                'total_dias': total_dias,
                'calorias_totales_consumidas': calorias_totales,
                'agua_total_consumida': round(agua_total, 2),
                'promedio_calorias_dia': int(calorias_totales / total_dias) if total_dias > 0 else 0,
                'promedio_agua_dia': round(agua_total / total_dias, 2) if total_dias > 0 else 0
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al obtener progreso: {str(e)}'
        }), 500

# ============================================
# UTILIDADES
# ============================================

def generar_plan_dieta():
    """Endpoint para generar un plan de dieta basado en perfil (sin guardar)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'msg': 'No se proporcionaron datos'}), 400
        
        # Aquí iría la lógica de generación de dieta
        # Por ahora, devolvemos un plan de ejemplo
        
        from datetime import datetime, timedelta
        
        # Datos básicos del perfil
        perfil = data.get('perfil', {})
        objetivo = perfil.get('objetivo', 'perder_peso')
        nivel_actividad = perfil.get('nivelActividad', 'moderado')
        comidas_por_dia = int(perfil.get('comidasPorDia', 3))
        
        # Calcular calorías (simplificado)
        peso = float(perfil.get('peso', 70))
        altura = float(perfil.get('altura', 170))
        edad = float(perfil.get('edad', 30))
        
        # TMB aproximada
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
        
        factores = {
            'sedentario': 1.2,
            'ligero': 1.375,
            'moderado': 1.55,
            'activo': 1.725,
            'muy_activo': 1.9
        }
        
        calorias = tmb * factores.get(nivel_actividad, 1.55)
        
        if objetivo == 'perder_peso':
            calorias -= 500
        elif objetivo == 'ganar_musculo':
            calorias += 300
        
        calorias = max(1200, min(4000, int(calorias)))
        
        # Generar días
        dias = []
        for i in range(7):
            fecha = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            fecha_formateada = (datetime.now() + timedelta(days=i)).strftime('%A, %d de %B')
            
            comidas = []
            tipos = ['Desayuno', 'Colación AM', 'Comida', 'Colación PM', 'Cena']
            
            for j in range(min(comidas_por_dia, len(tipos))):
                comida = {
                    'id': j,
                    'tipo': tipos[j],
                    'hora': f'{7 + j*3:02d}:00',
                    'completado': False,
                    'calorias': int(calorias / comidas_por_dia),
                    'items': []
                }
                
                # Items de ejemplo
                if j == 0:  # Desayuno
                    comida['items'] = [
                        {
                            'nombre': 'Avena con frutas',
                            'cantidad': '1 taza',
                            'preparacion': 'Cocida con leche de almendras',
                            'calorias': 250
                        },
                        {
                            'nombre': 'Huevos revueltos',
                            'cantidad': '2 unidades',
                            'preparacion': 'Con espinacas',
                            'calorias': 180
                        }
                    ]
                elif j == 2:  # Comida
                    comida['items'] = [
                        {
                            'nombre': 'Pechuga de pollo',
                            'cantidad': '150g',
                            'preparacion': 'A la plancha',
                            'calorias': 220
                        },
                        {
                            'nombre': 'Arroz integral',
                            'cantidad': '1 taza',
                            'preparacion': 'Cocido',
                            'calorias': 200
                        },
                        {
                            'nombre': 'Ensalada mixta',
                            'cantidad': '200g',
                            'preparacion': 'Con vinagreta',
                            'calorias': 100
                        }
                    ]
                elif j == 4:  # Cena
                    comida['items'] = [
                        {
                            'nombre': 'Salmón',
                            'cantidad': '120g',
                            'preparacion': 'Al horno',
                            'calorias': 250
                        },
                        {
                            'nombre': 'Verduras salteadas',
                            'cantidad': '150g',
                            'preparacion': 'Con ajo',
                            'calorias': 80
                        }
                    ]
                else:  # Colaciones
                    comida['items'] = [
                        {
                            'nombre': 'Yogurt griego',
                            'cantidad': '1 unidad',
                            'preparacion': 'Natural',
                            'calorias': 120
                        },
                        {
                            'nombre': 'Frutos secos',
                            'cantidad': '30g',
                            'preparacion': 'Mix',
                            'calorias': 150
                        }
                    ]
                
                comidas.append(comida)
            
            dias.append({
                'dia': i,
                'fecha': fecha,
                'fecha_formateada': fecha_formateada,
                'completado': False,
                'calorias_dia': calorias,
                'comidas': comidas
            })
        
        plan = {
            'perfil': perfil,
            'calorias_diarias': calorias,
            'fecha_inicio': datetime.now().isoformat(),
            'dias': dias
        }
        
        return jsonify({
            'success': True,
            'data': plan
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'msg': f'Error al generar plan: {str(e)}'
        }), 500