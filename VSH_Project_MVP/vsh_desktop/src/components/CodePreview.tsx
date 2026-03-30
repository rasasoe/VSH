import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface Finding {
  file: string;
  line: number;
  end_line: number;
}

interface CodePreviewProps {
  finding: Finding;
  apiBase: string;
}

function CodePreview({ finding, apiBase }: CodePreviewProps) {
  const [code, setCode] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchCode = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${apiBase}/file/content`, { params: { path: finding.file } });
      setCode(res.data.content);
    } catch {
      setError('Failed to load file content. Please check whether the file still exists.');
    }
    setLoading(false);
  };

  useEffect(() => {
    void fetchCode();
  }, [finding, apiBase]);

  const isVulnerableLine = (lineNum: number) => lineNum >= finding.line && lineNum <= finding.end_line;

  return (
    <div style={{ marginTop: 20, fontFamily: 'Monaco, Consolas, monospace' }}>
      <h2>Code Preview - {finding.file}</h2>
      {loading && <p>Loading code...</p>}
      {error && (
        <div style={{ color: 'red', marginBottom: 10 }}>
          {error}
          <button
            onClick={() => void fetchCode()}
            style={{
              marginLeft: 10,
              padding: '5px 10px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      )}
      <pre
        style={{
          backgroundColor: '#2d3748',
          color: '#e2e8f0',
          padding: 15,
          borderRadius: 8,
          overflow: 'auto',
          maxHeight: 400,
          fontSize: '14px',
          lineHeight: '1.5',
        }}
      >
        {code.split('\n').map((line, idx) => {
          const lineNum = idx + 1;
          const vulnerable = isVulnerableLine(lineNum);
          return (
            <div
              key={idx}
              style={{
                backgroundColor: vulnerable ? '#742a2a' : 'transparent',
                borderLeft: vulnerable ? '4px solid #ff4444' : '4px solid transparent',
                paddingLeft: 10,
                marginLeft: -10,
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <span
                style={{
                  color: '#718096',
                  marginRight: 15,
                  minWidth: '30px',
                  textAlign: 'right',
                  userSelect: 'none',
                }}
              >
                {lineNum}
              </span>
              <span style={{ color: vulnerable ? '#ffaaaa' : '#e2e8f0', fontWeight: vulnerable ? 'bold' : 'normal' }}>
                {line || ' '}
              </span>
              {vulnerable && (
                <span style={{ marginLeft: 10, color: '#ff4444', fontSize: '12px' }}>
                  VULNERABLE
                </span>
              )}
            </div>
          );
        })}
      </pre>
      <div style={{ marginTop: 10, fontSize: '12px', color: '#666' }}>
        <p>Red highlight marks the vulnerable lines ({finding.line}-{finding.end_line}).</p>
        <p>Use the file path above to open the source in your editor.</p>
      </div>
    </div>
  );
}

export default CodePreview;
