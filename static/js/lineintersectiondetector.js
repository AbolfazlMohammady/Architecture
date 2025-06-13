export class LineIntersectionDetector {
  constructor(line1, line2) {
    this.line1 = line1; // { x1, y1, x2, y2 }
    this.line2 = line2; // { x1, y1, x2, y2 }
  }

  /**
   * بررسی برخورد بین دو خط
   * @returns {null | {x: number, y: number}} نقطه برخورد یا null
   */
  checkIntersection() {
    const { x1, y1, x2, y2 } = this.line1;
    const { x3, y3, x4, y4 } = this.line2;

    const denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    if (denominator === 0) return null; // خطوط موازی یا روی‌هم هستند

    const px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator;
    const py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator;

    // بررسی اینکه نقطه تقاطع داخل هر دو بازه هست یا نه
    const within = (a, b, c) => Math.min(a, b) - 0.5 <= c && c <= Math.max(a, b) + 0.5;

    const onLine1 = within(x1, x2, px) && within(y1, y2, py);
    const onLine2 = within(x3, x4, px) && within(y3, y4, py);

    if (onLine1 && onLine2) {
      return { x: px, y: py };
    }

    return null;
  }
}
