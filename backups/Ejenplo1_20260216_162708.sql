-- Backup generado el 2026-02-16 16:27:08
-- Tipo: FULL
SET FOREIGN_KEY_CHECKS=0;

-- Estructura de la tabla: alembic_version
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: alembic_version
INSERT INTO `alembic_version` (`version_num`) VALUES 
  ('9ba9ad5706f7');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: backups
INSERT INTO `backups` (`id`, `filename`, `filepath`, `size_mb`, `tables_included`, `backup_type`, `status`, `created_at`) VALUES 
  (1, 'prueba_20260216_150044.sql.gz', 'C:\Proyects\Proyect-CrazyLettuces\Api-CrazyLettuces\backups\prueba_20260216_150044.sql.gz', 0.0, '["alembic_version", "backups", "direcciones", "especiales", "ingredientes", "notificaciones", "ordenes", "users"]', 'full', 'completed', '2026-02-16 21:00:44');
-- Fin de datos para tabla: backups

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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: direcciones
INSERT INTO `direcciones` (`id`, `user_id`, `calle`, `numero_exterior`, `numero_interior`, `colonia`, `ciudad`, `estado`, `codigo_postal`, `referencias`, `tipo`, `predeterminada`, `activa`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 1, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', 'Entre calle ricardo flores magon y Antigua calle ', 'casa', 1, 1, '2026-02-16 20:36:24', '2026-02-16 20:36:24'),
  (2, 2, 'Av de las Palmas', '117', '', 'Santa Maria Atarasquillo', 'Santa María Atarasquillo', 'Méx.', '52050', '', 'casa', 1, 1, '2026-02-16 20:39:14', '2026-02-16 20:39:14'),
  (3, 3, 'Av de las Palmas', '117', '', 'Santa Maria Atarasquillo', 'Santa María Atarasquillo', 'Méx.', '52050', '', 'casa', 1, 1, '2026-02-16 20:50:44', '2026-02-16 20:50:44');
-- Fin de datos para tabla: direcciones

-- Estructura de la tabla: especiales
CREATE TABLE `especiales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `ingredientes` text NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: especiales
INSERT INTO `especiales` (`id`, `nombre`, `ingredientes`, `precio`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Mediterráneo Cremoso', 'Pollo, Queso Mozzarella, Tomate, Crema, Aceite de olivo, Limon, Sal', '70.00', 1, '2026-02-16 20:57:51', '2026-02-16 20:57:51'),
  (2, 'Cítrico Delight', 'Pollo, Limon, Aceite de olivo, Sal', '30.00', 1, '2026-02-16 20:59:18', '2026-02-16 20:59:18'),
  (3, 'Tomate Aromático', 'Tomate, Aceite de olivo, Sal, Limon', '35.00', 1, '2026-02-16 21:00:06', '2026-02-16 21:00:06');
-- Fin de datos para tabla: especiales

-- Estructura de la tabla: ingredientes
CREATE TABLE `ingredientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: ingredientes
INSERT INTO `ingredientes` (`id`, `nombre`, `categoria`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Tomate', 'vegetales', 1, '2026-02-16 20:45:10', '2026-02-16 20:45:10'),
  (2, 'Pollo', 'proteinas', 1, '2026-02-16 20:45:10', '2026-02-16 20:48:36'),
  (3, 'Crema', 'lacteos', 1, '2026-02-16 20:49:31', '2026-02-16 20:49:31'),
  (4, 'Sal', 'condimentos', 1, '2026-02-16 20:52:14', '2026-02-16 20:52:14'),
  (5, 'Queso Mozzarella', 'lacteos', 1, '2026-02-16 20:52:47', '2026-02-16 20:53:40'),
  (6, 'Limon', 'vegetales', 1, '2026-02-16 20:52:57', '2026-02-16 20:52:57'),
  (7, 'Aceite de olivo', 'condimentos', 1, '2026-02-16 20:54:19', '2026-02-16 20:54:19');
-- Fin de datos para tabla: ingredientes

-- Estructura de la tabla: notificaciones
CREATE TABLE `notificaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: notificaciones
-- Tabla `notificaciones` está vacía
-- Fin de datos para tabla: notificaciones

-- Estructura de la tabla: ordenes
CREATE TABLE `ordenes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_unico` varchar(10) NOT NULL,
  `nombre_usuario` varchar(100) NOT NULL,
  `telefono_usuario` varchar(20) NOT NULL,
  `tipo_pedido` varchar(20) NOT NULL,
  `especial_id` int DEFAULT NULL,
  `direccion_texto` text,
  `direccion_id` int DEFAULT NULL,
  `ingredientes_personalizados` text,
  `precio` decimal(10,2) NOT NULL,
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
  KEY `especial_id` (`especial_id`),
  CONSTRAINT `ordenes_ibfk_1` FOREIGN KEY (`direccion_id`) REFERENCES `direcciones` (`id`),
  CONSTRAINT `ordenes_ibfk_2` FOREIGN KEY (`especial_id`) REFERENCES `especiales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: ordenes
-- Tabla `ordenes` está vacía
-- Fin de datos para tabla: ordenes

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
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: users
INSERT INTO `users` (`id`, `nombre`, `correo`, `contraseña`, `rol`, `telefono`, `sexo`, `fecha_registro`) VALUES 
  (1, 'Juan Carlos Villavicencio Gonzalez', 'carlos.villavicenciog180@gmail.com', '$2b$12$KZB7xy/os7MK7Y3SUaosW.vmODxqeGHc2kO2RixhQse993nDJUlrG', 1, '7294030702', 'Masculino', '2026-02-16 20:36:24'),
  (2, 'Amanda Carolina Jimenez Ocampo', 'amanda@gmail.com', '$2b$12$w8pNaNXpqUF5lf6SjPhmweSLWwAMxc3lU6wwPee8c9LvY2iJQ7wpq', 1, '7228984632', 'Femenino', '2026-02-16 20:39:14'),
  (3, 'Azalia Mejia', 'azalia@gmail.com', '$2b$12$xixjx307EKTlv8m65vDePe/qTAXYn85OkpRzo1wRdHMn1lBRtaPVC', 2, '7228963187', 'Femenino', '2026-02-16 20:50:44');
-- Fin de datos para tabla: users

SET FOREIGN_KEY_CHECKS=1;
