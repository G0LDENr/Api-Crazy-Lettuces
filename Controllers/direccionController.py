# Controllers/direccionController.py
from Models.Direccion import Direccion, DireccionSQL
from Models.User import user_repo
from flask import jsonify
import traceback
from config import DB_TYPE, db_mongo
from datetime import datetime

def get_all_direcciones():
    """
    Obtener todas las direcciones
    """
    try:
        direcciones = Direccion.get_all_direcciones()
        direcciones_dict = [Direccion.to_dict(dir) for dir in direcciones]
        return jsonify(direcciones_dict), 200
    except Exception as error:
        print(f"Error al obtener direcciones: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener las direcciones"}), 500

def get_single_direccion(direccion_id):
    """
    Obtener una dirección por ID
    """
    try:
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        direccion_dict = Direccion.to_dict(direccion)
        return jsonify(direccion_dict), 200
    except Exception as error:
        print(f"Error al obtener la dirección: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener la dirección"}), 500

def create_direccion(data):
    """Crear nueva dirección"""
    try:
        print(f"Creando dirección con datos: {data}")
        
        user_id = data.get('user_id')
        calle = data.get('calle')
        numero_exterior = data.get('numero_exterior')
        colonia = data.get('colonia')
        ciudad = data.get('ciudad')
        estado = data.get('estado')
        codigo_postal = data.get('codigo_postal')
        numero_interior = data.get('numero_interior', '')
        referencias = data.get('referencias', '')
        tipo = data.get('tipo', 'casa')
        predeterminada = data.get('predeterminada', False)
        
        if not all([user_id, calle, numero_exterior, colonia, ciudad, estado, codigo_postal]):
            return jsonify({'msg': 'Faltan datos requeridos', 
                           'required': ['user_id', 'calle', 'numero_exterior', 'colonia', 'ciudad', 'estado', 'codigo_postal']}), 400
        
        if DB_TYPE == 'mongodb':
            # Para MongoDB - usar string directamente
            direccion_data = {
                'user_id': str(user_id),
                'calle': calle,
                'numero_exterior': numero_exterior,
                'numero_interior': numero_interior,
                'colonia': colonia,
                'ciudad': ciudad,
                'estado': estado,
                'codigo_postal': codigo_postal,
                'referencias': referencias,
                'tipo': tipo,
                'predeterminada': predeterminada,
                'activa': True,
                'fecha_creacion': datetime.utcnow(),
                'fecha_actualizacion': datetime.utcnow()
            }
            
            # Si es predeterminada, quitar predeterminada de otras direcciones
            if predeterminada:
                db_mongo.db.direcciones.update_many(
                    {'user_id': str(user_id), 'predeterminada': True},
                    {'$set': {'predeterminada': False}}
                )
            
            result = db_mongo.db.direcciones.insert_one(direccion_data)
            direccion_data['_id'] = str(result.inserted_id)
            direccion_data['id'] = str(result.inserted_id)
            direccion_data['direccion_completa'] = f"{calle} #{numero_exterior}, {colonia}, {ciudad}, CP: {codigo_postal}"
            
            return jsonify({
                'msg': 'Dirección creada exitosamente',
                'direccion': direccion_data
            }), 201
            
        else:  # MySQL
            # Para MySQL - convertir a entero
            try:
                user_id_int = int(user_id)
                print(f"Creando dirección para usuario MySQL ID: {user_id_int}")
            except (ValueError, TypeError):
                return jsonify({'msg': 'ID de usuario inválido', 'error': f'No se pudo convertir {user_id} a entero'}), 400
            
            from config import db
            
            # CORREGIDO: usar DireccionSQL en lugar de Direccion
            # Si es predeterminada, quitar predeterminada de otras direcciones
            if predeterminada:
                DireccionSQL.query.filter_by(user_id=user_id_int, predeterminada=True).update({'predeterminada': False})
            
            nueva_direccion = DireccionSQL(
                user_id=user_id_int,
                calle=calle,
                numero_exterior=numero_exterior,
                numero_interior=numero_interior,
                colonia=colonia,
                ciudad=ciudad,
                estado=estado,
                codigo_postal=codigo_postal,
                referencias=referencias,
                tipo=tipo,
                predeterminada=predeterminada,
                activa=True
            )
            
            db.session.add(nueva_direccion)
            db.session.commit()
            
            direccion_dict = Direccion.to_dict(nueva_direccion)
            
            return jsonify({
                'msg': 'Dirección creada exitosamente',
                'direccion': direccion_dict
            }), 201
            
    except Exception as e:
        print(f"Error en create_direccion: {e}")
        traceback.print_exc()
        return jsonify({'msg': 'Error al crear dirección', 'error': str(e)}), 500

def update_direccion(direccion_id, update_data):
    """
    Actualizar una dirección
    """
    try:
        # Validar que la dirección exista
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        # Validar código postal si se actualiza
        if 'codigo_postal' in update_data:
            cp = str(update_data['codigo_postal'])
            if not cp.isdigit() or len(cp) != 5:
                return jsonify({"msg": "El código postal debe tener 5 dígitos"}), 400
        
        # Agregar fecha de actualización
        update_data['fecha_actualizacion'] = datetime.utcnow()
        
        # Actualizar dirección
        if Direccion.update_direccion(direccion_id, update_data):
            direccion_actualizada = Direccion.get_direccion_by_id(direccion_id)
            return jsonify({
                "msg": "Dirección actualizada exitosamente",
                "direccion": Direccion.to_dict(direccion_actualizada)
            }), 200
        else:
            return jsonify({"msg": "Error al actualizar la dirección"}), 500
            
    except Exception as error:
        print(f"Error al actualizar dirección: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al actualizar la dirección"}), 500

def delete_direccion(direccion_id):
    """
    Eliminar una dirección
    """
    try:
        # Verificar si la dirección existe
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        # Eliminar dirección
        if Direccion.delete_direccion(direccion_id):
            return jsonify({"msg": "Dirección eliminada exitosamente"}), 200
        else:
            return jsonify({"msg": "Error al eliminar la dirección"}), 500
            
    except Exception as error:
        print(f"Error al eliminar dirección: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al eliminar la dirección"}), 500

def get_direcciones_by_user(user_id):
    """Obtener direcciones de un usuario específico"""
    try:
        print(f"📦 Obteniendo direcciones para usuario ID: {user_id} (tipo: {type(user_id)})")
        print(f"📦 DB_TYPE: {DB_TYPE}")
        
        if DB_TYPE == 'mongodb':
            # Para MongoDB - usar string directamente
            user_id_str = str(user_id)
            print(f"📦 Buscando direcciones con user_id = '{user_id_str}'")
            
            direcciones = list(db_mongo.db.direcciones.find({'user_id': user_id_str, 'activa': True}))
            
            print(f"📦 Direcciones encontradas en MongoDB: {len(direcciones)}")
            
            for direccion in direcciones:
                direccion['_id'] = str(direccion['_id'])
                direccion['id'] = str(direccion['_id'])
                if 'user_id' in direccion:
                    direccion['user_id'] = str(direccion['user_id'])
                direccion['usuario_id'] = direccion['user_id']
                if 'fecha_creacion' in direccion and direccion['fecha_creacion']:
                    if hasattr(direccion['fecha_creacion'], 'isoformat'):
                        direccion['fecha_creacion'] = direccion['fecha_creacion'].isoformat()
                if 'fecha_actualizacion' in direccion and direccion['fecha_actualizacion']:
                    if hasattr(direccion['fecha_actualizacion'], 'isoformat'):
                        direccion['fecha_actualizacion'] = direccion['fecha_actualizacion'].isoformat()
                direccion['direccion_completa'] = f"{direccion.get('calle', '')} #{direccion.get('numero_exterior', '')}, {direccion.get('colonia', '')}, {direccion.get('ciudad', '')}, CP: {direccion.get('codigo_postal', '')}"
            
            return jsonify({
                'direcciones': direcciones,
                'total': len(direcciones)
            }), 200
            
        else:  # MySQL
            # Para MySQL - convertir a entero
            try:
                user_id_int = int(user_id)
                print(f"📦 Buscando direcciones para usuario MySQL ID: {user_id_int}")
            except (ValueError, TypeError):
                return jsonify({'msg': 'ID de usuario inválido', 'error': f'No se pudo convertir {user_id} a entero'}), 400
            
            # CORREGIDO: usar DireccionSQL en lugar de Direccion
            direcciones = DireccionSQL.query.filter_by(user_id=user_id_int, activa=True).all()
            
            print(f"📦 Direcciones encontradas en MySQL: {len(direcciones)}")
            
            direcciones_data = []
            for direccion in direcciones:
                direcciones_data.append({
                    'id': direccion.id,
                    'user_id': direccion.user_id,
                    'usuario_id': direccion.user_id,
                    'calle': direccion.calle,
                    'numero_exterior': direccion.numero_exterior,
                    'numero_interior': direccion.numero_interior,
                    'colonia': direccion.colonia,
                    'ciudad': direccion.ciudad,
                    'estado': direccion.estado,
                    'codigo_postal': direccion.codigo_postal,
                    'referencias': direccion.referencias,
                    'tipo': direccion.tipo,
                    'predeterminada': direccion.predeterminada,
                    'activa': direccion.activa,
                    'fecha_creacion': direccion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if direccion.fecha_creacion else None,
                    'fecha_actualizacion': direccion.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if direccion.fecha_actualizacion else None,
                    'direccion_completa': f"{direccion.calle} #{direccion.numero_exterior}, {direccion.colonia}, {direccion.ciudad}, CP: {direccion.codigo_postal}"
                })
            
            return jsonify({
                'direcciones': direcciones_data,
                'total': len(direcciones_data)
            }), 200
            
    except Exception as e:
        print(f"Error en get_direcciones_by_user: {e}")
        traceback.print_exc()
        return jsonify({'msg': 'Error al obtener direcciones', 'error': str(e)}), 500

def get_direccion_predeterminada(user_id):
    """
    Obtener dirección predeterminada de un usuario
    """
    try:
        print(f"📦 Obteniendo dirección predeterminada para usuario: {user_id}")
        
        # Verificar que el usuario exista
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        if DB_TYPE == 'mongodb':
            user_id_str = str(user_id)
            direccion = db_mongo.db.direcciones.find_one({
                'user_id': user_id_str, 
                'predeterminada': True, 
                'activa': True
            })
            
            if not direccion:
                return jsonify({"msg": "El usuario no tiene una dirección predeterminada"}), 404
            
            direccion['_id'] = str(direccion['_id'])
            direccion['id'] = str(direccion['_id'])
            direccion['direccion_completa'] = f"{direccion.get('calle', '')} #{direccion.get('numero_exterior', '')}, {direccion.get('colonia', '')}, {direccion.get('ciudad', '')}, CP: {direccion.get('codigo_postal', '')}"
            
            return jsonify({
                "direccion": direccion,
                "usuario": {
                    "id": str(user.get('_id')) if hasattr(user, 'get') else user.id,
                    "nombre": user.get('nombre') if hasattr(user, 'get') else user.nombre,
                    "correo": user.get('correo') if hasattr(user, 'get') else user.correo
                }
            }), 200
            
        else:  # MySQL
            try:
                user_id_int = int(user_id)
                print(f"📦 Buscando dirección predeterminada para MySQL usuario: {user_id_int}")
            except (ValueError, TypeError):
                return jsonify({'msg': 'ID de usuario inválido'}), 400
            
            # CORREGIDO: usar DireccionSQL en lugar de Direccion
            direccion = DireccionSQL.query.filter_by(user_id=user_id_int, predeterminada=True, activa=True).first()
            
            if not direccion:
                return jsonify({"msg": "El usuario no tiene una dirección predeterminada"}), 404
            
            return jsonify({
                "direccion": Direccion.to_dict(direccion),
                "usuario": {
                    "id": user.id,
                    "nombre": user.nombre,
                    "correo": user.correo
                }
            }), 200
        
    except Exception as error:
        print(f"Error al obtener dirección predeterminada: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al obtener dirección predeterminada"}), 500

def set_direccion_predeterminada(user_id, direccion_id):
    """
    Establecer dirección como predeterminada
    """
    try:
        # Verificar que el usuario exista
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        # Verificar que la dirección exista y pertenezca al usuario
        direccion = Direccion.get_direccion_by_id(direccion_id)
        if not direccion:
            return jsonify({"msg": "Dirección no encontrada"}), 404
        
        direccion_dict = Direccion.to_dict(direccion)
        
        if str(direccion_dict.get('user_id', direccion_dict.get('usuario_id'))) != str(user_id):
            return jsonify({"msg": "Dirección no pertenece al usuario"}), 403
        
        if DB_TYPE == 'mongodb':
            from bson import ObjectId
            user_id_str = str(user_id)
            # Quitar predeterminada de todas las direcciones del usuario
            db_mongo.db.direcciones.update_many(
                {'user_id': user_id_str, 'predeterminada': True},
                {'$set': {'predeterminada': False}}
            )
            
            # Establecer esta como predeterminada
            result = db_mongo.db.direcciones.update_one(
                {'_id': ObjectId(direccion_id)},
                {'$set': {'predeterminada': True, 'fecha_actualizacion': datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                return jsonify({"msg": "Dirección establecida como predeterminada exitosamente"}), 200
            else:
                return jsonify({"msg": "Error al establecer dirección predeterminada"}), 500
                
        else:  # MySQL
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                return jsonify({'msg': 'ID de usuario inválido'}), 400
            
            from config import db
            
            # CORREGIDO: usar DireccionSQL en lugar de Direccion
            # Quitar predeterminada de todas las direcciones del usuario
            DireccionSQL.query.filter_by(user_id=user_id_int, predeterminada=True).update({'predeterminada': False})
            
            # Establecer esta como predeterminada
            result = DireccionSQL.query.filter_by(id=direccion_id).update({'predeterminada': True})
            db.session.commit()
            
            if result:
                return jsonify({"msg": "Dirección establecida como predeterminada exitosamente"}), 200
            else:
                return jsonify({"msg": "Error al establecer dirección predeterminada"}), 500
            
    except Exception as error:
        print(f"Error al establecer dirección predeterminada: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al establecer dirección predeterminada"}), 500

def search_direcciones(query):
    """
    Buscar direcciones por calle, colonia, ciudad o estado
    """
    try:
        direcciones = Direccion.search_direcciones(query)
        direcciones_dict = [Direccion.to_dict(dir) for dir in direcciones]
        return jsonify(direcciones_dict), 200
        
    except Exception as error:
        print(f"Error al buscar direcciones: {error}")
        traceback.print_exc()
        return jsonify({"msg": "Error al buscar direcciones"}), 500