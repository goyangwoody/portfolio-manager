import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { X } from "lucide-react";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import type { Portfolio, Asset, AssetPerformanceData } from "@shared/types";
import { formatCurrency } from "@/lib/utils";

interface AssetDetailSheetProps {
  asset: Asset | null;
  portfolio: Portfolio | undefined;
  isOpen: boolean;
  onClose: () => void;
}

function AssetDetailSheet({ asset, portfolio, isOpen, onClose }: AssetDetailSheetProps) {
  const { data: performanceData } = useQuery<AssetPerformanceData[]>({
    queryKey: ["/api/assets", asset?.id, "performance"],
    enabled: isOpen && !!asset?.id,
  });

  const chartData = performanceData?.map((item: AssetPerformanceData) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short' }),
    price: item.price,
  })) || [];

  if (!isOpen || !asset) return null;

  const isPositiveChange = parseFloat(asset.dayChange) >= 0;
  const isPositivePL = asset.unrealizedPnL >= 0;
  const isPositiveReturn = asset.totalReturn >= 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
      <div className="bg-white dark:bg-dark-card w-full max-h-[80vh] rounded-t-2xl p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-dark-text" data-testid="text-asset-name">
              {asset.name}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400" data-testid="text-asset-ticker">
              {asset.ticker}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            data-testid="button-close-sheet"
          >
            <X className="h-6 w-6 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Current Price
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-current-price">
                ${asset.currentPrice}
              </div>
              <div className={`text-xs ${isPositiveChange ? 'text-success' : 'text-danger'}`} data-testid="text-day-change">
                {isPositiveChange ? '+' : ''}{asset.dayChange}% today
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Avg. Purchase Price
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-avg-price">
                {portfolio ? formatCurrency(asset.avgPrice, portfolio.currency) : `$${asset.avgPrice}`}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Held Quantity
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-quantity">
                {asset.quantity.toLocaleString()} shares
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Market Value
              </div>
              <div className="text-lg font-bold text-gray-900 dark:text-dark-text" data-testid="text-market-value">
                {portfolio ? formatCurrency(asset.currentPrice * asset.quantity, portfolio.currency) : `$${(asset.currentPrice * asset.quantity).toLocaleString()}`}
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
                {isPositivePL ? '+' : ''}{portfolio ? formatCurrency(Math.abs(asset.unrealizedPnL), portfolio.currency) : `$${Math.abs(asset.unrealizedPnL)}`}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                Total Return
              </div>
              <div className={`text-lg font-bold ${isPositiveReturn ? 'text-success' : 'text-danger'}`} data-testid="text-cumulative-return">
                {isPositiveReturn ? '+' : ''}{asset.totalReturn.toFixed(2)}%
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
  );
}

export default function Assets() {
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const queryClient = useQueryClient();

  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  const portfolio = currentPortfolio || portfolios?.[0];

  const handleTimePeriodChange = (period: TimePeriod, customWeek?: string, customMonth?: string) => {
    setTimePeriod(period);
    console.log("Period changed:", period, customWeek, customMonth);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
    // 포트폴리오 변경 시 자산 데이터 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "assets"] 
    });
  };

  const { data: assets, isLoading } = useQuery<Asset[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "assets"],
    enabled: !!portfolio?.id,
  });

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          No portfolio data available
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

      <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text mb-6">
        Portfolio Assets
      </h1>

      <div className="space-y-3">
        {assets?.map((asset, index) => {
          const isPositiveChange = parseFloat(asset.dayChange || "0") >= 0;
          
          return (
            <Card 
              key={asset.id} 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedAsset(asset)}
              data-testid={`asset-item-${index}`}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-dark-text">
                      {asset.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      Avg. {portfolio ? formatCurrency(asset.avgPrice, portfolio.currency) : `$${asset.avgPrice}`}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-medium ${isPositiveChange ? 'text-success' : 'text-danger'}`}>
                      {isPositiveChange ? '+' : ''}{asset.dayChange}%
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {portfolio ? formatCurrency(asset.currentPrice, portfolio.currency) : `$${asset.currentPrice}`}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        }) || (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            No assets available
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