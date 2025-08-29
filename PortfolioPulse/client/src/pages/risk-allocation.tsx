import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { TimePeriodSelector, type TimePeriod } from "@/components/time-period-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import type { Portfolio, AttributionData } from "@shared/types";

// 임시 타입 정의 (나중에 shared/types.ts로 이동)
interface RiskMetrics {
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  beta: number;
  var95: number;
  correlation: number;
}

interface SectorAllocation {
  sector: string;
  allocation: number;
  color: string;
}

export default function RiskAllocation() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>("all");
  const [customWeek, setCustomWeek] = useState<string>("");
  const [customMonth, setCustomMonth] = useState<string>("");
  const queryClient = useQueryClient();

  const { data: portfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
  });

  const portfolio = currentPortfolio || portfolios?.[0];

  const handleTimePeriodChange = (period: TimePeriod, customWeekParam?: string, customMonthParam?: string) => {
    console.log(`🔄 Risk-Allocation 기간 변경: ${timePeriod} → ${period}`, { customWeekParam, customMonthParam });
    
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
    
    console.log(`✅ Risk-Allocation 기간 변경 완료`);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    setCurrentPortfolio(newPortfolio);
    // 포트폴리오 변경 시 리스크 관련 데이터 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "attribution"] 
    });
    queryClient.invalidateQueries({ 
      queryKey: ["/api/portfolios", newPortfolio.id, "risk-allocation"] 
    });
  };

  const { data: attributionData } = useQuery<AttributionData[]>({
    queryKey: ["/api/portfolios", portfolio?.id, "attribution"],
    enabled: !!portfolio?.id,
  });

  const { data: riskAndAllocationData } = useQuery<any>({
    queryKey: ["/api/portfolios", portfolio?.id, "risk-allocation"],
    queryFn: async () => {
      const response = await fetch(`/api/portfolios/${portfolio?.id}/risk-allocation`);
      if (!response.ok) throw new Error('Failed to fetch risk allocation data');
      return response.json();
    },
    enabled: !!portfolio?.id,
  });

  // 백엔드 응답에서 데이터 분리
  const riskMetrics = riskAndAllocationData?.risk_metrics;
  const sectorAllocations = riskAndAllocationData?.sector_allocation;

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        <div className="text-center text-gray-500 dark:text-gray-400">
          No portfolio data available
        </div>
      </div>
    );
  }

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

  const allocationChartData = attributionData?.map((item, index) => ({
    name: item.assetClass,
    value: item.allocation,
    color: COLORS[index % COLORS.length]
  })) || [];

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

      {/* Current Allocation Chart */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Current Allocation
          </h3>
          
          <div className="h-64 w-full" data-testid="chart-allocation">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={allocationChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={0}
                  dataKey="value"
                >
                  {allocationChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="grid grid-cols-2 gap-3 mt-4">
            {allocationChartData.map((allocation, index) => (
              <div key={allocation.name} className="flex items-center space-x-2" data-testid={`allocation-${index}`}>
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: allocation.color }}
                ></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {allocation.name} ({allocation.value}%)
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Risk Analysis
          </h3>
          {riskMetrics ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Annualized Volatility</span>
                <span className="font-medium" data-testid="text-risk-volatility">
                  {riskMetrics.volatility}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Value at Risk (95%)</span>
                <span className="font-medium text-danger" data-testid="text-risk-var">
                  {riskMetrics.var95}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Maximum Drawdown</span>
                <span className="font-medium text-danger" data-testid="text-risk-drawdown">
                  {riskMetrics.maxDrawdown}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Beta vs S&P 500</span>
                <span className="font-medium" data-testid="text-risk-beta">
                  {riskMetrics.beta}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Correlation vs S&P 500</span>
                <span className="font-medium" data-testid="text-risk-correlation">
                  {riskMetrics.correlation}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
                <span className="font-medium text-success" data-testid="text-risk-sharpe">
                  {riskMetrics.sharpeRatio}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400">
              No risk metrics available
            </div>
          )}
        </CardContent>
      </Card>


    </div>
  );
}
