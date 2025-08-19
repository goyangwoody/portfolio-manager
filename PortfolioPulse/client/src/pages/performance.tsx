import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import type { Portfolio, PerformanceData, Benchmark } from "@shared/types";
import { formatCurrency } from "@/lib/utils";

export default function Performance() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const queryClient = useQueryClient();

  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  const portfolio = currentPortfolio || portfolios?.[0];

  const { data: performanceData, isLoading: performanceLoading } = useQuery<PerformanceData[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "performance"],
    queryFn: () => {
      console.log(`📊 Fetching performance data for portfolio ${portfolio?.id}`);
      return fetch(`/api/portfolios/${portfolio?.id}/performance`).then(res => res.json());
    },
    enabled: !!portfolio?.id,
    staleTime: 0,
    gcTime: 0,
  });

  const { data: benchmarks } = useQuery<Benchmark[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "benchmarks"],
    queryFn: () => {
      console.log(`📈 Fetching benchmarks for portfolio ${portfolio?.id}`);
      return fetch(`/api/portfolios/${portfolio?.id}/benchmarks`).then(res => res.json());
    },
    enabled: !!portfolio?.id,
    staleTime: 0,
    gcTime: 0,
  });

  const handleTimePeriodChange = (period: TimePeriod, customWeek?: string, customMonth?: string) => {
    setTimePeriod(period);
    // Here you would normally filter data based on the period
    console.log("Period changed:", period, customWeek, customMonth);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
    // 포트폴리오 변경 시 관련 쿼리들 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "performance"] 
    });
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "benchmarks"] 
    });
  };

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          No portfolio data available
        </div>
      </div>
    );
  }

  // Generate daily returns data for the chart
  const dailyReturnsData = performanceData?.map((item, index) => {
    const prevValue = index > 0 ? performanceData[index - 1].portfolioValue : item.portfolioValue;
    const currentValue = item.portfolioValue;
    const dailyReturn = index > 0 ? ((currentValue - prevValue) / prevValue) * 100 : 0;
    
    return {
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      return: dailyReturn
    };
  }).slice(1) || []; // Remove first item since it has no previous value

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Combined Portfolio and Time Period Selector */}
      <TimePeriodSelector
        value={timePeriod}
        onChange={handleTimePeriodChange}
        className="mb-6"
        onPortfolioChange={handlePortfolioChange}
        currentPortfolio={portfolio}
      />

      {/* Returns Cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <Card className="text-center">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              1D
            </div>
            <div className="text-lg font-bold text-success" data-testid="text-daily-return">
              +0.3%
            </div>
          </CardContent>
        </Card>
        
        <Card className="text-center">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              1W
            </div>
            <div className="text-lg font-bold text-success" data-testid="text-weekly-return">
              +1.8%
            </div>
          </CardContent>
        </Card>
        
        <Card className="text-center">
          <CardContent className="p-4">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              1M
            </div>
            <div className="text-lg font-bold text-success" data-testid="text-monthly-return">
              +2.1%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Daily Returns Chart */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Daily Returns
          </h3>
          
          {performanceLoading ? (
            <div className="h-64 w-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="h-64 w-full" data-testid="chart-daily-returns">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dailyReturnsData}>
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
                  <Bar 
                    dataKey="return" 
                    radius={[4, 4, 0, 0]}
                  >
                    {dailyReturnsData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.return >= 0 ? "#10B981" : "#EF4444"} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Benchmark Comparison */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            vs Benchmarks
          </h3>
          <div className="space-y-3">
            {benchmarks?.map((benchmark, index) => (
              <div 
                key={benchmark.id} 
                className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                data-testid={`benchmark-${index}`}
              >
                <div>
                  <div className="font-medium text-gray-900 dark:text-dark-text">
                    {benchmark.name}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    YTD Performance
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-600 dark:text-gray-400">
                    +{benchmark.return}%
                  </div>
                  <div className="text-sm text-success">
                    +{benchmark.outperformance}%
                  </div>
                </div>
              </div>
            )) || (
              <div className="text-center text-gray-500 dark:text-gray-400">
                No benchmark data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
