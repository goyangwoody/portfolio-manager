import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { ChevronLeft, TrendingUp, TrendingDown, PieChart } from "lucide-react";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import type { Portfolio, AttributionData, Holding } from "@shared/schema";

export default function Attribution() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const [selectedAssetClass, setSelectedAssetClass] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  const portfolio = currentPortfolio || portfolios?.[0];

  const handleTimePeriodChange = (period: TimePeriod, customWeek?: string, customMonth?: string) => {
    setTimePeriod(period);
    console.log("Period changed:", period, customWeek, customMonth);
  };

  const { data: attributionData } = useQuery<AttributionData[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "attribution"],
    enabled: !!portfolio?.id,
  });

  const { data: contributors } = useQuery<Holding[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "holdings"],
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

  const topContributors = contributors?.filter(h => h.type === "contributor") || [];
  const topDetractors = contributors?.filter(h => h.type === "detractor") || [];

  const getAssetClassColor = (index: number) => {
    const colors = ["bg-primary", "bg-success", "bg-warning", "bg-danger"];
    return colors[index % colors.length];
  };

  // Generate mock detailed data for asset class
  const getAssetClassDetails = (assetClass: string, allocation: string, contribution: string) => {
    const trendData = [
      { month: "Jan", value: parseFloat(allocation) * 0.95 },
      { month: "Feb", value: parseFloat(allocation) * 1.02 },
      { month: "Mar", value: parseFloat(allocation) * 0.98 },
      { month: "Apr", value: parseFloat(allocation) * 1.05 },
      { month: "May", value: parseFloat(allocation) * 1.08 },
      { month: "Jun", value: parseFloat(allocation) }
    ];
    
    const returnData = [
      { month: "Jan", return: parseFloat(contribution) * 0.8 },
      { month: "Feb", return: parseFloat(contribution) * 1.2 },
      { month: "Mar", return: parseFloat(contribution) * 0.9 },
      { month: "Apr", return: parseFloat(contribution) * 1.1 },
      { month: "May", return: parseFloat(contribution) * 1.3 },
      { month: "Jun", return: parseFloat(contribution) }
    ];

    return { trendData, returnData };
  };

  // Render detailed asset view (for contributors/detractors)
  if (selectedAsset) {
    const assetHolding = contributors?.find(h => h.name === selectedAsset);
    if (!assetHolding) return null;
    
    // Generate mock performance data for the asset
    const assetPerformanceData = [
      { date: "Jan", price: 150.25 },
      { date: "Feb", price: 155.30 },
      { date: "Mar", price: 148.90 },
      { date: "Apr", price: 162.40 },
      { date: "May", price: 168.75 },
      { date: "Jun", price: 175.80 }
    ];
    
    return (
      <div className="max-w-md mx-auto px-4 py-6 pb-20">
        {/* Header with Back Button */}
        <div className="flex items-center mb-6">
          <Button
            variant="ghost" 
            size="sm"
            onClick={() => setSelectedAsset(null)}
            className="mr-3 p-2"
            data-testid="button-back-asset"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-text">
            {assetHolding.name}
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
                  {assetHolding.weight}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Return
                </div>
                <div className={`text-lg font-bold ${parseFloat(assetHolding.return) >= 0 ? 'text-success' : 'text-danger'}`} data-testid="text-asset-return">
                  {parseFloat(assetHolding.return) >= 0 ? '+' : ''}{assetHolding.return}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Contribution
                </div>
                <div className={`text-lg font-bold ${parseFloat(assetHolding.contribution) >= 0 ? 'text-success' : 'text-danger'}`} data-testid="text-asset-contribution">
                  {parseFloat(assetHolding.contribution) >= 0 ? '+' : ''}{assetHolding.contribution}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Price Chart */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center mb-4">
              <TrendingUp className="h-4 w-4 text-primary mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                Price Performance
              </h3>
            </div>
            <div className="h-64" data-testid="chart-asset-performance">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={assetPerformanceData}>
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
    );
  }

  // Render detailed asset class view
  if (selectedAssetClass) {
    const assetClassData = attributionData?.find(attr => attr.assetClass === selectedAssetClass);
    if (!assetClassData) return null;
    
    const { trendData, returnData } = getAssetClassDetails(
      assetClassData.assetClass, 
      assetClassData.allocation, 
      assetClassData.contribution
    );
    
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
            {assetClassData.assetClass}
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
                  {assetClassData.allocation}%
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                  Contribution
                </div>
                <div className={`text-2xl font-bold ${parseFloat(assetClassData.contribution) >= 0 ? 'text-success' : 'text-danger'}`} data-testid="text-contribution-value">
                  {parseFloat(assetClassData.contribution) >= 0 ? '+' : ''}{assetClassData.contribution}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Market Value Trend */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center mb-4">
              <TrendingUp className="h-4 w-4 text-primary mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                Allocation Weight Trend
              </h3>
            </div>
            <div className="h-48" data-testid="chart-allocation-trend">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <XAxis 
                    dataKey="month" 
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
                    dataKey="value"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Return Trend */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center mb-4">
              <PieChart className="h-4 w-4 text-success mr-2" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                Return Trend
              </h3>
            </div>
            <div className="h-48" data-testid="chart-return-trend">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={returnData}>
                  <XAxis 
                    dataKey="month"
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
                    dataKey="return"
                    stroke="#10B981"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
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
        onPortfolioChange={setCurrentPortfolio}
        currentPortfolio={portfolio}
      />

      {/* Asset Class Attribution */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Attribution by Asset Class
          </h3>
          <div className="space-y-3">
            {attributionData?.map((attribution, index) => {
              const isPositive = parseFloat(attribution.contribution) > 0;
              return (
                <div 
                  key={attribution.id} 
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors" 
                  data-testid={`attribution-${index}`}
                  onClick={() => setSelectedAssetClass(attribution.assetClass)}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 ${getAssetClassColor(index)} rounded-full`}></div>
                    <span className="font-medium text-gray-900 dark:text-dark-text">
                      {attribution.assetClass}
                    </span>
                  </div>
                  <span className={`font-medium ${isPositive ? 'text-success' : 'text-danger'}`}>
                    {isPositive ? '+' : ''}{attribution.contribution}%
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
                  key={contributor.id} 
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors" 
                  data-testid={`contributor-${index}`}
                  onClick={() => setSelectedAsset(contributor.name)}
                >
                  <div>
                    <div className="font-medium text-gray-900 dark:text-dark-text">
                      {contributor.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {contributor.weight}% allocation
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-success">
                      +{contributor.return}%
                    </div>
                    <div className="text-sm text-success">
                      +{contributor.contribution}%
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
                  key={detractor.id} 
                  className="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors" 
                  data-testid={`detractor-${index}`}
                  onClick={() => setSelectedAsset(detractor.name)}
                >
                  <div>
                    <div className="font-medium text-gray-900 dark:text-dark-text">
                      {detractor.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {detractor.weight}% allocation
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-danger">
                      {detractor.return}%
                    </div>
                    <div className="text-sm text-danger">
                      {detractor.contribution}%
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
