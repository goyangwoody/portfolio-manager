import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import type { Portfolio } from "@shared/types";

interface PortfolioTypeSelectorProps {
  onPortfolioChange: (portfolio: Portfolio) => void;
  currentPortfolio?: Portfolio;
}

export function PortfolioTypeSelector({ onPortfolioChange, currentPortfolio }: PortfolioTypeSelectorProps) {
  const [selectedType, setSelectedType] = useState<"domestic" | "foreign">("domestic");
  const queryClient = useQueryClient();

  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
    queryFn: () => fetch("/api/portfolios").then(res => res.json()),
  });

  // 포트폴리오 ID에 따라 타입 매핑 (숫자로 변환해서 비교)
  const domesticPortfolio = portfolios?.find(p => Number(p.id) === 1);
  const foreignPortfolio = portfolios?.find(p => Number(p.id) === 3);

  // 초기 포트폴리오 설정
  useEffect(() => {
    if (domesticPortfolio && !currentPortfolio) {
      console.log("Setting initial portfolio:", domesticPortfolio);
      onPortfolioChange(domesticPortfolio);
    }
  }, [domesticPortfolio, currentPortfolio, onPortfolioChange]);

  // 현재 포트폴리오에 따라 선택된 타입 업데이트
  useEffect(() => {
    if (currentPortfolio) {
      const portfolioId = Number(currentPortfolio.id);
      if (portfolioId === 1) {
        setSelectedType("domestic");
      } else if (portfolioId === 3) {
        setSelectedType("foreign");
      }
    }
  }, [currentPortfolio]);

  const handleTypeChange = (type: "domestic" | "foreign") => {
    console.log(`🔄 Portfolio type changing to: ${type}`);
    
    setSelectedType(type);
    const portfolio = type === "domestic" ? domesticPortfolio : foreignPortfolio;
    
    if (portfolio) {
      console.log(`✅ Selected portfolio:`, portfolio);
      
      // 현재 포트폴리오와 다른 경우에만 캐시 무효화 및 변경 처리
      if (!currentPortfolio || Number(currentPortfolio.id) !== Number(portfolio.id)) {
        console.log(`🔄 Actually changing from portfolio ${currentPortfolio?.id} to ${portfolio.id}`);
        
        // 모든 관련 쿼리 캐시를 무효화 (포트폴리오 관련 모든 API 요청)
        queryClient.invalidateQueries({ 
          predicate: (query) => {
            const queryKey = query.queryKey;
            return Array.isArray(queryKey) && 
                   queryKey.some(key => typeof key === 'string' && key.includes('/api/portfolios'));
          }
        });
        
        // 포트폴리오 변경 이벤트 발생
        onPortfolioChange(portfolio);
        
        console.log(`🧹 Cache invalidated for all portfolio queries`);
      } else {
        console.log(`⏭️ Same portfolio selected (${portfolio.id}), no change needed`);
      }
    } else {
      console.error(`❌ No portfolio found for type: ${type}`);
    }
  };

  return (
    <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1 max-w-fit">
      <Button
        variant={selectedType === "domestic" ? "default" : "ghost"}
        size="sm"
        onClick={() => handleTypeChange("domestic")}
        disabled={!domesticPortfolio}
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
        disabled={!foreignPortfolio}
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