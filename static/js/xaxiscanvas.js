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
    console.log('XAxisCanvas.update:', { data, start_km, end_km });
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

    ctx.fillStyle = '#000';
    ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';

    // لیبل‌گذاری پویا بر اساس طول بازه
    const range = this.end_km - this.start_km;
    let step = range < 10 ? 0.5 : 1;
    let labels = [];
    for (let km = this.start_km; km <= this.end_km + 0.0001; km += step) {
      // گرد کردن به یک رقم اعشار برای جلوگیری از اعشار اضافی
      let label = Math.round(km * 10) / 10;
      labels.push(label);
    }
    labels.forEach((km) => {
      const x = ((km - this.start_km) / range) * this.width;
      // تبدیل عدد به فارسی
      let kmLabel = km.toString().replace('.', '٫').replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
      ctx.save();
      ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
      ctx.fillStyle = '#000';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.shadowColor = '#fff';
      ctx.shadowBlur = 2;
      ctx.fillText(kmLabel, x, this.height - 18);
      ctx.shadowBlur = 0;
      ctx.restore();
      // خط کوچک زیر لیبل
      ctx.beginPath();
      ctx.moveTo(x, this.height - 19 - this.margin);
      ctx.lineTo(x, this.height - 14 - this.margin);
      ctx.stroke();
    });
  }
}
