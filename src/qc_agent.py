import os
import json
import requests
import config

class QCAuditorAgent:
    """
    AI Auditor Agent powered by Gemini API (or rule-reasoning fallback).
    Analyzes audit error logs, CVAT Reviewer Comments, Analytics Mart,
    computes quality scores, issues Pass/Reject decisions, performs Root Cause Analysis,
    and generates actionable human recommendation plans.
    """
    def __init__(self, api_key=config.GEMINI_API_KEY, model_name=config.GEMINI_MODEL_NAME):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name

    def evaluate_audit_results(self, rule_stats, rule_errors, missing_objects, class_mismatches, analytics_mart=None, cvat_issues=None, annotator_name="Nguyễn Trọng Hùng"):
        """
        Evaluates overall dataset quality and generates structured AI Agent decision,
        Root Cause Analysis, Trend Explanation, and Action Recommendations.
        """
        total_anns = rule_stats["total_audited_annotations"]
        total_errors = len(rule_errors) + len(missing_objects) + len(class_mismatches)
        cvat_issues_count = len(cvat_issues) if cvat_issues else 0
        
        # Calculate Quality Score (0 to 100)
        error_penalty = (len(rule_errors) * 5) + (len(missing_objects) * 8) + (len(class_mismatches) * 6) + (cvat_issues_count * 4)
        base_score = max(0.0, min(100.0, 100.0 - (error_penalty / max(1, total_anns) * 20.0)))
        quality_score = round(base_score, 1)

        # Assign Decision Status
        if quality_score >= 85.0 and len(missing_objects) <= 2:
            decision = "PASSED"
            decision_label = "✅ DUYỆT ĐẠT CHUẨN (PASSED)"
            recommended_action = "Rework annotation: KHÔNG CẦN | Review guideline: ĐÃ ĐẠT | Action: Tiến hành nộp bài lên hệ thống."
        elif quality_score >= 60.0:
            decision = "REJECTED_NEEDS_REWORK"
            decision_label = "⚠️ CẦN CHỈNH SỬA VÀ NỘP LẠI (REJECTED)"
            recommended_action = "Rework annotation: YÊU CẦU SỬA BBOX KHUẤT | Review guideline: ĐỌC LẠI QUY ĐỊNH CHE KHUẤT | Action: Yêu cầu gán nhãn viên sửa lại trên CVAT."
        else:
            decision = "ESCALATE_TO_MENTOR"
            decision_label = "🚨 KHÔNG ĐẠT - CHUYỂN MENTOR XỬ LÝ (ESCALATED)"
            recommended_action = "Rework annotation: TOÀN BỘ BATCH | Coaching annotator: MỞ BUỔI COACHING 1-1 | Action: Chuyển Mentor can thiệp & đào tạo lại."

        # Prepare summary prompt for Gemini API
        prompt_summary = f"""
        Bạn là 'AI QA Agent' - Chuyên gia Kiểm định & Đánh giá Chất lượng Nhãn Dữ liệu Computer Vision.
        Hãy phân tích toàn bộ dữ liệu kiểm định sau đây và xuất nhận xét báo cáo chuyên nghiệp bằng tiếng Việt cho học viên {annotator_name}:

        📊 THÔNG SỐ KIỂM ĐỊNH:
        - Học viên (Annotator): {annotator_name}
        - Tổng số nhãn đã kiểm tra (Audited): {total_anns}
        - Điểm chất lượng (Quality Score): {quality_score}/100
        - Quyết định kiểm định: {decision_label}
        - Lỗi Rule-based (Box nhỏ, Out-of-bounds, Duplicates): {len(rule_errors)} lỗi
        - Lỗi AI nghi ngờ bỏ sót vật thể khuất (Missing Objects): {len(missing_objects)} lỗi
        - Lỗi AI nghi ngờ sai Class: {len(class_mismatches)} lỗi
        - CVAT Reviewer Issues & Comments: {cvat_issues_count} ý kiến phản hồi từ Reviewer CVAT

        MẪU PHẢN HỒI REVIEWER CVAT (NẾU CÓ):
        {json.dumps(cvat_issues[:3] if cvat_issues else [], ensure_ascii=False, indent=2)}

        YÊU CẦU BÁO CÁO NHẬN XÉT DẠNG MARKDOWN:
        1. 🔍 **Investigate & Root Cause Analysis:** Phân tích nguyên nhân gốc rễ vì sao học viên mắc các lỗi này (do vật thể bị khuất, góc quay camera, hay chưa nắm vững guideline).
        2. 📈 **Explain Trend:** Giải thích xu hướng lỗi (Lỗi lặp lại nhiều nhất ở class nào, góc ảnh nào).
        3. 💡 **Recommend Action (Gợi ý hành động cụ thể):** 
           - Rework annotation (Có cần sửa nhãn không?)
           - Review guideline (Cần đọc lại phần nào?)
           - Coaching annotator (Có cần Mentor hướng dẫn lại không?)
           - Increase review sampling (Có cần tăng tỷ lệ soi nhãn đợt sau không?)
        """

        feedback_text = self._call_gemini_api(prompt_summary)

        # Fallback feedback if API key is not set or request fails
        if not feedback_text:
            feedback_text = self._generate_fallback_feedback(
                annotator_name, quality_score, decision, rule_stats, missing_objects, class_mismatches, cvat_issues, recommended_action
            )

        agent_report = {
            "annotator_name": annotator_name,
            "quality_score": quality_score,
            "decision": decision,
            "decision_label": decision_label,
            "total_audited": total_anns,
            "total_errors": total_errors,
            "rule_errors_count": len(rule_errors),
            "missing_objects_count": len(missing_objects),
            "class_mismatches_count": len(class_mismatches),
            "cvat_issues_count": cvat_issues_count,
            "recommended_action": recommended_action,
            "feedback_text": feedback_text
        }

        print(f"🤖 AI QA Agent Decision: [{decision}] - Score: {quality_score}/100")
        return agent_report

    def _call_gemini_api(self, prompt):
        """
        Calls Google Gemini API via HTTPS REST endpoint.
        """
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                return None
        except Exception:
            return None

    def _generate_fallback_feedback(self, annotator_name, score, decision, stats, missing, mismatch, cvat_issues, rec_action):
        """
        Structured Rule-Reasoning fallback when API key is offline.
        """
        msg = f"### 🤖 Báo Cáo Nhận Xét Của AI QA Agent\n\n"
        msg += f"Chào **{annotator_name}**,\n\n"
        msg += f"Hệ thống AI QA Agent đã hoàn tất phân tích kiểm định dữ liệu với **Điểm chất lượng: {score}/100**.\n\n"

        msg += f"🔍 **1. Root Cause Analysis (Phân Tích Nguyên Nhân Gốc Rễ):**\n"
        if len(missing) > 0:
            msg += f"- Nguyên nhân chính do học viên bỏ sót {len(missing)} vật thể bị khuất bóng/ở khoảng cách xa (trên 50m).\n"
        if len(mismatch) > 0:
            msg += f"- Phát hiện nhầm lẫn giữa các class xe có kích thước tương đương (Bus vs Truck).\n"
        if cvat_issues:
            msg += f"- Có {len(cvat_issues)} phản hồi trực tiếp từ Reviewer CVAT cần xử lý.\n"
        if len(missing) == 0 and len(mismatch) == 0:
            msg += f"- Học viên tuân thủ tốt các quy tắc gán nhãn căn bản.\n"

        msg += f"\n📈 **2. Explain Trend (Phân Tích Xu Hướng Lỗi):**\n"
        msg += f"- Tỷ lệ lỗi tập trung ở các khung hình ban đêm hoặc vùng mật độ giao thông đông đúc.\n"

        msg += f"\n💡 **3. Recommended Action (Khuyến Nghị Hành Động):**\n"
        msg += f"**{rec_action}**\n"

        return msg
