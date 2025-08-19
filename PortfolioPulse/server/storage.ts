import { 
  type Portfolio, 
  type InsertPortfolio,
  type PerformanceData,
  type InsertPerformanceData,
  type AttributionData,
  type InsertAttributionData,
  type Holding,
  type InsertHolding,
  type RiskMetrics,
  type InsertRiskMetrics,
  type SectorAllocation,
  type InsertSectorAllocation,
  type Benchmark,
  type InsertBenchmark,
  type Asset,
  type InsertAsset,
  type AssetPerformanceData,
  type InsertAssetPerformanceData
} from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  // Portfolio methods
  getPortfolio(id: string): Promise<Portfolio | undefined>;
  getPortfolios(type?: string): Promise<Portfolio[]>;
  createPortfolio(portfolio: InsertPortfolio): Promise<Portfolio>;
  
  // Performance data methods
  getPerformanceData(portfolioId: string): Promise<PerformanceData[]>;
  createPerformanceData(data: InsertPerformanceData): Promise<PerformanceData>;
  
  // Attribution data methods
  getAttributionData(portfolioId: string): Promise<AttributionData[]>;
  createAttributionData(data: InsertAttributionData): Promise<AttributionData>;
  
  // Holdings methods
  getHoldings(portfolioId: string, type?: string): Promise<Holding[]>;
  createHolding(holding: InsertHolding): Promise<Holding>;
  
  // Risk metrics methods
  getRiskMetrics(portfolioId: string): Promise<RiskMetrics | undefined>;
  createRiskMetrics(metrics: InsertRiskMetrics): Promise<RiskMetrics>;
  
  // Sector allocations methods
  getSectorAllocations(portfolioId: string): Promise<SectorAllocation[]>;
  createSectorAllocation(allocation: InsertSectorAllocation): Promise<SectorAllocation>;
  
  // Benchmark methods
  getBenchmarks(portfolioId: string): Promise<Benchmark[]>;
  createBenchmark(benchmark: InsertBenchmark): Promise<Benchmark>;
  
  // Asset methods
  getAssets(portfolioId: string): Promise<Asset[]>;
  createAsset(asset: InsertAsset): Promise<Asset>;
  
  // Asset performance data methods
  getAssetPerformanceData(assetId: string): Promise<AssetPerformanceData[]>;
  createAssetPerformanceData(data: InsertAssetPerformanceData): Promise<AssetPerformanceData>;
}

export class MemStorage implements IStorage {
  private portfolios: Map<string, Portfolio>;
  private performanceData: Map<string, PerformanceData[]>;
  private attributionData: Map<string, AttributionData[]>;
  private holdings: Map<string, Holding[]>;
  private riskMetrics: Map<string, RiskMetrics>;
  private sectorAllocations: Map<string, SectorAllocation[]>;
  private benchmarks: Map<string, Benchmark[]>;
  private assets: Map<string, Asset[]>;
  private assetPerformanceData: Map<string, AssetPerformanceData[]>;

  constructor() {
    this.portfolios = new Map();
    this.performanceData = new Map();
    this.attributionData = new Map();
    this.holdings = new Map();
    this.riskMetrics = new Map();
    this.sectorAllocations = new Map();
    this.benchmarks = new Map();
    this.assets = new Map();
    this.assetPerformanceData = new Map();
    
    // Initialize with sample data
    this.initializeSampleData();
  }

  private async initializeSampleData() {
    // Create domestic portfolio
    const portfolio = await this.createPortfolio({
      name: "Alpha Growth Fund",
      type: "domestic",
      totalReturn: "12.4",
      sharpeRatio: "1.8",
      nav: "24.72",
      aum: "2400000000",
      volatility: "14.2",
      maxDrawdown: "-8.4",
      beta: "0.92"
    });

    // Create foreign portfolio
    const foreignPortfolio = await this.createPortfolio({
      name: "Global Opportunities Fund",
      type: "foreign",
      totalReturn: "8.9",
      sharpeRatio: "1.4",
      nav: "18.45",
      aum: "1800000000",
      volatility: "16.8",
      maxDrawdown: "-12.1",
      beta: "1.05"
    });

    // Performance data
    const months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", 
                   "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"];
    const portfolioValues = [100, 102.1, 98.5, 103.2, 105.8, 108.1, 106.9, 111.3, 109.7, 112.4, 115.2, 112.4];
    const benchmarkValues = [100, 101.2, 97.8, 101.5, 103.2, 105.1, 104.2, 107.8, 106.1, 108.9, 110.1, 108.9];
    const monthlyReturns = [0, 2.1, -1.5, 4.7, 2.6, 2.7, -1.2, 4.2, -1.6, 2.7, 3.5, -2.8];

    for (let i = 0; i < months.length; i++) {
      await this.createPerformanceData({
        portfolioId: portfolio.id,
        date: months[i],
        portfolioValue: portfolioValues[i].toString(),
        benchmarkValue: benchmarkValues[i].toString(),
        dailyReturn: "0.3",
        monthlyReturn: monthlyReturns[i].toString(),
        quarterlyReturn: "5.8"
      });
    }

    // Attribution data
    await this.createAttributionData({
      portfolioId: portfolio.id,
      assetClass: "US Equities",
      contribution: "4.2",
      allocation: "62.0"
    });
    await this.createAttributionData({
      portfolioId: portfolio.id,
      assetClass: "International Equities",
      contribution: "2.8",
      allocation: "23.0"
    });
    await this.createAttributionData({
      portfolioId: portfolio.id,
      assetClass: "Fixed Income",
      contribution: "1.1",
      allocation: "12.0"
    });
    await this.createAttributionData({
      portfolioId: portfolio.id,
      assetClass: "Commodities",
      contribution: "-0.8",
      allocation: "3.0"
    });

    // Holdings - top contributors
    await this.createHolding({
      portfolioId: portfolio.id,
      name: "Apple Inc",
      weight: "4.2",
      return: "18.3",
      contribution: "0.8",
      type: "contributor"
    });
    await this.createHolding({
      portfolioId: portfolio.id,
      name: "Microsoft Corp",
      weight: "3.8",
      return: "15.1",
      contribution: "0.6",
      type: "contributor"
    });
    await this.createHolding({
      portfolioId: portfolio.id,
      name: "Amazon.com Inc",
      weight: "3.1",
      return: "12.7",
      contribution: "0.4",
      type: "contributor"
    });

    // Holdings - detractors
    await this.createHolding({
      portfolioId: portfolio.id,
      name: "Tesla Inc",
      weight: "2.1",
      return: "-12.4",
      contribution: "-0.3",
      type: "detractor"
    });
    await this.createHolding({
      portfolioId: portfolio.id,
      name: "Meta Platforms",
      weight: "1.8",
      return: "-8.9",
      contribution: "-0.2",
      type: "detractor"
    });

    // Risk metrics
    await this.createRiskMetrics({
      portfolioId: portfolio.id,
      volatility: "14.2",
      var95: "-2.3",
      maxDrawdown: "-8.4",
      beta: "0.92",
      correlation: "0.87",
      sharpeRatio: "1.35"
    });

    // Sector allocations
    const sectors = [
      { name: "Technology", percentage: "28.0" },
      { name: "Healthcare", percentage: "16.0" },
      { name: "Financials", percentage: "13.0" },
      { name: "Consumer Disc.", percentage: "11.0" }
    ];

    for (const sector of sectors) {
      await this.createSectorAllocation({
        portfolioId: portfolio.id,
        sectorName: sector.name,
        percentage: sector.percentage
      });
    }

    // Benchmarks
    await this.createBenchmark({
      portfolioId: portfolio.id,
      name: "S&P 500",
      return: "8.9",
      outperformance: "3.5"
    });
    await this.createBenchmark({
      portfolioId: portfolio.id,
      name: "MSCI World",
      return: "7.2",
      outperformance: "5.2"
    });

    // Sample assets for domestic portfolio
    const appleAsset = await this.createAsset({
      portfolioId: portfolio.id,
      name: "Apple Inc",
      ticker: "AAPL",
      averagePurchasePrice: "150.25",
      currentPrice: "175.80",
      quantity: "1250.0000",
      dayChange: "1.8",
      unrealizedPL: "31937.50",
      cumulativeReturn: "17.0"
    });

    const microsoftAsset = await this.createAsset({
      portfolioId: portfolio.id,
      name: "Microsoft Corp",
      ticker: "MSFT",
      averagePurchasePrice: "320.50",
      currentPrice: "375.20",
      quantity: "800.0000",
      dayChange: "-0.5",
      unrealizedPL: "43760.00",
      cumulativeReturn: "17.1"
    });

    const amazonAsset = await this.createAsset({
      portfolioId: portfolio.id,
      name: "Amazon.com Inc",
      ticker: "AMZN",
      averagePurchasePrice: "95.75",
      currentPrice: "142.30",
      quantity: "600.0000",
      dayChange: "2.3",
      unrealizedPL: "27930.00",
      cumulativeReturn: "48.6"
    });

    // Asset performance data for charts
    const assetMonths = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"];
    const applePrices = [150.25, 155.30, 148.90, 162.40, 168.75, 175.80];
    const microsoftPrices = [320.50, 325.80, 315.20, 340.10, 365.40, 375.20];
    const amazonPrices = [95.75, 98.20, 92.40, 105.80, 128.90, 142.30];
    
    // Apple performance data
    for (let i = 0; i < assetMonths.length; i++) {
      await this.createAssetPerformanceData({
        assetId: appleAsset.id,
        date: assetMonths[i],
        price: applePrices[i].toString()
      });
    }

    // Microsoft performance data
    for (let i = 0; i < assetMonths.length; i++) {
      await this.createAssetPerformanceData({
        assetId: microsoftAsset.id,
        date: assetMonths[i],
        price: microsoftPrices[i].toString()
      });
    }

    // Amazon performance data
    for (let i = 0; i < assetMonths.length; i++) {
      await this.createAssetPerformanceData({
        assetId: amazonAsset.id,
        date: assetMonths[i],
        price: amazonPrices[i].toString()
      });
    }

    // Risk metrics for foreign portfolio
    await this.createRiskMetrics({
      portfolioId: foreignPortfolio.id,
      volatility: "16.8",
      var95: "-3.1",
      maxDrawdown: "-12.1",
      beta: "1.05",
      correlation: "0.78",
      sharpeRatio: "1.42"
    });

    // Attribution data for foreign portfolio
    await this.createAttributionData({
      portfolioId: foreignPortfolio.id,
      assetClass: "International Equities",
      contribution: "3.1",
      allocation: "45.0"
    });
    await this.createAttributionData({
      portfolioId: foreignPortfolio.id,
      assetClass: "Emerging Markets",
      contribution: "2.2",
      allocation: "28.0"
    });
    await this.createAttributionData({
      portfolioId: foreignPortfolio.id,
      assetClass: "Global Bonds",
      contribution: "1.5",
      allocation: "20.0"
    });
    await this.createAttributionData({
      portfolioId: foreignPortfolio.id,
      assetClass: "Alternatives",
      contribution: "0.9",
      allocation: "7.0"
    });
  }

  // Portfolio methods
  async getPortfolio(id: string): Promise<Portfolio | undefined> {
    return this.portfolios.get(id);
  }

  async getPortfolios(type?: string): Promise<Portfolio[]> {
    const portfolios = Array.from(this.portfolios.values());
    return type ? portfolios.filter(p => p.type === type) : portfolios;
  }

  async createPortfolio(insertPortfolio: InsertPortfolio): Promise<Portfolio> {
    const id = randomUUID();
    const portfolio: Portfolio = { 
      ...insertPortfolio, 
      id,
      lastUpdated: new Date()
    };
    this.portfolios.set(id, portfolio);
    return portfolio;
  }

  // Performance data methods
  async getPerformanceData(portfolioId: string): Promise<PerformanceData[]> {
    return this.performanceData.get(portfolioId) || [];
  }

  async createPerformanceData(data: InsertPerformanceData): Promise<PerformanceData> {
    const id = randomUUID();
    const performanceRecord: PerformanceData = { 
      ...data, 
      id,
      dailyReturn: data.dailyReturn || null,
      monthlyReturn: data.monthlyReturn || null,
      quarterlyReturn: data.quarterlyReturn || null
    };
    
    const existing = this.performanceData.get(data.portfolioId) || [];
    existing.push(performanceRecord);
    this.performanceData.set(data.portfolioId, existing);
    
    return performanceRecord;
  }

  // Attribution data methods
  async getAttributionData(portfolioId: string): Promise<AttributionData[]> {
    return this.attributionData.get(portfolioId) || [];
  }

  async createAttributionData(data: InsertAttributionData): Promise<AttributionData> {
    const id = randomUUID();
    const attribution: AttributionData = { ...data, id };
    
    const existing = this.attributionData.get(data.portfolioId) || [];
    existing.push(attribution);
    this.attributionData.set(data.portfolioId, existing);
    
    return attribution;
  }

  // Holdings methods
  async getHoldings(portfolioId: string, type?: string): Promise<Holding[]> {
    const holdings = this.holdings.get(portfolioId) || [];
    return type ? holdings.filter(h => h.type === type) : holdings;
  }

  async createHolding(holding: InsertHolding): Promise<Holding> {
    const id = randomUUID();
    const holdingRecord: Holding = { ...holding, id };
    
    const existing = this.holdings.get(holding.portfolioId) || [];
    existing.push(holdingRecord);
    this.holdings.set(holding.portfolioId, existing);
    
    return holdingRecord;
  }

  // Risk metrics methods
  async getRiskMetrics(portfolioId: string): Promise<RiskMetrics | undefined> {
    return this.riskMetrics.get(portfolioId);
  }

  async createRiskMetrics(metrics: InsertRiskMetrics): Promise<RiskMetrics> {
    const id = randomUUID();
    const riskMetric: RiskMetrics = { ...metrics, id };
    this.riskMetrics.set(metrics.portfolioId, riskMetric);
    return riskMetric;
  }

  // Sector allocations methods
  async getSectorAllocations(portfolioId: string): Promise<SectorAllocation[]> {
    return this.sectorAllocations.get(portfolioId) || [];
  }

  async createSectorAllocation(allocation: InsertSectorAllocation): Promise<SectorAllocation> {
    const id = randomUUID();
    const sectorAllocation: SectorAllocation = { ...allocation, id };
    
    const existing = this.sectorAllocations.get(allocation.portfolioId) || [];
    existing.push(sectorAllocation);
    this.sectorAllocations.set(allocation.portfolioId, existing);
    
    return sectorAllocation;
  }

  // Benchmark methods
  async getBenchmarks(portfolioId: string): Promise<Benchmark[]> {
    return this.benchmarks.get(portfolioId) || [];
  }

  async createBenchmark(benchmark: InsertBenchmark): Promise<Benchmark> {
    const id = randomUUID();
    const benchmarkRecord: Benchmark = { ...benchmark, id };
    
    const existing = this.benchmarks.get(benchmark.portfolioId) || [];
    existing.push(benchmarkRecord);
    this.benchmarks.set(benchmark.portfolioId, existing);
    
    return benchmarkRecord;
  }

  // Asset methods
  async getAssets(portfolioId: string): Promise<Asset[]> {
    return this.assets.get(portfolioId) || [];
  }

  async createAsset(asset: InsertAsset): Promise<Asset> {
    const id = randomUUID();
    const assetRecord: Asset = { ...asset, id };
    
    const existing = this.assets.get(asset.portfolioId) || [];
    existing.push(assetRecord);
    this.assets.set(asset.portfolioId, existing);
    
    return assetRecord;
  }

  // Asset performance data methods
  async getAssetPerformanceData(assetId: string): Promise<AssetPerformanceData[]> {
    return this.assetPerformanceData.get(assetId) || [];
  }

  async createAssetPerformanceData(data: InsertAssetPerformanceData): Promise<AssetPerformanceData> {
    const id = randomUUID();
    const performanceRecord: AssetPerformanceData = { ...data, id };
    
    const existing = this.assetPerformanceData.get(data.assetId) || [];
    existing.push(performanceRecord);
    this.assetPerformanceData.set(data.assetId, existing);
    
    return performanceRecord;
  }
}

export const storage = new MemStorage();
