import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Upload, ShieldCheck, AlertTriangle } from 'lucide-react';
import './styles.css';

const API = 'http://localhost:8000/api';

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function analyze() {
    if (!file) return;
    setLoading(true); setError(''); setResult(null);
    const form = new FormData(); form.append('file', file);
    try {
      const res = await fetch(`${API}/analyze-image`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Analysis failed');
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return <main className="page">
    <header><div><p className="eyebrow">SIH26034 · Prototype</p><h1>Packaged Commodity Compliance Inspector</h1><p className="sub">Upload a package image. The prototype extracts declarations and evaluates the first frozen compliance rules.</p></div><div className="badge">Ruleset: LM-PCR-Prototype-v1</div></header>

    <section className="grid">
      <div className="card">
        <h2><Upload size={20}/> New inspection</h2>
        <label className="drop"><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>setFile(e.target.files?.[0] || null)}/><strong>{file ? file.name : 'Choose package image'}</strong><span>JPG, PNG or WEBP</span></label>
        <button disabled={!file || loading} onClick={analyze}>{loading ? 'Analyzing…' : 'Analyze package'}</button>
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h2>Prototype status</h2>
        <div className="metric"><span>Current rules</span><strong>3</strong></div>
        <div className="metric"><span>Decision states</span><strong>PASS / FAIL / REVIEW</strong></div>
        <p className="note">This starter version checks MRP, net quantity, and manufacturer/packer/importer declaration presence. Legal applicability still needs final verification before demo claims.</p>
      </div>
    </section>

    {result && <section className="card result">
      <div className="resultHead"><div><p className="eyebrow">Inspection result</p><h2>{result.overall_status.replaceAll('_',' ')}</h2></div>{result.overall_status.includes('COMPLIANT') ? <ShieldCheck size={34}/> : <AlertTriangle size={34}/>}</div>
      <div className="checks">
        {result.checks.map(check => <article className={`check ${check.status.toLowerCase()}`} key={check.rule_id}>
          <div><strong>{check.label}</strong><small>{check.rule_id}</small></div><span className="status">{check.status}</span><p>{check.reason}</p>{check.evidence && <code>{check.evidence.raw_text}</code>}
        </article>)}
      </div>
    </section>}
  </main>
}

createRoot(document.getElementById('root')).render(<App />);
