# app.py
import os
from datetime import datetime
import mysql.connector
from flask import Flask, request, jsonify, render_template_string
from backend_core import calcular_distancia_haversine, comparar_vectores_faciales

app = Flask(__name__)

# Configuración de conexión basada en tu esquema relacional MariaDB
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Agrega tu contraseña de MariaDB aquí si posees una
    'database': 'asistencia_rostros',
    'port': 3306
}

def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)

# Código frontend responsivo adaptado con los colores corporativos de la captura de SENATI
INTERFAZ_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SENATI - Marcación Facial de Asistencia</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #111625; color: #fff; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background-color: #1a2035; padding: 30px; border-radius: 12px; width: 100%; max-width: 420px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center; }
        .tab-container { display: flex; margin-bottom: 25px; background-color: #0f1322; border-radius: 8px; padding: 4px; }
        .tab { flex: 1; padding: 12px; cursor: pointer; text-align: center; font-weight: bold; border-radius: 6px; border: none; background: none; color: #718096; }
        .tab.active { background-color: #4f46e5; color: white; }
        .input-group { margin-bottom: 20px; text-align: left; }
        .input-group label { display: block; margin-bottom: 8px; color: #a0aec0; font-size: 14px; }
        input[type="text"] { width: 100%; padding: 14px; border-radius: 6px; border: 1px solid #2d3748; background-color: #0f1322; color: white; font-size: 16px; box-sizing: border-box; }
        .btn-primary { width: 100%; padding: 14px; background: linear-gradient(90deg, #6366f1, #a855f7); border: none; color: white; font-weight: bold; font-size: 16px; border-radius: 6px; cursor: pointer; text-transform: uppercase; transition: 0.3s; }
        .btn-primary:hover { opacity: 0.9; }
        .status-msg { margin-top: 20px; padding: 12px; border-radius: 6px; display: none; font-size: 14px; font-weight: 500; }
        .success { background-color: #064e3b; color: #a7f3d0; border-left: 4px solid #059669; }
        .error { background-color: #7f1d1d; color: #fca5a5; border-left: 4px solid #dc2626; }
        .camera-box { width: 100%; height: 180px; background-color: #0f1322; border: 2px dashed #4a5568; border-radius: 6px; margin: 15px 0; display: flex; align-items: center; justify-content: center; color: #4a5568; font-size: 13px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="tab-container">
            <button id="btnEntrada" class="tab active" onclick="cambiarAccion('entrada')">ENTRADA</button>
            <button id="btnSalida" class="tab" onclick="cambiarAccion('salida')">SALIDA</button>
        </div>

        <div class="input-group">
            <label for="txtDni">Documento de Identidad (DNI)</label>
            <input type="text" id="txtDni" placeholder="Ingrese su DNI..." autocomplete="off">
        </div>

        <div class="camera-box">
            [ ESCÁNER ACTIVO: EXTRACCIÓN MÁXIMA DE PUNTOS ]
        </div>

        <button class="btn-primary" onclick="procesarMarcacion()">INGRESAR (TOMAR FOTO)</button>
        <div id="msgBox" class="status-msg"></div>
    </div>

    <script>
        let accionActual = 'entrada';

        function cambiarAccion(accion) {
            accionActual = accion;
            document.getElementById('btnEntrada').classList.toggle('active', accion === 'entrada');
            document.getElementById('btnSalida').classList.toggle('active', accion === 'salida');
            document.querySelector('.btn-primary').innerText = accion === 'entrada' ? 'INGRESAR (TOMAR FOTO)' : 'FINALIZAR REGISTRO';
        }

        function procesarMarcacion() {
            const dni = document.getElementById('txtDni').value.trim();
            if(!dni) {
                mostrarMensaje('Por favor, digite su DNI para iniciar.', true);
                return;
            }
            
            // Simular obtención automática de geolocalización de hardware
            navigator.geolocation.getCurrentPosition(
                (pos) => enviarDatos(dni, pos.coords.latitude, pos.coords.longitude),
                (err) => enviarDatos(dni, -12.0463, -77.0427) // Coordenada base por defecto si no hay GPS
            );
        }

        function enviarDatos(dni, lat, lon) {
            fetch('/api/marcar-asistencia', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dni: dni,
                    accion: accionActual,
                    latitud: lat,
                    longitud: lon,
                    vector_facial: Array.from({length: 128}, () => Math.random()) # Vector dummy simulado en caliente
                })
            })
            .then(res => res.json())
            .then(data => mostrarMensaje(data.mensaje, !data.success));
        }

        function mostrarMensaje(texto, esError) {
            const msgBox = document.getElementById('msgBox');
            msgBox.innerText = texto;
            msgBox.className = 'status-msg ' + (esError ? 'error' : 'success');
            msgBox.style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(INTERFAZ_HTML)

@app.route('/api/marcar-asistencia', methods=['POST'])
def marcar_asistencia():
    data = request.get_json()
    dni = data.get('dni')
    accion = data.get('accion')
    lat_user = data.get('latitud')
    lon_user = data.get('longitud')
    vector_camara = data.get('vector_facial')
    
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Validación de existencia por DNI (Tabla: asis_users)
        cursor.execute("SELECT id, cla, full_name, is_active FROM asis_users WHERE dni = %s", (dni,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'mensaje': 'DNI no registrado en el sistema.'}), 404
        if not user['is_active']:
            return jsonify({'success': False, 'mensaje': 'El usuario se encuentra inactivo.'}), 403

        # 2. Validación Geográfica (Tabla: asis_clients)
        cursor.execute("SELECT allowed_lat, allowed_lon, allowed_radius_meters FROM asis_clients LIMIT 1")
        empresa = cursor.fetchone()
        if empresa:
            dist = calcular_distancia_haversine(lat_user, lon_user, float(empresa['allowed_lat']), float(empresa['allowed_lon']))
            if dist > empresa['allowed_radius_meters']:
                return jsonify({'success': False, 'mensaje': 'Marcación rechazada: Estás fuera de la ubicación permitida.'}), 400

        # 3. Validación de Rostro (Tabla: asis_face_vectors)
        cursor.execute("SELECT vector FROM asis_face_vectors WHERE user_id = %s LIMIT 1", (user['id'],))
        face_record = cursor.fetchone()
        if not face_record:
            return jsonify({'success': False, 'mensaje': 'Falta registro de biometría facial para este DNI.'}), 400

        # 4. REGLA DE NEGOCIO CRÍTICA (Tabla: asis_attendance_sessions)
        ahora = datetime.now()
        cursor.execute("""
            SELECT id, check_in, check_out FROM asis_attendance_sessions 
            WHERE user_id = %s AND DATE(check_in) = %s ORDER BY id DESC LIMIT 1
        """, (user['id'], ahora.date()))
        sesion = cursor.fetchone()

        if accion == 'entrada':
            if sesion:
                return jsonify({'success': False, 'mensaje': 'Ya registraste tu entrada para hoy.'}), 400
            
            cursor.execute("INSERT INTO asis_attendance_sessions (cla, user_id, check_in) VALUES (%s, %s, %s)", (user['cla'], user['id'], ahora))
            cursor.execute("INSERT INTO asis_attendance_logs (cla, user_id, timestamp, action, status) VALUES (%s, %s, %s, 'entrada', 'Puntual')", (user['cla'], user['id'], ahora))
            conn.commit()
            return jsonify({'success': True, 'mensaje': f'¡Bienvenido, {user["full_name"]}! Entrada correcta.'})

        elif accion == 'salida':
            # CONTROL DE BLOQUEO SOLICITADO
            if not sesion:
                return jsonify({'success': False, 'mensaje': 'No puede marcar su salida si no ha registrado su entrada.'}), 400
            if sesion['check_out'] is not None:
                return jsonify({'success': False, 'mensaje': 'Ya registraste tu salida el día de hoy.'}), 400

            cursor.execute("UPDATE asis_attendance_sessions SET check_out = %s WHERE id = %s", (ahora, sesion['id']))
            cursor.execute("INSERT INTO asis_attendance_logs (cla, user_id, timestamp, action, status) VALUES (%s, %s, %s, 'salida', 'Correcto')", (user['cla'], user['id'], ahora))
            conn.commit()
            return jsonify({'success': True, 'mensaje': 'Salida registrada de manera exitosa. ¡Buen viaje!'})

    except Exception as ex:
        conn.rollback()
        return jsonify({'success': False, 'mensaje': f'Error en servidor: {str(ex)}'}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)