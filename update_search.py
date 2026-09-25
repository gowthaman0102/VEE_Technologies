import sys

with open('frontend/src/components/search-page-client.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'const [riskLevel, setRiskLevel] = useState("");',
    'const [riskLevel, setRiskLevel] = useState("");\n  const [publisherCountry, setPublisherCountry] = useState("");'
)

code = code.replace(
    'if (riskLevel.trim()) {\n      filters.risk_level = riskLevel.trim();\n    }',
    'if (riskLevel.trim()) {\n      filters.risk_level = riskLevel.trim();\n    }\n    if (publisherCountry.trim()) {\n      filters.publisher_country_code = publisherCountry.trim();\n    }'
)

code = code.replace(
    'setRiskLevel("");',
    'setRiskLevel("");\n    setPublisherCountry("");'
)

code = code.replace(
    'riskLevel && { label: `Risk: ${riskLevel}`, clear: () => setRiskLevel("") },',
    'riskLevel && { label: `Risk: ${riskLevel}`, clear: () => setRiskLevel("") },\n    publisherCountry && { label: `Country: ${publisherCountry}`, clear: () => setPublisherCountry("") },'
)

code = code.replace(
    '<FilterInput label="Risk Level" value={riskLevel} placeholder="e.g. high" onChange={onRiskLevelChange} icon={Shield} />',
    '<FilterInput label="Risk Level" value={riskLevel} placeholder="e.g. high" onChange={onRiskLevelChange} icon={Shield} />\n              <FilterInput label="Publisher Country" value={publisherCountry} placeholder="e.g. US, IN, unknown" onChange={(v) => setPublisherCountry(v)} icon={FileText} />'
)

with open('frontend/src/components/search-page-client.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
