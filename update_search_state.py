import sys

with open('frontend/src/components/search-page-client.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'const [riskLevel, setRiskLevel] = useState("");',
    'const [riskLevel, setRiskLevel] = useState("");\n  const [publisherCountry, setPublisherCountry] = useState("");'
)

with open('frontend/src/components/search-page-client.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
