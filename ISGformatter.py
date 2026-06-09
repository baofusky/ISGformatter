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
    "2.4.2.1": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1", "2.4.2.1"], "links": {"2.4.2.1": "https://techdata-marketing.box.com/s/8o3ge7tqskhqaqkrvlwt7q89zm2hfqu7","2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v"}},
    "2.4.8": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1", "2.4.8"], "links": {"2.4.8": "https://techdata-marketing.box.com/s/eisbjvx8p20xxmso6wflybc712rp1rsj","2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v"}},
    "2.4.9": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1", "2.4.9"], "links": {"2.4.9": "https://techdata-marketing.box.com/s/gljr9bmis5mpsmygiqjfm8kaumk87pz7","2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v"}},
    "2.4.10.1": {"up": ["より低いバージョンから直接アップグレード可能"], "down": ["2.5.5.1", "2.5.4.2", "2.4.10.1"], "links": {"2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf"}},
    "2.5.1.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1"], "down": ["any hight version of 2.5"], "links": {"2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v"}},
    "2.5.2.1": {"up": ["any2.x", "2.4.10.1", "2.5.2.1"], "down": ["any hight version of 2.5"], "links": {"2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.2.1": "https://techdata-marketing.box.com/s/p7xcrfgi52qoexiqzeninyhbe9yeel76"}},
    "2.5.3.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1", "2.5.3.1"], "down": ["any hight version of 2.5"], "links": {"2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v", "2.5.3.1": "https://techdata-marketing.box.com/s/seqq1ml85qzidxj3em1sqzgyu4tc89dl"}},
    "2.5.4.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1", "2.5.4.1"], "down": ["any hight version of 2.5"], "links": {"2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v", "2.5.4.1": "https://techdata-marketing.box.com/s/wcm1rwou15pjdi3woqlhb0bmeshnv3dm"}},
    "2.5.5.1": {"up": ["any2.x", "2.4.10.1", "2.5.1.1", "2.5.4.2", "2.5.5.1"], "down": ["any hight version of 2.5"], "links": {"2.4.10.1": "https://techdata-marketing.box.com/s/gqxbn470yd8y7pnayy3lba872w1rxfgf", "2.5.1.1": "https://techdata-marketing.box.com/s/b9aielst2dzjy6a6zkafhns6r8r6257v", "2.5.4.2": "https://techdata-marketing.box.com/s/xz724fthzoh738fi6pxf0lk1w4s2tga0", "2.5.5.1": "https://techdata-marketing.box.com/s/fotdnvxwb3zc1j2xi6ss5c19wvyhovrf"}},
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
            
            st.write("#### 関連リンク (Upgrade Path対象)")
            for up_ver in data["up"]:
                if up_ver in data["links"]:
                    st.write(f"- **{up_ver}**: [ダウンロードリンク]({data['links'][up_ver]})")
               
            st.write("#### 関連リンク (downgrade Path対象)")
            for down_ver in data["down"]:
                if down_ver in data["links"]:
                    st.write(f"- **{down_ver}**: [ダウンロードリンク]({data['links'][down_ver]})")
        else:
            # 💡 バージョンが辞書にない場合の表示
            st.error(f"バージョン {version} は特別ですので、古すぎるか新しすぎるかです。ファームウェアの入手方法について、お手数ですが、別途相談してください。")
              
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
tab1, tab2, tab3, tab5, tab4 = st.tabs([
    "1ページ目：ISGファイルの読込・整形・コマンド作成", 
    "2ページ目：SGOSファイルの整形",
    "3ページ目：作成コマンドの一括出力",
    "4ページ目 ISG設定リストア"
    "5ページ目：SGOS情報確認",
])

# 一括出力用コマンドの格納辞書を初期化
all_generated_cmds_dict = {
    "snmp": "", "lag": "", "hm": "", "ntp": "", "proxy": "", "smtp": "",
    "tz": "", "lic": "", "mach": "", "nic": "", "acl": "", "other": ""
}

# ==========================================
# 1ページ目：ISGファイルの読込・整形・コマンド作成
# ==========================================
with tab1:
    st.header("ISGファイル情報の解析とコマンド自動生成")
    
    uploaded_file = uploaded_file
    
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
        
        st.subheader("✂️ IG設定ファイルの整形およびACL抽出")
        col_acl1, col_acl2 = st.columns(2)
        with col_acl1:
            show_custom_area("全体整形結果（ACL抜き取り後の設定内容）", cleaned_text, 250, "cleaned", "isg_cleaned_config.txt")
        with col_acl2:
            show_custom_area("ACL抜き取り内容枠", acl_text, 250, "acl", "acl_extracted.txt")

        st.markdown("---")

       
# --------------------------------------
        # 👤 ローカルユーザー設定の精査と表示
        # --------------------------------------
        st.subheader("👤 ローカルユーザー設定の抽出")
        
        local_user_list = []
        in_local_user_section = False
        
        # 正規表現パターン: "edit user " に続く最初の単語を抽出
        pattern = re.compile(r'^edit user\s+(\S+)')
        
        for line in base_cleaned_lines:
            line_stripped = line.strip()
            
            # 開始条件: reset-interval で始まる行
            if line_stripped.startswith("reset-interval"):
                in_local_user_section = True
            
            # 終了条件: edit realm localRealm に到達した時点（含む直前まで）
            if in_local_user_section and line_stripped.startswith("edit realm localRealm"):
                break
                
            if in_local_user_section:
                # パターンにマッチするか確認
                match = pattern.match(line_stripped)
                if match:
                    user_name = match.group(1)
                    # admin 以外のユーザー名かつ、リストになければ追加
                    if user_name != "admin" and user_name not in local_user_list:
                        local_user_list.append(user_name)
        
        # 抽出結果の表示
        local_user_text = "\n".join(local_user_list) if local_user_list else "対象ユーザーは検出されませんでした。"
        show_custom_area("抽出されたローカルユーザー (admin以外)", local_user_text, 150, "local_users", "local_users.txt")
        
        # 警告文
        st.warning("⚠️ **警告: ローカルユーザーはadmin以外、以下の方法で手動で追加する必要があります。**")
        
        if local_user_list:
            # 抽出された全ユーザー分をまとめて警告文としてループ出力
            for user in local_user_list:
                st.code(f"""
localhost(config)# authentication
localhost(config-authentication)# edit local-user-list local-users
localhost(config-local-user-list-local-users)# create user
Value for 'name' (<string>): {user}
  ok
localhost(config-local-user-list-local-users)# edit user {user} add admin
localhost(config-local-user-list-local-users)# edit user {user} password
                """, language="text")
        else:
            st.info("追加設定が必要な対象ユーザーはいません。")

        st.markdown("---")
        
# --------------------------------------
        # 🌐 ネットワーク情報設定の抽出
        # --------------------------------------
        st.subheader("🌐 ネットワーク情報設定")
        network_info_lines = []
        start_index = -1
        
        # 1. "dns name-server" で始まる行を探す
        for i, line in enumerate(base_cleaned_lines):
            if line.strip().startswith("dns name-server"):
                start_index = i
                break
        
        # 2. 見つかった場合、そこから12行を取得
        if start_index != -1:
            network_info_lines = base_cleaned_lines[start_index : start_index + 12]
        
        # 抽出結果の表示
        if network_info_lines:
            network_info_text = "\n".join(network_info_lines)
            show_custom_area("DNS/ネットワーク設定 (12行)", network_info_text, 250, "network_info", "network_info.txt")
            st.session_state.m_network_info = network_info_text
        else:
            st.info("ネットワーク情報（dns name-serverから始まる設定）は見つかりませんでした。")

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
                elif s_line_stripped.startswith("target "):
                    current_target = re.sub(r'\s+', '', s_line_stripped.replace("target", "", 1))
                    parsed_targets[current_target] = {"ip":"", "port":"162", "tag":current_target, "timeout":"1500", "retries":"3", "sec_name":""}
                elif current_target:
                    if s_line_stripped.startswith("ip"):
                        parsed_targets[current_target]["ip"] = s_line_stripped.replace("ip", "").strip()
                    elif s_line_stripped.startswith("udp-port"):
                        parsed_targets[current_target]["port"] = s_line_stripped.replace("udp-port", "").strip()
                    elif s_line_stripped.startswith("tag"):
                        raw_tag = s_line_stripped.replace("tag", "").replace("[", "").replace("]", "")
                        parsed_targets[current_target]["tag"] = re.sub(r'\s+', '', raw_tag)
                    elif s_line_stripped.startswith("timeout"):
                        parsed_targets[current_target]["timeout"] = s_line_stripped.replace("timeout", "").strip()
                    elif s_line_stripped.startswith("retries"):
                        parsed_targets[current_target]["retries"] = s_line_stripped.replace("retries", "").strip()
                    elif "sec-name" in s_line_stripped:
                        s_part = s_line_stripped.split("sec-name")[-1].strip()
                        parsed_targets[current_target]["sec_name"] = s_part
                    elif s_line_stripped == "!":
                        current_target = None
                elif s_line_stripped.startswith("notify "):
                    current_notify = re.sub(r'\s+', '', s_line_stripped.replace("notify", "", 1))
                    parsed_notifies[current_notify] = {"tag": current_notify, "type": "trap"}
                elif current_notify:
                    if s_line_stripped.startswith("tag"):
                        raw_ntag = s_line_stripped.replace("tag", "")
                        parsed_notifies[current_notify]["tag"] = re.sub(r'\s+', '', raw_ntag)
                    elif s_line_stripped.startswith("type"):
                        parsed_notifies[current_notify]["type"] = s_line_stripped.replace("type", "").strip()
                    elif s_line_stripped == "!":
                        current_notify = None
                elif s_line_stripped.startswith("vacm group"):
                    current_vacm_group = s_line_stripped.replace("vacm group", "").strip()
                elif s_line_stripped.startswith("vacm view"):
                    current_vacm_view = s_line_stripped.replace("vacm view", "").strip()
                    parsed_views[current_vacm_view] = {"subtree": "1.3", "type": "included"}
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
                        parsed_views[current_vacm_view]["subtree"] = "1.3"
                    elif s_line_stripped in ["included", "excluded"]:
                        parsed_views[current_vacm_view]["type"] = s_line_stripped
                    elif s_line_stripped == "!" and not s_line.startswith(" "):
                        current_vacm_view = None

            snmp_commands = ["conf", f"snmp agent version {agent_version}\n"]
            
            for comm_name, sec_name in communities:
                snmp_commands.append(f"snmp community {comm_name}")
                
                for t_name, t_info in parsed_targets.items():
                    clean_t_name = re.sub(r'\s+', '', t_name)
                    clean_tag = re.sub(r'\s+', '', t_info['tag'])
                    
                    if t_info["sec_name"] == sec_name or clean_t_name.lower() in comm_name.lower() or comm_name.lower() in t_info["sec_name"].lower():
                        snmp_commands.append(
                            f"snmp target {clean_t_name} ip {t_info['ip']} udp-port {t_info['port']} "
                            f"tag {clean_tag} timeout {t_info['timeout']} retries {t_info['retries']} "
                            f"{agent_version} sec-name {t_info['sec_name']}"
                        )
                        if clean_t_name in parsed_notifies:
                            clean_notif_tag = re.sub(r'\s+', '', parsed_notifies[clean_t_name]['tag'])
                            snmp_commands.append(f"snmp notify {clean_t_name} tag {clean_notif_tag} type {parsed_notifies[clean_t_name]['type']}")
                
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
            all_generated_cmds_dict["snmp"] = snmp_generated_text
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
        # 🛠️ LAGの設定読込とコマンド変換
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
            
            lag_commands.append("lag")
            has_valid_interface = False
            
            for l_line in extracted_lag_lines:
                match = re.match(r'^(\d+)\s+([\d:, ]+)', l_line.strip())
                if match:
                    g_id = match.group(1)
                    interfaces = [i.strip() for i in match.group(2).split(",")]
                    for interface in interfaces:
                        if interface and interface != "-" and not interface.isspace():
                            lag_commands.append(f"group id {g_id} add {interface}")
                            has_valid_interface = True
            
            if has_valid_interface and len(lag_commands) > 1:
                lag_commands.append("exit")
                lag_generated_text = "\n".join(lag_commands)
                all_generated_cmds_dict["lag"] = lag_generated_text
            else:
                lag_generated_text = "Interfaces列に有効なNIC情報が検出されなかったため、LAGコマンドは生成されませんでした。"
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
        # ❤️ Healthmonitorの読込と動的コマンド再構築
        # --------------------------------------
        st.subheader("❤️ Healthmonitorの設定読込とコマンド再構築")
        
        hm_raw_text = ""
        hm_commands = []
        
        hm_start_index = -1
        for idx, l in enumerate(base_cleaned_lines):
            cleaned_l = l.lower().replace("-", " ").replace("_", " ")
            if "health" in cleaned_l and "monitoring" in cleaned_l and "settings" in cleaned_l:
                hm_start_index = idx
                break
        
        if hm_start_index != -1:
            full_hm_lines = base_cleaned_lines[hm_start_index : hm_start_index + 40]
            
            start_target_idx = -1
            end_target_idx = -1
            
            for idx, line in enumerate(full_hm_lines):
                line_str = line.strip()
                if line_str.startswith("CPU Utilization"):
                    start_target_idx = idx
                if line_str.startswith("Voltage Sensors"):
                    end_target_idx = idx
                    break
            
            if start_target_idx != -1 and end_target_idx != -1:
                extracted_hm_lines = full_hm_lines[start_target_idx : end_target_idx + 1]
            else:
                extracted_hm_lines = full_hm_lines
            
            hm_raw_text = "\n".join(extracted_hm_lines)
            
            metric_mapping = {
                "CPU Utilization": "cpu-util",
                "Memory Utilization": "memory-util",
                "Voltage Sensors": "voltage-sensors",
                "Current Sensors": "current-sensors",
                "Fan Sensors": "fan-sensors",
                "Power Supplies": "power-supplies",
                "RAID raid1-1 Working Members": "raid-status-raid1-1",
                "Temperature Sensors": "temperature-sensors",
                "Appliance Certificate Validation Status": "certificate-validation"
            }
            
            for line_data in extracted_hm_lines:
                line_stripped = line_data.strip()
                if not line_stripped or "---" in line_stripped:
                    continue
                
                matched_cmd_id = None
                for keyword, cmd_id in metric_mapping.items():
                    if keyword in line_stripped:
                        matched_cmd_id = cmd_id
                        break
                
                if matched_cmd_id:
                    thresholds = re.findall(r'(\d+)\s*(?:%|days)', line_stripped)
                    
                    if matched_cmd_id == "cpu-util" and len(thresholds) >= 2:
                        if thresholds[0] != "85":
                            hm_commands.append(f"health-monitoring metric cpu-util high-warning-threshold {thresholds[0]}")
                        if thresholds[1] != "95":
                            hm_commands.append(f"health-monitoring metric cpu-util high-critical-threshold {thresholds[1]}")
                            
                    elif matched_cmd_id == "memory-util" and len(thresholds) >= 2:
                        if thresholds[0] != "80":
                            hm_commands.append(f"health-monitoring metric memory-util high-warning-threshold {thresholds[0]}")
                        if thresholds[1] != "90":
                            hm_commands.append(f"health-monitoring metric memory-util high-critical-threshold {thresholds[1]}")
                    
                    parts = line_stripped.split('|')
                    if len(parts) >= 2:
                        alerts_section = parts[-1].strip()
                        if "T" in alerts_section:
                            hm_commands.append(f"health-monitoring metric {matched_cmd_id} trap enable")
                        if "M" in alerts_section or "E" in alerts_section:
                            hm_commands.append(f"health-monitoring metric {matched_cmd_id} email enable")
                                
            if hm_commands:
                hm_generated_text = "\n".join(hm_commands)
                all_generated_cmds_dict["hm"] = hm_generated_text
            else:
                hm_generated_text = "追加コマンドは不要です。"
        else:
            hm_raw_text = "ファイル内に「health-monitoring view settings」に該当するセクションが見つかりませんでした。"
            hm_generated_text = "Healthmonitorコマンドは生成されませんでした。"

        col_hm1, col_hm2 = st.columns(2)
        with col_hm1:
            show_custom_area("Healthmonitor 設定内容枠 (指定範囲を自動抽出)", hm_raw_text, 250, "hm_raw", "health_source.txt")
        with col_hm2:
            show_custom_area("再構築された Healthmonitor コマンド枠", hm_generated_text, 250, "hm_gen", "health_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # 🕒 NTP設定の読込とコマンド自動作成
        # --------------------------------------
        st.subheader("🕒 NTP設定の読込とコマンド自動生成")
        
        ntp_raw_text = ""
        ntp_generated_commands = ""
        
        ntp_match = re.search(r'(!\s*\n\s*ntp\s*[\s\S]*?)\s*(?=\n\s*!\s*\n\s*acl\s*\n\s*enable|\n\s*acl\s*\n\s*enable)', string_data, re.IGNORECASE)
        
        if ntp_match:
            ntp_raw_text = ntp_match.group(1).strip()
            if not ntp_raw_text.endswith("!"):
                ntp_raw_text += "\n!"
                
            ntp_lines = ntp_raw_text.splitlines()
            server_lines = []
            has_enable = False
            has_disable = False
            
            for n_line in ntp_lines:
                n_line_stripped = n_line.strip()
                if n_line_stripped.startswith("server "):
                    server_lines.append(n_line_stripped)
                if n_line_stripped == "enable":
                    has_enable = True
                if n_line_stripped == "disable":
                    has_disable = True
            
            commands_list = ["ntp"]
            commands_list.extend(server_lines)
            
            if has_enable:
                commands_list.append("enable")
            elif has_disable:
                commands_list.append("disable")
                
            commands_list.append("exit")
            
            ntp_generated_commands = "\n".join(commands_list)
            all_generated_cmds_dict["ntp"] = ntp_generated_commands
        else:
            ntp_raw_text = "ファイル内に指定条件を満たす「NTP設定セクション（!\\nntp ～ acl\\nenable の直上）」が見つかりませんでした。"
            ntp_generated_commands = "NTP設定がないため、コマンドは生成されませんでした。"
            
        col_ntp1, col_ntp2 = st.columns(2)
        with col_ntp1:
            show_custom_area("NTP設定の内容の表示", ntp_raw_text, 220, "ntp_raw", "ntp_source.txt")
        with col_ntp2:
            show_custom_area("作成されたNTPコマンド", ntp_generated_commands, 220, "ntp_gen", "ntp_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # 🛡️ ACL設定内容表示とコマンド自動作成
        # --------------------------------------
        st.subheader("🛡️ ACL設定の精査と個別コマンド生成")
        
        # 1ページ目で作成した acl_start_idx と acl_end_idx を利用して取得
        if acl_start_idx != -1 and acl_end_idx != -1:
            acl_raw_section = "\n".join(base_cleaned_lines[acl_start_idx : acl_end_idx + 1])
            acl_sec_lines = acl_lines # 既に抽出済みの変数を利用
        else:
            acl_raw_section = "ACLルールは検出されませんでした。"
            acl_sec_lines = []

        acl_status = "enable"
        acl_rule_lines = []
        for a_line in acl_sec_lines:
            a_line_stripped = a_line.strip()
            if a_line_stripped.lower().startswith("rule"):
                acl_rule_lines.append(a_line_stripped)
            if a_line_stripped in ["enable", "disable"]:
                acl_status = a_line_stripped
        
        if acl_sec_lines:
            acl_cmd_list = ["acl", acl_status, "yes"] + acl_rule_lines + ["exit"]
            acl_generated_commands = "\n".join(acl_cmd_list)
        else:
            acl_generated_commands = "ACL設定がないため、コマンドは生成されませんでした。"
            
        col_new_acl1, col_new_acl2 = st.columns(2)
        with col_new_acl1:
            show_custom_area("ACL設定の内容の表示", acl_raw_section, 250, "acl_raw_detail", "acl_source_detail.txt")
        with col_new_acl2:
            show_custom_area("作成されたACLコマンド", acl_generated_commands, 250, "acl_gen_detail", "acl_commands_detail.txt")
            
        all_generated_cmds_dict["acl"] = acl_generated_commands

        st.markdown("---")

        # --------------------------------------
        # 🌐 プロキシ設定の精査と個別コマンド生成
        # --------------------------------------
        st.subheader("🌐 プロキシ設定の精査と個別コマンド生成")
        
        proxy_raw_section = ""
        proxy_generated_commands = ""
        
        # 取得ロジック：proxy-settings から username 行まで
        proxy_lines = []
        in_proxy = False
        for line in base_cleaned_lines:
            if line.startswith("proxy-settings"):
                in_proxy = True
            if in_proxy:
                proxy_lines.append(line)
                if line.startswith("username"):
                    break
        
        if proxy_lines:
            proxy_raw_section = "\n".join(proxy_lines)
            
            # コマンド生成ロジック
            proxy_cmd_list = ["proxy-settings"]
            for p_line in proxy_lines:
                p_line_stripped = p_line.strip()
                if p_line_stripped.lower().startswith("host ") or p_line_stripped.lower().startswith("port "):
                    proxy_cmd_list.append(p_line_stripped)
                elif p_line_stripped.lower().startswith("username"):
                    proxy_cmd_list.append(p_line_stripped)
                elif p_line_stripped in ["enable", "disable"]:
                    proxy_cmd_list.append(p_line_stripped)
            proxy_cmd_list.append("exit")
            
            proxy_generated_commands = "\n".join(proxy_cmd_list)
            all_generated_cmds_dict["proxy"] = proxy_generated_commands
            
            # 左右分割表示
            col_proxy1, col_proxy2 = st.columns(2)
            with col_proxy1:
                show_custom_area("プロキシ設定の内容 (proxy-settings〜username)", proxy_raw_section, 250, "proxy_raw", "proxy_source.txt")
            with col_proxy2:
                show_custom_area("作成されたプロキシコマンド", proxy_generated_commands, 250, "proxy_gen", "proxy_commands.txt")
                
            # 警告を枠外に表示
            st.warning("⚠️ 警告: パスワードは自動設定できませんため、手動で設定する必要がある")
            
        else:
            st.error("プロキシ設定（proxy-settings から username 行まで）が見つかりませんでした。")

        st.markdown("---")
        # --------------------------------------
        # 📧 SMTP設定の読込とコマンド自動作成（★不具合完全修正：destination行の欠落を完全に解決）
        # --------------------------------------
        st.subheader("📧 SMTP設定の精査と個別コマンド生成")
        
        smtp_raw_section = ""
        smtp_generated_commands = ""
        
        # ★ 修正ポイント：テキスト全体から「smtpで始まる最初の行」から「最後に登場するdestinationで始まる行」までを完全にカバー
        # [^\n]* で最後のdestination行全体を巻き込み、直後に続くインデントされた実データ行までを含めるため、最長一致で安全に抽出します。
        smtp_block_match = re.search(r'(smtp\b[\s\S]*?destination\b[^\n]*)', string_data, re.IGNORECASE)

        if smtp_block_match:
            # 確実を期すため、マッチした位置以降で destination-addresses 階層が閉じる（または次の ! や空行）まで行単位でスキャン
            start_pos = smtp_block_match.start()
            rem_text = string_data[start_pos:]
            rem_lines = rem_text.splitlines()
            
            smtp_block_lines = []
            capture = True
            found_dest_end = False
            
            for line in rem_lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # ブロックの終了条件：smtp設定から十分離れ、次のセクションの区切り（!）が来た場合
                if found_dest_end and (line_stripped == "!" or (not line.startswith(" ") and line_stripped and not line_lower.startswith("smtp") and not line_lower.startswith("gateway") and not line_lower.startswith("from-address") and not line_lower.startswith("destination"))):
                    break
                    
                smtp_block_lines.append(line)
                
                if line_lower.startswith("destination") or "destination" in line_lower:
                    found_dest_end = True # destination関係の記述が始まったフラグ

            # 抽出したブロックテキストを表示用に格納
            smtp_raw_section = "\n".join(smtp_block_lines)
            
            smtp_cmd_list = []
            has_destination_line = False
            dest_addresses = []
            
            for line in smtp_block_lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                if not line_stripped or line_stripped == "!":
                    continue
                
                # 共通設定行のコマンド化
                if line_lower.startswith("smtp"):
                    cleaned = re.sub(r'\s+', ' ', line_stripped).strip()
                    smtp_cmd_list.append(cleaned)
                    
                elif line_lower.startswith("gateway"):
                    cleaned = re.sub(r'\s+', ' ', line_stripped).strip()
                    smtp_cmd_list.append(cleaned)
                    
                elif line_lower.startswith("from-address"):
                    cleaned = re.sub(r'\s+', ' ', line_stripped).strip()
                    smtp_cmd_list.append(cleaned)
                    
                # destination行を発見した場合（インデント有無を問わず、本物の「destination 」で始まる行を抽出）
                elif line_lower.startswith("destination "):
                    has_destination_line = True
                    addr_val = line_stripped[12:].strip()
                    if addr_val and addr_val not in dest_addresses:
                        dest_addresses.append(addr_val)

            # ガード条件判定: destination行が存在していれば対応する全アドレスのコマンドを生成
            if has_destination_line and dest_addresses:
                for addr in dest_addresses:
                    smtp_cmd_list.append(f"destination-addresses destination {addr}")
                    smtp_cmd_list.append("exit")
                
            if smtp_cmd_list:
                # 修正ポイント：destination行の数に応じてexitの数を調整
                # 基本的なexit（smtp用、設定ブロック用）の2つに加え、
                # destinationが存在する場合は、その数分だけ追加でexitを出力する
                
                # 1. 基本の終了コマンド
                smtp_cmd_list.append("exit")
                                             
                # 2. destination-addresses が作成された行数分、さらにexitを追加する
                for _ in dest_addresses:
                    smtp_cmd_list.append("exit")
                
                
                smtp_generated_commands = "\n".join(smtp_cmd_list)
                all_generated_cmds_dict["smtp"] = smtp_generated_commands
            else:
                smtp_generated_commands = "SMTP設定の解析結果が空のため、コマンドは生成されませんでした。"
        else:
            smtp_raw_section = "ファイル内に「smtp」行から「destination」行に至るSMTP設定セクションが検出されませんでした。"
            smtp_generated_commands = "SMTP設定がないため、コマンドは生成されませんでした。"
            
        col_smtp_box1, col_smtp_box2 = st.columns(2)
        with col_smtp_box1:
            show_custom_area("SMTP設定の内容の表示", smtp_raw_section, 250, "smtp_raw_detail", "smtp_source_detail.txt")
        with col_smtp_box2:
            show_custom_area("作成されたSMTPコマンド", smtp_generated_commands, 250, "smtp_gen_detail", "smtp_commands_detail.txt")

        all_generated_cmds_dict["smtp"] = smtp_generated_commands

        st.markdown("---")

        # --------------------------------------
        # 🕒 タイムゾーン設定内容表示とコマンド自動作成
        # --------------------------------------
        st.subheader("🕒 タイムゾーン設定の精査と個別コマンド生成")
        
        timezone_raw_section = ""
        timezone_generated_commands = ""
        
        tz_found_lines = [l.strip() for l in base_cleaned_lines if l.strip().lower().startswith("timezone")]
        
        if tz_found_lines:
            timezone_raw_section = "\n".join(tz_found_lines)
            timezone_generated_commands = "\n".join(tz_found_lines)
            all_generated_cmds_dict["tz"] = timezone_generated_commands
        else:
            timezone_raw_section = "ファイル内に条件を満たす「タイムゾーン設定行（timezone...）」が見つかりませんでした。"
            timezone_generated_commands = "タイムゾーン設定がないため、コマンドは生成されませんでした。"
                
        col_tz1, col_tz2 = st.columns(2)
        with col_tz1:
            show_custom_area("タイムゾーン設定の内容の表示", timezone_raw_section, 180, "tz_raw", "timezone_source.txt")
        with col_tz2:
            show_custom_area("作成されたタイムゾーンコマンド", timezone_generated_commands, 180, "tz_gen", "timezone_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # 🔑 ライセンス更新設定内容表示とコマンド自動作成
        # --------------------------------------
        st.subheader("🔑 ライセンス更新設定の精査と個別コマンド生成")
        
        licensing_raw_section = ""
        licensing_generated_commands = ""
        
        lic_found_lines = []
        for idx, l in enumerate(base_cleaned_lines):
            l_stripped = l.strip()
            if l_stripped.lower().startswith("licensing"):
                lic_found_lines.append(l_stripped)
                if idx + 1 < len(base_cleaned_lines):
                    next_l_stripped = base_cleaned_lines[idx + 1].strip()
                    if next_l_stripped.lower().startswith("auto-update"):
                        lic_found_lines.append(next_l_stripped)
                break

        if lic_found_lines:
            licensing_raw_section = "\n".join(lic_found_lines)
            has_true = any("true" in line.lower() for line in lic_found_lines if line.lower().startswith("auto-update"))
            
            if has_true:
                licensing_generated_commands = "licensing auto-update true"
            else:
                licensing_generated_commands = "licensing auto-update false"
            all_generated_cmds_dict["lic"] = licensing_generated_commands
        else:
            licensing_raw_section = "ファイル内に条件を満たす「ライセンス設定（licensing / auto-update）」が見つかりませんでした。"
            licensing_generated_commands = "ライセンス設定がないため、コマンドは生成されませんでした。"
            
        col_lic1, col_lic2 = st.columns(2)
        with col_lic1:
            show_custom_area("ライセンス更新設定の内容の表示", licensing_raw_section, 180, "lic_raw", "licensing_source.txt")
        with col_lic2:
            show_custom_area("作成されたライセンス更新コマンド", licensing_generated_commands, 180, "lic_gen", "licensing_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # 🖥️ マシン情報更新設定内容表示とコマンド自動作成
        # --------------------------------------
        st.subheader("🖥️ マシン情報更新設定の精査と個別コマンド生成")
        
        machine_info_raw_section = ""
        machine_info_generated_commands = ""
        
        start_m_idx = -1
        end_m_idx = -1
        
        for idx, l in enumerate(base_cleaned_lines):
            l_stripped = l.strip()
            if start_m_idx == -1 and l_stripped.lower().startswith("appliance-name"):
                start_m_idx = idx
            if start_m_idx != -1 and l_stripped.lower().startswith("ip default-gateway"):
                end_m_idx = idx
                break

        if start_m_idx != -1 and end_m_idx != -1:
            extracted_machine_lines = [base_cleaned_lines[k].strip() for k in range(start_m_idx, end_m_idx + 1)]
            machine_info_raw_section = "\n".join(extracted_machine_lines)
            machine_info_generated_commands = "\n".join(extracted_machine_lines)
            all_generated_cmds_dict["mach"] = machine_info_generated_commands
        else:
            machine_info_raw_section = "ファイル内に条件を満たす「マシン情報設定範囲（appliance-name ～ ip default-gateway）」が見つかりませんでした。"
            machine_info_generated_commands = "マシン情報設定がないため、コマンドは生成されませんでした。"
            
        col_mach1, col_mach2 = st.columns(2)
        with col_mach1:
            show_custom_area("マシン情報更新設定の内容の表示", machine_info_raw_section, 220, "mach_raw", "machine_info_source.txt")
        with col_mach2:
            show_custom_area("作成されたマシン情報更新コマンド", machine_info_generated_commands, 220, "mach_gen", "machine_info_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # 🔌 NIC設定内容表示とコマンド自動作成
        # --------------------------------------
        st.subheader("🔌 NIC設定の精査と個別コマンド生成")
        
        nic_raw_section = ""
        nic_generated_commands = ""
        
        start_nic_idx = -1
        end_nic_idx = -1
        
        for idx, l in enumerate(base_cleaned_lines):
            l_stripped = l.strip()
            if start_nic_idx == -1 and l_stripped.lower().startswith("interface 0:0"):
                start_nic_idx = idx
            if start_nic_idx != -1 and l_stripped.lower().startswith("authentication"):
                for back_idx in range(idx - 1, start_nic_idx, -1):
                    if base_cleaned_lines[back_idx].strip() == "!":
                        end_nic_idx = back_idx
                        break
                if end_nic_idx != -1:
                    break

        if start_nic_idx != -1 and end_nic_idx != -1:
            nic_extracted_lines = [base_cleaned_lines[k].strip() for k in range(start_nic_idx, end_nic_idx + 1)]
            nic_raw_section = "\n".join(nic_extracted_lines)
            
            interfaces_blocks = []
            current_block = []
            
            for line in nic_extracted_lines:
                if line.lower().startswith("interface "):
                    if current_block:
                        interfaces_blocks.append(current_block)
                    current_block = [line]
                elif current_block:
                    if line == "!":
                        interfaces_blocks.append(current_block)
                        current_block = []
                    else:
                        current_block.append(line)
            if current_block:
                interfaces_blocks.append(current_block)
                
            all_nic_cmds = []
            
            for block in interfaces_blocks:
                if not block:
                    continue
                
                if_line = block[0]
                status_line = "disable"
                dhcp_line = None
                speed_val = "auto"
                duplex_val = "auto"
                mtu_line = None
                vlan_line = None
                ip_line = None
                
                for b_line in block[1:]:
                    b_stripped = b_line.strip()
                    b_lower = b_stripped.lower()
                    
                    if b_lower in ["enable", "disable"]:
                        status_line = b_stripped
                    elif b_lower.startswith("dhcp"):
                        dhcp_line = b_stripped
                    elif b_lower.startswith("speed "):
                        speed_val = b_stripped.replace("speed", "").strip()
                    elif b_lower.startswith("duplex "):
                        duplex_val = b_stripped.replace("duplex", "").strip()
                    elif b_lower.startswith("mtu-size"):
                        mtu_line = b_stripped
                    elif b_lower.startswith("vlan-trunking"):
                        vlan_line = b_stripped
                    elif b_lower.startswith("ip-address"):
                        ip_line = b_stripped
                
                def clean_space(txt):
                    return re.sub(r'\s+', ' ', txt).strip()
                
                cmd_block = []
                cmd_block.append(clean_space(if_line))
                cmd_block.append(clean_space(status_line))
                
                if dhcp_line:
                    cmd_block.append(clean_space(dhcp_line))
                    
                raw_speed_duplex = f"speed {speed_val} duplex {duplex_val}"
                cmd_block.append(clean_space(raw_speed_duplex))
                
                if mtu_line:
                    cmd_block.append(clean_space(mtu_line))
                if vlan_line:
                    cmd_block.append(clean_space(vlan_line))
                if ip_line:
                    cmd_block.append(clean_space(ip_line))
                    
                cmd_block.append("exit")
                
                all_nic_cmds.append("\n".join(cmd_block))
                
            nic_generated_commands = "\n\n".join(all_nic_cmds)
            all_generated_cmds_dict["nic"] = nic_generated_commands
        else:
            nic_raw_section = "ファイル内に条件を満たす「NIC設定範囲（interface 0:0 ～ authentication直上の !）」が見つかりませんでした。"
            nic_generated_commands = "NIC設定がないため、コマンドは生成されませんでした。"
            
        col_nic1, col_nic2 = st.columns(2)
        with col_nic1:
            show_custom_area("NIC設定の内容の表示", nic_raw_section, 300, "nic_raw", "nic_info_source.txt")
        with col_nic2:
            show_custom_area("作成されたNICコマンド", nic_generated_commands, 300, "nic_gen", "nic_commands.txt")

        st.markdown("---")

        # --------------------------------------
        # ⚙️ その他設定内容表示とコマンド自動作成
        # --------------------------------------
        st.subheader("⚙️ その他設定の精査と個別コマンド生成")
        
        other_raw_section = ""
        other_generated_commands = ""
        
        start_other_idx = -1
        end_other_idx = -1
        
        for idx, l in enumerate(base_cleaned_lines):
            l_stripped = l.strip()
            if start_other_idx == -1 and l_stripped.lower().startswith("authentication"):
                start_other_idx = idx
            if start_other_idx != -1 and l_stripped.lower().startswith("nacm groups group admin"):
                end_other_idx = idx
                break

        if start_other_idx != -1 and end_other_idx != -1:
            other_extracted_lines = [base_cleaned_lines[k].strip() for k in range(start_other_idx, end_other_idx + 1)]
            other_raw_section = "\n".join(other_extracted_lines)
            
            other_cmd_lines = []
            
            for line in other_extracted_lines:
                if line.lower().startswith("nacm groups group admin"):
                    continue
                if line.lower().startswith("smtp"):
                    continue
                if line.lower().startswith("gateway"):
                    continue
                if line.lower().startswith("from-address"):
                    continue
                if line.lower().startswith("destination"):
                    continue 
                if line.lower().startswith("edit user"):
                    continue
                if line.lower().startswith("edit ccl"):
                    continue

                if line.lower().startswith("add"):
                    continue
                if line.lower().startswith("admin-realm"):
                    continue
                if line.lower().startswith("edit realm"):
                    continue 
                if line.lower().startswith("destination-addresses"):
                    continue 
                if line.lower().startswith("local-user-list local-users"):
                    continue 
                if line.startswith("!"):
                    continue
                if line in ["service Management", "service SNMP", "service WebRouter"]:
                    continue
                
                cleaned_line = re.sub(r'\s+', ' ', line).strip()
                other_cmd_lines.append(cleaned_line)
                
            if other_cmd_lines:
                other_generated_commands = "\n".join(other_cmd_lines)
                all_generated_cmds_dict["other"] = other_generated_commands
            else:
                other_generated_commands = "追加コマンドは不要です。"
        else:
            other_raw_section = "ファイル内に条件を満たす「その他設定範囲（authentication ～ nacm groups group admin）」が見つかりませんでした。"
            other_generated_commands = "その他設定がないため、コマンドは生成されませんでした。"
            
        col_oth1, col_oth2 = st.columns(2)
        with col_oth1:
            show_custom_area("その他設定の内容の表示", other_raw_section, 300, "other_other_raw", "other_info_source.txt")
        with col_oth2:
            show_custom_area("作成されたその他コマンド", other_generated_commands, 300, "other_gen", "other_commands.txt")


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
    st.markdown("1ページ目で自動生成された各コマンドを結合して表示します。NIC設定は最後に配置されます。")
     
    combined_ordered_list = []
    # NICを最後（otherの後）に移動
    order_keys = ["smtp","snmp", "lag", "hm", "ntp", "proxy", "tz", "lic", "mach", "acl", "other", "nic"]
    
    for key in order_keys:
        cmd_content = all_generated_cmds_dict.get(key, "").strip()
        
        # 不要なメッセージを除外して追加
        if cmd_content and "コマンドは生成されませんでした" not in cmd_content and "見つかりませんでした" not in cmd_content and "追加コマンドは不要です" not in cmd_content:
            combined_ordered_list.append(cmd_content)
    
    # 結合処理
    all_commands_text = "\n\n".join(combined_ordered_list)
    
    # SNMPが含まれていない場合にのみ先頭に "conf" を追加
    if all_commands_text and not all_commands_text.strip().startswith("conf"):
        all_commands_text = "conf\n\n" + all_commands_text

    st.session_state.isg_command = all_commands_text
    # 結果を表示
    if all_commands_text:
        show_custom_area("すべての作成済みコマンド一括表示", all_commands_text, 600, "all_cmds", "all_commands.txt")
    else:
        st.warning("表示するコマンドがありません。")


# --- 5ページ目の追加コード ---
# ※既存のtabs定義の末尾に "📋 ISG設定リストア" を追加してください
# 例: tabs = st.tabs(["Tab1", "Tab2", "Tab3", "Tab4", "📋 ISG設定リストア"])

def get_interface_0_0_info(file_content):
    """
    アップロードされた内容から 'interface 0:0' から始まる8行を抽出する関数
    """
    # 行単位に分割
    lines = file_content.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "interface 0:0":
            # 該当行から8行分を取得（存在する場合のみ）
            return "\n".join(lines[i : i + 8])
    return "interface 0:0 の情報が見つかりませんでした。"


with tab5:  # 5番目のタブを指定
    st.header("📋 ISG設定をリストアする手順")
    
    st.markdown("### 準備作業")
    st.write("■二本の電源ケーブルを接続します。")
    st.write("■シリアルコンソールに接続します。")
    st.write("お客様提供情報のisg_configファイルをこのサイトの上部にアップロードします。")
    st.markdown("・ポート COMx (MD の環境に合わせて選択)")
    st.markdown("・スピード 9600, データ 8 bit, パリティ none, ストップビット 1 bit, フロー制御 none")
    st.write("・TeraTerm：[設定(S)] - [キーボード(K)] - Backspace キー にチェック")
    st.write("・TeraTerm：[ファイル(F)] - [ログ(L)]（ファイル名：受付 No_日付.txt）")

    os_ver = st.session_state.get('isg_os_version', '未検出')
    model = st.session_state.get('machine_model', '未検出')
    serial = st.session_state.get('serial_number', '未検出') 
    netwok_a = st.session_state.get('m_network_info', '未検出')
    

    
   
    st.markdown("---")
    st.subheader("フェーズ一：ISGの設定を行う")
    st.write("ステップ1: Command Line Interfaceに入り `show json-config` でシリアル/モデルを確認します。")
    if st.checkbox("ステップ1: シリアルとモデル番号が一致しました"): st.success("OK")

    m_model = st.session_state.get('machine_mode', '未検出')
    s_number = st.session_state.get('serial_numbe', '未検出')
    st.code(f"お客様から提供されたファイルから特定したのISGOSのシリアル番号とモデルは:マシンモデル:{model}\nシリアル番号:{serial}")  
    st.write("ステップ2: `health-monitoring view current` でステータス確認します。")
    if st.checkbox(" Appliance Certificate Validation以外のステータスが全てOK"): st.success("OK")



    def extract_network_info(text):
     """
     テキストからネットワーク情報を抽出する。
     テキストが空、または None の場合は初期値の辞書を返して終了する。
     """
     # 初期値（すべて None）
     info = {
        "name-server": None,
        "default-gateway": None,
        "interface": None,
        "ip-address": None,
        "networkmask": None
     }
    
     # text が None または空文字の場合はここで処理を終了して初期値を返す
     if not text:
        return info
    
     # 以下、抽出処理
     match_dns = re.search(r'dns name-server\s+(\d+\.\d+\.\d+\.\d+)', text)
     if match_dns:
        info["name-server"] = match_dns.group(1)
        
     match_gw = re.search(r'ip default-gateway\s+(\d+\.\d+\.\d+\.\d+)', text)
     if match_gw:
        info["default-gateway"] = match_gw.group(1)
        
     match_int = re.search(r'interface\s+([\d:]+)', text)
     if match_int:
        info["interface"] = match_int.group(1)
        
     match_ip_mask = re.search(r'ip-address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)', text)
     if match_ip_mask:
        info["ip-address"] = match_ip_mask.group(1)
        info["networkmask"] = match_ip_mask.group(2)
        
     return info
        
    m_info = st.session_state.get("m_network_info", "")
    info = extract_network_info(m_info)
    
    st.write("ステップ3: ISGのネットワークを設定する！")
    
    st.code(f"お客様から提供されたファイルから特定したネットワーク情報は :\n{info["ip-address"]}\n{info["networkmask"]}\n{info["default-gateway"]}\n{info["name-server"]}")   
    
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px;">
Appliance Serial Console<br>
-------------------------- MENU ---------------------------<br>
1) Command Line Interface<br>
2) Setup console<br>
-----------------------------------------------------------<br>
Enter option: 2
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.5;">
Welcome to the Symantec S210 Series Appliance Setup console.<br>
<br>
-------------------------- (page 1 of 3) --------------------------<br>
<br>
Press &lt;CTRL-C&gt; to exit the Initial configuration wizard at any time<br>
<br>
Please enter the network configuration for the S210 Appliance<br>
The following interfaces are available for configuration:<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1. 0:0<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2. 1:0<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3. 2:0<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;4. 2:1<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5. 2:2<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6. 2:3<br>
<br>
<br>
Enter interface number to configure [1]: DHCP is enabled on this interface but no IP address is assigned yet.<br>
DHCP may only be enabled on one interface at a time.<br>
Continue with DHCP for IP address, gateway, and DNS settings on interface 0:0? Y/N [No] N
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.6;">
You have entered the following IP settings:<br>
<br>
IP address: {info['ip-address']}<br>
IP subnet mask: {info['networkmask']}<br>
IP gateway: {info['default-gateway']}<br>
DNS server(s): {info['name-server']}<br>
<br>
<br>
Would you like to change any of them? Y/N [No] N
</div>
""", unsafe_allow_html=True)

    
    st.markdown("---")

    st.write("ステップ4: お客様提供のadmin/enableパスワードを設定します。")
    st.markdown("---")
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.5;">
DIRECTIONS:<br>
<br>
The console username, password and enable password are special administrative<br>
credentials which can be used to log in to the command line interface or web<br>
management interface.<br>
<br>
Enter console password:<br>
Verify console password:<br>
<br>
<br>
Enter enable password:<br>
Verify enable password:
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    st.write("ステップ5: MDのネットワークもISGと同じネットワークのIPで設定します。")
    st.markdown("<span style='color:red'>ステップ6: Do you want to secure the serial port? -> かならず N で入れてください</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.5;">
DIRECTIONS:<br>
<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When the serial port is secured, access via the serial port must<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;be authenticated using both a setup password and administrative<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;credentials.<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A setup password is required to gain access to the Setup Console<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;and administrative credentials are required to access the<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;command line interface (CLI).<br>
<br>
<br>
Do you want to secure the serial port? Y/N [Yes] N
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    st.write("ステップ7: CLIに再ログインし、enableパスワードでのログイン確認を行います。")
    st.markdown("---")
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px;">
Appliance Serial Console<br>
-------------------------- MENU ---------------------------<br>
1) Command Line Interface<br>
2) Setup console<br>
-----------------------------------------------------------<br>
Enter option: 1
</div>
""", unsafe_allow_html=True)
    st.write("ステップ8: MDのネットワークからSSH経由でadminログイン確認を行います。")
    if st.checkbox("ステップ8: ネットワーク/ログイン確認が全てOK"): st.success("OK")


    st.markdown("---")
    st.subheader("フェーズ二：同じISGバージョンのインストール")

    st.write("ステップ1: アップグレードパスとダウングレードパスを確認します。")
    st.write("ステップ2: `localhost# installed-systems view` でファームウェアを確認します。")
    st.write("ステップ3: 必要ファームウェアをダウンロードし、MDのIISサイトに格納します。")
    st.write("ステップ4: `localhost# installed-systems load http://192.168.84.19/[ファームウェア名]` でロードします。")
    st.markdown("<span style='color:red'>注:192.168.84.19を実際のMDのIPに替えてください</span>", unsafe_allow_html=True)
    st.write("ステップ5: `localhost# installed-systems default [番号]` でバージョンを指定します。")
    st.write("ステップ6: 再起動後、バージョンの一致を確認します。")
    if st.checkbox("バージョンが一致していることを確認しました"): st.success("OK")
    st.code(f"お客様から提供されたファイルから特定したのISGOS バージョン :{os_ver}")           

    st.markdown("---")
    st.subheader("フェーズ三：ライセンスのインストール")
    st.write("ステップ1: CLIでenableパスワードでログインします。")
    st.markdown("---")
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px;">
Appliance Serial Console<br>
-------------------------- MENU ---------------------------<br>
1) Command Line Interface<br>
2) Setup console<br>
-----------------------------------------------------------<br>
Enter option: 1
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.write("ステップ2: `licensing inline passphrase synnex` 実行後、ライセンス開いて内容をコピーして、ターミナルにペーストします。コピーが完了したら Ctrl+D で終了します。")
    st.markdown("---")
    st.markdown("""

<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.5;">
localhost&gt; en<br>
Password:<br>
localhost# licensing inline passphrase synnex<br>
Enter the license key below and end it with a Ctrl-D
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    

    
    st.markdown("---")
   
    st.write("ステップ3: `licensing view` でライセンスIDが一致することを確認します。")
    if st.checkbox("ライセンスIDが一致することを確認しました"): st.success("OK")
        
    st.markdown("---")

    

    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.5;">
localhost# licensing view<br>
<br>
auto-update  :  not configured<br>
ID           Label<br>
---------   ---------<br>
xxxxxxxxx  <None>    <br>

</div>
""", unsafe_allow_html=True)


  
    st.markdown("---")
    st.subheader("フェーズ四：ISGconfigのリストア")
    st.markdown("---")
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px;">
Appliance Serial Console<br>
-------------------------- MENU ---------------------------<br>
1) Command Line Interface<br>
2) Setup console<br>
-----------------------------------------------------------<br>
Enter option: 1
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    st.write("ステップ1: CLIでenableパスワードでログインします(confは入れない)。")
    st.markdown("""
<div style="background-color: #000000; color: #00FF00; padding: 15px; font-family: monospace; border-radius: 5px; line-height: 1.5;">

consoleuser connected from 127.0.0.1 using console on localhost<br>
localhost&gt; en<br>
Password:<br>
localhost#<br>

</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    st.write("ステップ2: 作成済みコマンドをターミナルに貼り付けして、実行します。")
    i_command = st.session_state.get('isg_command', '未検出')
    st.code(f"\n{i_command}")   
    st.write("ステップ3: エラー時はSynnexへ連絡します。")
    st.write("""
### ステップ4: リストア後の設定確認とログ保存

リストア完了後、システム整合性を確認するために以下のコマンドを順番に発行してください。
取得した全ての出力結果を統合し、`isg_after_resore.txt` というファイル名で保存してください。

---
#### **実行コマンドリスト**
1. `show json-config`
2. `show running-config | nomore`
3. `health-monitoring view settings`
4. `show applications event-log view configuration`
5. `lag view`
---
""")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        file_cust = st.file_uploader("顧客提供ISG設定ファイル", type=["txt", "conf"], key="cust_diff")
    with col_u2:
        file_rest = st.file_uploader("リストア後ISG設定ファイル", type=["txt", "conf"], key="rest_diff")

    def clean_config(text):
        # "aaa authentication users user admin" から "agent enabled" の直前までを除去
        # re.DOTALLで改行を含め、先読み (?=agent enabled) を利用して安全に範囲指定
        pattern = re.compile(r'aaa authentication users user admin[\s\S]*?(?=agent enabled)', re.MULTILINE)
        return pattern.sub('', text).strip()

    if file_cust and file_rest:
        content_cust = clean_config(file_cust.getvalue().decode("utf-8"))
        content_rest = clean_config(file_rest.getvalue().decode("utf-8"))
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.subheader("顧客提供ISG (除去後)")
            st.code(content_cust)
            
        with c2:
            st.subheader("リストア後ISG (除去後)")
            st.code(content_rest)
            
        with c3:
            st.subheader("差異表示")
            diff = list(difflib.ndiff(content_cust.splitlines(), content_rest.splitlines()))
            # '+' や '-' で始まる行（差異）を抽出
            diff_lines = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]
            
            if not diff_lines:
                st.success("内容は同じです。")
            else:
                st.code("\n".join(diff))
    else:
        st.info("比較のため、両方のファイルをアップロードしてください。")
    # ==========================================
# 4ページ目：SGOS情報確認
# ==========================================
with tab4:
    st.header("🔍 SGOS 情報確認")

    # 1. ファイルアップロード
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

    results = [] # 全体判定用リスト

    # --- キッティング前の確認処理 ---
    if up_sys_pre:
        sys_p = up_sys_pre.getvalue().decode().splitlines()

        # --- 項目1: ハードウェア情報比較 (行そのものを比較) ---
        if up_sys_cust:
            sys_c = up_sys_cust.getvalue().decode().splitlines()
            
            def get_raw_lines(lines):
                # "Serial number is" で始まる行、RAM行、Cores行をそのまま抽出
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
            show_custom_area("詳細比較 (行単位)", f"お客様:\n{c_info}\n\nキッティング前:\n{p_info}", 150, "c1", "c1.txt")

        # --- 項目2: Storage ---
        st.subheader("✅ チェック項目2: Storage情報")
        target = "Storage100.5.5.1     00000000:00000000"
        found_line = next((l for l in sys_p if "Storage100.5.5.1" in l), "")
        is_ok2 = (found_line.strip() == target)
        results.append(is_ok2)
        st.markdown(f"判定: :{'green' if is_ok2 else 'red'}[{'OK' if is_ok2 else 'NG'}]")
        show_custom_area("抽出内容", found_line if found_line else "該当なし", 70, "c2", "c2.txt")

        # --- 項目3: Current State ---
        st.subheader("✅ チェック項目3: Current State確認")
        skip_w = ["Overall Health", "Base License Expiration", "Health Check Status", 
                  "Content Filter Communication Status", "SSL Proxy License Exporation", 
                  "License Server Communication Status", "Application Classification Communication Status"]
        
        results_c3, extracted_data = [], []
        for i, l in enumerate(sys_p):
            if "Current State" in l:
                prev = sys_p[i-1] if i > 0 else ""
                extracted_data.append(f"Header: {prev.strip()}\nData: {l.strip()}")
                
                # スキップ対象外のみ判定（"Current State : OK" と完全に一致するか）
                if not any(w in prev for w in skip_w):
                    # 前方一致等を考慮し、Current State : OK が含まれているか確認
                    results_c3.append("Current State" in l and ": OK" in l)
        
        is_ok3 = all(results_c3) if results_c3 else True
        results.append(is_ok3)
        st.markdown(f"判定: :{'green' if is_ok3 else 'red'}[{'OK' if is_ok3 else 'NG'}]")
        show_custom_area("抽出されたCurrent State", "\n\n".join(extracted_data), 200, "c3", "c3.txt")

        # --- 項目4/5: CPU/Memory ---
        for title, key_str in [("CPU", "system:cpu-usage~hourly"), ("メモリ", "system:memory-usage~hourly")]:
            st.subheader(f"✅ {title}使用率確認")
            lines = [l for l in sys_p if key_str in l]
            vals = []
            for l in lines:
                m = re.search(r'\(60, 60\):\s*(.*)', l)
                if m: vals.extend([int(n) for n in re.findall(r'\d+', m.group(1))])
            
            is_ok = all(v <= 50 for v in vals) if vals else True
            results.append(is_ok)
            st.markdown(f"判定: :{'green' if is_ok else 'red'}[{'OK' if is_ok else 'NG'}]")
            show_custom_area("抽出数値", str(vals), 100, f"c{title}", f"{title}.txt")

    # --- チェック項目6: Eventログ ---
    if up_ev_pre:
        st.subheader("✅ チェック項目6: イベントログエラー確認")
        errs = ["read error has occurred", "arning, a write episoded", "PSU no input"]
        content = up_ev_pre.getvalue().decode()
        found = [e for e in errs if e in content]
        is_ok6 = (len(found) == 0)
        results.append(is_ok6)
        st.markdown(f"判定: :{'green' if is_ok6 else 'red'}[{'OK' if is_ok6 else 'NG'}]")
        show_custom_area("検出エラー", str(found) if found else "エラーなし", 100, "c6", "c6.txt")

    # --- 全体判定 ---
    if len(results) >= 6:
        st.markdown("---")
        if all(results): st.success("### ✅ 全体判定：OK")
        else: st.error("### ❌ 全体判定：NG")

    # --- コンテンツフィルタ & Config後確認 ---
    if up_conf_cust:
        st.subheader("🛡️ コンテンツフィルタ設定")
        m = re.search(r'!- BEGIN content_filtering(.*?)!- END content_filtering', up_conf_cust.getvalue().decode(), re.DOTALL)
        if m: show_custom_area("抽出内容", m.group(0), 200, "cf", "cf.txt")

    if up_conf_cust and up_conf_post:
        st.subheader("🔧 キッティング後のConfig比較")
        c_lines = set(up_conf_cust.getvalue().decode().splitlines())
        p_lines = set(up_conf_post.getvalue().decode().splitlines())
        diff = c_lines ^ p_lines
        if diff:
            st.error("不一致あり")
            show_custom_area("不一致箇所", "\n".join(list(diff)), 300, "diff", "diff.txt")
        else: st.success("一致しています")
           
