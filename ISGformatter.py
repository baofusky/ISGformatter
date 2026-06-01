import json
import re
import streamlit as st

# ページ全体のレイアウト設定
st.set_page_config(page_title="ISG & SGOS 構成・整形ツール", layout="wide")

st.title("ISG & SGOS 設定ファイル 変換・整形ツール")

# 🛠️ すべての表示枠に「コピー」と「ダウンロード」を確実に配置する共通コンポーネント関数
def show_custom_area(label, text_value, height, unique_key, download_filename):
    st.markdown(f"**{label}**")
    
    # ダウンロードボタン用のカラム配置
    title_col, dl_col = st.columns([3, 1.2])
    
    with title_col:
        st.caption("💡 枠内の右上に表示されるボタンからクリップボードにコピーできます。")
        
    with dl_col:
        is_disabled = "は見つかりませんでした" in text_value or "は検出されませんでした" in text_value or not text_value.strip() or "コマンドは生成されませんでした" in text_value or "追加コマンドは不要です" in text_value
        st.download_button(
            label="📥 utf8TXTダウンロード",
            data=text_value.encode("utf-8"),
            file_name=download_filename,
            mime="text/plain",
            key=f"btn_dl_{unique_key}",
            disabled=is_disabled,
            use_container_width=True
        )

    # st.text_areaの代わりにst.codeを使用することで、確実にコピー機能を提供します。
    st.code(text_value, language="text", line_numbers=False)


# タブ構造
tab1, tab2, tab3 = st.tabs([
    "1ページ目：ISGファイルの読込・整形・コマンド作成", 
    "2ページ目：SGOSファイルの整形",
    "3ページ目：作成コマンドの一括出力"
])

# 一括出力用コマンドの格納辞書を初期化
all_generated_cmds_dict = {
    "snmp": "", "lag": "", "hm": "", "ntp": "", "proxy": "",
    "tz": "", "lic": "", "mach": "", "nic": "", "acl": "", "other": ""
}

# ==========================================
# 1ページ目：ISGファイルの読込・整形・コマンド作成
# ==========================================
with tab1:
    st.header("ISGファイル情報の解析とコマンド自動生成")
    
    uploaded_file = st.file_uploader("ISG設定ファイル（JSONまたはテキスト）をアップロードしてください", type=["json", "txt"], key="isg_upload")
    
    if uploaded_file is not None:
        string_data = uploaded_file.getvalue().decode("utf-8")
        
        isg_os_version = "未検出"
        machine_model = "未検出"
        serial_number = "未検出"
        
        try:
            json_data = json.loads(string_data)
            isg_os_version = json_data.get("versionNumber", "未検出")
            machine_model = json_data.get("model", "未検出")
            serial_number = json_data.get("serialNumber", "未検出")
        except json.JSONDecodeError:
            v_match = re.search(r'"versionNumber"\s*:\s*"([^"]+)"', string_data)
            m_match = re.search(r'"model"\s*:\s*"([^"]+)"', string_data)
            s_match = re.search(r'"serialNumber"\s*:\s*"([^"]+)"', string_data)
            if v_match: isg_os_version = v_match.group(1)
            if m_match: machine_model = m_match.group(1)
            if s_match: serial_number = s_match.group(1)

        st.subheader("📌 基本情報")
        st.text(f"ISGOS バージョン :{isg_os_version}\nマシンモデル:{machine_model}\nシリアル番号:{serial_number}")
        st.markdown("---")
        
        lines = string_data.splitlines()
        base_cleaned_lines = []
        
        for line in lines:
            if "--More--" in line:
                continue
            base_cleaned_lines.append(line.lstrip())
            
        acl_start_idx = -1
        acl_end_idx = -1
        last_rule_idx_in_block = -1
        
        i = 0
        while i < len(base_cleaned_lines):
            if i < len(base_cleaned_lines) - 1 and base_cleaned_lines[i].strip() == "acl" and base_cleaned_lines[i+1].strip() in ["enable", "disable"]:
                acl_start_idx = i
                j = i + 2
                while j < len(base_cleaned_lines):
                    if base_cleaned_lines[j].lower().startswith("rule"):
                        last_rule_idx_in_block = j
                    if last_rule_idx_in_block != -1 and base_cleaned_lines[j].strip() == "!":
                        acl_end_idx = j
                        break
                    j += 1
                break
            i += 1
            
        acl_lines = []
        remaining_lines = []
        
        if acl_start_idx != -1 and acl_end_idx != -1:
            acl_lines = base_cleaned_lines[acl_start_idx : acl_end_idx + 1]
            remaining_lines = base_cleaned_lines[:acl_start_idx] + base_cleaned_lines[acl_end_idx + 1:]
        else:
            remaining_lines = base_cleaned_lines
            
        cleaned_text = "\n".join(remaining_lines)
        acl_text = "\n".join(acl_lines) if acl_lines else "ACLルール（acl [enable/disable] および Rule行）は検出されませんでした。"
        
        st.subheader("✂️ IG設定ファイルの整形およびACL抽出")
        col_acl1, col_acl2 = st.columns(2)
        with col_acl1:
            show_custom_area("全体整形結果（ACL抜き取り後の設定内容）", cleaned_text, 250, "cleaned", "isg_cleaned_config.txt")
        with col_acl2:
            show_custom_area("ACL抜き取り内容枠", acl_text, 250, "acl", "acl_extracted.txt")

        st.markdown("---")
        
        # --------------------------------------
        # 3. SNMP設定の読込と動的コマンド再構築
        # --------------------------------------
        st.subheader("📡 SNMP設定の読込と動的コマンド生成")
        
        snmp_section_text
