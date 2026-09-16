import React from 'react';

interface Finding {
  id: string;
  file: string;
  line: number;
  end_line: number;
  severity: string;
  rule_id: string;
  message: string;
  evidence: string;
  reachability_status: string;
  reachability_confidence: number | null;
  reachability_confidence_basis?: number | string | null;
  l2_reasoning: {
    is_vulnerable: boolean | null;
    verdict?: string;
    provider?: string;
    confidence: number | null;
    reasoning: string;
    attack_scenario: string;
    fix_suggestion: string;
  };
  l3_validation: {
    validated: boolean | null;
    exploit_possible: boolean | null;
    confidence: number | null;
    evidence: string;
    recommended_fix: string;
  };
}

interface DetailPanelProps {
  finding: Finding;
}

function DetailPanel({ finding }: DetailPanelProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return '#dc3545';
      case 'HIGH':
        return '#fd7e14';
      case 'MEDIUM':
        return '#ffc107';
      default:
        return '#6c757d';
    }
  };

  const formatConfidence = (confidence: number | null) => typeof confidence === 'number' && Number.isFinite(confidence) ? `${Math.round(confidence * 100)}%` : 'Not available';
  const getConfidenceColor = (confidence: number | null) => {
    if (confidence == null || !Number.isFinite(confidence)) return '#6c757d';
    if (confidence >= 0.8) return '#1b5e20';
    if (confidence >= 0.6) return '#ef6c00';
    return '#b71c1c';
  };

  return (
    <div style={{ marginTop: 20, fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ color: getSeverityColor(finding.severity) }}>Finding Details - {finding.severity}</h2>

      <div style={{ backgroundColor: '#f9f9f9', padding: 15, borderRadius: 8, marginBottom: 15 }}>
        <h3>Basic Information</h3>
        <p><strong>File:</strong> {finding.file}</p>
        <p><strong>Line:</strong> {finding.line} - {finding.end_line}</p>
        <p><strong>Rule ID:</strong> {finding.rule_id}</p>
        <p><strong>Message:</strong> {finding.message}</p>
        <p><strong>Evidence:</strong> {finding.evidence}</p>
        <p>
          <strong>Reachability:</strong> {finding.reachability_status}{' '}
          <span style={{ color: getConfidenceColor(finding.reachability_confidence) }}>
            ({formatConfidence(finding.reachability_confidence)}{typeof finding.reachability_confidence_basis === 'string' ? `; heuristic: ${finding.reachability_confidence_basis}` : ''})
          </span>
        </p>
      </div>

      <div style={{ backgroundColor: '#e8f4fd', padding: 15, borderRadius: 8, marginBottom: 15, border: '2px solid #2196F3' }}>
        <h3>L2 Reasoning</h3>
        <p>
          <strong>Assessment:</strong>{' '}
          <span style={{ color: finding.l2_reasoning.is_vulnerable == null ? '#6c757d' : finding.l2_reasoning.is_vulnerable ? '#d32f2f' : '#2e7d32', fontWeight: 'bold' }}>
            {finding.l2_reasoning.verdict || 'needs_review'}
          </span>
        </p>
        <p><strong>Provider:</strong> {finding.l2_reasoning.provider || 'unknown'} — assessment, not proof of exploitability</p>
        <p>
          <strong>Confidence:</strong>{' '}
          <span style={{ color: getConfidenceColor(finding.l2_reasoning.confidence) }}>
            {formatConfidence(finding.l2_reasoning.confidence)}
          </span>
        </p>
        <p><strong>Reasoning:</strong></p>
        <div style={{ backgroundColor: 'white', padding: 10, borderRadius: 5, margin: '10px 0' }}>
          {finding.l2_reasoning.reasoning || 'No L2 reasoning text available.'}
        </div>
        <p><strong>Attack Scenario:</strong></p>
        <div style={{ backgroundColor: '#ffebee', padding: 10, borderRadius: 5, margin: '10px 0', border: '1px solid #ff4444' }}>
          {finding.l2_reasoning.attack_scenario || 'No attack scenario generated yet.'}
        </div>
        <p><strong>Fix Suggestion:</strong></p>
        <div style={{ backgroundColor: '#e8f5e8', padding: 10, borderRadius: 5, margin: '10px 0', border: '1px solid #44ff44' }}>
          {finding.l2_reasoning.fix_suggestion || 'No fix suggestion available.'}
        </div>
      </div>

      <div style={{ backgroundColor: '#fff3e0', padding: 15, borderRadius: 8, marginBottom: 15, border: '2px solid #ff9800' }}>
        <h3>L3 Validation</h3>
        <p>
          <strong>Validated:</strong>{' '}
          <span style={{ color: finding.l3_validation.validated ? '#2e7d32' : '#b71c1c', fontWeight: 'bold' }}>
            {finding.l3_validation.validated == null ? 'NOT RUN / PENDING' : finding.l3_validation.validated ? 'YES' : 'NOT CONFIRMED'}
          </span>
        </p>
        <p>
          <strong>Exploit Possible:</strong>{' '}
          <span style={{ color: finding.l3_validation.exploit_possible == null ? '#6c757d' : finding.l3_validation.exploit_possible ? '#d32f2f' : '#2e7d32', fontWeight: 'bold' }}>
            {finding.l3_validation.exploit_possible == null ? 'UNKNOWN' : finding.l3_validation.exploit_possible ? 'INDICATED BY VALIDATOR' : 'NOT DEMONSTRATED'}
          </span>
        </p>
        {finding.l3_validation.exploit_possible && (
          <div style={{ backgroundColor: '#ffebee', padding: 10, borderRadius: 5, margin: '10px 0', border: '1px solid #ff4444' }}>
            <strong>Exploit Details:</strong> This weakness appears practically exploitable and should be fixed first.
          </div>
        )}
        <p>
          <strong>Confidence:</strong>{' '}
          <span style={{ color: getConfidenceColor(finding.l3_validation.confidence) }}>
            {formatConfidence(finding.l3_validation.confidence)}
          </span>
        </p>
        <p><strong>Evidence:</strong></p>
        <div style={{ backgroundColor: 'white', padding: 10, borderRadius: 5, margin: '10px 0' }}>
          {finding.l3_validation.evidence || 'No L3 evidence available.'}
        </div>
        <p><strong>Recommended Fix:</strong></p>
        <div style={{ backgroundColor: '#e8f5e8', padding: 10, borderRadius: 5, margin: '10px 0', border: '1px solid #44ff44' }}>
          {finding.l3_validation.recommended_fix || 'No L3 fix recommendation available.'}
        </div>
      </div>
    </div>
  );
}

export default DetailPanel;
