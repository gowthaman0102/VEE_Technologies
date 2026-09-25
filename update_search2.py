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
    '<FilterInput label="Risk Level" value={riskLevel} placeholder="e.g. high" onChange={onRiskLevelChange} icon={Shield} />\n              <FilterInput label="Publisher Country" value={publisherCountry} placeholder="e.g. US, IN, unknown" onChange={setPublisherCountry} icon={Shield} />'
)

code = code.replace(
    '{riskLevel.trim() && (',
    '{publisherCountry.trim() && (\n                  <button type="button" onClick={() => setPublisherCountry("")} className="inline-flex items-center gap-1 rounded-full border border-primary-border bg-primary-soft px-2.5 py-1 text-xs text-primary hover:bg-primary hover:text-white transition-colors">\n                    Country: {publisherCountry} <X size={11} aria-hidden="true" />\n                  </button>\n                )}\n                {riskLevel.trim() && ('
)

with open('frontend/src/components/search-page-client.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
