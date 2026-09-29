from datetime import datetime
import json
import urllib.parse  # <--- Importante para codificar la URL correctamente
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
  # Codificar los parámetros y evitar caracteres de control o espacios inválidos
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
  st.warning(
      "No se pudieron cargar los datos en este momento. Intenta recargar la"
      " página."
  )
else:
  # Sidebar: Filtros y Segmentación
  st.sidebar.header("⚙️ Panel de Control y Filtros")

  segmentacion = st.sidebar.selectbox(
      "Agrupar información por:",
      ["Diario", "Semanal", "Mensual", "Anual"],
      index=2,
  )

  st.sidebar.subheader("🚨 Configuración de Alertas")
  activar_alerta = st.sidebar.checkbox("Activar alerta por umbral de TMR", value=True)
  limite_alerta = st.sidebar.number_input(
      "Notificar si la TMR supera (COP):",
      min_value=1000.0,
      max_value=10000.0,
      value=4500.0,
      step=50.0,
  )

  # Procesamiento y agrupación de datos
  datos_filtrados = {}
  for d in datos:
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
        f"🚨 **¡ALERTA FINANCIERA!** La TMR actual es de **${ultimo_valor:,.2f} COP**"
        f" (Supera el límite configurado de ${limite_alerta:,.2f})."
    )
  else:
    st.success(
        f"✅ **Estado Normal:** TMR actual en ${ultimo_valor:,.2f} COP al"
        f" {ultima_fecha}."
    )

  # Cálculo de Crecimiento
  primer_valor = valores_graf[0]
  cambio_absoluto = ultimo_valor - primer_valor
  cambio_porcentual = (cambio_absoluto / primer_valor) * 100

  col1, col2, col3 = st.columns(3)
  col1.metric(
      label="TMR Actual",
      value=f"${ultimo_valor:,.2f} COP",
      delta=f"{cambio_porcentual:.2f}% histórico",
  )
  col2.metric(
      label="Variación Absoluta",
      value=f"${abs(cambio_absoluto):,.2f} COP",
      delta_color="inverse",
  )
  col3.metric(label="Total Registros Agrupados", value=len(valores_graf))

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

  with st.expander("Ver datos tabulares detallados"):
    st.write(
        "Mostrando los últimos registros procesados según la segmentación"
        " elegida:"
    )
    tabla_datos = [
        {"Periodo": k, "TMR (COP)": v} for k, v in list(datos_filtrados.items())[-20:]
    ]
    st.table(tabla_datos)
