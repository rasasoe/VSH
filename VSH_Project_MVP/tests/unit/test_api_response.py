import pytest
from vsh_api.response import confidence, normalize_response


def test_severity_cards_do_not_relabel_risk_priorities():
    result = normalize_response({'vuln_records': [
        {'vuln_id': 'a', 'severity': 'HIGH', 'file_path': 'a.py'},
        {'vuln_id': 'b', 'severity': 'CRITICAL', 'file_path': 'a.py'},
    ], 'aggregate_summary': {'risk_distribution': {'P1': 99}}}, 'project', 'fixture')
    assert result['summary']['critical'] == 1
    assert result['summary']['high'] == 1
    assert result['summary']['total'] == 2


def test_l2_is_joined_by_id_and_unknown_l3_is_not_safe():
    result = normalize_response({'vuln_records': [{'vuln_id': 'a', 'evidence': 'L1 evidence', 'reachability_confidence': 'high'}],
        'l2_reasoning_results': [{'linked_vuln_id': 'a', 'verdict': 'needs_review', 'provider_name': 'mock',
                                 'confidence': .4, 'reasoning': 'review this', 'attack_scenario': 'scenario', 'secure_fix_guidance': 'fix'}]}, 'file', 'a.py')
    finding = result['findings'][0]
    assert finding['l2_reasoning']['reasoning'] == 'review this'
    assert finding['l2_reasoning']['provider'] == 'mock'
    assert finding['l2_reasoning']['is_vulnerable'] is None
    assert finding['reachability_confidence'] is None
    assert finding['reachability_confidence_basis'] == 'high'
    assert finding['l3_validation']['validated'] is None
    assert finding['l3_validation']['exploit_possible'] is None
    assert finding['l3_validation']['evidence'] == ''


@pytest.mark.parametrize('value', [None, 'high', float('nan'), float('inf'), -1, 2, True])
def test_invalid_confidence_stays_unknown(value):
    assert confidence(value) is None


@pytest.mark.parametrize('value', [0, .5, 1])
def test_valid_confidence_preserved(value):
    assert confidence(value) == value
