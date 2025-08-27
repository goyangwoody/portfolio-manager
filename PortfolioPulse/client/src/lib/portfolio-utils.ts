import { QueryClient } from "@tanstack/react-query";

/**
 * 포트폴리오 관련 모든 쿼리 캐시를 무효화하는 유틸리티 함수
 * 버튼 클릭이나 데이터 변경 시 새로운 정보를 가져오기 위해 사용
 */
export const invalidatePortfolioQueries = (queryClient: QueryClient) => {
  queryClient.invalidateQueries({ 
    predicate: (query) => {
      const queryKey = query.queryKey;
      return Array.isArray(queryKey) && 
             queryKey.some((key: any) => 
               typeof key === 'string' && key.includes('/api/portfolios')
             );
    }
  });
  console.log("🧹 모든 포트폴리오 관련 캐시 무효화 완료");
};

/**
 * 특정 포트폴리오의 쿼리만 무효화하는 함수
 */
export const invalidateSpecificPortfolioQueries = (queryClient: QueryClient, portfolioId: number | string) => {
  queryClient.invalidateQueries({ 
    predicate: (query) => {
      const queryKey = query.queryKey;
      return Array.isArray(queryKey) && 
             queryKey.includes('/api/portfolios') &&
             queryKey.includes(String(portfolioId));
    }
  });
  console.log(`🧹 포트폴리오 ${portfolioId} 관련 캐시 무효화 완료`);
};

/**
 * React Query 설정: 간단하고 확실한 설정
 */
export const getQueryOptions = (enabled: boolean = true) => ({
  enabled,
  staleTime: 0, // 항상 fresh하지 않게 해서 재조회 가능
  refetchOnMount: true, // 마운트 시 무조건 조회
  refetchOnWindowFocus: false, 
  retry: 1,
});

/**
 * 포트폴리오 ID 상수
 */
export const PORTFOLIO_IDS = {
  DOMESTIC: 1,
  FOREIGN: 3,
} as const;

export type PortfolioType = "domestic" | "foreign";
