"""
Report generation for validation results
"""
from typing import List, Dict
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
from .config import config


class ValidationReporter:
    """Generates validation reports in multiple formats"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(
        self,
        validation_results: List[Dict],
        format: str = "all"
    ) -> Dict[str, str]:
        """Generate validation reports in specified format(s)"""

        # Flatten validation data for reporting
        flat_data = self._flatten_validations(validation_results)

        generated_files = {}

        if format in ["excel", "all"]:
            excel_path = self._generate_excel_report(flat_data, validation_results)
            generated_files['excel'] = str(excel_path)

        if format in ["csv", "all"]:
            csv_path = self._generate_csv_report(flat_data)
            generated_files['csv'] = str(csv_path)

        if format in ["json", "all"]:
            json_path = self._generate_json_report(validation_results)
            generated_files['json'] = str(json_path)

        if format in ["markdown", "all"]:
            md_path = self._generate_markdown_report(validation_results)
            generated_files['markdown'] = str(md_path)

        return generated_files

    def _flatten_validations(self, results: List[Dict]) -> List[Dict]:
        """Flatten nested validation results for tabular format"""
        flat_data = []

        for result in results:
            page_url = result.get('page_url', '')
            property_id = result.get('property_id', '')

            for validation in result.get('validations', []):
                flat_data.append({
                    'page_url': page_url,
                    'property_id': property_id,
                    'label': validation.get('label', ''),
                    'displayed_value': validation.get('value', ''),
                    'expected_value': validation.get('expected_value', ''),
                    'db_field': validation.get('db_field', ''),
                    'status': validation.get('status', ''),
                    'confidence': validation.get('confidence', 0),
                    'match_type': validation.get('match_type', ''),
                    'selector': validation.get('selector', ''),
                    'data_type': validation.get('data_type', ''),
                    'pattern_type': validation.get('pattern_type', ''),
                    'issue': validation.get('issue', '')
                })

        return flat_data

    def _generate_excel_report(
        self,
        flat_data: List[Dict],
        full_results: List[Dict]
    ) -> Path:
        """Generate Excel report with multiple sheets"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_report_{timestamp}.xlsx"

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:

            # Sheet 1: All validations
            df_all = pd.DataFrame(flat_data)
            if not df_all.empty:
                df_all.to_excel(writer, sheet_name='All Validations', index=False)

            # Sheet 2: Mismatches only
            df_mismatches = pd.DataFrame([
                row for row in flat_data
                if row['status'] == 'mismatch'
            ])
            if not df_mismatches.empty:
                df_mismatches.to_excel(writer, sheet_name='Mismatches', index=False)

            # Sheet 3: Unmapped fields
            df_unmapped = pd.DataFrame([
                row for row in flat_data
                if row['status'] == 'unmapped'
            ])
            if not df_unmapped.empty:
                df_unmapped.to_excel(writer, sheet_name='Unmapped Fields', index=False)

            # Sheet 4: Summary statistics
            summary_data = self._generate_summary_stats(full_results)
            df_summary = pd.DataFrame([summary_data])
            df_summary.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 5: Field mapping report
            field_mappings = self._generate_field_mapping_report(flat_data)
            df_mappings = pd.DataFrame(field_mappings)
            if not df_mappings.empty:
                df_mappings.to_excel(writer, sheet_name='Field Mappings', index=False)

        return output_path

    def _generate_csv_report(self, flat_data: List[Dict]) -> Path:
        """Generate CSV report"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_results_{timestamp}.csv"

        df = pd.DataFrame(flat_data)
        df.to_csv(output_path, index=False)

        return output_path

    def _generate_json_report(self, results: List[Dict]) -> Path:
        """Generate JSON report"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_results_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return output_path

    def _generate_markdown_report(self, results: List[Dict]) -> Path:
        """Generate Markdown report with fix recommendations"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_report_{timestamp}.md"

        with open(output_path, 'w') as f:
            f.write("# UI Field Validation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Overall summary
            summary = self._generate_summary_stats(results)
            f.write("## Summary\n\n")
            f.write(f"- **Total Pages Validated:** {summary['total_pages']}\n")
            f.write(f"- **Total Fields Checked:** {summary['total_fields']}\n")
            f.write(f"- **Matched:** {summary['total_matched']} ({summary['match_percentage']}%)\n")
            f.write(f"- **Mismatched:** {summary['total_mismatched']}\n")
            f.write(f"- **Unmapped:** {summary['total_unmapped']}\n\n")

            # Mismatches section
            f.write("## Critical Mismatches\n\n")
            for result in results:
                mismatches = [
                    v for v in result.get('validations', [])
                    if v['status'] == 'mismatch'
                ]

                if mismatches:
                    f.write(f"### {result.get('page_url', 'Unknown URL')}\n")
                    f.write(f"**Property ID:** {result.get('property_id', 'N/A')}\n\n")

                    for m in mismatches:
                        f.write(f"- **{m['label']}**\n")
                        f.write(f"  - UI shows: `{m['value']}`\n")
                        f.write(f"  - Database has: `{m['expected_value']}`\n")
                        f.write(f"  - Field: `{m['db_field']}`\n")
                        f.write(f"  - Issue: {m.get('issue', 'Value mismatch')}\n\n")

            # Unmapped fields section
            f.write("## Unmapped Fields\n\n")
            f.write("These labels could not be mapped to database fields:\n\n")

            unmapped_labels = set()
            for result in results:
                for v in result.get('validations', []):
                    if v['status'] == 'unmapped':
                        unmapped_labels.add(v['label'])

            for label in sorted(unmapped_labels):
                f.write(f"- {label}\n")

            f.write("\n")

            # Fix recommendations
            f.write("## Fix Recommendations\n\n")
            recommendations = self._generate_fix_recommendations(results)
            for rec in recommendations:
                f.write(f"### {rec['type']}\n")
                f.write(f"{rec['description']}\n\n")
                if rec.get('code'):
                    f.write("```tsx\n")
                    f.write(rec['code'])
                    f.write("\n```\n\n")

        return output_path

    def _generate_summary_stats(self, results: List[Dict]) -> Dict:
        """Generate summary statistics"""

        total_pages = len(results)
        total_fields = 0
        total_matched = 0
        total_mismatched = 0
        total_unmapped = 0

        for result in results:
            summary = result.get('summary', {})
            total_fields += summary.get('total_fields', 0)
            total_matched += summary.get('matched', 0)
            total_mismatched += summary.get('mismatched', 0)
            total_unmapped += summary.get('unmapped', 0)

        match_percentage = round(
            (total_matched / total_fields * 100) if total_fields > 0 else 0,
            2
        )

        return {
            'total_pages': total_pages,
            'total_fields': total_fields,
            'total_matched': total_matched,
            'total_mismatched': total_mismatched,
            'total_unmapped': total_unmapped,
            'match_percentage': match_percentage
        }

    def _generate_field_mapping_report(self, flat_data: List[Dict]) -> List[Dict]:
        """Generate field mapping analysis"""

        mappings = {}

        for row in flat_data:
            label = row['label']
            db_field = row['db_field']

            if label not in mappings:
                mappings[label] = {
                    'label': label,
                    'db_field': db_field,
                    'occurrences': 0,
                    'confidence': row['confidence'],
                    'match_type': row['match_type']
                }

            mappings[label]['occurrences'] += 1

        return list(mappings.values())

    def _generate_fix_recommendations(self, results: List[Dict]) -> List[Dict]:
        """Generate actionable fix recommendations"""

        recommendations = []

        # Recommendation 1: Fix data mismatches
        mismatches = []
        for result in results:
            for v in result.get('validations', []):
                if v['status'] == 'mismatch':
                    mismatches.append(v)

        if mismatches:
            recommendations.append({
                'type': 'Data Mismatches',
                'description': f'Found {len(mismatches)} fields displaying incorrect data. '
                               'Review the database queries in your components to ensure correct field mapping.',
                'code': self._generate_field_fix_code(mismatches[0]) if mismatches else None
            })

        # Recommendation 2: Add unmapped field mappings
        unmapped = []
        for result in results:
            for v in result.get('validations', []):
                if v['status'] == 'unmapped':
                    unmapped.append(v)

        if unmapped:
            unique_unmapped = {v['label'] for v in unmapped}
            recommendations.append({
                'type': 'Unmapped Fields',
                'description': f'Found {len(unique_unmapped)} labels without database mappings. '
                               'Add these to validation/config.py LABEL_MAPPINGS:',
                'code': self._generate_mapping_code(list(unique_unmapped))
            })

        return recommendations

    def _generate_field_fix_code(self, mismatch: Dict) -> str:
        """Generate code snippet to fix a field mismatch"""

        label = mismatch['label']
        db_field = mismatch['db_field']
        expected = mismatch['expected_value']

        return f"""// Fix for: {label}
// Current value is incorrect
// Should display: {expected}

// Ensure you're using the correct database field:
<div>
  <span className="label">{label}:</span>
  <span className="value">{{propertyData.{db_field}}}</span>
</div>"""

    def _generate_mapping_code(self, unmapped_labels: List[str]) -> str:
        """Generate code to add unmapped field mappings"""

        mappings = []
        for label in unmapped_labels[:5]:  # Show first 5
            snake_case = label.lower().replace(' ', '_')
            mappings.append(f'    "{label.lower()}": "{snake_case}",')

        code = "# Add to LABEL_MAPPINGS in validation/config.py:\n\n"
        code += "LABEL_MAPPINGS = {\n"
        code += "\n".join(mappings)
        code += "\n    # ... add remaining mappings\n}"

        return code
