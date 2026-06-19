/**
 * Format a Date (or date-like value) as 'YY/MM/DD HH:mm'.
 * Returns the input unchanged if it cannot be parsed.
 *
 * @param {Date|string|number} date - value convertible to Date
 * @returns {string} formatted date string
 */
export function formatDateTime(date) {
  const d = new Date(date);
  if (Number.isNaN(d.getTime())) return date;
  const yy = String(d.getFullYear()).slice(-2);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yy}/${mm}/${dd} ${hh}:${mi}`;
}

