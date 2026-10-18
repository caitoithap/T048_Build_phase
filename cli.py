import os
import sys
import argparse
from pathlib import Path

import config
from src.qc_rules import QCRuleEngine
from src.model_assisted_qc import ModelAssistedQCAuditor
from src.qc_agent import QCAuditorAgent
from src.report_generator import QCReportExporter
from src.cvat_api import CVATApiClient
from src.analytics_mart import QualityAnalyticsMart

def main():
    parser = argparse.ArgumentParser(description="CVAT Automated QC & AI Reviewer Agent System (Stitch Architecture Edition)")
    parser.add_argument("--annotation", type=str, default="output/pre_annotations_cvat.xml", help="Path to CVAT XML annotation file")
    parser.add_argument("--images", type=str, default="sample_data", help="Path to image directory")
    parser.add_argument("--student", type=str, default="Nguyễn Trọng Hùng", help="Student / Annotator Name")
    parser.add_argument("--task-id", type=str, default="108361", help="CVAT Task ID for live ingestion")
    parser.add_argument("--cvat-url", type=str, default="https://app.cvat.ai", help="CVAT Server URL")
    parser.add_argument("--mock-cvat", action=argparse.BooleanOptionalAction, default=True,
                        help="Simulate CVAT API Live Ingestion Mode (--no-mock-cvat to skip)")
    parser.add_argument("--output-report", type=str, default="output/qc_audit_report.html", help="Path to save HTML report")

    args = parser.parse_args()

    print("=" * 75)
    print("🔍 CVAT AUTOMATED QC & AI REVIEWER AGENT SYSTEM (AI20K COHORT 4)")
    print("=" * 75)

    ann_path = Path(args.annotation)
    img_path = Path(args.images)
    cvat_issues = []

    # CVAT Live API Ingestion Simulation
    if args.mock_cvat:
        print(f"🌐 [0/4] Ingesting Live CVAT REST API Data for Task #{args.task_id}...")
        client = CVATApiClient(server_url=args.cvat_url)
        task_meta, ann_p, cvat_issues = client.mock_fetch_task_data(args.task_id, str(ann_path), "output")
        ann_path = Path(ann_p)
        print(f"✅ CVAT Data Ingested: Task '{task_meta['name']}' with {len(cvat_issues)} Reviewer Issues.")

    if not ann_path.exists():
        fallback_ann = Path("sample_data_output1/annotations.xml")
        if fallback_ann.exists():
            print(f"ℹ️ Annotation file [{ann_path}] not found. Falling back to default [{fallback_ann}]...")
            ann_path = fallback_ann
        else:
            print(f"❌ Annotation file [{ann_path}] not found.")
            sys.exit(1)

    # 1. Rule-Based QC Audit
    print("🧹 [1/4] Running Rule-Based QC Audit Engine...")
    rule_engine = QCRuleEngine()
    parsed_anns = rule_engine.parse_cvat_xml(ann_path)
    passed_anns, rule_errors, rule_stats = rule_engine.audit_annotations(parsed_anns)

    # 2. Model-Assisted Audit (Missing objects & class conflicts)
    print("🤖 [2/4] Running Model-Assisted Missing Object Audit on CPU...")
    model_auditor = ModelAssistedQCAuditor()
    missing_objs, class_mismatches = model_auditor.audit_missing_and_mislabels(img_path, parsed_anns)

    # 3. Quality Analytics Mart Computation
    print("📈 [3/4] Computing Quality Analytics Mart Metrics...")
    analytics_mart = QualityAnalyticsMart.compute_analytics_mart(
        rule_errors, missing_objs, class_mismatches, rule_stats["total_audited_annotations"], annotator_name=args.student
    )

    # 4. AI Auditor Agent Evaluation & Feedback Generation
    print("🧠 [4/4] Executing AI QA Agent Evaluation & Recommendation Plan...")
    agent = QCAuditorAgent()
    agent_report = agent.evaluate_audit_results(
        rule_stats, rule_errors, missing_objs, class_mismatches, analytics_mart, cvat_issues, annotator_name=args.student
    )

    # 5. Generate HTML Audit Report
    report_path = QCReportExporter.export_html_report(agent_report, rule_stats, rule_errors, missing_objs, class_mismatches, args.output_report)

    print("\n" + "=" * 75)
    print("📊 QC AUDIT & ANALYTICS SUMMARY")
    print("=" * 75)
    print(f"• Student / Annotator : {agent_report['annotator_name']}")
    print(f"• Total Annotations   : {agent_report['total_audited']}")
    print(f"• Quality Score       : {agent_report['quality_score']}/100")
    print(f"• Decision Status     : {agent_report['decision_label']}")
    print(f"• Issue Rate (%)      : {analytics_mart['issue_rate']}%")
    print(f"• Annotator Risk Tier : {analytics_mart['annotator_risk']['risk_badge']}")
    print(f"• Rule Errors Found   : {len(rule_errors)}")
    print(f"• Missing Occluded    : {len(missing_objs)}")
    print(f"• CVAT Reviewer Issues: {len(cvat_issues)}")
    print(f"• Report Saved At     : {Path(report_path).resolve()}")
    print("=" * 75)
    print("🎉 CVAT QC Audit Completed Successfully!")

if __name__ == "__main__":
    main()
