import html

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

COLUMNS = ["姓名", "電話", "地址", "備註"]
PAGE_SIZE = 10
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
        font-size: 19px;
        -webkit-text-size-adjust: 100%;
    }
    /* 主內容區：限制最大寬度並加大左右留白，平板直式／橫式皆舒適 */
    [data-testid="stMainBlockContainer"], .block-container {
        max-width: 1280px;
        padding: 2rem 2rem 4rem 2rem;
    }
    label, [data-testid="stWidgetLabel"] p {
        font-size: 19px !important;
        font-weight: 600;
        color: #5A4A35;
    }

    /* ── 輸入框：加高、加大字，方便手指點選 ── */
    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF;
        border: 1px solid #D1C7BD;
        border-radius: 12px;
        font-size: 21px !important;
        padding: 14px 16px !important;
        min-height: 56px;
    }

    /* ── 按鈕：最小高度 56px（大於 iOS 建議的 44px 觸控區） ── */
    .stButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondaryFormSubmit"] {
        min-height: 56px;
        padding: 12px 24px;
        font-size: 20px !important;
        font-weight: 600;
        border-radius: 14px;
    }
    .stButton > button p, .stFormSubmitButton > button p {
        font-size: 20px !important;
    }

    /* ── 側邊欄選單：每個選項都是大觸控區 ── */
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 10px;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label {
        background: #FFFFFF;
        border: 1px solid #E0D6C8;
        border-radius: 14px;
        padding: 14px 16px;
        min-height: 56px;
        width: 100%;
        align-items: center;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label p {
        font-size: 20px !important;
    }

    /* ── 卡片網格：窄螢幕（iPad 直式）單欄，寬螢幕（iPad 橫式）雙欄 ── */
    .card-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 22px;
        margin-top: 8px;
    }
    @media (min-width: 1100px) {
        .card-grid { grid-template-columns: 1fr 1fr; }
    }
    .card {
        background-color: #FFFFFF;
        border: 1px solid #E6E0D5;
        border-radius: 18px;
        padding: 28px 30px;
        box-shadow: 0 3px 10px rgba(90, 74, 53, 0.07);
        display: flex;
        flex-direction: column;
        gap: 14px;
    }
    .card-title {
        font-size: 30px;
        font-weight: 700;
        color: #5A4A35;
        line-height: 1.3;
        padding-bottom: 12px;
        border-bottom: 1px solid #EFE8DC;
    }
    .card-row {
        display: flex;
        gap: 12px;
        font-size: 22px;
        line-height: 1.55;
        color: #3F3A33;
    }
    .card-label {
        flex: 0 0 auto;
        min-width: 4.2em;
        color: #8A7A63;
        font-weight: 600;
    }
    .card-value {
        flex: 1 1 auto;
        word-break: break-word;
    }
    .card-value a {
        color: #3F3A33;
        text-decoration: none;
        border-bottom: 1px dashed #C8B79E;
    }
    .related {
        background-color: #F7F2EA;
        border-left: 5px solid #C8B79E;
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 6px;
        font-size: 19px;
        line-height: 1.6;
        color: #5A4A35;
    }
    .related-title {
        font-weight: 700;
        margin-bottom: 8px;
    }
    .related-item {
        padding: 6px 0;
        border-top: 1px dashed #E0D6C8;
    }
    .related-item:first-of-type { border-top: none; }
    .result-head {
        font-size: 24px;
        font-weight: 700;
        color: #5A4A35;
        margin: 18px 0 6px 0;
    }
    .result-range {
        font-size: 19px;
        color: #8A7A63;
        margin: 0 0 10px 0;
    }

    /* ── 分頁列：上一頁｜頁碼選單｜下一頁，任何寬度都維持同一列 ── */
    .st-key-pager {
        margin-top: 22px;
        padding: 14px;
        background: #FFFFFF;
        border: 1px solid #E6E0D5;
        border-radius: 18px;
    }
    .st-key-pager [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 12px;
        align-items: center;
    }
    .st-key-pager [data-testid="stColumn"] {
        min-width: 0 !important;
        width: auto !important;
    }
    .st-key-pager button:disabled {
        opacity: 0.35;
    }
    .st-key-pager [data-baseweb="select"] > div {
        min-height: 56px;
        border-radius: 14px;
        font-size: 20px;
        font-weight: 600;
        justify-content: center;
    }

    /* ── 手機（640px 以下）：縮小留白與字體，標籤改在內容上方 ── */
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"], .block-container {
            padding: 1rem 0.9rem 3rem 0.9rem;
        }
        h1 { font-size: 26px !important; }
        .card { padding: 20px 18px; border-radius: 14px; gap: 12px; }
        .card-title { font-size: 24px; }
        .card-row { flex-direction: column; gap: 2px; font-size: 19px; }
        .card-label { min-width: 0; font-size: 16px; }
        .related { padding: 12px 14px; font-size: 17px; }
        .result-head { font-size: 21px; }
        .st-key-pager { padding: 10px; }
        .st-key-pager [data-testid="stHorizontalBlock"] { gap: 6px; }
        .st-key-pager button { padding: 10px 6px; }
        .st-key-pager button p, .st-key-pager [data-baseweb="select"] > div { font-size: 16px !important; }
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
        # numericise_ignore=["all"]：保留原字串，避免電話 0912… 被轉成數字而遺失開頭 0
        df = pd.DataFrame(sheet.get_all_records(numericise_ignore=["all"]))
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


def phone_html(phone: str) -> str:
    # 電話做成可點擊連結，平板／手機上點一下即可撥號
    digits = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
    return f"<a href='tel:{digits}'>{esc(phone)}</a>" if digits else esc(phone)


def card_html(row, others: pd.DataFrame) -> str:
    rows = [("📞 電話", phone_html(row["電話"])), ("📍 地址", esc(row["地址"]))]
    if row["備註"].strip():
        rows.append(("📝 備註", esc(row["備註"])))
    body = "".join(
        f"<div class='card-row'><span class='card-label'>{label}</span><span class='card-value'>{value or '—'}</span></div>"
        for label, value in rows
    )
    related = ""
    if not others.empty:
        items = "".join(
            f"<div class='related-item'><b>{esc(o['姓名'])}</b>　{phone_html(o['電話'])}"
            + (f"<br><span style='color:#8A7A63'>{esc(o['備註'])}</span>" if o["備註"].strip() else "")
            + "</div>"
            for _, o in others.iterrows()
        )
        related = f"<div class='related'><div class='related-title'>🏠 同地址其他關聯資料（{len(others)} 筆）</div>{items}</div>"
    return f"<div class='card'><div class='card-title'>👤 {esc(row['姓名'])}</div>{body}{related}</div>"


def render_search(df: pd.DataFrame) -> None:
    col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom")
    with col_input:
        # autocomplete="off"：不讓瀏覽器顯示搜尋歷史
        query = st.text_input(
            "🔍 搜尋（姓名、電話、地址、備註模糊查找）",
            placeholder="輸入關鍵字立即尋找...",
            autocomplete="off",
        ).strip().lower()
    with col_btn:
        # 點按鈕會讓輸入框失去焦點並送出，平板上不必找鍵盤的 Enter
        st.button("🔍 搜尋", width="stretch")

    if not query:
        st.info(f"目前共有 {len(df)} 筆客戶資料，請輸入關鍵字搜尋。")
        return

    mask = df.apply(lambda col: col.str.lower().str.contains(query, regex=False)).any(axis=1)
    result = df[mask]
    total = len(result)
    st.markdown(f"<div class='result-head'>搜尋結果：找到 {total} 筆符合資料</div>", unsafe_allow_html=True)
    if result.empty:
        st.info("沒有找到符合的客戶資料。")
        return

    # 換關鍵字時頁碼重設為第 1 頁；只記住「目前這一個」關鍵字用來比對，不保留任何搜尋歷史
    pages = (total - 1) // PAGE_SIZE + 1
    if st.session_state.get("pager_query") != query:
        st.session_state["pager_query"] = query
        st.session_state["page"] = 1
    st.session_state["page"] = min(max(st.session_state.get("page", 1), 1), pages)
    page = st.session_state["page"]
    start = (page - 1) * PAGE_SIZE
    page_rows = result.iloc[start:start + PAGE_SIZE]
    st.markdown(
        f"<div class='result-range'>共 {total} 筆，第 {start + 1}–{start + len(page_rows)} 筆</div>",
        unsafe_allow_html=True,
    )

    addr_key = df["地址"].map(norm_address)
    cards = []
    for idx, row in page_rows.iterrows():
        key = addr_key[idx]
        others = df[(addr_key == key) & (df.index != idx)] if key else df.iloc[0:0]
        cards.append(card_html(row, others))
    st.markdown(f"<div class='card-grid'>{''.join(cards)}</div>", unsafe_allow_html=True)

    if pages > 1:
        render_pager(pages)


def _shift_page(delta: int) -> None:
    st.session_state["page"] += delta


def render_pager(pages: int) -> None:
    page = st.session_state["page"]
    with st.container(key="pager"):
        col_prev, col_jump, col_next = st.columns([1, 1.3, 1])
        with col_prev:
            st.button("◀ 上一頁", key="page_prev", width="stretch",
                      disabled=page <= 1, on_click=_shift_page, args=(-1,))
        with col_jump:
            # 下拉選單綁定 session_state["page"]，可直接跳到任一頁
            st.selectbox("跳頁", options=list(range(1, pages + 1)), key="page",
                         format_func=lambda p: f"第 {p} / {pages} 頁", label_visibility="collapsed")
        with col_next:
            st.button("下一頁 ▶", key="page_next", width="stretch",
                      disabled=page >= pages, on_click=_shift_page, args=(1,))


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
    # row_height 加高，方便在平板上用手指點選儲存格
    edited = st.data_editor(
        df, num_rows="dynamic", width="stretch", hide_index=True, row_height=48, height=620, key="table_editor"
    )
    if st.button("💾 儲存變更", type="primary", width="stretch"):
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
