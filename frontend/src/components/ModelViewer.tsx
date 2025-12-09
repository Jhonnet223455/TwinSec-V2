import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Database, 
  Play, 
  Settings, 
  Network,
  Activity,
  Gauge,
  Edit2,
  Save
} from "lucide-react";
import { useState } from "react";

interface ModelData {
  name: string;
  type: string;
  components: Array<{
    id: string;
    kind: string;
    label?: string;
    params: Record<string, any>;
  }>;
  connections: Array<{
    from: string;
    to: string;
    label?: string;
    signal?: string;
  }>;
  signals: {
    inputs?: string[];
    outputs?: string[];
    states?: string[];
  };
  solver: {
    method: string;
    dt: number;
  };
  hmi?: {
    widgets: Array<{
      kind: string;
      bind: string;
      label?: string;
    }>;
  };
}

interface ModelViewerProps {
  model: ModelData | null;
  onStartSimulation: () => void;
}

export function ModelViewer({ model, onStartSimulation }: ModelViewerProps) {
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [editedParams, setEditedParams] = useState<Record<string, any>>({});

  if (!model) {
    return (
      <Card className="shadow-panel border-border/50 h-full flex items-center justify-center">
        <CardContent className="text-center text-muted-foreground">
          <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No se ha generado ningún modelo aún</p>
          <p className="text-sm">Usa el editor de prompt para crear un gemelo digital</p>
        </CardContent>
      </Card>
    );
  }

  const getComponentIcon = (kind: string) => {
    switch (kind) {
      case 'tank': return '🛢️';
      case 'valve': return '🔧';
      case 'sensor_level': return '📏';
      case 'pump': return '⚡';
      case 'motor': return '🔌';
      case 'battery': return '🔋';
      case 'solar': return '☀️';
      default: return '⚙️';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'tank': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'microgrid_dc': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'drone': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getReadableParamName = (key: string): string => {
    const names: Record<string, string> = {
      area: "Área",
      h0: "Nivel Inicial",
      hmax: "Nivel Máximo",
      Kv: "Coef. Válvula",
      position: "Posición",
      noise: "Ruido",
      range: "Rango",
      unit: "Unidad"
    };
    return names[key] || key;
  };

  const handleEditComponent = (componentId: string, params: Record<string, any>) => {
    setEditingComponent(componentId);
    setEditedParams({ ...params });
  };

  const handleSaveParams = (componentId: string) => {
    // In a real implementation, this would update the model
    console.log("Guardando parámetros para", componentId, editedParams);
    setEditingComponent(null);
  };

  const handleParamChange = (key: string, value: any) => {
    setEditedParams(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Model Header */}
      <Card className="shadow-panel border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center space-x-2">
                <Network className="h-5 w-5 text-primary" />
                <span>{model.name}</span>
                <Badge className={`${getTypeColor(model.type)} text-xs`}>
                  {model.type.toUpperCase()}
                </Badge>
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Método: {model.solver.method} | dt: {model.solver.dt}s
              </p>
            </div>
            <Button 
              onClick={onStartSimulation}
              className="gradient-safe text-white hover:shadow-cyber"
            >
              <Play className="h-4 w-4 mr-2" />
              Iniciar Simulación
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Components */}
      <Card className="shadow-panel border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-accent" />
            <span>Componentes ({model.components.length})</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {model.components.map((component) => (
              <div 
                key={component.id}
                className="p-4 rounded-lg bg-secondary/50 border border-border/30 hover:border-border/60 transition-colors"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getComponentIcon(component.kind)}</span>
                    <div>
                      <p className="font-semibold text-sm">{component.label || component.id}</p>
                      <p className="text-xs text-muted-foreground font-mono">{component.id}</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => 
                      editingComponent === component.id 
                        ? handleSaveParams(component.id)
                        : handleEditComponent(component.id, component.params)
                    }
                  >
                    {editingComponent === component.id ? (
                      <Save className="h-4 w-4 text-primary" />
                    ) : (
                      <Edit2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                
                <Badge variant="outline" className="text-xs mb-3">
                  {component.kind}
                </Badge>

                <div className="space-y-2">
                  {Object.entries(editingComponent === component.id ? editedParams : component.params)
                    .filter(([key]) => key !== 'unit')
                    .map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-2">
                        <Label className="text-xs font-medium text-muted-foreground min-w-[100px]">
                          {getReadableParamName(key)}:
                        </Label>
                        {editingComponent === component.id ? (
                          <Input
                            type="text"
                            value={Array.isArray(value) ? JSON.stringify(value) : value}
                            onChange={(e) => handleParamChange(key, e.target.value)}
                            className="h-8 text-xs font-mono flex-1"
                          />
                        ) : (
                          <span className="font-mono text-xs text-right flex-1">
                            {Array.isArray(value) ? JSON.stringify(value) : value}
                            {component.params.unit && ` ${component.params.unit}`}
                          </span>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Connections */}
      <Card className="shadow-panel border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="h-5 w-5 text-primary" />
            <span>Conexiones de Señales ({model.connections.length})</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {model.connections.map((connection, index) => (
              <div 
                key={index}
                className="p-3 rounded bg-muted/30 space-y-1"
              >
                <div className="flex items-center space-x-3 text-sm font-mono">
                  <span className="text-sensor-green">{connection.from}</span>
                  <span className="text-muted-foreground">→</span>
                  <span className="text-actuator-blue">{connection.to}</span>
                </div>
                {connection.label && (
                  <p className="text-xs text-muted-foreground">{connection.label}</p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Signals & HMI */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="shadow-panel border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-warning" />
              <span>Señales</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {model.signals.outputs && (
              <div>
                <p className="text-sm font-medium mb-2">Salidas:</p>
                <div className="space-y-1">
                  {model.signals.outputs.map((signal, index) => (
                    <div key={index} className="text-xs font-mono bg-muted/30 p-1 rounded">
                      {signal}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {model.signals.inputs && (
              <div>
                <p className="text-sm font-medium mb-2">Entradas:</p>
                <div className="space-y-1">
                  {model.signals.inputs.map((signal, index) => (
                    <div key={index} className="text-xs font-mono bg-muted/30 p-1 rounded">
                      {signal}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {model.hmi && (
          <Card className="shadow-panel border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Gauge className="h-5 w-5 text-industrial-orange" />
                <span>Widgets HMI</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {model.hmi.widgets.map((widget, index) => (
                  <div 
                    key={index}
                    className="p-2 rounded bg-muted/30 space-y-1"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-mono text-xs">{widget.bind}</span>
                      <Badge variant="outline" className="text-xs">
                        {widget.kind}
                      </Badge>
                    </div>
                    {widget.label && (
                      <p className="text-xs text-muted-foreground">{widget.label}</p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}