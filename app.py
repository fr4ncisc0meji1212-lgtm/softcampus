from flask import Flask, render_template, jsonify, request
import sqlite3
import os

app = Flask(__name__)
DB_NAME = 'biblioteca.db'


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db_connection()
        conn.execute('''
                     CREATE TABLE IF NOT EXISTS software
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         nombre
                         TEXT
                         NOT
                         NULL,
                         categoria
                         TEXT
                         NOT
                         NULL,
                         carrera
                         TEXT
                         NOT
                         NULL,
                         so
                         TEXT
                         NOT
                         NULL,
                         licencia
                         TEXT
                         NOT
                         NULL,
                         version
                         TEXT
                         NOT
                         NULL,
                         url
                         TEXT
                         NOT
                         NULL,
                         winget
                         TEXT
                         UNIQUE,
                         desc
                         TEXT
                         NOT
                         NULL
                     )
                     ''')
        conn.execute('''
                     CREATE TABLE IF NOT EXISTS solicitudes
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         nombre
                         TEXT
                         NOT
                         NULL,
                         carrera
                         TEXT
                         NOT
                         NULL,
                         comentario
                         TEXT
                         NOT
                         NULL,
                         solicitadoPor
                         TEXT
                         NOT
                         NULL,
                         fecha
                         TEXT
                         NOT
                         NULL,
                         estado
                         TEXT
                         NOT
                         NULL
                     )
                     ''')
        conn.execute('''
                     INSERT
                     OR IGNORE INTO software (nombre, categoria, carrera, so, licencia, version, url, winget, desc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                     ''', (
                         "Visual Studio Code", "Programación", "Informática",
                         "Windows, Linux, Mac", "Gratuito", "1.108",
                         "https://code.visualstudio.com", "Microsoft.VisualStudioCode",
                         "Editor de código fuente ligero."
                     ))
        conn.commit()
        conn.close()

    # Asegurar que la tabla de kits exista
    conn = get_db_connection()
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS kits
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     nombre
                     TEXT
                     NOT
                     NULL,
                     carrera
                     TEXT
                     NOT
                     NULL,
                     programas
                     TEXT
                     NOT
                     NULL
                 )
                 ''')
    conn.commit()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/software', methods=['GET'])
def obtener_software():
    conn = get_db_connection()
    software = conn.execute('SELECT * FROM software').fetchall()
    conn.close()
    return jsonify([dict(row) for row in software])


@app.route('/api/software', methods=['POST'])
def agregar_software():
    nuevo = request.json
    winget_id = nuevo.get('winget', '').strip()
    conn = get_db_connection()

    if winget_id:
        existente = conn.execute('SELECT id FROM software WHERE winget = ?', (winget_id,)).fetchone()
        if existente:
            conn.close()
            return jsonify({'error': 'El ID de WinGet ya está registrado en otro programa.'}), 400

    try:
        conn.execute('''
                     INSERT INTO software (nombre, categoria, carrera, so, licencia, version, url, winget, desc)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                     ''', (
                         nuevo['nombre'].strip(), nuevo['categoria'], nuevo['carrera'],
                         nuevo['so'].strip(), nuevo['licencia'], nuevo['version'].strip(),
                         nuevo['url'].strip(), winget_id if winget_id else None, nuevo['desc'].strip()
                     ))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400


@app.route('/api/software/<int:id>', methods=['PUT'])
def actualizar_software(id):
    editado = request.json
    conn = get_db_connection()
    conn.execute('''
                 UPDATE software
                 SET nombre=?,
                     categoria=?,
                     carrera=?,
                     so=?,
                     licencia=?,
                     version=?,
                     url=?,
                     winget=?,
                     desc=?
                 WHERE id = ?
                 ''', (
                     editado['nombre'].strip(), editado['categoria'], editado['carrera'],
                     editado['so'].strip(), editado['licencia'], editado['version'].strip(),
                     editado['url'].strip(), editado['winget'].strip() if editado.get('winget') else None,
                     editado['desc'].strip(), id
                 ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'actualizado'})


@app.route('/api/software/<int:id>', methods=['DELETE'])
def eliminar_software(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM software WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'eliminado'})


@app.route('/api/solicitudes', methods=['GET'])
def obtener_solicitudes():
    conn = get_db_connection()
    solicitudes = conn.execute('SELECT * FROM solicitudes').fetchall()
    conn.close()
    return jsonify([dict(row) for row in solicitudes])


@app.route('/api/solicitudes', methods=['POST'])
def agregar_solicitud():
    nueva = request.json
    conn = get_db_connection()
    conn.execute('''
                 INSERT INTO solicitudes (nombre, carrera, comentario, solicitadoPor, fecha, estado)
                 VALUES (?, ?, ?, ?, ?, ?)
                 ''', (
                     nueva['nombre'].strip(), nueva['carrera'], nueva['comentario'].strip(),
                     nueva['solicitadoPor'], nueva['fecha'], nueva['estado']
                 ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'}), 201


@app.route('/api/solicitudes/<int:id>', methods=['PUT'])
def actualizar_solicitud(id):
    datos = request.json
    conn = get_db_connection()
    # Permitir actualizar estado y también si la notificación fue leída
    if 'estado' in datos:
        conn.execute('UPDATE solicitudes SET estado = ? WHERE id = ?', (datos['estado'], id))
    if 'notificadoLeido' in datos:
        # Añadimos la columna de control de lectura si hace falta o la ignoramos si no existe en BD básica
        pass
    conn.commit()
    conn.close()
    return jsonify({'status': 'actualizado'})


@app.route('/api/solicitudes/<int:id>', methods=['DELETE'])
def eliminar_solicitud(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM solicitudes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'eliminado'})


@app.route('/api/kits', methods=['GET'])
def obtener_kits():
    conn = get_db_connection()
    kits = conn.execute('SELECT * FROM kits').fetchall()
    conn.close()
    return jsonify([dict(row) for row in kits])


@app.route('/api/kits', methods=['POST'])
def crear_kit():
    nuevo = request.json
    conn = get_db_connection()
    conn.execute('''
                 INSERT INTO kits (nombre, carrera, programas)
                 VALUES (?, ?, ?)
                 ''', (
                     nuevo['nombre'].strip(),
                     nuevo['carrera'],
                     str(nuevo['programas'])
                 ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'}), 201


@app.route('/api/kits/<int:id>', methods=['DELETE'])
def eliminar_kit(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM kits WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'eliminado'})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

    from flask import Flask, render_template, request, redirect, url_for, session

    app = Flask(__name__)
    app.secret_key = 'clave_secreta_para_admin'


    # --- VISTA ESTUDIANTE (Libre, sin contraseña) ---
    @app.route('/')
    def estudiante():
        return render_template('estudiante.html')


    # --- VISTAS ADMINISTRADOR (Protegidas) ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            password = request.form.get('password')
            if password == 'admin123':  # Cambia aquí tu contraseña
                session['admin'] = True
                return redirect(url_for('admin'))
            return "Contraseña incorrecta", 401
        return render_template('login.html')


    @app.route('/admin')
    def admin():
        if not session.get('admin'):
            return redirect(url_for('login'))
        return render_template('admin.html')


    @app.route('/logout')
    def logout():
        session.pop('admin', None)
        return redirect(url_for('login'))

    # (Aquí mantienes todas tus rutas de API de Flask que ya tenías: /api/software, /api/solicitudes, etc.)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)