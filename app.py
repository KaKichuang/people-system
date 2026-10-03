import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="客戶資料管理系統",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #FAF8F5;
    }
    .stTextInput > div > div > input {
        background-color: #FFFFFF;
        border: 1px solid #D1C7BD;
        border-radius: 8px;
        font-size: 18px;
        padding: 10px;
    }
    .card {
        background-color: #FFFFFF;
        border: 1px solid #E6E0D5;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .card-title {
        font-size: 22px;
        font-weight: bold;
        color: #5A4A35;
        margin-bottom: 10px;
    }
    .card-text {
        font-size: 16px;
        color: #4A4A4A;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #5A4A35;'>客戶資料查詢與管理系統</h1>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #E6E0D5;'>", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet_name = st.secrets["sheet"]["sheet_name"]
        sheet = client.open(sheet_name).sheet1
        return sheet
    except Exception as e:
        return None

sheet = init_connection()

if sheet is None:
    st.warning("⚠️ 尚未設定 Google Sheets 連線憑證，請於 Streamlit Secrets 設定。")
else:
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"讀取 Google Sheets 資料失敗: {e}")
        df = pd.DataFrame(columns=["姓名", "電話", "地址", "備註"])

    expected_cols = ["姓名", "電話", "地址", "備註"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input("🔍 搜尋框（支援姓名、電話、地址、備註模糊查找）", placeholder="輸入關鍵字立即尋找...")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 重新整理", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

    if search_query:
        query = search_query.strip().lower()
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(query)).any(axis=1)
        filtered_df = df[mask]
        
        st.markdown(f"### 搜尋結果：找到 {len(filtered_df)} 筆符合資料")
        if len(filtered_df) > 0:
            for idx, row in filtered_df.iterrows():
                name = str(row.get("姓名", ""))
                phone = str(row.get("電話", ""))
                address = str(row.get("地址", ""))
                remark = str(row.get("備註", ""))
                
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">👤 {name}</div>
                    <div class="card-text"><b>📞 電話：</b>{phone}</div>
                    <div class="card-text"><b>📍 地址：</b>{address}</div>
                    <div class="card-text"><b>📝 備註：</b>{remark}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if address and address.strip() != "":
                    same_address_df = df[df["地址"] == address]
                    if len(same_address_df) > 1:
                        with st.expander(f"🏠 查看同地址 ({address}) 的其他關聯資料 ({len(same_address_df)} 筆)"):
                            for _, s_row in same_address_df.iterrows():
                                st.markdown(f"- **{s_row.get('姓名')}** | 電話: {s_row.get('電話')} | 備註: {s_row.get('備註')}")
        else:
            st.info("沒有找到符合的客戶資料。")

    with st.sidebar:
        st.markdown("<h2>⚙️ 功能選單</h2>", unsafe_allow_html=True)
        st.markdown("---")
        action = st.radio("選擇操作", ["快速新增客戶", "完整資料表管理"])
        
        if action == "快速新增客戶":
            st.subheader("➕ 新增客戶資料")
            with st.form("add_form"):
                new_name = st.text_input("姓名 *")
                new_phone = st.text_input("電話")
                new_address = st.text_input("地址")
                new_remark = st.text_area("備註")
                submit = st.form_submit_button("確認新增至 Google Sheets")
                
                if submit:
                    if new_name:
                        sheet.append_row([new_name, new_phone, new_address, new_remark])
                        st.success("成功新增客戶！")
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("請至少填寫姓名。")
                        
        elif action == "完整資料表管理":
            st.subheader("📊 完整資料清單")
            st.dataframe(df, use_container_width=True)