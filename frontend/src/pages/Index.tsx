import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Header } from "@/components/Header";
import { PromptEditor } from "@/components/PromptEditor";
import { ModelViewer } from "@/components/ModelViewer";
import { SimulationDashboard } from "@/components/SimulationDashboard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedModel, setGeneratedModel] = useState(null);
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);
  const [activeTab, setActiveTab] = useState("prompt");
  const { toast } = useToast();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/auth');
    }
  }, [user, loading, navigate]);

  const handleGenerateModel = async (prompt: string, llmProfile: string) => {
    setIsGenerating(true);
    
    try {
      // Simulate AI model generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock model response for tank system
      const mockModel = {
        name: "Sistema de Tanque Industrial",
        type: "tank",
        solver: { method: "euler", dt: 0.1 },
        components: [
          {
            id: "tanque_principal",
            kind: "tank",
            label: "Tanque Principal",
            params: { 
              area: 1.2, 
              h0: 0.5, 
              hmax: 2.0,
              unit: "m"
            }
          },
          {
            id: "valvula_entrada",
            kind: "valve",
            label: "Válvula de Entrada",
            params: { 
              Kv: 1.1, 
              position: 0.8,
              unit: "m³/h"
            }
          },
          {
            id: "valvula_salida", 
            kind: "valve",
            label: "Válvula de Salida",
            params: { 
              Kv: 0.9, 
              position: 0.6,
              unit: "m³/h"
            }
          },
          {
            id: "sensor_nivel",
            kind: "sensor_level",
            label: "Sensor de Nivel",
            params: { 
              noise: 0.005, 
              range: [0, 2],
              unit: "m"
            }
          }
        ],
        connections: [
          { from: "valvula_entrada.q", to: "tanque_principal.q_in", label: "Flujo de entrada" },
          { from: "tanque_principal.h", to: "valvula_salida.h_up", label: "Presión de salida" },
          { from: "tanque_principal.h", to: "sensor_nivel.y", label: "Medición de nivel" }
        ],
        signals: {
          outputs: ["tanque_principal.h", "valvula_entrada.q", "valvula_salida.q"],
          inputs: ["valvula_entrada.setpoint", "valvula_salida.setpoint"]
        },
        hmi: {
          widgets: [
            { kind: "plot", bind: "tanque_principal.h", label: "Nivel del Tanque" },
            { kind: "gauge", bind: "valvula_entrada.q", label: "Caudal de Entrada" },
            { kind: "gauge", bind: "valvula_salida.q", label: "Caudal de Salida" },
            { kind: "alarm", bind: "tanque_principal.h", label: "Alarma de Nivel" }
          ]
        }
      };

      setGeneratedModel(mockModel);
      setActiveTab("model");
      
      toast({
        title: "Model Generated Successfully",
        description: `Generated digital twin model using ${llmProfile}`,
      });
      
    } catch (error) {
      toast({
        title: "Generation Failed", 
        description: "Failed to generate model. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleStartSimulation = () => {
    if (!generatedModel) return;
    
    setIsSimulationRunning(true);
    setActiveTab("simulation");
    
    toast({
      title: "Simulation Started",
      description: "Digital twin is now running in real-time",
    });
  };

  const handleToggleSimulation = () => {
    setIsSimulationRunning(!isSimulationRunning);
    
    toast({
      title: isSimulationRunning ? "Simulation Paused" : "Simulation Resumed",
      description: isSimulationRunning ? "Real-time simulation paused" : "Real-time simulation resumed",
    });
  };

  const handleStopSimulation = () => {
    setIsSimulationRunning(false);
    
    toast({
      title: "Simulation Stopped", 
      description: "Digital twin simulation has been terminated",
      variant: "destructive"
    });
  };

  const handleToggleAttack = (attackType: string, target: string) => {
    toast({
      title: `${attackType} Attack Toggled`,
      description: `Target: ${target}`,
      variant: "destructive"
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-secondary">
            <TabsTrigger value="prompt" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              Model Generator
            </TabsTrigger>
            <TabsTrigger 
              value="model" 
              disabled={!generatedModel}
              className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              Digital Twin
            </TabsTrigger>
            <TabsTrigger 
              value="simulation" 
              disabled={!generatedModel}
              className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              Live Simulation
            </TabsTrigger>
          </TabsList>

          <TabsContent value="prompt" className="space-y-6">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <PromptEditor 
                onGenerate={handleGenerateModel}
                isGenerating={isGenerating}
              />
              <div className="space-y-4">
                <div className="text-center text-muted-foreground p-8 border border-border/30 rounded-lg bg-card/30">
                  <h3 className="text-lg font-semibold mb-2">TwinSec Studio</h3>
                  <p className="text-sm">Generate digital twins from natural language descriptions</p>
                  <p className="text-xs mt-2">Simulate • Test • Secure</p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="model" className="space-y-6">
            <ModelViewer 
              model={generatedModel}
              onStartSimulation={handleStartSimulation}
            />
          </TabsContent>

          <TabsContent value="simulation" className="space-y-6">
            <SimulationDashboard
              isRunning={isSimulationRunning}
              onToggleSimulation={handleToggleSimulation}
              onStopSimulation={handleStopSimulation}
              onToggleAttack={handleToggleAttack}
            />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
