import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 통화별 포매팅 함수
export function formatCurrency(amount: number, currency: string): string {
  const currencyConfig = {
    'KRW': { symbol: '₩', locale: 'ko-KR', decimals: 0 },
    'USD': { symbol: '$', locale: 'en-US', decimals: 2 },
    'EUR': { symbol: '€', locale: 'de-DE', decimals: 2 },
    'JPY': { symbol: '¥', locale: 'ja-JP', decimals: 0 },
  };

  const config = currencyConfig[currency as keyof typeof currencyConfig] || currencyConfig['USD'];
  
  try {
    return new Intl.NumberFormat(config.locale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: config.decimals,
      maximumFractionDigits: config.decimals,
    }).format(amount);
  } catch (error) {
    // 알 수 없는 통화인 경우 기본 포맷
    return `${config.symbol}${amount.toLocaleString(config.locale, {
      minimumFractionDigits: config.decimals,
      maximumFractionDigits: config.decimals,
    })}`;
  }
}

// 큰 숫자를 축약하여 표시 (AUM 등에 사용)
export function formatLargeNumber(amount: number, currency: string): string {
  if (amount >= 1e12) {
    return formatCurrency(amount / 1e12, currency).replace(/[\d.,]+/, (match) => 
      (parseFloat(match.replace(/,/g, '')) / 1000).toFixed(1) + 'T'
    );
  }
  if (amount >= 1e9) {
    return formatCurrency(amount / 1e9, currency).replace(/[\d.,]+/, (match) => 
      (parseFloat(match.replace(/,/g, '')) / 1000).toFixed(1) + 'B'
    );
  }
  if (amount >= 1e6) {
    return formatCurrency(amount / 1e6, currency).replace(/[\d.,]+/, (match) => 
      (parseFloat(match.replace(/,/g, '')) / 1000).toFixed(1) + 'M'
    );
  }
  return formatCurrency(amount, currency);
}
