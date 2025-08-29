interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  valueColor?: "success" | "primary" | "danger" | "default";
  testId?: string;
}

export function KpiCard({ title, value, subtitle, valueColor = "default", testId }: KpiCardProps) {
  const getValueColorClass = () => {
    switch (valueColor) {
      case "success":
        return "text-success";
      case "primary":
        return "text-primary";
      case "danger":
        return "text-danger";
      default:
        return "text-gray-900 dark:text-dark-text";
    }
  };

  return (
    <div className="bg-white dark:bg-dark-card rounded-xl p-4 shadow-sm text-center" data-testid={testId}>
      <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
        {title}
      </div>
      <div className={`text-2xl font-bold ${getValueColorClass()}`} data-testid={`text-${testId}-value`}>
        {value}
      </div>
      {subtitle && (
        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1" data-testid={`text-${testId}-subtitle`}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
