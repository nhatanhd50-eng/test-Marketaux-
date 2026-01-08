# app.py
import streamlit as st
import requests
import pandas as pd

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Phân Tích Tin Vàng (XAU)",
    page_icon="🥇",
    layout="wide"
)

st.title("🥇 Phân Tích Cảm Xúc Tin Tức Vàng (XAU/USD)")
st.markdown("Ứng dụng này sử dụng API **Marketaux** để lấy tin tức mới nhất về Vàng và phân tích cảm xúc thị trường.")

# --- NHẬP API KEY TỪ SECRETS ---
# Cách an toàn nhất để quản lý API Key
try:
    api_token = st.secrets["MARKETAUX_API_TOKEN"]
except KeyError:
    st.error("❌ Không tìm thấy MARKETAUX_API_TOKEN trong file .streamlit/secrets.toml")
    st.info("Hãy tạo file .streamlit/secrets.toml và thêm dòng: `MARKETAUX_API_TOKEN = 'key_cua_ban'`")
    st.stop()

# --- TÙY CHỌN INPUT ---
# Cho phép người dùng chọn symbol (XAU hoặc XAUUSD)
symbol_option = st.selectbox(
    "Chọn mã Vàng để phân tích:",
    ("XAU (Gold Spot)", "XAUUSD (Gold vs USD)")
)

symbol_map = {
    "XAU (Gold Spot)": "XAU",
    "XAUUSD (Gold vs USD)": "XAUUSD"
}
selected_symbol = symbol_map[symbol_option]

# Nút bấm để lấy dữ liệu
if st.button("🔍 Lấy Tin Tức & Phân Tích", type="primary"):
    with st.spinner("Đang tải dữ liệu từ Marketaux..."):
        # 1. Gọi API Marketaux
        base_url = "https://api.marketaux.com/v1/news/all"
        params = {
            "api_token": api_token,
            "symbols": selected_symbol,
            "filter_entities": "true",
            "language": "en",
            "limit": 10
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 2. Xử lý dữ liệu
            if data['meta']['found'] > 0:
                articles = data['data']
                formatted_data = []
                
                for article in articles:
                    # Tìm entity khớp
                    for entity in article.get('entities', []):
                        if entity['symbol'] == selected_symbol:
                            formatted_data.append({
                                'Tiêu đề': article['title'],
                                'Nguồn': article['source'],
                                'Ngày': article['published_at'][:10],
                                'Điểm cảm xúc': entity['sentiment_score'],
                                'Link': article['url']
                            })
                            break
                
                df = pd.DataFrame(formatted_data)
                
                # 3. Hiển thị kết quả
                st.success(f"✅ Tìm thấy {len(df)} bài viết cho {selected_symbol}")
                st.dataframe(df, use_container_width=True)
                
                # Hiển thị biểu đồ đơn giản
                if not df.empty:
                    st.subheader("Biểu đồ Cảm Xúc")
                    chart_data = pd.DataFrame({
                        'X Axis': range(len(df)),
                        'Sentiment': df['Điểm cảm xúc']
                    })
                    st.line_chart(chart_data, x='X Axis', y='Sentiment')
            else:
                st.warning("Không tìm thấy bài viết nào.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Lỗi kết nối: {e}")