// static/js/background_animation.js

console.log("DEBUG JS: Script file loaded.");

document.addEventListener('DOMContentLoaded', () => {
    console.log("DEBUG JS: DOMContentLoaded fired.");

    const canvas = document.getElementById('backgroundCanvas');
    if (!canvas) {
        console.error("DEBUG JS ERROR: Canvas element with ID 'backgroundCanvas' not found!");
        return;
    }
    console.log("DEBUG JS: Canvas element found.");

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error("DEBUG JS ERROR: 2D rendering context not available for canvas!");
        return;
    }
    console.log("DEBUG JS: Canvas context obtained.");

    let circles = [];
    const numCircles = 50;
    const spawnInterval = 100;
    let lastSpawnTime = 0;

    // Устанавливаем размер холста
    function setCanvasSize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        console.log("DEBUG JS: Canvas size set to: " + canvas.width + "x" + canvas.height);
    }

    // Класс для круга
    class Circle {
        constructor() {
            const side = Math.floor(Math.random() * 4);
            if (side === 0) { this.x = Math.random() * canvas.width; this.y = -10; }
            else if (side === 1) { this.x = canvas.width + 10; this.y = Math.random() * canvas.height; }
            else if (side === 2) { this.x = Math.random() * canvas.width; this.y = canvas.height + 10; }
            else { this.x = -10; this.y = Math.random() * canvas.height; }

            this.initialRadius = Math.random() * 10 + 5;
            this.radius = this.initialRadius;
            this.speed = Math.random() * 0.5 + 0.2;
            this.opacity = 1;
            this.lineWidth = Math.random() * 2 + 1;

            this.targetX = canvas.width / 2;
            this.targetY = canvas.height / 2;

            const angle = Math.atan2(this.targetY - this.y, this.targetX - this.x);
            this.dx = Math.cos(angle) * this.speed;
            this.dy = Math.sin(angle) * this.speed;

            // НОВОЕ: Временно сделаем цвет кругов черным для лучшей видимости
            this.strokeColor = 'rgba(0, 0, 0, 0.7)'; // Черный, 70% прозрачность
        }

        // Обновление состояния круга
        update() {
            this.x += this.dx;
            this.y += this.dy;
            this.radius += 0.1;
            this.opacity -= 0.005;

            const distanceToCenter = Math.sqrt(
                (this.x - canvas.width / 2)**2 + (this.y - canvas.height / 2)**2
            );
            const maxDistance = Math.sqrt((canvas.width/2)**2 + (canvas.height/2)**2) * 1.2;

            if (this.opacity <= 0 || distanceToCenter > maxDistance) {
                this.reset();
            }
        }

        // Рисование круга
        draw() {
            ctx.strokeStyle = this.strokeColor; // Используем новый цвет
            ctx.lineWidth = this.lineWidth;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Перезапуск круга
        reset() {
            const side = Math.floor(Math.random() * 4);
            if (side === 0) { this.x = Math.random() * canvas.width; this.y = -this.initialRadius; }
            else if (side === 1) { this.x = canvas.width + this.initialRadius; this.y = Math.random() * canvas.height; }
            else if (side === 2) { this.x = Math.random() * canvas.width; this.y = canvas.height + this.initialRadius; }
            else { this.x = -this.initialRadius; this.y = Math.random() * canvas.height; }

            this.radius = this.initialRadius;
            this.opacity = 1;
            const angle = Math.atan2(canvas.height / 2 - this.y, canvas.width / 2 - this.x);
            this.dx = Math.cos(angle) * this.speed;
            this.dy = Math.sin(angle) * this.speed;
        }
    }

    // Инициализация кругов
    function init() {
        console.log("DEBUG JS: Initializing circles.");
        circles = [];
        for (let i = 0; i < numCircles; i++) {
            circles.push(new Circle());
        }
    }

    // Главный цикл анимации
    function animate(currentTime) {
        if (!lastSpawnTime) lastSpawnTime = currentTime;

        ctx.clearRect(0, 0, canvas.width, canvas.height); // Очищаем холст

        // НОВОЕ: Временно закрашиваем Canvas красным, чтобы убедиться, что он вообще виден
        ctx.fillStyle = 'rgba(255, 0, 0, 0.1)'; // Полупрозрачный красный
        ctx.fillRect(0, 0, canvas.width, canvas.height);


        // Обновляем и рисуем существующие круги
        for (let i = 0; i < circles.length; i++) {
            circles[i].update();
            circles[i].draw();
        }

        requestAnimationFrame(animate);
    }

    // Обработчик изменения размера окна
    window.addEventListener('resize', () => {
        console.log("DEBUG JS: Window resized.");
        setCanvasSize();
        init();
    });

    // Запускаем
    setCanvasSize();
    init();
    animate();
    console.log("DEBUG JS: Animation started.");
});