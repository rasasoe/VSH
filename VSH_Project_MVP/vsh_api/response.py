"""Pure presentation adapter: never equate risk priority with severity."""
from collections import Counter
import math


def confidence(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0 <= number <= 1 else None


def normalize_response(result: dict, mode: str, target: str) -> dict:
    reasoning = {r['linked_vuln_id']: r for r in result.get('l2_reasoning_results', []) if r.get('linked_vuln_id')}
    findings = []
    for v in result.get('vuln_records', []):
        r = reasoning.get(v.get('vuln_id'), {})
        verdict = r.get('verdict', v.get('reasoning_verdict', 'needs_review'))
        validated = v.get('l3_validated')
        findings.append({
            'id': v.get('vuln_id'), 'file': v.get('file_path'),
            'line': v.get('line_number'), 'end_line': v.get('end_line_number', v.get('line_number')),
            'severity': str(v.get('severity') or 'UNKNOWN').upper(), 'rule_id': v.get('rule_id'),
            'message': v.get('evidence'), 'evidence': v.get('evidence'),
            'reachability_status': v.get('reachability_status'),
            'reachability_confidence': confidence(v.get('reachability_confidence')),
            'reachability_confidence_basis': v.get('reachability_confidence'),
            'l2_reasoning': {
                'verdict': verdict, 'provider': r.get('provider_name', 'unknown'),
                'is_vulnerable': True if verdict == 'likely_vulnerable' else False if verdict == 'not_vulnerable' else None,
                'confidence': confidence(r.get('confidence')),
                'reasoning': r.get('reasoning', ''), 'attack_scenario': r.get('attack_scenario', ''),
                'fix_suggestion': r.get('secure_fix_guidance', v.get('fix_suggestion', '')),
            },
            'l3_validation': {
                'validated': validated if isinstance(validated, bool) else None,
                'exploit_possible': v.get('exploit_possible') if isinstance(validated, bool) else None,
                'confidence': confidence(v.get('l3_confidence')) if isinstance(validated, bool) else None,
                'evidence': v.get('l3_evidence', '') if isinstance(validated, bool) else '',
                'recommended_fix': v.get('l3_recommended_fix', '') if isinstance(validated, bool) else '',
            },
        })
    counts = Counter(f['severity'] for f in findings)
    files = Counter(f['file'] for f in findings if f['file'])
    return {'target': target, 'mode': mode, 'findings': findings, 'summary': {
        'total': len(findings),
        **{level.lower(): counts[level] for level in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO', 'UNKNOWN')},
        'top_risky_files': sorted(files.items(), key=lambda item: (-item[1], item[0]))[:5],
    }}
