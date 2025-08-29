import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar as CalendarIcon, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import { format, addDays, subDays } from "date-fns";
import { cn } from "@/lib/utils";

interface DateSelectorProps {
  value?: Date;
  onChange: (date: Date | undefined) => void;
  className?: string;
  placeholder?: string;
  maxDate?: Date;
  minDate?: Date;
}

export function DateSelector({
  value,
  onChange,
  className = "",
  placeholder = "Select date",
  maxDate = new Date(), // 기본값: 오늘
  minDate
}: DateSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleDateSelect = (date: Date | undefined) => {
    onChange(date);
    setIsOpen(false);
  };

  const navigateDate = (direction: "prev" | "next") => {
    if (!value) return;
    
    const newDate = direction === "prev" ? subDays(value, 1) : addDays(value, 1);
    
    // 날짜 범위 체크
    if (maxDate && newDate > maxDate) return;
    if (minDate && newDate < minDate) return;
    
    onChange(newDate);
  };

  return (
    <div className={className}>
      <div className="flex items-center space-x-2">
        {/* 이전 날짜 버튼 */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigateDate("prev")}
          disabled={!value || (minDate && subDays(value, 1) < minDate)}
          className="h-8 w-8 p-0 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 hover:bg-blue-100 dark:hover:bg-blue-800/50"
          data-testid="date-prev-button"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        {/* 날짜 선택 버튼 */}
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                "flex-1 justify-between text-left font-normal",
                !value && "text-muted-foreground"
              )}
              data-testid="date-selector-trigger"
            >
              <div className="flex items-center space-x-2">
                <CalendarIcon className="h-4 w-4" />
                <span>
                  {value ? format(value, "MMM d, yyyy") : placeholder}
                </span>
              </div>
              <ChevronDown className="h-4 w-4 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={value}
              onSelect={handleDateSelect}
              disabled={(date) => {
                if (maxDate && date > maxDate) return true;
                if (minDate && date < minDate) return true;
                return false;
              }}
              initialFocus
            />
          </PopoverContent>
        </Popover>

        {/* 다음 날짜 버튼 */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigateDate("next")}
          disabled={!value || (maxDate && addDays(value, 1) > maxDate)}
          className="h-8 w-8 p-0 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 hover:bg-blue-100 dark:hover:bg-blue-800/50"
          data-testid="date-next-button"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
