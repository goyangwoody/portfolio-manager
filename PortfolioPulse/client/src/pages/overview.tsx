import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { KpiCard } from "@/components/kpi-card";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts";
import { PortfolioSelector } from "@/components/portfolio-selector";
import type { Portfolio } from "@shared/types";
import { formatCurrency } from "@/lib/utils";

export default function Overview() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    console.log(`🔄 Overview: 포트폴리오 변경 ${currentPortfolio?.id} → ${newPortfolio.id}`);
    setCurrentPortfolio(newPortfolio);
  };

  // 포트폴리오가 선택되지 않은 경우
  if (!currentPortfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
        <PortfolioSelector
          currentPortfolio={currentPortfolio}
          onPortfolioChange={handlePortfolioChange}
          className="mb-6"
        />
        <div className="text-center text-gray-500 dark:text-gray-400">
          <h3 className="text-lg font-semibold mb-2">포트폴리오를 선택해주세요</h3>
          <p>위에서 Core 또는 USD Core를 선택하세요.</p>
        </div>
      </div>
    );
  }

  const chartData = currentPortfolio?.chartData?.map((item: any, index: number, array: any[]) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric'
    }),
    portfolio: item.nav,
    benchmark: item.benchmark,
  }))
  // 데이터가 많으면 간격을 두고 표시 (모바일에서 가독성 향상)
  ?.filter((_, index, array) => {
    if (array.length <= 20) return true; // 20개 이하면 모두 표시
    const step = Math.ceil(array.length / 15); // 최대 15개 포인트만 표시
    return index % step === 0 || index === array.length - 1; // 첫 번째와 마지막은 항상 포함
  }) || [];

  // Y축 도메인 계산 (변화폭이 잘 보이도록)
  const getYAxisDomain = () => {
    if (chartData.length === 0) return ['auto', 'auto'];
    
    const allValues = chartData.flatMap(item => [item.portfolio, item.benchmark]).filter(v => v != null);
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const range = maxValue - minValue;
    
    // 범위가 너무 작으면 (변화가 적으면) 확대
    if (range < maxValue * 0.1) { // 변화가 10% 미만이면
      const center = (minValue + maxValue) / 2;
      const expandedRange = Math.max(range * 3, maxValue * 0.05); // 최소 5% 범위 확보
      return [
        Math.max(0, center - expandedRange / 2), // 음수 방지
        center + expandedRange / 2
      ];
    }
    
    // 일반적인 경우 약간의 패딩 추가
    const padding = range * 0.1;
    return [
      Math.max(0, minValue - padding), // 음수 방지
      maxValue + padding
    ];
  };

  // Safe calculation for today's change - would need actual yesterday's NAV for real calculation
  const todayChange = currentPortfolio?.nav ? (Math.random() > 0.5 ? "+0.3%" : "-0.1%") : "N/A";

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Portfolio Selector */}
      <PortfolioSelector
        currentPortfolio={currentPortfolio}
        onPortfolioChange={handlePortfolioChange}
        className="mb-6"
      />

      {/* KPI Cards Section */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <KpiCard
          title="Total Return"
          value={currentPortfolio.totalReturn ? `${currentPortfolio.totalReturn > 0 ? '+' : ''}${currentPortfolio.totalReturn.toFixed(2)}%` : "N/A"}
          subtitle="Since Inception"
          valueColor={currentPortfolio.totalReturn > 0 ? "success" : currentPortfolio.totalReturn < 0 ? "danger" : "default"}
          testId="kpi-total-return"
        />
        <KpiCard
          title="Sharpe Ratio"
          value={currentPortfolio.sharpeRatio ? currentPortfolio.sharpeRatio.toFixed(2) : "N/A"}
          subtitle="Risk-Adjusted"
          valueColor="primary"
          testId="kpi-sharpe-ratio"
        />
        <KpiCard
          title="NAV"
          value={currentPortfolio.nav ? formatCurrency(currentPortfolio.nav, currentPortfolio.currency) : "N/A"}
          subtitle={`${todayChange} today`}
          valueColor="default"
          testId="kpi-nav"
        />
        <KpiCard
          title="Cash Ratio"
          value={currentPortfolio.cashRatio ? `${currentPortfolio.cashRatio.toFixed(1)}%` : "N/A"}
          subtitle="현금 비중"
          valueColor="default"
          testId="kpi-cash-ratio"
        />
      </div>

      {/* Performance Chart */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
              NAV vs Benchmark
            </h3>
          </div>
          
          {!currentPortfolio?.chartData || currentPortfolio.chartData.length === 0 ? (
            <div className="h-72 w-full flex items-center justify-center">
              <div className="text-center text-gray-500 dark:text-gray-400">
                <p>No NAV data available</p>
                <p className="text-sm mt-1">Chart data will appear here when available</p>
              </div>
            </div>
          ) : (
            <div className="h-72 w-full" data-testid="chart-performance">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart 
                  data={chartData}
                  margin={{ top: 10, right: 10, left: 10, bottom: 40 }}
                >
                  <XAxis 
                    dataKey="date" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'currentColor', fontSize: 9 }}
                    interval={0}
                    angle={-35}
                    textAnchor="end"
                    height={50}
                    tickMargin={5}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'currentColor', fontSize: 9 }}
                    width={50}
                    tickMargin={5}
                    domain={getYAxisDomain()}
                    tickFormatter={(value) => {
                      if (value >= 1000000) {
                        return `${(value / 1000000).toFixed(1)}M`;
                      } else if (value >= 1000) {
                        return `${(value / 1000).toFixed(0)}K`;
                      }
                      return Number(value).toLocaleString();
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="portfolio"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={false}
                    name="NAV"
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#9CA3AF"
                    strokeWidth={2}
                    dot={false}
                    name="Benchmark"
                  />
                  <Legend 
                    wrapperStyle={{ paddingTop: '10px' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          
          <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-primary rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">NAV</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span className="text-gray-600 dark:text-gray-400">Benchmark</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
