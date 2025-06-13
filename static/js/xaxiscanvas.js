export class XAxisCanvas {
  constructor({canvasId, width, height, margin = 5,xunit}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = width;
    this.height = height;
    this.margin = margin;
    this.xunit = xunit

    this.canvas.width = width;
    this.canvas.height = height;

    this.data = [];
  }

  update(data) {
    this.data = data;
    this.draw();
  }

  draw() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.strokeStyle = 'black';
    ctx.lineWidth = 1;

    // خط افقی ثابت پایین یا بالا (اینجا پایین)
    ctx.beginPath();
    ctx.moveTo(0, this.height - 19 - this.margin);
    ctx.lineTo(this.width, this.height - 19 - this.margin);
    ctx.stroke();

    ctx.fillStyle = 'black';
    ctx.font = '12px monospace';
    ctx.textBaseline = 'middle';

    // فاصله بین لیبل‌ها
    const stepX = this.xunit;

    this.data.forEach((label, index) => {
      const x = stepX * index;

      // متن لیبل کمی از پایین فاصله بگیره (مارجین فقط عمودی)
      ctx.fillText(label.toString(), x , this.height - this.margin - 4);

      // خط کوچک عمودی کنار لیبل
      ctx.beginPath();
      ctx.moveTo(x, this.height - 19 - this.margin);
      ctx.lineTo(x, this.height - 14 - this.margin);
      ctx.stroke();
    });
  }
}
