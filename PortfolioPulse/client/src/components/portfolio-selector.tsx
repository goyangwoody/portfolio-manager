import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import type { Portfolio } from "@shared/types";

interface PortfolioSelectorProps {
  onPortfolioChange: (portfolio: Portfolio) => void;
  currentPortfolio?: Portfolio;
  className?: string;
}

type PortfolioType = "core" | "usd_core";

export function PortfolioSelector({ 
  onPortfolioChange, 
  currentPortfolio,
  className = ""
}: PortfolioSelectorProps) {
  const [selectedType, setSelectedType] = useState<PortfolioType>("core");

  // 선택된 타입에 따른 포트폴리오 데이터 조회
  const { data: portfoliosData, isLoading, refetch } = useQuery({
    queryKey: ["/api/portfolios", selectedType],
    queryFn: async () => {
      console.log(`🔍 포트폴리오 조회: ${selectedType}`);
      const response = await fetch(`/api/portfolios?portfolio_type=${selectedType}&include_kpi=true&include_chart=true`);
      
      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ 포트폴리오 데이터 수신:`, data);
      
      // 백엔드 응답에서 portfolios 배열 추출
      const portfoliosList = data.portfolios || data;
      
      // 백엔드 응답을 프론트엔드 형식으로 변환
      const transformedData = portfoliosList.map((portfolio: any) => ({
        ...portfolio,
        // 기존 필드명과의 호환성을 위한 매핑
        totalReturn: portfolio.total_return || 0,
        sharpeRatio: portfolio.sharpe_ratio || 0,
        cashRatio: portfolio.cash_ratio || 0,
        // 차트 데이터 추가
        chartData: portfolio.chart_data || [],
      }));
      
      return transformedData;
    },
    enabled: true, // 항상 활성화
  });

  // 포트폴리오 타입 변경 처리
  const handleTypeChange = (type: PortfolioType) => {
    console.log(`🔄 포트폴리오 타입 변경: ${selectedType} → ${type}`);
    setSelectedType(type);
    
    // 타입이 변경되면 React Query가 자동으로 새로운 API를 호출함
    // 새로운 데이터가 로드되면 useEffect에서 포트폴리오 변경 처리
  };

  // 포트폴리오 데이터 변경 시 첫 번째 포트폴리오 자동 선택
  useEffect(() => {
    if (portfoliosData && portfoliosData.length > 0) {
      const firstPortfolio = portfoliosData[0];
      console.log(`🎯 새로운 포트폴리오 선택:`, firstPortfolio);
      onPortfolioChange(firstPortfolio);
    }
  }, [portfoliosData, onPortfolioChange]);

  // 초기 로딩 시 Core 포트폴리오 자동 선택
  useEffect(() => {
    if (!currentPortfolio && portfoliosData && portfoliosData.length > 0) {
      console.log(`🚀 초기 포트폴리오 설정:`, portfoliosData[0]);
      onPortfolioChange(portfoliosData[0]);
    }
  }, [portfoliosData, currentPortfolio, onPortfolioChange]);

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Portfolio:
      </span>
      <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        <Button
          variant={selectedType === "core" ? "default" : "ghost"}
          size="sm"
          onClick={() => handleTypeChange("core")}
          disabled={isLoading}
          className={`px-4 py-2 text-xs font-medium transition-colors ${
            selectedType === "core"
              ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
          }`}
          data-testid="button-core-portfolio"
        >
          {isLoading && selectedType === "core" ? "Loading..." : "Core"}
        </Button>
        <Button
          variant={selectedType === "usd_core" ? "default" : "ghost"}
          size="sm"
          onClick={() => handleTypeChange("usd_core")}
          disabled={isLoading}
          className={`px-4 py-2 text-xs font-medium transition-colors ${
            selectedType === "usd_core"
              ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
          }`}
          data-testid="button-usd-core-portfolio"
        >
          {isLoading && selectedType === "usd_core" ? "Loading..." : "USD Core"}
        </Button>
      </div>
      {currentPortfolio && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          ({currentPortfolio.name})
        </span>
      )}
      {isLoading && (
        <span className="text-xs text-blue-500 dark:text-blue-400">
          Loading...
        </span>
      )}
    </div>
  );
}
