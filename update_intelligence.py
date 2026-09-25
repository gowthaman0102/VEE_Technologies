import sys

with open('frontend/src/components/intelligence-page-client.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'const [sourceName, setSourceName] = useState("");',
    'const [sourceName, setSourceName] = useState("");\n  const [publisherCountry, setPublisherCountry] = useState("");'
)

code = code.replace(
    'if (sourceName.trim()) {\n      filters.source_name = sourceName.trim();\n    }',
    'if (sourceName.trim()) {\n      filters.source_name = sourceName.trim();\n    }\n    if (publisherCountry.trim()) {\n      filters.publisher_country_code = publisherCountry.trim();\n    }'
)

code = code.replace(
    'setSourceName("");',
    'setSourceName("");\n    setPublisherCountry("");'
)

code = code.replace(
    'sourceName && { label: `Source: ${sourceName}`, clear: () => setSourceName("") },',
    'sourceName && { label: `Source: ${sourceName}`, clear: () => setSourceName("") },\n    publisherCountry && { label: `Country: ${publisherCountry}`, clear: () => setPublisherCountry("") },'
)

code = code.replace(
    '<FilterInput label="Source" value={sourceName} placeholder="e.g. reuters" onChange={setSourceName} />',
    '<FilterInput label="Source" value={sourceName} placeholder="e.g. reuters" onChange={setSourceName} />\n              <FilterInput label="Publisher Country" value={publisherCountry} placeholder="e.g. US, IN, unknown" onChange={(v: string) => setPublisherCountry(v)} />'
)

with open('frontend/src/components/intelligence-page-client.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
