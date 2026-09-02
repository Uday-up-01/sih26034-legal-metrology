from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_text_pipeline_all_three_fields_present():
    payload = {
        "text": "Maximum Retail Price: ₹40\nNet Weight: 100 g\nManufactured by: Demo Foods Pvt Ltd"
    }
    response = client.post("/api/analyze-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "COMPLIANT_FOR_PROTOTYPE_RULESET"
    assert {x["field_name"] for x in data["extracted_fields"]} >= {"mrp", "net_quantity", "manufacturer"}
