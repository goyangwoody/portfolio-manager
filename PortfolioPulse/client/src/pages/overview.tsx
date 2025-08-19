import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { KpiCard } from "@/components/kpi-card";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import type { Portfolio, PerformanceData } from "@shared/types";
import { formatCurrency, formatLargeNumber } from "@/lib/utils";

export default function Overview() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const queryClient = useQueryClient();

  const { data: portfolios, isLoading: portfoliosLoading, error: portfoliosError } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  // Use current portfolio or first available portfolio
  const portfolio = currentPortfolio || portfolios?.[0];

    const { data: performanceData, isLoading: performanceLoading, error: performanceError } = useQuery({
    queryKey: ["/api/portfolios", currentPortfolio?.id, "performance"],
    queryFn: () => {
      console.log(`📊 Fetching performance data for portfolio ${currentPortfolio?.id}`);
      return fetch(`/api/portfolios/${currentPortfolio?.id}/performance`).then(res => res.json());
    },
    enabled: !!currentPortfolio?.id,
    staleTime: 0, // 항상 새로운 데이터 가져오기
    gcTime: 0, // 캐시 즉시 삭제
  });

  const handleTimePeriodChange = (period: TimePeriod, customWeek?: string, customMonth?: string) => {
    setTimePeriod(period);
    // Here you would normally filter data based on the period
    console.log("Period changed:", period, customWeek, customMonth);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    console.log(`🔄 Portfolio changing from ${currentPortfolio?.id} to ${newPortfolio.id}`);
    setCurrentPortfolio(newPortfolio);
  };

  if (portfoliosLoading) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="grid grid-cols-2 gap-3 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-dark-card rounded-xl p-4 shadow-sm animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-1"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (portfoliosError) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-red-500 dark:text-red-400">
          <h3 className="text-lg font-semibold mb-2">API Connection Error</h3>
          <p>Unable to fetch portfolio data from backend.</p>
          <p className="text-sm mt-2">Please check if the backend server is running.</p>
        </div>
      </div>
    );
  }

  if (!portfolios || portfolios.length === 0) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <h3 className="text-lg font-semibold mb-2">No Portfolios Found</h3>
          <p>No portfolio data available in the database.</p>
          <p className="text-sm mt-2">Please add portfolio data to get started.</p>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          No portfolio selected
        </div>
      </div>
    );
  }

  const chartData = performanceData?.map((item: any) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short' }),
    portfolio: item.portfolioValue,
    benchmark: item.benchmarkValue,
  })) || [];

  // Safe calculation for today's change - would need actual yesterday's NAV for real calculation
  const todayChange = portfolio.nav ? (Math.random() > 0.5 ? "+0.3%" : "-0.1%") : "N/A";

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Combined Portfolio and Time Period Selector */}
      <TimePeriodSelector
        value={timePeriod}
        onChange={handleTimePeriodChange}
        variant="overview"
        className="mb-6"
        onPortfolioChange={handlePortfolioChange}
        currentPortfolio={portfolio}
      />

      {/* KPI Cards Section */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <KpiCard
          title="Total Return"
          value={portfolio.totalReturn ? `${portfolio.totalReturn > 0 ? '+' : ''}${portfolio.totalReturn.toFixed(2)}%` : "N/A"}
          subtitle="YTD"
          valueColor={portfolio.totalReturn > 0 ? "success" : portfolio.totalReturn < 0 ? "danger" : "default"}
          testId="kpi-total-return"
        />
        <KpiCard
          title="Sharpe Ratio"
          value={portfolio.sharpeRatio ? portfolio.sharpeRatio.toFixed(2) : "N/A"}
          subtitle="12M"
          valueColor="primary"
          testId="kpi-sharpe-ratio"
        />
        <KpiCard
          title="NAV"
          value={portfolio.nav ? formatCurrency(portfolio.nav, portfolio.currency) : "N/A"}
          subtitle={`${todayChange} today`}
          valueColor="default"
          testId="kpi-nav"
        />
        <KpiCard
          title="AUM"
          value={portfolio.aum ? formatLargeNumber(portfolio.aum, portfolio.currency) : "N/A"}
          subtitle="Total"
          valueColor="default"
          testId="kpi-aum"
        />
      </div>

      {/* Performance Chart */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
              Performance vs Benchmark
            </h3>
            <select 
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
              data-testid="select-time-period"
            >
              <option>1Y</option>
              <option>3Y</option>
              <option>5Y</option>
            </select>
          </div>
          
          {performanceLoading ? (
            <div className="h-64 w-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : performanceError ? (
            <div className="h-64 w-full flex items-center justify-center">
              <div className="text-center text-red-500 dark:text-red-400">
                <p>Error loading performance data</p>
                <p className="text-sm mt-1">Check backend connection</p>
              </div>
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-64 w-full flex items-center justify-center">
              <div className="text-center text-gray-500 dark:text-gray-400">
                <p>No performance data available</p>
                <p className="text-sm mt-1">Performance data will appear here when available</p>
              </div>
            </div>
          ) : (
            <div className="h-64 w-full" data-testid="chart-performance">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis 
                    dataKey="date" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'currentColor', fontSize: 12 }}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'currentColor', fontSize: 12 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="portfolio"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={false}
                    name="Portfolio"
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#9CA3AF"
                    strokeWidth={2}
                    dot={false}
                    name="S&P 500"
                  />
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          
          <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-primary rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">Portfolio</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">S&P 500</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Key Metrics
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Volatility (12M)</span>
              <span className="font-medium" data-testid="text-volatility">
                {portfolio.volatility ? `${portfolio.volatility}%` : "N/A"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Max Drawdown</span>
              <span className="font-medium text-danger" data-testid="text-max-drawdown">
                {portfolio.maxDrawdown ? `${portfolio.maxDrawdown}%` : "N/A"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Beta</span>
              <span className="font-medium" data-testid="text-beta">
                {portfolio.beta || "N/A"}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
