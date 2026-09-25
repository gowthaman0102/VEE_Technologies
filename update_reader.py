import sys

with open('frontend/src/components/article-reader-modal.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '<span className="font-semibold uppercase tracking-wider">{article.publisher_name}</span>',
    '<span className="font-semibold uppercase tracking-wider">{article.publisher_name}{article.publisher_country_name && ` · ${article.publisher_country_name}`}</span>'
)

with open('frontend/src/components/article-reader-modal.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
