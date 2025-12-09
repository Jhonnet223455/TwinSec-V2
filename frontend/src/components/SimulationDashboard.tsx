import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Play, 
  Pause, 
  Square, 
  Shield, 
  AlertTriangle, 
  Activity,
  Gauge,
  Zap,
  Wifi,
  WifiOff,
  Target
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TelemetryData {
  timestamp: number;
  vars: Record<string, number>;
  ids?: {
    score: number;
    label: string;
    explanation?: Record<string, number>;
  };
}

interface SimulationDashboardProps {
  isRunning: boolean;
  onToggleSimulation: () => void;
  onStopSimulation: () => void;
  onToggleAttack: (attackType: string, target: string) => void;
}

export function SimulationDashboard({ 
  isRunning, 
  onToggleSimulation, 
  onStopSimulation,
  onToggleAttack 
}: SimulationDashboardProps) {
  const [telemetryData, setTelemetryData] = useState<TelemetryData[]>([]);
  const [currentData, setCurrentData] = useState<TelemetryData | null>(null);
  const [activeAttacks, setActiveAttacks] = useState<Record<string, boolean>>({});
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');

  // Simulate real-time data
  useEffect(() => {
    if (!isRunning) return;

    setConnectionStatus('connected');
    
    const interval = setInterval(() => {
      const timestamp = Date.now();
      const time = timestamp / 1000;
      
      // Simulate tank system with some noise and attack effects
      const baseLevel = 0.5 + 0.3 * Math.sin(time * 0.1);
      const baseInFlow = 2.0 + 0.5 * Math.sin(time * 0.05);
      const baseOutFlow = 1.8 + 0.3 * Math.cos(time * 0.07);
      
      // Apply attack effects
      const level = activeAttacks['FDI_level'] ? 
        baseLevel + 0.2 * Math.random() : 
        baseLevel + 0.02 * (Math.random() - 0.5);
      
      const inFlow = activeAttacks['DoS_valve'] ? 
        0 : baseInFlow + 0.1 * (Math.random() - 0.5);
      
      const outFlow = baseOutFlow + 0.05 * (Math.random() - 0.5);

      // Simple anomaly detection simulation
      const idsScore = activeAttacks['FDI_level'] || activeAttacks['DoS_valve'] ?
        0.1 + 0.4 * Math.random() : 0.9 + 0.1 * Math.random();
      
      const newData: TelemetryData = {
        timestamp,
        vars: {
          'T1.h': Number(level.toFixed(3)),
          'V_in.q': Number(inFlow.toFixed(3)),
          'V_out.q': Number(outFlow.toFixed(3))
        },
        ids: {
          score: Number(idsScore.toFixed(3)),
          label: idsScore < 0.5 ? 'anomaly' : 'normal',
          explanation: {
            'T1.h': Number((0.3 + 0.2 * Math.random()).toFixed(2)),
            'V_in.q': Number((0.2 + 0.3 * Math.random()).toFixed(2)),
            'V_out.q': Number((0.1 + 0.2 * Math.random()).toFixed(2))
          }
        }
      };

      setCurrentData(newData);
      setTelemetryData(prev => {
        const updated = [...prev, newData];
        return updated.slice(-50); // Keep last 50 points
      });
    }, 200);

    return () => clearInterval(interval);
  }, [isRunning, activeAttacks]);

  const handleAttackToggle = (attackKey: string, attackType: string, target: string) => {
    const newState = !activeAttacks[attackKey];
    setActiveAttacks(prev => ({ ...prev, [attackKey]: newState }));
    onToggleAttack(attackType, target);
  };

  const getVariableColor = (varName: string) => {
    if (varName.includes('h')) return '#00bcd4'; // Level - cyan
    if (varName.includes('V_in')) return '#4caf50'; // Inlet - green  
    if (varName.includes('V_out')) return '#ff9800'; // Outlet - orange
    return '#9c27b0'; // Default - purple
  };

  const attackButtons = [
    { key: 'FDI_level', type: 'FDI', target: 'T1.h', label: 'FDI Attack on Level Sensor', icon: Target },
    { key: 'DoS_valve', type: 'DoS', target: 'V_in', label: 'DoS Attack on Inlet Valve', icon: WifiOff },
  ];

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <Card className="shadow-panel border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-primary" />
              <span>Simulation Control</span>
              <Badge 
                variant="outline" 
                className={`${connectionStatus === 'connected' ? 'border-accent text-accent' : 'border-muted-foreground'}`}
              >
                <div className="flex items-center space-x-1">
                  {connectionStatus === 'connected' ? (
                    <Wifi className="h-3 w-3" />
                  ) : (
                    <WifiOff className="h-3 w-3" />
                  )}
                  <span>{connectionStatus.toUpperCase()}</span>
                </div>
              </Badge>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                onClick={onToggleSimulation}
                variant={isRunning ? "outline" : "default"}
                size="sm"
                className={isRunning ? "" : "gradient-safe text-white"}
              >
                {isRunning ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Resume
                  </>
                )}
              </Button>
              <Button
                onClick={onStopSimulation}
                variant="outline"
                size="sm"
                className="border-destructive/30 text-destructive hover:bg-destructive/10"
              >
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Real-time Gauges */}
      {currentData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(currentData.vars).map(([varName, value]) => (
            <Card key={varName} className="shadow-panel border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{varName}</p>
                    <p className="text-2xl font-bold font-mono" style={{ color: getVariableColor(varName) }}>
                      {value.toFixed(3)}
                    </p>
                  </div>
                  <Gauge className="h-8 w-8" style={{ color: getVariableColor(varName) }} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Charts */}
      {telemetryData.length > 0 && (
        <Card className="shadow-panel border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-primary" />
              <span>Real-time Telemetry</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={telemetryData.map(d => ({ 
                  time: new Date(d.timestamp).toLocaleTimeString(),
                  ...d.vars
                }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="time" 
                    stroke="hsl(var(--muted-foreground))"
                    fontSize={12}
                  />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  {Object.keys(currentData?.vars || {}).map(varName => (
                    <Line
                      key={varName}
                      type="monotone"
                      dataKey={varName}
                      stroke={getVariableColor(varName)}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Attack Panel */}
      <Card className="shadow-panel border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5 text-destructive" />
            <span>Cyber Attack Simulation</span>
            <Badge variant="outline" className="text-xs border-destructive/30 text-destructive">
              TESTING MODE
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {attackButtons.map(({ key, type, target, label, icon: Icon }) => (
              <Button
                key={key}
                onClick={() => handleAttackToggle(key, type, target)}
                variant={activeAttacks[key] ? "destructive" : "outline"}
                className={`justify-start h-auto p-4 ${
                  activeAttacks[key] 
                    ? "animate-danger-pulse" 
                    : "border-destructive/30 text-destructive hover:bg-destructive/10"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className="h-5 w-5" />
                  <div className="text-left">
                    <p className="font-medium">{label}</p>
                    <p className="text-xs opacity-80">Target: {target}</p>
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* IDS Panel */}
      {currentData?.ids && (
        <Card className="shadow-panel border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="h-5 w-5 text-warning" />
              <span>Intrusion Detection System</span>
              <Badge 
                variant="outline" 
                className={`${
                  currentData.ids.label === 'anomaly' 
                    ? 'border-destructive text-destructive' 
                    : 'border-accent text-accent'
                }`}
              >
                {currentData.ids.label.toUpperCase()}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Anomaly Score:</span>
                <span className="text-lg font-mono" style={{ 
                  color: currentData.ids.score < 0.5 ? 'hsl(var(--destructive))' : 'hsl(var(--accent))' 
                }}>
                  {currentData.ids.score.toFixed(3)}
                </span>
              </div>
              
              {currentData.ids.explanation && (
                <div>
                  <p className="text-sm font-medium mb-2">SHAP Explanation:</p>
                  <div className="space-y-2">
                    {Object.entries(currentData.ids.explanation).map(([variable, importance]) => (
                      <div key={variable} className="flex items-center justify-between text-sm">
                        <span className="font-mono">{variable}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-warning transition-all duration-300"
                              style={{ width: `${importance * 100}%` }}
                            />
                          </div>
                          <span className="font-mono text-xs w-12 text-right">
                            {importance.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}