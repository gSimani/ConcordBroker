"""
Field Discovery Agent
Scans website components to discover all data fields and their IDs
"""

import os
import re
import json
from typing import Dict, List, Set, Tuple
from pathlib import Path
import ast
from datetime import datetime

class FieldDiscoveryAgent:
    """
    Agent responsible for discovering all data fields in the website
    """
    
    def __init__(self):
        self.discovered_fields = {}
        self.component_map = {}
        self.id_patterns = {}
        self.field_locations = {}
        self.web_root = Path("apps/web/src")
        
    def scan_all_components(self) -> Dict:
        """
        Scan all React components for data fields
        """
        print("[Field Discovery Agent] Starting component scan...")
        
        # File patterns to scan
        patterns = ["**/*.tsx", "**/*.jsx", "**/*.ts", "**/*.js"]
        
        for pattern in patterns:
            for file_path in self.web_root.glob(pattern):
                self._scan_file(file_path)
        
        return self.discovered_fields
    
    def _scan_file(self, file_path: Path) -> None:
        """
        Scan a single file for data fields
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract component name
            component_name = file_path.stem
            
            # Find all elements with IDs
            id_matches = re.findall(r'id=["\']([^"\']+)["\']', content)
            
            # Find all data field references
            data_refs = self._extract_data_references(content)
            
            # Find all Supabase field references
            supabase_refs = self._extract_supabase_references(content)
            
            # Store discovered fields
            if id_matches or data_refs or supabase_refs:
                self.discovered_fields[str(file_path)] = {
                    'component': component_name,
                    'ids': id_matches,
                    'data_fields': data_refs,
                    'supabase_fields': supabase_refs,
                    'path': str(file_path.relative_to(self.web_root))
                }
                
        except Exception as e:
            print(f"[Field Discovery Agent] Error scanning {file_path}: {e}")
    
    def _extract_data_references(self, content: str) -> List[str]:
        """
        Extract all data field references from component
        """
        fields = []
        
        # Pattern for data access (e.g., data.phy_addr1, property.owner_name)
        patterns = [
            r'data\.(\w+)',
            r'property\.(\w+)',
            r'row\.get\(["\'](\w+)["\']\)',
            r'\{(\w+)\}',  # Simple variable references
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            fields.extend(matches)
        
        # Common field names to look for
        common_fields = [
            'phy_addr1', 'phy_city', 'phy_zipcd', 'owner_name',
            'just_value', 'taxable_value', 'land_value',
            'total_living_area', 'year_built', 'sale_price'
        ]
        
        for field in common_fields:
            if field in content:
                fields.append(field)
        
        return list(set(fields))
    
    def _extract_supabase_references(self, content: str) -> List[str]:
        """
        Extract Supabase table and field references
        """
        refs = []
        
        # Patterns for Supabase queries
        patterns = [
            r'supabase\.table\(["\'](\w+)["\']\)',
            r'\.select\(["\']([^"\']+)["\']\)',
            r'\.eq\(["\'](\w+)["\']\s*,',
            r'\.ilike\(["\'](\w+)["\']\s*,',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            refs.extend(matches)
        
        return list(set(refs))
    
    def generate_field_map(self) -> Dict:
        """
        Generate a comprehensive field mapping
        """
        field_map = {
            'discovered_at': datetime.now().isoformat(),
            'total_components': len(self.discovered_fields),
            'components': {},
            'all_ids': [],
            'all_data_fields': set(),
            'all_supabase_fields': set()
        }
        
        for file_path, data in self.discovered_fields.items():
            component = data['component']
            field_map['components'][component] = {
                'path': data['path'],
                'ids': data['ids'],
                'data_fields': data['data_fields'],
                'supabase_fields': data['supabase_fields']
            }
            
            field_map['all_ids'].extend(data['ids'])
            field_map['all_data_fields'].update(data['data_fields'])
            field_map['all_supabase_fields'].update(data['supabase_fields'])
        
        # Convert sets to lists for JSON serialization
        field_map['all_data_fields'] = list(field_map['all_data_fields'])
        field_map['all_supabase_fields'] = list(field_map['all_supabase_fields'])
        
        return field_map
    
    def find_missing_ids(self) -> List[str]:
        """
        Find components that should have IDs but don't
        """
        missing = []
        
        for file_path, data in self.discovered_fields.items():
            if data['data_fields'] and not data['ids']:
                missing.append({
                    'component': data['component'],
                    'path': data['path'],
                    'data_fields': data['data_fields']
                })
        
        return missing
    
    def validate_id_convention(self) -> Dict:
        """
        Validate that IDs follow the naming convention
        """
        violations = []
        valid_patterns = [
            r'^[a-z]+-[a-z]+-[a-z]+(-\d+)?$',  # Static pattern
            r'^property-card-\d+-\w+$',  # Dynamic property card
            r'^[a-z]+-filter-[a-z]+-\w+$',  # Filter pattern
            r'^property-tab-[a-z]+-\w+$',  # Tab pattern
        ]
        
        for file_path, data in self.discovered_fields.items():
            for id_value in data['ids']:
                valid = any(re.match(pattern, id_value) for pattern in valid_patterns)
                if not valid:
                    violations.append({
                        'component': data['component'],
                        'id': id_value,
                        'suggestion': self._suggest_id_name(id_value, data['component'])
                    })
        
        return {
            'total_ids': sum(len(d['ids']) for d in self.discovered_fields.values()),
            'violations': violations,
            'violation_count': len(violations)
        }
    
    def _suggest_id_name(self, current_id: str, component: str) -> str:
        """
        Suggest a proper ID name based on convention
        """
        # Convert to kebab-case
        suggested = re.sub(r'([A-Z])', r'-\1', current_id).lower()
        suggested = re.sub(r'[^a-z0-9-]', '-', suggested)
        suggested = re.sub(r'-+', '-', suggested).strip('-')
        
        # Add component prefix if missing
        if not suggested.startswith(component.lower()):
            suggested = f"{component.lower()}-{suggested}"
        
        return suggested
    
    def save_discovery_report(self, output_path: str = "field_discovery_report.json") -> None:
        """
        Save the discovery report to a file
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'field_map': self.generate_field_map(),
            'missing_ids': self.find_missing_ids(),
            'id_validation': self.validate_id_convention()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[Field Discovery Agent] Report saved to {output_path}")
        
        # Print summary
        print(f"\n[Field Discovery Agent] Summary:")
        print(f"  - Components scanned: {report['field_map']['total_components']}")
        print(f"  - Total IDs found: {len(report['field_map']['all_ids'])}")
        print(f"  - Data fields found: {len(report['field_map']['all_data_fields'])}")
        print(f"  - Components missing IDs: {len(report['missing_ids'])}")
        print(f"  - ID convention violations: {report['id_validation']['violation_count']}")
    
    def get_field_location(self, field_name: str) -> List[Dict]:
        """
        Find all locations where a specific field is used
        """
        locations = []
        
        for file_path, data in self.discovered_fields.items():
            if field_name in data['data_fields'] or field_name in data['supabase_fields']:
                locations.append({
                    'component': data['component'],
                    'path': data['path'],
                    'ids_in_component': data['ids']
                })
        
        return locations


def main():
    """
    Run the Field Discovery Agent
    """
    agent = FieldDiscoveryAgent()
    
    print("[Field Discovery Agent] Initializing...")
    print("[Field Discovery Agent] Scanning website components...")
    
    # Scan all components
    fields = agent.scan_all_components()
    
    # Generate and save report
    agent.save_discovery_report()
    
    # Find specific field locations
    important_fields = ['phy_addr1', 'owner_name', 'just_value', 'land_value']
    
    print("\n[Field Discovery Agent] Field Location Analysis:")
    for field in important_fields:
        locations = agent.get_field_location(field)
        if locations:
            print(f"\n  Field '{field}' found in:")
            for loc in locations:
                print(f"    - {loc['component']} ({loc['path']})")


if __name__ == "__main__":
    main()