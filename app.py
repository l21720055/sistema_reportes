from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import json
import os
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

ARCHIVO_JSON = "reportes.json"
ARCHIVO_EXCEL = "reportes.xlsx"

# =========================
# CARGAR DATOS
# =========================
def cargar_datos():
    if not os.path.exists(ARCHIVO_JSON):
        return []
    try:
        with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# =========================
# GUARDAR DATOS
# =========================
def guardar_datos(data):
    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =========================
# ACTUALIZAR EXCEL
# =========================
def actualizar_excel():
    data = cargar_datos()
    if not data:
        return
    
    df = pd.DataFrame(data)
    df.to_excel(ARCHIVO_EXCEL, index=False)

# =========================
# GENERAR NUMERO
# =========================
def generar_numero():
    data = cargar_datos()
    if not data:
        return "R-001"
    
    try:
        numeros = []
        for item in data:
            num_str = item.get('Numero', 'R-000')
            num = int(num_str.replace('R-', ''))
            numeros.append(num)
        max_num = max(numeros)
        return f"R-{max_num + 1:03d}"
    except:
        return "R-001"

# =========================
# BUSCAR REPORTE POR NOMBRE Y TELÉFONO
# =========================
def buscar_reporte_por_nombre_telefono(nombre, telefono):
    data = cargar_datos()
    for item in data:
        if item.get('Nombre') == nombre and item.get('Telefono') == telefono:
            return item
    return None

# =========================
# INICIO
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = None
    tipo_mensaje = "success"
    reporte_duplicado = None
    nombre_buscado = ""
    telefono_buscado = ""

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        veces = request.form.get("veces", "0")

        nombre_buscado = nombre
        telefono_buscado = telefono

        if not nombre or not telefono:
            mensaje = "Nombre y teléfono son obligatorios"
            tipo_mensaje = "danger"
        else:
            # Verificar si ya existe un reporte con el mismo nombre y teléfono
            reporte_existente = buscar_reporte_por_nombre_telefono(nombre, telefono)
            
            if reporte_existente:
                # Si existe, guardar el reporte duplicado
                reporte_duplicado = reporte_existente
                mensaje = f"El reporte {reporte_existente['Numero']} ya existe."
                tipo_mensaje = "warning"
            else:
                # Si no existe, crear un nuevo reporte
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

                data = cargar_datos()
                data.append(nuevo)
                guardar_datos(data)
                actualizar_excel()

                mensaje = "Reporte guardado exitosamente"
                tipo_mensaje = "success"

    data = cargar_datos()
    total = len(data)
    
    # MOSTRAR TODOS LOS REPORTES (no solo los últimos 5)
    # Ordenar por número descendente (del más nuevo al más antiguo)
    todos_reportes = sorted(data, key=lambda x: x['Numero'], reverse=True)

    return render_template(
        "index.html",
        mensaje=mensaje,
        tipo_mensaje=tipo_mensaje,
        total=total,
        todos_reportes=todos_reportes,
        ahora=datetime.now().strftime("%d/%m/%Y"),
        reporte_duplicado=reporte_duplicado,
        nombre_buscado=nombre_buscado,
        telefono_buscado=telefono_buscado
    )

# =========================
# EDITAR (NUEVA LÓGICA)
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

        data = cargar_datos()
        
        # Buscar el reporte original
        reporte_original = None
        indice_original = -1
        for i, item in enumerate(data):
            if item.get('Numero') == numero:
                reporte_original = item
                indice_original = i
                break
        
        if reporte_original:
            # Verificar si solo aumentó las veces o cambió algo más
            if (reporte_original['Nombre'] == nuevo_nombre and 
                reporte_original['Telefono'] == nuevo_telefono and
                reporte_original['Dependencia'] == dependencia_final and
                reporte_original['Tipo'] == tipo_final):
                
                # Solo aumentar veces
                data[indice_original]['Veces'] = veces
                mensaje = "Veces actualizadas correctamente"
            else:
                # Crear un nuevo reporte (no borrar el anterior)
                nuevo_reporte = {
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Nombre": nuevo_nombre,
                    "Telefono": nuevo_telefono,
                    "Veces": veces,
                    "Dependencia": dependencia_final,
                    "Tipo": tipo_final,
                    "Numero": generar_numero()
                }
                data.append(nuevo_reporte)
                mensaje = "Nuevo reporte creado (el anterior se conserva)"
            
            guardar_datos(data)
            actualizar_excel()
        
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
        data = cargar_datos()
        data = [item for item in data if item.get('Numero') != numero]
        guardar_datos(data)
        actualizar_excel()
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
    
    data = cargar_datos()
    
    if not data:
        return "No hay reportes para mostrar.", 200

    df = pd.DataFrame(data)

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