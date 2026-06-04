# init_db.py
import mysql.connector

# Configuración inicial de conexión (Conectamos primero al servidor nativo)
CONFIG_SERVIDOR = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Coloca tu contraseña de MariaDB si usas una
    'port': 3306
}

def inicializar_base_de_datos():
    try:
        # 1. Conectar al servidor de MariaDB
        print("Conectando al servidor local de MariaDB...")
        conexion = mysql.connector.connect(**CONFIG_SERVIDOR)
        cursor = conexion.cursor()

        # 2. Crear la base de datos con codificación UTF-8
        print("Creando la base de datos 'asistencia_rostros'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS asistencia_rostros CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute("USE asistencia_rostros;")

        # 3. Diccionario con todas las tablas basadas en el modelo de SENATI
        tablas = {}
        
        tablas['asis_clients'] = """
            CREATE TABLE IF NOT EXISTS asis_clients (
                id INT(11) AUTO_INCREMENT PRIMARY KEY,
                company_name VARCHAR(100) NOT NULL,
                api_key VARCHAR(100) NOT NULL,
                is_active TINYINT(1) DEFAULT 1,
                max_requests_per_month INT(11) DEFAULT 10000,
                total_requests_made INT(11) DEFAULT 0,
                allowed_lat DECIMAL(10,7) NOT NULL,
                allowed_lon DECIMAL(10,7) NOT NULL,
                allowed_radius_meters INT(11) DEFAULT 50,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """

        tablas['asis_users'] = """
            CREATE TABLE IF NOT EXISTS asis_users (
                id INT(11) AUTO_INCREMENT PRIMARY KEY,
                cla INT(11) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                dni VARCHAR(20) NOT NULL UNIQUE,
                base_salary DECIMAL(10,2) NOT NULL,
                is_active TINYINT(1) DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """

        tablas['asis_face_vectors'] = """
            CREATE TABLE IF NOT EXISTS asis_face_vectors (
                id INT(11) AUTO_INCREMENT PRIMARY KEY,
                cla INT(11) NOT NULL,
                user_id INT(11) NOT NULL,
                vector TEXT NOT NULL,
                position_label VARCHAR(20) DEFAULT 'frontal',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES asis_users(id) ON DELETE CASCADE
            );
        """

        tablas['asis_attendance_sessions'] = """
            CREATE TABLE IF NOT EXISTS asis_attendance_sessions (
                id INT(11) AUTO_INCREMENT PRIMARY KEY,
                cla INT(11) NOT NULL,
                user_id INT(11) NOT NULL,
                check_in DATETIME NOT NULL,
                check_out DATETIME DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES asis_users(id) ON DELETE CASCADE
            );
        """

        tablas['asis_attendance_logs'] = """
            CREATE TABLE IF NOT EXISTS asis_attendance_logs (
                id INT(11) AUTO_INCREMENT PRIMARY KEY,
                cla INT(11) NOT NULL,
                user_id INT(11) NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                method VARCHAR(20) DEFAULT 'face_recognition',
                action VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL,
                photo TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES asis_users(id) ON DELETE CASCADE
            );
        """

        # 4. Ejecutar la creación de cada tabla de forma secuencial
        for nombre, ddl in tablas.items():
            print(f"Creando tabla {nombre}...")
            cursor.execute(ddl)

        # 5. Insertar datos de prueba iniciales de forma segura para que puedas testear
        print("Insertando registros de prueba iniciales...")
        
        # Insertar cliente/empresa (Coordenadas de Lima por defecto)
        cursor.execute("""
            INSERT IGNORE INTO asis_clients (id, company_name, api_key, allowed_lat, allowed_lon, allowed_radius_meters)
            VALUES (1, 'SENATI - ETI S.A.', 'llave_secreta_senati', -12.046374, -77.042793, 500);
        """)

        # Insertar tu usuario trabajador de prueba (DNI ficticio: 12345678, cámbialo si deseas)
        cursor.execute("""
            INSERT IGNORE INTO asis_users (id, cla, username, password_hash, full_name, dni, base_salary, is_active)
            VALUES (1, 101, 'hmamanchura', 'scrypt_hash_xyz', 'Hugo Mamanchura Lima', '12345678', 3500.00, 1);
        """)

        # Insertar un vector facial ficticio para este usuario
        cursor.execute("""
            INSERT IGNORE INTO asis_face_vectors (id, cla, user_id, vector, position_label)
            VALUES (1, 101, 1, '[0.015, -0.084, 0.122, 0.054]', 'frontal');
        """)

        # Confirmar los cambios en MariaDB
        conexion.commit()
        print("\n¡Enhorabuena! La base de datos y todas las tablas fueron creadas exitosamente.")
        
    except mysql.connector.Error as error:
        print(f"Error durante la inicialización de la base de datos: {error}")
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()
            print("Conexión con MariaDB cerrada de forma segura.")

if __name__ == '__main__':
    inicializar_base_de_datos()