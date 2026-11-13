export const CATEGORY_COLORS = {
  "Food & Dining": "#e8743b",
  Groceries: "#2f9e6e",
  Transport: "#3b82c4",
  Shopping: "#c2549b",
  "Bills & Utilities": "#7a6bd0",
  Entertainment: "#d9a521",
  Health: "#d6455d",
  Education: "#2a9db0",
  Travel: "#8a6a4f",
  Other: "#8b93a1",
};

export const money = (n, digits = 0) =>
  "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: digits, minimumFractionDigits: digits });

export const currentMonth = () => new Date().toISOString().slice(0, 7);
export const today = () => new Date().toISOString().slice(0, 10);

export const formatDate = (iso) =>
  new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
