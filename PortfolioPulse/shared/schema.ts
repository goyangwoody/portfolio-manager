import { sql } from "drizzle-orm";
import { pgTable, text, varchar, decimal, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Portfolio table
export const portfolios = pgTable("portfolios", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  type: text("type").notNull(), // "domestic" or "foreign"
  totalReturn: decimal("total_return", { precision: 10, scale: 4 }).notNull(),
  sharpeRatio: decimal("sharpe_ratio", { precision: 6, scale: 3 }).notNull(),
  nav: decimal("nav", { precision: 10, scale: 2 }).notNull(),
  aum: decimal("aum", { precision: 15, scale: 2 }).notNull(),
  volatility: decimal("volatility", { precision: 6, scale: 3 }).notNull(),
  maxDrawdown: decimal("max_drawdown", { precision: 6, scale: 3 }).notNull(),
  beta: decimal("beta", { precision: 6, scale: 3 }).notNull(),
  lastUpdated: timestamp("last_updated").defaultNow(),
});

// Performance data table
export const performanceData = pgTable("performance_data", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  date: text("date").notNull(), // ISO format
  portfolioValue: decimal("portfolio_value", { precision: 12, scale: 2 }).notNull(),
  benchmarkValue: decimal("benchmark_value", { precision: 12, scale: 2 }).notNull(),
  dailyReturn: decimal("daily_return", { precision: 8, scale: 4 }),
  monthlyReturn: decimal("monthly_return", { precision: 8, scale: 4 }),
  quarterlyReturn: decimal("quarterly_return", { precision: 8, scale: 4 }),
});

// Attribution data table
export const attributionData = pgTable("attribution_data", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  assetClass: text("asset_class").notNull(),
  contribution: decimal("contribution", { precision: 8, scale: 4 }).notNull(),
  allocation: decimal("allocation", { precision: 6, scale: 3 }).notNull(),
});

// Holdings data table
export const holdings = pgTable("holdings", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  name: text("name").notNull(),
  weight: decimal("weight", { precision: 6, scale: 3 }).notNull(),
  return: decimal("return", { precision: 8, scale: 4 }).notNull(),
  contribution: decimal("contribution", { precision: 8, scale: 4 }).notNull(),
  type: text("type").notNull(), // "contributor" or "detractor"
});

// Risk metrics table
export const riskMetrics = pgTable("risk_metrics", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  volatility: decimal("volatility", { precision: 6, scale: 3 }).notNull(),
  var95: decimal("var_95", { precision: 6, scale: 3 }).notNull(),
  maxDrawdown: decimal("max_drawdown", { precision: 6, scale: 3 }).notNull(),
  beta: decimal("beta", { precision: 6, scale: 3 }).notNull(),
  correlation: decimal("correlation", { precision: 6, scale: 3 }).notNull(),
  sharpeRatio: decimal("sharpe_ratio", { precision: 6, scale: 3 }).notNull(),
});

// Sector allocation table
export const sectorAllocations = pgTable("sector_allocations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  sectorName: text("sector_name").notNull(),
  percentage: decimal("percentage", { precision: 6, scale: 3 }).notNull(),
});

// Benchmark data table
export const benchmarks = pgTable("benchmarks", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  name: text("name").notNull(),
  return: decimal("return", { precision: 8, scale: 4 }).notNull(),
  outperformance: decimal("outperformance", { precision: 8, scale: 4 }).notNull(),
});

// Assets table
export const assets = pgTable("assets", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  portfolioId: varchar("portfolio_id").notNull().references(() => portfolios.id),
  name: text("name").notNull(),
  ticker: text("ticker").notNull(),
  averagePurchasePrice: decimal("average_purchase_price", { precision: 10, scale: 2 }).notNull(),
  currentPrice: decimal("current_price", { precision: 10, scale: 2 }).notNull(),
  quantity: decimal("quantity", { precision: 12, scale: 4 }).notNull(),
  dayChange: decimal("day_change", { precision: 6, scale: 3 }).notNull(),
  unrealizedPL: decimal("unrealized_pl", { precision: 12, scale: 2 }).notNull(),
  cumulativeReturn: decimal("cumulative_return", { precision: 8, scale: 4 }).notNull(),
});

// Asset performance data for charts
export const assetPerformanceData = pgTable("asset_performance_data", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  assetId: varchar("asset_id").notNull().references(() => assets.id),
  date: text("date").notNull(), // ISO format
  price: decimal("price", { precision: 10, scale: 2 }).notNull(),
});

// Insert schemas
export const insertPortfolioSchema = createInsertSchema(portfolios).omit({
  id: true,
  lastUpdated: true,
});

export const insertPerformanceDataSchema = createInsertSchema(performanceData).omit({
  id: true,
});

export const insertAttributionDataSchema = createInsertSchema(attributionData).omit({
  id: true,
});

export const insertHoldingSchema = createInsertSchema(holdings).omit({
  id: true,
});

export const insertRiskMetricsSchema = createInsertSchema(riskMetrics).omit({
  id: true,
});

export const insertSectorAllocationSchema = createInsertSchema(sectorAllocations).omit({
  id: true,
});

export const insertBenchmarkSchema = createInsertSchema(benchmarks).omit({
  id: true,
});

export const insertAssetSchema = createInsertSchema(assets).omit({
  id: true,
});

export const insertAssetPerformanceDataSchema = createInsertSchema(assetPerformanceData).omit({
  id: true,
});

// Types
export type Portfolio = typeof portfolios.$inferSelect;
export type InsertPortfolio = z.infer<typeof insertPortfolioSchema>;
export type PerformanceData = typeof performanceData.$inferSelect;
export type InsertPerformanceData = z.infer<typeof insertPerformanceDataSchema>;
export type AttributionData = typeof attributionData.$inferSelect;
export type InsertAttributionData = z.infer<typeof insertAttributionDataSchema>;
export type Holding = typeof holdings.$inferSelect;
export type InsertHolding = z.infer<typeof insertHoldingSchema>;
export type RiskMetrics = typeof riskMetrics.$inferSelect;
export type InsertRiskMetrics = z.infer<typeof insertRiskMetricsSchema>;
export type SectorAllocation = typeof sectorAllocations.$inferSelect;
export type InsertSectorAllocation = z.infer<typeof insertSectorAllocationSchema>;
export type Benchmark = typeof benchmarks.$inferSelect;
export type InsertBenchmark = z.infer<typeof insertBenchmarkSchema>;
export type Asset = typeof assets.$inferSelect;
export type InsertAsset = z.infer<typeof insertAssetSchema>;
export type AssetPerformanceData = typeof assetPerformanceData.$inferSelect;
export type InsertAssetPerformanceData = z.infer<typeof insertAssetPerformanceDataSchema>;
