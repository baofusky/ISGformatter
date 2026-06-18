        # --------------------------------------
        # 📄 Event Log設定の抽出
        # --------------------------------------
        st.subheader("📄 Event Log設定の抽出")

        eventlog_raw_text = ""
        eventlog_generated_commands = ""

        start_idx = -1
        end_idx = -1

        for idx, line in enumerate(base_cleaned_lines):

            line_strip = line.strip()

            if start_idx == -1 and line_strip.startswith("Log level:"):
                start_idx = idx

            if (
                start_idx != -1
                and line_strip.startswith("Syslog max size set to :")
            ):
                end_idx = idx
                break

        if start_idx != -1 and end_idx != -1:

            eventlog_lines = base_cleaned_lines[start_idx:end_idx + 1]

            eventlog_raw_text = "\n".join(eventlog_lines)

            cmds = ["event-log"]

            level_match = re.search(
                r'Log level:\s*(\d+)',
                eventlog_raw_text,
                re.IGNORECASE
            )

            if level_match:
                cmds.append(
                    f"event-log level {level_match.group(1)}"
                )

            for i, line in enumerate(eventlog_lines):

                if "Remote syslog servers:" in line:

                    search_lines = []

                    for j in range(i, min(i + 5, len(eventlog_lines))):
                        search_lines.append(eventlog_lines[j])

                    for target in search_lines:

                        m = re.search(
                            r'(UDP|TLS)\s+([\d\.]+):(\d+)',
                            target,
                            re.IGNORECASE
                        )

                        if m:

                            protocol = m.group(1).lower()
                            ipaddr = m.group(2)
                            port = m.group(3)

                            cmds.append(
                                f"syslog add {protocol} host {ipaddr} port {port}"
                            )

                    break

            size_match = re.search(
                r'Syslog max size set to\s*:\s*(\d+)M',
                eventlog_raw_text,
                re.IGNORECASE
            )

            if size_match:
                cmds.append(
                    f"log-size {size_match.group(1)}"
                )

            cmds.append("exit")

            eventlog_generated_commands = "\n".join(cmds)

            all_generated_cmds_dict["eventlog"] = (
                eventlog_generated_commands
            )

        else:

            eventlog_raw_text = (
                "Log level ～ Syslog max size set to : "
                "の範囲が見つかりませんでした"
            )

            eventlog_generated_commands = (
                "Event Log設定が見つかりませんでした"
            )

        col_evt1, col_evt2 = st.columns(2)

        with col_evt1:
            show_custom_area(
                "Event Log設定内容",
                eventlog_raw_text,
                220,
                "eventlog_raw",
                "eventlog_source.txt"
            )

        with col_evt2:
            show_custom_area(
                "作成されたEvent Logコマンド",
                eventlog_generated_commands,
                220,
                "eventlog_cmd",
                "eventlog_commands.txt"
            )

        st.markdown("---")
