from Models.Suplementos import Suplemento
from flask import jsonify, request

def get_all_suplementos():
    """
    Obtener todos los suplementos
    """
    try:
        only_active = request.args.get('all', 'false').lower() != 'true'
        suplementos = Suplemento.get_all_suplementos(only_active=only_active)
        suplementos_dict = [Suplemento.to_dict(s) for s in suplementos]
        return jsonify(suplementos_dict), 200
    except Exception as error:
        print(f"Error al obtener suplementos: {error}")
        return jsonify({"msg": "Error al obtener los suplementos"}), 500

def get_single_suplemento(suplemento_id):
    """
    Obtener un suplemento por ID
    """
    try:
        suplemento = Suplemento.find_by_id(suplemento_id)
        if not suplemento:
            return jsonify({"msg": "Suplemento no encontrado"}), 404
        
        suplemento_dict = Suplemento.to_dict(suplemento)
        return jsonify(suplemento_dict), 200
    except Exception as error:
        print(f"Error al obtener el suplemento: {error}")
        return jsonify({"msg": "Error al obtener el suplemento"}), 500

def create_suplemento(nombre, descripcion, precio, categoria='quemadores', 
                     presentacion='polvo', beneficios='', modo_uso='', stock=0, activo=True):
    """
    Crear nuevo suplemento
    """
    try:
        # Validaciones básicas
        if not nombre or not descripcion or precio is None:
            return jsonify({"msg": "Nombre, descripción y precio son requeridos"}), 400
        
        if precio < 0:
            return jsonify({"msg": "El precio no puede ser negativo"}), 400
        
        if stock < 0:
            return jsonify({"msg": "El stock no puede ser negativo"}), 400
        
        # Verificar si ya existe un suplemento con el mismo nombre
        existing = Suplemento.find_by_name(nombre)
        if existing:
            return jsonify({"msg": "Ya existe un suplemento con ese nombre"}), 400
        
        # Validar categoría
        if categoria not in Suplemento.CATEGORIAS:
            return jsonify({
                "msg": f"Categoría no válida. Categorías permitidas: {', '.join(Suplemento.CATEGORIAS.keys())}"
            }), 400
        
        # Validar presentación
        if presentacion not in Suplemento.PRESENTACIONES:
            return jsonify({
                "msg": f"Presentación no válida. Presentaciones permitidas: {', '.join(Suplemento.PRESENTACIONES.keys())}"
            }), 400
        
        # Crear nuevo suplemento
        suplemento_data = {
            'nombre': nombre,
            'descripcion': descripcion,
            'precio': precio,
            'categoria': categoria,
            'presentacion': presentacion,
            'beneficios': beneficios,
            'modo_uso': modo_uso,
            'stock': stock,
            'activo': activo
        }
        
        suplemento_id = Suplemento.create_suplemento(suplemento_data)
        suplemento = Suplemento.find_by_id(suplemento_id)
        suplemento_dict = Suplemento.to_dict(suplemento)
        
        return jsonify({
            "msg": "Suplemento creado exitosamente",
            "suplemento": suplemento_dict
        }), 201
        
    except Exception as error:
        print(f"Error al crear el suplemento: {error}")
        return jsonify({"msg": "Error al crear el suplemento"}), 500

def delete_suplemento(suplemento_id):
    """Eliminar un suplemento por ID"""
    try:
        existing = Suplemento.find_by_id(suplemento_id)
        if not existing:
            return jsonify({"msg": "Suplemento no encontrado"}), 404
        
        result = Suplemento.delete_suplemento(suplemento_id)
        
        if result:
            return jsonify({"msg": "Suplemento eliminado exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar el suplemento"}), 500
            
    except Exception as error:
        print(f"Error al eliminar suplemento {suplemento_id}: {str(error)}")
        return jsonify({"msg": "Error interno del servidor al eliminar suplemento"}), 500

def update_suplemento(suplemento_id, nombre=None, descripcion=None, precio=None, 
                     categoria=None, presentacion=None, beneficios=None, 
                     modo_uso=None, stock=None, activo=None):
    """
    Actualizar un suplemento por ID
    """
    try:
        existing = Suplemento.find_by_id(suplemento_id)
        if not existing:
            return jsonify({"msg": "Suplemento no encontrado"}), 404
        
        update_data = {}
        
        if nombre is not None:
            nombre_existing = Suplemento.find_by_name(nombre)
            if nombre_existing and nombre_existing.id != suplemento_id:
                return jsonify({"msg": "Ya existe un suplemento con ese nombre"}), 400
            update_data['nombre'] = nombre
            
        if descripcion is not None:
            update_data['descripcion'] = descripcion
            
        if precio is not None:
            if precio < 0:
                return jsonify({"msg": "El precio no puede ser negativo"}), 400
            update_data['precio'] = precio
            
        if categoria is not None:
            if categoria not in Suplemento.CATEGORIAS:
                return jsonify({
                    "msg": f"Categoría no válida. Categorías: {', '.join(Suplemento.CATEGORIAS.keys())}"
                }), 400
            update_data['categoria'] = categoria
            
        if presentacion is not None:
            if presentacion not in Suplemento.PRESENTACIONES:
                return jsonify({
                    "msg": f"Presentación no válida. Presentaciones: {', '.join(Suplemento.PRESENTACIONES.keys())}"
                }), 400
            update_data['presentacion'] = presentacion
            
        if beneficios is not None:
            update_data['beneficios'] = beneficios
            
        if modo_uso is not None:
            update_data['modo_uso'] = modo_uso
            
        if stock is not None:
            if stock < 0:
                return jsonify({"msg": "El stock no puede ser negativo"}), 400
            update_data['stock'] = stock
            
        if activo is not None:
            update_data['activo'] = activo
        
        if update_data:
            if Suplemento.update_suplemento(suplemento_id, update_data):
                updated = Suplemento.find_by_id(suplemento_id)
                suplemento_dict = Suplemento.to_dict(updated)
                
                return jsonify({
                    "msg": "Suplemento actualizado exitosamente",
                    "suplemento": suplemento_dict
                }), 200
            else:
                return jsonify({"msg": "No se realizaron cambios en el suplemento"}), 200
        else:
            return jsonify({"msg": "No se proporcionaron datos para actualizar"}), 400
            
    except Exception as error:
        print(f"Error al actualizar el suplemento: {error}")
        return jsonify({
            "msg": "Error al actualizar el suplemento",
            "error": str(error)
        }), 500

def toggle_suplemento_activo(suplemento_id):
    """
    Activar/desactivar un suplemento
    """
    try:
        existing = Suplemento.find_by_id(suplemento_id)
        if not existing:
            return jsonify({"msg": "Suplemento no encontrado"}), 404
        
        result = Suplemento.toggle_activo(suplemento_id)
        if result:
            updated = Suplemento.find_by_id(suplemento_id)
            suplemento_dict = Suplemento.to_dict(updated)
            
            estado = "activado" if updated.activo else "desactivado"
            return jsonify({
                "msg": f"Suplemento {estado} exitosamente",
                "suplemento": suplemento_dict
            }), 200
        else:
            return jsonify({"msg": "Error al cambiar el estado del suplemento"}), 500
            
    except Exception as error:
        print(f"Error al cambiar estado del suplemento: {error}")
        return jsonify({"msg": "Error al cambiar el estado del suplemento"}), 500

def search_suplementos(query):
    """Buscar suplementos por nombre, descripción o beneficios"""
    try:
        suplementos = Suplemento.search_suplementos(query)
        suplementos_dict = [Suplemento.to_dict(s) for s in suplementos]
        return jsonify(suplementos_dict), 200
        
    except Exception as error:
        print(f"Error al buscar suplementos: {error}")
        return jsonify({"msg": "Error al buscar suplementos"}), 500

def get_active_suplementos():
    """
    Obtener solo suplementos activos
    """
    try:
        suplementos = Suplemento.get_active_suplementos()
        suplementos_dict = [Suplemento.to_dict(s) for s in suplementos]
        return jsonify(suplementos_dict), 200
    except Exception as error:
        print(f"Error al obtener suplementos activos: {error}")
        return jsonify({"msg": "Error al obtener los suplementos activos"}), 500

def get_suplementos_by_categoria(categoria):
    """
    Obtener suplementos por categoría
    """
    try:
        if categoria not in Suplemento.CATEGORIAS:
            return jsonify({
                "msg": f"Categoría no válida. Categorías: {', '.join(Suplemento.CATEGORIAS.keys())}"
            }), 400
            
        suplementos = Suplemento.get_by_categoria(categoria)
        suplementos_dict = [Suplemento.to_dict(s) for s in suplementos]
        return jsonify(suplementos_dict), 200
    except Exception as error:
        print(f"Error al obtener suplementos por categoría: {error}")
        return jsonify({"msg": "Error al obtener suplementos por categoría"}), 500

def get_suplementos_by_presentacion(presentacion):
    """
    Obtener suplementos por presentación
    """
    try:
        if presentacion not in Suplemento.PRESENTACIONES:
            return jsonify({
                "msg": f"Presentación no válida. Presentaciones: {', '.join(Suplemento.PRESENTACIONES.keys())}"
            }), 400
            
        suplementos = Suplemento.get_by_presentacion(presentacion)
        suplementos_dict = [Suplemento.to_dict(s) for s in suplementos]
        return jsonify(suplementos_dict), 200
    except Exception as error:
        print(f"Error al obtener suplementos por presentación: {error}")
        return jsonify({"msg": "Error al obtener suplementos por presentación"}), 500

def get_bajo_stock():
    """
    Obtener suplementos con stock bajo
    """
    try:
        limite = request.args.get('limite', 10, type=int)
        suplementos = Suplemento.get_bajo_stock(limite)
        suplementos_dict = [Suplemento.to_dict(s) for s in suplementos]
        return jsonify({
            'suplementos': suplementos_dict,
            'count': len(suplementos_dict),
            'limite': limite
        }), 200
    except Exception as error:
        print(f"Error al obtener suplementos con stock bajo: {error}")
        return jsonify({"msg": "Error al obtener suplementos con stock bajo"}), 500

def get_categorias():
    """
    Obtener todas las categorías disponibles
    """
    try:
        return jsonify({
            'categorias': [
                {'id': k, 'nombre': v} for k, v in Suplemento.CATEGORIAS.items()
            ]
        }), 200
    except Exception as error:
        print(f"Error al obtener categorías: {error}")
        return jsonify({"msg": "Error al obtener categorías"}), 500

def get_presentaciones():
    """
    Obtener todas las presentaciones disponibles
    """
    try:
        return jsonify({
            'presentaciones': [
                {'id': k, 'nombre': v} for k, v in Suplemento.PRESENTACIONES.items()
            ]
        }), 200
    except Exception as error:
        print(f"Error al obtener presentaciones: {error}")
        return jsonify({"msg": "Error al obtener presentaciones"}), 500