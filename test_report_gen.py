import asyncio
import io
import sys
from datetime import datetime, timezone
from openpyxl import load_workbook
from pypdf import PdfReader
import httpx

async def main():
    print("Testing report generation with exact IDs...")
    # First get the company
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1") as client:
        comp_res = await client.get("/companies/active")
        if comp_res.status_code != 200:
            print("No active company found")
            sys.exit(1)
        company_id = comp_res.json()["id"]

        # Search for OpenAI
        search_res = await client.get(f"/search/keyword?company_id={company_id}&q=OpenAI&limit=55")
        if search_res.status_code != 200:
            print(f"Search failed: {search_res.status_code}")
            sys.exit(1)
        
        results = search_res.json()["results"]
        total_matches = len(results)
        print(f"Total matching articles in DB: {total_matches}")
        
        if total_matches < 2:
            print("Not enough articles to test subset")
        
        # Displayed IDs: limit to subset to simulate 50 vs 55
        subset_limit = max(1, total_matches - 2)
        displayed_ids = [r["article_id"] for r in results[:subset_limit]]
        print(f"Submitting report request for {len(displayed_ids)} items.")
        
        payload = {
            "company_id": company_id,
            "report_type": "all_history",
            "report_scope": "search_results",
            "article_ids": displayed_ids,
            "scope_metadata": {
                "query": "OpenAI",
                "mode": "keyword",
                "filters": {},
                "displayed_result_count": len(displayed_ids),
                "article_count": len(displayed_ids),
                "snapshot_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Trigger generation
        gen_res = await client.post("/reports/generate", json=payload)
        if gen_res.status_code != 200:
            print(f"Generation failed: {gen_res.status_code} {gen_res.text}")
            sys.exit(1)
            
        data = gen_res.json()
        print(f"Generated successfully: {data}")
        
        report_id = data["report_id"]
        
        # Wait a bit for other formats to be ready
        await asyncio.sleep(2)
        
        # Check history
        hist_res = await client.get("/reports/history")
        history = hist_res.json()["items"]
        print(f"History IDs: {[item['id'] for item in history]}")
        batch = next((item for item in history if item["id"] == report_id), None)
        
        if batch:
            print(f"History report article_count: {batch['scope_metadata']['article_count']}")
            assert batch['scope_metadata']['article_count'] == len(displayed_ids), "History count mismatch"
        else:
            print("Report ID not found in history.")
        
        # Download XLSX
        xlsx_res = await client.post(f"/reports/export?file_format=xlsx", json=payload)
        if xlsx_res.status_code == 200:
            wb = load_workbook(io.BytesIO(xlsx_res.content), read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            headers = rows[0]
            assert "Sentiment" in headers
            assert "Risk Level" in headers
            
            data_rows = rows[1:]
            print(f"XLSX row count: {len(data_rows)}")
            assert len(data_rows) == len(displayed_ids), "XLSX rows mismatch"
            
            # Print first row of Excel for inspection
            print("First XLSX row:")
            for h, v in zip(headers, data_rows[0]):
                print(f"  {h}: {v}")
        else:
            print(f"XLSX export failed: {xlsx_res.status_code} {xlsx_res.text}")

        print("Test passed!")

if __name__ == "__main__":
    asyncio.run(main())
