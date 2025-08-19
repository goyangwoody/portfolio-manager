import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, ChevronDown } from "lucide-react";
import type { Portfolio } from "@shared/schema";

export type TimePeriod = "all" | "1w" | "2w" | "1m" | "custom";

interface TimePeriodSelectorProps {
  value: TimePeriod;
  onChange: (period: TimePeriod, customWeek?: string, customMonth?: string) => void;
  variant?: "overview" | "default";
  className?: string;
  onPortfolioChange?: (portfolio: Portfolio) => void;
  currentPortfolio?: Portfolio;
}

export function TimePeriodSelector({ 
  value, 
  onChange, 
  variant = "default", 
  className = "",
  onPortfolioChange,
  currentPortfolio
}: TimePeriodSelectorProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customWeek, setCustomWeek] = useState("");
  const [customMonth, setCustomMonth] = useState("");
  const [selectedType, setSelectedType] = useState<"domestic" | "foreign">("domestic");

  const { data: domesticPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "domestic"],
    queryFn: () => fetch("/api/portfolios?type=domestic").then(res => res.json()),
  });

  const { data: foreignPortfolios } = useQuery<Portfolio[]>({
    queryKey: ["/api/portfolios", "foreign"], 
    queryFn: () => fetch("/api/portfolios?type=foreign").then(res => res.json()),
  });

  const handleTypeChange = (type: "domestic" | "foreign") => {
    setSelectedType(type);
    const portfolios = type === "domestic" ? domesticPortfolios : foreignPortfolios;
    if (portfolios && portfolios.length > 0 && onPortfolioChange) {
      onPortfolioChange(portfolios[0]);
    }
  };

  const handlePeriodChange = (newPeriod: TimePeriod) => {
    if (newPeriod === "custom") {
      setShowCustom(true);
    } else {
      setShowCustom(false);
      onChange(newPeriod);
    }
  };

  const handleCustomSelection = (type: "week" | "month", value: string) => {
    if (type === "week") {
      setCustomWeek(value);
      onChange("custom", value, undefined);
    } else {
      setCustomMonth(value);
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
  for (let i = 0; i < 12; i++) {
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - (i * 7));
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    
    const startStr = weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    // Create unique key using ISO week number
    const startOfYear = new Date(weekStart.getFullYear(), 0, 1);
    const weekNumber = Math.ceil(((weekStart.getTime() - startOfYear.getTime()) / 86400000 + startOfYear.getDay() + 1) / 7);
    
    weekOptions.push({
      value: `${weekStart.getFullYear()}-W${weekNumber}-${i}`,
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

  const getCurrentLabel = () => {
    if (value === "custom" && customWeek) {
      const weekOption = weekOptions.find(w => w.value === customWeek);
      return weekOption ? `Week: ${weekOption.label}` : "Custom Week";
    }
    if (value === "custom" && customMonth) {
      const monthOption = monthOptions.find(m => m.value === customMonth);
      return monthOption ? `Month: ${monthOption.label}` : "Custom Month";
    }
    const option = quickOptions.find(o => o.value === value);
    return option?.label || "All Time";
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Portfolio Type Selector - only show if onPortfolioChange is provided */}
      {onPortfolioChange && (
        <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1 max-w-fit">
          <Button
            variant={selectedType === "domestic" ? "default" : "ghost"}
            size="sm"
            onClick={() => handleTypeChange("domestic")}
            className={`px-4 py-2 text-xs font-medium transition-colors ${
              selectedType === "domestic"
                ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
                : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            }`}
            data-testid="button-domestic-portfolio"
          >
            Domestic
          </Button>
          <Button
            variant={selectedType === "foreign" ? "default" : "ghost"}
            size="sm"
            onClick={() => handleTypeChange("foreign")}
            className={`px-4 py-2 text-xs font-medium transition-colors ${
              selectedType === "foreign"
                ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
                : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            }`}
            data-testid="button-foreign-portfolio"
          >
            Foreign
          </Button>
        </div>
      )}
      
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
            <ChevronDown className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Current Selection Display */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/50 rounded-lg p-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-blue-700 dark:text-blue-300 uppercase tracking-wide">
            Current Period
          </span>
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
            <Select onValueChange={(value) => handleCustomSelection("week", value)}>
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
            <Select onValueChange={(value) => handleCustomSelection("month", value)}>
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