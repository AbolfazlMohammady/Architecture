export class YAxisCanvas {
  constructor({canvasId, height, width, margin,yunit}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.height = height;
    this.width = width;
    this.margin = margin;
    this.yunit = yunit;

    // تنظیم canvas با در نظر گیری devicePixelRatio برای کیفیت بالا
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    
    // تنظیم scale برای context
    this.ctx.scale(dpr, dpr);

    this.data = [];
  }

  update(data, yMin, yMax) {
    this.data = data;
    this.yMin = yMin;
    this.yMax = yMax;
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
  // پاک کردن canvas
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
  const canvasHeight = this.height - paddingY * 2;

  // محاسبه موقعیت Y هر لیبل بر اساس مقدار واقعی آن
  // yMin در پایین (نزدیک محور X) و yMax در بالا است
  this.data.forEach((label) => {
    // استخراج مقدار عددی از label (مثلاً "-0.5m" -> -0.5)
    const value = parseFloat(label);
    if (isNaN(value)) return;
    
    // محاسبه موقعیت Y بر اساس مقدار واقعی
    // اگر yMin و yMax تعریف شده باشند، از آنها استفاده کن
    // در غیر این صورت، از روش قبلی استفاده کن
    let y;
    if (this.yMin !== undefined && this.yMax !== undefined) {
      // تبدیل مقدار Y به موقعیت پیکسل
      // yMin در پایین (height - paddingY) و yMax در بالا (paddingY)
      const yRange = this.yMax - this.yMin;
      if (yRange > 0) {
        const normalizedY = (value - this.yMin) / yRange;
        // محاسبه دقیق موقعیت Y
        y = this.height - paddingY - (normalizedY * canvasHeight);
      } else {
        y = this.height / 2; // اگر range صفر است، در وسط قرار بده
      }
    } else {
      // fallback: استفاده از روش قبلی (فاصله مساوی)
      const index = this.data.indexOf(label);
      const stepY = this.yunit || 43;
      y = this.height - paddingY - stepY * index;
    }
    
    // اطمینان از اینکه y در محدوده canvas است
    if (y < paddingY || y > this.height - paddingY) return;
    
    let labelStr = value.toFixed(1).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
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