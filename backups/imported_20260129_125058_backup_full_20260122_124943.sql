-- Backup generado el 2026-01-22 12:49:43
-- Tipo: FULL
-- Tablas: 6
SET FOREIGN_KEY_CHECKS=0;

-- Estructura de la tabla: alembic_version
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: alembic_version
INSERT INTO `alembic_version` (`version_num`) VALUES 
  ('4262dfba730c');

================================================================================

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: backups
-- Tabla `backups` está vacía

================================================================================

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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: especiales
INSERT INTO `especiales` (`id`, `nombre`, `ingredientes`, `precio`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Picocito', 'Chile en Polvo, Sal, Limon, Chamoy, Gomita Picante', '50.00', 1, '2026-01-21 20:29:35', '2026-01-21 20:29:35');

================================================================================

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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: notificaciones
INSERT INTO `notificaciones` (`id`, `user_id`, `user_type`, `tipo`, `titulo`, `mensaje`, `leida`, `datos_adicionales`, `fecha_creacion`, `fecha_leida`, `orden_id`) VALUES 
  (6, 1, 'admin', 'nuevo_pedido', 'Nuevo Pedido Recibido', 'Nuevo pedido especial: Picocito - $50.00', 1, '{"precio": 50.0, "orden_id": 6, "tipo_pedido": "especial", "fecha_pedido": "2026-01-22T18:25:44", "codigo_pedido": "BEMLNQ", "cliente_nombre": "Amanda Carolina Jimenez Ocampo", "cliente_telefono": "7225987635"}', '2026-01-22 18:25:44', '2026-01-22 18:26:00', 6);

================================================================================

-- Estructura de la tabla: ordenes
CREATE TABLE `ordenes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_unico` varchar(10) NOT NULL,
  `nombre_usuario` varchar(100) NOT NULL,
  `telefono_usuario` varchar(20) NOT NULL,
  `tipo_pedido` varchar(20) NOT NULL,
  `especial_id` int DEFAULT NULL,
  `ingredientes_personalizados` text,
  `precio` decimal(10,2) NOT NULL,
  `estado` varchar(20) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo_unico` (`codigo_unico`),
  KEY `especial_id` (`especial_id`),
  CONSTRAINT `ordenes_ibfk_1` FOREIGN KEY (`especial_id`) REFERENCES `especiales` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: ordenes
INSERT INTO `ordenes` (`id`, `codigo_unico`, `nombre_usuario`, `telefono_usuario`, `tipo_pedido`, `especial_id`, `ingredientes_personalizados`, `precio`, `estado`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'GVT3MU', 'Amanda Carolina Jimenez Ocampo', '7225987635', 'personalizado', NULL, 'Limon, Sal', '30.00', 'listo', '2026-01-19 21:12:05', '2026-01-19 22:34:49'),
  (2, 'PI7IJG', 'Amanda Carolina Jimenez Ocampo', '7225987635', 'especial', 1, NULL, '50.00', 'pendiente', '2026-01-21 20:35:34', '2026-01-21 20:35:34'),
  (3, 'CSXWY0', 'Amanda Carolina Jimenez Ocampo', '7225987635', 'personalizado', NULL, 'Limon, Sal', '30.00', 'pendiente', '2026-01-21 21:11:20', '2026-01-21 21:11:20'),
  (4, 'MA4RF9', 'Amanda Carolina Jimenez Ocampo', '7225987635', 'especial', 1, NULL, '50.00', 'pendiente', '2026-01-21 21:19:44', '2026-01-21 21:19:44'),
  (5, 'PJT4HT', 'Amanda Carolina Jimenez Ocampo', '7225987635', 'especial', 1, NULL, '50.00', 'pendiente', '2026-01-21 22:54:17', '2026-01-21 22:54:17'),
  (6, 'BEMLNQ', 'Amanda Carolina Jimenez Ocampo', '7225987635', 'especial', 1, NULL, '50.00', 'pendiente', '2026-01-22 18:25:44', '2026-01-22 18:25:44');

================================================================================

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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: users
INSERT INTO `users` (`id`, `nombre`, `correo`, `contraseña`, `rol`, `telefono`, `sexo`, `fecha_registro`) VALUES 
  (1, 'Juan Carlos', 'carlos@gmail.com', '$2b$12$F/c9mwSdoaG8q45/cr315.tBZsYDpOAEdx4GTrylenLZn4WMJZthe', 1, '7294030702', 'M', '2026-01-19 20:08:04'),
  (2, 'Amanda Carolina Jimenez Ocampo', 'amanda@gmail.com', '$2b$12$38IuXZfb23ySMVHK6RYRv.9UMN4ZcL.7V.O.WQvIL./gYQr0MWyQK', 2, '7225987635', 'Femenino', '2026-01-19 21:04:15');

================================================================================

SET FOREIGN_KEY_CHECKS=1;
-- Backup completado el 2026-01-22 12:49:43
