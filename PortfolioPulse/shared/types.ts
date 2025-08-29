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

// KPI 지표가 포함된 포트폴리오 응답 (Hero Cover 섹션용)  
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
  
  // 차트 데이터 (Hero Cover 섹션용)
  chartData?: Array<{
    date: string;
    nav: number;
    benchmark: number;
  }>;
}

// 포트폴리오 목록 응답 래퍼 (백엔드 PortfoliosResponse와 일치)
export interface PortfoliosResponse {
  portfolios: PortfolioListResponse[];
  total_count?: number;
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
  symbol: string;           // 벤치마크 심볼
  return_pct: number;       // 수익률 (%)
  excess_return: number;    // 초과 수익률 (%)
  outperformance: number;   // 아웃퍼포먼스 (%) - 백워드 호환성
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
// ATTRIBUTION TYPES (TWR 기반)
// ================================

// 자산 필터 옵션
export type AssetFilter = "all" | "domestic" | "foreign";

// 일별 포트폴리오 수익률
export interface DailyPortfolioReturn {
  date: string;            // Date -> string in JSON
  daily_return: number;    // 일별 포트폴리오 수익률 (%)
  portfolio_value?: number; // 포트폴리오 가치 (선택적)
}

// 자산별 비중 변화 추이
export interface AssetWeightTrend {
  date: string;            // Date -> string in JSON  
  weight: number;          // 자산 비중 (%)
}

// 자산별 TWR 수익률 추이
export interface AssetReturnTrend {
  date: string;            // Date -> string in JSON
  cumulative_twr: number;  // 누적 TWR 수익률 (%)
  daily_twr: number;       // 일별 TWR 수익률 (%)
}

// 개별 자산 기여도 (TWR 기반)
export interface AssetContribution {
  asset_id: number;
  ticker: string;
  name: string;
  asset_class: string;
  region: string;          // domestic/foreign
  
  // 현재 상태
  current_allocation: number;  // 현재 비중 (%)
  current_price?: number;      // 현재가
  
  // 기간별 통계
  avg_weight: number;      // 평균 비중 (%)
  period_return: number;   // 자산 기간 TWR 수익률 (%)
  contribution: number;    // 포트폴리오 수익률 기여도 (%)
  
  // 상세 데이터 (드릴다운용)
  weight_trend?: AssetWeightTrend[]; // 비중 변화 추이
  return_trend?: AssetReturnTrend[]; // TWR 수익률 추이
}

// 자산클래스별 기여도 (TWR 기반)
export interface AssetClassContribution {
  asset_class: string;     // 자산 클래스명
  
  // 현재 상태
  current_allocation: number; // 현재 비중 (%)
  
  // 기간별 통계
  avg_weight: number;      // 평균 비중 (%)
  contribution: number;    // 포트폴리오 수익률 기여도 (%)
  
  // 차트 데이터
  weight_trend: AssetWeightTrend[]; // 자산클래스 비중 변화 추이
  return_trend: AssetReturnTrend[]; // 자산클래스 TWR 수익률 추이
  
  // 구성 자산들
  assets: AssetContribution[]; // 자산클래스 내 자산들
}

// 개별 자산 가격 성과 데이터
export interface PricePerformancePoint {
  date: string;            // Date -> string in JSON
  performance: number;     // 정규화된 성과 (기준일=0%)
}

// 개별 자산 상세 정보 (드릴다운용)
export interface AssetDetailResponse {
  asset_id: number;
  ticker: string;
  name: string;
  asset_class: string;
  region: string;
  
  // 현재 포지션 정보
  current_allocation: number; // 현재 비중 (%)
  current_price: number;      // 현재가
  nav_return: number;         // NAV 수익률 (%)
  twr_contribution: number;   // TWR 기여도 (%)
  
  // 차트 데이터
  price_performance: PricePerformancePoint[]; // 가격 성과 차트
}

// All Time 기여도 분석 응답
export interface AttributionAllTimeResponse {
  // 포트폴리오 전체 성과
  total_twr: number;       // 총 TWR 수익률 (%)
  daily_returns: DailyPortfolioReturn[]; // 일별 포트폴리오 수익률
  
  // 자산클래스별 기여도 (차트 데이터 포함)
  asset_class_contributions: AssetClassContribution[]; // 자산클래스별 기여도
  
  // 상위/하위 기여 자산
  top_contributors: AssetContribution[];   // 상위 기여 자산
  top_detractors: AssetContribution[];     // 상위 손실 자산
  
  // 필터 정보
  asset_filter: AssetFilter; // 적용된 자산 필터
  
  // 기간 정보
  period: string;          // TimePeriod enum value
  start_date: string;      // Date -> string in JSON
  end_date: string;        // Date -> string in JSON
  
  // 검증용 (디버깅)
  total_contribution_check?: number; // 총 기여도 합계 검증값
}

// Specific Period 기여도 분석 응답
export interface AttributionSpecificPeriodResponse {
  // 포트폴리오 전체 성과
  period_twr: number;      // 기간 TWR 수익률 (%)
  daily_returns: DailyPortfolioReturn[]; // 기간 중 일별 포트폴리오 수익률
  
  // 자산클래스별 기여도 (기간 중)
  asset_class_contributions: AssetClassContribution[]; // 기간 중 자산클래스별 기여도
  
  // 상위/하위 기여 자산 (기간 중)
  top_contributors: AssetContribution[];   // 기간 중 상위 기여 자산
  top_detractors: AssetContribution[];     // 기간 중 상위 손실 자산
  
  // 필터 정보
  asset_filter: AssetFilter; // 적용된 자산 필터
  
  // 기간 정보
  start_date: string;      // 분석 시작일 (Date -> string in JSON)
  end_date: string;        // 분석 종료일 (Date -> string in JSON)
  period_type: string;     // 기간 타입 (week/month/custom)
  
  // 검증용
  total_contribution_check?: number; // 총 기여도 합계 검증값
}

// Custom Period 기여도 분석 응답 (레거시)
export interface AttributionCustomPeriodResponse {
  // 포트폴리오 전체 성과
  period_twr: number;      // 기간 TWR 수익률 (%)
  daily_returns: DailyPortfolioReturn[]; // 기간 중 일별 포트폴리오 수익률
  
  // 자산클래스별 기여도
  asset_class_contributions: AssetClassContribution[]; // 자산클래스별 기여도
  
  // 상위/하위 기여 자산
  top_contributors: AssetContribution[];   // 상위 기여 자산 (top 5)
  top_detractors: AssetContribution[];     // 상위 손실 자산 (top 5)
  
  // 기간 정보
  start_date: string;      // 분석 시작일 (Date -> string in JSON)
  end_date: string;        // 분석 종료일 (Date -> string in JSON)
  period_type: string;     // 기간 타입 (week/month)
  
  // 검증용
  total_contribution_check?: number; // 총 기여도 합계 검증값
}

// ================================
// LEGACY ATTRIBUTION TYPES (REMOVED)
// ================================
// Legacy attribution types have been removed to use only TWR-based attribution
// Use AttributionAllTimeResponse, AttributionSpecificPeriodResponse instead

// ================================
// POSITION TYPES
// ================================

// 일별 포트폴리오 포지션 기본 타입
export interface PortfolioPositionDaily {
  portfolio_id: number;
  as_of_date: string; // JSON에서는 string으로 직렬화됨
  asset_id: number;
  quantity: number; // Decimal -> number in JSON
  avg_price: number; // Decimal -> number in JSON
  market_value: number; // Decimal -> number in JSON
}

// 자산 정보가 포함된 일별 포지션 상세 타입
export interface PortfolioPositionDailyDetail extends PortfolioPositionDaily {
  asset_name: string;
  asset_symbol: string;
  asset_class: string;
  current_price?: number; // Optional Decimal -> optional number
  day_change?: number; // Optional Decimal -> optional number
  day_change_percent?: number; // Optional Decimal -> optional number
  weight?: number; // Optional Decimal -> optional number
}

// 날짜별 포지션 그룹
export interface PortfolioPositionsByDate {
  as_of_date: string; // date -> string in JSON
  positions: PortfolioPositionDailyDetail[];
  total_market_value: number; // Decimal -> number in JSON
  asset_count: number;
}

// 포트폴리오 포지션 히스토리 응답
export interface PortfolioPositionsHistoryResponse {
  success: boolean;
  message: string;
  data: PortfolioPositionsByDate[];
  date_range: {
    start_date: string;
    end_date: string;
  };
  total_dates: number;
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

// ================================
// RISK TYPES
// ================================

// 자산군별 배분 데이터
export interface AssetClassAllocation {
  asset_class: string;        // 자산군명
  allocation: number;         // 배분 비중 (%)
  market_value: number;       // 시장가치
  assets: AssetAllocationDetail[]; // 구성 자산 목록
}

// 자산별 배분 상세 정보
export interface AssetAllocationDetail {
  asset_id: number;
  ticker: string;
  name: string;
  quantity: number;
  market_value: number;
  weight: number;             // 포트폴리오 내 비중 (%)
  currency: string;
  region: string;             // domestic/foreign
}

// 자산 배분 응답
export interface AssetAllocationResponse {
  asset_class_allocations: AssetClassAllocation[];
  total_value: number;
  as_of_date: string;
  asset_filter: string;
}

// 포트폴리오 리스크 지표
export interface PortfolioRiskMetrics {
  volatility: number;         // 변동성 (연환산, %)
  sharpe_ratio: number;       // 샤프 비율
  max_drawdown: number;       // 최대 낙폭 (%)
  var_95: number;            // 95% VaR (%)
  var_99: number;            // 99% VaR (%)
  period_days: number;       // 분석 기간 (일)
  start_date: string;        // 분석 시작일
  end_date: string;          // 분석 종료일
}

// 자산별 리스크 기여도
export interface AssetRiskContribution {
  asset_id: number;
  ticker: string;
  name: string;
  asset_class: string;
  current_weight: number;     // 현재 비중 (%)
  volatility: number;         // 개별 변동성 (%)
  beta?: number;              // 베타 (vs 포트폴리오)
  risk_contribution: number;  // 포트폴리오 리스크 기여도 (%)
  marginal_var: number;       // 한계 VaR
}

// 리스크 분석 응답
export interface RiskAnalysisResponse {
  portfolio_metrics: PortfolioRiskMetrics;
  asset_risk_contributions: AssetRiskContribution[];
  top_risk_contributors: AssetRiskContribution[];
  asset_filter: string;
  period: string;
  confidence_level: number;
  total_risk_contribution_check?: number;
}

// ================================
// ASSET ALLOCATION TYPES
// ================================

// 자산군별 배분 (기존 AssetAllocationDetail과 호환)
export interface AssetClassAllocation {
  asset_class: string;
  total_value: number;
  total_weight: number;
  asset_count: number;
  assets: AssetAllocationDetail[];
}

// 자산 배분 응답
export interface AssetAllocationResponse {
  total_portfolio_value: number;
  as_of_date: string;
  allocations: AssetClassAllocation[];
  asset_filter: string;
}

// 자산군 상세 - 개별 자산 정보
export interface AssetClassDetailItem {
  asset_id: number;
  ticker: string;
  name: string;
  asset_class: string;
  
  // 포지션 정보
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  weight: number;  // 포트폴리오 내 비중 (%)
  
  // 수익률 정보
  day_change?: number;
  day_change_percent?: number;
  unrealized_pnl?: number;
  total_return_percent?: number;
  
  // 메타데이터
  region?: string;
  currency?: string;
}

// 자산군별 상세 정보 응답
export interface AssetClassDetailsResponse {
  asset_class: string;
  total_value: number;
  total_weight: number;
  asset_count: number;
  assets: AssetClassDetailItem[];
  as_of_date: string;
  portfolio_id: number;
  
  // 통계 정보
  avg_return?: number;
  total_unrealized_pnl?: number;
  
  error?: string;
}
