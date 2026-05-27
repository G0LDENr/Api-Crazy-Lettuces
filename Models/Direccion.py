# Models/Direccion.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class DireccionSQL(db_sql.Model):
    __tablename__ = 'direcciones'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    user_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('users.id'), nullable=False)
    calle = db_sql.Column(db_sql.String(200), nullable=False)
    numero_exterior = db_sql.Column(db_sql.String(20), nullable=False)
    numero_interior = db_sql.Column(db_sql.String(20), nullable=True)
    colonia = db_sql.Column(db_sql.String(100), nullable=False)
    ciudad = db_sql.Column(db_sql.String(100), nullable=False)
    estado = db_sql.Column(db_sql.String(50), nullable=False)
    codigo_postal = db_sql.Column(db_sql.String(10), nullable=False)
    referencias = db_sql.Column(db_sql.Text, nullable=True)
    tipo = db_sql.Column(db_sql.String(20), default='casa')
    predeterminada = db_sql.Column(db_sql.Boolean, default=False)
    activa = db_sql.Column(db_sql.Boolean, default=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuario - Usar string 'UserSQL' en lugar de la clase directamente
    usuario = db_sql.relationship('UserSQL', back_populates='direcciones')
    
    def __repr__(self):
        return f'<Direccion {self.calle} {self.numero_exterior}>'

# ============================================
# CLASE PRINCIPAL - Usa el repositorio según DB_TYPE
# ============================================
class Direccion:
    """Clase que maneja direcciones en ambas bases de datos"""
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.direcciones
    
    @classmethod
    def get_all_direcciones(cls):
        """Obtener todas las direcciones"""
        try:
            if DB_TYPE == 'mysql':
                return DireccionSQL.query.all()
            else:
                cursor = cls._get_collection().find()
                return list(cursor)
        except Exception as error:
            print(f"Error en get_all_direcciones: {error}")
            return []
    
    @classmethod
    def create_direccion(cls, user_id, direccion_data):
        """Crear nueva dirección"""
        try:
            if DB_TYPE == 'mysql':
                # MySQL
                if direccion_data.get('predeterminada', False):
                    DireccionSQL.query.filter_by(user_id=user_id, predeterminada=True).update({'predeterminada': False})
                
                direccion = DireccionSQL(
                    user_id=user_id,
                    calle=direccion_data['calle'],
                    numero_exterior=direccion_data['numero_exterior'],
                    numero_interior=direccion_data.get('numero_interior'),
                    colonia=direccion_data['colonia'],
                    ciudad=direccion_data['ciudad'],
                    estado=direccion_data['estado'],
                    codigo_postal=direccion_data['codigo_postal'],
                    referencias=direccion_data.get('referencias'),
                    tipo=direccion_data.get('tipo', 'casa'),
                    predeterminada=direccion_data.get('predeterminada', False),
                    activa=direccion_data.get('activa', True)
                )
                
                db_sql.session.add(direccion)
                db_sql.session.commit()
                return direccion.id
                
            else:
                # MongoDB
                from bson.objectid import ObjectId
                
                # Si es predeterminada, quitar de otras
                if direccion_data.get('predeterminada', False):
                    cls._get_collection().update_many(
                        {'user_id': str(user_id), 'predeterminada': True},
                        {'$set': {'predeterminada': False}}
                    )
                
                direccion_doc = {
                    'user_id': str(user_id),
                    'calle': direccion_data['calle'],
                    'numero_exterior': direccion_data['numero_exterior'],
                    'numero_interior': direccion_data.get('numero_interior'),
                    'colonia': direccion_data['colonia'],
                    'ciudad': direccion_data['ciudad'],
                    'estado': direccion_data['estado'],
                    'codigo_postal': direccion_data['codigo_postal'],
                    'referencias': direccion_data.get('referencias'),
                    'tipo': direccion_data.get('tipo', 'casa'),
                    'predeterminada': direccion_data.get('predeterminada', False),
                    'activa': direccion_data.get('activa', True),
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(direccion_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error en create_direccion: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_direccion(cls, direccion_id, update_data):
        """Actualizar dirección"""
        try:
            if DB_TYPE == 'mysql':
                direccion = DireccionSQL.query.get(direccion_id)
                if not direccion:
                    return False
                
                if 'predeterminada' in update_data and update_data['predeterminada']:
                    DireccionSQL.query.filter_by(user_id=direccion.user_id, predeterminada=True).update({'predeterminada': False})
                
                campos = ['calle', 'numero_exterior', 'numero_interior', 'colonia', 
                         'ciudad', 'estado', 'codigo_postal', 'referencias', 
                         'tipo', 'predeterminada', 'activa']
                
                for campo in campos:
                    if campo in update_data:
                        setattr(direccion, campo, update_data[campo])
                
                direccion.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                # MongoDB
                from bson.objectid import ObjectId
                
                # Obtener dirección actual
                direccion = cls._get_collection().find_one({'_id': ObjectId(direccion_id)})
                if not direccion:
                    return False
                
                # Si se marca como predeterminada
                if 'predeterminada' in update_data and update_data['predeterminada']:
                    cls._get_collection().update_many(
                        {'user_id': direccion['user_id'], 'predeterminada': True},
                        {'$set': {'predeterminada': False}}
                    )
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(direccion_id)},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as error:
            print(f"Error en update_direccion: {error}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def delete_direccion(cls, direccion_id):
        """Eliminar dirección"""
        try:
            if DB_TYPE == 'mysql':
                direccion = DireccionSQL.query.get(direccion_id)
                if not direccion:
                    return False
                
                db_sql.session.delete(direccion)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(direccion_id)})
                return result.deleted_count > 0
                
        except Exception as error:
            print(f"Error al eliminar dirección: {error}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def get_direccion_by_id(cls, direccion_id):
        """Obtener dirección por ID"""
        try:
            if DB_TYPE == 'mysql':
                return DireccionSQL.query.get(direccion_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(direccion_id)})
        except:
            return None
    
    @classmethod
    def get_direcciones_by_user(cls, user_id):
        """Obtener todas las direcciones de un usuario"""
        try:
            if DB_TYPE == 'mysql':
                return DireccionSQL.query.filter_by(user_id=user_id).all()
            else:
                cursor = cls._get_collection().find({'user_id': str(user_id)})
                return list(cursor)
        except Exception as error:
            print(f"Error en get_direcciones_by_user: {error}")
            return []
    
    @classmethod
    def get_direccion_predeterminada(cls, user_id):
        """Obtener dirección predeterminada de un usuario"""
        try:
            if DB_TYPE == 'mysql':
                return DireccionSQL.query.filter_by(user_id=user_id, predeterminada=True).first()
            else:
                return cls._get_collection().find_one({'user_id': str(user_id), 'predeterminada': True})
        except Exception as error:
            print(f"Error en get_direccion_predeterminada: {error}")
            return None
    
    @classmethod
    def search_direcciones(cls, query):
        """Buscar direcciones por calle, colonia, ciudad o estado"""
        try:
            if DB_TYPE == 'mysql':
                return DireccionSQL.query.filter(
                    (DireccionSQL.calle.ilike(f'%{query}%')) |
                    (DireccionSQL.colonia.ilike(f'%{query}%')) |
                    (DireccionSQL.ciudad.ilike(f'%{query}%')) |
                    (DireccionSQL.estado.ilike(f'%{query}%'))
                ).all()
            else:
                import re
                regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                return list(cls._get_collection().find({
                    '$or': [
                        {'calle': {'$regex': regex}},
                        {'colonia': {'$regex': regex}},
                        {'ciudad': {'$regex': regex}},
                        {'estado': {'$regex': regex}}
                    ]
                }))
        except Exception as error:
            print(f"Error en search_direcciones: {error}")
            return []
    
    @classmethod
    def to_dict(cls, direccion):
        """Convertir dirección a diccionario"""
        if not direccion:
            return None
        
        if DB_TYPE == 'mysql':
            return {
                'id': direccion.id,
                'user_id': direccion.user_id,
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
                'direccion_completa': f"{direccion.calle} #{direccion.numero_exterior}" + 
                                      (f" Int. {direccion.numero_interior}" if direccion.numero_interior else "") +
                                      f", {direccion.colonia}, {direccion.ciudad}, {direccion.estado}. CP: {direccion.codigo_postal}"
            }
        else:
            # MongoDB
            from bson.objectid import ObjectId
            direccion_dict = dict(direccion)
            direccion_dict['id'] = str(direccion_dict.pop('_id'))
            
            if 'user_id' in direccion_dict and direccion_dict['user_id']:
                try:
                    if isinstance(direccion_dict['user_id'], str) and direccion_dict['user_id'].isdigit():
                        direccion_dict['user_id'] = int(direccion_dict['user_id'])
                except:
                    pass
            
            if 'fecha_creacion' in direccion_dict and direccion_dict['fecha_creacion']:
                if isinstance(direccion_dict['fecha_creacion'], datetime):
                    direccion_dict['fecha_creacion'] = direccion_dict['fecha_creacion'].strftime('%Y-%m-%d %H:%M:%S')
            
            if 'fecha_actualizacion' in direccion_dict and direccion_dict['fecha_actualizacion']:
                if isinstance(direccion_dict['fecha_actualizacion'], datetime):
                    direccion_dict['fecha_actualizacion'] = direccion_dict['fecha_actualizacion'].strftime('%Y-%m-%d %H:%M:%S')
            
            direccion_dict['direccion_completa'] = f"{direccion_dict['calle']} #{direccion_dict['numero_exterior']}" + \
                                                  (f" Int. {direccion_dict['numero_interior']}" if direccion_dict.get('numero_interior') else "") + \
                                                  f", {direccion_dict['colonia']}, {direccion_dict['ciudad']}, {direccion_dict['estado']}. CP: {direccion_dict['codigo_postal']}"
            
            return direccion_dict

# ============================================
# EXPORTACIÓN CONDICIONAL
# ============================================
# Solo exponer DireccionSQL cuando se usa MySQL
if DB_TYPE == 'mysql':
    # Esto es para que SQLAlchemy pueda mapear correctamente
    DireccionSQL = DireccionSQL
else:
    # Para MongoDB, no necesitamos el modelo SQL
    pass