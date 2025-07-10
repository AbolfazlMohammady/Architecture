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

  update(data, start_km, end_km) {
    this.data = data;
    this.start_km = start_km;
    this.end_km = end_km;
    this.draw();
  }

  draw() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.strokeStyle = '#bbb';
    ctx.lineWidth = 1;

    // خط افقی محور X
    ctx.beginPath();
    ctx.moveTo(0, this.height - 19 - this.margin);
    ctx.lineTo(this.width, this.height - 19 - this.margin);
    ctx.stroke();

    ctx.fillStyle = '#222';
    ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';

    // نمایش همه لیبل‌ها با فاصله مساوی
    const range = this.end_km - this.start_km;
    this.data.forEach((km, index) => {
      const x = ((km - this.start_km) / range) * this.width;
      let kmInt = Math.floor(km);
      let m = Math.round((km - kmInt) * 1000);
      let kmLabel = kmInt + (m > 0 ? '+' + (m < 100 ? ('0' + m).slice(-3) : m) : '+000');
      kmLabel = kmLabel.replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
      ctx.save();
      ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
      ctx.fillStyle = '#222';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(kmLabel, x, this.height - this.margin - 18);
      ctx.restore();
      // خط کوچک عمودی کنار لیبل
      ctx.beginPath();
      ctx.moveTo(x, this.height - 19 - this.margin);
      ctx.lineTo(x, this.height - 14 - this.margin);
      ctx.stroke();
    });

    // برچسب اصلی محور X
    // حذف عنوان محور X
  }
}
