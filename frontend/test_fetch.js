const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function testFetch() {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/overview`);
    const data = await res.json();
    console.log("Success:", data);
  } catch (err) {
    console.error("Error:", err);
  }
}

testFetch();
