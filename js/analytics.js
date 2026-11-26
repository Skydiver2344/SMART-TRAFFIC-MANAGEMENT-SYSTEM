/**
 * Smart Traffic Management System
 * Traffic Analytics Controller
 */

(function () {

    'use strict';


    // ==========================================
    // 1. ANALYTICS DATA
    // ==========================================

    // Demonstration data.
    // Replace this object with backend data later.

    const analyticsData = {

        vehicles: {
            cars: 620,
            bikes: 410,
            buses: 120,
            trucks: 100
        },

        density: {
            low: 45,
            medium: 35,
            high: 20
        },

        hourlyTraffic: [
            35, 45, 60, 85, 120, 180,
            250, 320, 280, 210, 160, 110
        ],

        hourlyLabels: [
            '7 AM', '8 AM', '9 AM', '10 AM',
            '11 AM', '12 PM', '1 PM', '2 PM',
            '3 PM', '4 PM', '5 PM', '6 PM'
        ]

    };


    // ==========================================
    // 2. UPDATE OVERVIEW CARDS
    // ==========================================

    function updateOverview() {

        const cars = analyticsData.vehicles.cars;
        const bikes = analyticsData.vehicles.bikes;
        const buses = analyticsData.vehicles.buses;
        const trucks = analyticsData.vehicles.trucks;

        const total = cars + bikes + buses + trucks;
        const heavy = buses + trucks;

        document.getElementById('total-vehicles').textContent =
            total.toLocaleString();

        document.getElementById('total-cars').textContent =
            cars.toLocaleString();

        document.getElementById('total-bikes').textContent =
            bikes.toLocaleString();

        document.getElementById('total-heavy').textContent =
            heavy.toLocaleString();

        document.getElementById('distribution-total').textContent =
            total.toLocaleString();

        document.getElementById('car-percentage').textContent =
            Math.round((cars / total) * 100) + '%';

        document.getElementById('bike-percentage').textContent =
            Math.round((bikes / total) * 100) + '%';

        document.getElementById('heavy-percentage').textContent =
            Math.round((heavy / total) * 100) + '%';

    }


    // ==========================================
    // 3. VEHICLE DISTRIBUTION DOUGHNUT CHART
    // ==========================================

    function drawDistributionChart() {

        const canvas = document.getElementById(
            'vehicle-distribution-chart'
        );

        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        const values = [
            analyticsData.vehicles.cars,
            analyticsData.vehicles.bikes,
            analyticsData.vehicles.buses +
            analyticsData.vehicles.trucks
        ];

        const colors = [
            '#397fc7',
            '#65b6d8',
            '#e5a33a'
        ];

        const total = values.reduce((sum, value) => sum + value, 0);

        const size = canvas.getBoundingClientRect();

        const dpr = window.devicePixelRatio || 1;

        canvas.width = size.width * dpr;
        canvas.height = size.height * dpr;

        ctx.scale(dpr, dpr);

        const centerX = size.width / 2;
        const centerY = size.height / 2;

        const radius = Math.min(size.width, size.height) * 0.42;
        const lineWidth = 22;

        let startAngle = -Math.PI / 2;

        values.forEach((value, index) => {

            const angle = (value / total) * Math.PI * 2;

            ctx.beginPath();

            ctx.arc(
                centerX,
                centerY,
                radius,
                startAngle,
                startAngle + angle
            );

            ctx.strokeStyle = colors[index];
            ctx.lineWidth = lineWidth;
            ctx.lineCap = 'round';

            ctx.stroke();

            startAngle += angle;

        });

    }


    // ==========================================
    // 4. TRAFFIC FLOW LINE CHART
    // ==========================================

    function drawTrafficFlowChart() {

        const canvas = document.getElementById(
            'traffic-flow-chart'
        );

        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        const values = analyticsData.hourlyTraffic;
        const labels = analyticsData.hourlyLabels;

        const width = canvas.clientWidth;
        const height = canvas.clientHeight;

        const dpr = window.devicePixelRatio || 1;

        canvas.width = width * dpr;
        canvas.height = height * dpr;

        ctx.scale(dpr, dpr);

        const padding = {
            top: 20,
            right: 15,
            bottom: 35,
            left: 38
        };

        const chartWidth =
            width - padding.left - padding.right;

        const chartHeight =
            height - padding.top - padding.bottom;

        const maxValue = Math.ceil(
            Math.max(...values) / 100
        ) * 100;

        // Horizontal grid lines

        ctx.font = '10px Arial';
        ctx.textAlign = 'right';

        for (let i = 0; i <= 4; i++) {

            const y =
                padding.top + (chartHeight / 4) * i;

            const value = maxValue - (maxValue / 4) * i;

            ctx.beginPath();

            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);

            ctx.strokeStyle = '#d5e0ed';
            ctx.lineWidth = 1;

            ctx.stroke();

            ctx.fillStyle = '#899bb2';

            ctx.fillText(
                Math.round(value),
                padding.left - 8,
                y + 3
            );

        }


        // Calculate points

        const points = values.map((value, index) => {

            return {

                x: padding.left +
                    (chartWidth / (values.length - 1)) * index,

                y: padding.top +
                    chartHeight -
                    (value / maxValue) * chartHeight

            };

        });


        // Draw gradient area

        const gradient = ctx.createLinearGradient(
            0,
            padding.top,
            0,
            height
        );

        gradient.addColorStop(
            0,
            'rgba(57, 127, 199, 0.25)'
        );

        gradient.addColorStop(
            1,
            'rgba(57, 127, 199, 0.01)'
        );

        ctx.beginPath();

        ctx.moveTo(points[0].x, points[0].y);

        points.forEach(point => {
            ctx.lineTo(point.x, point.y);
        });

        ctx.lineTo(
            points[points.length - 1].x,
            padding.top + chartHeight
        );

        ctx.lineTo(
            points[0].x,
            padding.top + chartHeight
        );

        ctx.closePath();

        ctx.fillStyle = gradient;
        ctx.fill();


        // Draw traffic line

        ctx.beginPath();

        points.forEach((point, index) => {

            if (index === 0) {
                ctx.moveTo(point.x, point.y);
            } else {
                ctx.lineTo(point.x, point.y);
            }

        });

        ctx.strokeStyle = '#397fc7';
        ctx.lineWidth = 3;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';

        ctx.stroke();


        // Draw points

        points.forEach(point => {

            ctx.beginPath();

            ctx.arc(point.x, point.y, 3.5, 0, Math.PI * 2);

            ctx.fillStyle = '#397fc7';
            ctx.fill();

        });


        // X-axis labels

        ctx.textAlign = 'center';
        ctx.fillStyle = '#899bb2';
        ctx.font = '10px Arial';

        labels.forEach((label, index) => {

            if (index % 2 !== 0) return;

            ctx.fillText(
                label,
                points[index].x,
                height - 10
            );

        });

    }


    // ==========================================
    // 5. TRAFFIC DENSITY
    // ==========================================

    function updateDensity() {

        const density = analyticsData.density;

        document.getElementById('low-density-value').textContent =
            density.low + '%';

        document.getElementById('medium-density-value').textContent =
            density.medium + '%';

        document.getElementById('high-density-value').textContent =
            density.high + '%';

        document.getElementById('low-density-bar').style.width =
            density.low + '%';

        document.getElementById('medium-density-bar').style.width =
            density.medium + '%';

        document.getElementById('high-density-bar').style.width =
            density.high + '%';

    }


    // ==========================================
    // 6. PEAK TRAFFIC HOURS
    // ==========================================

    function updatePeakHour() {

        const values = analyticsData.hourlyTraffic;

        const maxTraffic = Math.max(...values);

        const peakIndex = values.indexOf(maxTraffic);

        document.getElementById('peak-hour').textContent =
            analyticsData.hourlyLabels[peakIndex];

        document.getElementById('peak-vehicles').textContent =
            maxTraffic + ' vehicles detected';

    }


    // ==========================================
    // 7. INITIALIZATION
    // ==========================================

    function initAnalytics() {

        updateOverview();

        drawDistributionChart();

        drawTrafficFlowChart();

        updateDensity();

        updatePeakHour();

    }


    // ==========================================
    // 8. RESPONSIVE CHARTS
    // ==========================================

    let resizeTimer;

    window.addEventListener('resize', function () {

        clearTimeout(resizeTimer);

        resizeTimer = setTimeout(function () {

            drawDistributionChart();

            drawTrafficFlowChart();

        }, 150);

    });


    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initAnalytics
        );

    } else {

        initAnalytics();

    }

})();