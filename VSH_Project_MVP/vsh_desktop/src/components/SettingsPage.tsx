import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

interface SettingsPageProps {
  apiBase: string;
  onBack: () => void;
}

const defaultConfig = {
  llm: {
    provider: 'auto',
    gemini_api_key: '',
    openai_api_key: '',
    model: 'gemini-1.5-pro',
    enable_l2: true,
    enable_l3: true,
  },
  tools: {
    syft_path: '',
    syft_auto_detect: true,
    semgrep_path: '',
    semgrep_auto_detect: true,
  },
  l3: {
    sonar_url: 'https://sonarcloud.io',
    sonar_token: '',
    sonar_org: '',
    sonar_project_key: 'vsh-local',
  },
  scan: {
    watch_on_save: true,
    auto_scan_on_select: false,
    enable_sbom: true,
    max_files_per_scan: 200,
    exclude_dirs: ['.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build'],
    include_extensions: ['.py', '.js', '.ts', '.jsx', '.tsx'],
  },
  output: {
    export_path: './exports',
    save_json: true,
    save_markdown: true,
    save_diagnostics: true,
    auto_open_report_after_scan: false,
  },
  ui: {
    theme: 'dark',
    show_code_preview: true,
    show_attack_scenario: true,
    show_validation_panel: true,
  },
  system: {
    api_base_url: 'http://localhost:3000',
    config_version: 2,
  },
};

function SettingsPage({ apiBase, onBack }: SettingsPageProps) {
  const [config, setConfig] = useState<any>(defaultConfig);
  const [unsaved, setUnsaved] = useState(false);
  const [status, setStatus] = useState<any>({});
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('AI');
  const [llmTestResult, setLlmTestResult] = useState('');
  const [syftResult, setSyftResult] = useState('');
  const [semgrepResult, setSemgrepResult] = useState('');

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await axios.get(`${apiBase}/settings`);
        setConfig(res.data);
      } catch {
        setError('Unable to load settings. Using defaults.');
      }
      await refreshSystemStatus();
    };
    void loadSettings();
  }, [apiBase]);

  const refreshSystemStatus = async () => {
    try {
      const res = await axios.get(`${apiBase}/system/status`);
      setStatus(res.data);
      setError('');
    } catch {
      setError('Unable to fetch system status.');
    }
  };

  const updateConfig = (path: string[], value: any) => {
    setConfig((prev: any) => {
      const next = JSON.parse(JSON.stringify(prev));
      let cursor = next;
      for (let i = 0; i < path.length - 1; i += 1) {
        if (cursor[path[i]] === undefined) cursor[path[i]] = {};
        cursor = cursor[path[i]];
      }
      cursor[path[path.length - 1]] = value;
      return next;
    });
    setUnsaved(true);
  };

  const saveConfig = async () => {
    try {
      await axios.post(`${apiBase}/settings`, config);
      setMessage('Settings saved successfully.');
      setError('');
      setUnsaved(false);
      await refreshSystemStatus();
    } catch {
      setError('Failed to save settings.');
      setMessage('');
    }
  };

  const resetConfig = () => {
    setConfig(defaultConfig);
    setUnsaved(true);
    setMessage('Settings reset to defaults. Save to apply them.');
    setError('');
  };

  const reloadConfig = async () => {
    try {
      const res = await axios.get(`${apiBase}/settings`);
      setConfig(res.data);
      setUnsaved(false);
      setMessage('Settings reloaded.');
      setError('');
      await refreshSystemStatus();
    } catch {
      setError('Failed to reload settings.');
    }
  };

  const testLlm = async () => {
    try {
      const body = {
        provider: config.llm.provider,
        gemini_api_key: config.llm.gemini_api_key,
        openai_api_key: config.llm.openai_api_key,
      };
      const res = await axios.post(`${apiBase}/settings/test-llm`, body);
      setLlmTestResult(`Effective provider: ${res.data.provider} | ${res.data.connected ? 'Ready' : 'Unavailable'} | ${res.data.reason}`);
      setError('');
    } catch {
      setLlmTestResult('Connection test failed.');
      setError('LLM connection test failed.');
    }
  };

  const checkSyft = async () => {
    try {
      const body = {
        syft_path: config.tools.syft_path,
        syft_auto_detect: config.tools.syft_auto_detect,
      };
      const res = await axios.post(`${apiBase}/settings/check-syft`, body);
      const syftState = res.data.syft;
      const pathLabel = syftState.path || 'no path';
      setSyftResult(`Syft ${syftState.installed ? 'ready' : 'not found'} | ${syftState.source} | ${pathLabel}`);
      setError('');
    } catch {
      setSyftResult('Syft check failed.');
      setError('Syft check failed.');
    }
  };

  const checkSemgrep = async () => {
    try {
      const body = {
        semgrep_path: config.tools.semgrep_path,
        semgrep_auto_detect: config.tools.semgrep_auto_detect,
      };
      const res = await axios.post(`${apiBase}/settings/check-semgrep`, body);
      const semgrepState = res.data.semgrep;
      const pathLabel = semgrepState.path || 'no path';
      setSemgrepResult(`Semgrep ${semgrepState.installed ? 'ready' : 'not found'} | ${semgrepState.source} | ${pathLabel}`);
      setError('');
    } catch {
      setSemgrepResult('Semgrep check failed.');
      setError('Semgrep check failed.');
    }
  };

  const sectionStyle = {
    backgroundColor: '#ffffff',
    padding: 16,
    borderRadius: 10,
    marginBottom: 14,
    border: '1px solid #ddd',
  } as const;

  const effectiveProvider = useMemo(() => status.llm?.provider || config.llm.provider, [status.llm, config.llm.provider]);

  return (
    <div style={{ display: 'flex', height: '100%', fontFamily: 'Arial, sans-serif', backgroundColor: '#f6f7fb', color: '#1f2937' }}>
      <div style={{ width: 240, borderRight: '1px solid #d6dae3', padding: 16, backgroundColor: '#ffffff' }}>
        <h2 style={{ marginTop: 0 }}>Settings</h2>
        {['AI', 'Local Runtime', 'Scan', 'Output', 'System'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              width: '100%',
              textAlign: 'left',
              padding: '10px 12px',
              marginBottom: 8,
              backgroundColor: activeTab === tab ? '#1d4ed8' : '#f3f4f6',
              color: activeTab === tab ? '#ffffff' : '#111827',
              border: 'none',
              borderRadius: 8,
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, padding: 24, overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
          <div>
            <h1 style={{ marginBottom: 8 }}>Runtime Settings</h1>
            <p style={{ marginTop: 0, color: '#4b5563' }}>
              Local services such as Chroma and SQLite are automatic. Only external credentials like LLM API keys need manual input.
            </p>
          </div>
          <div>
            <button onClick={saveConfig} disabled={!unsaved} style={{ marginRight: 8, padding: '8px 12px' }}>Save</button>
            <button onClick={resetConfig} style={{ marginRight: 8, padding: '8px 12px' }}>Reset</button>
            <button onClick={reloadConfig} style={{ padding: '8px 12px' }}>Reload</button>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          {unsaved && <div style={{ color: '#b45309' }}>You have unsaved changes.</div>}
          {!unsaved && <div style={{ color: '#15803d' }}>Settings are in sync.</div>}
          {message && <div style={{ color: '#15803d' }}>{message}</div>}
          {error && <div style={{ color: '#b91c1c' }}>{error}</div>}
        </div>

        {activeTab === 'AI' && (
          <>
            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>LLM Provider</h3>
              <p style={{ color: '#4b5563' }}>
                Auto mode chooses OpenAI or Gemini when a key is available. If no key is configured, VSH falls back to mock reasoning automatically.
              </p>
              <div style={{ marginBottom: 10 }}>
                <label>Provider mode:&nbsp;</label>
                <select value={config.llm.provider} onChange={(e) => updateConfig(['llm', 'provider'], e.target.value)}>
                  <option value="auto">Auto</option>
                  <option value="gemini">Gemini only</option>
                  <option value="openai">OpenAI only</option>
                  <option value="mock">Mock only</option>
                </select>
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Gemini API Key:&nbsp;</label>
                <input type="password" value={config.llm.gemini_api_key} onChange={(e) => updateConfig(['llm', 'gemini_api_key'], e.target.value)} style={{ width: 420 }} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>OpenAI API Key:&nbsp;</label>
                <input type="password" value={config.llm.openai_api_key} onChange={(e) => updateConfig(['llm', 'openai_api_key'], e.target.value)} style={{ width: 420 }} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>LLM Model:&nbsp;</label>
                <input value={config.llm.model} onChange={(e) => updateConfig(['llm', 'model'], e.target.value)} style={{ width: 320 }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <button onClick={testLlm} style={{ padding: '6px 12px' }}>Test LLM Setup</button>
                <span>{llmTestResult || `Current effective provider: ${effectiveProvider}`}</span>
              </div>
            </div>

            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>How it works</h3>
              <div>L2 reasoning is automatic during scans.</div>
              <div>Live LLM calls happen only when a supported API key is configured.</div>
              <div>If no key exists, the app stays usable in mock mode instead of breaking.</div>
            </div>
          </>
        )}

        {activeTab === 'Local Runtime' && (
          <>
            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>Automatic Local Services</h3>
              <div>Chroma RAG: {status.chroma?.rag_enabled ? 'ready' : 'preparing or empty'} ({status.chroma?.path || 'unknown'})</div>
              <div>SQLite metadata DB: {status.sqlite?.exists ? 'ready' : 'missing'} ({status.sqlite?.path || 'unknown'})</div>
              <div style={{ marginTop: 8, color: '#4b5563' }}>
                These runtime databases are local to the app and do not require API keys or a separate setup screen.
              </div>
            </div>

            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>Semgrep Detection</h3>
              <p style={{ color: '#4b5563' }}>
                VSH can call the real Semgrep CLI when it is installed. If Semgrep is missing, VSH falls back to the built-in heuristic L1 engine.
              </p>
              <div style={{ marginBottom: 10 }}>
                <label>Override Semgrep path:&nbsp;</label>
                <input value={config.tools.semgrep_path} onChange={(e) => updateConfig(['tools', 'semgrep_path'], e.target.value)} style={{ width: 420 }} placeholder="Leave blank for auto-detect" />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Auto detect Semgrep:&nbsp;</label>
                <input type="checkbox" checked={config.tools.semgrep_auto_detect} onChange={(e) => updateConfig(['tools', 'semgrep_auto_detect'], e.target.checked)} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <button onClick={checkSemgrep} style={{ padding: '6px 12px' }}>Check Semgrep</button>
                <span>{semgrepResult || `Current status: ${status.semgrep?.installed ? 'ready' : 'not found'}`}</span>
              </div>
            </div>

            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>Syft Detection</h3>
              <p style={{ color: '#4b5563' }}>
                Syft is treated as an optional local CLI. VSH auto-detects it when installed. Use the path field only if you want to override auto-detection.
              </p>
              <div style={{ marginBottom: 10 }}>
                <label>Override Syft path:&nbsp;</label>
                <input value={config.tools.syft_path} onChange={(e) => updateConfig(['tools', 'syft_path'], e.target.value)} style={{ width: 420 }} placeholder="Leave blank for auto-detect" />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Auto detect Syft:&nbsp;</label>
                <input type="checkbox" checked={config.tools.syft_auto_detect} onChange={(e) => updateConfig(['tools', 'syft_auto_detect'], e.target.checked)} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <button onClick={checkSyft} style={{ padding: '6px 12px' }}>Check Syft</button>
                <span>{syftResult || `Current status: ${status.syft?.installed ? 'ready' : 'not found'}`}</span>
              </div>
            </div>

            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>L3 / Sonar Setup</h3>
              <p style={{ color: '#4b5563' }}>
                L3 becomes ready only when Docker and Sonar credentials are both available. Saving these settings re-checks the backend immediately.
              </p>
              <div style={{ marginBottom: 10 }}>
                <label>Sonar URL:&nbsp;</label>
                <input value={config.l3.sonar_url} onChange={(e) => updateConfig(['l3', 'sonar_url'], e.target.value)} style={{ width: 420 }} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Sonar Token:&nbsp;</label>
                <input type="password" value={config.l3.sonar_token} onChange={(e) => updateConfig(['l3', 'sonar_token'], e.target.value)} style={{ width: 420 }} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Sonar Org:&nbsp;</label>
                <input value={config.l3.sonar_org} onChange={(e) => updateConfig(['l3', 'sonar_org'], e.target.value)} style={{ width: 320 }} />
              </div>
              <div style={{ marginBottom: 10 }}>
                <label>Sonar Project Key:&nbsp;</label>
                <input value={config.l3.sonar_project_key} onChange={(e) => updateConfig(['l3', 'sonar_project_key'], e.target.value)} style={{ width: 320 }} />
              </div>
              <label>
                <input type="checkbox" checked={config.llm.enable_l3} onChange={(e) => updateConfig(['llm', 'enable_l3'], e.target.checked)} />
                &nbsp;Enable L3 pipeline
              </label>
            </div>

            <div style={sectionStyle}>
              <h3 style={{ marginTop: 0 }}>Dependency Analysis</h3>
              <label>
                <input type="checkbox" checked={config.scan.enable_sbom} onChange={(e) => updateConfig(['scan', 'enable_sbom'], e.target.checked)} />
                &nbsp;Enable SBOM-based enrichment when Syft is available
              </label>
            </div>
          </>
        )}

        {activeTab === 'Scan' && (
          <div style={sectionStyle}>
            <h3 style={{ marginTop: 0 }}>Scan Defaults</h3>
            <div style={{ marginBottom: 10 }}>
              <label>Watch on Save:&nbsp;</label>
              <input type="checkbox" checked={config.scan.watch_on_save} onChange={(e) => updateConfig(['scan', 'watch_on_save'], e.target.checked)} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <label>Auto Scan on Select:&nbsp;</label>
              <input type="checkbox" checked={config.scan.auto_scan_on_select} onChange={(e) => updateConfig(['scan', 'auto_scan_on_select'], e.target.checked)} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <label>Max Files per Scan:&nbsp;</label>
              <input type="number" value={config.scan.max_files_per_scan} onChange={(e) => updateConfig(['scan', 'max_files_per_scan'], Number(e.target.value))} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <label>Exclude Dirs:&nbsp;</label>
              <input type="text" value={config.scan.exclude_dirs.join(',')} onChange={(e) => updateConfig(['scan', 'exclude_dirs'], e.target.value.split(',').map((v: string) => v.trim()).filter(Boolean))} style={{ width: 420 }} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <label>Include Extensions:&nbsp;</label>
              <input type="text" value={config.scan.include_extensions.join(',')} onChange={(e) => updateConfig(['scan', 'include_extensions'], e.target.value.split(',').map((v: string) => v.trim()).filter(Boolean))} style={{ width: 420 }} />
            </div>
            <div style={{ color: '#4b5563' }}>
              L2 reasoning and local Chroma retrieval are automatic. This page only controls scan behavior, not backend feature wiring.
            </div>
          </div>
        )}

        {activeTab === 'Output' && (
          <div style={sectionStyle}>
            <h3 style={{ marginTop: 0 }}>Output</h3>
            <div style={{ marginBottom: 10 }}>
              <label>Export Path:&nbsp;</label>
              <input value={config.output.export_path} onChange={(e) => updateConfig(['output', 'export_path'], e.target.value)} style={{ width: 420 }} />
            </div>
            <div><label><input type="checkbox" checked={config.output.save_json} onChange={(e) => updateConfig(['output', 'save_json'], e.target.checked)} /> Save JSON</label></div>
            <div><label><input type="checkbox" checked={config.output.save_markdown} onChange={(e) => updateConfig(['output', 'save_markdown'], e.target.checked)} /> Save Markdown</label></div>
            <div><label><input type="checkbox" checked={config.output.save_diagnostics} onChange={(e) => updateConfig(['output', 'save_diagnostics'], e.target.checked)} /> Save Diagnostics</label></div>
            <div><label><input type="checkbox" checked={config.output.auto_open_report_after_scan} onChange={(e) => updateConfig(['output', 'auto_open_report_after_scan'], e.target.checked)} /> Auto-open report after scan</label></div>
          </div>
        )}

        {activeTab === 'System' && (
          <div style={sectionStyle}>
            <h3 style={{ marginTop: 0 }}>System Status</h3>
            <div>API Server: {status.api_server || 'unknown'}</div>
            <div>Python Core: {status.python_core || 'unknown'}</div>
            <div>LLM Requested: {status.llm?.requested_provider || 'unknown'}</div>
            <div>LLM Effective: {status.llm?.provider || 'unknown'} ({status.llm?.connected ? 'ready' : 'needs key'})</div>
            <div>L2 Reasoning: {status.l2?.enabled ? 'enabled' : 'disabled'} | {status.l2?.rag_mode || 'unknown'}</div>
            <div>Semgrep: {status.semgrep?.installed ? 'installed' : 'not found'} ({status.semgrep?.path || 'N/A'})</div>
            <div>Syft: {status.syft?.installed ? 'installed' : 'not found'} ({status.syft?.path || 'N/A'})</div>
            <div>L3 Pipeline: {status.l3?.enabled ? 'enabled' : 'disabled'} ({status.l3?.reason || 'unknown'})</div>
            <div>Docker: {status.l3?.docker?.installed ? 'installed' : 'not ready'} ({status.l3?.docker?.path || 'N/A'})</div>
            <div>Sonar: {status.l3?.sonar?.has_token ? 'token configured' : 'token missing'} | {status.l3?.sonar?.url || 'N/A'} | {status.l3?.sonar?.project_key || 'N/A'}</div>
            <div>Shared DB: {status.shared_db?.path || 'N/A'}</div>
            <div>SQLite DB: {status.sqlite?.path || 'N/A'} ({status.sqlite?.exists ? 'ready' : 'missing'})</div>
            <div>Chroma DB: {status.chroma?.path || 'N/A'} ({status.chroma?.status || 'unknown'})</div>
            <div>Config Path: {status.config_path || 'N/A'}</div>
          </div>
        )}
      </div>

      <div style={{ position: 'absolute', bottom: 20, left: 268 }}>
        <button onClick={onBack} style={{ padding: '8px 12px' }}>Back to Scanner</button>
      </div>
    </div>
  );
}

export default SettingsPage;
