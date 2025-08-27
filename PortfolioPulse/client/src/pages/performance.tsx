import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import type { 
  Portfolio, 
  PerformanceAllTimeResponse, 
  PerformanceCustomPeriodResponse,
  DailyReturnPoint, 
  BenchmarkReturn 
} from "@shared/types";
import { formatCurrency } from "@/lib/utils";

export default function Performance() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const [customWeek, setCustomWeek] = useState<string>("");
  const [customMonth, setCustomMonth] = useState<string>("");

  // 차트 기간 상태: all(전체), 1m(1달), 1w(1주)
  const [chartPeriod, setChartPeriod] = useState<"all" | "1m" | "1w">("all");
  const queryClient = useQueryClient();

  const { data: portfolios, isLoading: portfoliosLoading, error: portfoliosError } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "performance-basic"],
    queryFn: async () => {
      console.log("🔍 Performance 페이지: 포트폴리오 목록 조회");
      const response = await fetch("/api/portfolios?include_kpi=false");
      
      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("✅ Performance 페이지: 포트폴리오 데이터 수신:", data);
      
      // 백엔드 응답에서 portfolios 배열 추출
      const portfoliosList = data.portfolios || data;
      
      return portfoliosList;
    },
  });

  console.log("🔍 Performance 페이지 디버깅:", {
    portfolios,
    portfoliosLoading,
    portfoliosError,
    currentPortfolio,
  });

  const portfolio = currentPortfolio || portfolios?.[0];

  console.log("📋 선택된 포트폴리오:", portfolio);

  const { data: performanceData, isLoading: performanceLoading, error: performanceError } = useQuery<PerformanceAllTimeResponse | PerformanceCustomPeriodResponse>({
    queryKey: ["/api/portfolios", portfolio?.id, "performance", timePeriod, customWeek, customMonth, chartPeriod],
    queryFn: () => {
      console.log(`📊 성능 데이터 조회: 포트폴리오 ${portfolio?.id}, 기간: ${timePeriod}, 커스텀: ${customWeek || customMonth}, 차트기간: ${chartPeriod}`);
      const params = new URLSearchParams();
      params.append('period', timePeriod);
      
      // All Time일 때 차트 기간 추가
      if (timePeriod === 'all') {
        params.append('chart_period', chartPeriod);
      }
      
      // 커스텀 기간 처리
      if (timePeriod === 'custom') {
        if (customWeek) {
          params.append('custom_week', customWeek);
        } else if (customMonth) {
          params.append('custom_month', customMonth);
        }
      }
      
      const url = `/api/portfolios/${portfolio?.id}/performance?${params.toString()}`;
      console.log(`🔗 Performance API 호출 URL: ${url}`);
      
      return fetch(url).then(res => res.json());
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

  console.log("🔍 Performance 페이지 디버깅:", {
    portfolios: portfolios?.length || 0,
    currentPortfolio: currentPortfolio?.id,
    portfolio: portfolio?.id,
    timePeriod,
    performanceLoading,
    performanceError,
    performanceData,
    benchmarks: benchmarks.length,
    dataType: isAllTimeData(performanceData) ? 'AllTime' : isCustomPeriodData(performanceData) ? 'CustomPeriod' : 'Unknown'
  });

  const handleTimePeriodChange = (period: TimePeriod, customWeekParam?: string, customMonthParam?: string) => {
    console.log(`🔄 Performance 기간 변경: ${timePeriod} → ${period}`, { customWeekParam, customMonthParam });
    
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
    
    console.log(`✅ Performance 기간 변경 완료 - API 재호출됨`);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
    // 포트폴리오 변경 시 관련 쿼리들 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "performance"] 
    });
  };

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <p>No portfolio data available</p>
          {portfoliosLoading && <p className="mt-2">Loading portfolios...</p>}
          {portfoliosError && <p className="mt-2 text-red-500">Error loading portfolios: {String(portfoliosError)}</p>}
          {portfolios && <p className="mt-2">Portfolios loaded: {portfolios.length} items</p>}
        </div>
      </div>
    );
  }

  // Calculate returns based on performance data
  const calculateReturns = () => {
    if (!performanceData) {
      return { daily: null, weekly: null, monthly: null, total: null };
    }

    if (isAllTimeData(performanceData)) {
      // All Time 데이터 처리
      const recentReturns = performanceData.recent_returns;
      
      return {
        daily: recentReturns.daily_return,
        weekly: recentReturns.weekly_return,
        monthly: recentReturns.monthly_return,
        total: recentReturns.monthly_return // For all time, use monthly as total
      };
    } else if (isCustomPeriodData(performanceData)) {
      // Custom Period 데이터 처리
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
      // All Time: 백엔드에서 chart_period에 따라 이미 필터링된 데이터 사용
      return performanceData.daily_returns?.map((item: DailyReturnPoint) => ({
        date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        return: item.daily_return
      })) || [];
    } else if (isCustomPeriodData(performanceData)) {
      // Custom Period: 전체 기간 데이터 사용
      return performanceData.daily_returns?.map((item: DailyReturnPoint) => ({
        date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        return: item.daily_return
      })) || [];
    }
    return [];
  })();

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

      {/* Sharpe Ratio Card - All Time일 때만 표시 */}
      {isAllTimeData(performanceData) && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                  Sharpe Ratio
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Risk-adjusted returns (12M)
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-primary" data-testid="text-sharpe-ratio">
                  {portfolio.sharpeRatio ? portfolio.sharpeRatio.toFixed(2) : "N/A"}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {portfolio.sharpeRatio && portfolio.sharpeRatio > 1 ? "Excellent" : 
                   portfolio.sharpeRatio && portfolio.sharpeRatio > 0.5 ? "Good" : "Below Average"}
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

      {/* Benchmark Comparison */}
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
                    <div className={`text-sm ${benchmark.outperformance >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {benchmark.outperformance >= 0 ? '+' : ''}{benchmark.outperformance.toFixed(1)}%
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
  );
}
