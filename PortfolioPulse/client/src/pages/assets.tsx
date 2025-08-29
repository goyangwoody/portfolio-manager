import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { X } from "lucide-react";
import { DateSelector } from "@/components/date-selector";
import { AssetSortSelector, type SortField, type SortDirection } from "@/components/asset-sort-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import { ThemeToggle } from "@/components/theme-toggle";
import { ErrorBoundary } from "@/components/error-boundary";
import type { Portfolio, PortfolioPositionsByDate, PortfolioPositionDailyDetail } from "@shared/types";
import { formatCurrency, formatLargeNumber } from "@/lib/utils";
import { format } from "date-fns";

interface AssetDetailSheetProps {
  asset: PortfolioPositionDailyDetail | null;
  portfolio: Portfolio | undefined;
  isOpen: boolean;
  onClose: () => void;
}

function AssetDetailSheet({ asset, portfolio, isOpen, onClose }: AssetDetailSheetProps) {
  const { data: performanceData } = useQuery<{
    asset_id: number;
    asset_name: string;
    asset_symbol: string;
    prices: Array<{
      date: string;
      price: number;
    }>;
  }>({
    queryKey: ["/api/assets", asset?.asset_id, "price-history"],
    queryFn: async () => {
      if (!asset?.asset_id) throw new Error("No asset ID");
      
      const response = await fetch(`/api/assets/${asset.asset_id}/price-history?days=90`);
      if (!response.ok) {
        throw new Error(`Failed to fetch price history: ${response.status}`);
      }
      
      return response.json();
    },
    enabled: isOpen && !!asset?.asset_id,
  });

  const chartData = performanceData?.prices?.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    }),
    price: Number(item.price),
  })) || [];

  if (!isOpen || !asset) return null;

  // 안전하게 숫자로 변환
  const dayChangePercent = typeof asset.day_change_percent === 'string' 
    ? parseFloat(asset.day_change_percent) 
    : (asset.day_change_percent || 0);
  const isPositiveChange = dayChangePercent >= 0;
  const unrealizedPnL = asset.current_price && asset.avg_price 
    ? (asset.current_price - asset.avg_price) * asset.quantity
    : 0;
  const isPositivePL = unrealizedPnL >= 0;
  const totalReturnPct = asset.current_price && asset.avg_price && asset.avg_price > 0
    ? ((asset.current_price - asset.avg_price) / asset.avg_price) * 100
    : 0;
  const isPositiveReturn = totalReturnPct >= 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
      <div className="bg-white dark:bg-dark-card w-full max-h-[90vh] rounded-t-2xl overflow-hidden">
        {/* Header with drag indicator */}
        <div className="bg-gray-50 dark:bg-gray-800 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="w-12 h-1 bg-gray-300 dark:bg-gray-600 rounded-full mx-auto mb-4"></div>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-dark-text truncate" data-testid="text-asset-name">
                {asset.asset_name}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400" data-testid="text-asset-ticker">
                {asset.asset_symbol}
              </p>
            </div>
            <button 
              onClick={onClose}
              className="ml-4 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 flex-shrink-0"
              data-testid="button-close-sheet"
            >
              <X className="h-6 w-6 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Current Price
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-current-price">
                {portfolio ? formatCurrency(asset.current_price ?? asset.avg_price, portfolio.currency) : `$${(asset.current_price ?? asset.avg_price).toLocaleString()}`}
              </div>
              <div className={`text-xs ${isPositiveChange ? 'text-success' : 'text-danger'}`} data-testid="text-day-change">
                {isPositiveChange ? '+' : ''}{dayChangePercent.toFixed(2)}% today
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Avg. Purchase Price
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-avg-price">
                {portfolio ? formatCurrency(asset.avg_price, portfolio.currency) : `$${asset.avg_price}`}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Held Quantity
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-quantity">
                {Number(asset.quantity).toLocaleString(undefined, { 
                  minimumFractionDigits: 0, 
                  maximumFractionDigits: Number(asset.quantity) % 1 === 0 ? 0 : 2 
                })} shares
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Market Value
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-market-value">
                {portfolio ? formatCurrency(asset.market_value, portfolio.currency) : `$${asset.market_value.toLocaleString()}`}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* P/L and Returns */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Unrealized P/L
              </div>
              <div className={`text-lg font-bold ${isPositivePL ? 'text-success' : 'text-danger'}`} data-testid="text-unrealized-pl">
                {isPositivePL ? '+' : ''}{portfolio ? formatCurrency(Math.abs(unrealizedPnL), portfolio.currency) : `$${Math.abs(unrealizedPnL).toLocaleString()}`}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Total Return
              </div>
              <div className={`text-lg font-bold ${isPositiveReturn ? 'text-success' : 'text-danger'}`} data-testid="text-cumulative-return">
                {isPositiveReturn ? '+' : ''}{totalReturnPct.toFixed(2)}%
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Price Chart */}
        <Card>
          <CardContent className="p-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
              Price History
            </h3>
            <div className="h-64 w-full" data-testid="chart-asset-performance">
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
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(value) => 
                      portfolio ? 
                        formatLargeNumber(value, portfolio.currency) : 
                        `$${(value/1000).toFixed(0)}K`
                    }
                  />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}

export default function Assets() {
  return (
    <ErrorBoundary>
      <AssetsContent />
    </ErrorBoundary>
  );
}

function AssetsContent() {
  const [selectedAsset, setSelectedAsset] = useState<PortfolioPositionDailyDetail | null>(null);
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const queryClient = useQueryClient();

  const portfolio = currentPortfolio;

  // 최신 날짜 가져오기
  const { data: latestDateData } = useQuery<{ latest_date: string }>({
    queryKey: ["/api/portfolios", portfolio?.id, "positions", "latest-date"],
    queryFn: async () => {
      if (!portfolio?.id) throw new Error("No portfolio selected");
      
      const response = await fetch(`/api/portfolios/${portfolio.id}/positions/latest-date`);
      if (!response.ok) {
        throw new Error(`Failed to fetch latest date: ${response.status}`);
      }
      
      return response.json();
    },
    enabled: !!portfolio?.id,
  });

  // 최신 날짜를 기본값으로 설정
  if (latestDateData?.latest_date && !selectedDate) {
    setSelectedDate(new Date(latestDateData.latest_date));
  }

  console.log("🚀 Assets component rendering with:", {
    portfolio: portfolio?.name,
    selectedDate: selectedDate?.toISOString(),
    latestDate: latestDateData?.latest_date,
    sortField,
    sortDirection
  });

  const handleDateChange = (date: Date | undefined) => {
    console.log("🗓️ Date change triggered:", { 
      from: selectedDate, 
      to: date, 
      portfolioId: portfolio?.id 
    });
    setSelectedDate(date);
    
    // 날짜 변경 시 쿼리 무효화하여 새로운 데이터 요청
    if (portfolio?.id) {
      const queryKey = ["/api/portfolios", portfolio.id, "positions", date ? format(date, "yyyy-MM-dd") : "latest", sortField, sortDirection];
      console.log("🔄 Invalidating query with key:", queryKey);
      queryClient.invalidateQueries({ queryKey });
    }
  };

  const handleSortChange = (field: SortField, direction: SortDirection) => {
    setSortField(field);
    setSortDirection(direction);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
    console.log("Portfolio changed in Assets:", newPortfolio);
    // 포트폴리오 변경 시 자산 데이터 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "assets"] 
    });
  };

  const { data: positionsData, isLoading, error } = useQuery<PortfolioPositionsByDate>({
    queryKey: ["/api/portfolios", portfolio?.id, "positions", selectedDate ? format(selectedDate, "yyyy-MM-dd") : "latest", sortField, sortDirection],
    queryFn: async () => {
      if (!portfolio?.id) throw new Error("No portfolio selected");
      
      let url: string;
      if (selectedDate) {
        url = `/api/portfolios/${portfolio.id}/positions/${format(selectedDate, "yyyy-MM-dd")}`;
      } else {
        url = `/api/portfolios/${portfolio.id}/positions/latest`;
      }
      
      console.log("🌐 API Request:", {
        url,
        portfolioId: portfolio.id,
        selectedDate: selectedDate ? format(selectedDate, "yyyy-MM-dd") : "latest",
        sortField,
        sortDirection
      });
      
      const response = await fetch(url);
      console.log("🌐 API Response:", {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          // 404는 에러가 아니라 데이터가 없는 상태로 처리
          console.log("📭 No data found for the selected date");
          return null;
        }
        console.error("❌ API Error:", response.status, response.statusText);
        throw new Error(`Failed to fetch positions: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("📊 Positions data received:", {
        hasData: !!data,
        positionsCount: data?.positions?.length || 0,
        sampleData: data?.positions?.[0] || null
      });
      
      return data;
    },
    enabled: !!portfolio?.id,
  });

  console.log("🔄 Component State:", {
    portfolioId: portfolio?.id,
    selectedDate: selectedDate ? format(selectedDate, "yyyy-MM-dd") : "none",
    isLoading,
    error: error?.message,
    hasData: !!positionsData,
    positionsData: positionsData ? {
      hasPositions: !!positionsData.positions,
      positionsCount: positionsData.positions?.length || 0
    } : null
  });

  // 포지션 데이터에서 자산 목록 추출 (안전하게 처리)
  const assets = (positionsData && positionsData.positions) ? positionsData.positions : [];
  console.log("📊 Assets data:", {
    positionsData,
    assetsCount: assets.length,
    firstAsset: assets[0] || null
  });

  // 자산 정렬 함수 (안전하게 처리)
  const sortedAssets = Array.isArray(assets) && assets.length > 0 ? [...assets].sort((a, b) => {
    if (!a || !b) return 0;
    
    let aValue: any, bValue: any;
    
    try {
      switch (sortField) {
        case "name":
          aValue = (a.asset_name || '').toLowerCase();
          bValue = (b.asset_name || '').toLowerCase();
          break;
        case "avgPrice":
          aValue = a.avg_price || 0;
          bValue = b.avg_price || 0;
          break;
        case "currentPrice":
          aValue = a.current_price || a.avg_price || 0;
          bValue = b.current_price || b.avg_price || 0;
          break;
        case "dayChange":
          aValue = typeof a.day_change_percent === 'string' ? parseFloat(a.day_change_percent) : (a.day_change_percent || 0);
          bValue = typeof b.day_change_percent === 'string' ? parseFloat(b.day_change_percent) : (b.day_change_percent || 0);
          break;
        case "totalReturn":
          aValue = a.current_price && a.avg_price && a.avg_price > 0
            ? ((a.current_price - a.avg_price) / a.avg_price) * 100
            : 0;
          bValue = b.current_price && b.avg_price && b.avg_price > 0
            ? ((b.current_price - b.avg_price) / b.avg_price) * 100
            : 0;
          break;
        case "marketValue":
          aValue = a.market_value || 0;
          bValue = b.market_value || 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    } catch (error) {
      console.error("Sorting error:", error);
      return 0;
    }
  }) : [];

  if (!portfolio) {
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

  if (isLoading) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-dark-card rounded-xl p-4 shadow-sm animate-pulse">
              <div className="flex justify-between items-center">
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                </div>
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 에러 상태 처리
  if (error) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
        <PortfolioSelector
          currentPortfolio={currentPortfolio}
          onPortfolioChange={handlePortfolioChange}
          className="mb-6"
        />
        
        <DateSelector
          value={selectedDate}
          onChange={handleDateChange}
          className="mb-6"
        />

        <div className="text-center text-gray-500 dark:text-gray-400 py-8">
          <h3 className="text-lg font-semibold mb-2">선택한 날짜에 데이터가 없습니다</h3>
          <p className="text-sm">다른 날짜를 선택해보세요.</p>
          {selectedDate && (
            <p className="text-xs mt-2">
              선택된 날짜: {format(selectedDate, "yyyy년 MM월 dd일")}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Top Header with Portfolio Selector and Theme Toggle */}
      <div className="flex items-center justify-between mb-6">
        <PortfolioSelector
          currentPortfolio={currentPortfolio}
          onPortfolioChange={handlePortfolioChange}
        />
        <ThemeToggle />
      </div>

      {/* Date and Sort Controls */}
      <div className="space-y-4 mb-6">
        {/* Date Selector */}
        <div className="space-y-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Analysis Date
          </span>
          <DateSelector
            value={selectedDate}
            onChange={handleDateChange}
            placeholder="Select analysis date"
            maxDate={new Date()}
          />
        </div>

        {/* Sort Controls */}
        <div className="space-y-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Sort By
          </span>
          <AssetSortSelector
            sortField={sortField}
            sortDirection={sortDirection}
            onSortChange={handleSortChange}
          />
        </div>
      </div>

      <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text mb-6">
        Portfolio Assets
        {selectedDate && (
          <span className="text-sm font-normal text-gray-500 dark:text-gray-400 block">
            as of {format(selectedDate, "MMM d, yyyy")}
          </span>
        )}
      </h1>

      <div className="space-y-3">
        {sortedAssets?.length > 0 ? sortedAssets.map((asset, index) => {
          // 안전하게 숫자로 변환
          const dayChangePercent = typeof asset.day_change_percent === 'string' 
            ? parseFloat(asset.day_change_percent) 
            : (asset.day_change_percent || 0);
          const isPositiveChange = dayChangePercent >= 0;
          
          return (
            <Card 
              key={asset.asset_id} 
              className="cursor-pointer hover:shadow-md transition-shadow active:scale-[0.98] active:shadow-sm"
              onClick={() => setSelectedAsset(asset)}
              data-testid={`asset-item-${index}`}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <div className="flex-1 min-w-0 pr-3">
                    <div className="font-medium text-gray-900 dark:text-dark-text truncate">
                      {asset.asset_name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Avg. {portfolio ? formatCurrency(asset.avg_price, portfolio.currency) : `$${asset.avg_price}`}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className={`font-medium ${isPositiveChange ? 'text-success' : 'text-danger'}`}>
                      {isPositiveChange ? '+' : ''}{dayChangePercent.toFixed(2)}%
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {portfolio ? formatCurrency(asset.current_price || asset.avg_price, portfolio.currency) : `$${asset.current_price || asset.avg_price}`}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        }) : (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <h3 className="text-lg font-semibold mb-2">
              {error ? "선택한 날짜에 데이터가 없습니다" : "자산 데이터를 불러오는 중..."}
            </h3>
            <p className="text-sm">
              {error ? "다른 날짜를 선택해보세요." : "잠시만 기다려주세요."}
            </p>
            {selectedDate && error && (
              <p className="text-xs mt-2">
                선택된 날짜: {format(selectedDate, "yyyy년 MM월 dd일")}
              </p>
            )}
          </div>
        )}
      </div>

      <AssetDetailSheet 
        asset={selectedAsset}
        portfolio={portfolio}
        isOpen={!!selectedAsset}
        onClose={() => setSelectedAsset(null)}
      />
    </div>
  );
}