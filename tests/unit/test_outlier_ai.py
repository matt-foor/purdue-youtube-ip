from src.services import outlier_ai


def test_extract_json_block_handles_fenced_payload() -> None:
    text = """
    Here is the report:
    ```json
    {"executive_headline":"Fast Movers","key_takeaway":"A few ideas are breaking out."}
    ```
    """

    parsed = outlier_ai._extract_json_block(text)

    assert parsed == {
        "executive_headline": "Fast Movers",
        "key_takeaway": "A few ideas are breaking out.",
    }


def test_report_from_payload_maps_new_bento_fields() -> None:
    payload = {
        "executive_headline": "Fast Movers",
        "key_takeaway": "A few ideas are breaking out.",
        "confidence_label": "Medium",
        "confidence_notes": ["Language confidence is mixed."],
        "breakout_themes": [{"title": "Theme", "body": "Reason", "support": "Signal"}],
        "title_patterns": [{"title": "Pattern", "body": "Hook", "support": "Evidence"}],
        "repeatable_angles": [{"title": "Angle", "body": "What to make", "support": "Why"}],
        "notable_anomalies": [{"title": "Anomaly", "body": "Odd result", "support": "Caveat"}],
        "next_steps": ["Test a shorter hook"],
        "warnings": ["Public data only"],
    }

    report = outlier_ai._report_from_payload("gemini", "gemini-2.5-flash", payload, raw_text="")

    assert report.executive_headline == "Fast Movers"
    assert report.confidence_notes == ("Language confidence is mixed.",)
    assert report.breakout_themes[0].title == "Theme"
    assert report.notable_anomalies[0].title == "Anomaly"
    assert report.next_steps == ("Test a shorter hook",)
    assert report.warnings == ("Public data only",)


def test_fallback_report_sets_low_confidence_notice() -> None:
    report = outlier_ai._fallback_report("openai", "gpt-4o-mini", "Unstructured answer")

    assert report.confidence_label == "Low"
    assert report.confidence_notes
    assert report.warnings
    assert report.raw_fallback == "Unstructured answer"
