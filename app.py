import os
import psycopg2
import psycopg2.extras
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

    cur.execute('''
        CREATE TABLE IF NOT EXISTS kits (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            carrera TEXT NOT NULL,
            programas TEXT NOT NULL
        )
    ''')

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


@app.route('/api/solicitudes', methods=['GET'])
def obtener_solicitudes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM solicitudes')
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
        INSERT INTO solicitudes (nombre, carrera, comentario, solicitadoPor, fecha, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (
        nueva['nombre'].strip(), nueva['carrera'], nueva['comentario'].strip(),
        nueva['solicitadoPor'], nueva['fecha'], nueva['estado']
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


init_db()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
