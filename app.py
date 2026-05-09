from flask import Flask, render_template, request, redirect, send_file
from pymongo import MongoClient
from datetime import datetime
import os

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# =========================
# CONEXIÓN A MONGODB
# =========================
# 🔥 REEMPLAZA <db_password> CON TU CONTRASEÑA REAL
MONGO_URI = "mongodb+srv://mariaxd:<cris123>@cluster0.svaktzr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI)
    db = client['sistema_reportes']  # Nombre de la base de datos
    coleccion = db['reportes']        # Nombre de la colección
    print("✅ Conectado a MongoDB Atlas")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")

# =========================
# GENERAR NUMERO
# =========================
def generar_numero():
    # Obtener el último reporte
    ultimo = coleccion.find_one(sort=[('Numero', -1)])
    if not ultimo:
        return "R-001"
    
    try:
        num_str = ultimo.get('Numero', 'R-000')
        num = int(num_str.replace('R-', ''))
        return f"R-{num + 1:03d}"
    except:
        return "R-001"

# =========================
# BUSCAR REPORTE POR NOMBRE Y TELÉFONO
# =========================
def buscar_reporte_por_nombre_telefono(nombre, telefono):
    return coleccion.find_one({
        'Nombre': nombre,
        'Telefono': telefono
    })

# =========================
# INICIO
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = None
    tipo_mensaje = "success"
    reporte_duplicado = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        veces = request.form.get("veces", "0")

        if not nombre or not telefono:
            mensaje = "Nombre y teléfono son obligatorios"
            tipo_mensaje = "danger"
        else:
            reporte_existente = buscar_reporte_por_nombre_telefono(nombre, telefono)
            
            if reporte_existente:
                mensaje = f"⚠️ El reporte {reporte_existente['Numero']} ya existe."
                tipo_mensaje = "warning"
                reporte_duplicado = reporte_existente
            else:
                dependencia = request.form.get("dependencia", "")
                dependencia_extra = request.form.get("dependencia_extra", "").strip()
                tipo = request.form.get("tipo", "")
                tipo_extra = request.form.get("tipo_extra", "").strip()

                dependencia_final = dependencia_extra if dependencia_extra else dependencia
                tipo_final = tipo_extra if tipo_extra else tipo

                nuevo = {
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Nombre": nombre,
                    "Telefono": telefono,
                    "Veces": veces,
                    "Dependencia": dependencia_final,
                    "Tipo": tipo_final,
                    "Numero": generar_numero()
                }

                coleccion.insert_one(nuevo)
                mensaje = "Reporte guardado exitosamente"
                tipo_mensaje = "success"

    # Obtener todos los reportes desde MongoDB
    todos_reportes = list(coleccion.find().sort('Numero', -1))
    total = len(todos_reportes)

    return render_template(
        "index.html",
        mensaje=mensaje,
        tipo_mensaje=tipo_mensaje,
        total=total,
        todos_reportes=todos_reportes,
        ahora=datetime.now().strftime("%d/%m/%Y"),
        reporte_duplicado=reporte_duplicado
    )

# =========================
# EDITAR
# =========================
@app.route("/editar", methods=["POST"])
def editar():
    try:
        numero = request.form.get("numero_editar", "").strip()
        nuevo_nombre = request.form.get("nombre_editar", "").strip()
        nuevo_telefono = request.form.get("telefono_editar", "").strip()
        
        dependencia = request.form.get("dependencia_editar", "")
        dependencia_extra = request.form.get("dependencia_extra_editar", "").strip()
        
        tipo = request.form.get("tipo_editar", "")
        tipo_extra = request.form.get("tipo_extra_editar", "").strip()
        
        veces = request.form.get("veces_editar", "0")

        if not numero or not nuevo_nombre or not nuevo_telefono:
            return redirect('/')

        dependencia_final = dependencia_extra if dependencia_extra else dependencia
        tipo_final = tipo_extra if tipo_extra else tipo

        # Actualizar en MongoDB
        coleccion.update_one(
            {'Numero': numero},
            {'$set': {
                'Nombre': nuevo_nombre,
                'Telefono': nuevo_telefono,
                'Dependencia': dependencia_final,
                'Tipo': tipo_final,
                'Veces': veces
            }}
        )
        
        return redirect('/')

    except Exception as e:
        print(f"Error al editar: {e}")
        return redirect('/')

# =========================
# ELIMINAR
# =========================
@app.route('/delete/<numero>')
def delete_reporte(numero):
    try:
        coleccion.delete_one({'Numero': numero})
        return redirect('/')

    except Exception as e:
        print(f"Error al eliminar: {e}")
        return redirect('/')

# =========================
# EXPORTAR PDF
# =========================
@app.route("/pdf")
def pdf():
    from reportlab.lib.pagesizes import letter
    
    todos_reportes = list(coleccion.find().sort('Numero', -1))
    
    if not todos_reportes:
        return "No hay reportes para mostrar.", 200

    df = pd.DataFrame(todos_reportes)

    archivo = "reportes.pdf"
    doc = SimpleDocTemplate(archivo, pagesize=letter)
    elementos = []

    datos = [list(df.columns)]
    for fila in df.values:
        datos.append(list(fila))

    tabla = Table(datos)

    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.blue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elementos.append(tabla)
    doc.build(elementos)

    return send_file(archivo, as_attachment=True)

# =========================
# EJECUTAR
# =========================
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')