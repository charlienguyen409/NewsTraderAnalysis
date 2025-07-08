import { useState, useEffect, useRef } from 'react';
import { Clock, AlertCircle, Info, AlertTriangle, Zap, ChevronDown, ChevronRight, Users, Database, BarChart3, FileText, Layers } from 'lucide-react';
import { formatDate } from '../lib/utils';

interface ActivityLogEntry {
  id: string;
  timestamp: string;
  level: string;
  category: string;
  action: string;
  message: string;
  details: Record<string, any>;
  session_id?: string;
}

interface ActivityLogSummary {
  total_errors: number;
  errors_by_category: Record<string, number>;
  time_window_hours: number;
}

interface ActivityLogProps {
  sessionId?: string | null;
  showSummary?: boolean;
}

export default function ActivityLog({ sessionId, showSummary = true }: ActivityLogProps) {
  const [logs, setLogs] = useState<ActivityLogEntry[]>([]);
  const [summary, setSummary] = useState<ActivityLogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<{
    level: string;
    category: string;
  }>({
    level: '',
    category: ''
  });
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const wsRef = useRef<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  const fetchLogs = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      }
      
      const params = new URLSearchParams();
      params.append('limit', '100');
      if (filter.level) params.append('level', filter.level);
      if (filter.category) params.append('category', filter.category);
      if (sessionId) params.append('session_id', sessionId);

      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/activity-logs/?${params}`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data);
      }
    } catch (error) {
      console.error('Failed to fetch activity logs:', error);
    } finally {
      if (isRefresh) {
        setRefreshing(false);
      }
    }
  };

  const fetchSummary = async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/activity-logs/summary/?hours=24`);
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      console.error('Failed to fetch activity summary:', error);
    }
  };

  // WebSocket connection setup
  useEffect(() => {
    if (sessionId) {
      // Get the API URL and convert it to WebSocket URL
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const WS_BASE_URL = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
      const wsUrl = `${WS_BASE_URL}/ws/analysis/${sessionId}`;
      
      setConnectionStatus('connecting');
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected for activity log');
        setConnectionStatus('connected');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received WebSocket update:', data);
          
          // Handle different types of WebSocket messages
          if (data.type === 'analysis_status' || data.type === 'analysis_update') {
            fetchLogs(true);
          } else if (data.type === 'activity_log_update') {
            // Real-time activity log update - refresh immediately
            fetchLogs(true);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        setConnectionStatus('disconnected');
        
        // Don't retry if it was a normal closure
        if (event.code !== 1000) {
          console.log('WebSocket will fall back to polling for updates');
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
        console.log('WebSocket connection failed, falling back to polling for updates');
      };
      
      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    }
  }, [sessionId]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const promises = [fetchLogs()];
      if (showSummary) {
        promises.push(fetchSummary());
      }
      await Promise.all(promises);
      setLoading(false);
    };
    
    loadData();
    
    // Set up periodic refresh as fallback (longer interval since we have WebSocket)
    const interval = setInterval(() => {
      if (connectionStatus !== 'connected') {
        fetchLogs(true);
      }
    }, 5000); // Refresh every 5 seconds only if WebSocket not connected
    
    return () => clearInterval(interval);
  }, [filter, sessionId, showSummary, connectionStatus]);

  // Auto-expand latest session and some groups when logs are loaded
  useEffect(() => {
    if (logs.length > 0 && !sessionId) {
      const groupedLogs = groupLogs(logs);
      const latestSession = Object.keys(groupedLogs).sort().pop();
      if (latestSession && !expandedSessions.has(latestSession)) {
        setExpandedSessions(new Set([latestSession]));
      }
    }
  }, [logs, sessionId]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'INFO':
        return <Info className="w-4 h-4 text-blue-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'scraping':
        return <Zap className="w-4 h-4 text-green-500" />;
      case 'llm':
        return <BarChart3 className="w-4 h-4 text-purple-500" />;
      case 'analysis':
        return <FileText className="w-4 h-4 text-indigo-500" />;
      case 'cache':
        return <Layers className="w-4 h-4 text-blue-500" />;
      case 'database':
        return <Database className="w-4 h-4 text-orange-500" />;
      case 'processing':
        return <Zap className="w-4 h-4 text-cyan-500" />;
      case 'progress':
        return <Clock className="w-4 h-4 text-amber-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const getLogBg = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'bg-red-50 border-red-400';
      case 'WARNING':
        return 'bg-yellow-50 border-yellow-400';
      case 'INFO':
        return 'bg-blue-50 border-blue-400';
      default:
        return 'bg-gray-50 border-gray-400';
    }
  };

  // Group logs by session and then by action type
  const groupLogs = (logs: ActivityLogEntry[]) => {
    if (sessionId) {
      // For specific session, group by action type
      const grouped = logs.reduce((acc, log) => {
        const groupKey = `${log.category}:${log.action}`;
        if (!acc[groupKey]) {
          acc[groupKey] = [];
        }
        acc[groupKey].push(log);
        return acc;
      }, {} as Record<string, ActivityLogEntry[]>);
      
      return { [sessionId]: grouped };
    } else {
      // For all logs, group by session first, then by action type
      const sessionGroups = logs.reduce((acc, log) => {
        const sessionKey = log.session_id || 'general';
        if (!acc[sessionKey]) {
          acc[sessionKey] = {};
        }
        
        const groupKey = `${log.category}:${log.action}`;
        if (!acc[sessionKey][groupKey]) {
          acc[sessionKey][groupKey] = [];
        }
        acc[sessionKey][groupKey].push(log);
        return acc;
      }, {} as Record<string, Record<string, ActivityLogEntry[]>>);
      
      return sessionGroups;
    }
  };

  const toggleSessionExpansion = (sessionKey: string) => {
    const newExpanded = new Set(expandedSessions);
    if (newExpanded.has(sessionKey)) {
      newExpanded.delete(sessionKey);
    } else {
      newExpanded.add(sessionKey);
    }
    setExpandedSessions(newExpanded);
  };

  const toggleGroupExpansion = (groupKey: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupKey)) {
      newExpanded.delete(groupKey);
    } else {
      newExpanded.add(groupKey);
    }
    setExpandedGroups(newExpanded);
  };

  const formatGroupTitle = (groupKey: string) => {
    const [category, action] = groupKey.split(':');
    return `${category.charAt(0).toUpperCase() + category.slice(1)} • ${action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
  };

  const getSessionTitle = (sessionKey: string, logs: Record<string, ActivityLogEntry[]>) => {
    if (sessionKey === 'general') return 'General System Logs';
    
    // Find session start log to get better title
    const allSessionLogs = Object.values(logs).flat();
    const sessionStart = allSessionLogs.find(log => log.action.includes('start'));
    
    if (sessionStart) {
      const analysisType = sessionStart.details?.analysis_type || 
                          (sessionStart.action.includes('headline') ? 'Headlines' : 'Full');
      return `Analysis Session (${analysisType}) - ${formatDate(sessionStart.timestamp)}`;
    }
    
    return `Session ${sessionKey.slice(0, 8)} - ${formatDate(allSessionLogs[0]?.timestamp)}`;
  };

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      {showSummary && summary && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Error Summary (Last 24 Hours)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{summary.total_errors}</div>
              <div className="text-sm text-red-600">Total Errors</div>
            </div>
            {Object.entries(summary.errors_by_category).map(([category, count]) => (
              <div key={category} className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-700">{count}</div>
                <div className="text-sm text-gray-600 capitalize">{category} Errors</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Log */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">
            {sessionId ? 'Session Activity' : 'Activity Log'}
          </h3>
          <div className="flex items-center space-x-3">
            {sessionId && (
              <div className="flex items-center text-xs">
                <div className={`w-2 h-2 rounded-full mr-1 ${
                  connectionStatus === 'connected' ? 'bg-green-500' :
                  connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                  'bg-red-500'
                }`}></div>
                <span className="text-gray-600">
                  {connectionStatus === 'connected' ? 'Live' :
                   connectionStatus === 'connecting' ? 'Connecting...' :
                   'Offline'}
                </span>
              </div>
            )}
            {refreshing && (
              <div className="flex items-center text-sm text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                Updating...
              </div>
            )}
          </div>
        </div>
        
        {!sessionId && (
          <div className="flex flex-wrap gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
              <select
                value={filter.level}
                onChange={(e) => setFilter({ ...filter, level: e.target.value })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">All Levels</option>
                <option value="ERROR">Error</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select
                value={filter.category}
                onChange={(e) => setFilter({ ...filter, category: e.target.value })}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">All Categories</option>
                <option value="scraping">Scraping</option>
                <option value="llm">LLM</option>
                <option value="analysis">Analysis</option>
                <option value="system">System</option>
              </select>
            </div>
          </div>
        )}

        {/* Log Entries */}
        <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 -mr-2">
          {logs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p>
                {sessionId 
                  ? 'Activity log will appear here during analysis'
                  : 'No activity logs found'
                }
              </p>
            </div>
          ) : (
            (() => {
              const groupedLogs = groupLogs(logs);
              
              return Object.entries(groupedLogs).map(([sessionKey, sessionGroups]) => (
                <div key={sessionKey} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Session Header */}
                  {!sessionId && (
                    <div 
                      className="bg-gray-50 px-4 py-3 border-b border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => toggleSessionExpansion(sessionKey)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center">
                            {expandedSessions.has(sessionKey) ? (
                              <ChevronDown className="h-4 w-4 text-gray-600" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-gray-600" />
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            <Users className="h-4 w-4 text-gray-600" />
                            <span className="font-medium text-gray-800">
                              {getSessionTitle(sessionKey, sessionGroups)}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                            {Object.keys(sessionGroups).length} group{Object.keys(sessionGroups).length !== 1 ? 's' : ''}
                          </span>
                          <span className="text-xs text-gray-500">
                            {Object.values(sessionGroups).flat().length} log{Object.values(sessionGroups).flat().length !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Session Content */}
                  {(sessionId || expandedSessions.has(sessionKey)) && (
                    <div className="space-y-2 p-2">
                      {Object.entries(sessionGroups).map(([groupKey, groupLogs]) => (
                        <div key={groupKey} className="border border-gray-100 rounded-md overflow-hidden">
                          {/* Group Header */}
                          <div 
                            className="bg-white px-3 py-2 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => toggleGroupExpansion(`${sessionKey}:${groupKey}`)}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <div className="flex items-center">
                                  {expandedGroups.has(`${sessionKey}:${groupKey}`) ? (
                                    <ChevronDown className="h-3 w-3 text-gray-500" />
                                  ) : (
                                    <ChevronRight className="h-3 w-3 text-gray-500" />
                                  )}
                                </div>
                                <div className="flex items-center space-x-2">
                                  {getCategoryIcon(groupLogs[0].category)}
                                  <span className="text-sm font-medium text-gray-700">
                                    {formatGroupTitle(groupKey)}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`text-xs px-2 py-0.5 rounded-full ${
                                  groupLogs.some(log => log.level === 'ERROR') ? 'bg-red-100 text-red-700' :
                                  groupLogs.some(log => log.level === 'WARNING') ? 'bg-yellow-100 text-yellow-700' :
                                  'bg-blue-100 text-blue-700'
                                }`}>
                                  {groupLogs.length} item{groupLogs.length !== 1 ? 's' : ''}
                                </span>
                                <span className="text-xs text-gray-400">
                                  {formatDate(groupLogs[0].timestamp)}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          {/* Group Content */}
                          {expandedGroups.has(`${sessionKey}:${groupKey}`) && (
                            <div className="space-y-2 p-2 bg-gray-50">
                              {groupLogs.map((log) => (
                                <div
                                  key={log.id}
                                  className={`p-3 rounded border-l-3 ${getLogBg(log.level)} bg-white ${
                                    log.category === 'progress' ? 'ring-2 ring-amber-200' : ''
                                  }`}
                                >
                                  <div className="space-y-2">
                                    {/* Log Header */}
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center space-x-2">
                                        {getLevelIcon(log.level)}
                                        <span className="text-xs text-gray-500">
                                          {formatDate(log.timestamp)}
                                        </span>
                                      </div>
                                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                                        log.level === 'ERROR' ? 'bg-red-100 text-red-700' :
                                        log.level === 'WARNING' ? 'bg-yellow-100 text-yellow-700' :
                                        'bg-blue-100 text-blue-700'
                                      }`}>
                                        {log.level}
                                      </span>
                                    </div>
                                    
                                    {/* Message */}
                                    <div className="text-sm text-gray-700 leading-relaxed break-words whitespace-pre-wrap">
                                      {log.category === 'cache' && (
                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mr-2 ${
                                          log.action.includes('hit') 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-orange-100 text-orange-800'
                                        }`}>
                                          {log.action.includes('hit') ? '✓ Cache Hit' : '⚡ Cache Miss'}
                                        </span>
                                      )}
                                      {log.category === 'progress' && (
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 mr-2">
                                          🔄 In Progress
                                        </span>
                                      )}
                                      {log.message}
                                    </div>
                                    
                                    {/* Details */}
                                    {Object.keys(log.details).length > 0 && (
                                      <details className="group">
                                        <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-800 font-medium flex items-center space-x-1">
                                          <span className="group-open:rotate-90 transition-transform">▶</span>
                                          <span>Details ({Object.keys(log.details).length})</span>
                                        </summary>
                                        <div className="mt-2 p-2 bg-gray-100 rounded border text-xs">
                                          <div className="space-y-1">
                                            {Object.entries(log.details).map(([key, value]) => (
                                              <div key={key}>
                                                <span className="font-medium text-gray-700 capitalize">
                                                  {key.replace(/_/g, ' ')}:
                                                </span>
                                                <div className="ml-2">
                                                  {typeof value === 'object' ? (
                                                    <pre className="text-gray-600 whitespace-pre-wrap break-words">
                                                      {JSON.stringify(value, null, 2)}
                                                    </pre>
                                                  ) : (
                                                    <span className="text-gray-600 break-words">
                                                      {String(value)}
                                                    </span>
                                                  )}
                                                </div>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      </details>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ));
            })()
          )}
        </div>
      </div>
    </div>
  );
}