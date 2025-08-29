import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Calendar, TrendingUp, Shield, AlertTriangle } from "lucide-react";

import { Portfolio, PortfoliosResponse, AssetAllocationResponse, AssetClassAllocation, AssetAllocationDetail } from "@shared/types";
import { PortfolioSelector } from "../components/portfolio-selector";
import { DateRangePicker } from "../components/date-range-picker";
import { KpiCard } from "../components/kpi-card";

// Attribution에서 사용된 자산군별 색상 정의
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

// 파이 차트용 데이터 변환
const transformToPieData = (allocations: AssetClassAllocation[]) => {
  return allocations.map(allocation => ({
    name: allocation.asset_class,
    value: allocation.allocation,
    market_value: allocation.market_value,
    assets_count: allocation.assets.length
  }));
};

// 커스텀 툴팁
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
        <p className="font-medium text-gray-900 dark:text-white">{data.name}</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          비중: {data.value.toFixed(2)}%
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          시장가치: ₩{(data.market_value / 1000000).toFixed(1)}M
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          자산 수: {data.assets_count}개
        </p>
      </div>
    );
  }
  return null;
};

export default function Risk() {
  const [currentPortfolio, setCurrentPortfolio] = useState<Portfolio | undefined>();
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedAssetClass, setSelectedAssetClass] = useState<string | null>(null);

  // 포트폴리오 목록 조회
  const { data: portfoliosResponse, isLoading: portfoliosLoading } = useQuery<PortfoliosResponse>({
    queryKey: ["/api/portfolios"],
    queryFn: async () => {
      const response = await fetch('/api/portfolios?include_kpi=false');
      if (!response.ok) throw new Error('Failed to fetch portfolios');
      return response.json();
    },
  });

  const portfolios = portfoliosResponse?.portfolios || [];

  // 자산 배분 데이터 조회
  const { data: allocationData, isLoading: allocationLoading } = useQuery<AssetAllocationResponse>({
    queryKey: ["/api/risk/allocation", currentPortfolio?.id, selectedDate],
    queryFn: async () => {
      if (!currentPortfolio?.id) return null;
      
      const dateParam = selectedDate.toISOString().split('T')[0];
      const response = await fetch(`/api/risk/allocation/${currentPortfolio.id}?as_of_date=${dateParam}&asset_filter=all`);
      if (!response.ok) throw new Error('Failed to fetch allocation data');
      return response.json();
    },
    enabled: !!currentPortfolio?.id,
  });

  // 색상 매핑 생성
  const assetClassColors = useMemo(() => {
    if (!allocationData?.asset_class_allocations) return {};
    const assetClasses = allocationData.asset_class_allocations.map(ac => ac.asset_class);
    return generateColorPalette(assetClasses);
  }, [allocationData]);

  // 파이 차트 데이터
  const pieData = useMemo(() => {
    if (!allocationData?.asset_class_allocations) return [];
    return transformToPieData(allocationData.asset_class_allocations);
  }, [allocationData]);

  // 선택된 자산군의 상세 정보
  const selectedAssetClassDetail = useMemo(() => {
    if (!selectedAssetClass || !allocationData?.asset_class_allocations) return null;
    return allocationData.asset_class_allocations.find(ac => ac.asset_class === selectedAssetClass);
  }, [selectedAssetClass, allocationData]);

  // KPI 계산
  const totalAssetClasses = allocationData?.asset_class_allocations?.length || 0;
  const largestAllocation = allocationData?.asset_class_allocations?.[0]?.allocation || 0;
  const concentrationRisk = largestAllocation > 50 ? "높음" : largestAllocation > 30 ? "보통" : "낮음";

  if (portfoliosLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">로딩 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 pb-20">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Risk</h1>
          </div>
        </div>

        {/* 포트폴리오 선택 */}
        <PortfolioSelector
          portfolios={portfolios}
          currentPortfolio={currentPortfolio}
          onPortfolioChange={setCurrentPortfolio}
          isLoading={portfoliosLoading}
        />

        {/* 날짜 선택 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2 mb-3">
            <Calendar className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">기준일 선택</h3>
          </div>
          <DateRangePicker
            selectedDate={selectedDate}
            onDateChange={(date) => setSelectedDate(date || new Date())}
            mode="single"
          />
        </div>

        {/* KPI 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <KpiCard
            title="자산군 수"
            value={totalAssetClasses.toString()}
            subtitle="다양화 수준"
            valueColor="primary"
          />
          <KpiCard
            title="최대 집중도"
            value={`${largestAllocation.toFixed(1)}%`}
            subtitle="단일 자산군 비중"
            valueColor={largestAllocation > 50 ? "danger" : largestAllocation > 30 ? "primary" : "success"}
          />
          <KpiCard
            title="집중 위험"
            value={concentrationRisk}
            subtitle="포트폴리오 집중도"
            valueColor={concentrationRisk === "높음" ? "danger" : concentrationRisk === "보통" ? "primary" : "success"}
          />
        </div>

        {allocationLoading ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center">
              <div className="text-gray-500 dark:text-gray-400">데이터를 불러오는 중...</div>
            </div>
          </div>
        ) : allocationData && allocationData.asset_class_allocations.length > 0 ? (
          <>
            {/* 자산군별 배분 파이 차트 */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2 mb-6">
                <TrendingUp className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">자산군별 배분</h3>
              </div>
              
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name} ${value.toFixed(1)}%`}
                      labelLine={false}
                    >
                      {pieData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={assetClassColors[entry.name] || '#8884d8'}
                          className="cursor-pointer hover:opacity-80"
                          onClick={() => setSelectedAssetClass(
                            selectedAssetClass === entry.name ? null : entry.name
                          )}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 자산군별 비중 목록 */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">자산군별 세부 정보</h3>
              <div className="space-y-3">
                {allocationData.asset_class_allocations.map((allocation, index) => (
                  <div
                    key={allocation.asset_class}
                    className={`p-4 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                      selectedAssetClass === allocation.asset_class 
                        ? 'ring-2 ring-primary bg-blue-50 dark:bg-blue-900/20' 
                        : ''
                    }`}
                    onClick={() => setSelectedAssetClass(
                      selectedAssetClass === allocation.asset_class ? null : allocation.asset_class
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div 
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: assetClassColors[allocation.asset_class] }}
                        />
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {allocation.asset_class}
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {allocation.assets.length}개 자산
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {allocation.allocation.toFixed(2)}%
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          ₩{(allocation.market_value / 1000000).toFixed(1)}M
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 선택된 자산군의 상세 정보 */}
            {selectedAssetClassDetail && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-2 mb-4">
                  <div 
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: assetClassColors[selectedAssetClassDetail.asset_class] }}
                  />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedAssetClassDetail.asset_class} 구성 자산
                  </h3>
                </div>
                
                <div className="grid gap-4">
                  {selectedAssetClassDetail.assets.map((asset) => (
                    <div
                      key={asset.asset_id}
                      className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {asset.name}
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {asset.ticker} • {asset.region === 'domestic' ? '국내' : '해외'}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-gray-900 dark:text-white">
                            {asset.weight.toFixed(2)}%
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            ₩{(asset.market_value / 1000000).toFixed(1)}M
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-500">
                            {asset.quantity.toLocaleString()} {asset.currency}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex flex-col items-center justify-center text-center">
              <AlertTriangle className="h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                데이터가 없습니다
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {currentPortfolio ? '선택한 날짜에 포지션 데이터가 없습니다.' : '포트폴리오를 선택해주세요.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
