import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // Get all portfolios
  app.get("/api/portfolios", async (req, res) => {
    try {
      const type = req.query.type as string | undefined;
      const portfolios = await storage.getPortfolios(type);
      res.json(portfolios);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch portfolios" });
    }
  });

  // Get portfolio by ID
  app.get("/api/portfolios/:id", async (req, res) => {
    try {
      const portfolio = await storage.getPortfolio(req.params.id);
      if (!portfolio) {
        return res.status(404).json({ message: "Portfolio not found" });
      }
      res.json(portfolio);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch portfolio" });
    }
  });

  // Get performance data
  app.get("/api/portfolios/:id/performance", async (req, res) => {
    try {
      const performanceData = await storage.getPerformanceData(req.params.id);
      res.json(performanceData);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch performance data" });
    }
  });

  // Get attribution data
  app.get("/api/portfolios/:id/attribution", async (req, res) => {
    try {
      const attributionData = await storage.getAttributionData(req.params.id);
      res.json(attributionData);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch attribution data" });
    }
  });

  // Get holdings
  app.get("/api/portfolios/:id/holdings", async (req, res) => {
    try {
      const type = req.query.type as string | undefined;
      const holdings = await storage.getHoldings(req.params.id, type);
      res.json(holdings);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch holdings" });
    }
  });

  // Get risk metrics
  app.get("/api/portfolios/:id/risk", async (req, res) => {
    try {
      const riskMetrics = await storage.getRiskMetrics(req.params.id);
      if (!riskMetrics) {
        return res.status(404).json({ message: "Risk metrics not found" });
      }
      res.json(riskMetrics);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch risk metrics" });
    }
  });

  // Get sector allocations
  app.get("/api/portfolios/:id/sectors", async (req, res) => {
    try {
      const sectorAllocations = await storage.getSectorAllocations(req.params.id);
      res.json(sectorAllocations);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch sector allocations" });
    }
  });

  // Get benchmarks
  app.get("/api/portfolios/:id/benchmarks", async (req, res) => {
    try {
      const benchmarks = await storage.getBenchmarks(req.params.id);
      res.json(benchmarks);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch benchmarks" });
    }
  });

  // Get assets
  app.get("/api/portfolios/:id/assets", async (req, res) => {
    try {
      const assets = await storage.getAssets(req.params.id);
      res.json(assets);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch assets" });
    }
  });

  // Get asset performance data
  app.get("/api/assets/:id/performance", async (req, res) => {
    try {
      const performanceData = await storage.getAssetPerformanceData(req.params.id);
      res.json(performanceData);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch asset performance data" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
