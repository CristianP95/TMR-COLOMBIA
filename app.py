from datetime import datetime, date
import json
import urllib.parse
import urllib.request
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Analizador TMR Colombia", page_icon="📈", layout="wide"
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
    tmr_hoy = datos[-1]["valor"] # Último valor real del dataset global (Hoy)

    # Cabecera principal con TMR de Hoy destacada al lado del título
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.title("🇨🇴 Histórico y Análisis de la TMR")
    with col_badge:
        st.metric(label="💵 TMR de Hoy", value=f"${tmr_hoy:,.2f} COP")

    st.markdown(
        "Datos oficiales obtenidos en tiempo real desde el portal de datos abiertos de Colombia (`datos.gov.co`)."
    )

    # Inicializar Session State para el botón de restablecer filtros
    if "rango_anios" not in st.session_state:
        st.session_state.rango_anios = (fecha_min_global.year, fecha_max_global.year)
    if "segmentacion" not in st.session_state:
        st.session_state.segmentacion = "Mensual"
    if "limite_alerta" not in st.session_state:
        st.session_state.limite_alerta = 4500.0

    def reset_filtros():
        st.session_state.rango_anios = (fecha_min_global.year, fecha_max_global.year)
        st.session_state.segmentacion = "Mensual"
        st.session_state.limite_alerta = 4500.0

    # Sidebar: Panel de Control, Segmentación y Filtros con Slider
    st.sidebar.header("⚙️ Panel de Control y Filtros")

    # Botón de Restablecer Filtros
    st.sidebar.button("🔄 Restablecer Filtros", on_click=reset_filtros)

    # 1. Filtro de Rango de Años con Barra de Desplazamiento (Slider)
    st.sidebar.subheader("📅 Rango de Años en el Eje X")
    rango_anios = st.sidebar.slider(
        "Selecciona el intervalo de años:",
        min_value=fecha_min_global.year,
        max_value=fecha_max_global.year,
        value=st.session_state.rango_anios,
        key="rango_anios"
    )

    # 2. Selector de segmentación
    st.sidebar.subheader("📊 Agrupación")
    segmentacion = st.sidebar.selectbox(
        "Agrupar información por:",
        ["Diario", "Semanal", "Mensual", "Anual"],
        index=["Diario", "Semanal", "Mensual", "Anual"].index(st.session_state.segmentacion),
        key="segmentacion"
    )

    # 3. Configuración de Alertas
    st.sidebar.subheader("🚨 Configuración de Alertas")
    activar_alerta = st.sidebar.checkbox("Activar alerta por umbral de TMR", value=True)
    limite_alerta = st.sidebar.number_input(
        "Notificar si la TMR supera (COP):",
        min_value=1000.0,
        max_value=10000.0,
        step=50.0,
        key="limite_alerta"
    )

    # Filtrar datos según el rango de años seleccionado en el slider
    anio_inicio, anio_fin = rango_anios
    datos_en_rango = [
        d for d in datos 
        if anio_inicio <= d["fecha"].year <= anio_fin
    ]

    if not datos_en_rango:
        st.warning("No hay registros en el rango de años seleccionado.")
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

        # Estadísticas del periodo seleccionado
        promedio_periodo = sum(valores_graf) / len(valores_graf)
        max_periodo = max(valores_graf)
        min_periodo = min(valores_graf)

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

        # Métricas Superiores Organizadas (4 columnas principales del rango)
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
