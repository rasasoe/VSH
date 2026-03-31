import React, { useState } from 'react';

interface SetupWizardProps {
  apiBase: string;
  onComplete: (config: any) => void;
}

function SetupWizard({ apiBase, onComplete }: SetupWizardProps) {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<any>({
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
    },
    output: {
      export_path: './exports',
      save_json: true,
      save_markdown: true,
      save_diagnostics: true,
      auto_open_report_after_scan: false,
    },
  });

  const next = () => setStep((prev) => Math.min(prev + 1, 4));
  const prev = () => setStep((prev) => Math.max(prev - 1, 1));

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div>
            <h2>Welcome to VSH</h2>
            <p>VSH now handles local runtime pieces automatically so setup is much simpler.</p>
            <ul>
              <li>Python and Node.js are required.</li>
              <li>SQLite and Chroma runtime storage are automatic.</li>
              <li>LLM API keys are optional and only needed for live reasoning.</li>
              <li>Semgrep and Syft are optional local CLIs that VSH can auto-detect.</li>
              <li>Syft is auto-detected if installed.</li>
            </ul>
            <button onClick={next}>Next</button>
          </div>
        );
      case 2:
        return (
          <div>
            <h2>LLM Setup</h2>
            <p>Pick how VSH should choose its reasoning provider. Auto is recommended.</p>
            <div style={{ marginBottom: 12 }}>
              <label>Provider mode:&nbsp;</label>
              <select value={config.llm.provider} onChange={(e) => setConfig((c: any) => ({ ...c, llm: { ...c.llm, provider: e.target.value } }))}>
                <option value="auto">Auto</option>
                <option value="gemini">Gemini only</option>
                <option value="openai">OpenAI only</option>
                <option value="mock">Mock only</option>
              </select>
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Gemini API Key:&nbsp;</label>
              <input value={config.llm.gemini_api_key} onChange={(e) => setConfig((c: any) => ({ ...c, llm: { ...c.llm, gemini_api_key: e.target.value } }))} style={{ width: 360 }} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>OpenAI API Key:&nbsp;</label>
              <input value={config.llm.openai_api_key} onChange={(e) => setConfig((c: any) => ({ ...c, llm: { ...c.llm, openai_api_key: e.target.value } }))} style={{ width: 360 }} />
            </div>
            <div style={{ marginTop: 12 }}>
              <button onClick={prev}>Back</button>
              <button onClick={next} style={{ marginLeft: 8 }}>Next</button>
            </div>
          </div>
        );
      case 3:
        return (
          <div>
            <h2>Local Runtime</h2>
            <p>Chroma RAG and SQLite are automatic. Semgrep and Syft are optional CLIs and can be auto-detected or manually pointed to.</p>
            <div style={{ marginBottom: 8 }}>
              <label>Override Semgrep path:&nbsp;</label>
              <input value={config.tools.semgrep_path} onChange={(e) => setConfig((c: any) => ({ ...c, tools: { ...c.tools, semgrep_path: e.target.value } }))} style={{ width: 360 }} placeholder="Leave blank for auto-detect" />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Auto detect Semgrep:&nbsp;</label>
              <input type="checkbox" checked={config.tools.semgrep_auto_detect} onChange={(e) => setConfig((c: any) => ({ ...c, tools: { ...c.tools, semgrep_auto_detect: e.target.checked } }))} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Override Syft path:&nbsp;</label>
              <input value={config.tools.syft_path} onChange={(e) => setConfig((c: any) => ({ ...c, tools: { ...c.tools, syft_path: e.target.value } }))} style={{ width: 360 }} placeholder="Leave blank for auto-detect" />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Auto detect Syft:&nbsp;</label>
              <input type="checkbox" checked={config.tools.syft_auto_detect} onChange={(e) => setConfig((c: any) => ({ ...c, tools: { ...c.tools, syft_auto_detect: e.target.checked } }))} />
            </div>
            <div style={{ marginTop: 12 }}>
              <button onClick={prev}>Back</button>
              <button onClick={next} style={{ marginLeft: 8 }}>Next</button>
            </div>
          </div>
        );
      case 4:
        return (
          <div>
            <h2>Scan and L3 Defaults</h2>
            <div style={{ marginBottom: 8 }}>
              <label>Watch on Save:&nbsp;</label>
              <input type="checkbox" checked={config.scan.watch_on_save} onChange={(e) => setConfig((c: any) => ({ ...c, scan: { ...c.scan, watch_on_save: e.target.checked } }))} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Auto Scan on Select:&nbsp;</label>
              <input type="checkbox" checked={config.scan.auto_scan_on_select} onChange={(e) => setConfig((c: any) => ({ ...c, scan: { ...c.scan, auto_scan_on_select: e.target.checked } }))} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Enable SBOM when Syft is available:&nbsp;</label>
              <input type="checkbox" checked={config.scan.enable_sbom} onChange={(e) => setConfig((c: any) => ({ ...c, scan: { ...c.scan, enable_sbom: e.target.checked } }))} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Enable L3 pipeline:&nbsp;</label>
              <input type="checkbox" checked={config.llm.enable_l3} onChange={(e) => setConfig((c: any) => ({ ...c, llm: { ...c.llm, enable_l3: e.target.checked } }))} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Sonar URL:&nbsp;</label>
              <input value={config.l3.sonar_url} onChange={(e) => setConfig((c: any) => ({ ...c, l3: { ...c.l3, sonar_url: e.target.value } }))} style={{ width: 360 }} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Sonar Token:&nbsp;</label>
              <input type="password" value={config.l3.sonar_token} onChange={(e) => setConfig((c: any) => ({ ...c, l3: { ...c.l3, sonar_token: e.target.value } }))} style={{ width: 360 }} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Sonar Org:&nbsp;</label>
              <input value={config.l3.sonar_org} onChange={(e) => setConfig((c: any) => ({ ...c, l3: { ...c.l3, sonar_org: e.target.value } }))} style={{ width: 360 }} />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Sonar Project Key:&nbsp;</label>
              <input value={config.l3.sonar_project_key} onChange={(e) => setConfig((c: any) => ({ ...c, l3: { ...c.l3, sonar_project_key: e.target.value } }))} style={{ width: 360 }} />
            </div>
            <div style={{ marginTop: 12 }}>
              <button onClick={prev}>Back</button>
              <button onClick={() => onComplete(config)} style={{ marginLeft: 8 }}>Finish</button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ padding: 24, fontFamily: 'Arial, sans-serif', maxWidth: 720 }}>
      <h1>Setup Wizard</h1>
      <p>API base: {apiBase}</p>
      <p>Step {step} / 4</p>
      {renderStep()}
    </div>
  );
}

export default SetupWizard;
