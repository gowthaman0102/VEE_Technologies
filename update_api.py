import sys
import re

with open('frontend/src/lib/api.ts', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(r'publisher_name: string;', 'publisher_name: string;\n  publisher_country_code?: string | null;\n  publisher_country_name?: string | null;', code)

# Add country distribution schema
code = code.replace(
    'comparison: Record<string, number>;',
    'comparison: Record<string, number>;\n  publisher_country_distribution?: Array<{ country_code: string | null, country_name: string | null, article_count: number }>;'
)

with open('frontend/src/lib/api.ts', 'w', encoding='utf-8') as f:
    f.write(code)
