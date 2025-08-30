import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LineChart, Line, Tooltip, Legend } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import { ThemeToggle } from "@/components/theme-toggle";
import { KpiCard } from "@/components/kpi-card";
import { ChevronDown } from "lucide-react";
import type { 
  Portfolio, 
  PerformanceAllTimeResponse, 
  PerformanceCustomPeriodResponse,
  DailyReturnPoint, 
  BenchmarkReturn 
} from "@shared/types";
import { formatCurrency, formatLargeNumber } from "@/lib/utils";

// Hero Cover 컴포넌트
function HeroCover({ 
  currentPortfolio, 
  onPortfolioChange 
}: { 
  currentPortfolio?: Portfolio;
  onPortfolioChange: (portfolio: Portfolio) => void;
}) {
  const todayChange = currentPortfolio?.nav ? (Math.random() > 0.5 ? "+0.3%" : "-0.1%") : "N/A";

  // NAV 포맷팅 함수
  const formatNavValue = (nav: number, currency: string) => {
    const symbols: { [key: string]: string } = {
      'KRW': '₩', 'USD': '$', 'EUR': '€', 'JPY': '¥'
    };
    const symbol = symbols[currency] || '$';
    return nav >= 1e6 ? `${symbol}${Math.round(nav / 1e6)}M` : formatCurrency(nav, currency);
  };

  return (
    <section className="h-screen flex flex-col justify-between bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 snap-start">
      {/* Header */}
      <div className="max-w-md mx-auto w-full px-4 pt-4">
        <div className="flex items-center justify-between mb-2">
          <PortfolioSelector
            currentPortfolio={currentPortfolio}
            onPortfolioChange={onPortfolioChange}
          />
          <ThemeToggle />
        </div>
      </div>

      {/* Hero Content */}
      <div className="max-w-md mx-auto w-full px-4 flex-1 flex flex-col">
        <div>
          <div className="mb-5 space-y-3">
            {/* Main Title with gradient */}
            <div className="space-y-2">
              <div className="space-y-1">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Team
                </div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent leading-tight">
                  The Next<br />Warren Buffetts
                </h1>
              </div>
              <div className="w-14 h-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"></div>
            </div>
            
            {/* Description with highlight */}
            <div className="space-y-2">
              <p className="text-base text-gray-700 dark:text-gray-200 leading-relaxed">
                Competing in <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-md font-semibold">2025 DB GAPS</span>, we are Industrial Engineering students at <span className="font-semibold text-gray-900 dark:text-white">SNU</span> with a passion for finance.
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-300 italic border-l-4 border-blue-500 pl-4">
                We pursue quantitative rigor and uphold ethical investing.
              </p>
            </div>
            
            {/* Team members with icons */}
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-3 space-y-2">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Our Team</h3>
              <div className="space-y-1.5">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="font-semibold text-gray-900 dark:text-white">Sungahn Kwon</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">– Global Risk Assets</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="font-semibold text-gray-900 dark:text-white">Seungjae Lee</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">– Domestic Risk Assets</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="font-semibold text-gray-900 dark:text-white">Yesung Lee</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">– Domestic Safe Assets</span>
                </div>
              </div>
            </div>
            
            {/* Catchphrase with special styling */}
            <div className="relative">
              <div className="absolute -left-2 top-0 w-1 h-full bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
              <p className="text-base font-medium text-gray-800 dark:text-gray-100 pl-6">
                Turning <span className="bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent font-bold">analysis</span> into <span className="bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent font-bold">alpha</span>, responsibly.
              </p>
            </div>
          </div>
          
          {/* Scroll Indicator - moved between text and KPI cards */}
          <div className="text-center">
            <div className="inline-flex flex-col items-center text-gray-500 dark:text-gray-400 animate-bounce">
              <span className="text-sm">Scroll for details</span>
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-3 gap-2">
          <KpiCard
            title="Total Return"
            value={currentPortfolio?.totalReturn ? `${currentPortfolio.totalReturn > 0 ? '+' : ''}${currentPortfolio.totalReturn.toFixed(2)}%` : "N/A"}
            valueColor={currentPortfolio?.totalReturn && currentPortfolio.totalReturn > 0 ? "success" : currentPortfolio?.totalReturn && currentPortfolio.totalReturn < 0 ? "danger" : "default"}
            testId="hero-total-return"
          />
          <KpiCard
            title="NAV"
            value={currentPortfolio?.nav ? formatNavValue(currentPortfolio.nav, currentPortfolio.currency) : "N/A"}
            valueColor="default"
            testId="hero-nav"
          />
          <KpiCard
            title="Cash Ratio"
            value={currentPortfolio?.cashRatio ? `${currentPortfolio.cashRatio.toFixed(1)}%` : "N/A"}
            valueColor="primary"
            testId="hero-cash-ratio"
          />
        </div>
      </div>
    </section>
  );
}

// Performance Content 컴포넌트  
function PerformanceContent({ 
  currentPortfolio, 
  onPortfolioChange 
}: { 
  currentPortfolio?: Portfolio;
  onPortfolioChange: (portfolio: Portfolio) => void;
}) {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const [customWeek, setCustomWeek] = useState<string>("");
  const [customMonth, setCustomMonth] = useState<string>("");
  const [chartPeriod, setChartPeriod] = useState<"all" | "1m" | "1w">("all");
  const queryClient = useQueryClient();

  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "performance-basic"],
    queryFn: async () => {
      const response = await fetch("/api/portfolios?include_kpi=false");
      if (!response.ok) throw new Error(`API 호출 실패: ${response.status}`);
      const data = await response.json();
      return data.portfolios || data;
    },
  });

  const portfolio = currentPortfolio || portfolios?.[0];

  const { data: performanceData, isLoading: performanceLoading } = useQuery<PerformanceAllTimeResponse | PerformanceCustomPeriodResponse>({
    queryKey: ["/api/portfolios", portfolio?.id, "performance", timePeriod, customWeek, customMonth, chartPeriod],
    queryFn: () => {
      const params = new URLSearchParams();
      params.append('period', timePeriod);
      
      if (timePeriod === 'all') {
        params.append('chart_period', chartPeriod);
      }
      
      if (timePeriod === 'custom') {
        if (customWeek) {
          params.append('custom_week', customWeek);
        } else if (customMonth) {
          params.append('custom_month', customMonth);
        }
      }
      
      const url = `/api/portfolios/${portfolio?.id}/performance?${params.toString()}`;
      return fetch(url).then(res => res.json());
    },
    enabled: !!portfolio?.id,
    staleTime: 0,
    gcTime: 0,
  });

  // 벤치마크 비교 차트 데이터
  const { data: benchmarkChartData, isLoading: benchmarkLoading } = useQuery({
    queryKey: ["/api/portfolios", portfolio?.id, "performance", "benchmark-comparison", chartPeriod],
    queryFn: async () => {
      const period = chartPeriod === 'all' ? 'all' : chartPeriod === '1m' ? '1m' : '1w';
      const response = await fetch(`/api/portfolios/${portfolio?.id}/performance/benchmark-comparison?period=${period}`);
      if (!response.ok) throw new Error('Failed to fetch benchmark data');
      return response.json();
    },
    enabled: !!portfolio?.id,
    staleTime: 0,
    gcTime: 0,
  });

  // 벤치마크 데이터는 performance 데이터에 포함됨
  const benchmarks = performanceData?.benchmark_returns || [];

  // Type guards
  const isAllTimeData = (data: any): data is PerformanceAllTimeResponse => {
    return data && 'recent_returns' in data;
  };

  const isCustomPeriodData = (data: any): data is PerformanceCustomPeriodResponse => {
    return data && 'cumulative_return' in data;
  };

  const handleTimePeriodChange = (period: TimePeriod, customWeekParam?: string, customMonthParam?: string) => {
    setTimePeriod(period);
    
    if (period === 'custom') {
      if (customWeekParam) {
        setCustomWeek(customWeekParam);
        setCustomMonth("");
      } else if (customMonthParam) {
        setCustomMonth(customMonthParam);
        setCustomWeek("");
      }
    } else {
      setCustomWeek("");
      setCustomMonth("");
    }
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    onPortfolioChange(newPortfolio);
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "performance"] 
    });
  };

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <p>No portfolio data available</p>
        </div>
      </div>
    );
  }

  // Calculate returns based on performance data
  const calculateReturns = () => {
    if (!performanceData) return { daily: null, weekly: null, monthly: null, total: null };

    if (isAllTimeData(performanceData)) {
      const recentReturns = performanceData.recent_returns;
      return {
        daily: recentReturns.daily_return,
        weekly: recentReturns.weekly_return,
        monthly: recentReturns.monthly_return,
        total: recentReturns.monthly_return
      };
    } else if (isCustomPeriodData(performanceData)) {
      return {
        daily: null,
        weekly: null,
        monthly: null,
        total: performanceData.cumulative_return
      };
    }

    return { daily: null, weekly: null, monthly: null, total: null };
  };

  const returns = calculateReturns();

  // Generate daily returns data for the chart
  const dailyReturnsData = (() => {
    if (!performanceData) return [];
    
    if (isAllTimeData(performanceData)) {
      return performanceData.daily_returns?.map((item: DailyReturnPoint) => ({
        date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        return: item.daily_return
      })) || [];
    } else if (isCustomPeriodData(performanceData)) {
      return performanceData.daily_returns?.map((item: DailyReturnPoint) => ({
        date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        return: item.daily_return
      })) || [];
    }
    
    return [];
  })();

  // Generate benchmark comparison chart data
  const benchmarkComparisonData = (() => {
    if (!benchmarkChartData || !benchmarkChartData.portfolio_data || !benchmarkChartData.benchmark_data) return [];
    
    const portfolioData = benchmarkChartData.portfolio_data;
    const benchmarkData = benchmarkChartData.benchmark_data;
    
    // 포트폴리오와 벤치마크 데이터를 날짜별로 결합
    const combinedData = portfolioData.map((portfolioPoint: any, index: number) => {
      const benchmarkPoint = benchmarkData[index];
      return {
        date: new Date(portfolioPoint.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        portfolio: portfolioPoint.value,
        benchmark: benchmarkPoint ? benchmarkPoint.value : null,
        benchmarkName: benchmarkPoint ? benchmarkPoint.name : 'Benchmark'
      };
    });
    
    return combinedData;
  })();

  return (
    <section className="min-h-screen bg-background snap-start">
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Top Header with Portfolio Selector and Theme Toggle */}
      <div className="flex items-center justify-between mb-4">
        <PortfolioSelector
          currentPortfolio={portfolio}
          onPortfolioChange={handlePortfolioChange}
        />
        <ThemeToggle />
      </div>
      
      {/* Time Period Selector */}
      <TimePeriodSelector
        value={timePeriod}
        onChange={handleTimePeriodChange}
        className="mb-6"
      />

      {/* Returns Cards - All Time일 때만 표시 */}
      {isAllTimeData(performanceData) && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Card className="text-center">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                1D
              </div>
              {performanceLoading ? (
                <div className="text-lg font-bold text-gray-400">
                  <div className="animate-pulse">---</div>
                </div>
              ) : (
                <div 
                  className={`text-lg font-bold ${
                    returns.daily === null || returns.daily === undefined ? 'text-gray-400' : 
                    returns.daily >= 0 ? 'text-success' : 'text-destructive'
                  }`} 
                  data-testid="text-daily-return"
                >
                  {returns.daily === null || returns.daily === undefined ? 'N/A' : 
                   `${returns.daily >= 0 ? '+' : ''}${returns.daily.toFixed(2)}%`}
                </div>
              )}
            </CardContent>
          </Card>
          
          <Card className="text-center">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                1W
              </div>
              {performanceLoading ? (
                <div className="text-lg font-bold text-gray-400">
                  <div className="animate-pulse">---</div>
                </div>
              ) : (
                <div 
                  className={`text-lg font-bold ${
                    returns.weekly === null || returns.weekly === undefined ? 'text-gray-400' : 
                    returns.weekly >= 0 ? 'text-success' : 'text-destructive'
                  }`} 
                  data-testid="text-weekly-return"
                >
                  {returns.weekly === null || returns.weekly === undefined ? 'N/A' : 
                   `${returns.weekly >= 0 ? '+' : ''}${returns.weekly.toFixed(2)}%`}
                </div>
              )}
            </CardContent>
          </Card>
          
          <Card className="text-center">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                1M
              </div>
              {performanceLoading ? (
                <div className="text-lg font-bold text-gray-400">
                  <div className="animate-pulse">---</div>
                </div>
              ) : (
                <div 
                  className={`text-lg font-bold ${
                    returns.monthly === null || returns.monthly === undefined ? 'text-gray-400' : 
                    returns.monthly >= 0 ? 'text-success' : 'text-destructive'
                  }`} 
                  data-testid="text-monthly-return"
                >
                  {returns.monthly === null || returns.monthly === undefined ? 'N/A' : 
                   `${returns.monthly >= 0 ? '+' : ''}${returns.monthly.toFixed(2)}%`}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Custom Period일 때 Cumulative Return Card */}
      {isCustomPeriodData(performanceData) && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                  Cumulative Return
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {performanceData.start_date} to {performanceData.end_date}
                </p>
              </div>
              <div className="text-right">
                <div 
                  className={`text-2xl font-bold ${
                    performanceData.cumulative_return >= 0 ? 'text-success' : 'text-destructive'
                  }`} 
                  data-testid="text-cumulative-return"
                >
                  {performanceData.cumulative_return >= 0 ? '+' : ''}{performanceData.cumulative_return.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {performanceData.period_type === 'week' ? 'Weekly Period' : 'Monthly Period'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cash Ratio Card - All Time일 때만 표시 */}
      {isAllTimeData(performanceData) && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                  Cash Ratio
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Cash allocation percentage
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-primary" data-testid="text-cash-ratio">
                  {portfolio.cashRatio ? `${portfolio.cashRatio.toFixed(1)}%` : "N/A"}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {portfolio.cashRatio && portfolio.cashRatio > 20 ? "High Cash" : 
                   portfolio.cashRatio && portfolio.cashRatio > 5 ? "Moderate Cash" : "Low Cash"}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}


      {/* Daily Returns Chart (All Time: 기간 선택 UI) */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
              Daily Returns
            </h3>
            {/* All Time일 때만 기간 선택 UI */}
            {isAllTimeData(performanceData) && (
              <div className="flex gap-1">
                <button
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${chartPeriod === 'all' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  onClick={() => setChartPeriod('all')}
                >All Time</button>
                <button
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${chartPeriod === '1m' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  onClick={() => setChartPeriod('1m')}
                >1 Month</button>
                <button
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${chartPeriod === '1w' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  onClick={() => setChartPeriod('1w')}
                >1 Week</button>
              </div>
            )}
          </div>
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
                    {dailyReturnsData.map((entry: any, index: number) => (
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

      {/* Benchmark Comparison Chart */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
              Portfolio vs Benchmark
            </h3>
            {/* All Time일 때만 기간 선택 UI */}
            {isAllTimeData(performanceData) && (
              <div className="flex gap-1">
                <button
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${chartPeriod === 'all' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  onClick={() => setChartPeriod('all')}
                >All Time</button>
                <button
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${chartPeriod === '1m' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  onClick={() => setChartPeriod('1m')}
                >1 Month</button>
                <button
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${chartPeriod === '1w' ? 'bg-primary text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}
                  onClick={() => setChartPeriod('1w')}
                >1 Week</button>
              </div>
            )}
          </div>
          
          {benchmarkLoading ? (
            <div className="h-64 w-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : benchmarkComparisonData.length > 0 ? (
            <div className="h-64 w-full" data-testid="chart-benchmark-comparison">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={benchmarkComparisonData}>
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
                    domain={['dataMin - 5', 'dataMax + 5']}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                    formatter={(value: any, name: string) => [
                      `${Number(value).toFixed(1)}`,
                      name === 'portfolio' ? portfolio?.name || 'Portfolio' : benchmarkComparisonData[0]?.benchmarkName || 'Benchmark'
                    ]}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="portfolio" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={false}
                    name={portfolio?.name || 'Portfolio'}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="benchmark" 
                    stroke="#EF4444" 
                    strokeWidth={2}
                    dot={false}
                    strokeDasharray="5 5"
                    name={benchmarkComparisonData[0]?.benchmarkName || 'Benchmark'}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 w-full flex items-center justify-center text-gray-500 dark:text-gray-400">
              <div className="text-center">
                <p>벤치마크 비교 데이터 준비 중</p>
                <p className="text-xs mt-1">포트폴리오 통화에 따른 벤치마크 자동 선택</p>
              </div>
            </div>
          )}
          
          {/* 벤치마크 정보 */}
          {benchmarkChartData && (
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between text-sm">
                <div className="text-gray-600 dark:text-gray-400">
                  Benchmark: {benchmarkChartData.benchmark_name} ({benchmarkChartData.benchmark_symbol})
                </div>
                <div className="text-gray-500 dark:text-gray-500">
                  Based on portfolio currency: {portfolio?.currency}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Benchmark Performance Summary */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            vs Benchmarks ({timePeriod === 'all' ? 'All Time' : 
                           timePeriod === '2w' ? '2 Weeks' :
                           timePeriod === '1m' ? '1 Month' :
                           timePeriod === '1w' ? '1 Week' :
                           'Custom Period'})
          </h3>
          <div className="space-y-3">
            {benchmarks && benchmarks.length > 0 ? (
              benchmarks.map((benchmark, index) => (
                <div 
                  key={index} 
                  className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
                  data-testid={`benchmark-${index}`}
                >
                  <div>
                    <div className="font-medium text-gray-900 dark:text-dark-text">
                      {benchmark.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {timePeriod === 'all' ? 'Total Performance' :
                       timePeriod === '1w' ? '1W Performance' :
                       timePeriod === '2w' ? '2W Performance' :
                       timePeriod === '1m' ? '1M Performance' :
                       'Period Performance'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-600 dark:text-gray-400">
                      {benchmark.return_pct >= 0 ? '+' : ''}{benchmark.return_pct.toFixed(1)}%
                    </div>
                    <div className={`text-sm ${benchmark.excess_return >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {benchmark.excess_return >= 0 ? '+' : ''}{benchmark.excess_return.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400">
                <p>벤치마크 데이터 준비 중</p>
                <p className="text-xs mt-1">KOSPI, KOSPI200, S&P500 지수 연동 예정</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      </div>
    </section>
  );
}

export default function Performance() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();

  // 포트폴리오 KPI 데이터를 위한 쿼리 (Hero Cover용)
  const { data: portfolioKpiData } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "core", "kpi"],
    queryFn: async () => {
      const response = await fetch("/api/portfolios?portfolio_type=core&include_kpi=true&include_chart=true");
      if (!response.ok) throw new Error('Failed to fetch portfolio KPI');
      const data = await response.json();
      const portfoliosList = data.portfolios || data;
      return portfoliosList.map((portfolio: any) => ({
        ...portfolio,
        totalReturn: portfolio.total_return || 0,
        sharpeRatio: portfolio.sharpe_ratio || 0,
        cashRatio: portfolio.cash_ratio || 0,
        chartData: portfolio.chart_data || [],
      }));
    },
  });

  // 포트폴리오 자동 선택
  useEffect(() => {
    if (!currentPortfolio && portfolioKpiData && portfolioKpiData.length > 0) {
      setCurrentPortfolio(portfolioKpiData[0]);
    }
  }, [portfolioKpiData, currentPortfolio]);

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
  };

  return (
    <div className="snap-y snap-mandatory overflow-y-scroll h-screen">
      <HeroCover 
        currentPortfolio={currentPortfolio} 
        onPortfolioChange={handlePortfolioChange}
      />
      <PerformanceContent 
        currentPortfolio={currentPortfolio}
        onPortfolioChange={handlePortfolioChange}
      />
    </div>
  );
}
