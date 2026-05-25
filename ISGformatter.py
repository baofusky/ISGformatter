# --------------------------------------
        # 【範囲修正】Healthmonitorの読込と動的コマンド再構築
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
            # まずhealth-monitoringセクション全体（40行）を切り出す
            full_hm_lines = base_cleaned_lines[hm_start_index : hm_start_index + 40]
            
            # 💡 【今回の修正】「CPU Utilization」から「Voltage Sensors」までの行を動的に抽出
            start_target_idx = -1
            end_target_idx = -1
            
            for idx, line in enumerate(full_hm_lines):
                if "CPU Utilization" in line:
                    start_target_idx = idx
                if "Voltage Sensors" in line:
                    end_target_idx = idx
                    break  # Voltage Sensorsの行を見つけたらそこで終了
            
            # 安全に対象範囲の行を抽出（見つからなかった場合は全体をフォールバック）
            if start_target_idx != -1 and end_target_idx != -1:
                extracted_hm_lines = full_hm_lines[start_target_idx : end_target_idx + 1]
            else:
                extracted_hm_lines = full_hm_lines
            
            # 画面表示用にテキストを結合
            hm_raw_text = "\n".join(extracted_hm_lines)
            
            # マッピング定義 (対応するコマンド用ID)
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
            
            # 抽出された範囲の行のみを順番に走査して解析
            for line_data in extracted_hm_lines:
                line_stripped = line_data.strip()
                if not line_stripped or "---" in line_stripped:
                    continue
                
                # 行内のメトリックを特定
                matched_cmd_id = None
                for keyword, cmd_id in metric_mapping.items():
                    if keyword in line_stripped:
                        matched_cmd_id = cmd_id
                        break
                
                if matched_cmd_id:
                    # 1. 閾値（Warning / Critical）の動的解析
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
                    
                    # 2. 末尾のアラートフラグ（T, M）の動的判定
                    parts = line_stripped.split('|')
                    if len(parts) >= 2:
                        alerts_section = parts[-1].strip()
                        
                        if "T" in alerts_section:
                            hm_commands.append(f"health-monitoring metric {matched_cmd_id} trap enable")
                        if "M" in alerts_section:
                            hm_commands.append(f"health-monitoring metric {matched_cmd_id} email enable")
                                
            hm_generated_text = "\n".join(hm_commands) if hm_commands else "追加コマンドは不要です。"
        else:
            hm_raw_text = "ファイル内に「health-monitoring view settings」に該当するセクションが見つかりませんでした。"
            hm_generated_text = "Healthmonitorコマンドは生成されませんでした。"

        col_hm1, col_hm2 = st.columns(2)
        with col_hm1:
            show_custom_area("Healthmonitor 設定内容枠 (指定範囲を自動抽出)", hm_raw_text, 250, "hm_raw", "health_source.txt")
        with col_hm2:
            show_custom_area("再構築された Healthmonitor コマンド枠", hm_generated_text, 250, "hm_gen", "health_commands.txt")
