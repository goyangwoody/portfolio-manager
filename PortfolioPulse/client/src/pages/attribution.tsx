import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine } from "recharts";
import { ChevronLeft, TrendingUp, TrendingDown, PieChart } from "lucide-react";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import { ThemeToggle } from "@/components/theme-toggle";
import type { 
  Portfolio, 
  PortfoliosResponse,
  PortfolioListResponse,
  AttributionAllTimeResponse,
  AttributionSpecificPeriodResponse,
  AssetClassContribution,
  AssetContribution,
  AssetDetailResponse
} from "@shared/types";

// generateColorPalette: create a stable color mapping for asset classes
const generateColorPalette = (assetClasses: string[]): Record<string, string> => {
  const colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
    '#bcbd22', '#17becf'
  ];
  const colorMap: Record<string, string> = {};
  assetClasses.forEach((assetClass, index) => {
    colorMap[assetClass] = colors[index % colors.length];
  });
  return colorMap;
};

export default function Attribution() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const [selectedAssetClass, setSelectedAssetClass] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  const { data: portfoliosResponse, isLoading: portfoliosLoading, error: portfoliosError } = useQuery<PortfoliosResponse>({
    queryKey: ["/api/portfolios"],
    queryFn: async () => {
      const response = await fetch('/api/portfolios?include_kpi=false');
      if (!response.ok) throw new Error('Failed to fetch portfolios');
      return response.json();
    },
  });

  const portfolios = portfoliosResponse?.portfolios || [];
  const portfolio = currentPortfolio || (portfolios[0] ? {
    ...portfolios[0],
    totalReturn: 0,
    sharpeRatio: 0
  } : undefined);

  const handleTimePeriodChange = (period: TimePeriod, customWeek?: string, customMonth?: string) => {
    setTimePeriod(period);
    console.log("Period changed:", period, customWeek, customMonth);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
    // 포트폴리오 변경 시 기여도 분석 데이터 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "attribution"] 
    });
  };

  // TWR 기반 All Time 기여도 데이터
  const { 
    data: allTimeAttributionData, 
    isLoading: allTimeLoading, 
    error: allTimeError 
  } = useQuery<AttributionAllTimeResponse>({
    queryKey: ["/api/portfolios", portfolio?.id, "attribution", "all-time"],
    queryFn: async () => {
      const response = await fetch(`/api/portfolios/${portfolio?.id}/attribution/all-time?asset_filter=all`);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Attribution API Error:', response.status, errorText);
        throw new Error(`Failed to fetch attribution data: ${response.status} - ${errorText}`);
      }
      return response.json();
    },
    enabled: !!portfolio?.id && timePeriod === "all",
  });

  // TWR 기반 Specific Period 기여도 데이터 (필요시 구현)
  const { data: specificPeriodAttributionData } = useQuery<AttributionSpecificPeriodResponse>({
    queryKey: ["/api/portfolios", portfolio?.id, "attribution", "specific-period", timePeriod],
    queryFn: async () => {
      // 실제로는 TimePeriod에 따라 start_date, end_date를 계산해야 함
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]; // 30일 전
      
      const response = await fetch(
        `/api/portfolios/${portfolio?.id}/attribution/specific-period?start_date=${startDate}&end_date=${endDate}&asset_filter=all&period_type=month`
      );
      if (!response.ok) throw new Error('Failed to fetch attribution data');
      return response.json();
    },
    enabled: !!portfolio?.id && timePeriod !== "all",
  });

  // 개별 자산 상세 정보
  const { 
    data: assetDetailData, 
    isLoading: assetDetailLoading, 
    error: assetDetailError 
  } = useQuery<AssetDetailResponse>({
    queryKey: ["/api/portfolios", portfolio?.id, "attribution", "asset-detail", selectedAssetId],
    queryFn: async () => {
      const response = await fetch(`/api/portfolios/${portfolio?.id}/attribution/asset-detail/${selectedAssetId}`);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Asset Detail API Error:', response.status, errorText);
        throw new Error(`Failed to fetch asset detail: ${response.status} - ${errorText}`);
      }
      return response.json();
    },
    enabled: !!portfolio?.id && !!selectedAssetId,
  });

  // 현재 사용할 데이터 결정
  const currentAttributionData = timePeriod === "all" ? allTimeAttributionData : specificPeriodAttributionData;

  // TWR 기반 데이터 사용 (레거시 변환 제거)
  const assetClassContributions = currentAttributionData?.asset_class_contributions || [];
  // generate color mapping for asset classes returned by the API
  const assetClassColors = generateColorPalette(assetClassContributions.map((ac: AssetClassContribution) => ac.asset_class));
  const topContributors = currentAttributionData?.top_contributors || [];
  const topDetractors = currentAttributionData?.top_detractors || []; 

  // 에러 상태 처리
  if (portfoliosError) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-red-500">
          Error loading portfolios: {portfoliosError.message}
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
        <PortfolioSelector
          currentPortfolio={portfolio}
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

  const getAssetClassColor = (index: number) => {
    const colors = ["bg-primary", "bg-success", "bg-warning", "bg-danger"];
    return colors[index % colors.length];
  };

  // Render detailed asset view (for contributors/detractors)
  if (selectedAsset && selectedAssetId) {
    if (assetDetailLoading) {
      return (
        <div className="max-w-md mx-auto px-4 py-6 pb-20">
          <div className="flex items-center mb-6">
            <Button
              variant="ghost" 
              size="sm"
              onClick={() => {
                setSelectedAsset(null);
                setSelectedAssetId(null);
              }}
              className="mr-3 p-2"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text">
              {selectedAsset}
            </h1>
          </div>
          <div className="text-center text-gray-500 dark:text-gray-400">
            Loading asset details...
          </div>
        </div>
      );
    }

    if (assetDetailError) {
      return (
        <div className="max-w-md mx-auto px-4 py-6 pb-20">
          <div className="flex items-center mb-6">
            <Button
              variant="ghost" 
              size="sm"
              onClick={() => {
                setSelectedAsset(null);
                setSelectedAssetId(null);
              }}
              className="mr-3 p-2"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text">
              {selectedAsset}
            </h1>
          </div>
          <div className="text-center text-red-500">
            Error loading asset details: {assetDetailError.message}
          </div>
        </div>
      );
    }

    if (!assetDetailData) {
      return (
        <div className="max-w-md mx-auto px-4 py-6 pb-20">
          <div className="flex items-center mb-6">
            <Button
              variant="ghost" 
              size="sm"
              onClick={() => {
                setSelectedAsset(null);
                setSelectedAssetId(null);
              }}
              className="mr-3 p-2"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text">
              {selectedAsset}
            </h1>
          </div>
          <div className="text-center text-gray-500 dark:text-gray-400">
            No asset details available
          </div>
        </div>
      );
    }
    return (
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
        {/* Header with Back Button */}
        <div className="flex items-center mb-6">
          <Button
            variant="ghost" 
            size="sm"
            onClick={() => {
              setSelectedAsset(null);
              setSelectedAssetId(null);
            }}
            className="mr-3 p-2"
            data-testid="button-back-asset"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text">
            {assetDetailData.name}
          </h1>
        </div>

        {/* Asset Overview */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Allocation
                </div>
                <div className="text-lg font-bold text-primary" data-testid="text-asset-allocation">
                  {assetDetailData.current_allocation.toFixed(1)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Period Return
                </div>
                <div className={`text-lg font-bold ${assetDetailData.nav_return >= 0 ? 'text-success' : 'text-danger'}`} data-testid="text-asset-return">
                  {assetDetailData.nav_return >= 0 ? '+' : ''}{assetDetailData.nav_return.toFixed(1)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  TWR Contribution
                </div>
                <div className={`text-lg font-bold ${assetDetailData.twr_contribution >= 0 ? 'text-success' : 'text-danger'}`} data-testid="text-asset-contribution">
                  {assetDetailData.twr_contribution >= 0 ? '+' : ''}{assetDetailData.twr_contribution.toFixed(2)}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Price Performance Chart */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center mb-4">
              <TrendingUp className="h-4 w-4 text-primary mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                Price Performance (% Change)
              </h3>
            </div>
            <div className="h-64" data-testid="chart-asset-performance">
              {assetDetailData.price_performance && assetDetailData.price_performance.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={assetDetailData.price_performance.map(p => ({
                    date: new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                    performance: p.performance
                  }))}>
                    <XAxis 
                      dataKey="date"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'currentColor', fontSize: 10 }}
                      interval="preserveStartEnd"
                      minTickGap={20}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'currentColor', fontSize: 12 }}
                      domain={['dataMin', 'dataMax']}
                      tickFormatter={(value) => `${value.toFixed(1)}%`}
                    />
                    <Line
                      type="monotone"
                      dataKey="performance"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  No price performance data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render detailed asset class view
  if (selectedAssetClass) {
    const assetClassData = currentAttributionData?.asset_class_contributions?.find(ac => ac.asset_class === selectedAssetClass);
    if (!assetClassData) return null;
    
    // 차트 데이터 변환
    const trendData = assetClassData.weight_trend?.map(wt => ({
      month: new Date(wt.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      value: wt.weight,
      date: wt.date
    })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()) || [];
    
    const returnData = assetClassData.return_trend?.map(rt => ({
      month: new Date(rt.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
      return: rt.daily_twr,
      date: rt.date
    })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()) || [];
    
    return (
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
        {/* Header with Back Button */}
        <div className="flex items-center mb-6">
          <Button
            variant="ghost" 
            size="sm"
            onClick={() => setSelectedAssetClass(null)}
            className="mr-3 p-2"
            data-testid="button-back-asset-class"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text">
            {assetClassData.asset_class}
          </h1>
        </div>

        {/* Overview Card */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Current Allocation
                </div>
                <div className="text-2xl font-bold text-primary" data-testid="text-allocation-value">
                  {assetClassData.current_allocation.toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Contribution
                </div>
                <div className={`text-2xl font-bold ${assetClassData.contribution >= 0 ? 'text-success' : 'text-danger'}`} data-testid="text-contribution-value">
                  {assetClassData.contribution >= 0 ? '+' : ''}{assetClassData.contribution.toFixed(2)}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Allocation Weight Trend */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center mb-4">
              <TrendingUp className="h-4 w-4 text-primary mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                Allocation Weight Trend
              </h3>
            </div>
            <div className="h-48" data-testid="chart-allocation-trend">
              {trendData && trendData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <XAxis 
                      dataKey="month" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'currentColor', fontSize: 9 }}
                      interval={Math.max(0, Math.floor(trendData.length / 6))}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'currentColor', fontSize: 12 }}
                      domain={['dataMin', 'dataMax']}
                      tickFormatter={(value) => `${value.toFixed(1)}%`}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  No allocation trend data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* TWR Return Trend */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center mb-4">
              <PieChart className="h-4 w-4 mr-2" style={{ color: assetClassColors[selectedAssetClass] || '#10B981' }} />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                Daily TWR Return (%)
              </h3>
            </div>
                        <div className="h-64" data-testid="chart-return-trend">
              {returnData && returnData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={returnData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                    <XAxis 
                      dataKey="month"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'currentColor', fontSize: 9 }}
                      interval={Math.max(0, Math.floor(returnData.length / 8))}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'currentColor', fontSize: 12 }}
                      tickFormatter={(value) => `${value.toFixed(1)}%`}
                      domain={['dataMin', 'dataMax']}
                    />
                    <ReferenceLine y={0} stroke="#374151" strokeDasharray="3 3" />
                    <Bar
                      dataKey="return"
                      radius={[2, 2, 0, 0]}
                    >
                      {returnData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.return >= 0 
                            ? (entry.return > 5 ? "#047857" : "#10B981") 
                            : (entry.return < -5 ? "#B91C1C" : "#EF4444")} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  No return trend data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Top Header with Portfolio Selector and Theme Toggle */}
      <div className="flex items-center justify-between mb-6">
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
        className="mb-4"
      />

      {/* Attribution 데이터 로딩 상태 */}
      {(timePeriod === "all" && allTimeLoading) && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="text-center text-gray-500 dark:text-gray-400">
              Loading attribution data...
            </div>
          </CardContent>
        </Card>
      )}

      {/* Attribution 데이터 에러 상태 */}
      {(timePeriod === "all" && allTimeError) && (
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="text-center text-red-500">
              Error loading attribution data: {allTimeError.message}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Asset Class Attribution */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Attribution by Asset Class
          </h3>
          <div className="space-y-3">
            {assetClassContributions?.map((attribution, index) => {
              const isPositive = attribution.contribution > 0;
              return (
                <div 
                  key={attribution.asset_class} 
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors" 
                  data-testid={`attribution-${index}`}
                  onClick={() => setSelectedAssetClass(attribution.asset_class)}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: assetClassColors[attribution.asset_class] || '#10B981' }}></div>
                    <span className="font-medium text-gray-900 dark:text-dark-text">
                      {attribution.asset_class}
                    </span>
                  </div>
                  <span className={`font-medium ${isPositive ? 'text-success' : 'text-danger'}`}>
                    {isPositive ? '+' : ''}{attribution.contribution.toFixed(2)}%
                  </span>
                </div>
              );
            }) || (
              <div className="text-center text-gray-500 dark:text-gray-400">
                No attribution data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Top Contributors */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Top Contributors
          </h3>
          <div className="space-y-3">
            {topContributors.length > 0 ? (
              topContributors.map((contributor, index) => (
                <div 
                  key={contributor.asset_id} 
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors" 
                  data-testid={`contributor-${index}`}
                  onClick={() => {
                    setSelectedAsset(contributor.name);
                    setSelectedAssetId(contributor.asset_id);
                  }}
                >
                  <div>
                    <div className="font-medium text-gray-900 dark:text-dark-text">
                      {contributor.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {contributor.current_allocation?.toFixed(1)}% allocation
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-success">
                      +{contributor.period_return.toFixed(1)}%
                    </div>
                    <div className="text-sm text-success">
                      Contrib: +{contributor.contribution.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400">
                No contributor data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Top Detractors */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Top Detractors
          </h3>
          <div className="space-y-3">
            {topDetractors.length > 0 ? (
              topDetractors.map((detractor, index) => (
                <div 
                  key={detractor.asset_id} 
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors" 
                  data-testid={`detractor-${index}`}
                  onClick={() => {
                    setSelectedAsset(detractor.name);
                    setSelectedAssetId(detractor.asset_id);
                  }}
                >
                  <div>
                    <div className="font-medium text-gray-900 dark:text-dark-text">
                      {detractor.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {detractor.current_allocation?.toFixed(1)}% allocation
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-danger">
                      {detractor.period_return.toFixed(1)}%
                    </div>
                    <div className="text-sm text-danger">
                      Contrib: {detractor.contribution.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400">
                No detractor data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
