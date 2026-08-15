const numberFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });
const integerFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export const format = {
  number: (value: number, digits = 3) =>
    new Intl.NumberFormat("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value),
  compact: (value: number) => numberFormatter.format(value),
  integer: (value: number) => integerFormatter.format(value),
  percent: (value: number, digits = 2) =>
    new Intl.NumberFormat("en-US", {
      style: "percent",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value),
  currency: (value: number) => currencyFormatter.format(value),
  timestamp: (value: string) =>
    new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
      timeZoneName: "short",
    }).format(new Date(value)),
};
