import json
from pathlib import Path

class QCReportExporter:
    """
    Exports clean, standalone HTML and Markdown QC Audit Reports for Mentors & Students.
    """
    @staticmethod
    def export_html_report(agent_report, rule_stats, rule_errors, missing_objects, class_mismatches, output_html_path):
        """
        Generates a professional standalone HTML report.
        """
        output_html_path = Path(output_html_path)
        output_html_path.parent.mkdir(parents=True, exist_ok=True)

        status_color = "#28a745" if agent_report["decision"] == "PASSED" else ("#ffc107" if agent_report["decision"] == "REJECTED_NEEDS_REWORK" else "#dc3545")

        formatted_feedback = agent_report['feedback_text'].replace('\n', '<br>')

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Báo Cáo Kiểm Định Chất Lượng Nhãn - AI QC Auditor Agent</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 950px; margin: auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 3px solid #007bff; padding-bottom: 15px; margin-bottom: 25px; }}
        .header h1 {{ margin: 0; color: #007bff; font-size: 26px; }}
        .badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: #fff; font-weight: bold; font-size: 16px; background-color: {status_color}; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background: #f1f3f5; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-card h3 {{ margin: 0; font-size: 24px; color: #212529; }}
        .metric-card p {{ margin: 5px 0 0; color: #6c757d; font-size: 13px; }}
        .agent-box {{ background: #e7f5ff; border-left: 5px solid #1c7ed6; padding: 20px; border-radius: 5px; margin: 25px 0; }}
        .agent-box h3 {{ margin-top: 0; color: #1971c2; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; border: 1px solid #dee2e6; text-align: left; font-size: 14px; }}
        th {{ background-color: #f1f3f5; }}
        .tag-err {{ color: #d9480f; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 BÁO CÁO KIỂM ĐỊNH CHẤT LƯỢNG NHÃN (AI QC AUDIT)</h1>
            <p><strong>Học viên:</strong> {agent_report['annotator_name']} | <strong>Dự án:</strong> VinUni AI20K - Road Object Detection</p>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2>Điểm Chất Lượng: <span style="color: {status_color};">{agent_report['quality_score']}/100</span></h2>
            </div>
            <div>
                <span class="badge">{agent_report['decision_label']}</span>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>{agent_report['total_audited']}</h3>
                <p>Tổng Số Nhãn Audited</p>
            </div>
            <div class="metric-card">
                <h3>{agent_report['rule_errors_count']}</h3>
                <p>Lỗi Quy Tắc Rule-Based</p>
            </div>
            <div class="metric-card">
                <h3>{agent_report['missing_objects_count']}</h3>
                <p>Lỗi Nghi Bỏ Sót Xe Khuất</p>
            </div>
            <div class="metric-card">
                <h3>{agent_report['class_mismatches_count']}</h3>
                <p>Lỗi Nghi Sai Class</p>
            </div>
        </div>

        <div class="agent-box">
            <h3>🤖 Nhận Xét Chi Tiết Từ AI QC Auditor Agent</h3>
            <div>{formatted_feedback}</div>
        </div>

        <h2>📌 Danh Sách Lỗi Cần Khắc Phục</h2>
        <table>
            <thead>
                <tr>
                    <th>Frame / Ảnh</th>
                    <th>Loại Lỗi</th>
                    <th>Class</th>
                    <th>Mô Tả Lỗi Chi Tiết</th>
                </tr>
            </thead>
            <tbody>
"""
        # Append rule errors
        for err in rule_errors[:15]:
            html_content += f"""
                <tr>
                    <td>{err['frame_name']}</td>
                    <td><span class="tag-err">{err['error_type']}</span></td>
                    <td>{err.get('class_name', 'N/A')}</td>
                    <td>{err['error_msg']}</td>
                </tr>
            """

        # Append missing object errors
        for err in missing_objects[:10]:
            html_content += f"""
                <tr>
                    <td>{err['frame_name']}</td>
                    <td><span class="tag-err">{err['error_type']}</span></td>
                    <td>{err['class_name']}</td>
                    <td>{err['error_msg']}</td>
                </tr>
            """

        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"📄 HTML QC Audit Report Exported: {output_html_path}")
        return str(output_html_path)
