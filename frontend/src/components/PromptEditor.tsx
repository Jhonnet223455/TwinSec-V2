import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Bot, Send, Cpu, Cloud, Server } from "lucide-react";

interface PromptEditorProps {
  onGenerate: (prompt: string, llmProfile: string) => void;
  isGenerating: boolean;
}

export function PromptEditor({ onGenerate, isGenerating }: PromptEditorProps) {
  const [prompt, setPrompt] = useState("");
  const [llmProfile, setLlmProfile] = useState("openai:gpt-4o-mini");

  const examplePrompts = [
    "Tanque de 5 m³ con válvula de entrada y salida, sensor de nivel, muestreo 10 Hz",
    "Microred DC con 3 fuentes solares, 2 baterías y cargas variables",
    "Sistema de control de dron con sensores IMU y GPS, actuadores de motor",
    "Proceso industrial con bomba centrífuga, medidor de flujo y controlador PID"
  ];

  const handleGenerate = () => {
    if (prompt.trim() && !isGenerating) {
      onGenerate(prompt, llmProfile);
    }
  };

  return (
    <Card className="shadow-panel border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Bot className="h-5 w-5 text-primary" />
          <span>Natural Language Model Generator</span>
          <Badge variant="outline" className="text-xs">
            AI-Powered
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">LLM Provider</label>
          <Select value={llmProfile} onValueChange={setLlmProfile}>
            <SelectTrigger className="bg-secondary border-border/50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="openai:gpt-4o-mini">
                <div className="flex items-center space-x-2">
                  <Cloud className="h-4 w-4" />
                  <span>OpenAI GPT-4o Mini</span>
                </div>
              </SelectItem>
              <SelectItem value="anthropic:claude-3-haiku">
                <div className="flex items-center space-x-2">
                  <Cloud className="h-4 w-4" />
                  <span>Anthropic Claude 3 Haiku</span>
                </div>
              </SelectItem>
              <SelectItem value="azure:gpt-4">
                <div className="flex items-center space-x-2">
                  <Cloud className="h-4 w-4" />
                  <span>Azure OpenAI GPT-4</span>
                </div>
              </SelectItem>
              <SelectItem value="local:llama3">
                <div className="flex items-center space-x-2">
                  <Server className="h-4 w-4" />
                  <span>Local LLaMA 3 (On-Premise)</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">System Description</label>
          <Textarea
            placeholder="Describe su sistema dinámico en lenguaje natural..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="min-h-32 bg-secondary border-border/50 font-mono text-sm"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">
            Ejemplos (click para usar):
          </label>
          <div className="grid grid-cols-1 gap-2">
            {examplePrompts.map((example, index) => (
              <button
                key={index}
                onClick={() => setPrompt(example)}
                className="text-left p-2 rounded-md bg-muted/50 hover:bg-muted text-sm border border-border/30 hover:border-primary/30 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <Button 
          onClick={handleGenerate}
          disabled={!prompt.trim() || isGenerating}
          className="w-full gradient-cyber text-white hover:shadow-cyber"
        >
          {isGenerating ? (
            <>
              <Cpu className="h-4 w-4 mr-2 animate-spin" />
              Generando modelo...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Generar Modelo Digital
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}