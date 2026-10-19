"""Integration test for Hybrid Asset Service and Static Image Serving."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from fastapi.testclient import TestClient

def test_asset_service_integration():
    client = TestClient(app)
    
    # 1. Test GET /api/case/sample
    response = client.get("/api/case/sample")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    print("\n=== SAMPLE CASE ASSET ENRICHMENT TEST ===")
    print("Case Title:", data["title"])
    
    print("\n[Suspects]")
    for s in data["suspects"]:
        img = s.get("image_url")
        print(f"  - [{s['id']}] {s['name']} ({s['occupation']}, {s['age']}yo) -> {img}")
        assert img is not None and "/static/assets/suspects/" in img, f"Invalid suspect image_url: {img}"
        
        # Verify static file can be fetched
        img_resp = client.get(img)
        assert img_resp.status_code == 200, f"Failed to fetch {img}: {img_resp.status_code}"
        assert len(img_resp.content) > 1000, f"Empty or tiny image content for {img}"

    print("\n[Evidences]")
    for ev in data["evidences"]:
        img = ev.get("image_url")
        print(f"  - [{ev['id']}] {ev['title']} ({ev['location']}) -> {img}")
        assert img is not None and "/static/assets/evidences/" in img, f"Invalid evidence image_url: {img}"
        
        # Verify static file can be fetched
        img_resp = client.get(img)
        assert img_resp.status_code == 200, f"Failed to fetch {img}: {img_resp.status_code}"
        assert len(img_resp.content) > 1000, f"Empty or tiny image content for {img}"

    print("\n🎉 ALL ASSET SERVICE TESTS PASSED 100%!")

if __name__ == "__main__":
    test_asset_service_integration()
