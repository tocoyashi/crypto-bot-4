import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import ccxt
import pandas as pd
import ta
import requests
import time
import random

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

def generate_summary(direction, strategy, df, tp1, tp4, sl):
    rsi_val = round(df['rsi'].iloc[-1], 1)
    
    if df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1]:
        structure_txt = random.choice([
            "4H chart shows a strong bullish structure with key EMAs stacked upward.",
            "Higher highs and higher lows on the 4H timeframe confirm a solid bullish trend.",
            "The 4H structure remains heavily bullish as price holds above major moving averages."
        ])
    else:
        structure_txt = random.choice([
            "4H chart shows a strong bearish structure with key EMAs stacked downward.",
            "Lower highs and lower lows on the 4H timeframe confirm a solid bearish trend.",
            "The 4H structure remains heavily bearish as price stays suppressed below key MAs."
        ])

    if "Pullback" in strategy:
        if direction == "LONG":
            action_txt = random.choice([
                "A healthy pullback to dynamic support (EMA 21) has been rejected, resuming the uptrend.",
                "Price dipped perfectly into the EMA 21 demand zone and bounced sharply.",
                "Buyers stepped in aggressively at the 21 EMA, signaling continuation."
            ])
        else:
            action_txt = random.choice([
                "A temporary rise to dynamic resistance (EMA 21) has been rejected, resuming the downtrend.",
                "Price rallied into the EMA 21 supply zone and was met with strong selling pressure.",
                "Sellers defended the 21 EMA aggressively, indicating bearish continuation."
            ])
    elif "Volume" in strategy:
        if direction == "LONG":
            action_txt = random.choice([
                "A massive institutional volume spike has been detected, driving bullish momentum.",
                "Unusual trading volume just broke out, suggesting smart money accumulation.",
                "Heavy buying pressure accompanied by a major volume explosion confirms the upside move."
            ])
        else:
            action_txt = random.choice([
                "A massive institutional volume spike has been detected, driving bearish momentum.",
                "Unusual trading volume just broke down, suggesting smart money distribution.",
                "Heavy selling pressure accompanied by a major volume explosion confirms the downside move."
            ])
    else: # Swing Trend
        if direction == "LONG":
            action_txt = random.choice([
                "A major EMA 50/200 golden cross confirms a new bullish swing phase.",
                "The recent bullish crossover of the 50 and 200 EMAs marks the start of a macro uptrend."
            ])
        else:
            action_txt = random.choice([
                "A major EMA 50/200 death cross confirms a new bearish swing phase.",
                "The recent bearish crossover of the 50 and 200 EMAs marks the start of a macro downtrend."
            ])

    if direction == "LONG":
        if rsi_val < 60:
            rsi_txt = random.choice([
                f"RSI at {rsi_val} supports room to run before overbought conditions.",
                f"RSI sitting comfortably at {rsi_val}, leaving plenty of upside breathing room.",
                f"Momentum indicator (RSI) reads {rsi_val}, confirming healthy buying strength."
            ])
        else:
            rsi_txt = random.choice([
                f"RSI is strong at {rsi_val}, confirming high buying pressure.",
                f"RSI shows extreme bullish power at {rsi_val}, riding the momentum wave."
            ])
    else:
        if rsi_val > 40:
            rsi_txt = random.choice([
                f"RSI at {rsi_val} supports room to drop before oversold conditions.",
                f"RSI sitting comfortably at {rsi_val}, leaving plenty of downside breathing room.",
                f"Momentum indicator (RSI) reads {rsi_val}, confirming healthy selling strength."
            ])
        else:
            rsi_txt = random.choice([
                f"RSI is weak at {rsi_val}, confirming high selling pressure.",
                f"RSI shows extreme bearish power at {rsi_val}, riding the downward momentum."
            ])

    if direction == "LONG":
        levels_txt = random.choice([
            f"Key level to hold is the {sl} stop; immediate target at {tp1} with final extension near {tp4}.",
            f"Invalidation point is set at {sl}; looking for an initial push towards {tp1} and a full run to {tp4}.",
            f"Risk is managed below {sl}; expecting a move to hit {tp1} initially, extending to {tp4}."
        ])
    else:
        levels_txt = random.choice([
            f"Key level to hold is the {sl} stop; immediate target at {tp1} with final extension near {tp4}.",
            f"Invalidation point is set at {sl}; looking for an initial drop towards {tp1} and a full run to {tp4}.",
            f"Risk is managed above {sl}; expecting a move to hit {tp1} initially, extending to {tp4}."
        ])

    summary = f"📊 {structure_txt} {action_txt} {rsi_txt} {levels_txt}"
    return summary

def send_crypto_signal(coin_name, direction, strategy, entry, leverage, tp1, tp2, tp3, tp4, sl, summary_text):
    signal_id = get_next_signal_id()
    trend_emoji = "📈" if direction.lower() == "long" else "📉"
    direction_text = "Long" if direction.lower() == "long" else "Short"
    clean_name = coin_name.replace("/", "")
    
    zone_low = round(entry * 0.9985, get_decimals(entry))
    zone_high = round(entry * 1.0015, get_decimals(entry))

    # Added HTML tags (<b>...</b>) for Bold text
    text = f"🔖 <b>Signal ID: {signal_id}</b>\n📩 #{clean_name} | {strategy}\n{trend_emoji} {direction_text} Entry Zone: {zone_low}-{zone_high}\n⚡ Leverage: {leverage}x\n\n🎯 Strategy Details:\nTarget 1: {tp1}\nTarget 2: {tp2}\nTarget 3: {tp3}\nTarget 4: {tp4}\n\n🔺 Stop-Loss: {sl}\n💡 After reaching the first target you can put the rest of the position to breakeven.\n\n<b>{summary_text}</b>"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Added "parse_mode": "HTML" to tell Telegram to read the <b> tags
    payload = {"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True, "parse_mode": "HTML"}
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
            lev = "10" # Changed Leverage to 10x
            
            # Changed TP1 to 1.20% (1.012)
            long_tps = (round(entry * 1.012, decimals), round(entry * 1.06, decimals), round(entry * 1.10, decimals), round(entry * 1.15, decimals))
            long_sl = round(entry * 0.96, decimals)
            
            # Changed TP1 to -1.20% (0.988)
            short_tps = (round(entry * 0.988, decimals), round(entry * 0.94, decimals), round(entry * 0.90, decimals), round(entry * 0.85, decimals))
            short_sl = round(entry * 1.04, decimals)

            # Changed time.sleep(2) to time.sleep(6) for Cornix integration
            if pullback_buy:
                summary = generate_summary("LONG", "Swing Pullback", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", f"Swing Pullback", entry, lev, *long_tps, long_sl, summary)
                time.sleep(6)
            elif pullback_sell:
                summary = generate_summary("SHORT", "Swing Pullback", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", f"Swing Pullback", entry, lev, *short_tps, short_sl, summary)
                time.sleep(6)

            elif vol_buy:
                summary = generate_summary("LONG", "Swing Volume", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", f"Swing Volume", entry, lev, *long_tps, long_sl, summary)
                time.sleep(6)
            elif vol_sell:
                summary = generate_summary("SHORT", "Swing Volume", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", f"Swing Volume", entry, lev, *short_tps, short_sl, summary)
                time.sleep(6)

            elif swing_buy:
                summary = generate_summary("LONG", "Swing Trend", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", f"Swing Trend", entry, lev, *long_tps, long_sl, summary)
                time.sleep(6)
            elif swing_sell:
                summary = generate_summary("SHORT", "Swing Trend", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", f"Swing Trend", entry, lev, *short_tps, short_sl, summary)
                time.sleep(6)
                
        except Exception as e:
            print(f"Error {symbol}: {e}")

if __name__ == "__main__":
    print("Custom Swing Bot started...")
    analyze_and_trade()