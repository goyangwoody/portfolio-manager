import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";
import { BottomNavigation } from "@/components/bottom-navigation";
import Performance from "@/pages/performance";
import Attribution from "@/pages/attribution";
import RiskAllocation from "@/pages/risk-allocation";
import Assets from "@/pages/assets";
import NotFound from "@/pages/not-found";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <div className="min-h-screen bg-background">
            <main>
              <Switch>
                <Route path="/" component={Performance} />
                <Route path="/performance" component={Performance} />
                <Route path="/attribution" component={Attribution} />
                <Route path="/assets" component={Assets} />
                <Route path="/risk" component={RiskAllocation} />
                <Route component={NotFound} />
              </Switch>
            </main>
            <BottomNavigation />
          </div>
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
