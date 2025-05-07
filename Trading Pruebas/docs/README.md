# Sistema de Trading Automatizado Adaptativo (Python-MT5 Directo)

## 🌐 Resumen del Proyecto

Este proyecto es un sistema de trading algorítmico diseñado para operar de forma automatizada en los mercados financieros a través de la plataforma MetaTrader 5. La arquitectura centralizada en Python permite la implementación de lógicas de estrategia complejas, análisis de mercado y gestión de decisiones, comunicándose directamente con el terminal MT5 para la obtención de datos en tiempo real y la ejecución de órdenes. El diseño modular facilita la adición y prueba de múltiples estrategias de trading (Scalping, Day Trading, Swing Trading) con parámetros configurables, con un enfoque primordial en la validación rigurosa en entornos demo antes de considerar su aplicación en cuentas reales. El proyecto tiene una visión a largo plazo orientada a la adaptabilidad, la detección de regímenes de mercado y la integración de técnicas de Machine Learning.

## ✨ Visión y Objetivos

### Visión a Largo Plazo

Construir un sistema de trading automatizado de alto rendimiento, capaz de adaptarse a condiciones de mercado cambiantes, optimizar su operación de forma autónoma y operar con un riesgo consistentemente controlado. Buscamos ser pioneros en la aplicación práctica de tecnología y análisis de datos avanzados para la automatización del trading.

### Objetivos Clave

* **Establecer una Arquitectura Robusta:** Implementar y refinar la comunicación bidireccional eficiente y fiable entre Python y el terminal MT5 para datos y ejecución.
* **Modularidad Estratégica:** Desarrollar un framework que permita definir, configurar y cambiar fácilmente entre diversas estrategias de trading.
* **Validación Empírica:** Implementar un proceso de prueba riguroso en cuentas demo para evaluar objetivamente el rendimiento de cada estrategia y set de parámetros.
* **Minimización de Pérdidas:** Desarrollar e implementar lógicas de gestión de riesgo robustas a nivel de estrategia y a nivel de sistema.
* **Adaptabilidad Futura:** Sentar las bases para incorporar detección de regímenes de mercado y modelos de Machine Learning para la toma de decisiones adaptativa.
* **Potencial de Crecimiento:** Crear un proyecto escalable con vistas a una eventual aplicación en trading con capital real y posible comercialización.

## 🧠 Metodología de Desarrollo

El proyecto adopta un enfoque pragmático y estructurado:

* **Desarrollo Iterativo:** Construcción incremental del sistema, comenzando con la infraestructura base y una estrategia simple, añadiendo complejidad y características en ciclos sucesivos.
* **Diseño Modular:** División del sistema en componentes lógicos (conexión de datos, carga de parámetros, lógica de estrategia individual, ejecución de órdenes, notificaciones) con interfaces claras. Esto facilita el desarrollo paralelo, la depuración y la reutilización de código.
* **Pruebas Guiadas por el Rendimiento:** La validación en cuenta demo es el motor del desarrollo. Las métricas de rendimiento (drawdown, profit factor, índice de pérdida, etc.) guían la mejora y el refinamiento de las estrategias y el código.
* **Configuración Basada en Datos:** La parametrización de las estrategias se desacopla del código principal mediante archivos de configuración (CSV), permitiendo experimentar con múltiples sets de parámetros sin modificar la lógica.
* **Enfoque "Demo-First":** Todo el desarrollo y la optimización inicial se realiza exclusivamente en entornos de simulación para mitigar el riesgo financiero.

## 🏗️ Arquitectura del Sistema

La arquitectura actual se basa en la comunicación directa entre un script Python y un terminal MetaTrader 5:

* **1. Componente Python ("El Cerebro"):**
    * **Ubicación:** Se ejecuta como un script independiente en el entorno Python del usuario (`Trading_Pruebas/src/trading_automatizado.py`).
    * **Funcionalidad:**
        * Establece conexión y se comunica con un terminal MT5 running a través de la librería `MetaTrader5`.
        * Obtiene datos de mercado (velas históricas, ticks) desde MT5.
        * Carga parámetros de estrategia desde `config/parameters.csv`.
        * Aplica la lógica de la estrategia activa a los datos de mercado.
        * Si se genera una señal de trading, construye la solicitud de orden (`MqlTradeRequest`).
        * **Envía la solicitud de orden DIRECTAMENTE al terminal MT5** usando `mt5.OrderSend()`.
        * Procesa y registra el resultado de la operación recibido de MT5.
        * Envía notificaciones en tiempo real a través de Telegram.
    * **Tecnologías:** Python 3.x, `MetaTrader5`, `pandas`, `numpy`, `pandas_ta`, `python-telegram-bot`.
* **2. Terminal MetaTrader 5 ("El Ejecutor y Proveedor de Datos"):**
    * **Ubicación:** Una instalación estándar o portable del terminal MetaTrader 5.
    * **Funcionalidad:**
        * Proporciona datos de mercado a la librería `MetaTrader5` cuando es solicitada por el script Python.
        * Recibe solicitudes de órdenes directamente desde el script Python a través de la API de `MetaTrader5`.
        * Ejecuta las órdenes recibidas con el broker.
        * Gestiona la conexión con el broker, la cuenta de trading, el historial, etc.
    * **Tecnologías:** Plataforma MetaTrader 5.
* **Capa de Comunicación:**
    * La librería `MetaTrader5` actúa como el puente tecnológico, traduciendo las llamadas de función de Python a solicitudes comprensibles para la API interna del terminal MT5 y viceversa (para datos y resultados de operaciones).
    * **Nota:** La comunicación por archivos (`trading_command.txt`) utilizada en arquitecturas Python-MT4 ya **no** forma parte del flujo principal de ejecución en esta arquitectura Python-MT5 directa.

## 📦 Estructura de Carpetas del Proyecto

La estructura recomendada para el proyecto Python (`Trading_Pruebas/`) es la siguiente:

Trading_Pruebas/
├── src/                      # Directorio principal del código fuente Python
│   └── trading_automatizado.py # Script principal del cerebro del sistema
│
├── config/                   # Directorio para archivos de configuración
│   └── parameters.csv        # Archivo CSV con los sets de parámetros de estrategia
│   └── settings.json         # (Opcional) Configuraciones generales del script (ej: Telegram credenciales si no son variables de entorno)
│
├── venv/                     # Directorio del Entorno Virtual de Python (¡IGNORAR en Git!)
│   └── ... (archivos del entorno virtual)
│
├── requirements.txt          # Archivo que lista las dependencias de librerías Python
│
├── tests/                    # Directorio (Opcional) para scripts de pruebas unitarias o de integración
│   └── ... (archivos de prueba)
│
└── docs/                     # Directorio (Opcional) para la documentación del proyecto
└── README.md             # Este archivo


* Los archivos y carpetas específicos del terminal MetaTrader 5 (ej: `MQL5/Experts/`, `MQL5/Files/`, `Logs/` dentro de la Carpeta de Datos de MT5) existen en una ubicación **separada** gestionada por el terminal MT5, no dentro de este proyecto Python.

## 🛠️ Configuración e Instalación

Para poner en marcha el sistema, sigue estos pasos:

1.  **Clonar/Descargar el Repositorio:** Obtén todos los archivos y carpetas dentro de la estructura `Trading_Pruebas/`.
2.  **Instalar MetaTrader 5:** Si aún no lo has hecho, descarga e instala el terminal MetaTrader 5 desde el sitio web oficial. Conéctalo a una cuenta demo.
3.  **Configurar Entorno Virtual de Python:**
    * Abre tu terminal o línea de comandos. Navega hasta la carpeta raíz de tu proyecto (`Trading_Pruebas/`).
    * Crea un entorno virtual (si es el primer uso): `python -m venv venv`
    * Activa el entorno virtual:
        * Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
        * Windows (Command Prompt): `.\venv\Scripts\activate.bat`
        * Linux/macOS/Git Bash: `source venv/bin/activate`
4.  **Instalar Dependencias Python:** Con el entorno virtual activado, instala las librerías necesarias.
    * Se recomienda crear un `requirements.txt` ejecutando `pip freeze > requirements.txt` después de instalar manualmente por primera vez. Luego, puedes instalar con:
        ```bash
        pip install -r requirements.txt
        ```
    * Alternativamente, instala manualmente las librerías clave:
        ```bash
        pip install MetaTrader5 pandas numpy pandas-ta python-telegram-bot
        ```
5.  **Configurar Archivo de Parámetros (`config/parameters.csv`):**
    * Edita el archivo `Trading_Pruebas/config/parameters.csv`.
    * Define tus estrategias y sets de parámetros utilizando las columnas especificadas (`StrategyName`, `ParamSetName`, `Timeframe`, `NumCandles`, `LotSize`, `SL_PIPS`, `TP_PIPS`, y los parámetros específicos de tus indicadores).
6.  **Configurar Credenciales de Telegram (¡IMPORTANTE!):**
    * Obtén tu **Token del Bot** de Telegram a través de `@BotFather`.
    * Obtén el **ID numérico del chat** donde quieres recibir las notificaciones (puede ser tu chat privado con el bot o el ID de un grupo). La forma más fiable es enviar un mensaje al bot en ese chat y usar `https://api.telegram.org/bot[TU_TOKEN]/getUpdates` en un navegador para ver el ID del chat dentro del JSON (en el objeto `"chat":{"id": ...}`).
    * En el script `trading_automatizado.py`, actualiza las variables `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` con tus datos. **Para producción, se recomienda usar variables de entorno o un archivo de configuración local excluido de control de versiones para estos datos sensibles.**
7.  **Configurar Ruta del Terminal MT5 (Opcional):**
    * En `trading_automatizado.py`, la línea `mt5.initialize()` intenta encontrar el terminal automáticamente.
    * Si la conexión falla, **descomenta** la línea `mt5.initialize(path=...)` y reemplaza la ruta con la **ruta completa y exacta** al archivo `terminal64.exe` (o `terminal.exe`) de tu instalación de MT5. Asegúrate de usar dobles barras invertidas (`\\`) en Windows.
8.  **Definir Estrategia Activa:** En `trading_automatizado.py`, modifica las variables `ACTIVE_STRATEGY_NAME` y `ACTIVE_PARAM_SET_NAME` para seleccionar qué estrategia y set de parámetros (definidos en `parameters.csv`) el script debe usar al ejecutarse. Asegúrate de que la estrategia seleccionada tenga su lógica implementada y activada en el diccionario `STRATEGY_FUNCTIONS`.

## ▶️ Ejecución del Sistema

1.  Abre tu terminal MetaTrader 5 y asegúrate de que esté corriendo y conectado a tu cuenta demo.
2.  Abre tu terminal de línea de comandos o la terminal integrada de VS Code.
3.  Activa tu entorno virtual de Python (`venv`).
4.  Navega hasta la carpeta raíz de tu proyecto (`Trading_Pruebas/`).
5.  Ejecuta el script Python:
    ```bash
    python src/trading_automatizado.py
    ```
6.  El script se conectará a MT5, cargará parámetros, y empezará a monitorear los datos según el `CHECK_INTERVAL_SECONDS` definido.

## 📊 Monitoreo y Depuración

* **Terminal de Python:** Observa los logs impresos en la terminal de VS Code.
* **Telegram:** Revisa los mensajes enviados por tu bot para notificaciones sobre inicio, errores, señales detectadas y resultados de órdenes.
* **Terminal MetaTrader 5:**
    * Pestaña "Trading": Para ver posiciones abiertas, órdenes pendientes y el Magic Number asociado.
    * Pestaña "History": Para revisar el historial de operaciones cerradas, incluyendo el Magic Number.
    * Pestaña "Expertos": Para ver los logs del terminal y los mensajes de la librería `MetaTrader5` sobre la conexión y los intentos de enviar órdenes (`mt5.OrderSend`). Los errores de ejecución (ej: margen insuficiente) también aparecerán aquí.

## 📈 Implementación de Estrategias

La lógica para cada estrategia reside en funciones separadas dentro de `trading_automatizado.py`.

* **Estructura de la Función de Estrategia:** Cada función (`strategy_ema_crossover`, `strategy_bb_rsi_scalper`, etc.) debe aceptar dos argumentos: `rates_frame` (DataFrame de Pandas con los datos de velas) y `parameters` (diccionario con los parámetros cargados desde CSV para esa estrategia y set).
* **Cálculo de Indicadores:** Utiliza `pandas_ta` para calcular los indicadores necesarios sobre el `rates_frame`.
* **Lógica de Señal:** Implementa las reglas exactas (condiciones) para determinar una señal de COMPRA o VENTA basándote en los valores de los indicadores y los parámetros cargados.
* **Validación de Parámetros:** Dentro de cada función de estrategia, **valida** que los parámetros específicos que esa estrategia necesita (`parameters.get('NombreParametro')`) existan y tengan valores válidos antes de usarlos.
* **Retorno:** Si se detecta una señal, la función debe retornar un **diccionario** con los detalles necesarios para la orden (al menos `{'action': 'BUY' o 'SELL', 'lot_size': valor, 'sl_pips': valor, 'tp_pips': valor}`). Si no hay señal, retorna `None`.
* **Activación:** Añade la función al diccionario `STRATEGY_FUNCTIONS` para que pueda ser seleccionada a través de `ACTIVE_STRATEGY_NAME`.

## ⏭️ Próximas Etapas y Contribución

Este proyecto está en desarrollo activo. Las próximas etapas incluyen completar la implementación de las lógicas de estrategia, refinar la gestión de riesgo, implementar la detección de regímenes y explorar la integración de Machine Learning.

¡Las contribuciones son bienvenidas! Si estás interesado en ayudar, considera:

* Implementar la lógica para estrategias adicionales.
* Mejorar la función `send_mt5_order` (ej: gestión de lotaje basada en riesgo).
* Implementar la lógica de detección de regímenes de mercado.
* Añadir manejo de errores más robusto.
* Mejorar el logging y el monitoreo.
* Escribir pruebas unitarias o de integración.
* Mejorar la documentación.

## ❓ Solución de Problemas (Ver también en el código)

* **`SyntaxError: ... unicodeescape...`:** Usar `\\` o `/` en rutas de Windows en Python.
* **`ImportError: cannot import name 'NaN' from 'numpy'`:** Problema de compatibilidad de librerías. Intenta reinstalar `pandas-ta` y `numpy` con `--no-cache-dir` o en un entorno virtual nuevo.
* **Fallo de `mt5.initialize()`:** Terminal MT5 no corriendo/conectado, o ruta en `MT5_TERMINAL_PATH` incorrecta (si se usa `path=`).
* **Notificaciones de Telegram no llegan:** Credenciales (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) incorrectas, bot no inicializado, bot bloqueado, problema de conexión a internet.
* **Órdenes no se envían/rechazadas:** Mensajes de error en la terminal de Python y en el log de Expertos de MT5 indicarán el motivo (margen, mercado cerrado, SL/TP inválido, trading deshabilitado).

## 📄 Licencia

Este proyecto está bajo la Licencia [Especificar Licencia, ej: MIT]. (Añadir archivo LICENSE si se publica).

---

Este documento es un punto de partida detallado. Puedes (y debes) expandirlo y adaptarlo a medida que tu proyecto evolucione y gane complejidad. Guarda este contenido en un archivo llamado `README.md` dentro de la carpeta `Trading_Pruebas/docs/`.