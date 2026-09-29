from datetime import datetime, date
import json
import urllib.parse
import urllib.request
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Analizador TMR Colombia", page_icon="📈", layout="wide"
)

st.title("🇨🇴 Histórico y Análisis de la Tasa Representativa del Mercado (TMR)")
st.markdown(
    "Datos oficiales obtenidos en tiempo real desde el portal de datos abiertos"
    " de Colombia (`datos.gov.co`)."
)

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
    # Definir límites globales basados en los datos
    fecha_min_global = datos[0]["fecha"].date()
    fecha_max_global = datos[-1]["fecha"].date()

    # Sidebar: Panel de Control, Segmentación y Filtros de Fecha
    st.sidebar.header("⚙️ Panel de Control y Filtros")

    # 1. Filtro de Rango de Fechas (Nuevo)
    st.sidebar.subheader("📅 Rango de Fechas en el Eje X")
    rango_fechas = st.sidebar.date_input(
        "Selecciona el intervalo:",
        value=(fecha_min_global, fecha_max_global),
        min_value=fecha_min_global,
        max_value=fecha_max_global
    )

    # 2. Selector de segmentación (Ya establecido)
    st.sidebar.subheader("📊 Agrupación")
    segmentacion = st.sidebar.selectbox(
        "Agrupar información por:",
        ["Diario", "Semanal", "Mensual", "Anual"],
        index=2,
    )

    # 3. Configuración de Alertas
    st.sidebar.subheader("🚨 Configuración de Alertas")
    activar_alerta = st.sidebar.checkbox("Activar alerta por umbral de TMR", value=True)
    limite_alerta = st.sidebar.number_input(
        "Notificar si la TMR supera (COP):",
        min_value=1000.0,
        max_value=10000.0,
        value=4500.0,
        step=50.0,
    )

    # Filtrar datos según el rango de fechas seleccionado en la barra lateral
    if len(rango_fechas) == 2:
        f_inicio, f_fin = rango_fechas
        datos_en_rango = [
            d for d in datos 
            if f_inicio <= d["fecha"].date() <= f_fin
        ]
    else:
        datos_en_rango = datos

    if not datos_en_rango:
        st.warning("No hay registros en el rango de fechas seleccionado.")
    else:
        # Procesamiento y agrupación de datos filtrados
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

        # Sistema de Alertas
        if activar_alerta and ultimo_valor > limite_alerta:
            st.error(
                f"🚨 **¡ALERTA FINANCIERA!** La TMR actual en el rango es de **${ultimo_valor:,.2f} COP** "
                f"(Supera el límite configurado de ${limite_alerta:,.2f})."
            )
        else:
            st.success(
                f"✅ **Estado Normal:** TMR actual en ${ultimo_valor:,.2f} COP al {ultima_fecha}."
            )

        # Cálculo de Crecimiento para el rango seleccionado
        primer_valor = valores_graf[0]
        cambio_absoluto = ultimo_valor - primer_valor
        cambio_porcentual = (cambio_absoluto / primer_valor) * 100 if primer_valor > 0 else 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric(
            label="TMR al Final del Rango",
            value=f"${ultimo_valor:,.2f} COP",
            delta=f"{cambio_porcentual:.2f}% en el periodo",
        )
        col2.metric(
            label="Variación Absoluta",
            value=f"${abs(cambio_absoluto):,.2f} COP",
            delta_color="inverse",
        )
        col3.metric(label="Total Puntos en Gráfica", value=len(valores_graf))

        st.subheader(f"📈 Tendencia Histórica ({segmentacion})")

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
