import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, ChevronLeft, ChevronRight, Clock } from "lucide-react";

export type TimePeriod = "all" | "1w" | "2w" | "1m" | "custom";

interface TimePeriodSelectorProps {
  value: TimePeriod;
  onChange: (period: TimePeriod, customWeek?: string, customMonth?: string) => void;
  variant?: "overview" | "default";
  className?: string;
}

export function TimePeriodSelector({ 
  value, 
  onChange, 
  variant = "default", 
  className = ""
}: TimePeriodSelectorProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customWeek, setCustomWeek] = useState("");
  const [customMonth, setCustomMonth] = useState("");

  const handlePeriodChange = (newPeriod: TimePeriod) => {
    if (newPeriod === "custom") {
      // Custom 선택 시 바로 가장 최근 주를 선택하되, 드롭다운도 표시
      const latestWeek = weekOptions[0]?.value; // 가장 최근 주
      if (latestWeek) {
        setCustomWeek(latestWeek);
        setCustomMonth(""); // 월간 선택 클리어
        setShowCustom(true); // 드롭다운도 표시해서 다른 선택 가능
        onChange("custom", latestWeek, undefined);
      }
    } else {
      setShowCustom(false);
      // 일반 기간 선택 시 커스텀 상태 클리어
      setCustomWeek("");
      setCustomMonth("");
      // 일반 기간 선택 시에도 전체 파라미터 전달 (커스텀 파라미터는 undefined)
      onChange(newPeriod, undefined, undefined);
    }
  };

  const handleCustomSelection = (type: "week" | "month", value: string) => {
    if (type === "week") {
      setCustomWeek(value);
      setCustomMonth(""); // 월간 선택 클리어
      onChange("custom", value, undefined);
    } else {
      setCustomMonth(value);
      setCustomWeek(""); // 주간 선택 클리어
      onChange("custom", undefined, value);
    }
    setShowCustom(false);
  };

  const isOverview = variant === "overview";

  const quickOptions = isOverview 
    ? [
        { value: "all" as const, label: "All Time" },
        { value: "1w" as const, label: "1W" },
        { value: "2w" as const, label: "2W" },
        { value: "1m" as const, label: "1M" }
      ]
    : [
        { value: "all" as const, label: "All Time" }
      ];

  // Generate week options (last 12 weeks)
  const weekOptions: Array<{ value: string; label: string }> = [];
  const today = new Date();
  
  // Find the start of current week (Monday)
  const getCurrentWeekStart = (date: Date): Date => {
    const d = new Date(date);
    const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
    const diff = day === 0 ? -6 : 1 - day; // Sunday면 -6일, 다른 요일은 1-day
    const monday = new Date(d);
    monday.setDate(d.getDate() + diff);
    return monday;
  };
  
  // ISO 8601 주차 계산 (백엔드와 동일한 방식)
  const getISOWeekNumber = (date: Date): { year: number; week: number } => {
    const d = new Date(date);
    const year = d.getFullYear();
    
    // 1월 4일은 항상 첫 번째 주에 포함 (ISO 8601 기준)
    const jan4 = new Date(year, 0, 4); // 1월 4일
    
    // 1월 4일이 포함된 주의 월요일 찾기
    const jan4Day = jan4.getDay(); // 0=Sunday, 1=Monday, ..., 6=Saturday
    const daysSinceMonday = jan4Day === 0 ? 6 : jan4Day - 1; // Sunday면 6, 다른 요일은 day-1
    const firstWeekMonday = new Date(jan4);
    firstWeekMonday.setDate(jan4.getDate() - daysSinceMonday);
    
    // 현재 날짜가 포함된 주의 월요일 찾기
    const currentDay = d.getDay();
    const currentDaysSinceMonday = currentDay === 0 ? 6 : currentDay - 1;
    const currentWeekMonday = new Date(d);
    currentWeekMonday.setDate(d.getDate() - currentDaysSinceMonday);
    
    // 주차 계산 (첫 번째 주의 월요일부터 몇 주 후인지)
    const diffTime = currentWeekMonday.getTime() - firstWeekMonday.getTime();
    const diffWeeks = Math.floor(diffTime / (7 * 24 * 60 * 60 * 1000));
    const weekNumber = diffWeeks + 1;
    
    // 음수 주차면 이전 연도의 마지막 주
    if (weekNumber < 1) {
      return getISOWeekNumber(new Date(year - 1, 11, 31));
    }
    
    // 53주를 넘으면 다음 연도의 첫 번째 주
    if (weekNumber > 52) {
      const nextYearJan4 = new Date(year + 1, 0, 4);
      if (d >= nextYearJan4) {
        return getISOWeekNumber(new Date(year + 1, 0, 1));
      }
    }
    
    return { year, week: weekNumber };
  };
  
  const currentWeekStart = getCurrentWeekStart(today);
  
  for (let i = 0; i < 12; i++) {
    const weekStart = new Date(currentWeekStart);
    weekStart.setDate(currentWeekStart.getDate() - (i * 7));
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    
    const startStr = weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    const { year, week } = getISOWeekNumber(weekStart);
    
    weekOptions.push({
      value: `${year}-W${week.toString().padStart(2, '0')}`,
      label: `${startStr} - ${endStr}`
    });
  }

  // Generate month options (last 12 months)
  const monthOptions: Array<{ value: string; label: string }> = [];
  for (let i = 0; i < 12; i++) {
    const month = new Date();
    month.setMonth(today.getMonth() - i);
    monthOptions.push({
      value: month.toISOString().slice(0, 7),
      label: month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    });
  }

  // Navigation functions for week/month
  const navigatePeriod = (direction: "prev" | "next") => {
    if (customWeek && !customMonth) {
      // Week navigation
      const currentIndex = weekOptions.findIndex(w => w.value === customWeek);
      if (currentIndex !== -1) {
        let newIndex;
        if (direction === "prev") {
          newIndex = currentIndex < weekOptions.length - 1 ? currentIndex + 1 : currentIndex;
        } else {
          newIndex = currentIndex > 0 ? currentIndex - 1 : currentIndex;
        }
        const newWeek = weekOptions[newIndex];
        if (newWeek) {
          setCustomWeek(newWeek.value);
          onChange("custom", newWeek.value, undefined);
        }
      }
    } else if (customMonth && !customWeek) {
      // Month navigation
      const currentIndex = monthOptions.findIndex(m => m.value === customMonth);
      if (currentIndex !== -1) {
        let newIndex;
        if (direction === "prev") {
          newIndex = currentIndex < monthOptions.length - 1 ? currentIndex + 1 : currentIndex;
        } else {
          newIndex = currentIndex > 0 ? currentIndex - 1 : currentIndex;
        }
        const newMonth = monthOptions[newIndex];
        if (newMonth) {
          setCustomMonth(newMonth.value);
          onChange("custom", undefined, newMonth.value);
        }
      }
    }
  };

  const getCurrentLabel = () => {
    if (value === "custom") {
      // 월간이 선택된 경우 (customMonth가 있고 customWeek가 없거나 빈 문자열)
      if (customMonth && !customWeek) {
        const monthOption = monthOptions.find(m => m.value === customMonth);
        return monthOption ? `Month: ${monthOption.label}` : "Custom Month";
      }
      // 주간이 선택된 경우 (customWeek가 있고 customMonth가 없거나 빈 문자열)
      if (customWeek && !customMonth) {
        const weekOption = weekOptions.find(w => w.value === customWeek);
        return weekOption ? `Week: ${weekOption.label}` : "Custom Week";
      }
      // 둘 다 없는 경우
      return "Select Period";
    }
    const option = quickOptions.find(o => o.value === value);
    return option?.label || "All Time";
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Period Selection */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Calendar className="h-4 w-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Analysis Period
          </span>
        </div>
        
        <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {quickOptions.map((option) => (
            <Button
              key={option.value}
              variant={value === option.value ? "default" : "ghost"}
              size="sm"
              onClick={() => handlePeriodChange(option.value)}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                value === option.value
                  ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              }`}
              data-testid={`button-period-${option.value}`}
            >
              {option.label}
            </Button>
          ))}
          
          <Button
            variant={value === "custom" ? "default" : "ghost"}
            size="sm"
            onClick={() => handlePeriodChange("custom")}
            className={`px-3 py-1 text-xs font-medium transition-colors ${
              value === "custom"
                ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
                : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            }`}
            data-testid="button-period-custom"
          >
            <Clock className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Current Selection Display */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/50 rounded-lg p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-medium text-blue-700 dark:text-blue-300 uppercase tracking-wide">
              Current Period
            </span>
            {/* Navigation arrows - only show for custom week/month */}
            {value === "custom" && (customWeek || customMonth) && (
              <div className="flex items-center space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigatePeriod("prev")}
                  className="h-6 w-6 p-0 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 hover:bg-blue-100 dark:hover:bg-blue-800/50"
                  data-testid="button-prev-period"
                >
                  <ChevronLeft className="h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigatePeriod("next")}
                  className="h-6 w-6 p-0 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 hover:bg-blue-100 dark:hover:bg-blue-800/50"
                  data-testid="button-next-period"
                >
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
          <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
            {getCurrentLabel()}
          </span>
        </div>
      </div>

      {/* Custom Selection Dropdown */}
      {showCustom && (
        <div className="space-y-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Specific Week
            </label>
            <Select onValueChange={(value) => handleCustomSelection("week", value)} value={customWeek}>
              <SelectTrigger className="w-full" data-testid="select-custom-week">
                <SelectValue placeholder="Choose a week" />
              </SelectTrigger>
              <SelectContent>
                {weekOptions.map((week) => (
                  <SelectItem key={week.value} value={week.value}>
                    {week.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Specific Month
            </label>
            <Select onValueChange={(value) => handleCustomSelection("month", value)} value={customMonth}>
              <SelectTrigger className="w-full" data-testid="select-custom-month">
                <SelectValue placeholder="Choose a month" />
              </SelectTrigger>
              <SelectContent>
                {monthOptions.map((month) => (
                  <SelectItem key={month.value} value={month.value}>
                    {month.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      )}
    </div>
  );
}