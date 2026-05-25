import json
import re
import streamlit as st
import streamlit.components.v1 as components

# ページ全体のレイアウト設定
st.set_page_config(page_title="ISG & SGOS 構成・整形ツール", layout="wide")

st.title("ISG & SGOS 設定ファイル 変換・整形ツール")

# 🛠️ すべての表示枠に「コピー」と「ダウンロード」を確実に配置する共通コンポーネント関数
def show_custom_area(label, text_value, height, unique_key, download_filename):
    """
    ヘッダー行に「📋 コピー」と「📥 ダウンロード」のボタンを横並びで配置し、
    その直下にテキストエリアを表示する関数
    """
    # 1行の中にタイトル、コピーボタン、ダウンロードボタンを配置
    title_col, copy_col, dl_col = st.columns([2, 1, 1.2])
    
    with title_col:
        st.markdown(f"**{label}**")
        
    with copy_col:
        # コピー用のStreamlit標準ボタン
        if st.button(f"📋 コピーする", key=f"btn_copy_{unique_key}", use_container_width=True):
            escaped_text = json.dumps(text_value)
            js_code = f"""
            <script>
                var text = {escaped_text};
                navigator.clipboard.writeText(text).then(function() {{
                    parent.postMessage({{type: 'copy_success', key: '{unique_key}'}}, '*');
                }}).catch(function(err) {{
                    var textArea = document.createElement("textarea");
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {{
                        document.execCommand('copy');
                    }} catch (e) {{
                        alert('コピーに失敗しました');
                    }}
                    document.body.removeChild(textArea);
                }});
            </script>
            """
            components.html(js_code, height=0, width=0)
            st.toast("✅ クリップボードにコピーしました！", icon="📝")

    with dl_col:
        # ダウンロード用のStreamlit標準ボタン
        # 特定の枠で中身が空、あるいは未検出の警告文の場合はダウンロード不可にする制御
        is_disabled = "は見つかりませんでした" in text_value or "は検出されませんでした" in text_value or not text_value.strip()
        st.download_button(
            label="📥 utf8TXTダウンロード",
            data=text_value.encode("utf-8"),
            file_name=download_filename,
            mime="text/plain",
            key=f"btn_dl_{unique_key}",
            disabled=is_disabled,
            use_container_width=True
        )

    # メインのテキストエリア表示枠 (上のカスタムヘッダーと重複させないようラベルは非表示)
    st.text_area(label, text_value, height=height, key=f"area_{unique_key}", label_visibility="collapsed")


# タブ構造
tab1, tab2 = st.tabs(["1ページ目：ISGファイルの読込・整形・コマンド作成", "2ページ目：SGOSファイルの整形"])

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
        
        snmp_section_text = ""
        if "agent enabled" in string_data:
            snmp_range_match = re.search(r'(agent enabled.*?)(?=ntp)', string_data, re.DOTALL | re.IGNORECASE)
            if snmp_range_match:
                snmp_section_text = "snmp\n " + snmp_range_match.group(1).strip()
            else:
                snmp_range_match_eof = re.search(r'(agent enabled.*)', string_data, re.DOTALL | re.IGNORECASE)
                if snmp_range_match_eof:
                    snmp_section_text = "snmp\n " + snmp_range_match_eof.group(1).strip()
        
        if snmp_section_text:
            snmp_lines = snmp_section_text.splitlines()
            
            agent_version = "v2c"
            communities = []
            parsed_targets = {}
            parsed_notifies = {}
            vacm_groups = []
            parsed_access = {}
            parsed_views = {}
            
            current_target = None
            current_notify = None
            current_vacm_group = None
            current_vacm_view = None
            
            for s_line in snmp_lines:
                s_line_stripped = s_line.strip()
                if not s_line_stripped:
                    continue
                
                if s_line_stripped.startswith("agent version"):
                    agent_version = s_line_stripped.replace("agent version", "").strip()
                elif s_line_stripped.startswith("community"):
                    last_community = s_line_stripped.replace("community", "").strip()
                elif s_line_stripped.startswith("sec-name") and 'last_community' in locals():
                    s_name = s_line_stripped.replace("sec-name", "").strip()
                    communities.append((last_community, s_name))
                elif s_line_stripped.startswith("target"):
                    current_target = s_line_stripped.replace("target", "").strip()
                    parsed_targets[current_target] = {"ip":"", "port":"162", "tag":current_target, "timeout":"1500", "retries":"3", "sec_name":""}
                elif current_target:
                    if s_line_stripped.startswith("ip"):
                        parsed_targets[current_target]["ip"] = s_line_stripped.replace("ip", "").strip()
                    elif s_line_stripped.startswith("udp-port"):
                        parsed_targets[current_target]["port"] = s_line_stripped.replace("udp-port", "").strip()
                    elif s_line_stripped.startswith("tag"):
                        parsed_targets[current_target]["tag"] = s_line_stripped.replace("tag", "").replace("[", "").replace("]", "").strip()
                    elif s_line_stripped.startswith("timeout"):
                        parsed_targets[current_target]["timeout"] = s_line_stripped.replace("timeout", "").strip()
                    elif s_line_stripped.startswith("retries"):
                        parsed_targets[current_target]["retries"] = s_line_stripped.replace("retries", "").strip()
                    elif "sec-name" in s_line_stripped:
                        s_part = s_line_stripped.split("sec-name")[-1].strip()
                        parsed_targets[current_target]["sec_name"] = s_part
                    elif s_line_stripped == "!":
                        current_target = None
                elif s_line_stripped.startswith("notify"):
                    current_notify = s_line_stripped.replace("notify", "").strip()
                    parsed_notifies[current_notify] = {"tag": current_notify, "type": "trap"}
                elif current_notify:
                    if s_line_stripped.startswith("tag"):
                        parsed_notifies[current_notify]["tag"] = s_line_stripped.replace("tag", "").strip()
                    elif s_line_stripped.startswith("type"):
                        parsed_notifies[current_notify]["type"] = s_line_stripped.replace("type", "").strip()
                    elif s_line_stripped == "!":
                        current_notify = None
                elif s_line_stripped.startswith("vacm group"):
                    current_vacm_group = s_line_stripped.replace("vacm group", "").strip()
                elif s_line_stripped.startswith("vacm view"):
                    current_vacm_view = s_line_stripped.replace("vacm view", "").strip()
                    parsed_views[current_vacm_view] = {"subtree": "", "type": "included"}
                elif current_vacm_group:
                    if s_line_stripped.startswith("member"):
                        last_vacm_member = s_line_stripped.replace("member", "").strip()
                    elif s_line_stripped.startswith("sec-model") and 'last_vacm_member' in locals():
                        v_model = s_line_stripped.replace("sec-model", "").replace("[", "").replace("]", "").strip()
                        vacm_groups.append((current_vacm_group, last_vacm_member, v_model))
                    elif s_line_stripped.startswith("access"):
                        acc_parts = s_line_stripped.split()
                        last_acc_model = acc_parts[1] if len(acc_parts) > 1 else "v2c"
                        last_acc_auth = acc_parts[2] if len(acc_parts) > 2 else "no-auth-no-priv"
                        parsed_access[current_vacm_group] = {"model": last_acc_model, "auth": last_acc_auth, "read": "", "notify": ""}
                    elif s_line_stripped.startswith("read-view"):
                        if current_vacm_group in parsed_access:
                            parsed_access[current_vacm_group]["read"] = s_line_stripped.replace("read-view", "").strip()
                    elif s_line_stripped.startswith("notify-view"):
                        if current_vacm_group in parsed_access:
                            parsed_access[current_vacm_group]["notify"] = s_line_stripped.replace("notify-view", "").strip()
                    elif s_line_stripped == "!" and not s_line.startswith(" "):
                        current_vacm_group = None
                elif current_vacm_view:
                    if s_line_stripped.startswith("subtree"):
                        parsed_views[current_vacm_view]["subtree"] = s_line_stripped.replace("subtree", "").strip()
                    elif s_line_stripped in ["included", "excluded"]:
                        parsed_views[current_vacm_view]["type"] = s_line_stripped
                    elif s_line_stripped == "!" and not s_line.startswith(" "):
                        current_vacm_view = None

            snmp_commands = ["conf", f"snmp agent version {agent_version}\n"]
            
            for comm_name, sec_name in communities:
                snmp_commands.append(f"snmp community {comm_name}")
                
                for t_name, t_info in parsed_targets.items():
                    if t_info["sec_name"] == sec_name or t_name.lower() in comm_name.lower() or comm_name.lower() in t_info["sec_name"].lower():
                        snmp_commands.append(
                            f"snmp target {t_name} ip {t_info['ip']} udp-port {t_info['port']} "
                            f"tag {t_info['tag']} timeout {t_info['timeout']} retries {t_info['retries']} "
                            f"{agent_version} sec-name {t_info['sec_name']}"
                        )
                        if t_name in parsed_notifies:
                            snmp_commands.append(f"snmp notify {t_name} tag {parsed_notifies[t_name]['tag']} type {parsed_notifies[t_name]['type']}")
                
                for j_name, member, s_model in vacm_groups:
                    if j_name.lower() == comm_name.lower() or member.lower() == sec_name.lower():
                        snmp_commands.append(f"snmp vacm group {j_name} member {member} sec-model {s_model}")
                        
                        if j_name in parsed_access:
                            acc = parsed_access[j_name]
                            r_view = acc["read"]
                            if r_view in parsed_views:
                                snmp_commands.append(f"snmp vacm view {r_view} subtree {parsed_views[r_view]['subtree']} {parsed_views[r_view]['type']}")
                            
                            snmp_commands.append(f"snmp vacm group {j_name} access {acc['model']} {acc['auth']} read-view {acc['read']} notify-view {acc['notify']}")
                
                snmp_commands.append("exit\nexit\n")
                
            snmp_generated_text = "\n".join(snmp_commands).replace("\n\n\n", "\n\n").strip()
        else:
            snmp_section_text = "ファイル内に「agent enabled」から始まるSNMP設定が見つかりませんでした。"
            snmp_generated_text = "SNMP設定がないため、コマンドは生成されませんでした。"

        col_snmp1, col_snmp2 = st.columns(2)
        with col_snmp1:
            show_custom_area("SNMP 設定読み込み枠", snmp_section_text, 350, "snmp_raw", "snmp_source.txt")
        with col_snmp2:
            show_custom_area("分析・再構築された SNMP コマンド枠", snmp_generated_text, 350, "snmp_gen", "snmp_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # LAGの設定読込とコマンド変換
        # --------------------------------------
        st.subheader("🔗 LAGの設定読込とコマンド変換")
        
        lag_raw_text = ""
        lag_commands = []
        
        lag_start_index = -1
        for idx, l in enumerate(base_cleaned_lines):
            if "lag view" in l.lower():
                lag_start_index = idx
                break
        
        if lag_start_index != -1:
            extracted_lag_lines = base_cleaned_lines[lag_start_index + 1 : lag_start_index + 12]
            lag_raw_text = "\n".join(extracted_lag_lines)
            
            for l_line in extracted_lag_lines:
                match = re.match(r'^(\d+)\s+([\d:, ]+)', l_line.strip())
                if match:
                    g_id = match.group(1)
                    interfaces = [i.strip() for i in match.group(2).split(",")]
                    for interface in interfaces:
                        if interface and interface != "-":
                            lag_commands.append(f"group id {g_id} add {interface}")
                            
            lag_generated_text = "\n".join(lag_commands) if lag_commands else "有効なLAG設定行が検出されませんでした。"
        else:
            lag_raw_text = "ファイル内に「# lag view」に該当するセクションが見つかりませんでした。"
            lag_generated_text = "LAGコマンドは生成されませんでした。"

        col_lag1, col_lag2 = st.columns(2)
        with col_lag1:
            show_custom_area("LAG view 設定内容枠 (ヘッダー下の11行を自動抽出)", lag_raw_text, 220, "lag_raw", "lag_source.txt")
        with col_lag2:
            show_custom_area("作成された LAG コマンド枠", lag_generated_text, 220, "lag_gen", "lag_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # Healthmonitorの読込と動的コマンド再構築
        # --------------------------------------
        st.subheader("❤️ Healthmonitorの設定読込とコマンド再構築")
        
        hm_raw_text = ""
        hm_commands = []
        
        metric_mapping = {
            "CPU Utilization": "cpu-util",
            "Current Sensors": "current-sensors",
            "Fan Sensors": "fan-sensors",
            "Memory Utilization": "memory-util",
            "Power Supplies": "power-supplies",
            "RAID raid1-1 Working Members": "raid-status-raid1-1",
            "Temperature Sensors": "temperature-sensors",
            "Voltage Sensors": "voltage-sensors"
        }
        
        hm_start_index = -1
        for idx, l in enumerate(base_cleaned_lines):
            cleaned_l = l.lower().replace("-", " ").replace("_", " ")
            if "health" in cleaned_l and "monitoring" in cleaned_l and "settings" in cleaned_l:
                hm_start_index = idx
                break
        
        if hm_start_index != -1:
            extracted_hm_lines = base_cleaned_lines[hm_start_index : hm_start_index + 26]
            hm_raw_text = "\n".join(extracted_hm_lines)
            
            for h_line in extracted_hm_lines:
                for m_name, cmd_id in metric_mapping.items():
                    if m_name in h_line:
                        if cmd_id == "cpu-util":
                            thresholds = re.findall(r'(\d+)\s*%', h_line)
                            if len(thresholds) >= 2:
                                if thresholds[0] != "85":
                                    hm_commands.append(f"health-monitoring metric cpu-util high-warning-threshold {thresholds[0]}")
                                if thresholds[1] != "95":
                                    hm_commands.append(f"health-monitoring metric cpu-util high-critical-threshold {thresholds[1]}")
                        
                        elif cmd_id == "memory-util":
                            thresholds = re.findall(r'(\d+)\s*%', h_line)
                            if len(thresholds) >= 2:
                                if thresholds[0] != "80":
                                    hm_commands.append(f"health-monitoring metric memory-util high-warning-threshold {thresholds[0]}")
                                if thresholds[1] != "90":
                                    hm_commands.append(f"health-monitoring metric memory-util high-critical-threshold {thresholds[1]}")
                        
                        if re.search(r'\bT\b', h_line):
                            hm_commands.append(f"health-monitoring metric {cmd_id} trap enable")
                        if re.search(r'\bM\b', h_line):
                            hm_commands.append(f"health-monitoring metric {cmd_id} email enable")
                                
            hm_generated_text = "\n".join(hm_commands) if hm_commands else "追加コマンドは不要です。"
        else:
            hm_raw_text = "ファイル内に「health-monitoring view settings」に該当するセクションが見つかりませんでした。"
            hm_generated_text = "Healthmonitorコマンドは生成されませんでした。"

        col_hm1, col_hm2 = st.columns(2)
        with col_hm1:
            show_custom_area("Healthmonitor 設定内容枠 (ヘッダーから25行を自動抽出)", hm_raw_text, 250, "hm_raw", "health_source.txt")
        with col_hm2:
            show_custom_area("再構築された Healthmonitor コマンド枠", hm_generated_text, 250, "hm_gen", "health_commands.txt")


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
