from datetime import datetime, date
import json
import urllib.parse
import urllib.request
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Analizador TMR Colombia", page_icon="📈", layout="wide"
)

# Diccionarios en español para formatear la fecha de hoy
DIAS_ES = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

def obtener_fecha_formateada(dt):
    dia_semana = DIAS_ES.get(dt.strftime("%A"), "")
    mes = MESES_ES.get(dt.month, "")
    return f"{dia_semana} {dt.day} de {mes} de {dt.year}"

# Función para consumir la API con caché y codificación de URL segura
@st.cache_data(ttl=3600)
def cargar_datos_tmr():
    base_url = "https://www.datos.gov.co/resource/mcec-87by.json"
    parametros = {"$order": "vigenciadesde ASC", "$limit": "50000"}
    url = f"{base_url}?{urllib.parse.urlencode(parametros)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            datos_limpios = []
            for item in data:
                if "valor" in item and "vigenciadesde" in item:
                    fecha_str = item["vigenciadesde"].split("T")[0]
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                    valor = float(item["valor"])
                    datos_limpios.append({"fecha": fecha, "valor": valor})
            return datos_limpios
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
        return []

# Cargar datos
datos = cargar_datos_tmr()

if not datos:
    st.warning("No se pudieron cargar los datos en este momento. Intenta recargar la página.")
else:
    fecha_min_global = datos[0]["fecha"].date()
    fecha_max_global = datos[-1]["fecha"].date()
    tmr_hoy = datos[-1]["valor"]  
    fecha_hoy_obj = datos[-1]["fecha"]
    fecha_hoy_str = obtener_fecha_formateada(fecha_hoy_obj)

    # Cabecera principal con TMR de Hoy y su fecha detallada
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.title("🇨🇴 Histórico y Análisis de la TMR")
    with col_badge:
        st.metric(
            label="💵 TMR de Hoy", 
            value=f"${tmr_hoy:,.2f} COP", 
            delta=fecha_hoy_str,
            delta_color="off"
        )

    st.markdown(
        "Datos oficiales obtenidos en tiempo real desde el portal de datos abiertos de Colombia (`datos.gov.co`)."
    )

    # Sidebar: Panel de Control con jerarquía de filtros
    st.sidebar.header("⚙️ Panel de Control y Filtros")

    if st.sidebar.button("🔄 Restablecer Filtros"):
        st.rerun()

    st.sidebar.subheader("📊 Agrupación Temporal")
    segmentacion = st.sidebar.selectbox(
        "Agrupar información por:",
        ["Anual", "Mensual", "Semanal", "Diario"],
        index=1 
    )

    st.sidebar.subheader("📅 Rango del Eje X")
    
    if segmentacion == "Anual":
        anos_disponibles = sorted(list(set(d["fecha"].strftime("%Y") for d in datos)))
        rango_seleccionado = st.sidebar.select_slider(
            "Selecciona el intervalo de años:",
            options=anos_disponibles,
            value=(anos_disponibles[0], anos_disponibles[-1])
        )
        ini, fin = rango_seleccionado
        datos_en_rango = [d for d in datos if ini <= d["fecha"].strftime("%Y") <= fin]

    elif segmentacion == "Mensual":
        meses_disponibles = sorted(list(set(d["fecha"].strftime("%Y-%m") for d in datos)))
        rango_seleccionado = st.sidebar.select_slider(
            "Selecciona el intervalo de meses:",
            options=meses_disponibles,
            value=(meses_disponibles[0], meses_disponibles[-1])
        )
        ini, fin = rango_seleccionado
        datos_en_rango = [d for d in datos if ini <= d["fecha"].strftime("%Y-%m") <= fin]

    elif segmentacion == "Semanal":
        semanas_disponibles = sorted(list(set(d["fecha"].strftime("%Y-W%V") for d in datos)))
        rango_seleccionado = st.sidebar.select_slider(
            "Selecciona el intervalo de semanas:",
            options=semanas_disponibles,
            value=(semanas_disponibles[0], semanas_disponibles[-1])
        )
        ini, fin = rango_seleccionado
        datos_en_rango = [d for d in datos if ini <= d["fecha"].strftime("%Y-W%V") <= fin]

    else:  # Diario
        rango_fechas = st.sidebar.date_input(
            "Selecciona el intervalo de días:",
            value=(fecha_min_global, fecha_max_global),
            min_value=fecha_min_global,
            max_value=fecha_max_global
        )
        if len(rango_fechas) == 2:
            f_inicio, f_fin = rango_fechas
            datos_en_rango = [d for d in datos if f_inicio <= d["fecha"].date() <= f_fin]
        else:
            datos_en_rango = datos

    st.sidebar.subheader("🚨 Configuración de Alertas")
    activar_alerta = st.sidebar.checkbox("Activar alerta por umbral de TMR", value=True)
    limite_alerta = st.sidebar.number_input(
        "Notificar si la TMR supera (COP):",
        min_value=1000.0,
        max_value=10000.0,
        value=4500.0,
        step=50.0
    )

    if not datos_en_rango:
        st.warning("No hay registros en el rango seleccionado.")
    else:
        datos_filtrados = {}
        for d in datos_en_rango:
            f = d["fecha"]
            if segmentacion == "Diario":
                key = f.strftime("%Y-%m-%d")
            elif segmentacion == "Semanal":
                key = f.strftime("%Y-W%V")
            elif segmentacion == "Mensual":
                key = f.strftime("%Y-%m")
            else:
                key = f.strftime("%Y")

            datos_filtrados[key] = d["valor"]

        fechas_graf = list(datos_filtrados.keys())
        valores_graf = list(datos_filtrados.values())

        ultimo_valor = valores_graf[-1]
        ultima_fecha = fechas_graf[-1]

        # Fechas de inicio y fin exactas del período filtrado
        fecha_inicio_periodo = datos_en_rango[0]["fecha"].strftime("%d de %B de %Y")
        fecha_fin_periodo = datos_en_rango[-1]["fecha"].strftime("%d de %B de %Y")

        promedio_periodo = sum(valores_graf) / len(valores_graf)
        max_periodo = max(valores_graf)
        min_periodo = min(valores_graf)

        if activar_alerta and ultimo_valor > limite_alerta:
            st.error(
                f"🚨 **¡ALERTA FINANCIERA!** La TMR actual en el rango es de **${ultimo_valor:,.2f} COP** "
                f"(Supera el límite configurado de ${limite_alerta:,.2f})."
            )
        else:
            st.success(
                f"✅ **Estado Normal:** TMR actual en ${ultimo_valor:,.2f} COP al {ultima_fecha}."
            )

        primer_valor = valores_graf[0]
        cambio_absoluto = ultimo_valor - primer_valor
        cambio_porcentual = (cambio_absoluto / primer_valor) * 100 if primer_valor > 0 else 0.0

        # Métricas Superiores
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            label="TMR Final del Rango",
            value=f"${ultimo_valor:,.2f}",
            delta=f"{cambio_porcentual:.2f}%",
        )
        col2.metric(
            label="Promedio Periodo",
            value=f"${promedio_periodo:,.2f}",
        )
        col3.metric(
            label="Máximo Periodo",
            value=f"${max_periodo:,.2f}",
        )
        col4.metric(
            label="Mínimo Periodo",
            value=f"${min_periodo:,.2f}",
        )

        st.subheader(f"📈 Tendencia Histórica ({segmentacion})")
        
        # Subtítulo con las fechas de inicio y fin del rango analizado
        st.markdown(f"🗓️ **Intervalo analizado:** Del {datos_en_rango[0]['fecha'].strftime('%Y-%m-%d')} al {datos_en_rango[-1]['fecha'].strftime('%Y-%m-%d')}")

        chart_data = {
            "Periodo": fechas_graf,
            "TMR (COP)": valores_graf,
        }

        st.line_chart(
            chart_data,
            x="Periodo",
            y="TMR (COP)",
            use_container_width=True,
        )

        with st.expander("Ver datos tabulares detallados del rango"):
            st.write("Mostrando los registros procesados según los filtros aplicados:")
            tabla_datos = [
                {"Periodo": k, "TMR (COP)": v} for k, v in list(datos_filtrados.items())[-20:]
            ]
            st.table(tabla_datos)
