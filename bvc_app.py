import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import time
import random
from datetime import datetime, timedelta, timezone

# Venezuela Timezone (UTC-4)
VET = timezone(timedelta(hours=-4))


# --- Page Configuration ---
st.set_page_config(
    page_title="Mercado de Valores",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        border-color: rgba(56, 189, 248, 0.5);
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.025em;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0.5rem 0;
    }

    /* Mobile Enhancements */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 1.5rem !important;
        }
        .metric-card {
            padding: 12px !important;
        }
        .mobile-hide {
            display: none !important;
        }
        .mobile-text-sm {
            font-size: 0.95rem !important;
        }
        .mobile-text-xs {
            font-size: 0.75rem !important;
        }
    }
    
    .metric-delta {
        font-size: 0.875rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    .delta-positive { color: #4ade80; }
    .delta-negative { color: #f87171; }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a; 
    }
    ::-webkit-scrollbar-thumb {
        background: #334155; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569; 
    }

    /* Plotly Chart Background */
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
    
    /* Sortable Table Headers */
    div[data-testid="column"] button {
        background: transparent !important;
        border: none !important;
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: bold !important;
        padding: 8px 4px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        transition: color 0.2s !important;
    }
    
    div[data-testid="column"] button:hover {
        color: #38bdf8 !important;
        background: rgba(56, 189, 248, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Fetching Functions ---

@st.cache_data(ttl=60)
def fetch_interbono_data():
    """
    Fetches data from the Interbono API proxy (Yahoo Finance wrapper).
    Returns a dictionary with market summary and a DataFrame of stocks.
    """
    url = "https://getmarketvalues-hdiyird7fq-uc.a.run.app"
    
    # List of symbols derived from Interbono's website
    symbols = [
        "ABC-A.CR", "BEX.CR", "BNC.CR", "BPV.CR", "BVE.CR", "BVCC.CR", "BVL.CR",
        "CCP-B.CR", "CCR.CR", "CGQ.CR", "CIE.CR", "CRM-A.CR", "DOM.CR",
        "EFE.CR", "ENV.CR", "FNC.CR", "FNV.CR", "FVIA.CR", "FVIB.CR",
        "GMC-B.CR", "GZL.CR", "ICP-B.CR", "INV.CR", "IVC-A.CR", "IVC-B.CR",
        "MPA.CR", "MVZ-A.CR", "MVZ-B.CR", "PCP-B.CR", "PER.CR", "PGR.CR", "PIV-B.CR",
        "PTN.CR", "RFM.CR", "RST.CR", "RST-B.CR", "SVS.CR", "TDV-D.CR",
        "TPG.CR", "VNA-B.CR"
    ]
    
    yahoo_urls = [f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}" for symbol in symbols]
    
    payload = {
        "urls": yahoo_urls
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        stocks_list = []
        
        if 'data' in data:
            results = data['data']
            for i, result in enumerate(results):
                try:
                    # Defensive parsing as per API structure
                    chart_result = result.get('chart', {}).get('result', [{}])[0]
                    meta = chart_result.get('meta', {})
                    
                    symbol = meta.get('symbol', symbols[i])
                    price = meta.get('regularMarketPrice', 0.0)
                    prev_close = meta.get('chartPreviousClose', meta.get('previousClose', price))
                    
                    # Extra fields for table
                    open_price = meta.get('regularMarketOpen', 0.0) # Might be missing
                    if open_price == 0.0:
                         open_price = prev_close # Fallback ensuring UI doesn't look broken
                    
                    day_high = meta.get('regularMarketDayHigh', 0.0)
                    day_low = meta.get('regularMarketDayLow', 0.0)

                    # Calculate change
                    change_amount = price - prev_close
                    change_percent = (change_amount / prev_close * 100) if prev_close else 0.0
                    
                    # Get name mapping
                    api_name = meta.get('shortName', meta.get('longName', symbol))
                    name = api_name.title()
                    
                    stocks_list.append({
                        "Symbol": symbol,
                        "Name": name,
                        "Price": price,
                        "Change": change_amount,
                        "ChangePercent": change_percent,
                        "Volume": meta.get('regularMarketVolume', 0),
                        "Open": open_price,
                        "DayHigh": day_high,
                        "DayLow": day_low
                    })
                except Exception as e:
                    print(f"Error parsing result for {symbols[i]}: {e}")
                    continue
                    
        df = pd.DataFrame(stocks_list)
        
        # Calculate a pseudo index or "Market Heat" based on average change
        avg_change = df['ChangePercent'].mean() if not df.empty else 0.0
        
        current_date = datetime.now(VET).strftime("%d/%m/%Y %H:%M:%S")
        
        return {
            "status": "online",
            "market_avg_change": avg_change,
            "stocks": df,
            "date": current_date
        }

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        # Fallback empty structure
        return {
            "status": "error",
            "market_avg_change": 0.0,
            "stocks": pd.DataFrame(),
            "date": datetime.now(VET).strftime("%d/%m/%Y")
        }

def fetch_historical_price(symbol, target_date):
    """
    Fetches the historical close price for a symbol on a specific date.
    target_date should be a datetime.date object.
    """
    url = "https://getmarketvalues-hdiyird7fq-uc.a.run.app"
    
    # Convert date to timestamp range (start and end of the day)
    dt = datetime.combine(target_date, datetime.min.time())
    p1 = int(dt.timestamp())
    p2 = p1 + 86400 # +24 hours
    
    yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={p1}&period2={p2}&interval=1d"
    
    payload = {"urls": [yahoo_url]}
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and data['data']:
            result = data['data'][0]
            chart_result = result.get('chart', {}).get('result', [{}])[0]
            
            # Try to get the close price from indicators
            indicators = chart_result.get('indicators', {}).get('quote', [{}])[0]
            closes = indicators.get('close', [])
            
            # Filter out None values and get the first valid close
            valid_closes = [c for c in closes if c is not None]
            if valid_closes:
                return valid_closes[0]
            
            # Fallback to adjclose if necessary
            adjcloses = chart_result.get('indicators', {}).get('adjclose', [{}])[0].get('adjclose', [])
            valid_adj = [c for c in adjcloses if c is not None]
            if valid_adj:
                return valid_adj[0]
                
        return None
    except Exception as e:
        print(f"Error fetching historical price for {symbol}: {e}")
        return None

def generate_history(symbol, start_price, trend=0):
    """Generates a random walk history for sparking lines (visual candy only)."""
    dates = pd.date_range(end=datetime.now(VET), periods=30)
    prices = [start_price]
    for _ in range(29):
        # Biased random walk based on trend
        change = random.uniform(-0.02, 0.02) + (trend * 0.01)
        prices.append(prices[-1] * (1 + change))
    
    return pd.DataFrame({"Date": dates, "Price": prices})

# --- Main Layout ---

# Auto-refresh logic (1 minute = 60 seconds)
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Mercado de Valores")
with col2:
    if st.button("🔄 Actualizar Ahora"):
        st.cache_data.clear()
        st.rerun()
    st.markdown(f"<div style='text-align: right; font-size: 0.8rem; color: #94a3b8;'>Última actualización: {datetime.now(VET).strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

# Fetch Data
data = fetch_interbono_data()

# --- Database Init ---
import database

@st.cache_resource
def init_db_wrapper():
    database.init_db()

init_db_wrapper()

# --- Tabs ---
tab_market, tab_portfolio = st.tabs(["🏛️ Mercado", "💼 Mi Portafolio"])

# --- TAB: MERCADO ---
with tab_market:
    if data['status'] == 'error' or data['stocks'].empty:
        st.warning("No se pudo conectar con el servicio de datos. Intente nuevamente.")
    else:
        # Market Summary Hero
        st.markdown("### 📊 Resumen del Mercado")
        ibc_col1, ibc_col2, ibc_col3 = st.columns([1, 2, 1])

        with ibc_col1:
            avg_change = data['market_avg_change']
            delta_color = "delta-positive" if avg_change >= 0 else "delta-negative"
            delta_icon = "▲" if avg_change >= 0 else "▼"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Tendencia Promedio</div>
                <div class="metric-value" style="font-size: 1.5rem;">{avg_change:.2f}%</div>
                <div class="metric-delta {delta_color}">
                    {delta_icon} Mercado General
                </div>
            </div>
            """, unsafe_allow_html=True)

        with ibc_col2:
            # Top Gainer
            top_gainer = data['stocks'].loc[data['stocks']['ChangePercent'].idxmax()] if not data['stocks'].empty else None
            if top_gainer is not None:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Mayor Alza 🚀</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div class="metric-value">{top_gainer['Symbol'].replace('.CR', '')}</div>
                            <div style="font-size: 0.9rem; color: #94a3b8;">{top_gainer['Name']}</div>
                        </div>
                        <div class="metric-value" style="color: #4ade80;">+{top_gainer['ChangePercent']:.2f}%</div>
                    </div>
                    <div style="color: #94a3b8;">Precio: {top_gainer['Price']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        with ibc_col3:
            # Market Volume (Sum of simple volumes for demo)
            total_vol = data['stocks']['Volume'].sum() if 'Volume' in data['stocks'].columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Volumen Total</div>
                <div class="metric-value" style="font-size: 1.5rem;">{total_vol:,.0f}</div>
                <div class="metric-delta delta-positive">
                    Acciones
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Market Overview (Stocks) Table
        st.markdown("### 🏢 Cotizaciones en Tiempo Real")
        
        # Initialize sort state
        if 'sort_column' not in st.session_state:
            st.session_state.sort_column = 'ChangePercent'
            st.session_state.sort_ascending = False
        
        df_display = data['stocks'].copy()
        
        # Table Header with Clickable Buttons
        # Use more responsive weights
        header_cols = st.columns([2, 1.2, 1, 1.2, 1, 1, 1.2])
        
        # Define sortable columns and their labels
        column_mappings = [
            ("Symbol", "ACCIÓN"),
            ("Price", "PRECIO"),
            ("Change", "CAMBIO"),
            ("ChangePercent", "% CAMBIO"),
            ("Open", "APERTURA"),
            ("Volume", "VOLUMEN"),
            (None, "RANGO")
        ]
        
        # We'll hide columns 5, 6, 7 on mobile
        mobile_hide_indices = [4, 5, 6] 
        
        for i, (col, (column_key, label)) in enumerate(zip(header_cols, column_mappings)):
            with col:
                is_mobile_hide = i in mobile_hide_indices
                class_str = "mobile-hide" if is_mobile_hide else ""
                
                if column_key:
                    arrow = ""
                    if st.session_state.sort_column == column_key:
                        arrow = " ↑" if st.session_state.sort_ascending else " ↓"
                    
                    st.markdown(f'<div class="{class_str}">', unsafe_allow_html=True)
                    if st.button(f"{label}{arrow}", key=f"sort_{column_key}", use_container_width=True):
                        if st.session_state.sort_column == column_key:
                            st.session_state.sort_ascending = not st.session_state.sort_ascending
                        else:
                            st.session_state.sort_column = column_key
                            st.session_state.sort_ascending = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='{class_str}' style='color: #94a3b8; font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; text-align: center;'>{label}</div>", unsafe_allow_html=True)
        
        # Apply sorting
        df_display = df_display.sort_values(
            by=st.session_state.sort_column,
            ascending=st.session_state.sort_ascending
        )
            
        # Table Rows
        for idx, row in df_display.iterrows():
            with st.container():
                # Define Colors
                text_color = "#4ade80" if row['Change'] >= 0 else "#f87171"
                bg_badge = "rgba(74, 222, 128, 0.1)" if row['Change'] >= 0 else "rgba(248, 113, 113, 0.1)"
                # arrow_icon = "↑" if row['Change'] >= 0 else "↓"
                
                # Layout with responsive weights
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1.2, 1, 1.2, 1, 1, 1.2])
                
                # Col 1: Symbol & Name
                with c1:
                    st.markdown(f"""
                    <div style="margin-bottom: 10px;">
                        <div style="font-weight: bold; font-size: 1.1rem; color: #f8fafc;">{row['Symbol'].replace('.CR', '')}</div>
                        <div style="font-size: 0.8rem; color: #94a3b8;">{row['Name']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Col 2: Price
                with c2:
                     st.markdown(f"""
                    <div>
                        <div style="font-weight: bold; font-size: 1rem;">Bs. {row['Price']:,.2f}</div>
                        <div style="font-size: 0.75rem; color: #64748b;">Actual</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Col 3: Change
                with c3:
                    st.markdown(f"""
                    <div class="mobile-hide">
                        <div style="font-weight: bold; font-size: 1rem; color: {text_color};">{'+' if row['Change'] > 0 else ''}{row['Change']:,.2f}</div>
                        <div style="font-size: 0.75rem; color: #64748b;">Hoy</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Col 4: % Change Badge
                with c4:
                     st.markdown(f"""
                    <div style="
                        background-color: {bg_badge};
                        color: {text_color};
                        padding: 4px 8px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 0.85rem;
                        display: inline-block;
                        text-align: center;
                    ">
                        {'+' if row['ChangePercent'] > 0 else ''}{row['ChangePercent']:.2f}%
                    </div>
                    """, unsafe_allow_html=True)
                
                # Col 5: Open
                with c5:
                     st.markdown(f"""
                    <div class="mobile-hide">
                         <div style="font-weight: 600; font-size: 0.95rem;">{row['Open']:,.2f}</div>
                         <div style="font-size: 0.75rem; color: #64748b;">Apertura</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Col 6: Volume
                with c6:
                     vol_str = f"{row['Volume']/1000:.1f}K" if row['Volume'] > 1000 else str(row['Volume'])
                     st.markdown(f"""
                    <div class="mobile-hide">
                         <div style="font-weight: 600; font-size: 0.95rem;">{vol_str}</div>
                         <div style="font-size: 0.75rem; color: #64748b;">Vol</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Col 7: Range
                with c7:
                     st.markdown(f"""
                    <div class="mobile-hide" style="font-size: 0.8rem;">
                         <div style="color: #4ade80;">↑ {row['DayHigh']:,.2f}</div>
                         <div style="color: #f87171;">↓ {row['DayLow']:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<div style='height: 1px; background: rgba(255,255,255,0.05); margin: 8px 0;'></div>", unsafe_allow_html=True)

# --- TAB: MI PORTAFOLIO ---
with tab_portfolio:
    st.markdown("### 💼 Gestión de Portafolio")
    
    # 1. Add Asset Section
    with st.expander("➕ Agregar Activo", expanded=False):
        # Interactive Add Asset
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        available_symbols = data['stocks']['Symbol'].tolist() if not data['stocks'].empty else []
        
        # Helper Dict
        symbol_to_name = dict(zip(data['stocks']['Symbol'], data['stocks']['Name'])) if not data['stocks'].empty else {}
        
        def format_func(symbol):
            s_clean = symbol.replace('.CR', '')
            s_name = symbol_to_name.get(symbol, '')
            if not s_name or s_name.upper() == s_clean.upper():
                return s_clean
            return f"{s_clean} ({s_name})"

        with c1:
            symbol_sel = st.selectbox("Acción", options=available_symbols, format_func=format_func, key="pf_symbol_select")

        with c2:
            # Default to today
            purchase_date = st.date_input("Fecha Compra", value=datetime.now(VET).date(), key="pf_date_input")

        # Logic to update price when symbol or date changes
        if 'last_pf_selection' not in st.session_state:
            st.session_state.last_pf_selection = (None, None)
        
        current_selection = (symbol_sel, purchase_date)
        
        if current_selection != st.session_state.last_pf_selection:
            with st.spinner("Consultando precio..."):
                # If it's today, we can use the current price
                if purchase_date == datetime.now(VET).date():
                     row = data['stocks'][data['stocks']['Symbol'] == symbol_sel]
                     price_to_set = float(row['Price'].values[0]) if not row.empty else 0.0
                else:
                    # Fetch historical
                    hist_price = fetch_historical_price(symbol_sel, purchase_date)
                    price_to_set = float(hist_price) if hist_price else 0.0
                
                st.session_state.pf_cost_input = price_to_set
                st.session_state.last_pf_selection = current_selection

        with c3:
            qty_input = st.number_input("Cantidad", min_value=1, value=100, key="pf_qty_input")
        with c4:
            cost_input = st.number_input("Costo (Bs)", min_value=0.0, step=0.01, format="%.2f", key="pf_cost_input")
            
        if st.button("Agregar al Portafolio"):
            try:
                database.add_holding(symbol_sel, qty_input, cost_input, purchase_date.isoformat())
                st.success("Portafolio actualizado")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # 2. Portfolio Summary
    holdings = database.get_holdings()

    if not holdings:
        st.info("Tu portafolio está vacío. Agrega acciones arriba para comenzar. (Ahora se guardan en Base de Datos)")
    else:
        # Calculate Logic
        portfolio_data = []
        total_value = 0.0
        total_cost = 0.0
        
        for item in holdings:
            # Get current market data - with proper error handling
            curr_price = item['avg_cost']  # Default fallback
            day_change_pct = 0.0
            
            # Only try to access market data if stocks data is available and not empty
            if data['status'] == 'online' and not data['stocks'].empty:
                try:
                    market_dat = data['stocks'][data['stocks']['Symbol'] == item['symbol']]
                    if not market_dat.empty:
                        curr_price = market_dat['Price'].values[0]
                        day_change_pct = market_dat['ChangePercent'].values[0]
                except (KeyError, IndexError) as e:
                    # Fallback to cost if any error occurs
                    pass
            
            market_val = curr_price * item['qty']
            cost_val = item['avg_cost'] * item['qty']
            gain_loss = market_val - cost_val
            gain_loss_pct = (gain_loss / cost_val * 100) if cost_val > 0 else 0
            
            total_value += market_val
            total_cost += cost_val
            
            portfolio_data.append({
                "id": item['id'], # For removal
                "Symbol": item['symbol'],
                "Cantidad": item['qty'],
                "Precio Mercado": curr_price,
                "Costo Prom.": item['avg_cost'],
                "Valor Total": market_val,
                "Ganancia/Pérdida": gain_loss,
                "G/P %": gain_loss_pct,
                "Cambio Diario %": day_change_pct,
                "purchase_date": item.get('purchase_date')
            })
            
        # Summary Metrics
        p_col1, p_col2, p_col3 = st.columns(3)
        total_gain = total_value - total_cost
        total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
        
        with p_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Valor Total Portafolio</div>
                <div class="metric-value">Bs {total_value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with p_col2:
            color = "delta-positive" if total_gain >= 0 else "delta-negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Ganancia/Pérdida Total</div>
                <div class="metric-value" style="font-size: 1.5rem;">Bs {total_gain:,.2f}</div>
                <div class="metric-delta {color}">
                    {total_gain_pct:.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Holdings Table
        st.markdown("#### 📜 Mis Activos")
        
        # Display as cards or table? Table is better for density
        # Collection for bulk delete
        items_to_delete = []
        
        # Display as cards or table? Table is better for density
        for p_item in portfolio_data:
            display_symbol = p_item['Symbol'].replace('.CR', '')
            
            # Layout: Card | Checkbox
            content_col, sel_col = st.columns([0.95, 0.05])
            
            with content_col:
                st.markdown(f"""
                <div class="portfolio-card" style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; font-size: 1.2rem;" class="mobile-text-sm">{display_symbol}</div>
                        <div style="font-size: 0.9rem; color: #ccc;" class="mobile-text-xs">{p_item['Cantidad']} acciones @ {p_item['Costo Prom.']:,.2f}</div>
                        <div style="font-size: 0.75rem; color: #64748b;" class="mobile-hide">Comprado el {datetime.fromisoformat(p_item['purchase_date']).strftime('%d/%m/%Y') if p_item['purchase_date'] else 'N/A'}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: bold; font-size: 1.2rem;" class="mobile-text-sm">{p_item['Valor Total']:,.2f}</div>
                        <div style="color: {'#4ade80' if p_item['Ganancia/Pérdida'] >= 0 else '#f87171'};" class="mobile-text-xs">
                            {'+' if p_item['Ganancia/Pérdida'] >= 0 else ''}{p_item['Ganancia/Pérdida']:,.2f} ({p_item['G/P %']:.2f}%)
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with sel_col:
                st.write("") # Spacer
                st.write("") 
                if st.checkbox("Eliminar", key=f"del_chk_{p_item['id']}", label_visibility="collapsed"):
                    items_to_delete.append(p_item['id'])

        if items_to_delete:
            # Create right-aligned container for delete button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"🗑️ Eliminar ({len(items_to_delete)}) Seleccionados", type="primary", use_container_width=True):
                    for del_id in items_to_delete:
                        database.delete_holding(del_id)
                    st.success("Activos eliminados correctamente.")
                    time.sleep(1)
                    st.rerun()

# Footer (outside tabs)
st.markdown("---")
with st.expander("🛠️ Estado del Sistema (Debug)"):
    mode = "PostgreSQL (Nube)" if database.DB_URL else "SQLite (Local)"
    st.write(f"**Modo de Conexión:** `{mode}`")
    st.write(f"**Ubicación/URL:** `{database.DB_NAME if not database.DB_URL else 'Oculta (Secrets)'}`")
    
    db_exists = True if database.DB_URL else os.path.exists(database.SQLITE_PATH)
    st.write(f"**Estado Conexión:** {'✅ Activa' if db_exists else '❌ Archivo no encontrado'}")
    
    if "db_error" in st.session_state:
        st.error(f"Error de Conexión: {st.session_state.db_error}")
        st.info("💡 Tip: Verifica que tu DATABASE_URL incluya '?sslmode=require' al final.")
    
    st.write(f"**Total Activos:** {len(database.get_holdings())}")
    
    if not database.DB_URL and os.path.exists(database.SQLITE_PATH):
        st.write(f"**Tamaño DB Local:** {os.path.getsize(database.SQLITE_PATH) / 1024:.2f} KB")

st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8rem;'>Aplicación de Seguimiento de Portafolio v2.0</div>", unsafe_allow_html=True)

# Auto-refresh mechanic (at the end to not block rendering)
# We use a placeholder to track time and rerun
refresh_placeholder = st.empty()

with refresh_placeholder:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
