import streamlit as st
import re
import json
import difflib

if 'isg_info' not in st.session_state:
    st.session_state['isg_info'] = {
        "isg_os_version": "",
        "machine_model": "",
        "serial_number": "",
        "m_network_info": "",
        "isg_command": ""
    }

# ページ設定
st.set_page_config(page_title="ISG 構成・整形ツール", layout="wide")
st.title("ISG 設定ファイル 解析・生成ツール")

# 🔗 バージョンデータ定義
VERSION_DATA = {
    "2.4.2.1": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1", "2.4.2.1"], "links": {}},
    "2.4.8": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1", "2.4.8"], "links": {}},
    "2.4.9": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1", "2.4.9"], "links": {}},
    "2.4.10.1": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1"], "links": {}},
    "2.5.1.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1"], "down": ["any hight version of 2.5"], "links": {}},
    "2.5.2.1": {"up": ["any2.x", "2.4.10.1", "2.5.2.1"], "down": ["any hight version of 2.5"], "links": {}},
    "2.5.3.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1", "2.5.3.1"], "down": ["any hight version of 2.5"], "links": {}},
    "2.5.4.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1", "2.5.4.1"], "down": ["any hight version of 2.5"], "links": {}},
    "2.5.5.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1", "2.5.4.2", "2.5.5.1"], "down": ["any hight version of 2.5"], "links": {}},
}

# 共通UI: ファイルアップロード
uploaded_file = st.file_uploader("ISG設定ファイルをアップロードしてください", type=["json", "txt"])

if uploaded_file:
    file_content = uploaded_file.getvalue().decode("utf-8")
    
    # バージョン抽出
    try:
        data_json = json.loads(file_content)
        version = data_json.get("versionNumber", "不明")
    except json.JSONDecodeError:
        match = re.search(r'"versionNumber":\s*"([\d\.]+)"', file_content)
        version = match.group(1) if match else "不明"

    if version != "不明":
        st.success(f"解析対象バージョン: {version}")
        
        # 判定と表示
        if version in VERSION_DATA:
            data = VERSION_DATA[version]
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Upgrade Path**\n" + "\n".join([f"- {v}" for v in data["up"]]))
            with col2:
                st.warning(f"**Downgrade Path**\n" + "\n".join([f"- {v}" for v in data["down"]]))
        else:
            st.error(f"バージョン {version} は特別ですので、古すぎるか新しすぎるかです。ファームウェアの入手方法について、お手数ですが、別途相談ください。")
              
        st.divider()
    else:
        st.error("ファイルから 'versionNumber' を特定できませんでした。")

# 🛠️ すべての表示枠に「コピー」と「ダウンロード」を確実に配置する共通コンポーネント関数
def show_custom_area(label, text_value, height, unique_key, download_filename):
    st.markdown(f"**{label}**")
    
    # ダウンロードボタン用のカラム配置
    title_col, dl_col = st.columns([3, 1.2])
    
    with title_col:
        st.caption("💡 枠内の右上に表示されるボタンからクリップボードにコピーできます。")
        
    with dl_col:
        is_disabled = "は見つかりませんでした" in text_value or "は検出されませんでした" in text_value or not text_value.strip() or "コマンドは生成されませんでした" in text_value
        st.download_button(
            label="📥 utf8TXTダウンロード",
            data=text_value.encode("utf-8"),
            file_name=download_filename,
            mime="text/plain",
            key=f"btn_dl_{unique_key}",
            disabled=is_disabled,
            use_container_width=True
        )

    st.code(text_value, language="text", line_numbers=False)

# タブ構造
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1ページ目：ISGファイルの読込・整形・コマンド作成", 
    "2ページ目：SGOSファイルの整形",
    "3ページ目：作成コマンドの一括出力",
    "4ページ目：ISG設定リストア",
    "5ページ目：SGOS情報確認"
])

# 一括出力用コマンドの格納辞書を初期化
all_generated_cmds_dict = {
    "snmp": "", "lag": "", "hm": "", "ntp": "", "proxy": "", "smtp": "",
    "tz": "", "lic": "", "mach": "", "nic": "", "acl": "", "other": "", "eventlog": ""
}

# ==========================================
# 1ページ目：ISGファイルの読込・整形・コマンド作成
# ==========================================
with tab1:
    st.header("ISGファイル情報の解析とコマンド自動生成")
    
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

        st.session_state.isg_os_version = isg_os_version
        st.session_state.machine_model = machine_model
        st.session_state.serial_number = serial_number
        
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
        
        st.subheader("✂️ ISG設定ファイルの整形およびACL抽出")
        col_acl1, col_acl2 = st.columns(2)
        with col_acl1:
            show_custom_area("全体整形結果（ACL抜き取り後の設定内容）", cleaned_text, 250, "cleaned", "isg_cleaned_config.txt")
        with col_acl2:
            show_custom_area("ACL抜き取り内容枠", acl_text, 250, "acl", "acl_extracted.txt")

        st.markdown("---")

        # 📄 Event Log設定の抽出
        st.subheader("📄 Event Log設定の抽出")

        eventlog_raw_text = ""
        eventlog_generated_commands = ""

        start_idx = -1
        end_idx = -1

        for idx, line in enumerate(base_cleaned_lines):
            line_strip = line.strip()

            if start_idx == -1 and line_strip.startswith("Log level:"):
                start_idx = idx

            if start_idx != -1 and line_strip.startswith("Syslog max size set to :"):
                end_idx = idx
                break

        if start_idx != -1 and end_idx != -1:
            eventlog_lines = base_cleaned_lines[start_idx:end_idx + 1]
            eventlog_raw_text = "\n".join(eventlog_lines)

            cmds = ["event-log"]

            # Log level
            level_match = re.search(r'Log level:\s*(\d+)', eventlog_raw_text, re.IGNORECASE)

            if level_match:
                level = level_match.group(1)
                cmds.append(f"event-log level {level}")

            # Remote syslog servers
            eventlog_lines_split = eventlog_raw_text.splitlines()

            for idx, line in enumerate(eventlog_lines_split):
                if "Remote syslog servers:" in line:
                    search_area = [line]

                    for offset in range(1, 5):
                        if idx + offset < len(eventlog_lines_split):
                            search_area.append(eventlog_lines_split[idx + offset])

                    for target_line in search_area:
                        m = re.search(r'(UDP|TLS)\s+([\d\.]+):(\d+)', target_line, re.IGNORECASE)

                        if m:
                            protocol = m.group(1).lower()
                            ip_addr = m.group(2)
                            port_num = m.group(3)

                            cmds.append(f"syslog add {protocol} host {ip_addr} port {port_num}")
                            break

                    break

            # Syslog max size
            size_match = re.search(r'Syslog max size set to\s*:\s*(\d+)M', eventlog_raw_text, re.IGNORECASE)

            if size_match:
                log_size = size_match.group(1)
                cmds.append(f"log-size {log_size}")

            cmds.append("exit")
            eventlog_generated_commands = "\n".join(cmds)
            all_generated_cmds_dict["eventlog"] = eventlog_generated_commands

        else:
            eventlog_raw_text = "Log level: ～ Syslog max size set to : の範囲が見つかりませんでした。"
            eventlog_generated_commands = "Event Logコマンドは生成されませんでした。"

        col_evt1, col_evt2 = st.columns(2)

        with col_evt1:
            show_custom_area("Event Log設定内容", eventlog_raw_text, 220, "eventlog_raw", "eventlog_source.txt")

        with col_evt2:
            show_custom_area("作成されたEvent Logコマンド", eventlog_generated_commands, 220, "eventlog_cmd", "eventlog_commands.txt")

        st.markdown("---")
        
        # 👤 ローカルユーザー設定の精査と表示
        st.subheader("👤 ローカルユーザー設定の抽出")
        
        local_user_list = []
        in_local_user_section = False
        
        pattern = re.compile(r'^edit user\s+(\S+)')
        
        for line in base_cleaned_lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith("reset-interval"):
                in_local_user_section = True
            
            if in_local_user_section and line_stripped.startswith("edit realm localRealm"):
                break
                
            if in_local_user_section:
                match = pattern.match(line_stripped)
                if match:
                    user_name = match.group(1)
                    if user_name != "admin" and user_name not in local_user_list:
                        local_user_list.append(user_name)
        
        local_user_text = "\n".join(local_user_list) if local_user_list else "対象ユーザーは検出されませんでした。"
        show_custom_area("抽出されたローカルユーザー (admin以外)", local_user_text, 150, "local_users", "local_users.txt")
        
        st.warning("⚠️ **警告: ローカルユーザーはadmin以外、以下の方法で手動で追加する必要があります。**")
        
        if local_user_list:
            for user in local_user_list:
                st.code(f"""localhost(config)# authentication
localhost(config-authentication)# edit local-user-list local-users
localhost(config-local-user-list-local-users)# create user
Value for 'name' (<string>): {user}
  ok
localhost(config-local-user-list-local-users)# edit user {user} add admin
localhost(config-local-user-list-local-users)# edit user {user} password""", language="text")
        else:
            st.info("追加設定が必要な対象ユーザーはいません。")

        st.markdown("---")
        
        # 🌐 ネットワーク情報設定の抽出
        st.subheader("🌐 ネットワーク情報設定")
        network_info_lines = []
        start_index = -1
        
        for i, line in enumerate(base_cleaned_lines):
            if line.strip().startswith("dns name-server"):
                start_index = i
                break
        
        if start_index != -1:
            network_info_lines = base_cleaned_lines[start_index : start_index + 12]
        
        if network_info_lines:
            network_info_text = "\n".join(network_info_lines)
            show_custom_area("DNS/ネットワーク設定 (12行)", network_info_text, 250, "network_info", "network_info.txt")
            st.session_state.m_network_info = network_info_text
        else:
            st.info("ネットワーク情報（dns name-serverから始まる設定）は見つかりませんでした。")

        st.markdown("---")

# ==========================================
# 2ページ目：SGOSファイルの整形
# ==========================================
with tab2:
    st.header("SGOS設定ファイルの整形・依存関係補完")
    
    uploaded_sgos = st.file_uploader("SGOS設定ファイルを読み込んでください", type=["txt", "cfg"], key="sgos_upload")
    
    if uploaded_sgos is not None:
        sgos_data = uploaded_sgos.getvalue().decode("utf-8")
        
        sgos_version = "未検出"
        sgos_serial = "未検出"
        
        v_match = re.search(r'!-\s*Version:\s*(.*?)(?=\n|$)', sgos_data)
        s_match = re.search(r'!-\s*Serial number:\s*(\d+)', sgos_data)
        
        if v_match:
            sgos_version = v_match.group(1).replace("SGOS ", "").replace(" SWG Edition", "").strip()
        if s_match:
            sgos_serial = s_match.group(1).strip()
            
        st.subheader("📋 SGOS機器基本情報")
        st.text(f"SGOSのバージョン:{sgos_version}\nシリアル番号:{sgos_serial}")
        st.markdown("---")
        
        status_report = {
            "edit format cifs ;mode": {"found": False, "insert": 'create format "cifs"'},
            "edit format mapi ;mode": {"found": False, "insert": 'create format "mapi"'},
            "edit log cifs ;mode": {"found": False, "insert": 'create log "cifs"'},
            "edit log mapi ;mode": {"found": False, "insert": 'create log "mapi"'}
        }
        
        sgos_lines = sgos_data.splitlines()
        edited_sgos_lines = []
        
        for s_line in sgos_lines:
            matched = False
            for target_str, info in status_report.items():
                if target_str in s_line:
                    info["found"] = True
                    edited_sgos_lines.append(info["insert"])
                    edited_sgos_lines.append(s_line)
                    matched = True
                    break
            if not matched:
                edited_sgos_lines.append(s_line)
                
        edited_sgos_text = "\n".join(edited_sgos_lines)
        
        show_custom_area("整形・コマンド補完後の設定内容", edited_sgos_text, 400, "sgos_edited", "sgos_configured.txt")
        
        st.markdown("---")
        st.subheader("📊 依存関係コマンドの挿入処理結果レポート")
        
        for target_str, info in status_report.items():
            if info["found"]:
                st.write(f"✅️ **「{target_str}」** が見つかったため、直前に **「{info['insert']}」** の挿入を実行しました。")
            else:
                st.write(f"❌ **「{target_str}」** は見つからなかったので、**「{info['insert']}」** の挿入を実行しませんでした。")

# ==========================================
# 3ページ目：作成コマンドの一括出力
# ==========================================
with tab3:
    st.header("📋 作成されたコマンドの一括出力")
    st.markdown("1ページ目で自動生成された各コマンドを結合して表示します。")
     
    combined_ordered_list = []
    order_keys = ["smtp", "snmp", "lag", "hm", "ntp", "proxy", "tz", "lic", "mach", "acl", "other", "nic", "eventlog"]
    
    for key in order_keys:
        cmd_content = all_generated_cmds_dict.get(key, "").strip()
        
        if cmd_content and "コマンドは生成されませんでした" not in cmd_content and "見つかりませんでした" not in cmd_content and "追加コマンドは不要です" not in cmd_content:
            combined_ordered_list.append(cmd_content)
    
    all_commands_text = "\n\n".join(combined_ordered_list)
    
    if all_commands_text and not all_commands_text.strip().startswith("conf"):
        all_commands_text = "conf\n\n" + all_commands_text

    st.session_state.isg_command = all_commands_text
    
    if all_commands_text:
        show_custom_area("すべての作成済みコマンド一括表示", all_commands_text, 600, "all_cmds", "all_commands.txt")
    else:
        st.warning("表示するコマンドがありません。")

# ==========================================
# 4ページ目：ISG設定リストア
# ==========================================
with tab4:
    st.header("📋 ISG設定をリストアする手順")
    
    st.markdown("### 準備作業")
    st.write("■二本の電源ケーブルを接続します。")
    st.write("■シリアルコンソールに接続します。")
    
    st.markdown("---")
    st.subheader("フェーズ一：ISGの設定を行う")
    
    os_ver = st.session_state.get('isg_os_version', '未検出')
    model = st.session_state.get('machine_model', '未検出')
    serial = st.session_state.get('serial_number', '未検出')
    
    st.code(f"お客様から提供されたファイルから特定したISGOS情報\nバージョン: {os_ver}\nマシンモデル: {model}\nシリアル番号: {serial}")
    
    st.write("リストア手順に従い、ISGを設定してください。")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        file_cust = st.file_uploader("顧客提供ISG設定ファイル", type=["txt", "conf"], key="cust_diff")
    with col_u2:
        file_rest = st.file_uploader("リストア後ISG設定ファイル", type=["txt", "conf"], key="rest_diff")

    def clean_config(text):
        pattern = re.compile(r'aaa authentication users user admin[\s\S]*?(?=agent enabled)', re.MULTILINE)
        return pattern.sub('', text).strip()

    if file_cust and file_rest:
        content_cust = clean_config(file_cust.getvalue().decode("utf-8"))
        content_rest = clean_config(file_rest.getvalue().decode("utf-8"))
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.subheader("顧客提供ISG (除去後)")
            st.code(content_cust[:500])
            
        with c2:
            st.subheader("リストア後ISG (除去後)")
            st.code(content_rest[:500])
            
        with c3:
            st.subheader("差異表示")
            diff = list(difflib.ndiff(content_cust.splitlines(), content_rest.splitlines()))
            diff_lines = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]
            
            if not diff_lines:
                st.success("内容は同じです。")
            else:
                st.code("\n".join(diff[:20]))
    else:
        st.info("比較のため、両方のファイルをアップロードしてください。")

# ==========================================
# 5ページ目：SGOS情報確認
# ==========================================
with tab5:
    st.header("🔍 SGOS 情報確認")

    st.subheader("📁 ファイルアップロード")
    c1, c2, c3 = st.columns(3)
    with c1:
        up_sys_cust = st.file_uploader("お客様提供: SG_sysinfo", key="sys_cust")
        up_conf_cust = st.file_uploader("お客様提供: SG_config", key="conf_cust")
    with c2:
        up_sys_pre = st.file_uploader("キッティング前: SG_sysinfo", key="sys_pre")
        up_ev_pre = st.file_uploader("キッティング前: SG_event", key="ev_pre")
    with c3:
        up_sys_post = st.file_uploader("キッティング後: SG_sysinfo", key="sys_post")
        up_conf_post = st.file_uploader("キッティング後: SG_config", key="conf_post")

    st.markdown("---")

    results = []

    if up_sys_pre:
        sys_p = up_sys_pre.getvalue().decode().splitlines()

        if up_sys_cust:
            sys_c = up_sys_cust.getvalue().decode().splitlines()
            
            def get_raw_lines(lines):
                info = {"serial": "", "ram": "", "cores": ""}
                for l in lines:
                    if "serial number is" in l.lower():
                        info["serial"] = l.strip()
                    if "RAM:" in l:
                        info["ram"] = l.strip()
                    if "Number of cores:" in l:
                        info["cores"] = l.strip()
                return info
            
            c_info, p_info = get_raw_lines(sys_c), get_raw_lines(sys_p)
            is_match = (c_info == p_info)
            results.append(is_match)
            st.subheader("✅ キッティング前の確認")
            st.markdown(f"ハードウェア情報判定: :{'green' if is_match else 'red'}[{'OK' if is_match else 'NG'}]")
            show_custom_area("詳細比較", f"お客様: {c_info}\n\nキッティング前: {p_info}", 150, "c1", "c1.txt")

    if up_ev_pre:
        st.subheader("✅ チェック項目: イベントログエラー確認")
        errs = ["read error has occurred", "arning, a write episoded", "PSU no input"]
        content = up_ev_pre.getvalue().decode()
        found = [e for e in errs if e in content]
        is_ok6 = (len(found) == 0)
        results.append(is_ok6)
        st.markdown(f"判定: :{'green' if is_ok6 else 'red'}[{'OK' if is_ok6 else 'NG'}]")
        show_custom_area("検出エラー", str(found) if found else "エラーなし", 100, "c6", "c6.txt")

    if len(results) > 0:
        st.markdown("---")
        if all(results):
            st.success("### ✅ 全体判定：OK")
        else:
            st.error("### ❌ 全体判定：NG")

    if up_conf_cust and up_conf_post:
        st.subheader("🔧 キッティング後のConfig比較")
        c_lines = set(up_conf_cust.getvalue().decode().splitlines())
        p_lines = set(up_conf_post.getvalue().decode().splitlines())
        diff = c_lines ^ p_lines
        if diff:
            st.error("不一致あり")
            show_custom_area("不一致箇所", "\n".join(list(diff)), 300, "diff", "diff.txt")
        else:
            st.success("一致しています")
