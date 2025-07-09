export class LandLine {
    constructor({ canvasId, width = 1100, height = 450, start_kilometer,end_kilometer }) {
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
        this.fillClosedArea(); // بعد از رسم خط زمین، فضاهای بسته رو رنگ می‌کنیم
    }

    draw() {
        if (this.points.length < 2) return;

        const ctx = this.ctx;
        ctx.strokeStyle = 'gray';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';


        
        ctx.beginPath();
        // ctx.moveTo(0,this.canvas.height/2)
        // ctx.lineTo(this.canvas.width,this.canvas.height/2)
        let x = this.kmToX(this.points[0].x);

        let y = this.heightToY(this.points[0].y) 
        
        console.log(x,y)
        // // ctx.moveTo(x, this.points[0].y);
        ctx.moveTo(x, y);

        for (let i = 1; i < this.points.length; i++) {
            const ptx = this.kmToX(this.points[i].x, this.start_kilometer, this.end_kilometer, this.canvas.width);
            const pty = this.heightToY(this.points[i].y);
            
            ctx.lineTo(ptx, pty);
        }
        ctx.stroke();
        ctx.setLineDash([]);
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


    fillClosedArea() {
        const ctx = this.ctx;
        const roadY = this.height / 2;
        const linkeddot = [];

        for (let index = 0; index < this.points.length - 1; index++) {
            const start = this.points[index];
            const end = this.points[index + 1];

            const intersection = new LineIntersectionDetector({
                line1: { x1: start.x, y1: start.y, x2: end.x, y2: end.y },
                line2: { x3: 0, y3: roadY, x4: this.width, y4: roadY }
            }).checkIntersection();

            if (intersection) {
                linkeddot.push(intersection);
                if (linkeddot.length === 1) {
                    linkeddot.push(end);
                } else {


                    const pattern = ctx.createPattern(createHatchPattern(90, 'gray', 8), 'repeat');

                    ctx.fillStyle = pattern;

                    // this.ctx.fillStyle = pattern;
                    ctx.beginPath();
                    ctx.moveTo(linkeddot[0].x, linkeddot[0].y);

                    for (let pt of linkeddot.slice(1)) {
                        ctx.lineTo(pt.x, pt.y);
                    }

                    ctx.closePath();

                    ctx.fill();
                    // ctx.fillRect(50, 50, 200, 100); // رسم مستطیل با حاشور زاویه‌دار

                    // ctx.strokeStyle = 'rgba(0, 150, 255, 0.6)';
                    // ctx.stroke();
                    var temp = linkeddot[linkeddot.length - 1]
                    linkeddot.length = 0
                    linkeddot.push(temp)
                    linkeddot.push(end);
                }

            } else if (linkeddot.length > 1) {
                linkeddot.push(end)
            }


        }
    }
}


function createHatchPattern(angle = 45, color = 'black', spacing = 10) {
    const size = spacing * 4; // بزرگتر برای جلوگیری از تداخل
    const patternCanvas = document.createElement('canvas');
    patternCanvas.width = size;
    patternCanvas.height = size;

    const pctx = patternCanvas.getContext('2d');
    pctx.clearRect(0, 0, size, size);

    pctx.strokeStyle = color;
    pctx.lineWidth = 1;

    // چرخش حول مرکز
    pctx.translate(size / 2, size / 2);
    pctx.rotate((angle * Math.PI) / 180);
    pctx.translate(-size / 2, -size / 2);

    // رسم خطوط مورب با فاصله منظم
    for (let i = -size; i < size * 2; i += spacing) {
        pctx.beginPath();
        pctx.moveTo(i, 0);
        pctx.lineTo(i - size, size);
        pctx.stroke();
    }

    return patternCanvas;
}




class LineIntersectionDetector {
    constructor({ line1, line2 }) {
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
