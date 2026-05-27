from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class DietaSQL(db_sql.Model):
    __tablename__ = 'dietas'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    nombre = db_sql.Column(db_sql.String(100), nullable=False)
    descripcion = db_sql.Column(db_sql.Text, nullable=False)
    objetivo = db_sql.Column(db_sql.String(50), nullable=False, default='perder_peso')
    duracion_dias = db_sql.Column(db_sql.Integer, nullable=False, default=7)
    calorias_diarias = db_sql.Column(db_sql.Integer, nullable=False, default=2000)
    nivel_actividad = db_sql.Column(db_sql.String(50), nullable=False, default='moderado')
    restricciones = db_sql.Column(db_sql.Text, nullable=True)  # JSON string
    comidas_por_dia = db_sql.Column(db_sql.Integer, nullable=False, default=3)
    plan_alimentacion = db_sql.Column(db_sql.Text, nullable=True)  # JSON string
    activo = db_sql.Column(db_sql.Boolean, default=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Dieta {self.nombre}>'
    
    def to_dict(self):
        """Convertir a diccionario"""
        import json
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'objetivo': self.objetivo,
            'objetivo_nombre': Dieta.OBJETIVOS.get(self.objetivo, self.objetivo),
            'duracion_dias': self.duracion_dias,
            'calorias_diarias': self.calorias_diarias,
            'nivel_actividad': self.nivel_actividad,
            'nivel_actividad_nombre': Dieta.NIVELES_ACTIVIDAD.get(self.nivel_actividad, self.nivel_actividad),
            'restricciones': json.loads(self.restricciones) if self.restricciones else [],
            'comidas_por_dia': self.comidas_por_dia,
            'plan_alimentacion': json.loads(self.plan_alimentacion) if self.plan_alimentacion else None,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

# ============================================
# MODELO PARA MySQL - DIETA PERSONALIZADA POR USUARIO
# ============================================
class DietaUsuarioSQL(db_sql.Model):
    __tablename__ = 'dietas_usuario'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    usuario_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('users.id'), nullable=False)  # Cambiado a 'users.id'
    dieta_base_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('dietas.id'), nullable=True)
    nombre = db_sql.Column(db_sql.String(100), nullable=False)
    descripcion = db_sql.Column(db_sql.Text, nullable=True)
    fecha_inicio = db_sql.Column(db_sql.DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin = db_sql.Column(db_sql.DateTime, nullable=True)
    perfil_usuario = db_sql.Column(db_sql.Text, nullable=True)  # JSON con datos del perfil
    plan_generado = db_sql.Column(db_sql.Text, nullable=False)  # JSON con el plan completo
    progreso = db_sql.Column(db_sql.Integer, default=0)  # Porcentaje de progreso
    activo = db_sql.Column(db_sql.Boolean, default=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DietaUsuario {self.nombre} - Usuario: {self.usuario_id}>'
    
    def to_dict(self):
        """Convertir a diccionario"""
        import json
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'dieta_base_id': self.dieta_base_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'perfil_usuario': json.loads(self.perfil_usuario) if self.perfil_usuario else {},
            'plan_generado': json.loads(self.plan_generado) if self.plan_generado else {},
            'progreso': self.progreso,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

# ============================================
# MODELO PARA MySQL - SEGUIMIENTO DIARIO
# ============================================
class SeguimientoDietaSQL(db_sql.Model):
    __tablename__ = 'seguimiento_dieta'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    dieta_usuario_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('dietas_usuario.id'), nullable=False)
    dia_numero = db_sql.Column(db_sql.Integer, nullable=False)
    fecha = db_sql.Column(db_sql.Date, nullable=False, default=datetime.utcnow().date)
    completado = db_sql.Column(db_sql.Boolean, default=False)
    comidas_completadas = db_sql.Column(db_sql.Text, nullable=True)  # JSON con IDs de comidas completadas
    calorias_consumidas = db_sql.Column(db_sql.Integer, default=0)
    agua_consumida = db_sql.Column(db_sql.Float, default=0)  # En litros
    notas = db_sql.Column(db_sql.Text, nullable=True)
    fecha_creacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db_sql.Column(db_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Seguimiento Dieta {self.dieta_usuario_id} - Día {self.dia_numero}>'
    
    def to_dict(self):
        """Convertir a diccionario"""
        import json
        return {
            'id': self.id,
            'dieta_usuario_id': self.dieta_usuario_id,
            'dia_numero': self.dia_numero,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'completado': self.completado,
            'comidas_completadas': json.loads(self.comidas_completadas) if self.comidas_completadas else [],
            'calorias_consumidas': self.calorias_consumidas,
            'agua_consumida': self.agua_consumida,
            'notas': self.notas,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }

# ============================================
# CLASE PRINCIPAL
# ============================================
class Dieta:
    """Clase que maneja dietas en ambas bases de datos"""
    
    # Objetivos disponibles
    OBJETIVOS = {
        'perder_peso': 'Perder Peso',
        'mantener': 'Mantener Peso',
        'ganar_musculo': 'Ganar Músculo',
        'definicion': 'Definición Muscular',
        'volumen': 'Volumen',
        'saludable': 'Alimentación Saludable'
    }
    
    # Niveles de actividad
    NIVELES_ACTIVIDAD = {
        'sedentario': 'Sedentario (poco o ningún ejercicio)',
        'ligero': 'Ligero (ejercicio 1-3 días/semana)',
        'moderado': 'Moderado (ejercicio 3-5 días/semana)',
        'activo': 'Activo (ejercicio 6-7 días/semana)',
        'muy_activo': 'Muy Activo (ejercicio diario intenso)'
    }
    
    # Tipos de comidas
    TIPOS_COMIDA = {
        'desayuno': 'Desayuno',
        'colacion_am': 'Colación AM',
        'comida': 'Comida',
        'colacion_pm': 'Colación PM',
        'cena': 'Cena',
        'colacion_nocturna': 'Colación Nocturna',
        'post_entreno': 'Post-Entreno'
    }
    
    # Restricciones alimenticias comunes
    RESTRICCIONES = {
        'vegetariano': 'Vegetariano',
        'vegano': 'Vegano',
        'sin_gluten': 'Sin Gluten',
        'sin_lactosa': 'Sin Lactosa',
        'bajo_carbohidratos': 'Bajo en Carbohidratos',
        'bajo_grasas': 'Bajo en Grasas',
        'alto_proteina': 'Alto en Proteína',
        'dieta_keto': 'Dieta Keto',
        'paleo': 'Paleo',
        'mediterranea': 'Mediterránea',
        'dash': 'Dieta DASH',
        'ayuno_intermitente': 'Ayuno Intermitente'
    }
    
    @classmethod
    def _get_collection(cls):
        """Obtener colección de MongoDB para dietas base"""
        return db_mongo.db.dietas
    
    @classmethod
    def _get_usuario_collection(cls):
        """Obtener colección de MongoDB para dietas de usuario"""
        return db_mongo.db.dietas_usuario
    
    @classmethod
    def _get_seguimiento_collection(cls):
        """Obtener colección de MongoDB para seguimiento"""
        return db_mongo.db.seguimiento_dieta
    
    # ========== MÉTODOS PARA DIETAS BASE ==========
    
    @classmethod
    def find_by_id(cls, dieta_id):
        """Buscar dieta base por ID"""
        try:
            if DB_TYPE == 'mysql':
                return DietaSQL.query.get(dieta_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_collection().find_one({'_id': ObjectId(dieta_id)})
        except:
            return None
    
    @classmethod
    def find_by_name(cls, nombre):
        """Buscar dieta base por nombre"""
        try:
            if DB_TYPE == 'mysql':
                return DietaSQL.query.filter_by(nombre=nombre).first()
            else:
                return cls._get_collection().find_one({'nombre': nombre})
        except:
            return None

    @classmethod
    def get_all_dietas(cls, only_active=True):
        """Obtener todas las dietas base"""
        try:
            if DB_TYPE == 'mysql':
                if only_active:
                    return DietaSQL.query.filter_by(activo=True).all()
                return DietaSQL.query.all()
            else:
                query = {}
                if only_active:
                    query['activo'] = True
                return list(cls._get_collection().find(query))
        except Exception as e:
            print(f"Error en get_all_dietas: {e}")
            return []
    
    @classmethod
    def create_dieta(cls, dieta_data):
        """Crear nueva dieta base"""
        try:
            if DB_TYPE == 'mysql':
                import json
                print(f"Creando dieta en MySQL: {dieta_data}")
                dieta = DietaSQL(
                    nombre=dieta_data['nombre'],
                    descripcion=dieta_data.get('descripcion', ''),
                    objetivo=dieta_data.get('objetivo', 'perder_peso'),
                    duracion_dias=dieta_data.get('duracion_dias', 7),
                    calorias_diarias=dieta_data.get('calorias_diarias', 2000),
                    nivel_actividad=dieta_data.get('nivel_actividad', 'moderado'),
                    restricciones=json.dumps(dieta_data.get('restricciones', [])),
                    comidas_por_dia=dieta_data.get('comidas_por_dia', 3),
                    plan_alimentacion=json.dumps(dieta_data.get('plan_alimentacion', {})),
                    activo=dieta_data.get('activo', True)
                )
                
                db_sql.session.add(dieta)
                db_sql.session.commit()
                print(f"✅ Dieta creada con ID: {dieta.id}")
                return dieta.id
                
            else:
                from bson.objectid import ObjectId
                
                dieta_doc = {
                    'nombre': dieta_data['nombre'],
                    'descripcion': dieta_data.get('descripcion', ''),
                    'objetivo': dieta_data.get('objetivo', 'perder_peso'),
                    'duracion_dias': dieta_data.get('duracion_dias', 7),
                    'calorias_diarias': dieta_data.get('calorias_diarias', 2000),
                    'nivel_actividad': dieta_data.get('nivel_actividad', 'moderado'),
                    'restricciones': dieta_data.get('restricciones', []),
                    'comidas_por_dia': dieta_data.get('comidas_por_dia', 3),
                    'plan_alimentacion': dieta_data.get('plan_alimentacion', {}),
                    'activo': dieta_data.get('activo', True),
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_collection().insert_one(dieta_doc)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"❌ Error en create_dieta: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_dieta(cls, dieta_id, update_data):
        """Actualizar dieta base"""
        try:
            if DB_TYPE == 'mysql':
                import json
                dieta = DietaSQL.query.get(dieta_id)
                if not dieta:
                    return False
                
                if 'nombre' in update_data:
                    dieta.nombre = update_data['nombre']
                if 'descripcion' in update_data:
                    dieta.descripcion = update_data['descripcion']
                if 'objetivo' in update_data:
                    dieta.objetivo = update_data['objetivo']
                if 'duracion_dias' in update_data:
                    dieta.duracion_dias = update_data['duracion_dias']
                if 'calorias_diarias' in update_data:
                    dieta.calorias_diarias = update_data['calorias_diarias']
                if 'nivel_actividad' in update_data:
                    dieta.nivel_actividad = update_data['nivel_actividad']
                if 'restricciones' in update_data:
                    dieta.restricciones = json.dumps(update_data['restricciones'])
                if 'comidas_por_dia' in update_data:
                    dieta.comidas_por_dia = update_data['comidas_por_dia']
                if 'plan_alimentacion' in update_data:
                    dieta.plan_alimentacion = json.dumps(update_data['plan_alimentacion'])
                if 'activo' in update_data:
                    dieta.activo = update_data['activo']
                
                dieta.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                
                if 'restricciones' in update_data and isinstance(update_data['restricciones'], list):
                    update_data['restricciones'] = update_data['restricciones']
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_collection().update_one(
                    {'_id': ObjectId(dieta_id)},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_dieta: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def delete_dieta(cls, dieta_id):
        """Eliminar dieta base"""
        try:
            if DB_TYPE == 'mysql':
                dieta = DietaSQL.query.get(dieta_id)
                if not dieta:
                    return False
                
                db_sql.session.delete(dieta)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_collection().delete_one({'_id': ObjectId(dieta_id)})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_dieta: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def get_by_objetivo(cls, objetivo):
        """Obtener dietas por objetivo"""
        try:
            if DB_TYPE == 'mysql':
                return DietaSQL.query.filter_by(objetivo=objetivo, activo=True).all()
            else:
                return list(cls._get_collection().find({'objetivo': objetivo, 'activo': True}))
        except Exception as e:
            print(f"Error en get_by_objetivo: {e}")
            return []
    
    @classmethod
    def get_by_restriccion(cls, restriccion):
        """Obtener dietas que cumplan con una restricción"""
        try:
            if DB_TYPE == 'mysql':
                import json
                all_dietas = DietaSQL.query.filter_by(activo=True).all()
                return [d for d in all_dietas if restriccion in json.loads(d.restricciones or '[]')]
            else:
                return list(cls._get_collection().find({
                    'restricciones': restriccion,
                    'activo': True
                }))
        except Exception as e:
            print(f"Error en get_by_restriccion: {e}")
            return []
    
    # ========== MÉTODOS PARA DIETAS DE USUARIO ==========
    
    @classmethod
    def find_usuario_dieta_by_id(cls, dieta_usuario_id):
        """Buscar dieta de usuario por ID"""
        try:
            if DB_TYPE == 'mysql':
                return DietaUsuarioSQL.query.get(dieta_usuario_id)
            else:
                from bson.objectid import ObjectId
                return cls._get_usuario_collection().find_one({'_id': ObjectId(dieta_usuario_id)})
        except:
            return None
    
    @classmethod
    def get_dietas_by_usuario(cls, usuario_id):
        """Obtener todas las dietas de un usuario"""
        try:
            if DB_TYPE == 'mysql':
                return DietaUsuarioSQL.query.filter_by(usuario_id=usuario_id).order_by(DietaUsuarioSQL.fecha_creacion.desc()).all()
            else:
                return list(cls._get_usuario_collection().find({'usuario_id': usuario_id}).sort('fecha_creacion', -1))
        except Exception as e:
            print(f"Error en get_dietas_by_usuario: {e}")
            return []
    
    @classmethod
    def get_dieta_activa_usuario(cls, usuario_id):
        """Obtener la dieta activa de un usuario"""
        try:
            if DB_TYPE == 'mysql':
                return DietaUsuarioSQL.query.filter_by(usuario_id=usuario_id, activo=True).first()
            else:
                return cls._get_usuario_collection().find_one({'usuario_id': usuario_id, 'activo': True})
        except Exception as e:
            print(f"Error en get_dieta_activa_usuario: {e}")
            return None
    
    @classmethod
    def crear_dieta_usuario(cls, usuario_id, dieta_data):
        """Crear una nueva dieta personalizada para un usuario"""
        try:
            if DB_TYPE == 'mysql':
                import json
                
                dieta_usuario = DietaUsuarioSQL(
                    usuario_id=usuario_id,
                    dieta_base_id=dieta_data.get('dieta_base_id'),
                    nombre=dieta_data['nombre'],
                    descripcion=dieta_data.get('descripcion', ''),
                    fecha_inicio=datetime.utcnow(),
                    fecha_fin=dieta_data.get('fecha_fin'),
                    perfil_usuario=json.dumps(dieta_data.get('perfil_usuario', {})),
                    plan_generado=json.dumps(dieta_data['plan_generado']),
                    progreso=0,
                    activo=True
                )
                
                db_sql.session.add(dieta_usuario)
                db_sql.session.commit()
                
                # Crear registros de seguimiento para cada día
                plan = dieta_data['plan_generado']
                if 'dias' in plan:
                    for dia in plan['dias']:
                        seguimiento = SeguimientoDietaSQL(
                            dieta_usuario_id=dieta_usuario.id,
                            dia_numero=dia.get('dia', 0),
                            fecha=datetime.strptime(dia.get('fecha', datetime.utcnow().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                            completado=False,
                            comidas_completadas=json.dumps([]),
                            calorias_consumidas=0,
                            agua_consumida=0
                        )
                        db_sql.session.add(seguimiento)
                    
                    db_sql.session.commit()
                
                return dieta_usuario.id
                
            else:
                from bson.objectid import ObjectId
                
                dieta_usuario_doc = {
                    'usuario_id': usuario_id,
                    'dieta_base_id': dieta_data.get('dieta_base_id'),
                    'nombre': dieta_data['nombre'],
                    'descripcion': dieta_data.get('descripcion', ''),
                    'fecha_inicio': datetime.utcnow(),
                    'fecha_fin': dieta_data.get('fecha_fin'),
                    'perfil_usuario': dieta_data.get('perfil_usuario', {}),
                    'plan_generado': dieta_data['plan_generado'],
                    'progreso': 0,
                    'activo': True,
                    'fecha_creacion': datetime.utcnow(),
                    'fecha_actualizacion': datetime.utcnow()
                }
                
                result = cls._get_usuario_collection().insert_one(dieta_usuario_doc)
                dieta_usuario_id = str(result.inserted_id)
                
                # Crear registros de seguimiento para cada día
                plan = dieta_data['plan_generado']
                if 'dias' in plan:
                    for dia in plan['dias']:
                        seguimiento_doc = {
                            'dieta_usuario_id': dieta_usuario_id,
                            'dia_numero': dia.get('dia', 0),
                            'fecha': datetime.strptime(dia.get('fecha', datetime.utcnow().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
                            'completado': False,
                            'comidas_completadas': [],
                            'calorias_consumidas': 0,
                            'agua_consumida': 0,
                            'fecha_creacion': datetime.utcnow(),
                            'fecha_actualizacion': datetime.utcnow()
                        }
                        cls._get_seguimiento_collection().insert_one(seguimiento_doc)
                
                return dieta_usuario_id
                
        except Exception as e:
            print(f"❌ Error en crear_dieta_usuario: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            raise e
    
    @classmethod
    def update_dieta_usuario(cls, dieta_usuario_id, update_data):
        """Actualizar dieta de usuario"""
        try:
            if DB_TYPE == 'mysql':
                import json
                dieta = DietaUsuarioSQL.query.get(dieta_usuario_id)
                if not dieta:
                    return False
                
                if 'nombre' in update_data:
                    dieta.nombre = update_data['nombre']
                if 'descripcion' in update_data:
                    dieta.descripcion = update_data['descripcion']
                if 'fecha_fin' in update_data:
                    dieta.fecha_fin = update_data['fecha_fin']
                if 'perfil_usuario' in update_data:
                    dieta.perfil_usuario = json.dumps(update_data['perfil_usuario'])
                if 'plan_generado' in update_data:
                    dieta.plan_generado = json.dumps(update_data['plan_generado'])
                if 'progreso' in update_data:
                    dieta.progreso = update_data['progreso']
                if 'activo' in update_data:
                    dieta.activo = update_data['activo']
                
                dieta.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                
                if 'perfil_usuario' in update_data and isinstance(update_data['perfil_usuario'], dict):
                    update_data['perfil_usuario'] = update_data['perfil_usuario']
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_usuario_collection().update_one(
                    {'_id': ObjectId(dieta_usuario_id)},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_dieta_usuario: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    # ========== MÉTODOS PARA SEGUIMIENTO ==========
    
    @classmethod
    def get_seguimiento_by_dieta(cls, dieta_usuario_id):
        """Obtener todo el seguimiento de una dieta"""
        try:
            if DB_TYPE == 'mysql':
                return SeguimientoDietaSQL.query.filter_by(dieta_usuario_id=dieta_usuario_id).order_by(SeguimientoDietaSQL.dia_numero).all()
            else:
                return list(cls._get_seguimiento_collection().find({'dieta_usuario_id': dieta_usuario_id}).sort('dia_numero', 1))
        except Exception as e:
            print(f"Error en get_seguimiento_by_dieta: {e}")
            return []
    
    @classmethod
    def get_seguimiento_dia(cls, dieta_usuario_id, dia_numero):
        """Obtener seguimiento de un día específico"""
        try:
            if DB_TYPE == 'mysql':
                return SeguimientoDietaSQL.query.filter_by(dieta_usuario_id=dieta_usuario_id, dia_numero=dia_numero).first()
            else:
                return cls._get_seguimiento_collection().find_one({
                    'dieta_usuario_id': dieta_usuario_id,
                    'dia_numero': dia_numero
                })
        except Exception as e:
            print(f"Error en get_seguimiento_dia: {e}")
            return None
    
    @classmethod
    def actualizar_seguimiento(cls, seguimiento_id, update_data):
        """Actualizar seguimiento de un día"""
        try:
            if DB_TYPE == 'mysql':
                import json
                seguimiento = SeguimientoDietaSQL.query.get(seguimiento_id)
                if not seguimiento:
                    return False
                
                if 'completado' in update_data:
                    seguimiento.completado = update_data['completado']
                if 'comidas_completadas' in update_data:
                    seguimiento.comidas_completadas = json.dumps(update_data['comidas_completadas'])
                if 'calorias_consumidas' in update_data:
                    seguimiento.calorias_consumidas = update_data['calorias_consumidas']
                if 'agua_consumida' in update_data:
                    seguimiento.agua_consumida = update_data['agua_consumida']
                if 'notas' in update_data:
                    seguimiento.notas = update_data['notas']
                
                seguimiento.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                
                # Actualizar progreso de la dieta
                cls._actualizar_progreso_dieta(seguimiento.dieta_usuario_id)
                
                return True
                
            else:
                from bson.objectid import ObjectId
                
                if 'comidas_completadas' in update_data and isinstance(update_data['comidas_completadas'], list):
                    update_data['comidas_completadas'] = update_data['comidas_completadas']
                
                update_data['fecha_actualizacion'] = datetime.utcnow()
                
                result = cls._get_seguimiento_collection().update_one(
                    {'_id': ObjectId(seguimiento_id)},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    # Obtener el seguimiento para actualizar progreso de la dieta
                    seguimiento = cls._get_seguimiento_collection().find_one({'_id': ObjectId(seguimiento_id)})
                    if seguimiento:
                        cls._actualizar_progreso_dieta(seguimiento['dieta_usuario_id'])
                
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en actualizar_seguimiento: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def _actualizar_progreso_dieta(cls, dieta_usuario_id):
        """Actualizar el progreso total de una dieta"""
        try:
            seguimientos = cls.get_seguimiento_by_dieta(dieta_usuario_id)
            if not seguimientos:
                return
            
            total_dias = len(seguimientos)
            dias_completados = sum(1 for s in seguimientos if (s.completado if DB_TYPE == 'mysql' else s.get('completado', False)))
            
            progreso = int((dias_completados / total_dias) * 100) if total_dias > 0 else 0
            
            cls.update_dieta_usuario(dieta_usuario_id, {'progreso': progreso})
            
        except Exception as e:
            print(f"Error en _actualizar_progreso_dieta: {e}")
    
    @classmethod
    def marcar_comida_completada(cls, seguimiento_id, comida_id, completado):
        """Marcar una comida específica como completada/no completada"""
        try:
            if DB_TYPE == 'mysql':
                import json
                seguimiento = SeguimientoDietaSQL.query.get(seguimiento_id)
                if not seguimiento:
                    return False
                
                comidas = json.loads(seguimiento.comidas_completadas or '[]')
                
                if completado and comida_id not in comidas:
                    comidas.append(comida_id)
                elif not completado and comida_id in comidas:
                    comidas.remove(comida_id)
                
                seguimiento.comidas_completadas = json.dumps(comidas)
                
                # Verificar si todas las comidas del día están completadas
                dieta_usuario = cls.find_usuario_dieta_by_id(seguimiento.dieta_usuario_id)
                if dieta_usuario and DB_TYPE == 'mysql':
                    plan = json.loads(dieta_usuario.plan_generado)
                    dia = next((d for d in plan.get('dias', []) if d.get('dia') == seguimiento.dia_numero), None)
                    if dia:
                        total_comidas = len(dia.get('comidas', []))
                        seguimiento.completado = len(comidas) >= total_comidas
                
                seguimiento.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                
                cls._actualizar_progreso_dieta(seguimiento.dieta_usuario_id)
                
                return True
                
            else:
                from bson.objectid import ObjectId
                
                seguimiento = cls._get_seguimiento_collection().find_one({'_id': ObjectId(seguimiento_id)})
                if not seguimiento:
                    return False
                
                comidas = seguimiento.get('comidas_completadas', [])
                
                if completado and comida_id not in comidas:
                    comidas.append(comida_id)
                elif not completado and comida_id in comidas:
                    comidas.remove(comida_id)
                
                # Verificar si todas las comidas del día están completadas
                dieta_usuario = cls.find_usuario_dieta_by_id(seguimiento['dieta_usuario_id'])
                if dieta_usuario:
                    plan = dieta_usuario.get('plan_generado', {})
                    dia = next((d for d in plan.get('dias', []) if d.get('dia') == seguimiento['dia_numero']), None)
                    if dia:
                        total_comidas = len(dia.get('comidas', []))
                        completado_dia = len(comidas) >= total_comidas
                    else:
                        completado_dia = False
                else:
                    completado_dia = False
                
                result = cls._get_seguimiento_collection().update_one(
                    {'_id': ObjectId(seguimiento_id)},
                    {'$set': {
                        'comidas_completadas': comidas,
                        'completado': completado_dia,
                        'fecha_actualizacion': datetime.utcnow()
                    }}
                )
                
                if result.modified_count > 0:
                    cls._actualizar_progreso_dieta(seguimiento['dieta_usuario_id'])
                
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en marcar_comida_completada: {e}")
            if DB_TYPE == 'mysql':
                db_sql.session.rollback()
            return False
    
    @classmethod
    def registrar_agua(cls, seguimiento_id, litros):
        """Registrar consumo de agua"""
        try:
            if DB_TYPE == 'mysql':
                seguimiento = SeguimientoDietaSQL.query.get(seguimiento_id)
                if not seguimiento:
                    return False
                
                seguimiento.agua_consumida = litros
                seguimiento.fecha_actualizacion = datetime.utcnow()
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = cls._get_seguimiento_collection().update_one(
                    {'_id': ObjectId(seguimiento_id)},
                    {'$set': {
                        'agua_consumida': litros,
                        'fecha_actualizacion': datetime.utcnow()
                    }}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en registrar_agua: {e}")
            return False
    
    @classmethod
    def search_dietas(cls, query):
        """Buscar dietas base por nombre o descripción"""
        try:
            if DB_TYPE == 'mysql':
                if query:
                    return DietaSQL.query.filter(
                        (DietaSQL.nombre.ilike(f'%{query}%')) | 
                        (DietaSQL.descripcion.ilike(f'%{query}%'))
                    ).all()
                return DietaSQL.query.all()
                
            else:
                import re
                if query:
                    regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                    return list(cls._get_collection().find({
                        '$or': [
                            {'nombre': {'$regex': regex}},
                            {'descripcion': {'$regex': regex}}
                        ]
                    }))
                return list(cls._get_collection().find())
                
        except Exception as e:
            print(f"Error en search_dietas: {e}")
            return []
    
    @classmethod
    def to_dict(cls, dieta, tipo='base'):
        """Convertir dieta a diccionario según el tipo"""
        if not dieta:
            return None
        
        if DB_TYPE == 'mysql':
            if tipo == 'base':
                return dieta.to_dict()
            elif tipo == 'usuario':
                return dieta.to_dict()
            elif tipo == 'seguimiento':
                return dieta.to_dict()
        else:
            from bson.objectid import ObjectId
            dieta_dict = dict(dieta)
            dieta_dict['id'] = str(dieta_dict.pop('_id'))
            
            # Agregar nombres legibles según el tipo
            if tipo == 'base':
                if 'objetivo' in dieta_dict:
                    dieta_dict['objetivo_nombre'] = cls.OBJETIVOS.get(dieta_dict['objetivo'], dieta_dict['objetivo'])
                if 'nivel_actividad' in dieta_dict:
                    dieta_dict['nivel_actividad_nombre'] = cls.NIVELES_ACTIVIDAD.get(dieta_dict['nivel_actividad'], dieta_dict['nivel_actividad'])
            
            # Convertir fechas
            for campo in ['fecha_creacion', 'fecha_actualizacion', 'fecha_inicio', 'fecha_fin']:
                if campo in dieta_dict and dieta_dict[campo]:
                    if isinstance(dieta_dict[campo], datetime):
                        dieta_dict[campo] = dieta_dict[campo].isoformat()
            
            if 'fecha' in dieta_dict and dieta_dict['fecha']:
                if hasattr(dieta_dict['fecha'], 'isoformat'):
                    dieta_dict['fecha'] = dieta_dict['fecha'].isoformat()
            
            return dieta_dict