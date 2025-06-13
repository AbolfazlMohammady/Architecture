export class RoadLine {
  constructor({ canvasId, width = 1100, height = 450, start_kilometer, end_kilometer }) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');

    this.width = width;
    this.height = height;

    this.canvas.width = this.width;
    this.canvas.height = this.height;

    this.points = [];

    this.start_kilometer = start_kilometer
    this.end_kilometer = end_kilometer
  }

  update(points) {
    this.points = points;
    this.draw();

  }
  // رسم خط از (startX, startY) به (startX + lengthX, startY + lengthY)
  draw() {
    const ctx = this.ctx;

    

    ctx.beginPath();
    ctx.strokeStyle = "black";
    ctx.lineWidth = 3;

    ctx.moveTo(this.kmToX(this.points[0].x), this.heightToY(this.points[0].y));
     for (let i = 1; i < this.points.length; i++) {
            const ptx = this.kmToX(this.points[i].x);
            const pty = this.heightToY(this.points[i].y);

            ctx.lineTo(ptx, pty);
     }
    ctx.stroke();
  }
heightToY(height) {
    const metersRange = 50; // دامنه کامل ارتفاع از -25 تا +25
    const pixelsPerMeter = this.height / metersRange;
    return (this.height / 2) - (height * pixelsPerMeter);
}

  kmToX(xInMeters) {
    const xKm = xInMeters / 1000; // مثلاً 30100 → 30.1
    const range = 1

    const relativeKm = xKm - this.start_kilometer;
    const ratio = relativeKm / range;

    return ratio * this.canvas.width;
  }
}
