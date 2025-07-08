import { useState, useEffect } from 'react'
import { Save, AlertCircle } from 'lucide-react'
import { LLMSelector } from '../components/LLMSelector'
import { DEFAULT_MODEL_ID } from '../config/models'

export default function Settings() {
  const [settings, setSettings] = useState({
    maxPositions: 10,
    minConfidence: 0.7,
    defaultLlmModel: DEFAULT_MODEL_ID,
    scrapingRateLimit: 10,
    sources: ['finviz', 'biztoc'],
    autoAnalysis: false,
    analysisInterval: 60, // minutes
  })

  const [apiKeys, setApiKeys] = useState({
    openaiKey: '',
    anthropicKey: '',
  })

  const [saved, setSaved] = useState(false)

  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('marketAnalysisSettings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
    
    const savedApiKeys = localStorage.getItem('marketAnalysisApiKeys')
    if (savedApiKeys) {
      setApiKeys(JSON.parse(savedApiKeys))
    }
  }, [])

  const handleSave = () => {
    // In a real app, this would save to backend
    localStorage.setItem('marketAnalysisSettings', JSON.stringify(settings))
    localStorage.setItem('marketAnalysisApiKeys', JSON.stringify(apiKeys))
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleSourceToggle = (source: string) => {
    setSettings(prev => ({
      ...prev,
      sources: prev.sources.includes(source)
        ? prev.sources.filter(s => s !== source)
        : [...prev.sources, source]
    }))
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          Configure analysis parameters and API keys
        </p>
      </div>

      {/* Analysis Settings */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Configuration</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Maximum Positions
            </label>
            <input
              type="number"
              className="input"
              value={settings.maxPositions}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                maxPositions: parseInt(e.target.value)
              }))}
              min="1"
              max="50"
            />
            <p className="text-xs text-gray-500 mt-1">
              Maximum number of trading positions to generate per analysis
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Confidence
            </label>
            <input
              type="number"
              className="input"
              value={settings.minConfidence}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                minConfidence: parseFloat(e.target.value)
              }))}
              min="0"
              max="1"
              step="0.1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Minimum confidence score required for position recommendations
            </p>
          </div>

          <div className="md:col-span-2">
            <LLMSelector
              value={settings.defaultLlmModel}
              onChange={(value) => setSettings(prev => ({ ...prev, defaultLlmModel: value }))}
              label="Default LLM Model"
              description="Default language model for sentiment analysis"
              showPricing={true}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scraping Rate Limit (per minute)
            </label>
            <input
              type="number"
              className="input"
              value={settings.scrapingRateLimit}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                scrapingRateLimit: parseInt(e.target.value)
              }))}
              min="1"
              max="60"
            />
            <p className="text-xs text-gray-500 mt-1">
              Number of requests per minute per domain
            </p>
          </div>
        </div>
      </div>

      {/* Data Sources */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Sources</h2>
        
        <div className="space-y-3">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="finviz"
              checked={settings.sources.includes('finviz')}
              onChange={() => handleSourceToggle('finviz')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="finviz" className="ml-3 text-sm text-gray-700">
              FinViz - Financial news and market data
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="biztoc"
              checked={settings.sources.includes('biztoc')}
              onChange={() => handleSourceToggle('biztoc')}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="biztoc" className="ml-3 text-sm text-gray-700">
              BizToc - Business and financial news aggregator
            </label>
          </div>
        </div>
      </div>

      {/* Automation */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Automation</h2>
        
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="autoAnalysis"
              checked={settings.autoAnalysis}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                autoAnalysis: e.target.checked
              }))}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="autoAnalysis" className="ml-3 text-sm text-gray-700">
              Enable automatic analysis
            </label>
          </div>
          
          {settings.autoAnalysis && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Interval (minutes)
              </label>
              <input
                type="number"
                className="input max-w-xs"
                value={settings.analysisInterval}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  analysisInterval: parseInt(e.target.value)
                }))}
                min="15"
                max="1440"
              />
              <p className="text-xs text-gray-500 mt-1">
                How often to run automatic analysis (15 minutes to 24 hours)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* API Keys */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">API Keys</h2>
        
        <div className="bg-warning-50 border border-warning-200 rounded-md p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-warning-600 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-warning-800">
                Security Notice
              </h3>
              <p className="text-sm text-warning-700 mt-1">
                API keys are stored locally in your browser. For production use, configure these on the server side.
              </p>
            </div>
          </div>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key
            </label>
            <input
              type="password"
              className="input"
              placeholder="sk-..."
              value={apiKeys.openaiKey}
              onChange={(e) => setApiKeys(prev => ({
                ...prev,
                openaiKey: e.target.value
              }))}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Anthropic API Key
            </label>
            <input
              type="password"
              className="input"
              placeholder="sk-ant-..."
              value={apiKeys.anthropicKey}
              onChange={(e) => setApiKeys(prev => ({
                ...prev,
                anthropicKey: e.target.value
              }))}
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className={`btn ${saved ? 'btn-success' : 'btn-primary'} flex items-center`}
        >
          <Save className="h-4 w-4 mr-2" />
          {saved ? 'Settings Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}