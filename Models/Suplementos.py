from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class SuplementoSQL(db_sql.Model):
    __tablename__ = 'suplementos'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    nombre = db_sql.Column(db_sql.String(100), nullable=False)
    descripcion = db_sql.Column(db_sql.Text, nullable=False)
    precio = db_sql.Column(db_sql.Numeric(10, 2), nullable=False)
    categoria = db_sql.Column(db_sql.String(50), nullable=False, default='quemadores')
    presentacion = db_sql.Column(db_sql.String(50), nullable=False, default='polvo')
    beneficios = db_sql.Column(db_sql.Text, nullable=True)
    modo_uso = db_sql.Column(db_sql.Text, nullable=True)
    stock = db_sql.Column(db_sql.Integer, default=0)
    activo = db_sql.Column(db_sql.Boolean, default=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Suplemento {self.nombre}>'
    
    def to_dict(self):
        """Convertir a diccionario"""
        print(f"DEBUG to_dict - {self.nombre}: stock={self.stock}")
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio': float(self.precio) if self.precio else 0.0,
            'categoria': self.categoria,
            'categoria_nombre': Suplemento.CATEGORIAS.get(self.categoria, self.categoria),
            'presentacion': self.presentacion,
            'presentacion_nombre': Suplemento.PRESENTACIONES.get(self.presentacion, self.presentacion),
            'beneficios': self.beneficios,
            'modo_uso': self.modo_uso,
            'stock': self.stock,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

# ============================================
# CLASE PRINCIPAL
# ============================================
class Suplemento:
    """Clase que maneja suplementos en ambas bases de datos"""
    
    # Categorías disponibles
    CATEGORIAS = {
        'quemadores': 'Quemadores de Grasa',
        'proteinas': 'Proteínas',
        'fibras': 'Fibras y Digestivos',
        'detox': 'Detox y Limpieza',
        'termogenicos': 'Termogénicos',
        'control_apetito': 'Control de Apetito',
        'energeticos': 'Energéticos Naturales',
        'vitaminas': 'Vitaminas y Minerales'
    }
    
    # Presentaciones disponibles
    PRESENTACIONES = {
        'polvo': 'Polvo',
        'capsulas': 'Cápsulas',
        'tableta': 'Tableta',
        'liquidos': 'Líquidos',
        'gomitas': 'Gomitas',
        'barritas': 'Barritas'
    }
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.suplementos
    
    @classmethod
    def find_by_id(cls, suplemento_id):
        """Buscar suplemento por ID"""
        try:
            if DB_TYPE == 'mysql':
                return SuplementoSQL.query.get(suplemento_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(suplemento_id)})
        except:
            return None
    
    @classmethod
    def find_by_name(cls, nombre):
        """Buscar suplemento por nombre"""
        try:
            if DB_TYPE == 'mysql':
                return SuplementoSQL.query.filter_by(nombre=nombre).first()
            else:
                return cls._get_collection().find_one({'nombre': nombre})
        except:
            return None

    @classmethod
    def get_all_suplementos(cls, only_active=True):
        """Obtener todos los suplementos"""
        try:
            if DB_TYPE == 'mysql':
                if only_active:
                    return SuplementoSQL.query.filter_by(activo=True).all()
                return SuplementoSQL.query.all()
            else:
                query = {}
                if only_active:
                    query['activo'] = True
                return list(cls._get_collection().find(query))
        except Exception as e:
            print(f"Error en get_all_suplementos: {e}")
            return []
    
    @classmethod
    def get_active_suplementos(cls):
        """Obtener solo suplementos activos"""
        return cls.get_all_suplementos(only_active=True)
    
    @classmethod
    def create_suplemento(cls, suplemento_data):
        """Crear nuevo suplemento"""
        try:
            if DB_TYPE == 'mysql':
                print(f"Creando suplemento en MySQL: {suplemento_data}")
                suplemento = SuplementoSQL(
                    nombre=suplemento_data['nombre'],
                    descripcion=suplemento_data.get('descripcion', ''),
                    precio=suplemento_data['precio'],
                    categoria=suplemento_data.get('categoria', 'quemadores'),
                    presentacion=suplemento_data.get('presentacion', 'polvo'),
                    beneficios=suplemento_data.get('beneficios', ''),
                    modo_uso=suplemento_data.get('modo_uso', ''),
                    stock=suplemento_data.get('stock', 0),
                    activo=suplemento_data.get('activo', True)
                )
                
                db_sql.session.add(suplemento)
                db_sql.session.commit()
                print(f"✅ Suplemento creado con ID: {suplemento.id}")
                return suplemento.id
                
            else:
                from bson.objectid import ObjectId
                
                suplemento_doc = {
                    'nombre': suplemento_data['nombre'],
                    'descripcion': suplemento_data.get('descripcion', ''),
                    'precio': float(suplemento_data['precio']),
                    'categoria': suplemento_data.get('categoria', 'quemadores'),
                    'presentacion': suplemento_data.get('presentacion', 'polvo'),
                    'beneficios': suplemento_data.get('beneficios', ''),
                    'modo_uso': suplemento_data.get('modo_uso', ''),
                    'stock': suplemento_data.get('stock', 0),
                    'activo': suplemento_data.get('activo', True),
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(suplemento_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"❌ Error en create_suplemento: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_suplemento(cls, suplemento_id, update_data):
        """Actualizar suplemento"""
        try:
            if DB_TYPE == 'mysql':
                suplemento = SuplementoSQL.query.get(suplemento_id)
                if not suplemento:
                    return False
                
                if 'nombre' in update_data:
                    suplemento.nombre = update_data['nombre']
                if 'descripcion' in update_data:
                    suplemento.descripcion = update_data['descripcion']
                if 'precio' in update_data:
                    suplemento.precio = update_data['precio']
                if 'categoria' in update_data:
                    suplemento.categoria = update_data['categoria']
                if 'presentacion' in update_data:
                    suplemento.presentacion = update_data['presentacion']
                if 'beneficios' in update_data:
                    suplemento.beneficios = update_data['beneficios']
                if 'modo_uso' in update_data:
                    suplemento.modo_uso = update_data['modo_uso']
                if 'stock' in update_data:
                    suplemento.stock = update_data['stock']
                if 'activo' in update_data:
                    suplemento.activo = update_data['activo']
                
                suplemento.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                
                if 'precio' in update_data:
                    update_data['precio'] = float(update_data['precio'])
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(suplemento_id)},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_suplemento: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def delete_suplemento(cls, suplemento_id):
        """Eliminar suplemento (eliminación física)"""
        try:
            if DB_TYPE == 'mysql':
                suplemento = SuplementoSQL.query.get(suplemento_id)
                if not suplemento:
                    return False
                
                db_sql.session.delete(suplemento)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(suplemento_id)})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_suplemento: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def toggle_activo(cls, suplemento_id):
        """Activar/desactivar suplemento"""
        try:
            if DB_TYPE == 'mysql':
                suplemento = SuplementoSQL.query.get(suplemento_id)
                if not suplemento:
                    return False
                
                suplemento.activo = not suplemento.activo
                suplemento.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                suplemento = cls.find_by_id(suplemento_id)
                if not suplemento:
                    return False
                
                nuevo_estado = not suplemento.get('activo', True)
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(suplemento_id)},
                    {'$set': {'activo': nuevo_estado, 'fecha_actualizacion': datetime.utcnow()}}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en toggle_activo: {e}")
            return False
    
    @classmethod
    def search_suplementos(cls, query):
        """Buscar suplementos por nombre, descripción o beneficios"""
        try:
            if DB_TYPE == 'mysql':
                if query:
                    return SuplementoSQL.query.filter(
                        (SuplementoSQL.nombre.ilike(f'%{query}%')) | 
                        (SuplementoSQL.descripcion.ilike(f'%{query}%')) |
                        (SuplementoSQL.beneficios.ilike(f'%{query}%')) |
                        (SuplementoSQL.modo_uso.ilike(f'%{query}%'))
                    ).all()
                return SuplementoSQL.query.all()
                
            else:
                import re
                if query:
                    regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                    return list(cls._get_collection().find({
                        '$or': [
                            {'nombre': {'$regex': regex}},
                            {'descripcion': {'$regex': regex}},
                            {'beneficios': {'$regex': regex}},
                            {'modo_uso': {'$regex': regex}}
                        ]
                    }))
                return list(cls._get_collection().find())
                
        except Exception as e:
            print(f"Error en search_suplementos: {e}")
            return []
    
    @classmethod
    def get_by_categoria(cls, categoria):
        """Obtener suplementos por categoría"""
        try:
            if DB_TYPE == 'mysql':
                return SuplementoSQL.query.filter_by(categoria=categoria, activo=True).all()
            else:
                return list(cls._get_collection().find({'categoria': categoria, 'activo': True}))
        except Exception as e:
            print(f"Error en get_by_categoria: {e}")
            return []
    
    @classmethod
    def get_by_presentacion(cls, presentacion):
        """Obtener suplementos por presentación"""
        try:
            if DB_TYPE == 'mysql':
                return SuplementoSQL.query.filter_by(presentacion=presentacion, activo=True).all()
            else:
                return list(cls._get_collection().find({'presentacion': presentacion, 'activo': True}))
        except Exception as e:
            print(f"Error en get_by_presentacion: {e}")
            return []
    
    @classmethod
    def get_bajo_stock(cls, limite=10):
        """Obtener suplementos con stock bajo"""
        try:
            if DB_TYPE == 'mysql':
                return SuplementoSQL.query.filter(SuplementoSQL.stock <= limite, SuplementoSQL.activo == True).all()
            else:
                return list(cls._get_collection().find({
                    'stock': {'$lte': limite},
                    'activo': True
                }))
        except Exception as e:
            print(f"Error en get_bajo_stock: {e}")
            return []
    
    @classmethod
    def to_dict(cls, suplemento):
        """Convertir suplemento a diccionario"""
        if not suplemento:
            return None
        
        if DB_TYPE == 'mysql':
            return suplemento.to_dict()
        else:
            from bson.objectid import ObjectId
            suplemento_dict = dict(suplemento)
            suplemento_dict['id'] = str(suplemento_dict.pop('_id'))
            
            if 'precio' in suplemento_dict and not isinstance(suplemento_dict['precio'], float):
                suplemento_dict['precio'] = float(suplemento_dict['precio'])
            
            if 'categoria' in suplemento_dict:
                suplemento_dict['categoria_nombre'] = cls.CATEGORIAS.get(suplemento_dict['categoria'], suplemento_dict['categoria'])
            
            if 'presentacion' in suplemento_dict:
                suplemento_dict['presentacion_nombre'] = cls.PRESENTACIONES.get(suplemento_dict['presentacion'], suplemento_dict['presentacion'])
            
            if 'fecha_creacion' in suplemento_dict and suplemento_dict['fecha_creacion']:
                if isinstance(suplemento_dict['fecha_creacion'], datetime):
                    suplemento_dict['fecha_creacion'] = suplemento_dict['fecha_creacion'].isoformat()
            
            if 'fecha_actualizacion' in suplemento_dict and suplemento_dict['fecha_actualizacion']:
                if isinstance(suplemento_dict['fecha_actualizacion'], datetime):
                    suplemento_dict['fecha_actualizacion'] = suplemento_dict['fecha_actualizacion'].isoformat()
            
            return suplemento_dict