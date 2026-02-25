# Models/Ingrediente.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class IngredienteSQL(db_sql.Model):
    __tablename__ = 'ingredientes'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    nombre = db_sql.Column(db_sql.String(100), nullable=False, unique=True)
    categoria = db_sql.Column(db_sql.String(50), nullable=True)
    activo = db_sql.Column(db_sql.Boolean, default=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ingrediente {self.nombre}>'

# ============================================
# CLASE PRINCIPAL - Usa el repositorio según DB_TYPE
# ============================================
class Ingrediente:
    """Clase que maneja ingredientes en ambas bases de datos"""
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB"""
        return db_mongo.db.ingredientes
    
    @classmethod
    def find_by_id(cls, ingrediente_id):
        """Buscar ingrediente por ID"""
        try:
            if DB_TYPE == 'mysql':
                return IngredienteSQL.query.get(ingrediente_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(ingrediente_id)})
        except:
            return None
    
    @classmethod
    def find_by_name(cls, nombre):
        """Buscar ingrediente por nombre"""
        try:
            if DB_TYPE == 'mysql':
                return IngredienteSQL.query.filter_by(nombre=nombre).first()
            else:
                return cls._get_collection().find_one({'nombre': nombre})
        except:
            return None
    
    @classmethod
    def get_all_ingredientes(cls, only_active=True, categoria=None):
        """Obtener todos los ingredientes"""
        try:
            if DB_TYPE == 'mysql':
                query = IngredienteSQL.query
                
                if only_active:
                    query = query.filter_by(activo=True)
                
                if categoria:
                    query = query.filter_by(categoria=categoria)
                
                return query.order_by(IngredienteSQL.nombre.asc()).all()
                
            else:
                query = {}
                if only_active:
                    query['activo'] = True
                if categoria:
                    query['categoria'] = categoria
                
                return list(cls._get_collection().find(query).sort('nombre', 1))
                
        except Exception as e:
            print(f"Error en get_all_ingredientes: {e}")
            return []
    
    @classmethod
    def get_ingredientes_activos(cls):
        """Obtener solo ingredientes activos"""
        return cls.get_all_ingredientes(only_active=True)
    
    @classmethod
    def create_ingrediente(cls, ingrediente_data):
        """Crear nuevo ingrediente"""
        try:
            if DB_TYPE == 'mysql':
                ingrediente = IngredienteSQL(
                    nombre=ingrediente_data['nombre'],
                    categoria=ingrediente_data.get('categoria'),
                    activo=ingrediente_data.get('activo', True)
                )
                
                db_sql.session.add(ingrediente)
                db_sql.session.commit()
                return ingrediente.id
                
            else:
                from bson.objectid import ObjectId
                
                ingrediente_doc = {
                    'nombre': ingrediente_data['nombre'],
                    'categoria': ingrediente_data.get('categoria'),
                    'activo': ingrediente_data.get('activo', True),
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(ingrediente_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error en create_ingrediente: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_ingrediente(cls, ingrediente_id, update_data):
        """Actualizar ingrediente"""
        try:
            if DB_TYPE == 'mysql':
                ingrediente = IngredienteSQL.query.get(ingrediente_id)
                if not ingrediente:
                    return False
                
                if 'nombre' in update_data:
                    ingrediente.nombre = update_data['nombre']
                if 'categoria' in update_data:
                    ingrediente.categoria = update_data['categoria']
                if 'activo' in update_data:
                    ingrediente.activo = update_data['activo']
                
                ingrediente.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                
                if 'activo' in update_data and update_data['activo'] == False:
                    cls._enviar_notificaciones_desactivacion(ingrediente_id)
                
                return True
                
            else:
                from bson.objectid import ObjectId
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(ingrediente_id)},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0 and 'activo' in update_data and update_data['activo'] == False:
                    cls._enviar_notificaciones_desactivacion(ingrediente_id)
                
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_ingrediente: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def delete_ingrediente(cls, ingrediente_id):
        """Eliminar ingrediente (eliminación física)"""
        try:
            if DB_TYPE == 'mysql':
                ingrediente = IngredienteSQL.query.get(ingrediente_id)
                if not ingrediente:
                    return False
                
                db_sql.session.delete(ingrediente)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(ingrediente_id)})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_ingrediente: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def toggle_activo(cls, ingrediente_id):
        """Activar/desactivar ingrediente"""
        try:
            if DB_TYPE == 'mysql':
                ingrediente = IngredienteSQL.query.get(ingrediente_id)
                if not ingrediente:
                    return False
                
                estado_anterior = ingrediente.activo
                ingrediente.activo = not ingrediente.activo
                ingrediente.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                
                if estado_anterior == True and ingrediente.activo == False:
                    cls._enviar_notificaciones_desactivacion(ingrediente_id)
                
                return True
                
            else:
                from bson.objectid import ObjectId
                ingrediente = cls.find_by_id(ingrediente_id)
                if not ingrediente:
                    return False
                
                estado_anterior = ingrediente.get('activo', True)
                nuevo_estado = not estado_anterior
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(ingrediente_id)},
                    {'$set': {'activo': nuevo_estado, 'fecha_actualizacion': datetime.utcnow()}}
                )
                
                if result.modified_count > 0 and estado_anterior == True and nuevo_estado == False:
                    cls._enviar_notificaciones_desactivacion(ingrediente_id)
                
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en toggle_activo: {e}")
            return False
    
    @classmethod
    def _enviar_notificaciones_desactivacion(cls, ingrediente_id):
        """
        Enviar notificaciones cuando un ingrediente se desactiva
        """
        try:
            from Models.Notificaciones import Notificacion
            from Models.User import User
            from Models.Especiales import Especial
            
            ingrediente = cls.find_by_id(ingrediente_id)
            if not ingrediente:
                return False
            
            ingrediente_dict = cls.to_dict(ingrediente)
            
            print(f"\n🔔 [NOTIFICACIONES] ========== INGREDIENTE DESACTIVADO ==========")
            print(f"📦 Ingrediente: {ingrediente_dict['nombre']}")
            print(f"🆔 ID: {ingrediente_dict['id']}")
            
            # 1. Buscar especiales activos que contengan este ingrediente
            especiales_afectados = []
            todos_especiales = Especial.get_all_especiales(only_active=True)
            
            print(f"🔍 Buscando especiales activos...")
            
            for especial in todos_especiales:
                try:
                    especial_dict = Especial.to_dict(especial)
                    if especial_dict.get('ingredientes') and ingrediente_dict.get('nombre'):
                        ingredientes_especial = especial_dict['ingredientes'].lower()
                        ingrediente_nombre = ingrediente_dict['nombre'].lower()
                        
                        if ingrediente_nombre in ingredientes_especial:
                            especiales_afectados.append({
                                'id': especial_dict['id'],
                                'nombre': especial_dict['nombre'],
                                'ingredientes': especial_dict['ingredientes']
                            })
                            print(f"   ✅ Especial afectado: {especial_dict['nombre']}")
                except Exception as e:
                    continue
            
            print(f"📊 Total especiales afectados: {len(especiales_afectados)}")
            
            # 2. Notificar a administradores
            admins = User.get_users_by_role(1) if DB_TYPE == 'mysql' else []
            notificaciones_admin = 0
            
            mensaje_admin = f"El ingrediente '{ingrediente_dict['nombre']}' ha sido marcado como INACTIVO.\n\n"
            
            if especiales_afectados:
                mensaje_admin += f"📋 ESPECIALES AFECTADOS ({len(especiales_afectados)}):\n"
                for i, especial in enumerate(especiales_afectados, 1):
                    mensaje_admin += f"{i}. {especial['nombre']}\n"
            else:
                mensaje_admin += "📋 ESPECIALES AFECTADOS: 0\n"
            
            for admin in admins:
                admin_dict = User.to_dict(admin)
                try:
                    Notificacion.crear_notificacion_admin(
                        admin_id=admin_dict['id'],
                        tipo='ingrediente_inactivo',
                        titulo=f'🚨 INGREDIENTE INACTIVO: {ingrediente_dict["nombre"]}',
                        mensaje=mensaje_admin,
                        datos_adicionales={
                            'ingrediente_id': ingrediente_dict['id'],
                            'ingrediente_nombre': ingrediente_dict['nombre'],
                            'especiales_afectados': especiales_afectados,
                            'total_especiales_afectados': len(especiales_afectados)
                        }
                    )
                    notificaciones_admin += 1
                except:
                    pass
            
            # 3. Notificar a clientes
            clientes = User.get_users_by_role(2) if DB_TYPE == 'mysql' else []
            notificaciones_cliente = 0
            
            if len(clientes) > 0:
                mensaje_cliente = f"ACTUALIZACIÓN IMPORTANTE\n\n"
                mensaje_cliente += f"El ingrediente '{ingrediente_dict['nombre']}' ya no está disponible.\n\n"
                
                if especiales_afectados:
                    mensaje_cliente += "Esto afecta los siguientes especiales del día:\n"
                    for i, especial in enumerate(especiales_afectados[:3], 1):
                        mensaje_cliente += f"• {especial['nombre']}\n"
                    
                    if len(especiales_afectados) > 3:
                        mensaje_cliente += f"• ... y {len(especiales_afectados) - 3} más\n"
                
                for cliente in clientes:
                    cliente_dict = User.to_dict(cliente)
                    try:
                        Notificacion.crear_notificacion_cliente(
                            cliente_id=cliente_dict['id'],
                            tipo='ingrediente_inactivo',
                            titulo=f'⚠️ Actualización de Menú - {ingrediente_dict["nombre"]}',
                            mensaje=mensaje_cliente,
                            datos_adicionales={
                                'ingrediente_id': ingrediente_dict['id'],
                                'ingrediente_nombre': ingrediente_dict['nombre'],
                                'especiales_afectados_count': len(especiales_afectados)
                            }
                        )
                        notificaciones_cliente += 1
                    except:
                        pass
            
            print(f"\n📈 RESUMEN FINAL:")
            print(f"   • Ingrediente: {ingrediente_dict['nombre']}")
            print(f"   • Especiales afectados: {len(especiales_afectados)}")
            print(f"   • Admins notificados: {notificaciones_admin}")
            print(f"   • Clientes notificados: {notificaciones_cliente}")
            print(f"🔔 [NOTIFICACIONES] ========== FIN ==========\n")
            
            return True
            
        except Exception as error:
            print(f"❌ ERROR en _enviar_notificaciones_desactivacion: {error}")
            return False
    
    @classmethod
    def get_by_categoria(cls, categoria, only_active=True):
        """Obtener ingredientes por categoría"""
        return cls.get_all_ingredientes(only_active=only_active, categoria=categoria)
    
    @classmethod
    def get_categorias(cls):
        """Obtener lista de categorías únicas"""
        try:
            if DB_TYPE == 'mysql':
                categorias = IngredienteSQL.query.with_entities(IngredienteSQL.categoria).distinct().all()
                return [cat[0] for cat in categorias if cat[0] is not None]
            else:
                pipeline = [
                    {'$match': {'categoria': {'$ne': None}}},
                    {'$group': {'_id': '$categoria'}}
                ]
                result = cls._get_collection().aggregate(pipeline)
                return [r['_id'] for r in result]
        except:
            return []
    
    @classmethod
    def search_ingredientes(cls, query):
        """Buscar ingredientes por nombre o categoría"""
        try:
            if DB_TYPE == 'mysql':
                if query:
                    return IngredienteSQL.query.filter(
                        (IngredienteSQL.nombre.ilike(f'%{query}%')) | 
                        (IngredienteSQL.categoria.ilike(f'%{query}%'))
                    ).all()
                return IngredienteSQL.query.all()
                
            else:
                import re
                if query:
                    regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                    return list(cls._get_collection().find({
                        '$or': [
                            {'nombre': {'$regex': regex}},
                            {'categoria': {'$regex': regex}}
                        ]
                    }))
                return list(cls._get_collection().find())
        except:
            return []
    
    @classmethod
    def bulk_crear_ingredientes(cls, ingredientes_list):
        """Crear múltiples ingredientes a la vez"""
        creados = []
        for ingrediente_data in ingredientes_list:
            try:
                existente = cls.find_by_name(ingrediente_data['nombre'])
                if not existente:
                    ingrediente_id = cls.create_ingrediente(ingrediente_data)
                    creados.append(ingrediente_id)
            except Exception as e:
                print(f"Error al crear ingrediente {ingrediente_data['nombre']}: {e}")
        
        return creados
    
    @classmethod
    def to_dict(cls, ingrediente):
        """Convertir ingrediente a diccionario"""
        if not ingrediente:
            return None
        
        if DB_TYPE == 'mysql':
            return {
                'id': ingrediente.id,
                'nombre': ingrediente.nombre,
                'categoria': ingrediente.categoria,
                'activo': ingrediente.activo,
                'fecha_creacion': ingrediente.fecha_creacion.isoformat() if ingrediente.fecha_creacion else None,
                'fecha_actualizacion': ingrediente.fecha_actualizacion.isoformat() if ingrediente.fecha_actualizacion else None
            }
        else:
            from bson.objectid import ObjectId
            ingrediente_dict = dict(ingrediente)
            ingrediente_dict['id'] = str(ingrediente_dict.pop('_id'))
            
            if 'fecha_creacion' in ingrediente_dict and ingrediente_dict['fecha_creacion']:
                if isinstance(ingrediente_dict['fecha_creacion'], datetime):
                    ingrediente_dict['fecha_creacion'] = ingrediente_dict['fecha_creacion'].isoformat()
            
            if 'fecha_actualizacion' in ingrediente_dict and ingrediente_dict['fecha_actualizacion']:
                if isinstance(ingrediente_dict['fecha_actualizacion'], datetime):
                    ingrediente_dict['fecha_actualizacion'] = ingrediente_dict['fecha_actualizacion'].isoformat()
            
            return ingrediente_dict

# Para compatibilidad con código existente
if DB_TYPE == 'mysql':
    IngredienteSQL = Ingrediente