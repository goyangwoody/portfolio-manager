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
  cash_ratio?: number;      // 현금 비중 (%)
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
  cash_ratio?: number;
  
  // 기존 코드와의 호환성을 위한 별칭
  totalReturn: number;
  sharpeRatio: number;
  cashRatio?: number;       // 현금 비중 (%)
  
  // 차트 데이터 (Overview 페이지용)
  chartData?: Array<{
    date: string;
    nav: number;
    benchmark: number;
  }>;
}

// ================================
// PERFORMANCE TYPES
// ================================

// ================================
// PERFORMANCE TYPES
// ================================

// 최근 수익률 데이터
export interface RecentReturnData {
  daily_return?: number;    // 1일 수익률 (%)
  weekly_return?: number;   // 1주 수익률 (%)
  monthly_return?: number;  // 1개월 수익률 (%)
}

// 일별 수익률 차트 포인트
export interface DailyReturnPoint {
  date: string;             // Date -> string in JSON
  daily_return: number;     // 일별 수익률 (%)
}

// 벤치마크 수익률 데이터
export interface BenchmarkReturn {
  name: string;             // 벤치마크 이름
  return_pct: number;       // 수익률 (%)
  outperformance: number;   // 아웃퍼포먼스 (%)
}

// All Time 성과 데이터 응답
export interface PerformanceAllTimeResponse {
  recent_returns: RecentReturnData;
  recent_week_daily_returns: DailyReturnPoint[];
  daily_returns: DailyReturnPoint[];  // chart_period에 따른 일별 수익률 데이터
  benchmark_returns: BenchmarkReturn[];
}

// Custom Period 성과 데이터 응답
export interface PerformanceCustomPeriodResponse {
  cumulative_return: number;       // 기간 누적 수익률 (%)
  daily_returns: DailyReturnPoint[]; // 기간 중 일별 수익률
  benchmark_returns: BenchmarkReturn[]; // 기간 중 벤치마크 대비 수익률
  start_date: string;              // 분석 시작일 (Date -> string in JSON)
  end_date: string;                // 분석 종료일 (Date -> string in JSON)
  period_type: string;             // 기간 타입 (week/month)
}

// 기존 Performance 데이터 (다른 기간용)
export interface PerformanceData {
  date: string;             // Date -> string in JSON
  portfolio_value: number;
  benchmark_value: number;
  daily_return?: number;
  
  // 기존 필드명과의 호환성
  portfolioValue: number;
  benchmarkValue: number;
}

// 벤치마크 데이터 (기존 코드 호환성)
export interface Benchmark {
  id: string;
  name: string;
  return: number;           // 수익률 (%)
  outperformance: number;   // 아웃퍼포먼스 (%)
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
