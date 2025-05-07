# =============================================================================
# Script Python: El Cerebro de la Automatización (Multi-Estrategia con Ejemplos)
# Versión con Ejecución Directa en MT5 y Notificaciones Telegram
# -----------------------------------------------------------------------------
# Responsable de:
# 1. Conectarse a un terminal MetaTrader 5.
# 2. Cargar parámetros para la estrategia activa desde CSV.
# 3. Obtener datos para el timeframe requerido.
# 4. Aplicar la lógica de la estrategia activa.
# 5. Si hay señal, enviar la orden directamente a MT5.
# 6. Enviar notificaciones por Telegram.
# =============================================================================

import MetaTrader5 as mt5
import time
import datetime
import pandas as pd
import numpy as np
import os
import sys
import logging

# Librerías requeridas (asumimos que están instaladas)
import pandas_ta as ta
from telegram import Bot
from telegram.error import TelegramError


# --- Configuración del Logger ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout) # Para ver logs en consola
        # logging.FileHandler("trading_brain.log") # Descomentar para logs en archivo
    ]
)
logger = logging.getLogger(__name__)

# --- Configuración General del Sistema ---
MT5_TERMINAL_PATH = "C:\\Users\\Usuario\\AppData\\Roaming\\MetaTrader\\terminal64.exee"
MagicNumber = 12345

ACTIVE_STRATEGY_NAME = "EMA_Crossover"
ACTIVE_PARAM_SET_NAME = "H1_Safe"
symbol = "EURUSD"
CHECK_INTERVAL_SECONDS = 10

# --- Configuración de Notificaciones Telegram ---
TELEGRAM_BOT_TOKEN = "7744884363:AAH-jAD6Iuocg4TT5l0Cz8AdguoRVFJlI2U"
TELEGRAM_CHAT_ID = "6314518866" # Tu Chat ID numérico

telegram_bot = None
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    try:
        telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
        logger.info("Bot de Telegram inicializado.")
    except Exception as e:
        logger.error(f"Error al inicializar el bot de Telegram: {e}")
        telegram_bot = None
else:
    logger.warning("Token o Chat ID de Telegram no configurados. Notificaciones deshabilitadas.")


def send_telegram_message(message):
    if telegram_bot is None:
        return
    try:
        telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')
        logger.debug(f"Mensaje enviado a Telegram: '{message[:50]}...'") # Cambiado a debug para menos verbosidad
    except TelegramError as e:
        logger.error(f"ERROR al enviar mensaje a Telegram: {e}")
        if "chat not found" in str(e).lower() or "bot was blocked by the user" in str(e).lower():
            logger.error("VERIFICA TU TELEGRAM_CHAT_ID o si el bot fue bloqueado.")
    except Exception as e:
        logger.error(f"ERROR inesperado al enviar mensaje a Telegram: {e}")

# --- Conexión MT5 ---
def connect_mt5():
    logger.info(f"Intentando conectar al terminal MT5 en: {MT5_TERMINAL_PATH}...")
    if not mt5.initialize(path=MT5_TERMINAL_PATH):
        logger.error(f"Fallo en la inicialización de MT5: {mt5.last_error()}")
        send_telegram_message(f"🔴 CRÍTICO: Fallo en la inicialización de MT5: {mt5.last_error()}")
        return False
    
    logger.info(f"Conexión a MT5 exitosa. Versión: {mt5.version()}")
    account_info = mt5.account_info()
    if account_info:
        logger.info(f"Conectado a la cuenta: {account_info.login}, Servidor: {account_info.server}, Balance: {account_info.balance} {account_info.currency}")
        start_message = (
            f"✅ *Script de Trading INICIADO*\n"
            f"Broker: `{account_info.broker}`\n"
            f"Cuenta: `{account_info.login}` (`{account_info.currency}`)\n"
            f"Estrategia: *{ACTIVE_STRATEGY_NAME}* / Set: *{ACTIVE_PARAM_SET_NAME}*\n"
            f"Símbolo: *{symbol}*"
        )
        send_telegram_message(start_message)
    else:
        logger.warning("No se pudo obtener información de la cuenta MT5.")
        send_telegram_message(f"⚠️ Conexión a MT5 exitosa, pero no se pudo obtener info de la cuenta.")
    return True

def disconnect_mt5():
    logger.info("Desconectando de MT5.")
    send_telegram_message("🛑 Script de Trading DETENIDO. Desconectando de MT5.")
    mt5.shutdown()

# --- Carga de Parámetros desde Archivo CSV ---
CONFIG_FILE_RELATIVE_PATH = os.path.join("config", "parameters.csv")

def load_parameters(strategy_name, param_set_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE_PATH = os.path.join(script_dir, CONFIG_FILE_RELATIVE_PATH)
    # Asegúrate de que la carpeta 'config' y el archivo 'parameters.csv' existan en la ubicación correcta
    # relativa al script.

    logger.info(f"Intentando cargar parámetros desde: {CONFIG_FILE_PATH}")
    logger.info(f"Buscando Estrategia='{strategy_name}', Set='{param_set_name}'...")

    try:
        if not os.path.exists(CONFIG_FILE_PATH):
            logger.error(f"Archivo de configuración no encontrado: {CONFIG_FILE_PATH}")
            return None

        params_df = pd.read_csv(CONFIG_FILE_PATH)
        
        required_system_cols = ['StrategyName', 'ParamSetName', 'Timeframe', 'NumCandles', 'LotSize']
        if not all(col in params_df.columns for col in required_system_cols):
            missing_cols = [col for col in required_system_cols if col not in params_df.columns]
            logger.error(f"CSV de parámetros no tiene todas las columnas mínimas requeridas. Faltan: {missing_cols}")
            return None

        # Comparación insensible a mayúsculas/minúsculas y espacios
        param_row = params_df[
            (params_df['StrategyName'].str.strip().str.lower() == strategy_name.strip().lower()) &
            (params_df['ParamSetName'].str.strip().str.lower() == param_set_name.strip().lower())
        ]

        if param_row.empty:
            logger.error(f"No se encontraron parámetros para Strategy='{strategy_name}', Set='{param_set_name}' en {CONFIG_FILE_PATH}.")
            return None
        
        if len(param_row) > 1:
             logger.warning(f"Se encontraron múltiples filas para Strategy='{strategy_name}', Set='{param_set_name}'. Usando la primera.")

        parameters = param_row.iloc[0].dropna().to_dict()

        try:
            parameters['NumCandles'] = int(parameters['NumCandles'])
            parameters['LotSize'] = float(parameters['LotSize'])
            if parameters['NumCandles'] <= 0 or parameters['LotSize'] <= 0.0: # LotSize puede ser muy pequeño
                raise ValueError("NumCandles y LotSize deben ser positivos.")
            if parameters['Timeframe'] not in TIMEFRAME_MAP:
                logger.error(f"Timeframe '{parameters['Timeframe']}' no es válido. Valores permitidos: {list(TIMEFRAME_MAP.keys())}")
                return None
        except (ValueError, KeyError) as e:
            logger.error(f"Error de tipo, valor o ausencia en NumCandles/LotSize/Timeframe para {strategy_name}/{param_set_name}: {e}")
            return None

        logger.info(f"Parámetros cargados para {strategy_name}/{param_set_name}.")
        return parameters

    except FileNotFoundError: # Ya cubierto por os.path.exists
        logger.error(f"Archivo de configuración no encontrado: {CONFIG_FILE_PATH}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"El archivo CSV de parámetros '{CONFIG_FILE_PATH}' está vacío.")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al cargar parámetros desde CSV '{CONFIG_FILE_PATH}': {e}", exc_info=True)
        return None

# --- Obtención de Datos Históricos ---
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1, "MN1": mt5.TIMEFRAME_MN1,
}

def get_historical_data(symbol_name, timeframe_str, count):
    mt5_timeframe = TIMEFRAME_MAP.get(timeframe_str)
    if mt5_timeframe is None:
        logger.error(f"Timeframe '{timeframe_str}' no válido.")
        return None
    if count <= 0:
        logger.error(f"Número de velas ({count}) debe ser positivo.")
        return None

    try:
        rates = mt5.copy_rates_from_pos(symbol_name, mt5_timeframe, 0, count)
    except Exception as e:
        logger.error(f"Excepción al llamar a copy_rates_from_pos para {symbol_name} {timeframe_str}: {e}", exc_info=True)
        return None

    if rates is None:
        logger.error(f"Fallo al obtener datos para {symbol_name} {timeframe_str}: {mt5.last_error()}")
        return None
    elif len(rates) == 0:
        logger.warning(f"No se recibieron datos para {symbol_name} {timeframe_str} (solicitadas: {count}).")
        return pd.DataFrame() 
    
    rates_frame = pd.DataFrame(rates)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s', utc=True)
    rates_frame.set_index('time', inplace=True)
    return rates_frame

# --- Helper para Validación y Conversión de Parámetros de Estrategia ---
def _validate_and_convert_params(parameters, param_specs, strategy_name):
    typed_params = {}
    for p_name, spec in param_specs.items():
        if p_name not in parameters:
            if spec.get('required', True):
                msg = f"ERROR ({strategy_name}): Parámetro requerido '{p_name}' no encontrado en CSV."
                logger.error(msg)
                send_telegram_message(f"⚠️ ERROR Config ({strategy_name}): Falta '{p_name}' en CSV.")
                return None
            else:
                typed_params[p_name] = spec.get('default', None)
                continue
        
        try:
            value_str = str(parameters[p_name]).strip() # Limpiar espacios
            if spec['type'] == float and ',' in value_str: # Manejar comas decimales si vienen del CSV
                value_str = value_str.replace(',', '.')
            
            value = spec['type'](value_str)

            if 'min_val' in spec and value < spec['min_val']:
                msg = f"ERROR ({strategy_name}): Parámetro '{p_name}' ({value}) < min ({spec['min_val']})."
                logger.error(msg)
                send_telegram_message(f"⚠️ ERROR Config ({strategy_name}): '{p_name}' ({value}) < min ({spec['min_val']}).")
                return None
            if 'max_val' in spec and value > spec['max_val']:
                msg = f"ERROR ({strategy_name}): Parámetro '{p_name}' ({value}) > max ({spec['max_val']})."
                logger.error(msg)
                send_telegram_message(f"⚠️ ERROR Config ({strategy_name}): '{p_name}' ({value}) > max ({spec['max_val']}).")
                return None
            typed_params[p_name] = value
        except (ValueError, TypeError) as e:
            msg = f"ERROR ({strategy_name}): Parámetro '{p_name}' ('{parameters[p_name]}') tipo inválido. Esperado {spec['type'].__name__}. Error: {e}"
            logger.error(msg)
            send_telegram_message(f"⚠️ ERROR Config ({strategy_name}): Tipo inválido para '{p_name}'.")
            return None
    return typed_params


# =============================================================================
# Lógicas de Estrategias Individuales
# =============================================================================

def strategy_ema_crossover(rates_frame, parameters):
    strategy_name = "EMA Crossover"
    param_specs = {
        'EMA_Fast': {'type': int, 'required': True, 'min_val': 1},
        'EMA_Slow': {'type': int, 'required': True, 'min_val': 2},
        'SL_PIPS': {'type': float, 'required': True, 'min_val': 0},
        'TP_PIPS': {'type': float, 'required': True, 'min_val': 0},
    }
    
    params_dict = _validate_and_convert_params(parameters, param_specs, strategy_name)
    if not params_dict: return None

    ema_period_fast = params_dict['EMA_Fast']
    ema_period_slow = params_dict['EMA_Slow']
    sl_pips = params_dict['SL_PIPS']
    tp_pips = params_dict['TP_PIPS']
    lot_size = parameters['LotSize'] 

    if ema_period_fast >= ema_period_slow:
        logger.error(f"ERROR ({strategy_name}): EMA_Fast ({ema_period_fast}) debe ser < EMA_Slow ({ema_period_slow}).")
        return None

    min_candles_needed = max(ema_period_fast, ema_period_slow) + 2
    if rates_frame is None or len(rates_frame) < min_candles_needed:
        return None

    try:
        df_copy = rates_frame.copy() # Trabajar sobre una copia
        df_copy[f'EMA_{ema_period_fast}'] = ta.ema(df_copy['close'], length=ema_period_fast)
        df_copy[f'EMA_{ema_period_slow}'] = ta.ema(df_copy['close'], length=ema_period_slow)
    except Exception as e:
        logger.error(f"Error calculando EMAs ({strategy_name}): {e}", exc_info=True)
        return None
        
    ema_fast_col_name = f'EMA_{ema_period_fast}'
    ema_slow_col_name = f'EMA_{ema_period_slow}'

    if ema_fast_col_name not in df_copy.columns or ema_slow_col_name not in df_copy.columns:
        logger.warning(f"({strategy_name}) Columnas EMA no encontradas después del cálculo.")
        return None

    df_copy.dropna(subset=[ema_fast_col_name, ema_slow_col_name], inplace=True)
    if len(df_copy) < 2: # Necesitamos al menos 2 puntos para comparar cruce
        return None

    ema_fast_current = df_copy[ema_fast_col_name].iloc[-1]
    ema_slow_current = df_copy[ema_slow_col_name].iloc[-1]
    ema_fast_previous = df_copy[ema_fast_col_name].iloc[-2]
    ema_slow_previous = df_copy[ema_slow_col_name].iloc[-2]
    
    action = None
    # Cruce alcista: la rápida estaba por debajo o igual y ahora está por encima
    if ema_fast_previous <= ema_slow_previous and ema_fast_current > ema_slow_current:
        logger.info(f"({strategy_name}) Cruce ALCISTA: EMA{ema_period_fast}({ema_fast_current:.5f}) > EMA{ema_period_slow}({ema_slow_current:.5f})")
        action = "BUY"
    # Cruce bajista: la rápida estaba por encima o igual y ahora está por debajo
    elif ema_fast_previous >= ema_slow_previous and ema_fast_current < ema_slow_current:
        logger.info(f"({strategy_name}) Cruce BAJISTA: EMA{ema_period_fast}({ema_fast_current:.5f}) < EMA{ema_period_slow}({ema_slow_current:.5f})")
        action = "SELL"

    if action:
        return {'action': action, 'lot_size': lot_size, 'sl_pips': sl_pips, 'tp_pips': tp_pips}
    return None


def strategy_bb_rsi_scalper(rates_frame, parameters):
    strategy_name = "BB+RSI Scalper"
    param_specs = {
        'BB_Period': {'type': int, 'required': True, 'min_val': 2},
        'BB_Deviations': {'type': float, 'required': True, 'min_val': 0.1},
        'RSI_Period': {'type': int, 'required': True, 'min_val': 2},
        'RSI_Oversold': {'type': float, 'required': True, 'min_val': 1, 'max_val': 99},
        'RSI_Overbought': {'type': float, 'required': True, 'min_val': 1, 'max_val': 99},
        'SL_PIPS': {'type': float, 'required': True, 'min_val': 0},
        'TP_PIPS': {'type': float, 'required': True, 'min_val': 0}
    }
    params_dict = _validate_and_convert_params(parameters, param_specs, strategy_name)
    if not params_dict: return None

    bb_period = params_dict['BB_Period']
    bb_dev = params_dict['BB_Deviations'] # pandas_ta espera std como float
    rsi_period = params_dict['RSI_Period']
    rsi_oversold = params_dict['RSI_Oversold']
    rsi_overbought = params_dict['RSI_Overbought']
    sl_pips = params_dict['SL_PIPS']
    tp_pips = params_dict['TP_PIPS']
    lot_size = parameters['LotSize']

    if rsi_oversold >= rsi_overbought:
        logger.error(f"ERROR ({strategy_name}): RSI_Oversold ({rsi_oversold}) debe ser < RSI_Overbought ({rsi_overbought}).")
        return None

    min_candles_needed = max(bb_period, rsi_period) + 1
    if rates_frame is None or rates_frame.empty or len(rates_frame) < min_candles_needed:
        return None

    df_copy = rates_frame.copy()
    try:
        bbands_df = ta.bbands(close=df_copy['close'], length=bb_period, std=bb_dev)
        if bbands_df is None or bbands_df.empty:
             logger.warning(f"({strategy_name}) Cálculo de BBands retornó None o vacío.")
             return None
        # pandas_ta puede nombrar las columnas como BBL_length_std.0, BBM_..., BBU_...
        # Es más seguro acceder por índice si los nombres exactos son inciertos o varían entre versiones de pandas_ta
        df_copy['BBL'] = bbands_df.iloc[:, 0]  # Lower band
        # df_copy['BBM'] = bbands_df.iloc[:, 1]  # Middle band (opcional)
        df_copy['BBU'] = bbands_df.iloc[:, 2]  # Upper band
        
        df_copy['RSI'] = ta.rsi(close=df_copy['close'], length=rsi_period)
    except Exception as e:
        logger.error(f"Error calculando BB/RSI ({strategy_name}): {e}", exc_info=True)
        return None
        
    required_cols = ['BBL', 'BBU', 'RSI', 'close']
    df_copy.dropna(subset=required_cols, inplace=True)
    if df_copy.empty:
        return None

    current_close = df_copy['close'].iloc[-1]
    current_bb_lower = df_copy['BBL'].iloc[-1]
    current_bb_upper = df_copy['BBU'].iloc[-1]
    current_rsi = df_copy['RSI'].iloc[-1]
     
    action = None
    if current_close <= current_bb_lower and current_rsi <= rsi_oversold:
        logger.info(f"({strategy_name}) COMPRA: Close({current_close:.5f})<=BBL({current_bb_lower:.5f}) & RSI({current_rsi:.2f})<={rsi_oversold}")
        action = "BUY"
    elif current_close >= current_bb_upper and current_rsi >= rsi_overbought:
        logger.info(f"({strategy_name}) VENTA: Close({current_close:.5f})>=BBU({current_bb_upper:.5f}) & RSI({current_rsi:.2f})>={rsi_overbought}")
        action = "SELL"

    if action:
        return {'action': action, 'lot_size': lot_size, 'sl_pips': sl_pips, 'tp_pips': tp_pips}
    return None

# Implementa las otras estrategias (DT_MACD_EMA, ST_PSAR_ADX) aquí.

# =============================================================================
# Mapeo de Nombres de Estrategia a Funciones
# =============================================================================
STRATEGY_FUNCTIONS = {
    "EMA_Crossover": strategy_ema_crossover,
    "SC_BB_RSI": strategy_bb_rsi_scalper,
    # "DT_MACD_EMA": strategy_macd_ema_daytrading,
    # "ST_PSAR_ADX": strategy_psar_adx_swingtrading,
}


# =============================================================================
# Función de Envío de Órdenes a MT5
# =============================================================================
def send_mt5_order(symbol_name, order_type_str, lot, sl_pips, tp_pips, magic_number_val, comment="PyBot"):
    
    symbol_info = mt5.symbol_info(symbol_name)
    if symbol_info is None:
        logger.error(f"No se pudo obtener información para {symbol_name}. Orden no enviada.")
        send_telegram_message(f"❌ Error Órden: No se pudo obtener info para `{symbol_name}`.")
        return None

    if not symbol_info.visible:
        logger.warning(f"Símbolo {symbol_name} no visible. Intentando agregarlo...")
        if not mt5.symbol_select(symbol_name, True):
            err_mt5 = mt5.last_error()
            logger.error(f"No se pudo hacer visible {symbol_name}. MT5 Error: {err_mt5}. Orden no enviada.")
            send_telegram_message(f"❌ Error Órden: `{symbol_name}` no visible y no se pudo agregar (Error: {err_mt5[1]}).")
            return None
        time.sleep(0.5) 
        symbol_info = mt5.symbol_info(symbol_name)
        if not symbol_info or not symbol_info.visible:
            logger.error(f"Símbolo {symbol_name} sigue sin estar visible. Orden no enviada.")
            send_telegram_message(f"❌ Error Órden: `{symbol_name}` no se pudo hacer visible.")
            return None
        logger.info(f"Símbolo {symbol_name} ahora visible.")

    point = symbol_info.point
    digits = symbol_info.digits
    
    tick = mt5.symbol_info_tick(symbol_name)
    if tick is None:
        logger.error(f"No se pudo obtener tick actual para {symbol_name}. Orden no enviada.")
        send_telegram_message(f"❌ Error Órden: No se pudo obtener tick para `{symbol_name}`.")
        return None

    price = 0.0
    order_type_mt5 = None

    if order_type_str.upper() == "BUY":
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = tick.ask
    elif order_type_str.upper() == "SELL":
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        logger.error(f"Tipo de orden desconocido: {order_type_str}")
        send_telegram_message(f"❌ Error Órden: Tipo de orden desconocido `{order_type_str}`.")
        return None

    if price == 0.0:
        logger.error(f"Precio para {symbol_name} es 0.0 ({order_type_str}). Orden no enviada.")
        send_telegram_message(f"❌ Error Órden: Precio para `{symbol_name}` es 0.0.")
        return None

    sl_price = 0.0
    tp_price = 0.0

    if sl_pips > 0:
        sl_abs_value = sl_pips * point
        if order_type_mt5 == mt5.ORDER_TYPE_BUY: sl_price = price - sl_abs_value
        else: sl_price = price + sl_abs_value
        sl_price = round(sl_price, digits)

    if tp_pips > 0:
        tp_abs_value = tp_pips * point
        if order_type_mt5 == mt5.ORDER_TYPE_BUY: tp_price = price + tp_abs_value
        else: tp_price = price - tp_abs_value
        tp_price = round(tp_price, digits)
    
    volume_min = symbol_info.volume_min
    volume_max = symbol_info.volume_max
    volume_step = symbol_info.volume_step
    
    lot_adj = lot
    if lot_adj < volume_min:
        logger.warning(f"Lote {lot_adj:.{len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0}f} < min {volume_min:.{len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0}f} para {symbol_name}. Usando {volume_min:.{len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0}f}.")
        lot_adj = volume_min
    if lot_adj > volume_max:
        logger.warning(f"Lote {lot_adj:.{len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0}f} > max {volume_max:.{len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0}f} para {symbol_name}. Usando {volume_max:.{len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0}f}.")
        lot_adj = volume_max
    
    # Ajustar lote al volume_step
    lot_adj = round(int(lot_adj / volume_step) * volume_step, len(str(volume_step).split('.')[1]) if '.' in str(volume_step) else 0)
    if lot_adj == 0.0 and lot > 0.0: 
        logger.warning(f"Lote ajustado a 0.0 para {symbol_name} (orig: {lot}, step: {volume_step}). Usando volumen mínimo {volume_min}.")
        lot_adj = volume_min

    request = {
        "action": mt5.TRADE_ACTION_DEAL, # Ejecución de mercado
        "symbol": symbol_name,
        "volume": lot_adj,
        "type": order_type_mt5,
        "price": price, # Para órdenes de mercado, MT5 usa el precio actual
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 20, 
        "magic": magic_number_val,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC, 
    }
    
    logger.info(f"Enviando orden: {order_type_str} {lot_adj:.2f} {symbol_name} @ {price:.{digits}f} SL={sl_price:.{digits}f} TP={tp_price:.{digits}f} M={magic_number_val}")
    
    result = None
    try:
        result = mt5.order_send(request)
    except Exception as e: # Capturar excepciones más generales también
        logger.error(f"Excepción durante mt5.order_send: {e}", exc_info=True)
        send_telegram_message(f"💥 Excepción MT5: Error al enviar orden para `{symbol_name}`: {e}")
        return None

    if result is None:
        err_code_tuple = mt5.last_error()
        logger.error(f"mt5.order_send() retornó None. MT5 Error: {err_code_tuple}")
        send_telegram_message(f"❌ Error Órden MT5: order_send retornó None para `{symbol_name}`. Código: {err_code_tuple[0]}, Desc: {err_code_tuple[1]}")
        return None

    logger.info(f"Resultado orden_send: retcode={result.retcode}, deal={result.deal}, order={result.order}, comment='{result.comment}'")

    retcode_messages = { # Solo algunos ejemplos, lista completa en la documentación de MQL5
        10004: "Requote", 10006: "Request rejected", 10007: "Request cancelled by trader",
        10008: "Order placed", 10009: "Request completed", 10013: "Invalid request",
        10014: "Invalid volume", 10015: "Invalid price", 10016: "Invalid stops (SL/TP too close or wrong side)",
        10017: "Trade is disabled", 10018: "Market is closed", 10019: "Not enough money",
        10020: "Prices changed", 10021: "Too many requests", 10024: "No connection with trade server",
        10027: "Too frequent requests to the same order",
        4016: "Mobile trading disabled by server (for this account)", # Ejemplo de error específico
    }
    retcode_message = retcode_messages.get(result.retcode, f"Retcode no mapeado: {result.retcode}")

    if result.retcode == mt5.TRADE_RETCODE_DONE or result.retcode == mt5.TRADE_RETCODE_PLACED:
        msg = (
            f"✅ *Orden Enviada/Colocada!*\n"
            f"Acción: *{order_type_str} {symbol_name}*\n"
            f"Volumen: {result.volume:.2f}\n"
            f"Precio Ejec: {result.price:.{digits}f}\n"
            f"SL: {result.sl:.{digits}f} (Sol: {sl_price:.{digits}f})\n"
            f"TP: {result.tp:.{digits}f} (Sol: {tp_price:.{digits}f})\n"
            f"Ticket: *{result.order}*\n"
            # f"Comentario Broker: `{result.comment}`\n" # Puede ser largo
            f"Retcode: {result.retcode} ({retcode_message})"
        )
        send_telegram_message(msg)
    else:
        msg = (
            f"❌ *Fallo al Enviar Orden!*\n"
            f"Acción: {order_type_str} {symbol_name}\n"
            f"Vol Solicitado: {lot_adj:.2f}\n"
            f"Retcode: *{result.retcode}* ({retcode_message})\n"
            f"Comentario Broker: `{result.comment}`\n"
            f"Error MT5 (last_error): {mt5.last_error()[1]}" # Descripción del último error
        )
        send_telegram_message(msg)
        logger.error(f"Orden para {symbol_name} falló: Retcode={result.retcode} - {result.comment}. MT5 Error: {mt5.last_error()}")
    
    return result


# =============================================================================
# Bucle Principal del Sistema
# =============================================================================
def main_loop():
    logger.info("Iniciando el Cerebro de Automatización...")

    if not connect_mt5():
        logger.critical("No se pudo conectar a MT5. Saliendo.")
        sys.exit(1)

    parameters = load_parameters(ACTIVE_STRATEGY_NAME, ACTIVE_PARAM_SET_NAME)
    if parameters is None:
        err_msg = f"No se pudieron cargar los parámetros para {ACTIVE_STRATEGY_NAME}/{ACTIVE_PARAM_SET_NAME}. Saliendo."
        logger.critical(err_msg)
        send_telegram_message(f"🔴 CRÍTICO: {err_msg} Revisa `config/parameters.csv`.")
        disconnect_mt5()
        sys.exit(1)
    
    timeframe_str = parameters['Timeframe']
    num_candles_to_fetch = parameters['NumCandles']

    active_strategy_function = STRATEGY_FUNCTIONS.get(ACTIVE_STRATEGY_NAME)
    if not active_strategy_function:
        err_msg = f"Estrategia '{ACTIVE_STRATEGY_NAME}' no encontrada. Saliendo."
        logger.critical(err_msg)
        send_telegram_message(f"🔴 CRÍTICO: {err_msg} Revisa STRATEGY_FUNCTIONS.")
        disconnect_mt5()
        sys.exit(1)
    
    logger.info(f"Estrategia: {ACTIVE_STRATEGY_NAME} ({ACTIVE_PARAM_SET_NAME}) | Símbolo: {symbol} | TF: {timeframe_str}")
    logger.info(f"Velas: {num_candles_to_fetch} | Lote: {parameters['LotSize']} | SL: {parameters.get('SL_PIPS','N/A')}p | TP: {parameters.get('TP_PIPS','N/A')}p")

    last_checked_candle_time = None 

    try:
        while True:
            if not mt5.terminal_info().connected:
                logger.error("Desconectado de MT5. Intentando reconectar...")
                send_telegram_message("🔌 Desconectado de MT5. Intentando reconectar...")
                if not connect_mt5(): 
                    logger.warning("Fallo al reconectar. Esperando para reintentar...")
                    time.sleep(CHECK_INTERVAL_SECONDS * 3) 
                    continue 
            
            latest_candle_df = get_historical_data(symbol, timeframe_str, 1)
            
            if latest_candle_df is not None and not latest_candle_df.empty:
                new_candle_open_time = latest_candle_df.index[-1] 

                if last_checked_candle_time is None or new_candle_open_time > last_checked_candle_time:
                    logger.info(f"Nueva vela {timeframe_str} [{symbol}]: {new_candle_open_time.strftime('%Y-%m-%d %H:%M:%S %Z')}. Verificando...")
                    last_checked_candle_time = new_candle_open_time
                    
                    # Es crucial obtener los datos FRESCOS aquí para la decisión
                    rates_frame_for_strategy = get_historical_data(symbol, timeframe_str, num_candles_to_fetch)
                    
                    if rates_frame_for_strategy is not None and not rates_frame_for_strategy.empty:
                        if len(rates_frame_for_strategy) < num_candles_to_fetch:
                             logger.warning(f"Datos obtenidos: {len(rates_frame_for_strategy)} velas, solicitadas: {num_candles_to_fetch}.")

                        # Pasar una copia a la estrategia para evitar modificaciones no deseadas del dataframe original
                        order_params = active_strategy_function(rates_frame_for_strategy.copy(), parameters) 
                        
                        if order_params:
                            logger.info(f"SEÑAL: {order_params['action']} {symbol} | Lote:{order_params['lot_size']}, SL:{order_params['sl_pips']}p, TP:{order_params['tp_pips']}p")
                            send_mt5_order(
                                symbol_name=symbol, 
                                order_type_str=order_params['action'],
                                lot=order_params['lot_size'],
                                sl_pips=order_params['sl_pips'],
                                tp_pips=order_params['tp_pips'],
                                magic_number_val=MagicNumber,
                                comment=f"{ACTIVE_STRATEGY_NAME[:7]}-{ACTIVE_PARAM_SET_NAME[:5]}" # Comentario más corto
                            )
                    else:
                        logger.warning(f"No se pudieron obtener datos históricos completos para {symbol} {timeframe_str} para el análisis de la estrategia.")
            else:
                logger.warning(f"No se pudo obtener la última vela para {symbol} {timeframe_str} (para chequear nueva barra).")

            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Interrupción por teclado detectada. Saliendo...")
    except Exception as e:
        error_msg = f"Error inesperado en el bucle principal: {e}"
        logger.critical(error_msg, exc_info=True)
        send_telegram_message(f"💥 CRÍTICO: Error en bucle principal: `{e}`")
    finally:
        disconnect_mt5()
        logger.info("Cerebro de Automatización detenido.")

if __name__ == "__main__":
    terminal_dir = os.path.dirname(MT5_TERMINAL_PATH)
    if not os.path.exists(MT5_TERMINAL_PATH) and not os.path.isdir(terminal_dir):
        logger.error(f"El directorio del terminal MT5 ('{terminal_dir}') NO existe.")
        logger.error("Verifica la configuración de MT5_TERMINAL_PATH.")
        send_telegram_message(f"🔴 CRÍTICO: Directorio del terminal MT5 `{terminal_dir}` NO existe. Verifica `MT5_TERMINAL_PATH`.")
    elif not os.path.exists(MT5_TERMINAL_PATH) and os.path.isdir(terminal_dir):
         logger.warning(f"El archivo terminal64.exe no se encontró en '{MT5_TERMINAL_PATH}', pero el directorio sí existe. mt5.initialize() podría intentar encontrar otro terminal.")
            
    main_loop()