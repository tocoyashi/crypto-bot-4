import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import ccxt
import pandas as pd
import ta
import requests
import time
import random
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
GIST_ID = os.environ.get("GIST_ID")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

TIMEFRAME = "4h"

SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "TRX/USDT", "AVAX/USDT", "LINK/USDT",
    "POL/USDT", "LTC/USDT", "UNI/USDT",
    "ATOM/USDT", "XLM/USDT", "NEAR/USDT", "APT/USDT", "SUI/USDT",
    "INJ/USDT", "ARB/USDT", "OP/USDT", "FIL/USDT", "AAVE/USDT",
    "PEPE/USDT", "FET/USDT"
]

def get_decimals(price):
    if price > 100: return 2
    elif price > 1: return 3
    elif price > 0.01: return 5
    else: return 8

def get_next_signal_id():
    if not GIST_ID or not GITHUB_TOKEN:
        print("Warning: GIST_ID or GITHUB_TOKEN not set, using local counter")
        return get_local_signal_id()
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            gist_data = response.json()
            content = gist_data['files']['signal_counter.txt']['content'].strip()
            current_id = int(content)
        else:
            current_id = 200
    except Exception as e:
        print(f"Error reading Gist: {e}")
        current_id = 200
    
    next_id = current_id + 1
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        data = {
            "files": {
                "signal_counter.txt": {
                    "content": str(next_id)
                }
            }
        }
        requests.patch(url, headers=headers, json=data)
    except Exception as e:
        print(f"Error updating Gist: {e}")
        
    return f"{next_id:03d}"

def get_local_signal_id():
    filename = "signal_counter.txt"
    try:
        with open(filename, "r") as file:
            current_id = int(file.read().strip())
    except (FileNotFoundError, ValueError):
        current_id = 200
    
    next_id = current_id + 1
    
    try:
        with open(filename, "w") as file:
            file.write(str(next_id))
    except Exception as e:
        print(f"Error saving signal ID: {e}")
        
    return f"{next_id:03d}"

def generate_chart(df, symbol, direction, entry, tp1, tp4, sl):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    ax.plot(df['timestamp'], df['close'], color='#2c3e50', linewidth=1.5, label='Price')
    ax.plot(df['timestamp'], df['ema_21'], color='#3498db', linewidth=1, label='EMA 21', alpha=0.8)
    ax.plot(df['timestamp'], df['ema_50'], color='#f39c12', linewidth=1, label='EMA 50', alpha=0.8)
    ax.plot(df['timestamp'], df['ema_200'], color='#e74c3c', linewidth=1, label='EMA 200', alpha=0.8)
    
    if direction == "LONG":
        ax.axhline(y=tp1, color='#27ae60', linestyle='--', linewidth=1, alpha=0.7, label=f'TP1: {tp1}')
        ax.axhline(y=tp4, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.9, label=f'TP4: {tp4}')
        ax.axhline(y=sl, color='#e74c3c', linestyle='--', linewidth=1.5, alpha=0.9, label=f'SL: {sl}')
        ax.axhline(y=entry, color='#9b59b6', linestyle='-', linewidth=1, alpha=0.7, label=f'Entry: {entry}')
    else:
        ax.axhline(y=tp1, color='#27ae60', linestyle='--', linewidth=1, alpha=0.7, label=f'TP1: {tp1}')
        ax.axhline(y=tp4, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.9, label=f'TP4: {tp4}')
        ax.axhline(y=sl, color='#e74c3c', linestyle='--', linewidth=1.5, alpha=0.9, label=f'SL: {sl}')
        ax.axhline(y=entry, color='#9b59b6', linestyle='-', linewidth=1, alpha=0.7, label=f'Entry: {entry}')
    
    ax.set_title(f'{symbol} - {direction} Signal | 4H Chart', fontsize=14, fontweight='bold', color='#2c3e50')
    ax.set_xlabel('Date', fontsize=10, color='#2c3e50')
    ax.set_ylabel('Price (USDT)', fontsize=10, color='#2c3e50')
    
    ax.tick_params(colors='#2c3e50')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.spines['top'].set_color('#bdc3c7')
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['right'].set_color('#bdc3c7')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45)
    
    ax.grid(True, alpha=0.2, color='#95a5a6', linestyle='-')
    ax.legend(loc='upper left', fontsize=8, facecolor='white', edgecolor='#bdc3c7')
    
    plt.tight_layout()
    
    # ✅ حفظ كـ BytesIO بدلاً من base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, facecolor='white', edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    
    return buf

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
                "A healthy pullback to dynamic support has been rejected, resuming the uptrend.",
                "Price dipped perfectly into the demand zone and bounced sharply.",
                "Buyers stepped in aggressively at the dynamic support, signaling continuation."
            ])
        else:
            action_txt = random.choice([
                "A temporary rise to dynamic resistance has been rejected, resuming the downtrend.",
                "Price rallied into the supply zone and was met with strong selling pressure.",
                "Sellers defended the dynamic resistance aggressively, indicating bearish continuation."
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
    else: 
        if direction == "LONG":
            action_txt = random.choice([
                "A major golden cross confirms a new bullish swing phase.",
                "The recent bullish crossover marks the start of a macro uptrend."
            ])
        else:
            action_txt = random.choice([
                "A major death cross confirms a new bearish swing phase.",
                "The recent bearish crossover marks the start of a macro downtrend."
            ])

    if direction == "LONG":
        if rsi_val < 60:
            rsi_txt = random.choice([
                f"RSI at {rsi_val} supports room to run before overbought conditions.",
                f"RSI sitting comfortably at {rsi_val}, leaving plenty of upside breathing room.",
                f"Momentum indicator reads {rsi_val}, confirming healthy buying strength."
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
                f"Momentum indicator reads {rsi_val}, confirming healthy selling strength."
            ])
        else:
            rsi_txt = random.choice([
                f"RSI is weak at {rsi_val}, confirming high selling pressure.",
                f"RSI shows extreme bearish power at {rsi_val}, riding the downward momentum."
            ])

    if direction == "LONG":
        levels_txt = random.choice([
            "Risk is managed safely below the invalidation level; looking for an initial push towards the first target with a full run to the final extension.",
            "Invalidation point is clearly defined; expecting a strong breakout towards the upper targets.",
            "Risk/Reward ratio is highly favorable here; expecting a steady climb to hit the projected levels."
        ])
    else:
        levels_txt = random.choice([
            "Risk is managed safely above the invalidation level; looking for an initial drop towards the first target with a full run to the final extension.",
            "Invalidation point is clearly defined; expecting a heavy breakdown towards the lower targets.",
            "Risk/Reward ratio is highly favorable here; expecting a steady decline to hit the projected levels."
        ])

    summary = f"{structure_txt} {action_txt} {rsi_txt} {levels_txt}"
    return summary

def send_crypto_signal(coin_name, direction, strategy, entry, leverage, tp1, tp2, tp3, tp4, sl, summary_text, chart_buf=None):
    signal_id = get_next_signal_id()
    direction_text = "LONG" if direction.lower() == "long" else "SHORT"
    clean_name = coin_name.replace("/", "")
    
    zone_low = round(entry * 0.9985, get_decimals(entry))
    zone_high = round(entry * 1.0015, get_decimals(entry))

    text = f"📌 SIGNAL ID: #{signal_id}\nCOIN: #{clean_name}\nLeverage: {leverage}\nDirection: {direction_text} | Type: {strategy}\n➖➖➖➖➖➖➖\nENTRY: {zone_low} - {zone_high}\nTARGETS: {tp1} - {tp2} - {tp3} - {tp4}\nSTOP LOSS: {sl}\n\n📊 {summary_text}\n➖➖➖➖➖➖➖\nCrypto Bullets: By Banana Bot®"

    # إرسال النص
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True}
    try:
        response = requests.post(url, json=payload)
        if response.json().get('ok'): 
            print(f"Signal {signal_id} sent for {coin_name} via {strategy}")
        else: 
            print(f"ERROR for {coin_name}: {response.json().get('description')}")
    except Exception as e: 
        print(f"Network error: {e}")
        return

    # ✅ إرسال الشارت كملف (binary)
    if chart_buf:
        try:
            chart_buf.seek(0)  # العودة لبداية الملف
            photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {
                'photo': ('chart.png', chart_buf, 'image/png')
            }
            data = {
                "chat_id": CHANNEL_ID,
                "caption": f"📈 {clean_name} 4H Chart Analysis"
            }
            photo_response = requests.post(photo_url, data=data, files=files)
            if photo_response.json().get('ok'):
                print(f"Chart sent for {coin_name}")
            else:
                print(f"Chart error: {photo_response.json().get('description')}")
        except Exception as e:
            print(f"Chart send error: {e}")

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

            pullback_buy = (df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1]) and \
                           (df['low'].iloc[-1] <= df['ema_21'].iloc[-1]) and \
                           (current_close > df['ema_21'].iloc[-1]) and \
                           (df['rsi'].iloc[-1] < 60)

            pullback_sell = (df['ema_50'].iloc[-1] < df['ema_200'].iloc[-1]) and \
                            (df['high'].iloc[-1] >= df['ema_21'].iloc[-1]) and \
                            (current_close < df['ema_21'].iloc[-1]) and \
                            (df['rsi'].iloc[-1] > 40)

            vol_buy = (df['volume'].iloc[-1] > df['vol_sma'].iloc[-1] * 2.5) and (current_close > current_open)
            vol_sell = (df['volume'].iloc[-1] > df['vol_sma'].iloc[-1] * 2.5) and (current_close < current_open)

            swing_buy = (df['ema_50'].iloc[-2] <= df['ema_200'].iloc[-2]) and (df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1])
            swing_sell = (df['ema_50'].iloc[-2] >= df['ema_200'].iloc[-2]) and (df['ema_50'].iloc[-1] < df['ema_200'].iloc[-1])

            entry = round(current_close, decimals)
            lev = "10x"
            
            long_tps = (round(entry * 1.012, decimals), round(entry * 1.03, decimals), round(entry * 1.06, decimals), round(entry * 1.12, decimals))
            long_sl = round(entry * 0.92, decimals)
            
            short_tps = (round(entry * 0.988, decimals), round(entry * 0.97, decimals), round(entry * 0.94, decimals), round(entry * 0.88, decimals))
            short_sl = round(entry * 1.08, decimals)

            chart = None

            if pullback_buy:
                chart = generate_chart(df, symbol, "LONG", entry, long_tps[0], long_tps[3], long_sl)
                summary = generate_summary("LONG", "Swing Pullback", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", "Swing Pullback", entry, lev, *long_tps, long_sl, summary, chart)
                time.sleep(6)
            elif pullback_sell:
                chart = generate_chart(df, symbol, "SHORT", entry, short_tps[0], short_tps[3], short_sl)
                summary = generate_summary("SHORT", "Swing Pullback", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", "Swing Pullback", entry, lev, *short_tps, short_sl, summary, chart)
                time.sleep(6)

            elif vol_buy:
                chart = generate_chart(df, symbol, "LONG", entry, long_tps[0], long_tps[3], long_sl)
                summary = generate_summary("LONG", "Swing Volume", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", "Swing Volume", entry, lev, *long_tps, long_sl, summary, chart)
                time.sleep(6)
            elif vol_sell:
                chart = generate_chart(df, symbol, "SHORT", entry, short_tps[0], short_tps[3], short_sl)
                summary = generate_summary("SHORT", "Swing Volume", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", "Swing Volume", entry, lev, *short_tps, short_sl, summary, chart)
                time.sleep(6)

            elif swing_buy:
                chart = generate_chart(df, symbol, "LONG", entry, long_tps[0], long_tps[3], long_sl)
                summary = generate_summary("LONG", "Swing Trend", df, long_tps[0], long_tps[3], long_sl)
                send_crypto_signal(symbol, "LONG", "Swing Trend", entry, lev, *long_tps, long_sl, summary, chart)
                time.sleep(6)
            elif swing_sell:
                chart = generate_chart(df, symbol, "SHORT", entry, short_tps[0], short_tps[3], short_sl)
                summary = generate_summary("SHORT", "Swing Trend", df, short_tps[0], short_tps[3], short_sl)
                send_crypto_signal(symbol, "SHORT", "Swing Trend", entry, lev, *short_tps, short_sl, summary, chart)
                time.sleep(6)
                
        except Exception as e:
            print(f"Error {symbol}: {e}")

if __name__ == "__main__":
    print("Custom Swing Bot started...")
    analyze_and_trade()
