const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function testFetchAll() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 7);
  const endStr = end.toISOString();
  const startStr = start.toISOString();

  const urls = [
    `${API_BASE_URL}/dashboard/overview`,
    `${API_BASE_URL}/dashboard/intelligence?limit=6`,
    `${API_BASE_URL}/companies/active`,
    `${API_BASE_URL}/analytics/overview?start=${startStr}&end=${endStr}`,
    `${API_BASE_URL}/analytics/events?start=${startStr}&end=${endStr}`,
    `${API_BASE_URL}/analytics/sources?start=${startStr}&end=${endStr}`,
    `${API_BASE_URL}/analytics/articles/trend?start=${startStr}&end=${endStr}&bucket=day`,
    `${API_BASE_URL}/analytics/sentiment/trend?start=${startStr}&end=${endStr}`,
    `${API_BASE_URL}/analytics/business-impact?start=${startStr}&end=${endStr}`
  ];

  for (const url of urls) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        console.log(`Failed: ${url} - Status: ${res.status}`);
      } else {
        console.log(`OK: ${url}`);
      }
    } catch (err) {
      console.log(`Error: ${url}`, err);
    }
  }
}

testFetchAll();
