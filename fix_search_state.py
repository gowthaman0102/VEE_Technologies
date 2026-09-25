import sys

with open('frontend/src/components/search-page-client.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
seen = set()
for line in lines:
    if 'const [publisherCountry, setPublisherCountry]' in line:
        if 'publisherCountry' in seen:
            continue
        seen.add('publisherCountry')
    new_lines.append(line)

with open('frontend/src/components/search-page-client.tsx', 'w', encoding='utf-8') as f:
    f.write("".join(new_lines))
