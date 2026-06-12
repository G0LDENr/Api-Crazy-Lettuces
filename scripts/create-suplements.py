import random
from datetime import datetime
from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, Boolean, DateTime, text, func
from sqlalchemy.orm import sessionmaker

# Configuración de tu base de datos MySQL
DATABASE_URL = "mysql+pymysql://root:131023@localhost:3307/crazylettuces"

# Crear engine y sesión
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# Inicializar Faker
fake = Faker('es_ES')

# Listas predefinidas
CATEGORIAS = ['quemadores', 'proteinas', 'vitaminas', 'minerales', 
              'pre-entreno', 'post-entreno', 'aminoacidos', 'creatina', 
              'ganadores de peso', 'recuperacion', 'termogenicos', 'detox']

PRESENTACIONES = ['polvo', 'capsulas', 'tabletas', 'liquido', 'barritas', 'geles', 'spray']

NOMBRES_REALES = [
    'Whey Protein Gold', 'Creatina Monohidrato', 'BCAA 2:1:1', 'Glutamina Pura',
    'Omega 3 Premium', 'Multivitamínico Diario', 'Termogénico Extreme', 'Caseína Nocturna',
    'L-Carnitina Líquida', 'ZMA Plus', 'Beta Alanina', 'Citrulina Malato',
    'Arginina AKG', 'Tribulus Terrestris', 'Ashwagandha KSM-66', 'Maca Peruana Orgánica',
    'Colágeno Hidrolizado', 'Magnesio Quelado', 'Zinc Picolinato', 'Vitamina D3',
    'CLA Quemador', 'Garcinia Cambogia', 'Té Verde EGCG', 'Espirulina', 'Clorofila Líquida',
    'Proteína Vegana', 'Gainer Extreme', 'Pre-Workout Black', 'Recuperador Post-Entreno',
    'Electrolitos Hidratación', 'Melatonina Sueño', '5-HTP Estado de Ánimo'
]

BENEFICIOS_PLANTILLA = [
    "Aumenta la energía y vitalidad",
    "Mejora el rendimiento deportivo",
    "Acelera el metabolismo",
    "Ayuda en la recuperación muscular",
    "Fortalece el sistema inmunológico",
    "Mejora la concentración",
    "Reduce la fatiga",
    "Aumenta la masa muscular",
    "Quema grasa corporal",
    "Mejora la digestión",
    "Reduce el estrés oxidativo",
    "Mejora la calidad del sueño",
    "Fortalece huesos y articulaciones",
    "Regula el apetito",
    "Mejora la absorción de nutrientes"
]

def generar_suplemento():
    """Genera un diccionario con datos de un suplemento"""
    nombre = random.choice(NOMBRES_REALES)
    if random.random() < 0.3:
        nombre = f"{nombre} {random.randint(1, 10)}X"
    
    categoria = random.choice(CATEGORIAS)
    presentacion = random.choice(PRESENTACIONES)
    
    descripciones = [
        f"Suplemento premium de {categoria} diseñado para {fake.sentence()}",
        f"{nombre} es un producto de alta calidad que {fake.paragraph(nb_sentences=2)}",
        f"Fórmula avanzada de {categoria} con {random.choice(['tecnología exclusiva', 'ingredientes naturales', 'alta concentración', 'máxima absorción'])}"
    ]
    descripcion = random.choice(descripciones)
    
    # Precio realista según categoría
    if categoria in ['proteinas', 'ganadores de peso']:
        precio = round(random.uniform(25, 80), 2)
    elif categoria in ['quemadores', 'termogenicos']:
        precio = round(random.uniform(30, 70), 2)
    elif categoria in ['vitaminas', 'minerales']:
        precio = round(random.uniform(15, 45), 2)
    else:
        precio = round(random.uniform(20, 60), 2)
    
    # Beneficios
    num_beneficios = random.randint(3, 6)
    beneficios_seleccionados = random.sample(BENEFICIOS_PLANTILLA, num_beneficios)
    beneficios = "\n".join(f"• {b}" for b in beneficios_seleccionados)
    
    # Modo de uso
    if presentacion == 'polvo':
        cantidad = random.choice(["1", "2", "3", "una", "dos"])
        dosis = f"{cantidad} {'cucharada' if cantidad in ['una', 'dos'] else 'cucharadas'}"
        modo_uso = f"Mezclar {dosis} de {nombre} con 200-300ml de agua. Consumir {random.choice(['antes', 'después'])} del entrenamiento."
    elif presentacion in ['capsulas', 'tabletas']:
        dosis = random.randint(1, 3)
        modo_uso = f"Tomar {dosis} {presentacion} {random.choice(['con agua', 'con las comidas', 'en ayunas'])}."
    elif presentacion == 'liquido':
        modo_uso = f"Consumir {random.choice(['1', '2'])} ml directamente o diluido en agua."
    else:
        modo_uso = f"Consumir {random.choice(['antes', 'durante', 'después'])} de la actividad física."
    
    stock = random.choice([0] + list(range(10, 500, 25)))
    activo = random.random() < 0.85
    
    fecha_creacion = fake.date_time_between(start_date='-1y', end_date='now')
    fecha_actualizacion = fake.date_time_between(start_date=fecha_creacion, end_date='now')
    
    return {
        'nombre': nombre[:100],
        'descripcion': descripcion,
        'precio': precio,
        'categoria': categoria,
        'presentacion': presentacion,
        'beneficios': beneficios[:500],
        'modo_uso': modo_uso[:500],
        'stock': stock,
        'activo': activo,
        'fecha_creacion': fecha_creacion,
        'fecha_actualizacion': fecha_actualizacion
    }

def insertar_suplementos(cantidad=1000, batch_size=100):
    """Inserta registros directamente usando SQL"""
    print(f"Conectando a: {DATABASE_URL}")
    print(f"Iniciando inserción de {cantidad} registros...\n")
    
    registros_insertados = 0
    
    try:
        # Verificar conexión
        session.execute(text("SELECT 1"))
        print("✅ Conexión a MySQL establecida correctamente\n")
        
        # SQL para insertar (sin especificar ID para que sea autoincremental)
        insert_sql = text("""
            INSERT INTO suplementos 
            (nombre, descripcion, precio, categoria, presentacion, 
             beneficios, modo_uso, stock, activo, fecha_creacion, fecha_actualizacion)
            VALUES 
            (:nombre, :descripcion, :precio, :categoria, :presentacion, 
             :beneficios, :modo_uso, :stock, :activo, :fecha_creacion, :fecha_actualizacion)
        """)
        
        for i in range(0, cantidad, batch_size):
            lote = []
            for j in range(batch_size):
                if registros_insertados + j >= cantidad:
                    break
                lote.append(generar_suplemento())
            
            if lote:
                # Insertar lote
                for registro in lote:
                    session.execute(insert_sql, registro)
                session.commit()
                registros_insertados += len(lote)
                
                # Mostrar progreso
                porcentaje = (registros_insertados / cantidad) * 100
                barra = "█" * int(porcentaje // 2) + "░" * (50 - int(porcentaje // 2))
                print(f"\r[{barra}] {porcentaje:.1f}% - {registros_insertados}/{cantidad} registros", end="")
        
        print(f"\n\n✅ ¡Completado! Se insertaron {registros_insertados} registros correctamente.")
        
        # Mostrar estadísticas
        mostrar_estadisticas()
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error durante la inserción: {e}")
        raise
    finally:
        session.close()

def mostrar_estadisticas():
    """Muestra estadísticas de los datos insertados"""
    try:
        total = session.execute(text("SELECT COUNT(*) FROM suplementos")).scalar()
        
        categorias = session.execute(text("""
            SELECT categoria, COUNT(*) 
            FROM suplementos 
            GROUP BY categoria 
            ORDER BY COUNT(*) DESC
        """)).fetchall()
        
        precio_promedio = session.execute(text("SELECT AVG(precio) FROM suplementos")).scalar()
        stock_total = session.execute(text("SELECT SUM(stock) FROM suplementos")).scalar()
        
        print("\n📊 Estadísticas de la tabla 'suplementos':")
        print(f"  • Total registros: {total}")
        if precio_promedio:
            print(f"  • Precio promedio: ${precio_promedio:.2f}")
        print(f"  • Stock total: {stock_total or 0} unidades")
        print(f"\n  • Distribución por categoría:")
        for categoria, count in categorias:
            print(f"    - {categoria}: {count}")
            
    except Exception as e:
        print(f"Error al mostrar estadísticas: {e}")

# Ejecutar el script
if __name__ == "__main__":
    print("=" * 60)
    print("SCRIPT DE INSERCIÓN DE SUPLEMENTOS")
    print("=" * 60)
    
    # Verificar conexión
    try:
        engine.connect()
        print("✅ Conexión a la base de datos exitosa\n")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\nVerifica que:")
        print("1. MySQL esté corriendo en localhost:3307")
        print("2. La base de datos 'crazylettuces' exista")
        print("3. Las credenciales sean correctas")
        exit(1)
    
    # Insertar registros
    insertar_suplementos(cantidad=1000, batch_size=100)