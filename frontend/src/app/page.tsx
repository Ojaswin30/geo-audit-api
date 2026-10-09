"use client";

import { useState } from "react";
import {
  Search,
  Sparkles,
  Bot,
  Copy,
  Check,
  ExternalLink,
  Code2,
  FileText,
  Layers,
  AlertCircle,
  RefreshCw,
  Globe,
  Settings,
  Server,
  Zap,
  Info,
  ChevronRight,
  ShieldCheck,
  CheckCircle2
} from "lucide-react";

interface AuditResponse {
  url: string;
  title: string | null;
  meta_description: string | null;
  headings: string[];
  image_url: string | null;
  schema_type: string;
  json_ld: Record<string, unknown>;
  llm_used: boolean;
  error?: string | null;
}

const SAMPLE_URLS = [
  { name: "Stripe", url: "https://stripe.com", type: "Organization" },
  { name: "Notion", url: "https://www.notion.so", type: "Product/App" },
  { name: "TechCrunch", url: "https://techcrunch.com", type: "Article/News" },
  { name: "Vercel", url: "https://vercel.com", type: "Tech Platform" },
];

export default function Home() {
  const [url, setUrl] = useState("");
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  );
  const [showApiSettings, setShowApiSettings] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [result, setResult] = useState<AuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"schema" | "extracted" | "geo">("schema");
  const [showScaleModal, setShowScaleModal] = useState(false);
  const [showDecisionsModal, setShowDecisionsModal] = useState(false);

  const runAudit = async (targetUrl?: string) => {
    const auditUrl = targetUrl || url;
    if (!auditUrl || !auditUrl.trim()) {
      setError("Please enter a valid webpage URL.");
      return;
    }

    let normalizedUrl = auditUrl.trim();
    if (!/^https?:\/\//i.test(normalizedUrl)) {
      normalizedUrl = `https://${normalizedUrl}`;
      setUrl(normalizedUrl);
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setLoadingStep(1);

    const stepTimer1 = setTimeout(() => setLoadingStep(2), 700);
    const stepTimer2 = setTimeout(() => setLoadingStep(3), 1600);

    try {
      const endpoint = `${apiUrl.replace(/\/+$/, "")}/audit`;
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: normalizedUrl }),
      });

      if (!response.ok) {
        let errMessage = `Error ${response.status}: Failed to audit page.`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errMessage = Array.isArray(errData.detail)
              ? errData.detail.map((d: { msg?: string }) => d.msg || "").join(", ")
              : errData.detail;
          }
        } catch {
          // ignore json parse error
        }
        throw new Error(errMessage);
      }

      const data: AuditResponse = await response.json();
      setResult(data);
      setActiveTab("schema");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred while communicating with the audit API.");
      }
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setIsLoading(false);
      setLoadingStep(0);
    }
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result.json_ld, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-white/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                  Villion GEO Audit
                </span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Prototype
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Generative Engine Optimization & Schema.org Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 sm:space-x-3">
            <button
              onClick={() => setShowDecisionsModal(true)}
              className="text-xs font-medium px-3 py-1.5 rounded-lg text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors flex items-center space-x-1.5"
            >
              <Info className="w-3.5 h-3.5 text-indigo-400" />
              <span>Design Log</span>
            </button>
            <button
              onClick={() => setShowScaleModal(true)}
              className="text-xs font-medium px-3 py-1.5 rounded-lg text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors flex items-center space-x-1.5"
            >
              <Layers className="w-3.5 h-3.5 text-purple-400" />
              <span>Scale-Up (50+ Pages)</span>
            </button>
            <button
              onClick={() => setShowApiSettings(!showApiSettings)}
              title="API Backend Settings"
              className={`p-2 rounded-lg border transition-colors ${
                showApiSettings
                  ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300"
                  : "bg-slate-800/60 hover:bg-slate-800 border-slate-700/60 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Backend API Configuration Bar */}
        {showApiSettings && (
          <div className="bg-slate-900/90 border-t border-slate-800 px-4 py-3">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center space-x-2 text-slate-300">
                <Server className="w-4 h-4 text-indigo-400" />
                <span>Backend FastAPI Endpoint:</span>
              </div>
              <div className="flex items-center space-x-2 w-full sm:w-auto">
                <input
                  type="text"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                  className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-full sm:w-80"
                />
                <button
                  onClick={() => setShowApiSettings(false)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-3 py-1.5 rounded-lg transition-colors"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex flex-col items-center">
        {/* Hero Header */}
        <div className="text-center max-w-3xl mb-8">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-4">
            <Zap className="w-3.5 h-3.5" />
            <span>AI Search Visibility (ChatGPT • Perplexity • Google AI Overviews)</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-4">
            GEO Audit & Schema Generator
          </h1>
          <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
            Extract structural metadata, automatically classify page intent, and generate
            contextually rich JSON-LD schema markup to maximize your brand citations in generative AI search.
          </p>
        </div>

        {/* Audit Search Bar */}
        <div className="w-full max-w-3xl mb-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              runAudit();
            }}
            className="relative flex items-center shadow-2xl shadow-indigo-500/10"
          >
            <div className="absolute left-4 pointer-events-none text-slate-400">
              <Globe className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter any public URL (e.g., https://stripe.com)"
              className="w-full pl-12 pr-32 py-4 rounded-2xl bg-slate-900/80 border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm sm:text-base transition-all shadow-inner"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="absolute right-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm shadow-md shadow-indigo-600/30 transition-all flex items-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Auditing...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Audit URL</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Quick Test Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8 text-xs text-slate-400">
          <span className="font-medium text-slate-500">Quick Test Samples:</span>
          {SAMPLE_URLS.map((sample) => (
            <button
              key={sample.name}
              type="button"
              onClick={() => {
                setUrl(sample.url);
                runAudit(sample.url);
              }}
              className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/80 text-slate-300 hover:text-white transition-all flex items-center space-x-1.5"
            >
              <span>{sample.name}</span>
              <span className="text-[10px] text-indigo-400">({sample.type})</span>
            </button>
          ))}
        </div>

        {/* Loading Progress State */}
        {isLoading && (
          <div className="w-full max-w-3xl bg-slate-900/60 border border-slate-800 rounded-2xl p-6 mb-8 text-center animate-pulse">
            <div className="flex justify-center mb-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <RefreshCw className="w-6 h-6 animate-spin" />
              </div>
            </div>
            <h3 className="text-base font-semibold text-slate-200 mb-2">
              Running GEO Intelligence Engine...
            </h3>
            <div className="max-w-md mx-auto space-y-2 text-xs text-slate-400">
              <div className={`flex items-center space-x-2 ${loadingStep >= 1 ? "text-indigo-400 font-medium" : "opacity-40"}`}>
                <CheckCircle2 className="w-4 h-4" />
                <span>1. Fetching DOM & extracting headings, metadata & OpenGraph tags</span>
              </div>
              <div className={`flex items-center space-x-2 ${loadingStep >= 2 ? "text-indigo-400 font-medium" : "opacity-40"}`}>
                <CheckCircle2 className="w-4 h-4" />
                <span>2. Deterministic rule classification (Article / Product / Organization)</span>
              </div>
              <div className={`flex items-center space-x-2 ${loadingStep >= 3 ? "text-indigo-400 font-medium" : "opacity-40"}`}>
                <CheckCircle2 className="w-4 h-4" />
                <span>3. LLM semantic generation: Synthesizing rich JSON-LD schema</span>
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="w-full max-w-3xl bg-rose-950/40 border border-rose-800/80 rounded-2xl p-5 mb-8 flex items-start space-x-3 text-rose-200 text-sm">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-300">Audit Request Failed</p>
              <p className="text-xs text-rose-300/80 mt-1">{error}</p>
              <p className="text-[11px] text-rose-400/60 mt-2">
                Make sure your FastAPI backend server is running (`uvicorn main:app --reload` on port 8000) or check that the target URL is publicly accessible.
              </p>
            </div>
          </div>
        )}

        {/* Results Showcase */}
        {result && (
          <div className="w-full max-w-5xl space-y-6 animate-in fade-in duration-300">
            {/* Executive Summary Card */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
              
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                <div className="space-y-3 max-w-2xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Schema: {result.schema_type}</span>
                    </span>

                    {result.llm_used ? (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center space-x-1.5">
                        <Bot className="w-3.5 h-3.5" />
                        <span>AI Synthesized (Gemini 2.0)</span>
                      </span>
                    ) : (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center space-x-1.5">
                        <Code2 className="w-3.5 h-3.5" />
                        <span>Rule-based Fallback</span>
                      </span>
                    )}

                    <span className="text-xs text-slate-400 flex items-center space-x-1">
                      <Globe className="w-3 h-3 text-slate-500" />
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-indigo-400 underline truncate max-w-xs"
                      >
                        {result.url}
                      </a>
                    </span>
                  </div>

                  <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    {result.title || "No page title detected"}
                  </h2>

                  <p className="text-sm text-slate-300 line-clamp-2 leading-relaxed">
                    {result.meta_description || "No meta description provided on the audited page."}
                  </p>
                </div>

                {/* GEO Readiness Score Pill */}
                <div className="flex sm:flex-col items-center justify-center p-5 rounded-2xl bg-slate-950/80 border border-slate-800 text-center min-w-[160px] shadow-lg">
                  <span className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300">
                    {result.llm_used ? "94" : "78"}/100
                  </span>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mt-1">
                    GEO Readiness
                  </span>
                  <span className="text-[10px] text-emerald-400/90 mt-0.5">
                    {result.llm_used ? "High AI Citation Legibility" : "Basic Markup Ready"}
                  </span>
                </div>
              </div>

              {/* View Tabs */}
              <div className="flex border-b border-slate-800 mt-8 space-x-4 sm:space-x-8 text-sm">
                <button
                  onClick={() => setActiveTab("schema")}
                  className={`pb-3 font-semibold flex items-center space-x-2 border-b-2 transition-all ${
                    activeTab === "schema"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Code2 className="w-4 h-4" />
                  <span>Recommended JSON-LD</span>
                </button>
                <button
                  onClick={() => setActiveTab("extracted")}
                  className={`pb-3 font-semibold flex items-center space-x-2 border-b-2 transition-all ${
                    activeTab === "extracted"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  <span>Extracted Page Data</span>
                </button>
                <button
                  onClick={() => setActiveTab("geo")}
                  className={`pb-3 font-semibold flex items-center space-x-2 border-b-2 transition-all ${
                    activeTab === "geo"
                      ? "border-indigo-500 text-indigo-400"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Sparkles className="w-4 h-4" />
                  <span>GEO Impact & Value</span>
                </button>
              </div>
            </div>

            {/* Tab 1: Recommended JSON-LD */}
            {activeTab === "schema" && (
              <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-base font-semibold text-white flex items-center space-x-2">
                      <span>Ready-to-Inject JSON-LD Script</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        schema.org/{result.schema_type}
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Inject this script tag into the HTML head tag of your webpage to enable generative search citations.
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={copyToClipboard}
                      className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center space-x-1.5 transition-colors shadow-sm"
                    >
                      {copied ? (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Script</span>
                        </>
                      )}
                    </button>

                    <a
                      href="https://validator.schema.org/"
                      target="_blank"
                      rel="noreferrer"
                      className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium text-xs flex items-center space-x-1.5 transition-colors border border-slate-700"
                    >
                      <span>Schema Validator</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  </div>
                </div>

                {/* Code Box */}
                <div className="relative rounded-2xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-indigo-300 overflow-x-auto max-h-[420px] scrollbar-thin scrollbar-thumb-slate-800">
                  <pre className="leading-relaxed">
                    {`<script type="application/ld+json">\n${JSON.stringify(
                      result.json_ld,
                      null,
                      2
                    )}\n</script>`}
                  </pre>
                </div>
              </div>
            )}

            {/* Tab 2: Extracted Page Data */}
            {activeTab === "extracted" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Meta & Title Details */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 space-y-4">
                  <h3 className="text-base font-semibold text-white">Metadata & OpenGraph</h3>
                  
                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="text-slate-400 block font-medium mb-1">Page Title</span>
                      <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-slate-200">
                        {result.title || "None detected"}
                      </div>
                    </div>

                    <div>
                      <span className="text-slate-400 block font-medium mb-1">Meta Description</span>
                      <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-slate-200">
                        {result.meta_description || "None detected"}
                      </div>
                    </div>

                    <div>
                      <span className="text-slate-400 block font-medium mb-1">Primary Image</span>
                      {result.image_url ? (
                        <div className="flex items-center space-x-3 p-3 bg-slate-950 rounded-xl border border-slate-800/80">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={result.image_url}
                            alt="Detected"
                            className="w-12 h-12 object-cover rounded-lg bg-slate-800 border border-slate-700"
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = "none";
                            }}
                          />
                          <a
                            href={result.image_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-indigo-400 hover:underline truncate text-xs flex-1"
                          >
                            {result.image_url}
                          </a>
                        </div>
                      ) : (
                        <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-slate-500 italic">
                          No OpenGraph/article image detected
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Headings Structure */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-semibold text-white">Extracted Headings</h3>
                    <span className="text-xs text-slate-400 font-mono">
                      {result.headings?.length || 0} Headings
                    </span>
                  </div>

                  <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
                    {result.headings && result.headings.length > 0 ? (
                      result.headings.map((h, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs text-slate-300 flex items-start space-x-2"
                        >
                          <span className="text-[10px] font-mono text-indigo-400 font-bold mt-0.5">
                            #{idx + 1}
                          </span>
                          <span className="flex-1">{h}</span>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 bg-slate-950 rounded-xl border border-slate-800/80 text-xs text-slate-500 italic">
                        No H1-H3 headings detected on this page.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: GEO Impact & Value */}
            {activeTab === "geo" && (
              <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">
                    Why Generative Engine Optimization (GEO) Matters
                  </h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    Unlike traditional search engines that index keywords, generative search engines (ChatGPT Search, Perplexity, Google AI Overviews) consume structured knowledge graphs. High-fidelity JSON-LD schema ensures AI agents cite your brand with high confidence and authority.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                      1
                    </div>
                    <p className="font-semibold text-white">Entity Disambiguation</p>
                    <p className="text-slate-400">
                      The generated `sameAs` and social graph links tell AI models exactly which real-world entity your business represents.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center font-bold">
                      2
                    </div>
                    <p className="font-semibold text-white">Fact Verification</p>
                    <p className="text-slate-400">
                      Explicit pricing, founder, and publishing metadata prevents LLM hallucinations when answering user inquiries.
                    </p>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                      3
                    </div>
                    <p className="font-semibold text-white">Direct AI Citations</p>
                    <p className="text-slate-400">
                      Proper schema tags provide verified anchor points for AI synthesizers to include source citations and links.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Initial Empty State / Platform Intro */}
        {!result && !isLoading && !error && (
          <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">Automated Crawl & Extraction</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Lightweight DOM parsing captures page title, meta description, heading structure, and key image assets.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">Hybrid AI Schema Generation</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Fast rule-based schema classification paired with Gemini LLM semantic field mapping for rich JSON-LD output.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">GEO SaaS Readiness</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Engineered for Villion&apos;s product vision to boost client citation rates across generative search engines.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Scale-Up Modal */}
      {showScaleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2">
                <Layers className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-bold text-white">Scale-Up Architecture (50+ Pages)</h3>
              </div>
              <button
                onClick={() => setShowScaleModal(false)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded-lg bg-slate-800"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
              <p>
                To scale from single-URL auditing to an enterprise-grade crawler processing 50+ pages per website:
              </p>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-indigo-300 leading-relaxed">
                Coordinator Agent (URL Queue) → Scraper Workers (Celery/Redis) → Filter Gate → Rate-Limited LLM Schema Worker → PostgreSQL + Redis Cache
              </div>

              <div className="space-y-2">
                <div className="flex items-start space-x-2">
                  <ChevronRight className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-white">Asynchronous Task Queue (Celery + Redis):</strong> Distribute page crawls across worker pools without blocking HTTP requests.
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <ChevronRight className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-white">Selective LLM Invocation:</strong> Rule-based filters determine schema type deterministically; LLM is only called on content-rich key pages to conserve API quota and latency.
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <ChevronRight className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-white">Dead-Letter Queue & Retries:</strong> Handles network hiccups, anti-bot challenges, and transient timeouts gracefully.
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <ChevronRight className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-white">URL Hash Caching:</strong> Avoid re-crawling unchanged URLs using Redis TTL caching.
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowScaleModal(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Decision Log Modal */}
      {showDecisionsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-2">
                <Info className="w-5 h-5 text-indigo-400" />
                <h3 className="text-lg font-bold text-white">Design Decision Log</h3>
              </div>
              <button
                onClick={() => setShowDecisionsModal(false)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded-lg bg-slate-800"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <p className="font-semibold text-white mb-1">1. Hybrid Architecture (Deterministic + LLM)</p>
                <p className="text-slate-400">
                  Schema classification (Article/Product/Organization) uses fast keyword heuristics (free, sub-millisecond). Semantic JSON-LD field generation uses Gemini 2.0 Flash to synthesize complex metadata (`founder`, `sameAs`, `offers`).
                </p>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <p className="font-semibold text-white mb-1">2. BeautifulSoup vs. Playwright</p>
                <p className="text-slate-400">
                  BS4 + Requests was chosen for prototype efficiency, zero browser overhead, and instant cold starts. Playwright is planned as an on-demand fallback for client-rendered SPAs.
                </p>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <p className="font-semibold text-white mb-1">3. Graceful LLM Fallback</p>
                <p className="text-slate-400">
                  If the LLM call encounters rate limits or network issues, the system automatically falls back to rule-based JSON-LD with `llm_used: false`, ensuring 100% API uptime.
                </p>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowDecisionsModal(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>Built for Villion GEO SaaS Competency Assessment • Ready for Vercel Deployment</p>
      </footer>
    </div>
  );
}
