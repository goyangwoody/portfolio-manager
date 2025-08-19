import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import type { Portfolio } from "@shared/schema";

interface PortfolioTypeSelectorProps {
  onPortfolioChange: (portfolio: Portfolio) => void;
  currentPortfolio?: Portfolio;
}

export function PortfolioTypeSelector({ onPortfolioChange, currentPortfolio }: PortfolioTypeSelectorProps) {
  const [selectedType, setSelectedType] = useState<"domestic" | "foreign">("domestic");

  const { data: domesticPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "domestic"],
    queryFn: () => fetch("/api/portfolios?type=domestic").then(res => res.json()),
  });

  const { data: foreignPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "foreign"],
    queryFn: () => fetch("/api/portfolios?type=foreign").then(res => res.json()),
  });

  const handleTypeChange = (type: "domestic" | "foreign") => {
    setSelectedType(type);
    const portfolios = type === "domestic" ? domesticPortfolios : foreignPortfolios;
    if (portfolios && portfolios.length > 0) {
      onPortfolioChange(portfolios[0]);
    }
  };

  return (
    <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1 max-w-fit">
      <Button
        variant={selectedType === "domestic" ? "default" : "ghost"}
        size="sm"
        onClick={() => handleTypeChange("domestic")}
        className={`px-4 py-2 text-xs font-medium transition-colors ${
          selectedType === "domestic"
            ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
            : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        }`}
        data-testid="button-domestic-portfolio"
      >
        Domestic
      </Button>
      <Button
        variant={selectedType === "foreign" ? "default" : "ghost"}
        size="sm"
        onClick={() => handleTypeChange("foreign")}
        className={`px-4 py-2 text-xs font-medium transition-colors ${
          selectedType === "foreign"
            ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
            : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        }`}
        data-testid="button-foreign-portfolio"
      >
        Foreign
      </Button>
    </div>
  );
}