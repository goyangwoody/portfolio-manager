// Simple TypeScript types for API responses
export interface Portfolio {
  id: string;
  name: string;
  type: string;
  currency: string;  // 포트폴리오 기준 통화 (KRW, USD, etc.)
  totalReturn: number;
  sharpeRatio: number;
  nav: number;
  aum: number;
  volatility: number;
  maxDrawdown: number;
  beta: number;
  lastUpdated: string;
}

export interface PerformanceData {
  id: string;
  portfolioId: string;
  date: string;
  portfolioValue: number;
  benchmarkValue: number;
  dailyReturn?: number;
  monthlyReturn?: number;
  quarterlyReturn?: number;
}

export interface AttributionData {
  id: string;
  portfolioId: string;
  assetClass: string;
  contribution: number;
  allocation: number;
}

export interface Holding {
  id: string;
  portfolioId: string;
  name: string;
  weight: number;
  return: number;
  contribution: number;
  type: string;
}

export interface RiskMetrics {
  id: string;
  portfolioId: string;
  var95: number;
  var99: number;
  expectedShortfall: number;
  trackingError: number;
  informationRatio: number;
  sharpeRatio: number;
  volatility: number;
  maxDrawdown: number;
  beta: number;
  correlation: number;
}

export interface SectorAllocation {
  id: string;
  portfolioId: string;
  sector: string;
  allocation: number;
  contribution: number;
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

export interface Asset {
  id: string;
  portfolioId: string;
  name: string;
  ticker: string;
  quantity: number;
  avgPrice: number;
  averagePurchasePrice: number;  // 별칭
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPL: number;  // 별칭
  realizedPnL: number;
  totalReturn: number;
  cumulativeReturn: number;  // 별칭
  dayChange: string;  // 일일 변화율
  weight: number;
  sector: string;
}

export interface AssetPerformanceData {
  id: string;
  assetId: string;
  date: string;
  price: number;
}
