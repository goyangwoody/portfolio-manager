import { BarChart3, TrendingUp, PieChart, Shield, Wallet } from "lucide-react";
import { Link, useLocation } from "wouter";

const navigationItems = [
  {
    path: "/",
    label: "Overview",
    icon: BarChart3,
    testId: "nav-overview"
  },
  {
    path: "/performance",
    label: "Performance",
    icon: TrendingUp,
    testId: "nav-performance"
  },
  {
    path: "/attribution",
    label: "Attribution",
    icon: PieChart,
    testId: "nav-attribution"
  },
  {
    path: "/assets",
    label: "Assets",
    icon: Wallet,
    testId: "nav-assets"
  },
  {
    path: "/risk",
    label: "Risk",
    icon: Shield,
    testId: "nav-risk"
  }
];

export function BottomNavigation() {
  const [location] = useLocation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-dark-card border-t border-gray-200 dark:border-gray-700 px-4 py-2">
      <div className="max-w-md mx-auto">
        <div className="flex justify-around">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.path;
            
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex flex-col items-center py-2 px-2 rounded-lg transition-colors duration-200 ${
                  isActive
                    ? "text-primary bg-blue-50 dark:bg-blue-900/20"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                }`}
                data-testid={`link-${item.testId}`}
              >
                <Icon className="text-lg mb-1 h-4 w-4" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
