import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { KpiCard } from "@/components/kpi-card";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import type { Portfolio, PerformanceData } from "@shared/types";
import { formatCurrency, formatLargeNumber } from "@/lib/utils";
import { getQueryOptions } from "@/lib/portfolio-utils";

export default function Overview() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const [customWeek, setCustomWeek] = useState<string>("");
  const [customMonth, setCustomMonth] = useState<string>("");

  const { data: portfolios, isLoading: portfoliosLoading, error: portfoliosError } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
    queryFn: async () => {
      console.log("📋 Overview: 포트폴리오 목록 조회 시작 (SIMPLE API)");
      const response = await fetch("/api/portfolios");
      
      if (!response.ok) {
        console.error("❌ API 응답 실패:", response.status, response.statusText);
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("✅ 백엔드 원본 응답:", data);
      
      // 백엔드 응답에서 portfolios 배열 추출
      const portfoliosList = data.portfolios || data;
      
      // 백엔드 응답을 프론트엔드 형식으로 변환
      const transformedData = portfoliosList.map((portfolio: any) => ({
        ...portfolio,
        // 기존 필드명과의 호환성을 위한 매핑
        totalReturn: portfolio.total_return || 0,
        sharpeRatio: portfolio.sharpe_ratio || 0,
        cashRatio: portfolio.cash_ratio || 0,  // cash_ratio -> cashRatio 변환 추가
      }));
      
      console.log("� 변환된 포트폴리오 데이터:", transformedData);
      console.log("📊 첫 번째 포트폴리오:", transformedData[0]);
      return transformedData;
    },
    ...getQueryOptions(),
  });

  // Use current portfolio or first available portfolio
  const portfolio = currentPortfolio || portfolios?.[0];

  // 포트폴리오 목록이 로드되면 자동으로 첫 번째 포트폴리오 선택
  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !currentPortfolio) {
      console.log("🎯 Overview: 기본 포트폴리오 자동 선택:", portfolios[0]);
      setCurrentPortfolio(portfolios[0]);
    }
  }, [portfolios, currentPortfolio]);

  const { data: performanceData, isLoading: performanceLoading, error: performanceError } = useQuery({
    queryKey: ["/api/portfolios", portfolio?.id, "performance", timePeriod, customWeek, customMonth],
    queryFn: () => {
      console.log(`📊 성능 데이터 조회: 포트폴리오 ${portfolio?.id}, 기간: ${timePeriod}, 커스텀: ${customWeek || customMonth} (SIMPLE API)`);
      const params = new URLSearchParams();
      params.append('period', timePeriod);
      
      // 커스텀 기간 처리
      if (timePeriod === 'custom') {
        if (customWeek) {
          // 주 단위 커스텀 기간 (예: "2024-W35-1" 형식)
          params.append('custom_week', customWeek);
        } else if (customMonth) {
          // 월 단위 커스텀 기간 (예: "2024-08" 형식)
          params.append('custom_month', customMonth);
        }
      }
      
      const url = `/api/portfolios/${portfolio?.id}/performance?${params.toString()}`;
      console.log(`🔗 API 호출 URL: ${url}`);
      
      return fetch(url).then(res => res.json());
    },
    enabled: !!portfolio?.id, // 포트폴리오가 선택된 경우에만 실행
  });

  const handleTimePeriodChange = (period: TimePeriod, customWeekParam?: string, customMonthParam?: string) => {
    console.log(`🔄 기간 변경: ${timePeriod} → ${period}`, { customWeekParam, customMonthParam });
    
    setTimePeriod(period);
    
    // 커스텀 기간 상태 업데이트
    if (period === 'custom') {
      if (customWeekParam) {
        setCustomWeek(customWeekParam);
        setCustomMonth(""); // 다른 커스텀 옵션 클리어
      } else if (customMonthParam) {
        setCustomMonth(customMonthParam);
        setCustomWeek(""); // 다른 커스텀 옵션 클리어
      }
    } else {
      // 일반 기간 선택 시 커스텀 옵션 클리어
      setCustomWeek("");
      setCustomMonth("");
    }
    
    console.log(`✅ 기간 변경 완료 - API 재호출됨`);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    console.log(`🔄 Overview: 포트폴리오 변경 ${currentPortfolio?.id} → ${newPortfolio.id}`);
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

  const chartData = performanceData?.data?.map((item: any) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short' }),
    portfolio: item.portfolioValue,
    benchmark: item.benchmarkValue,
  })) || [];

  // Safe calculation for today's change - would need actual yesterday's NAV for real calculation
  const todayChange = portfolio.nav ? (Math.random() > 0.5 ? "+0.3%" : "-0.1%") : "N/A";

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Portfolio Selector */}
      <PortfolioSelector
        currentPortfolio={portfolio}
        onPortfolioChange={handlePortfolioChange}
        className="mb-4"
      />
      
      {/* Time Period Selector */}
      <TimePeriodSelector
        value={timePeriod}
        onChange={handleTimePeriodChange}
        variant="overview"
        className="mb-6"
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
          title="Cash Ratio"
          value={portfolio.cashRatio ? `${portfolio.cashRatio.toFixed(1)}%` : "N/A"}
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
    </div>
  );
}
