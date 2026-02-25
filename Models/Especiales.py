# Models/Especiales.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class EspecialSQL(db_sql.Model):
    __tablename__ = 'especiales'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    nombre = db_sql.Column(db_sql.String(100), nullable=False)
    ingredientes = db_sql.Column(db_sql.Text, nullable=False)
    precio = db_sql.Column(db_sql.Numeric(10, 2), nullable=False)
    activo = db_sql.Column(db_sql.Boolean, default=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Especial {self.nombre}>'

# ============================================
# CLASE PRINCIPAL - Usa el repositorio según DB_TYPE
# ============================================
class Especial:
    """Clase que maneja especiales en ambas bases de datos"""
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.especiales
    
    @classmethod
    def find_by_id(cls, especial_id):
        """Buscar especial por ID"""
        try:
            if DB_TYPE == 'mysql':
                return EspecialSQL.query.get(especial_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(especial_id)})
        except:
            return None
    
    @classmethod
    def find_by_name(cls, nombre):
        """Buscar especial por nombre"""
        try:
            if DB_TYPE == 'mysql':
                return EspecialSQL.query.filter_by(nombre=nombre).first()
            else:
                return cls._get_collection().find_one({'nombre': nombre})
        except:
            return None
    
    @classmethod
    def get_all_especiales(cls, only_active=True):
        """Obtener todos los especiales"""
        try:
            if DB_TYPE == 'mysql':
                if only_active:
                    return EspecialSQL.query.filter_by(activo=True).all()
                return EspecialSQL.query.all()
            else:
                query = {}
                if only_active:
                    query['activo'] = True
                return list(cls._get_collection().find(query))
        except Exception as e:
            print(f"Error en get_all_especiales: {e}")
            return []
    
    @classmethod
    def get_active_especiales(cls):
        """Obtener solo especiales activos"""
        return cls.get_all_especiales(only_active=True)
    
    @classmethod
    def create_especial(cls, especial_data):
        """Crear nuevo especial"""
        try:
            if DB_TYPE == 'mysql':
                especial = EspecialSQL(
                    nombre=especial_data['nombre'],
                    ingredientes=especial_data['ingredientes'],
                    precio=especial_data['precio'],
                    activo=especial_data.get('activo', True)
                )
                
                db_sql.session.add(especial)
                db_sql.session.commit()
                return especial.id
                
            else:
                from bson.objectid import ObjectId
                
                especial_doc = {
                    'nombre': especial_data['nombre'],
                    'ingredientes': especial_data['ingredientes'],
                    'precio': float(especial_data['precio']),
                    'activo': especial_data.get('activo', True),
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(especial_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error en create_especial: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_especial(cls, especial_id, update_data):
        """Actualizar especial"""
        try:
            if DB_TYPE == 'mysql':
                especial = EspecialSQL.query.get(especial_id)
                if not especial:
                    return False
                
                if 'nombre' in update_data:
                    especial.nombre = update_data['nombre']
                if 'ingredientes' in update_data:
                    especial.ingredientes = update_data['ingredientes']
                if 'precio' in update_data:
                    especial.precio = update_data['precio']
                if 'activo' in update_data:
                    especial.activo = update_data['activo']
                
                especial.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                
                if 'precio' in update_data:
                    update_data['precio'] = float(update_data['precio'])
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(especial_id)},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_especial: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def delete_especial(cls, especial_id):
        """Eliminar especial (eliminación física)"""
        try:
            if DB_TYPE == 'mysql':
                especial = EspecialSQL.query.get(especial_id)
                if not especial:
                    return False
                
                db_sql.session.delete(especial)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(especial_id)})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_especial: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def toggle_activo(cls, especial_id):
        """Activar/desactivar especial"""
        try:
            if DB_TYPE == 'mysql':
                especial = EspecialSQL.query.get(especial_id)
                if not especial:
                    return False
                
                especial.activo = not especial.activo
                especial.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                especial = cls.find_by_id(especial_id)
                if not especial:
                    return False
                
                nuevo_estado = not especial.get('activo', True)
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(especial_id)},
                    {'$set': {'activo': nuevo_estado, 'fecha_actualizacion': datetime.utcnow()}}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en toggle_activo: {e}")
            return False
    
    @classmethod
    def search_especiales(cls, query):
        """Buscar especiales por nombre o ingredientes"""
        try:
            if DB_TYPE == 'mysql':
                if query:
                    return EspecialSQL.query.filter(
                        (EspecialSQL.nombre.ilike(f'%{query}%')) | 
                        (EspecialSQL.ingredientes.ilike(f'%{query}%'))
                    ).all()
                return EspecialSQL.query.all()
                
            else:
                import re
                if query:
                    regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                    return list(cls._get_collection().find({
                        '$or': [
                            {'nombre': {'$regex': regex}},
                            {'ingredientes': {'$regex': regex}}
                        ]
                    }))
                return list(cls._get_collection().find())
                
        except Exception as e:
            print(f"Error en search_especiales: {e}")
            return []
    
    @classmethod
    def to_dict(cls, especial):
        """Convertir especial a diccionario"""
        if not especial:
            return None
        
        if DB_TYPE == 'mysql':
            return {
                'id': especial.id,
                'nombre': especial.nombre,
                'ingredientes': especial.ingredientes,
                'precio': float(especial.precio) if especial.precio else 0.0,
                'activo': especial.activo,
                'fecha_creacion': especial.fecha_creacion.isoformat() if especial.fecha_creacion else None,
                'fecha_actualizacion': especial.fecha_actualizacion.isoformat() if especial.fecha_actualizacion else None
            }
        else:
            from bson.objectid import ObjectId
            especial_dict = dict(especial)
            especial_dict['id'] = str(especial_dict.pop('_id'))
            
            if 'precio' in especial_dict and not isinstance(especial_dict['precio'], float):
                especial_dict['precio'] = float(especial_dict['precio'])
            
            if 'fecha_creacion' in especial_dict and especial_dict['fecha_creacion']:
                if isinstance(especial_dict['fecha_creacion'], datetime):
                    especial_dict['fecha_creacion'] = especial_dict['fecha_creacion'].isoformat()
            
            if 'fecha_actualizacion' in especial_dict and especial_dict['fecha_actualizacion']:
                if isinstance(especial_dict['fecha_actualizacion'], datetime):
                    especial_dict['fecha_actualizacion'] = especial_dict['fecha_actualizacion'].isoformat()
            
            return especial_dict

# Para compatibilidad con código existente
if DB_TYPE == 'mysql':
    EspecialSQL = Especial