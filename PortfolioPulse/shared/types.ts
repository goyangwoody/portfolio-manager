// TypeScript types for API responses (matching Pydantic schemas)

// ================================
// PORTFOLIO TYPES
// ================================

// 기본 포트폴리오 목록 응답 (포트폴리오 선택용)
export interface PortfolioListResponse {
  id: number;
  name: string;
  currency: string;
}

// KPI 지표가 포함된 포트폴리오 응답 (Overview 페이지용)  
export interface PortfolioSummaryResponse extends PortfolioListResponse {
  total_return?: number;    // 총 수익률 (%)
  sharpe_ratio?: number;    // 샤프 비율
  nav?: number;             // 순자산가치
  aum?: number;             // 총 자산 관리 규모
}

// 기존 Portfolio 인터페이스를 PortfolioSummaryResponse로 매핑
export interface Portfolio {
  id: number;
  name: string;
  currency: string;
  
  // 백엔드 API 응답 필드들
  total_return?: number;
  sharpe_ratio?: number;
  nav?: number;
  aum?: number;
  
  // 기존 코드와의 호환성을 위한 별칭
  totalReturn: number;
  sharpeRatio: number;
  
  // Overview 페이지에서 사용하는 추가 필드들 (선택적)
  volatility?: number;
  maxDrawdown?: number;
  beta?: number;
  cashRatio?: number;       // 현금 비중 (%)
}

// ================================
// PERFORMANCE TYPES
// ================================

export interface PerformanceData {
  date: string;             // Date -> string in JSON
  portfolio_value: number;
  benchmark_value: number;
  daily_return?: number;
  
  // 기존 필드명과의 호환성
  portfolioValue: number;
  benchmarkValue: number;
}

// ================================
// ASSET & HOLDINGS TYPES
// ================================

export interface AssetResponse {
  id: number;
  ticker: string;
  name?: string;
  currency: string;
  asset_class?: string;
}

export interface AssetHoldingResponse {
  id: number;
  name: string;
  ticker: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  day_change: number;       // 일일 변동률 (%)
  weight: number;          // 포트폴리오 내 비중 (%)
  
  // 기존 필드명과의 호환성
  avgPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  dayChange: string;       // "%"를 포함한 문자열로 변환
}

export interface PortfolioHoldingsResponse {
  holdings: AssetHoldingResponse[];
  total_market_value: number;
  cash_balance: number;
  total_value: number;
}

// ================================
// ATTRIBUTION TYPES  
// ================================

export interface AssetClassAttributionResponse {
  id: string;
  asset_class: string;
  allocation: number;       // 비중 (%)
  contribution: number;     // 기여도 (%)
  
  // 기존 필드명과의 호환성
  assetClass: string;
}

export interface TopContributorResponse {
  id: string;
  name: string;
  contribution: number;     // 기여도 (%)
  weight: number;          // 비중 (%)
  return_rate: number;     // 수익률 (%)
  type: "contributor" | "detractor";
  
  // 기존 필드명과의 호환성
  return: number;
}

export interface AttributionAnalysisResponse {
  asset_class_attribution: AssetClassAttributionResponse[];
  top_contributors: TopContributorResponse[];
  top_detractors: TopContributorResponse[];
}

// ================================
// LEGACY COMPATIBILITY TYPES
// ================================

// 기존 코드와의 호환성을 위한 타입들
export interface AttributionData extends AssetClassAttributionResponse {
  assetClass: string;
}

export interface Holding extends TopContributorResponse {
  return: number;
}

export interface Asset extends AssetHoldingResponse {
  portfolioId: string;
  sector: string;
  avgPrice: number;
  averagePurchasePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPL: number;
  realizedPnL: number;
  totalReturn: number;
  cumulativeReturn: number;
  dayChange: string;
}

export interface AssetPerformanceData {
  id: string;
  assetId: string;
  date: string;
  price: number;
}

export interface Benchmark {
  id: string;
  portfolioId: string;
  name: string;
  value: string;
  change: string;
  changePercent: string;
  return: number;
  outperformance: number;
}
