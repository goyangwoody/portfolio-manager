import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { DateSelector } from "@/components/date-selector";
import { PortfolioSelector } from "@/components/portfolio-selector";
import { format } from "date-fns";
import type { 
  Portfolio, 
  AssetAllocationResponse, 
  AssetClassAllocation 
} from "@shared/types";

// generateColorPalette: create a stable color mapping for asset classes (from attribution page)
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

export default function RiskAllocation() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [selectedAssetClass, setSelectedAssetClass] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const portfolio = currentPortfolio;

  // 포트폴리오 자동 선택을 위한 더미 쿼리 (PortfolioSelector 내부 로직 참고)
  const { data: portfoliosData } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios"],
    queryFn: async () => {
      const response = await fetch(`/api/portfolios?portfolio_type=core&include_kpi=true&include_chart=true`);
      if (!response.ok) throw new Error('Failed to fetch portfolios');
      const data = await response.json();
      return data.portfolios || [];
    },
  });

  // 포트폴리오 자동 선택
  useEffect(() => {
    if (!currentPortfolio && portfoliosData && portfoliosData.length > 0) {
      console.log(`🚀 Risk-Allocation 초기 포트폴리오 설정:`, portfoliosData[0]);
      setCurrentPortfolio(portfoliosData[0]);
    }
  }, [portfoliosData, currentPortfolio]);

  // 포트폴리오 자동 선택
  useEffect(() => {
    if (portfoliosData && portfoliosData.length > 0 && !currentPortfolio) {
      console.log(`🔄 Risk-Allocation 포트폴리오 자동 선택:`, portfoliosData[0]);
      setCurrentPortfolio(portfoliosData[0]);
    }
  }, [portfoliosData, currentPortfolio]);

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

  // 최신 날짜 자동 선택
  useEffect(() => {
    if (latestDateData?.latest_date && !selectedDate) {
      setSelectedDate(new Date(latestDateData.latest_date));
    }
  }, [latestDateData?.latest_date, selectedDate]);

  const handleDateChange = (date: Date | undefined) => {
    console.log(`🔄 Risk-Allocation 날짜 변경:`, date);
    setSelectedDate(date);
  };

  const handlePortfolioChange = (newPortfolio: Portfolio) => {
    console.log(`🔄 Risk-Allocation 포트폴리오 변경:`, newPortfolio);
    setCurrentPortfolio(newPortfolio);
    setSelectedAssetClass(null); // 포트폴리오 변경 시 선택된 자산군 초기화
    // 포트폴리오 변경 시 관련 데이터 무효화
    queryClient.invalidateQueries({ 
      queryKey: ["/api/risk/allocation", newPortfolio.id] 
    });
    queryClient.invalidateQueries({ 
      queryKey: ["/api/risk/analysis", newPortfolio.id] 
    });
  };

  const handleAssetClassClick = (assetClass: string) => {
    console.log(`🔄 Risk-Allocation 자산군 선택:`, assetClass);
    console.log(`🔄 현재 portfolio:`, portfolio);
    console.log(`🔄 현재 selectedDate:`, selectedDate);
    // TODO: 자산군 상세 카드 구현 예정
    // setSelectedAssetClass(assetClass);
  };

  const handleBackClick = () => {
    setSelectedAssetClass(null);
  };

  // 자산 배분 데이터 조회
  const { data: allocationData } = useQuery<AssetAllocationResponse>({
    queryKey: ["/api/risk/allocation", portfolio?.id, selectedDate ? format(selectedDate, "yyyy-MM-dd") : "latest"],
    queryFn: async () => {
      const dateParam = selectedDate ? `?as_of_date=${format(selectedDate, "yyyy-MM-dd")}` : '';
      const response = await fetch(`/api/risk/allocation/${portfolio?.id}${dateParam}`);
      if (!response.ok) throw new Error('Failed to fetch asset allocation data');
      return response.json();
    },
    enabled: !!portfolio?.id && !!selectedDate,
  });

  // // 리스크 분석 데이터 조회 (나중에 구현)
  // const { data: riskAnalysisData } = useQuery<RiskAnalysisResponse>({
  //   queryKey: ["/api/risk/analysis", portfolio?.id],
  //   queryFn: async () => {
  //     const response = await fetch(`/api/risk/analysis/${portfolio?.id}`);
  //     if (!response.ok) throw new Error('Failed to fetch risk analysis data');
  //     return response.json();
  //   },
  //   enabled: !!portfolio?.id,
  // });

  // 선택된 자산군의 상세 정보 조회 (나중에 구현)
  /*
  const { data: assetClassDetails, isLoading: isLoadingDetails, error: detailsError } = useQuery<AssetClassDetailsResponse>({
    queryKey: ["/api/risk/allocation", portfolio?.id, "class", selectedAssetClass, selectedDate ? format(selectedDate, "yyyy-MM-dd") : "latest"],
    queryFn: async () => {
      console.log(`🚀 API 호출 시작:`, {
        portfolio_id: portfolio?.id,
        asset_class: selectedAssetClass,
        date: selectedDate ? format(selectedDate, "yyyy-MM-dd") : "latest"
      });
      const dateParam = selectedDate ? `?as_of_date=${format(selectedDate, "yyyy-MM-dd")}` : '';
      const url = `/api/risk/allocation/${portfolio?.id}/class/${encodeURIComponent(selectedAssetClass!)}${dateParam}`;
      console.log(`🚀 요청 URL:`, url);
      const response = await fetch(url);
      if (!response.ok) {
        console.error(`❌ API 에러:`, response.status, response.statusText);
        throw new Error('Failed to fetch asset class details');
      }
      const data = await response.json();
      console.log(`✅ API 응답:`, data);
      return data;
    },
    enabled: !!portfolio?.id && !!selectedAssetClass,
  });

  console.log(`🔍 selectedAssetClass:`, selectedAssetClass);
  console.log(`🔍 assetClassDetails:`, assetClassDetails);
  console.log(`🔍 isLoadingDetails:`, isLoadingDetails);
  console.log(`🔍 detailsError:`, detailsError);
  */

  if (!portfolio) {
    return (
      <div className="max-w-md mx-auto px-4 py-6">
        {/* Portfolio Selector - 포트폴리오가 없을 때도 표시 */}
        <PortfolioSelector
          currentPortfolio={portfolio}
          onPortfolioChange={handlePortfolioChange}
          className="mb-4"
        />
        <div className="text-center text-gray-500 dark:text-gray-400">
          Please select a portfolio to view risk allocation
        </div>
      </div>
    );
  }

  // 색깔 매핑 생성
  const assetClasses = allocationData?.allocations?.map(item => item.asset_class) || [];
  const colorMap = generateColorPalette(assetClasses);

  // 파이 차트 데이터 생성
  const allocationChartData = allocationData?.allocations?.map((allocation) => ({
    name: allocation.asset_class,
    value: allocation.total_weight,
    color: colorMap[allocation.asset_class]
  })) || [];

  // 메인 페이지 렌더링
  return (
    <div className="max-w-md mx-auto px-4 py-6 pb-20">
      {/* Portfolio Selector */}
      <PortfolioSelector
        currentPortfolio={portfolio}
        onPortfolioChange={handlePortfolioChange}
        className="mb-4"
      />
      
      {/* Date Selector */}
      <DateSelector
        value={selectedDate}
        onChange={handleDateChange}
        className="mb-6"
      />

      {/* Allocation Chart */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Allocation
          </h3>
          
          {/* 세로 막대 차트 */}
          <div className="space-y-4">
            {/* 막대 차트와 범례를 나란히 배치 */}
            <div className="flex items-end space-x-6">
              {/* 왼쪽 세로 막대 */}
              <div className="flex flex-col justify-end w-8" style={{ height: `${allocationChartData.length * 52 + (allocationChartData.length - 1) * 4}px` }}>
                <div className="flex flex-col bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden">
                  {allocationChartData.map((allocation, index) => (
                    <div
                      key={allocation.name}
                      className="cursor-pointer transition-opacity hover:opacity-80"
                      style={{ 
                        height: `${allocation.value * (allocationChartData.length * 52 + (allocationChartData.length - 1) * 4) / 100}px`,
                        backgroundColor: allocation.color 
                      }}
                      onClick={() => handleAssetClassClick(allocation.name)}
                      data-testid={`allocation-bar-${index}`}
                      title={`${allocation.name}: ${allocation.value.toFixed(1)}%`}
                    />
                  ))}
                </div>
              </div>
              
              {/* 오른쪽 스택 순서 범례 */}
              <div className="flex-1 space-y-1">
                {allocationChartData.map((allocation, index) => (
                  <div 
                    key={allocation.name} 
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors h-[52px]"
                    onClick={() => handleAssetClassClick(allocation.name)}
                    data-testid={`allocation-${index}`}
                  >
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-4 h-4 rounded-sm" 
                        style={{ backgroundColor: allocation.color }}
                      ></div>
                      <span className="font-medium text-gray-900 dark:text-dark-text">
                        {allocation.name}
                      </span>
                    </div>
                    <span className="text-lg font-semibold text-gray-900 dark:text-dark-text">
                      {allocation.value.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sharpe Ratio Card */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Risk Metrics
          </h3>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
            <span className="font-medium text-green-600 text-xl" data-testid="text-risk-sharpe">
              1.24
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics - 나중에 구현 */}
      {/* <Card className="mb-6">
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-4">
            Risk Metrics
          </h3>
          {riskAnalysisData?.portfolio_metrics ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Annualized Volatility</span>
                <span className="font-medium" data-testid="text-risk-volatility">
                  {riskAnalysisData.portfolio_metrics.volatility.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Value at Risk (95%)</span>
                <span className="font-medium text-red-600" data-testid="text-risk-var">
                  {riskAnalysisData.portfolio_metrics.var_95.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Maximum Drawdown</span>
                <span className="font-medium text-red-600" data-testid="text-risk-drawdown">
                  {riskAnalysisData.portfolio_metrics.max_drawdown.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
                <span className="font-medium text-green-600" data-testid="text-risk-sharpe">
                  {riskAnalysisData.portfolio_metrics.sharpe_ratio.toFixed(2)}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400">
              No risk metrics available
            </div>
          )}
        </CardContent>
      </Card> */}
    </div>
  );
}
