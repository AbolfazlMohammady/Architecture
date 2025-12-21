export class YAxisCanvas {
  constructor({canvasId, height, width, margin,yunit}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.height = height;
    this.width = width;
    this.margin = margin;
    this.yunit = yunit;

    // تنظیم canvas با در نظر گیری devicePixelRatio برای کیفیت بالا (حداقل 2)
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    
    // تنظیم scale برای context
    this.ctx.scale(dpr, dpr);
    
    // بهبود کیفیت رندرینگ - حرفه‌ای
    this.ctx.imageSmoothingEnabled = true;
    this.ctx.imageSmoothingQuality = 'high';

    this.data = [];
  }

  update(data, min, max) {
    this.data = data;
    this.min = min;
    this.max = max;
    this.draw();
  }
  
  resize(width, height) {
    this.width = width;
    this.height = height;
    
    // تنظیم canvas با در نظر گیری devicePixelRatio برای کیفیت بالا (حداقل 2)
    const dpr = Math.max(window.devicePixelRatio || 1, 2);
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    
    // تنظیم scale برای context
    this.ctx.scale(dpr, dpr);
    
    // بهبود کیفیت رندرینگ - حرفه‌ای
    this.ctx.imageSmoothingEnabled = true;
    this.ctx.imageSmoothingQuality = 'high';
    
    // رسم مجدد اگر داده‌ها وجود دارند
    if (this.data && this.data.length > 0) {
      this.draw();
    }
  }
  
  getYPosition(value) {
    const margin = this.margin;
    const mainCanvasHeight = this.height - margin * 2 - 30;
    const min = parseFloat(this.min);
    const max = parseFloat(this.max);

    if (!isFinite(min) || !isFinite(max) || max <= min) {
      return margin + mainCanvasHeight / 2;
    }
    if (mainCanvasHeight <= 0) {
      return margin;
    }

    const normalized = (value - min) / (max - min);
    const y = margin + mainCanvasHeight - normalized * mainCanvasHeight;
    return y;
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

  ctx.strokeStyle = '#666';
  ctx.lineWidth = 1.5;

  const paddingTop = this.margin;
  const paddingBottom = this.margin + 30; // فضای محور X در پایین
  const usableHeight = this.height - paddingTop - paddingBottom;
  const labelOffset = 0;

  // خط عمودی ثابت سمت راست y-axis که فقط در محدوده نمودار اصلی رسم می‌شود
  ctx.beginPath();
  ctx.moveTo(this.width - 1 - this.margin, paddingTop);
  ctx.lineTo(this.width - 1 - this.margin, paddingTop + usableHeight);
  ctx.stroke();

  ctx.fillStyle = '#222';
  ctx.font = 'bold 14px Vazirmatn, Tahoma, Arial, sans-serif';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'right';

  // محاسبه موقعیت Y هر لیبل بر اساس مقدار واقعی آن
  // yMin در پایین (نزدیک محور X) و yMax در بالا است
  this.data.forEach((label) => {
    // استخراج مقدار عددی از label (مثلاً "-0.5" -> -0.5)
    const value = parseFloat(label);
    if (isNaN(value)) return;
    
    // محاسبه موقعیت Y بر اساس مقدار واقعی
    // اگر yMin و yMax تعریف شده باشند، از آنها استفاده کن
    let y;
    if (this.min !== undefined && this.max !== undefined) {
      const rawY = this.getYPosition(value);
      y = Math.round(rawY) + 0.5;
    } else {
      // fallback: استفاده از روش قبلی (فاصله مساوی)
      const index = this.data.indexOf(label);
      const stepY = this.yunit || 43;
      const rawY = paddingTop + usableHeight - stepY * index;
      y = Math.round(rawY) + 0.5;
    }
    
    // اطمینان از اینکه y در محدوده canvas است (با حاشیه بیشتر)
    if (y < paddingTop - 5 || y > paddingTop + usableHeight + 5) return;
    
    // تبدیل به فارسی و نمایش با فرمت بهتر
    let labelStr = value.toFixed(1).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
    // اگر مقدار منفی است، علامت منفی را اضافه کن
    if (value < 0) {
        labelStr = '−' + labelStr.replace('-', ''); // استفاده از علامت منفی فارسی
    }
    ctx.fillStyle = '#111827';
    ctx.fillText(this.fittext(labelStr), this.width - 12, y + labelOffset);
    // خط تیک محور Y - بهبود کیفیت
    ctx.beginPath();
    ctx.moveTo(this.width - 10 - this.margin, y);
    ctx.lineTo(this.width - 1 - this.margin, y);
    ctx.stroke();
  });

  // برچسب اصلی محور Y (ارتفاع)
  // حذف عنوان محور Y
  }
 }