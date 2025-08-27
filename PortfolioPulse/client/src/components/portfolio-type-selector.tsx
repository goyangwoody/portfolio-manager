import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import type { Portfolio } from "@shared/types";

interface PortfolioTypeSelectorProps {
  onPortfolioChange: (portfolio: Portfolio) => void;
  currentPortfolio?: Portfolio;
}

// 포트폴리오 ID 매핑 상수
const PORTFOLIO_IDS = {
  DOMESTIC: 1,
  FOREIGN: 3,
} as const;

type PortfolioType = "domestic" | "foreign";

// 데이터 새로고침 유틸리티 함수
const invalidatePortfolioQueries = (queryClient: any) => {
  queryClient.invalidateQueries({ 
    predicate: (query: any) => {
      const queryKey = query.queryKey;
      return Array.isArray(queryKey) && 
             queryKey.some((key: any) => 
               typeof key === 'string' && key.includes('/api/portfolios')
             );
    }
  });
  console.log("🧹 모든 포트폴리오 관련 캐시 무효화 완료");
};

export function PortfolioTypeSelector({ onPortfolioChange, currentPortfolio }: PortfolioTypeSelectorProps) {
  const [selectedType, setSelectedType] = useState<PortfolioType>("domestic");
  const queryClient = useQueryClient();

  // 포트폴리오 데이터 조회
  const { data: portfolios, isLoading } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
    queryFn: () => fetch("/api/portfolios").then(res => res.json()),
    staleTime: 0,
    gcTime: 300000, // 5분간 캐시 유지
  });

  // ID 기반 포트폴리오 매핑
  const domesticPortfolio = portfolios?.find(p => Number(p.id) === PORTFOLIO_IDS.DOMESTIC);
  const foreignPortfolio = portfolios?.find(p => Number(p.id) === PORTFOLIO_IDS.FOREIGN);

  // 디버깅 로그
  useEffect(() => {
    console.log("=== 포트폴리오 선택기 디버깅 ===");
    console.log("🔍 portfolios 상태:", portfolios);
    console.log("🔍 isLoading:", isLoading);
    console.log("🏠 domesticPortfolio:", domesticPortfolio);
    console.log("🌍 foreignPortfolio:", foreignPortfolio);
    console.log("📌 currentPortfolio:", currentPortfolio);
    console.log("🎯 selectedType:", selectedType);
    console.log("==================");
  }, [portfolios, isLoading, domesticPortfolio, foreignPortfolio, currentPortfolio, selectedType]);

  // 초기 포트폴리오 설정 (Domestic 우선)
  useEffect(() => {
    if (domesticPortfolio && !currentPortfolio) {
      console.log("🏠 초기 포트폴리오 설정: Domestic");
      onPortfolioChange(domesticPortfolio);
    }
  }, [domesticPortfolio, currentPortfolio, onPortfolioChange]);

  // 현재 포트폴리오에 따른 UI 상태 동기화
  useEffect(() => {
    if (currentPortfolio) {
      const portfolioId = Number(currentPortfolio.id);
      if (portfolioId === PORTFOLIO_IDS.DOMESTIC) {
        setSelectedType("domestic");
      } else if (portfolioId === PORTFOLIO_IDS.FOREIGN) {
        setSelectedType("foreign");
      }
    }
  }, [currentPortfolio]);

  // 포트폴리오 변경 핸들러 (재사용 가능한 로직)
  const handlePortfolioChange = (type: PortfolioType) => {
    console.log(`🔄 포트폴리오 타입 변경: ${type}`);
    
    const targetPortfolio = type === "domestic" ? domesticPortfolio : foreignPortfolio;
    
    if (!targetPortfolio) {
      console.error(`❌ ${type} 포트폴리오를 찾을 수 없습니다`);
      return;
    }

    // 실제로 다른 포트폴리오인지 확인
    const currentId = currentPortfolio?.id;
    const targetId = targetPortfolio.id;
    
    if (currentId && Number(currentId) === Number(targetId)) {
      console.log(`⏭️ 동일한 포트폴리오 (ID: ${targetId}), 변경 불필요`);
      return;
    }

    console.log(`🔄 포트폴리오 변경: ${currentId} → ${targetId}`);
    
    // UI 상태 업데이트
    setSelectedType(type);
    
    // 캐시 무효화 (모든 관련 데이터 새로고침)
    invalidatePortfolioQueries(queryClient);
    
    // 부모 컴포넌트에 변경 알림
    onPortfolioChange(targetPortfolio);
    
    console.log(`✅ 포트폴리오 변경 완료: ${targetPortfolio.name} (ID: ${targetId})`);
  };

  if (isLoading) {
    return (
      <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1 max-w-fit">
        <div className="px-4 py-2 text-xs text-gray-500">로딩 중...</div>
      </div>
    );
  }

  // 강제 렌더링 체크
  console.log("🔄 렌더링 시점 체크:");
  console.log("- portfolios:", portfolios);
  console.log("- domesticPortfolio:", domesticPortfolio);
  console.log("- foreignPortfolio:", foreignPortfolio);

  return (
    <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1 max-w-fit">
      <Button
        variant={selectedType === "domestic" ? "default" : "ghost"}
        size="sm"
        onClick={() => handlePortfolioChange("domestic")}
        disabled={!domesticPortfolio}
        className={`px-4 py-2 text-xs font-medium transition-colors ${
          selectedType === "domestic"
            ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
            : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        }`}
        data-testid="button-domestic-portfolio"
      >
        Domestic {portfolios ? `(${domesticPortfolio?.name || 'ID=1 없음'})` : '(로딩중)'}
      </Button>
      <Button
        variant={selectedType === "foreign" ? "default" : "ghost"}
        size="sm"
        onClick={() => handlePortfolioChange("foreign")}
        disabled={!foreignPortfolio}
        className={`px-4 py-2 text-xs font-medium transition-colors ${
          selectedType === "foreign"
            ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
            : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        }`}
        data-testid="button-foreign-portfolio"
      >
        Foreign {portfolios ? `(${foreignPortfolio?.name || 'ID=3 없음'})` : '(로딩중)'}
      </Button>
    </div>
  );
}