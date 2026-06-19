import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import ccxt
import pandas as pd
import ta
import requests
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

TIMEFRAME = "4h" # Swing Timeframe

SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "TRX/USDT", "AVAX/USDT", "LINK/USDT",
    "DOT/USDT", "POL/USDT", "SHIB/USDT", "LTC/USDT", "UNI/USDT",
    "ATOM/USDT", "XLM/USDT", "NEAR/USDT", "APT/USDT", "SUI/USDT",
    "ARB/USDT", "OP/USDT", "INJ/USDT", "TIA/USDT", "FIL/USDT",
    "AAVE/USDT", "GRT/USDT", "PEPE/USDT", "FET/USDT", "FLOKI/USDT",
    "WIF/USDT", "SEI/USDT", "ETC/USDT", "ICP/USDT", "WLD/USDT",
    "IMX/USDT", "RENDER/USDT", "JUP/USDT", "STRK/USDT", "BONK/USDT",
    "ONDO/USDT", "PYTH/USDT", "ENA/USDT", "ORDI/USDT", "KAS/USDT",
    "MINA/USDT", "JTO/USDT", "BLUR/USDT", "API3/USDT", "W/USDT"
]

def get_decimals(price):
    if price > 100: return 2
    elif price > 1: return 3
    elif price > 0.01: return 5
    else: return 8

def get_next_signal_id():
    filename = "signal_counter.txt"
    try:
        with open(filename, "r") as file:
            current_id = int(file.read().strip())
    except (FileNotFoundError, ValueError):
        current_id = 0
    
    next_id = current_id + 1
    
    try:
        with open(filename, "w") as file:
            file.write(str(next_id))
    except Exception as e:
        print(f"Error saving signal ID: {e}")
        
    return f"{next_id:03d}"

# New Function to generate the dynamic professional summary
def generate_summary(direction, strategy, df, tp1, tp4, sl):
    direction_word = "bullish" if direction == "LONG" else "bearish"
    rsi_val = round(df['rsi'].iloc[-1], 1)
    
    # 1. Determine Structure Text
    if df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1]:
        structure_txt = "4H chart shows a strong bullish structure with key EMAs stacked upward."
    else:
        structure_txt = "4H chart shows a strong bearish structure with key EMAs stacked downward."

    # 2. Determine Strategy Specific Text
    if "Pullback" in strategy:
        if direction == "LONG":
            action_txt = "A healthy pullback to dynamic support (EMA 21) has been rejected, resuming the uptrend."
        else:
            action_txt = "A temporary rise to dynamic resistance (EMA 21) has been rejected, resuming the downtrend."
    elif "Volume" in strategy:
        action_txt = f"A massive institutional volume spike has been detected, driving {direction_word} momentum."
    else: # Swing Trend
        action_txt = f"A major EMA 50/200 crossover confirms a new {direction_word} swing phase."

    # 3. Determine RSI Text
    if direction == "LONG":
        rsi_txt = f"RSI at {rsi_val} supports room to run before overbought conditions." if rsi_val < 60 else f"RSI is strong at {rsi_val}, confirming high buying pressure."
    else:
        rsi_txt = f"RSI at {rsi_val} supports room to drop before oversold conditions." if rsi_val > 40 else f"RSI is weak at {rsi_val}, confirming high selling pressure."

    # 4. Combine Levels
    levels_txt = f"Key level to hold is the {sl} stop; immediate target at {tp1} with final extension near {tp4}."

    # Assemble Final Summary
    summary = f"📊 {structure_txt} {action_txt} {rsi_txt} {levels_txt}"
    return summary

def send_crypto_signal(coin_name, direction, strategy, entry, leverage, tp1, tp2, tp3, tp4, sl, summary_text):
    signal_id = get_next_signal_id()
    trend_emoji = "📈" if direction.lower() == "long" else "📉"
    direction_text = "Long" if direction.lower() == "long" else "Short"
    clean_name = coin_name.replace("/", "")
    
    zone_low = round(entry * 0.9985, get_decimals(entry))
    zone_high = round(entry * 1.0015, get_decimals(entry))

    text = f"🔖 Signal ID: {signal_id}\n📩 #{clean_name} | {strategy}\n{trend_emoji} {direction_text} Entry Zone: {zone_low}-{zone_high}\n⚡ Leverage: {leverage}x\n\n🎯 Strategy Details:\nTarget 1: {tp1}\nTarget 2: {tp2}\nTarget 3: {tp3}\nTarget 4: {tp4}\n\n🔺 Stop-Loss: {sl}\n💡 After reaching the first target you can put the rest of the position to breakeven.\n\n{summary_text}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True}
    try:
        response = requests.post(url, json=payload)
        if response.json().get('ok'): print(f"Signal {signal_id} sent for {coin_name} via {strategy}")
        else: print(f"ERROR for {coin_name}: {response.json().get('description')}")
    except Exception as e: print(f"Network error: {e}")

def analyze_and_trade():
    print(f"Starting SWING Scan ({TIMEFRAME}) - Pullback / Volume / Swing...")
    exchange = ccxt.mexc()
    
    for symbol in SYMBOLS:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=250)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            current_close = df['close'].iloc[-1]
            current_open = df['open'].iloc[-1]
            decimals = get_decimals(current_close)
            
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
            df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            df['vol_sma'] = df['volume'].rolling(window=20).mean()

            # ==========================================
            # 1. Pullback Strategy
            # ==========================================
            pullback_buy = (df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1]) and \
                           (df['low'].iloc[-1] <= df['ema_21'].iloc[-1]) and \
                           (current_close > df['ema_21'].iloc[-1]) and \
                           (df['rsi'].iloc[-1] < 60)

            pullback_sell = (df['ema_50'].iloc[-1] < df['ema_200'].iloc[-1]) and \
                            (df['high'].iloc[-1] >= df['ema_21'].iloc[-1]) and \
                            (current_close < df['ema_21'].iloc[-1]) and \
                            (df['rsi'].iloc[-1] > 40)

            # ==========================================
            # 2. Volume Strategy
            # ==========================================
            vol_buy = (df['volume'].iloc[-1] > df['vol_sma'].iloc[-1] * 2.5) and (current_close > current_open)
            vol_sell = (df['volume'].iloc[-1] > df['vol_sma'].iloc[-1] * 2.5) and (current_close < current_open)

            # ==========================================
            # 3. Swing Strategy
            # ==========================================
            swing_buy = (df['ema_50'].iloc[-2] <= df['ema_200'].iloc[-2]) and (df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1])
            swing_sell = (df['ema_50'].iloc[-2] >= df['ema_200'].iloc[-2]) and (df['ema_50'].iloc[-1] < df['ema_200'].iloc[-1])

            # ==========================================
            # Setup signals and trigger
            # ==========================================
            entry = round(current_close, decimals)
            lev = "5"
            
            long_tps = (round(entry * 1.03, decimals), round(entry * 1.06, decimals), round(entry * 1.10, decimals), round(entry * 1.15, decimals))
            long_sl = round(entry * 0.96, decimals)
            
            short_tps = (round(entry * 0.97, decimals), round(entry * 0.94, decimals), round(entry * 0.90, decimals), round(entry * 0.85, decimals))
            short_sl = round(entry * 1.04, decimals)

            # Triggering signals and passing the generated summary
            if pullback_buy:
                summary = generate_summary("LONG", "Swing Pullback", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", f"Swing Pullback", entry, lev, *long_tps, long_sl, summary)
                time.sleep(2)
            elif pullback_sell:
                summary = generate_summary("SHORT", "Swing Pullback", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", f"Swing Pullback", entry, lev, *short_tps, short_sl, summary)
                time.sleep(2)

            elif vol_buy:
                summary = generate_summary("LONG", "Swing Volume", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", f"Swing Volume", entry, lev, *long_tps, long_sl, summary)
                time.sleep(2)
            elif vol_sell:
                summary = generate_summary("SHORT", "Swing Volume", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", f"Swing Volume", entry, lev, *short_tps, short_sl, summary)
                time.sleep(2)

            elif swing_buy:
                summary = generate_summary("LONG", "Swing Trend", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", f"Swing Trend", entry, lev, *long_tps, long_sl, summary)
                time.sleep(2)
            elif swing_sell:
                summary = generate_summary("SHORT", "Swing Trend", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", f"Swing Trend", entry, lev, *short_tps, short_sl, summary)
                time.sleep(2)
                
        except Exception as e:
            print(f"Error {symbol}: {e}")

if __name__ == "__main__":
    print("Custom Swing Bot started...")
    analyze_and_trade()
