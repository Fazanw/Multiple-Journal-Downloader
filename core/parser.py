import rispy
import bibtexparser
import re
import os
import csv
import json

def extract_doi(text_list):
    """Helper to extract a single DOI from a string or list of strings"""
    if not isinstance(text_list, list):
        text_list = [text_list]
        
    doi_pattern = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)
    
    for text in text_list:
        if not text: continue
        match = doi_pattern.search(str(text))
        if match:
            return match.group(0).rstrip('.,:;')
    return None

def extract_all_dois_from_text(text):
    """Helper to extract ALL DOIs found in a giant block of text"""
    doi_pattern = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)
    return [m.rstrip('.,:;') for m in doi_pattern.findall(text)]

def parse_file(filepath: str) -> list[dict]:
    """
    Parses various reference files (.ris, .bib, .csv, .json, .txt, .xml).
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.ris':
        return parse_ris(filepath)
    elif ext == '.bib':
        return parse_bib(filepath)
    elif ext == '.csv':
        return parse_csv(filepath)
    elif ext == '.json':
        return parse_json(filepath)
    elif ext in ['.txt', '.xml']:
        return parse_raw_text(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def parse_ris(filepath: str) -> list[dict]:
    extracted = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            entries = rispy.load(f)
            for entry in entries:
                fields_to_check = [entry.get('doi', ''), *entry.get('urls', [])]
                doi = extract_doi(fields_to_check)
                            
                extracted.append({
                    "title": entry.get("title", entry.get("primary_title", "Unknown Title")),
                    "authors": entry.get("authors", []),
                    "year": entry.get("year", ""),
                    "doi": doi,
                    "status": "Pending"
                })
    except Exception as e:
        print(f"Error parsing RIS: {e}")
    return extracted

def parse_bib(filepath: str) -> list[dict]:
    extracted = []
    try:
        library = bibtexparser.parse_file(filepath)
        for entry in library.entries:
            fields_to_check = []
            if 'doi' in entry: fields_to_check.append(entry['doi'])
            if 'url' in entry: fields_to_check.append(entry['url'])
                
            doi = extract_doi(fields_to_check)
            title = entry.get('title', 'Unknown Title')
            year = entry.get('year', '')
            
            extracted.append({
                "title": str(title),
                "authors": [],
                "year": str(year),
                "doi": doi,
                "status": "Pending"
            })
    except Exception as e:
        print(f"Error parsing BibTeX: {e}")
    return extracted

def parse_csv(filepath: str) -> list[dict]:
    extracted = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Combine all values in the row to find a DOI using regex
                row_text = " ".join(str(v) for v in row.values() if v)
                doi = extract_doi([row_text])
                
                title = row.get('Title', row.get('title', f"Paper {len(extracted)+1}"))
                
                if doi:
                    extracted.append({
                        "title": title,
                        "authors": [],
                        "year": "",
                        "doi": doi,
                        "status": "Pending"
                    })
    except Exception as e:
        print(f"Error parsing CSV: {e}")
    return extracted

def parse_json(filepath: str) -> list[dict]:
    extracted = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    item_str = json.dumps(item)
                    doi = extract_doi([item_str])
                    title = item.get('title', item.get('Title', f"Paper {len(extracted)+1}")) if isinstance(item, dict) else f"Paper {len(extracted)+1}"
                    if doi:
                        extracted.append({
                            "title": title,
                            "authors": [],
                            "year": "",
                            "doi": doi,
                            "status": "Pending"
                        })
    except Exception as e:
        print(f"Error parsing JSON: {e}")
    return extracted

def parse_raw_text(filepath: str) -> list[dict]:
    extracted = []
    try:
        seen = set()
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                dois = extract_all_dois_from_text(line)
                for doi in dois:
                    if doi not in seen:
                        seen.add(doi)
                        extracted.append({
                            "title": f"Extracted Document ({doi})",
                            "authors": [],
                            "year": "",
                            "doi": doi,
                            "status": "Pending"
                        })
    except Exception as e:
        print(f"Error parsing raw text/xml: {e}")
    return extracted
