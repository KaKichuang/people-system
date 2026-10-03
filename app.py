import html

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

COLUMNS = ["姓名", "電話", "地址", "備註"]
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

st.set_page_config(
    page_title="客戶資料管理系統",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FAF8F5;
    }
    [data-testid="stSidebar"] {
        background-color: #F3EEE6;
    }
    html, body, [class*="css"] {
        font-size: 18px;
    }
    .stTextInput input {
        background-color: #FFFFFF;
        border: 1px solid #D1C7BD;
        border-radius: 8px;
        font-size: 20px;
        padding: 12px;
    }
    .card {
        background-color: #FFFFFF;
        border: 1px solid #E6E0D5;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(90, 74, 53, 0.06);
    }
    .card-title {
        font-size: 24px;
        font-weight: bold;
        color: #5A4A35;
        margin-bottom: 10px;
    }
    .card-text {
        font-size: 18px;
        color: #4A4A4A;
        margin-bottom: 6px;
    }
    .related {
        background-color: #F7F2EA;
        border-left: 4px solid #C8B79E;
        border-radius: 8px;
        padding: 10px 16px;
        margin: -6px 0 16px 0;
        font-size: 17px;
        color: #5A4A35;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #5A4A35;'>客戶資料查詢與管理系統</h1>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #E6E0D5;'>", unsafe_allow_html=True)


@st.cache_resource
def init_connection():
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
        client = gspread.authorize(creds)
        return client.open(st.secrets["sheet"]["sheet_name"]).sheet1
    except Exception:
        return None


def load_data(sheet) -> pd.DataFrame:
    try:
        df = pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        st.error(f"讀取 Google Sheets 資料失敗: {e}")
        df = pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS].fillna("").astype(str)


def esc(value) -> str:
    return html.escape(str(value))


def norm_address(value: str) -> str:
    return "".join(str(value).split())


def render_search(df: pd.DataFrame) -> None:
    # autocomplete="off"：不讓瀏覽器顯示搜尋歷史
    query = st.text_input(
        "🔍 搜尋（姓名、電話、地址、備註模糊查找）",
        placeholder="輸入關鍵字立即尋找...",
        autocomplete="off",
    ).strip().lower()
    if not query:
        st.info(f"目前共有 {len(df)} 筆客戶資料，請輸入關鍵字搜尋。")
        return

    mask = df.apply(lambda col: col.str.lower().str.contains(query, regex=False)).any(axis=1)
    result = df[mask]
    st.markdown(f"### 搜尋結果：找到 {len(result)} 筆符合資料")
    if result.empty:
        st.info("沒有找到符合的客戶資料。")
        return

    addr_key = df["地址"].map(norm_address)
    for idx, row in result.iterrows():
        st.markdown(f"""
        <div class="card">
            <div class="card-title">👤 {esc(row['姓名'])}</div>
            <div class="card-text"><b>📞 電話：</b>{esc(row['電話'])}</div>
            <div class="card-text"><b>📍 地址：</b>{esc(row['地址'])}</div>
            <div class="card-text"><b>📝 備註：</b>{esc(row['備註'])}</div>
        </div>
        """, unsafe_allow_html=True)

        key = addr_key[idx]
        if not key:
            continue
        others = df[(addr_key == key) & (df.index != idx)]
        if others.empty:
            continue
        lines = "".join(
            f"<div>・<b>{esc(o['姓名'])}</b>｜電話：{esc(o['電話'])}｜備註：{esc(o['備註'])}</div>"
            for _, o in others.iterrows()
        )
        st.markdown(
            f"<div class='related'>🏠 同地址其他關聯資料（{len(others)} 筆）{lines}</div>",
            unsafe_allow_html=True,
        )


def render_quick_add(sheet) -> None:
    st.subheader("➕ 快速新增客戶")
    with st.form("add_form", clear_on_submit=True):
        new_name = st.text_input("姓名 *", autocomplete="off")
        new_phone = st.text_input("電話", autocomplete="off")
        new_address = st.text_input("地址", autocomplete="off")
        new_remark = st.text_area("備註")
        if st.form_submit_button("確認新增至 Google Sheets", width="stretch"):
            if not new_name.strip():
                st.error("請至少填寫姓名。")
            else:
                sheet.append_row(
                    [new_name.strip(), new_phone.strip(), new_address.strip(), new_remark.strip()],
                    value_input_option="RAW",
                )
                st.success(f"已新增客戶：{new_name.strip()}")


def render_table_manager(sheet, df: pd.DataFrame) -> None:
    st.markdown("### 📊 完整資料表管理")
    st.caption("可直接修改儲存格、在最下方新增列、勾選列後按 Delete 刪除；完成後按「儲存變更」寫回 Google Sheets。")
    edited = st.data_editor(df, num_rows="dynamic", width="stretch", hide_index=True, key="table_editor")
    if st.button("💾 儲存變更", type="primary"):
        edited = edited[COLUMNS].fillna("").astype(str)
        edited = edited[edited["姓名"].str.strip() != ""]
        sheet.clear()
        sheet.update([COLUMNS] + edited.values.tolist(), value_input_option="RAW")
        st.success(f"已儲存，共 {len(edited)} 筆資料。")
        st.rerun()


sheet = init_connection()

if sheet is None:
    st.warning("⚠️ 尚未設定 Google Sheets 連線憑證，請於 Streamlit Secrets 設定 gcp_service_account 與 sheet.sheet_name。")
    st.stop()

with st.sidebar:
    st.markdown("<h2 style='color: #5A4A35;'>⚙️ 功能選單</h2>", unsafe_allow_html=True)
    mode = st.radio("選擇功能", ["客戶搜尋", "完整資料表管理"], label_visibility="collapsed")
    if st.button("🔄 重新整理資料", width="stretch"):
        st.rerun()
    st.markdown("---")
    render_quick_add(sheet)

data = load_data(sheet)
if mode == "完整資料表管理":
    render_table_manager(sheet, data)
else:
    render_search(data)
