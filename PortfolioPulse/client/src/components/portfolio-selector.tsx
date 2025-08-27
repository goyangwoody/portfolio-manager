import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import type { Portfolio } from "@shared/types";

interface PortfolioSelectorProps {
  onPortfolioChange: (portfolio: Portfolio) => void;
  currentPortfolio?: Portfolio;
  className?: string;
}

type PortfolioType = "domestic" | "foreign";

export function PortfolioSelector({ 
  onPortfolioChange, 
  currentPortfolio,
  className = ""
}: PortfolioSelectorProps) {
  const [selectedType, setSelectedType] = useState<PortfolioType>("domestic");

  // 포트폴리오 타입별 데이터 조회
  const { data: domesticPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios/by-type", "domestic"],
    queryFn: async () => {
      const response = await fetch("/api/portfolios/by-type?type=domestic");
      const data = await response.json();
      return data.portfolios || [];
    },
  });

  const { data: foreignPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios/by-type", "foreign"], 
    queryFn: async () => {
      const response = await fetch("/api/portfolios/by-type?type=foreign");
      const data = await response.json();
      return data.portfolios || [];
    },
  });

  // 포트폴리오 타입 변경 처리
  const handleTypeChange = (type: PortfolioType) => {
    setSelectedType(type);
    const portfolios = type === "domestic" ? domesticPortfolios : foreignPortfolios;
    if (portfolios && portfolios.length > 0) {
      onPortfolioChange(portfolios[0]);
    }
  };

  // 초기 포트폴리오 설정
  useEffect(() => {
    if (!currentPortfolio && domesticPortfolios && domesticPortfolios.length > 0) {
      onPortfolioChange(domesticPortfolios[0]);
    }
  }, [domesticPortfolios, currentPortfolio, onPortfolioChange]);

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Portfolio:
      </span>
      <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
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
      {currentPortfolio && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          ({currentPortfolio.name})
        </span>
      )}
    </div>
  );
}
