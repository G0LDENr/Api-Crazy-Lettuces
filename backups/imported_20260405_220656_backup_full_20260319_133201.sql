-- Backup generado el 2026-03-19 13:32:01
-- Tipo: FULL
-- DB_TYPE: mysql
SET FOREIGN_KEY_CHECKS=0;

-- Estructura de la tabla: alembic_version
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: alembic_version
INSERT INTO `alembic_version` (`version_num`) VALUES 
  ('fb8d4127d9b3');
-- Fin de datos para tabla: alembic_version

-- Estructura de la tabla: backups
CREATE TABLE `backups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `filepath` varchar(500) NOT NULL,
  `size_mb` float DEFAULT NULL,
  `tables_included` text,
  `backup_type` varchar(50) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: backups
INSERT INTO `backups` (`id`, `filename`, `filepath`, `size_mb`, `tables_included`, `backup_type`, `status`, `created_at`) VALUES 
  (4, 'backup_partial_20260319_133154.sql.gz', 'C:\Proyects\Proyect-CrazyLettuces\Api-CrazyLettuces\backups\backup_partial_20260319_133154.sql.gz', 0.0, '["suplementos"]', 'partial', 'completed', '2026-03-19 19:31:55');
-- Fin de datos para tabla: backups

-- Estructura de la tabla: dietas
CREATE TABLE `dietas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text NOT NULL,
  `objetivo` varchar(50) NOT NULL,
  `duracion_dias` int NOT NULL,
  `calorias_diarias` int NOT NULL,
  `nivel_actividad` varchar(50) NOT NULL,
  `restricciones` text,
  `comidas_por_dia` int NOT NULL,
  `plan_alimentacion` text,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: dietas
-- Tabla `dietas` está vacía
-- Fin de datos para tabla: dietas

-- Estructura de la tabla: dietas_usuario
CREATE TABLE `dietas_usuario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `dieta_base_id` int DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `fecha_inicio` datetime NOT NULL,
  `fecha_fin` datetime DEFAULT NULL,
  `perfil_usuario` text,
  `plan_generado` text NOT NULL,
  `progreso` int DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dieta_base_id` (`dieta_base_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `dietas_usuario_ibfk_1` FOREIGN KEY (`dieta_base_id`) REFERENCES `dietas` (`id`),
  CONSTRAINT `dietas_usuario_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: dietas_usuario
-- Tabla `dietas_usuario` está vacía
-- Fin de datos para tabla: dietas_usuario

-- Estructura de la tabla: direcciones
CREATE TABLE `direcciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `calle` varchar(200) NOT NULL,
  `numero_exterior` varchar(20) NOT NULL,
  `numero_interior` varchar(20) DEFAULT NULL,
  `colonia` varchar(100) NOT NULL,
  `ciudad` varchar(100) NOT NULL,
  `estado` varchar(50) NOT NULL,
  `codigo_postal` varchar(10) NOT NULL,
  `referencias` text,
  `tipo` varchar(20) DEFAULT NULL,
  `predeterminada` tinyint(1) DEFAULT NULL,
  `activa` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `direcciones_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: direcciones
INSERT INTO `direcciones` (`id`, `user_id`, `calle`, `numero_exterior`, `numero_interior`, `colonia`, `ciudad`, `estado`, `codigo_postal`, `referencias`, `tipo`, `predeterminada`, `activa`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 1, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-19 04:18:54', '2026-03-19 04:18:54'),
  (2, 2, 'Av de las Palmas', '117', '', 'Santa Maria Atarasquillo', 'Santa María Atarasquillo', 'Méx.', '52050', '', 'casa', 1, 1, '2026-02-16 20:39:14', '2026-02-16 20:39:14'),
  (3, 3, 'Av de las Palmas', '117', '', 'Santa Maria Atarasquillo', 'Santa María Atarasquillo', 'Méx.', '52050', '', 'casa', 1, 1, '2026-02-16 20:50:44', '2026-02-16 20:50:44'),
  (4, 4, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-02 03:42:15', '2026-03-02 03:42:15'),
  (5, 5, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-02 03:55:56', '2026-03-02 03:55:56'),
  (6, 6, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-02 04:03:56', '2026-03-02 04:03:56'),
  (7, 7, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-03 02:20:53', '2026-03-03 02:20:53'),
  (8, 8, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-03 02:36:31', '2026-03-03 02:36:31'),
  (9, 9, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-03 02:42:26', '2026-03-03 02:42:26'),
  (10, 10, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-03 04:22:03', '2026-03-03 04:22:03'),
  (11, 11, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-03 04:51:27', '2026-03-03 04:51:27'),
  (12, 12, 'LAS PALMAS', 'S/N', '', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', '', 'casa', 1, 1, '2026-03-05 20:48:07', '2026-03-05 20:48:07');
-- Fin de datos para tabla: direcciones

-- Estructura de la tabla: notificaciones
CREATE TABLE `notificaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `user_type` varchar(20) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `titulo` varchar(200) NOT NULL,
  `mensaje` text NOT NULL,
  `leida` tinyint(1) DEFAULT NULL,
  `datos_adicionales` json DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_leida` datetime DEFAULT NULL,
  `orden_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `orden_id` (`orden_id`),
  CONSTRAINT `notificaciones_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: notificaciones
INSERT INTO `notificaciones` (`id`, `user_id`, `user_type`, `tipo`, `titulo`, `mensaje`, `leida`, `datos_adicionales`, `fecha_creacion`, `fecha_leida`, `orden_id`) VALUES 
  (4, 1, 'admin', 'nuevo_pedido', 'Pedido #ZZY32R', 'NUEVO PEDIDO #ZZY32R
Cliente: Azalia Mejia
Tel: 7228963187
Pedido: Whey Protein x1
Método pago: Pago en efectivo
Total: $45.99
Notas: Pedido de Whey Protein - Cantidad: 1...', 0, '{"notas": "Pedido de Whey Protein - Cantidad: 1", "estado": "pendiente", "cantidad": 1, "orden_id": 1, "info_pago": null, "timestamp": "2026-03-19T06:40:51.580754", "metodo_pago": "efectivo", "tipo_pedido": "suplemento", "fecha_pedido": "2026-03-19T06:40:51.580725", "precio_total": 45.99, "codigo_pedido": "ZZY32R", "cliente_nombre": "Azalia Mejia", "precio_unitario": 45.99, "producto_nombre": "Whey Protein", "telefono_cliente": "7228963187", "detalles_completos": "Whey Protein x1", "direccion_completa": "Av de las Palmas #117, Santa Maria Atarasquillo, Santa María Atarasquillo, Méx., CP: 52050"}', '2026-03-19 06:40:52', NULL, 1),
  (5, 2, 'admin', 'nuevo_pedido', 'Pedido #ZZY32R', 'NUEVO PEDIDO #ZZY32R
Cliente: Azalia Mejia
Tel: 7228963187
Pedido: Whey Protein x1
Método pago: Pago en efectivo
Total: $45.99
Notas: Pedido de Whey Protein - Cantidad: 1...', 0, '{"notas": "Pedido de Whey Protein - Cantidad: 1", "estado": "pendiente", "cantidad": 1, "orden_id": 1, "info_pago": null, "timestamp": "2026-03-19T06:40:51.580754", "metodo_pago": "efectivo", "tipo_pedido": "suplemento", "fecha_pedido": "2026-03-19T06:40:51.580725", "precio_total": 45.99, "codigo_pedido": "ZZY32R", "cliente_nombre": "Azalia Mejia", "precio_unitario": 45.99, "producto_nombre": "Whey Protein", "telefono_cliente": "7228963187", "detalles_completos": "Whey Protein x1", "direccion_completa": "Av de las Palmas #117, Santa Maria Atarasquillo, Santa María Atarasquillo, Méx., CP: 52050"}', '2026-03-19 06:40:52', NULL, 1),
  (6, 3, 'cliente', 'confirmacion_pedido', 'Pedido recibido #ZZY32R', 'Tu pedido #ZZY32R ha sido recibido.
Total: $45.99
Método pago: Pago en efectivo
Te notificaremos cuando esté en proceso.', 0, '{"notas": "Pedido de Whey Protein - Cantidad: 1", "estado": "pendiente", "cantidad": 1, "orden_id": 1, "info_pago": null, "timestamp": "2026-03-19T06:40:51.580754", "metodo_pago": "efectivo", "tipo_pedido": "suplemento", "fecha_pedido": "2026-03-19T06:40:51.580725", "precio_total": 45.99, "codigo_pedido": "ZZY32R", "cliente_nombre": "Azalia Mejia", "precio_unitario": 45.99, "producto_nombre": "Whey Protein", "telefono_cliente": "7228963187", "detalles_completos": "Whey Protein x1", "direccion_completa": "Av de las Palmas #117, Santa Maria Atarasquillo, Santa María Atarasquillo, Méx., CP: 52050"}', '2026-03-19 06:40:52', NULL, 1);
-- Fin de datos para tabla: notificaciones

-- Estructura de la tabla: ordenes
CREATE TABLE `ordenes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_unico` varchar(10) NOT NULL,
  `nombre_usuario` varchar(100) NOT NULL,
  `telefono_usuario` varchar(20) NOT NULL,
  `tipo_pedido` varchar(20) NOT NULL,
  `suplemento_id` int DEFAULT NULL,
  `tarjeta_id` int DEFAULT NULL,
  `direccion_texto` text,
  `direccion_id` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `precio_total` decimal(10,2) NOT NULL,
  `metodo_pago` varchar(20) DEFAULT NULL,
  `info_pago_json` text,
  `notas` text,
  `pedido_json` text,
  `estado` varchar(20) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo_unico` (`codigo_unico`),
  KEY `direccion_id` (`direccion_id`),
  KEY `suplemento_id` (`suplemento_id`),
  KEY `tarjeta_id` (`tarjeta_id`),
  CONSTRAINT `ordenes_ibfk_1` FOREIGN KEY (`direccion_id`) REFERENCES `direcciones` (`id`),
  CONSTRAINT `ordenes_ibfk_2` FOREIGN KEY (`suplemento_id`) REFERENCES `suplementos` (`id`),
  CONSTRAINT `ordenes_ibfk_3` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjetas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: ordenes
INSERT INTO `ordenes` (`id`, `codigo_unico`, `nombre_usuario`, `telefono_usuario`, `tipo_pedido`, `suplemento_id`, `tarjeta_id`, `direccion_texto`, `direccion_id`, `cantidad`, `precio_unitario`, `precio_total`, `metodo_pago`, `info_pago_json`, `notas`, `pedido_json`, `estado`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'ZZY32R', 'Azalia Mejia', '7228963187', 'suplemento', 1, NULL, 'Av de las Palmas #117, Santa Maria Atarasquillo, Santa María Atarasquillo, Méx., CP: 52050', 3, 1, '45.99', '45.99', 'efectivo', NULL, 'Pedido de Whey Protein - Cantidad: 1', NULL, 'pendiente', '2026-03-19 06:40:52', '2026-03-19 06:40:52');
-- Fin de datos para tabla: ordenes

-- Estructura de la tabla: seguimiento_dieta
CREATE TABLE `seguimiento_dieta` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dieta_usuario_id` int NOT NULL,
  `dia_numero` int NOT NULL,
  `fecha` date NOT NULL,
  `completado` tinyint(1) DEFAULT NULL,
  `comidas_completadas` text,
  `calorias_consumidas` int DEFAULT NULL,
  `agua_consumida` float DEFAULT NULL,
  `notas` text,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dieta_usuario_id` (`dieta_usuario_id`),
  CONSTRAINT `seguimiento_dieta_ibfk_1` FOREIGN KEY (`dieta_usuario_id`) REFERENCES `dietas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: seguimiento_dieta
-- Tabla `seguimiento_dieta` está vacía
-- Fin de datos para tabla: seguimiento_dieta

-- Estructura de la tabla: suplementos
CREATE TABLE `suplementos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `categoria` varchar(50) NOT NULL,
  `presentacion` varchar(50) NOT NULL,
  `beneficios` text,
  `modo_uso` text,
  `stock` int DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: suplementos
INSERT INTO `suplementos` (`id`, `nombre`, `descripcion`, `precio`, `categoria`, `presentacion`, `beneficios`, `modo_uso`, `stock`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Whey Protein', 'Proteína de suero de leche de rápida absorción, 24g de proteína por porción', '45.99', 'proteina', 'polvo', 'Ayuda en la recuperación muscular, aumenta la síntesis de proteínas', 'Mezclar 1 scoop (30g) con 250ml de agua, consumir después del entrenamiento', 50, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (2, 'L-Carnitina Líquida', 'Aminoácido que ayuda en el transporte de grasas para su oxidación', '29.99', 'quemadores de grasa', 'liquidos', 'Acelera la quema de grasas, mejora el rendimiento, reduce la fatiga', 'Tomar 15ml 30 minutos antes del cardio o entrenamiento', 40, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (3, 'Multivitamínico Completo', 'Fórmula con todas las vitaminas y minerales esenciales', '24.99', 'vitaminas y minerales', 'tableta', 'Fortalece el sistema inmune, mejora la energía, cubre deficiencias nutricionales', 'Tomar 1 tableta con el desayuno', 80, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (4, 'Cafeína 200mg', 'Estimulante natural que aumenta el rendimiento y la concentración', '12.90', 'termogenicos', 'capsulas', 'Aumenta energía, mejora enfoque, acelera metabolismo', 'Tomar 1 cápsula 30 minutos antes del entrenamiento', 100, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (5, 'Garcinia Cambogia', 'Suplemento natural que ayuda a controlar el apetito', '26.90', 'control de apetito', 'capsulas', 'Reduce ansiedad por comer, mejora estado de ánimo', 'Tomar 2 cápsulas 30 minutos antes de cada comida', 35, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (6, 'Pre-Entreno Explosivo', 'Fórmula completa para maximizar rendimiento deportivo', '49.99', 'energeticos naturales', 'polvo', 'Aumenta fuerza, mejora resistencia, retrasa fatiga muscular', 'Mezclar 1 scoop con 300ml de agua 30 minutos antes de entrenar', 30, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (7, 'Psyllium Husk', 'Fibra natural que mejora el tránsito intestinal y la digestión', '23.90', 'fibras y digestivos', 'polvo', 'Mejora digestión, regula intestino, controla colesterol', 'Mezclar 1 cucharada con agua o jugo 2 veces al día', 45, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (8, 'Cardo Mariano', 'Hierba que protege y desintoxica el hígado', '19.90', 'detox y limpieza', 'capsulas', 'Protege hígado, efecto antioxidante, mejora digestión', 'Tomar 2 cápsulas al día con las comidas', 30, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34'),
  (9, 'Gomitas Multivitamínicas', 'Deliciosas gomitas con vitaminas esenciales para adultos', '19.90', 'vitaminas y minerales', 'gomitas', 'Fáciles de tomar, sabor agradable, aporte vitamínico completo', 'Masticar 2 gomitas al día', 80, 1, '2026-03-19 00:38:34', '2026-03-19 00:38:34');
-- Fin de datos para tabla: suplementos

-- Estructura de la tabla: tarjetas
CREATE TABLE `tarjetas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `nombre_titular` varchar(100) NOT NULL,
  `numero_tarjeta` varchar(255) NOT NULL,
  `numero_enmascarado` varchar(20) NOT NULL,
  `mes_expiracion` varchar(2) NOT NULL,
  `anio_expiracion` varchar(4) NOT NULL,
  `tipo_tarjeta` varchar(20) NOT NULL,
  `predeterminada` tinyint(1) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `tarjetas_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: tarjetas
INSERT INTO `tarjetas` (`id`, `user_id`, `nombre_titular`, `numero_tarjeta`, `numero_enmascarado`, `mes_expiracion`, `anio_expiracion`, `tipo_tarjeta`, `predeterminada`, `fecha_registro`) VALUES 
  (1, 9, 'Vanessa', '$2b$12$A90vQtv/e0VAUF3D8Aqby.UcbCW0lsDB.SkizWvJiP1TJJgSSMsL6', '**** **** **** 1698', '11', '2030', 'otra', 1, '2026-03-03 02:42:26'),
  (2, 10, 'brenda', '$2b$12$IC2fN9hNP99ANm4rmT8SQOsbDeh3rajMX4an7Ap4wWSpF6whHZ57e', '**** **** **** 9615', '06', '2030', 'otra', 1, '2026-03-03 04:22:03'),
  (3, 11, 'Lucifer', '$2b$12$JPSt80lPnT7twX4x9Y9QZukUXUmhN0eMR5xyeIAIHrtLtT1fDx06G', '**** **** **** 0167', '11', '2029', 'otra', 1, '2026-03-03 04:51:28');
-- Fin de datos para tabla: tarjetas

-- Estructura de la tabla: users
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `contraseña` varchar(255) NOT NULL,
  `rol` int DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `sexo` varchar(10) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT NULL,
  `tipo_cuenta` varchar(20) DEFAULT NULL,
  `edad` int DEFAULT NULL,
  `tutor_nombre` varchar(100) DEFAULT NULL,
  `tutor_telefono` varchar(20) DEFAULT NULL,
  `restricciones_infantiles` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: users
INSERT INTO `users` (`id`, `nombre`, `correo`, `contraseña`, `rol`, `telefono`, `sexo`, `fecha_registro`, `tipo_cuenta`, `edad`, `tutor_nombre`, `tutor_telefono`, `restricciones_infantiles`) VALUES 
  (1, 'Carlos Villavicencio Gonzalez', 'carlos.villavicenciog180@gmail.com', '$2b$12$OPkyttufDxs3T3gn2EQ8LObR4KpvfGj2Z6JYFX3RWkxOy9zndhfOq', 1, '5538986602', 'M', '2026-03-19 04:18:53', 'personal', NULL, NULL, NULL, NULL),
  (2, 'Amanda Carolina Jimenez Ocampo', 'amanda@gmail.com', '$2b$12$w8pNaNXpqUF5lf6SjPhmweSLWwAMxc3lU6wwPee8c9LvY2iJQ7wpq', 1, '7228984632', 'Femenino', '2026-02-16 20:39:14', NULL, NULL, NULL, NULL, NULL),
  (3, 'Azalia Mejia', 'azalia@gmail.com', '$2b$12$xixjx307EKTlv8m65vDePe/qTAXYn85OkpRzo1wRdHMn1lBRtaPVC', 2, '7228963187', 'Femenino', '2026-02-16 20:50:44', NULL, NULL, NULL, NULL, NULL),
  (4, 'manuel', 'manuel@gmail.com', '$2b$12$MU/.6xTylareiw/9cmxUpOOMv85sTowUl8/HA3.E3QvVCQrXW.qLu', 2, '5538986602', 'M', '2026-03-02 03:42:15', NULL, NULL, NULL, NULL, NULL),
  (5, 'Omar', 'omar@gmail.com', '$2b$12$2BL3EUwWZCv0bNFQ.BccwORWa5bORRmn0/kzfe.obTsTPpGpfrvs2', 2, '7229658435', 'M', '2026-03-02 03:55:56', NULL, NULL, NULL, NULL, NULL),
  (6, 'sebas', 'sebas@gmail.com', '$2b$12$QRxIRxSoXVhNhzT/I0A/s.OAl1Zsh/mM/iZ.0CX6ny3LgJ7q0IdbK', 2, '7229658741', 'M', '2026-03-02 04:03:55', NULL, NULL, NULL, NULL, NULL),
  (7, 'Oscar', 'oscar@gmail.com', '$2b$12$50UtF3XfsDuXTLt5TLFFpeIR4eFlbtQj7PnGMr4LOsFSENvcC6/f.', 2, '5555986347', 'M', '2026-03-03 02:20:53', NULL, NULL, NULL, NULL, NULL),
  (8, 'Luis', 'luis@gmail.com', '$2b$12$1P/9A.nETWER5Qp2KmQt5O4ImCE7Qg2bPqoEa735bmMq5AAs7qTdS', 2, '7223648195', 'M', '2026-03-03 02:36:31', NULL, NULL, NULL, NULL, NULL),
  (9, 'Vanessa', 'vanessa@gmail.com', '$2b$12$u86m53/MTnH0utgHkBBIWuW2bIZ8pqr58MZDQ5gReabA7cMWi52E2', 2, '7228964517', 'M', '2026-03-03 02:42:25', NULL, NULL, NULL, NULL, NULL),
  (10, 'Brenda', 'brenda@gmail.com', '$2b$12$.cMs/gGAhZ4B6WmYnX7QqumrSkd6sPkbGvDCO5MyA00aedOC5vOVW', 2, '7229654831', 'F', '2026-03-03 04:22:02', NULL, NULL, NULL, NULL, NULL),
  (11, 'Lucifer', 'lucifer@gmail.com', '$2b$12$CCcIWXKvYAJdMqqD2uePc.V8dqKl6mRoghuYBHfjp5T70HNWJVZ0q', 2, '7229654873', 'M', '2026-03-03 04:51:26', NULL, NULL, NULL, NULL, NULL),
  (12, 'Sandra', 'san@gmail.com', '$2b$12$cTVv.HAIn6Ydnp2/gdekWOq34mop6ZlKGpDbp2SfMgDwLIIVS8W4O', 2, '7229632597', 'Femenino', '2026-03-05 20:48:06', NULL, NULL, NULL, NULL, NULL);
-- Fin de datos para tabla: users

SET FOREIGN_KEY_CHECKS=1;
