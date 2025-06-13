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

  ctx.strokeStyle = 'black';
  ctx.lineWidth = 1;

  // خط عمودی ثابت سمت راست y-axis
  ctx.beginPath();
  ctx.moveTo(this.width - 1 - this.margin, 0);
  ctx.lineTo(this.width - 1 - this.margin, this.height);
  ctx.stroke();

  ctx.fillStyle = 'black';
  ctx.font = '12px monospace';
  ctx.textBaseline = 'middle';

//   const stepY = this.height / (this.data.length - 1 || 1);

  const paddingY = 10; // فاصله عمودی دلخواه بالا و پایین
const stepY = this.yunit;

this.data.forEach((label, index) => {
  const y = this.height - paddingY - stepY * index;

  ctx.fillText(this.fittext(label.toString()), this.margin, y);

  ctx.beginPath();
  ctx.moveTo(this.width - 10 - this.margin, y);
  ctx.lineTo(this.width - 1 - this.margin, y);
  ctx.stroke();
});

}
 }