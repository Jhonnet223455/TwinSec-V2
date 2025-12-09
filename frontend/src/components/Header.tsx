import { Shield, Zap, Activity, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const { user, signOut } = useAuth();
  
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Shield className="h-8 w-8 text-primary animate-pulse-glow" />
              <div className="absolute -top-1 -right-1 h-3 w-3 bg-accent rounded-full animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-cyber bg-clip-text text-transparent">
                TwinSec Studio
              </h1>
              <p className="text-sm text-muted-foreground">
                OT Cybersecurity Testing Platform
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <Activity className="h-4 w-4 text-accent" />
              <span className="text-muted-foreground">System Status:</span>
              <span className="text-accent font-mono">ONLINE</span>
            </div>
            
            <Button variant="outline" size="sm" className="border-primary/30 hover:border-primary">
              <Zap className="h-4 w-4 mr-2" />
              Connect SIEM
            </Button>
            
            {user && (
              <div className="flex items-center gap-3 ml-4 pl-4 border-l border-border">
                <span className="text-sm text-muted-foreground">{user.email}</span>
                <Button variant="outline" size="sm" onClick={() => signOut()}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}