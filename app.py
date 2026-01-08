# app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Phân Tích Tin Vàng (XAU)",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🥇 Phân Tích Cảm Xúc Tin Tức Vàng (XAU/USD)")
st.markdown(
    """
    Ứng dụng sử dụng API **Marketaux** để lấy tin tức mới nhất về Vàng và phân tích cảm xúc thị trường.
    Dữ liệu được lấy từ các nguồn tiếng Anh (US, UK, CA, AU).
    """
)

# --- SIDEBAR: CẤU HÌNH ---
st.sidebar.header("⚙️ Cài Đặt")

# Cho phép người dùng chọn symbol (XAU hoặc XAUUSD)
symbol_option = st.sidebar.selectbox(
    "Chọn mã Vàng để phân tích:",
    ("XAU (Gold Spot)", "XAUUSD (Gold vs USD)")
)

# Ánh xạ lựa chọn sang symbol API
symbol_map = {
    "XAU (Gold Spot)": "XAU",
    "XAUUSD (Gold vs USD)": "XAUUSD"
}
selected_symbol = symbol_map[symbol_option]

# Chọn số lượng bài viết muốn hiển thị
limit_news = st.sidebar.slider("Số lượng bài viết:", 5, 50, 10)

# Lựa chọn lọc cảm xúc
sentiment_filter = st.sidebar.radio(
    "Lọc theo cảm xúc:",
    ("Tất cả", "Chỉ Tích cực (>= 0)", "Chỉ Tiêu cực (< 0)")
)

# --- NHẬP API KEY TỪ SECRETS ---
try:
    api_token = st.secrets["MARKETAUX_API_TOKEN"]
except KeyError:
    st.error("❌ Lỗi: Không tìm thấy `MARKETAUX_API_TOKEN` trong file `.streamlit/secrets.toml`.")
    st.info("💡 Hãy tạo file `.streamlit/secrets.toml` và thêm dòng: `MARKETAUX_API_TOKEN = 'key_cua_ban'`")
    st.stop()

# --- CHỨ NĂNG CHÍNH ---
st.divider()
if st.button("🔍 Lấy Dữ Liệu Tin Tức", type="primary", use_container_width=True):
    # Hiển thị trạng thái đang tải
    with st.spinner(f"Đang kết nối với Marketaux để lấy tin tức cho {selected_symbol}..."):
        # 1. Cấu hình URL và Tham số
        base_url = "https://api.marketaux.com/v1/news/all"
        params = {
            "api_token": api_token,
            "symbols": selected_symbol,
            "filter_entities": "false",  # Đặt false để dễ tìm kiếm hơn
            # Không lọc theo ngôn ngữ 'en' để tránh bỏ sót bài viết tiếng Anh từ các quốc gia khác
            # Thay vào đó, lọc theo quốc gia có nguồn tin tiếng Anh
            "countries": "us,gb,ca,au", # Mỹ (us), Anh (gb), Canada (ca), Úc (au)
            "limit": limit_news
        }

        # Xử lý lọc cảm xúc
        if sentiment_filter == "Chỉ Tích cực (>= 0)":
            params["sentiment_gte"] = "0"
        elif sentiment_filter == "Chỉ Tiêu cực (< 0)":
            params["sentiment_lte"] = "-0.0001" # Dưới 0 là tiêu cực (dùng số nhỏ để bao gồm cả số âm)

        try:
            # 2. Gọi API
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 3. Xử lý dữ liệu trả về
            if data['meta']['found'] > 0:
                articles = data['data']
                formatted_data = []
                
                for article in articles:
                    # Lấy entity khớp với symbol đã chọn
                    target_entity = None
                    for entity in article.get('entities', []):
                        if entity['symbol'] == selected_symbol:
                            target_entity = entity
                            break
                    
                    if target_entity:
                        formatted_data.append({
                            'Tiêu đề': article['title'],
                            'Nguồn': article['source'],
                            'Ngày đăng': article['published_at'][:10], # YYYY-MM-DD
                            'Điểm cảm xúc': target_entity['sentiment_score'],
                            'Link bài viết': article['url'],
                            'Trích dẫn': target_entity.get('highlights', [{}])[0].get('highlight', '')[:100] + '...' if target_entity.get('highlights') else 'N/A'
                        })
                
                # Chuyển thành DataFrame
                df = pd.DataFrame(formatted_data)
                
                # 4. Hiển thị kết quả
                st.success(f"✅ Tải thành công {len(df)} bài viết mới nhất cho **{selected_symbol}**!")
                
                # Bảng dữ liệu chi tiết
                st.dataframe(df, use_container_width=True, height=400)
                
                # --- PHÂN TÍCH CẢM XÚC ---
                st.divider()
                st.subheader(f"📊 Thống kê Cảm Xúc - {selected_symbol}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_sentiment = df['Điểm cảm xúc'].mean()
                    delta_color = "normal" if -0.1 < avg_sentiment < 0.1 else "inverse"
                    st.metric(
                        label="Điểm TB Cảm Xúc",
                        value=f"{avg_sentiment:.3f}",
                        delta="Trung bình",
                        delta_color=delta_color
                    )
                
                with col2:
                    pos_count = len(df[df['Điểm cảm xúc'] > 0])
                    st.metric(label="Bài Tích cực", value=pos_count, delta="Cao hơn 0")
                
                with col3:
                    neg_count = len(df[df['Điểm cảm xúc'] < 0])
                    st.metric(label="Bài Tiêu cực", value=neg_count, delta="Thấp hơn 0")
                
                # Vẽ biểu đồ xu hướng cảm xúc
                st.subheader("Biểu đồ Xu Hướng Cảm Xúc")
                # Đảo ngược dataframe để vẽ từ cũ nhất -> mới nhất
                df_chart = df.iloc[::-1]
                
                fig = px.line(
                    df_chart, 
                    x='Ngày đăng', 
                    y='Điểm cảm xúc',
                    title=f"Biểu đồ Cảm Xúc Tin Tức {selected_symbol}",
                    markers=True,
                    template="plotly_white"
                )
                # Thêm đường trung tuyến
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                
                st.plotly_chart(fig, use_container_width=True)

                # Hiển thị danh sách link
                with st.expander("🔗 Xem Link Gốc"):
                    for index, row in df.iterrows():
                        st.markdown(f"[{row['Tiêu đề']}]({row['Link bài viết']})")

            else:
                st.warning("⚠️ Không tìm thấy bài viết nào theo điều kiện lọc của bạn.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Lỗi kết nối tới API Marketaux: {e}")
        except KeyError as e:
            st.error(f"❌ Lỗi xử lý dữ liệu: {e}")

# --- FOOTER ---
st.divider()
st.caption("Dữ liệu được cung cấp bởi Marketaux API. Ứng dụng được xây dựng bởi Streamlit.")
