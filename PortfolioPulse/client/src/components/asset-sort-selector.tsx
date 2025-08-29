import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

export type SortField = "name" | "avgPrice" | "currentPrice" | "dayChange" | "totalReturn" | "marketValue";
export type SortDirection = "asc" | "desc";

interface SortOption {
  value: SortField;
  label: string;
}

interface AssetSortSelectorProps {
  sortField: SortField;
  sortDirection: SortDirection;
  onSortChange: (field: SortField, direction: SortDirection) => void;
  className?: string;
}

const sortOptions: SortOption[] = [
  { value: "name", label: "Asset Name" },
  { value: "avgPrice", label: "Avg Price" },
  { value: "currentPrice", label: "Current Price" },
  { value: "dayChange", label: "Day Change" },
  { value: "totalReturn", label: "Total Return" },
  { value: "marketValue", label: "Market Value" }
];

export function AssetSortSelector({
  sortField,
  sortDirection,
  onSortChange,
  className = ""
}: AssetSortSelectorProps) {
  const handleFieldChange = (field: SortField) => {
    onSortChange(field, sortDirection);
  };

  const handleDirectionToggle = () => {
    const newDirection = sortDirection === "asc" ? "desc" : "asc";
    onSortChange(sortField, newDirection);
  };

  const getSortIcon = () => {
    if (sortDirection === "asc") {
      return <ArrowUp className="h-4 w-4" />;
    } else {
      return <ArrowDown className="h-4 w-4" />;
    }
  };

  const currentOption = sortOptions.find(option => option.value === sortField);

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className="flex-1">
        <Select value={sortField} onValueChange={handleFieldChange}>
          <SelectTrigger className="w-full" data-testid="sort-field-selector">
            <SelectValue>
              <div className="flex items-center space-x-2">
                <ArrowUpDown className="h-4 w-4 text-gray-500" />
                <span>{currentOption?.label || "Sort by"}</span>
              </div>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {sortOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      <Button
        variant="outline"
        size="sm"
        onClick={handleDirectionToggle}
        className="px-3"
        data-testid="sort-direction-toggle"
      >
        {getSortIcon()}
      </Button>
    </div>
  );
}
