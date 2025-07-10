export class YAxisCanvas {
  constructor({canvasId, height, width, margin,yunit}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.height = height;
    this.width = width;
    this.margin = margin;
    this.yunit = yunit;

    this.canvas.width = width;
    this.canvas.height = height ;

    this.data = [];
  }

  update(data) {
    this.data = data;
    this.draw();
  }
  fittext(text){
    while(text.length < 5){
        text = " " + text
    }
    return text

  }
  draw() {
  const ctx = this.ctx;
  ctx.clearRect(0, 0, this.width, this.height);

  ctx.strokeStyle = '#bbb';
  ctx.lineWidth = 1;

  // خط عمودی ثابت سمت راست y-axis
  ctx.beginPath();
  ctx.moveTo(this.width - 1 - this.margin, 0);
  ctx.lineTo(this.width - 1 - this.margin, this.height);
  ctx.stroke();

  ctx.fillStyle = '#222';
  ctx.font = '14px Vazirmatn, Tahoma, Arial, sans-serif';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'right';

  const paddingY = 10;
  const stepY = this.yunit;

  // نمایش همه لیبل‌ها با فاصله مساوی
  this.data.forEach((label, index) => {
    const y = this.height - paddingY - stepY * index;
    let labelStr = parseFloat(label).toFixed(1).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
    ctx.fillText(this.fittext(labelStr), this.width - 12, y);
    ctx.beginPath();
    ctx.moveTo(this.width - 10 - this.margin, y);
    ctx.lineTo(this.width - 1 - this.margin, y);
    ctx.stroke();
  });

  // برچسب اصلی محور Y (ارتفاع)
  // حذف عنوان محور Y
  }
 }