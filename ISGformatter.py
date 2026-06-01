import json
import re
import streamlit as st

st.set_page_config(page_title="ISG & SGOS 構成・整形ツール", layout="wide")

st.title("ISG & SGOS 設定ファイル 変換・整形ツール")

def show_custom_area(label, text_value, height, unique_key, download_filename):
    st.markdown(f"**{label}**")
    
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

    st.code(text_value, language="text", line_numbers=False)


tab1, tab2, tab3 = st.tabs([
    "1ページ目：ISGファイルの読込・整形・コマンド作成", 
    "2ページ目：SGOSファイルの整形",
    "3ページ目：作成コマンドの一括出力"
])

all_generated_cmds_dict = {
    "snmp": "", "lag": "", "hm": "", "ntp": "", "proxy": "", "smtp": "",
    "tz": "", "lic": "", "mach": "", "nic": "", "acl": "", "other": ""
}

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
