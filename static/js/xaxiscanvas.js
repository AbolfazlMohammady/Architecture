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

    ctx.fillStyle = '#222';
    ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';

    // نمایش لیبل‌ها هر ۰.۵ کیلومتر
    const range = this.end_km - this.start_km;
    this.data.forEach((km, index) => {
      const x = ((km - this.start_km) / range) * this.width;
      // Format label: show decimals only if needed, negative with '-', positive without sign, Persian digits
      let kmLabelNum = (km % 1 === 0) ? Math.floor(km) : parseFloat(km.toFixed(1));
      let kmLabel = '';
      if (kmLabelNum < 0) {
        kmLabel = '-' + Math.abs(kmLabelNum);
      } else {
        kmLabel = kmLabelNum.toString();
      }
      // Replace dot with Persian decimal, and digits with Persian digits
      kmLabel = kmLabel.replace('.', '٫').replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
      ctx.save();
      ctx.font = '11px Vazirmatn, Tahoma, Arial, sans-serif'; // even smaller font
      ctx.fillStyle = '#444';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.shadowColor = '#fff';
      ctx.shadowBlur = 2;
      ctx.fillText(kmLabel, x, this.height - 28); // adjust position for smaller font
      ctx.shadowBlur = 0;
      ctx.restore();
      // Draw small vertical tick under label
      ctx.beginPath();
      ctx.moveTo(x, this.height - 19 - this.margin);
      ctx.lineTo(x, this.height - 14 - this.margin);
      ctx.stroke();
    });

    // برچسب اصلی محور X
    // حذف عنوان محور X
  }
}
