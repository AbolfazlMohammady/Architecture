export class Structure {
    constructor({ canvasId, structure_type }) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.structure_type = structure_type
        this.position = 0
    }
    update(position) {
        this.position = position
        

    }
    draw() {
        if (this.structure_type === "bridge") {
            this.drawBridge(this.position,this.canvas.height/2)
        }
    }
    drawBridge(x, y, size = 30, color = 'black', direction = 'down') {
        const ctx = this.ctx;

        ctx.fillStyle = color;
        ctx.beginPath();

        switch (direction) {
            case 'up':
                ctx.moveTo(x, y);
                ctx.lineTo(x - size / 2, y - size);
                ctx.lineTo(x + size / 2, y - size);
                break;
            case 'down':
                ctx.moveTo(x, y);
                ctx.lineTo(x - size / 2, y + size);
                ctx.lineTo(x + size / 2, y + size);
                break;
            case 'left':
                ctx.moveTo(x, y);
                ctx.lineTo(x - size, y - size / 2);
                ctx.lineTo(x - size, y + size / 2);
                break;
            case 'right':
                ctx.moveTo(x, y);
                ctx.lineTo(x + size, y - size / 2);
                ctx.lineTo(x + size, y + size / 2);
                break;
            default:
                // حالت پیش‌فرض "up"
                ctx.moveTo(x, y);
                ctx.lineTo(x - size / 2, y - size);
                ctx.lineTo(x + size / 2, y - size);
        }

        ctx.closePath();
        ctx.fill();
    }
}
