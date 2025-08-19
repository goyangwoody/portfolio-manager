import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { KpiCard } from "@/components/kpi-card";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import type { Portfolio, PerformanceData } from "@shared/schema";

export default function Overview() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");

  const { data: portfolios, isLoading: portfoliosLoading } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  const portfolio = currentPortfolio || portfolios?.[0]; // Get current or first portfolio

  const { data: performanceData, isLoading: performanceLoading } = useQuery<PerformanceData[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "performance"],
    enabled: !!portfolio?.id,
  });

  const handleTimePeriodChange = (period: TimePeriod, customWeek?: string, customMonth?: string) => {
    setTimePeriod(period);
    // Here you would normally filter data based on the period
    console.log("Period changed:", period, customWeek, customMonth);
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

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          No portfolio data available
        </div>
      </div>
    );
  }

  const chartData = performanceData?.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short' }),
    portfolio: parseFloat(item.portfolioValue),
    benchmark: parseFloat(item.benchmarkValue),
  })) || [];

  const todayChange = portfolio.nav && parseFloat(portfolio.nav) > 24 ? "+0.3%" : "+0.3%";

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Combined Portfolio and Time Period Selector */}
      <TimePeriodSelector
        value={timePeriod}
        onChange={handleTimePeriodChange}
        variant="overview"
        className="mb-6"
        onPortfolioChange={setCurrentPortfolio}
        currentPortfolio={portfolio}
      />

      {/* KPI Cards Section */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <KpiCard
          title="Total Return"
          value={`+${portfolio.totalReturn}%`}
          subtitle="YTD"
          valueColor="success"
          testId="kpi-total-return"
        />
        <KpiCard
          title="Sharpe Ratio"
          value={portfolio.sharpeRatio}
          subtitle="12M"
          valueColor="primary"
          testId="kpi-sharpe-ratio"
        />
        <KpiCard
          title="NAV"
          value={`$${portfolio.nav}`}
          subtitle={`${todayChange} today`}
          valueColor="default"
          testId="kpi-nav"
        />
        <KpiCard
          title="AUM"
          value={`$${(parseFloat(portfolio.aum) / 1000000000).toFixed(1)}B`}
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
                {portfolio.volatility}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Max Drawdown</span>
              <span className="font-medium text-danger" data-testid="text-max-drawdown">
                {portfolio.maxDrawdown}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Beta</span>
              <span className="font-medium" data-testid="text-beta">
                {portfolio.beta}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
