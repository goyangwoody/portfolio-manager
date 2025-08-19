import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";
import { BottomNavigation } from "@/components/bottom-navigation";
import { PortfolioTypeSelector } from "@/components/portfolio-type-selector";
import Overview from "@/pages/overview";
import Performance from "@/pages/performance";
import Attribution from "@/pages/attribution";
import RiskAllocation from "@/pages/risk-allocation";
import Assets from "@/pages/assets";
import NotFound from "@/pages/not-found";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import type { Portfolio } from "@shared/schema";

function Header() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | null>(null);
  
  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  // Set initial portfolio when data loads
  if (portfolios && portfolios.length > 0 && !currentPortfolio) {
    setCurrentPortfolio(portfolios[0]);
  }

  const handlePortfolioChange = (portfolio: Portfolio) => {
    setCurrentPortfolio(portfolio);
    // Update other queries to use the new portfolio
    queryClient.invalidateQueries();
  };

  return (
    <header className="bg-white dark:bg-dark-card shadow-sm px-4 py-3 sticky top-0 z-40">
      <div className="max-w-md mx-auto">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-dark-text" data-testid="text-portfolio-name">
              {currentPortfolio?.name || "Loading..."}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400" data-testid="text-last-updated">
              Updated 2 hours ago
            </p>
          </div>
          <ThemeToggle />
        </div>
        <div className="flex justify-center">
          <PortfolioTypeSelector 
            currentPortfolio={currentPortfolio || undefined}
            onPortfolioChange={handlePortfolioChange}
          />
        </div>
      </div>
    </header>
  );
}

function Router() {
  return (
    <>
      <Header />
      <main>
        <Switch>
          <Route path="/" component={Overview} />
          <Route path="/performance" component={Performance} />
          <Route path="/attribution" component={Attribution} />
          <Route path="/assets" component={Assets} />
          <Route path="/risk" component={RiskAllocation} />
          <Route component={NotFound} />
        </Switch>
      </main>
      <BottomNavigation />
    </>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <div className="min-h-screen bg-gray-50 dark:bg-dark-bg text-gray-900 dark:text-dark-text">
            <Toaster />
            <Router />
          </div>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
