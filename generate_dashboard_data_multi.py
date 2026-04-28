"""
generate_dashboard_data_multi.py
===============================

This script takes one or more research JSON files produced by
``multi_account_research.py`` and converts them into a consolidated
dashboard data structure. The resulting JSON file (by default
``dashboard_multi_data.json``) contains a list of accounts with
summarised metrics, top entities (opportunities), intelligence gaps
and other signals. The format is designed to work with the
``multi_dashboard.html`` front‑end provided in this project.

Example usage:

```
python generate_dashboard_data_multi.py research_schneider_electric_20260428T150000Z.json \
    research_siemens_20260428T150010Z.json research_abb_20260428T150020Z.json

# or, to generate data from all research files in the current directory:
python generate_dashboard_data_multi.py
```

If no arguments are provided, the script will search the current
directory for files matching ``research_*.json`` and use all of them.

Dependencies: Standard library only.
"""

import json
import glob
import os
import sys
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any


def load_research_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_account_name_from_filename(filename: str) -> str:
    """Derive the account (company) name from a research file name."""
    # Assumes filename pattern: research_<company>_<timestamp>.json
    base = os.path.basename(filename)
    parts = base.split('_')
    # join all parts except the first and last into a company name
    # e.g. research_schneider_electric_20260428T123456Z.json -> schneider electric
    if len(parts) < 3:
        return base
    company_parts = parts[1:-1]
    company_name = ' '.join(company_parts)
    return company_name.title()


def summarise_entities(articles: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """Return a list of the top entities by frequency across all articles."""
    counter = Counter()
    for art in articles:
        for ent in art.get('entities', []):
            counter[ent] += 1
    top_entities = counter.most_common(top_n)
    # Convert to list of dicts for easier consumption in the UI
    return [{"name": name, "count": count} for name, count in top_entities]


def summarise_account(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute summary metrics and extract top entities from a research dataset."""
    articles = data.get('articles', [])
    entities = set()
    for art in articles:
        for ent in art.get('entities', []):
            entities.add(ent)
    intel_gaps = data.get('intel_gaps', {})
    summary = {
        'last_update': data.get('timestamp'),
        'num_articles': len(articles),
        'num_entities': len(entities),
        'num_intel_gaps': len(intel_gaps),
        'top_entities': summarise_entities(articles, top_n=5),
        'intel_gaps': intel_gaps,
        'github_repos': data.get('github_repos', []),
        'youtube_videos': data.get('youtube_videos', []),
        'podcasts': data.get('podcasts', []),
        'case_studies': data.get('case_studies', [])
    }
    return summary


def main() -> None:
    # Determine which research files to process
    if len(sys.argv) > 1:
        research_files = sys.argv[1:]
    else:
        research_files = sorted(glob.glob('research_*.json'))
        if not research_files:
            print("No research files found. Please run multi_account_research.py first.")
            sys.exit(1)

    accounts_data = []
    last_updated = None

    for filepath in research_files:
        try:
            data = load_research_file(filepath)
        except Exception as e:
            print(f"Failed to load {filepath}: {e}")
            continue
        account_name = extract_account_name_from_filename(filepath)
        summary = summarise_account(data)
        accounts_data.append({
            'account': account_name,
            'data_file': filepath,
            **summary
        })
        # Track the most recent update across all accounts
        ts = summary.get('last_update')
        if ts:
            try:
                dt = datetime.strptime(ts, "%Y%m%dT%H%M%SZ")
            except Exception:
                dt = None
            if dt and (last_updated is None or dt > last_updated):
                last_updated = dt

    # Sort accounts alphabetically for stable ordering
    accounts_data.sort(key=lambda a: a['account'])
    dashboard_data = {
        'last_updated': last_updated.strftime("%Y-%m-%d %H:%M:%SZ") if last_updated else None,
        'accounts': accounts_data
    }
    # Write to file
    output_file = 'dashboard_multi_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=2)
    print(f"Saved combined dashboard data to {output_file}")


if __name__ == '__main__':
    main()
