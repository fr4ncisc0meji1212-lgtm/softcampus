import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS software (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            carrera TEXT NOT NULL,
            so TEXT NOT NULL,
            licencia TEXT NOT NULL,
            version TEXT NOT NULL,
            url TEXT NOT NULL,
            winget TEXT UNIQUE,
            "desc" TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS solicitudes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            carrera TEXT NOT NULL,
            comentario TEXT NOT NULL,
            solicitadoPor TEXT NOT NULL,
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    ''')
    cur.execute('ALTER TABLE solicitudes ADD COLUMN IF NOT EXISTS nie TEXT')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS kits (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            carrera TEXT NOT NULL,
            programas TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id SERIAL PRIMARY KEY,
            nie TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL
        )
    ''')
    cur.execute('ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS password TEXT')

    cur.execute('''
        INSERT INTO software (nombre, categoria, carrera, so, licencia, version, url, winget, "desc")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (winget) DO NOTHING
    ''', (
        "Visual Studio Code", "Programación", "Informática",
        "Windows, Linux, Mac", "Gratuito", "1.108",
        "https://code.visualstudio.com", "Microsoft.VisualStudioCode",
        "Editor de código fuente ligero."
    ))

    conn.commit()
    cur.close()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html')


# ---------- SOFTWARE ----------

@app.route('/api/software', methods=['GET'])
def obtener_software():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM software')
    software = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in software])


@app.route('/api/software', methods=['POST'])
def agregar_software():
    nuevo = request.json
    winget_id = nuevo.get('winget', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if winget_id:
        cur.execute('SELECT id FROM software WHERE winget = %s', (winget_id,))
        existente = cur.fetchone()
        if existente:
            cur.close()
            conn.close()
            return jsonify({'error': 'El ID de WinGet ya está registrado en otro programa.'}), 400

    try:
        cur.execute('''
            INSERT INTO software (nombre, categoria, carrera, so, licencia, version, url, winget, "desc")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            nuevo['nombre'].strip(), nuevo['categoria'], nuevo['carrera'],
            nuevo['so'].strip(), nuevo['licencia'], nuevo['version'].strip(),
            nuevo['url'].strip(), winget_id if winget_id else None, nuevo['desc'].strip()
        ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/software/<int:id>', methods=['PUT'])
def actualizar_software(id):
    editado = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE software
        SET nombre=%s, categoria=%s, carrera=%s, so=%s, licencia=%s,
            version=%s, url=%s, winget=%s, "desc"=%s
        WHERE id = %s
    ''', (
        editado['nombre'].strip(), editado['categoria'], editado['carrera'],
        editado['so'].strip(), editado['licencia'], editado['version'].strip(),
        editado['url'].strip(), editado['winget'].strip() if editado.get('winget') else None,
        editado['desc'].strip(), id
    ))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'actualizado'})


@app.route('/api/software/<int:id>', methods=['DELETE'])
def eliminar_software(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM software WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'eliminado'})


# ---------- SOLICITUDES ----------

@app.route('/api/solicitudes', methods=['GET'])
def obtener_solicitudes():
    nie = request.args.get('nie')
    conn = get_db_connection()
    cur = conn.cursor()
    if nie:
        cur.execute('SELECT * FROM solicitudes WHERE nie = %s ORDER BY id DESC', (nie,))
    else:
        cur.execute('SELECT * FROM solicitudes ORDER BY id DESC')
    solicitudes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in solicitudes])


@app.route('/api/solicitudes', methods=['POST'])
def agregar_solicitud():
    nueva = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO solicitudes (nombre, carrera, comentario, solicitadoPor, fecha, estado, nie)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (
        nueva['nombre'].strip(), nueva['carrera'], nueva['comentario'].strip(),
        nueva['solicitadoPor'], nueva['fecha'], nueva['estado'], nueva.get('nie')
    ))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'}), 201


@app.route('/api/solicitudes/<int:id>', methods=['PUT'])
def actualizar_solicitud(id):
    datos = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    if 'estado' in datos:
        cur.execute('UPDATE solicitudes SET estado = %s WHERE id = %s', (datos['estado'], id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'actualizado'})


@app.route('/api/solicitudes/<int:id>', methods=['DELETE'])
def eliminar_solicitud(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM solicitudes WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'eliminado'})


# ---------- KITS ----------

@app.route('/api/kits', methods=['GET'])
def obtener_kits():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM kits')
    kits = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in kits])


@app.route('/api/kits', methods=['POST'])
def crear_kit():
    nuevo = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO kits (nombre, carrera, programas)
        VALUES (%s, %s, %s)
    ''', (
        nuevo['nombre'].strip(),
        nuevo['carrera'],
        str(nuevo['programas'])
    ))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'ok'}), 201


@app.route('/api/kits/<int:id>', methods=['DELETE'])
def eliminar_kit(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM kits WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'eliminado'})


# ---------- ESTUDIANTES (cuentas y login) ----------

@app.route('/api/estudiantes', methods=['GET'])
def obtener_estudiantes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nie, nombre FROM estudiantes ORDER BY id DESC')
    estudiantes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in estudiantes])


@app.route('/api/estudiantes', methods=['POST'])
def crear_estudiante():
    datos = request.json
    nie = str(datos.get('nie', '')).strip()
    nombre = str(datos.get('nombre', '')).strip()
    password = str(datos.get('password', '')).strip()

    if not nie.isdigit() or len(nie) < 8:
        return jsonify({'error': 'El NIE debe tener 8 dígitos o más, solo números.'}), 400
    if not nombre:
        return jsonify({'error': 'El nombre es obligatorio.'}), 400
    if not password or len(password) < 4:
        return jsonify({'error': 'La contraseña debe tener al menos 4 caracteres.'}), 400

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO estudiantes (nie, nombre, password) VALUES (%s, %s, %s)', (nie, nombre, password_hash))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        if 'unique' in str(e).lower():
            return jsonify({'error': 'Ese NIE ya tiene una cuenta registrada.'}), 400
        return jsonify({'error': str(e)}), 400


@app.route('/api/estudiantes/<int:id>', methods=['DELETE'])
def eliminar_estudiante(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM estudiantes WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'eliminado'})


@app.route('/api/login-estudiante', methods=['POST'])
def login_estudiante():
    datos = request.json
    nie = str(datos.get('nie', '')).strip()
    password = str(datos.get('password', '')).strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, nie, nombre, password FROM estudiantes WHERE nie = %s', (nie,))
    estudiante = cur.fetchone()
    cur.close()
    conn.close()

    if estudiante and estudiante.get('password') and check_password_hash(estudiante['password'], password):
        return jsonify({'status': 'ok', 'nie': estudiante['nie'], 'nombre': estudiante['nombre']})
    else:
        return jsonify({'error': 'NIE o contraseña incorrectos.'}), 401


init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
