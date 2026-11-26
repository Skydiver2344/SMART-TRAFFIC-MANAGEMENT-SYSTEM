/**
 * Smart Traffic Management System
 * Real-Time Traffic Analytics Controller
 */

(function () {

    'use strict';


    // ==========================================
    // 1. CONFIGURATION
    // ==========================================

    const API_URL = '/api/analytics';
    const STATUS_URL = '/api/status';

    const REFRESH_INTERVAL = 1500;

    let analyticsData = null;
    let monitoringStatus = 'stopped';

    let resizeTimer;


    // ==========================================
    // 2. DOM HELPERS
    // ==========================================

    function getElement(id) {
        return document.getElementById(id);
    }

    function setText(id, value) {
        const element = getElement(id);

        if (element) {
            element.textContent = value;
        }
    }


    // ==========================================
    // 3. FETCH BACKEND DATA
    // ==========================================

    async function fetchAnalytics() {

        try {

            const [analyticsResponse, statusResponse] =
                await Promise.all([
                    fetch(API_URL, { cache: 'no-store' }),
                    fetch(STATUS_URL, { cache: 'no-store' })
                ]);

            if (!analyticsResponse.ok || !statusResponse.ok) {
                throw new Error('Unable to fetch analytics data.');
            }

            const analytics = await analyticsResponse.json();
            const status = await statusResponse.json();

            analyticsData = analytics;
            monitoringStatus = status.status;

            updateDashboard();

        } catch (error) {

            console.error('Analytics API error:', error);

            setText(
                'analytics-session-status',
                'Unable to connect to traffic monitoring backend.'
            );

        }

    }


    // ==========================================
    // 4. SESSION STATUS
    // ==========================================

    function updateSessionStatus() {

        const messages = {

            starting: 'Starting traffic monitoring...',

            running: 'Traffic monitoring is active.',

            stopping: 'Stopping traffic monitoring...',

            stopped: 'Monitoring stopped.',

            completed: 'Monitoring session completed.',

            error: 'Traffic monitoring encountered an error.'

        };

        setText(
            'analytics-session-status',
            messages[monitoringStatus] || 'Waiting for monitoring session...'
        );

    }


    // ==========================================
    // 5. VEHICLE DISTRIBUTION
    // ==========================================

    function getVehicleCounts() {

        const distribution =
            analyticsData.vehicle_distribution || {};

        const cars = distribution.cars || 0;
        const bikes = distribution.motorcycles || 0;
        const vans = distribution.vans || 0;
        const buses = distribution.buses || 0;
        const trucks = distribution.trucks || 0;

        return {
            cars,
            bikes,
            heavy: vans + buses + trucks,
            total: cars + bikes + vans + buses + trucks
        };

    }


    // ==========================================
    // 6. UPDATE OVERVIEW CARDS
    // ==========================================

    function updateOverview() {

        const counts = getVehicleCounts();

        setText(
            'total-vehicles',
            counts.total.toLocaleString()
        );

        setText(
            'total-cars',
            counts.cars.toLocaleString()
        );

        setText(
            'total-bikes',
            counts.bikes.toLocaleString()
        );

        setText(
            'total-heavy',
            counts.heavy.toLocaleString()
        );

        setText(
            'distribution-total',
            counts.total.toLocaleString()
        );

        const carPercentage = counts.total
            ? Math.round(counts.cars / counts.total * 100)
            : 0;

        const bikePercentage = counts.total
            ? Math.round(counts.bikes / counts.total * 100)
            : 0;

        const heavyPercentage = counts.total
            ? Math.round(counts.heavy / counts.total * 100)
            : 0;

        setText('car-percentage', carPercentage + '%');
        setText('bike-percentage', bikePercentage + '%');
        setText('heavy-percentage', heavyPercentage + '%');

    }


    // ==========================================
    // 7. VEHICLE DISTRIBUTION CHART
    // ==========================================

    function drawDistributionChart() {

        const canvas = getElement(
            'vehicle-distribution-chart'
        );

        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        const counts = getVehicleCounts();

        const values = [
            counts.cars,
            counts.bikes,
            counts.heavy
        ];

        const colors = [
            '#397fc7',
            '#65b6d8',
            '#e5a33a'
        ];

        const size = canvas.getBoundingClientRect();

        if (size.width <= 0 || size.height <= 0) return;

        const dpr = window.devicePixelRatio || 1;

        canvas.width = size.width * dpr;
        canvas.height = size.height * dpr;

        ctx.scale(dpr, dpr);

        const centerX = size.width / 2;
        const centerY = size.height / 2;

        const radius = Math.min(
            size.width,
            size.height
        ) * 0.42;

        const lineWidth = 22;

        const total = values.reduce(
            (sum, value) => sum + value,
            0
        );

        if (total === 0) {

            ctx.beginPath();

            ctx.arc(
                centerX,
                centerY,
                radius,
                0,
                Math.PI * 2
            );

            ctx.strokeStyle = '#d5e0ed';
            ctx.lineWidth = lineWidth;
            ctx.stroke();

            return;

        }

        let startAngle = -Math.PI / 2;

        values.forEach((value, index) => {

            if (value === 0) return;

            const angle =
                (value / total) * Math.PI * 2;

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
    // 8. TRAFFIC FLOW CHART
    // ==========================================

    function drawTrafficFlowChart() {

        const canvas = getElement(
            'traffic-flow-chart'
        );

        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        const flow = analyticsData.traffic_flow || [];

        const values = flow.map(
            item => Number(item.vehicles) || 0
        );

        const labels = flow.map(
            item => `${item.start_seconds}-${item.end_seconds}s`
        );

        const width = canvas.clientWidth;
        const height = canvas.clientHeight;

        if (width <= 0 || height <= 0) return;

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

        const maxValue = Math.max(
            1,
            Math.ceil(Math.max(0, ...values) / 10) * 10
        );

        // Draw horizontal grid lines.

        ctx.font = '10px Arial';
        ctx.textAlign = 'right';

        for (let i = 0; i <= 4; i++) {

            const y =
                padding.top + (chartHeight / 4) * i;

            const value =
                maxValue - (maxValue / 4) * i;

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


        // No traffic data.

        if (values.length === 0) {

            ctx.fillStyle = '#899bb2';
            ctx.textAlign = 'center';
            ctx.font = '12px Arial';

            ctx.fillText(
                'No traffic data yet',
                width / 2,
                height / 2
            );

            return;

        }


        // Calculate chart points.

        const points = values.map((value, index) => {

            const x = values.length === 1
                ? padding.left + chartWidth / 2
                : padding.left +
                  (chartWidth / (values.length - 1)) * index;

            const y =
                padding.top +
                chartHeight -
                (value / maxValue) * chartHeight;

            return { x, y };

        });


        // Draw gradient area.

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


        // Draw traffic line.

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


        // Draw data points.

        points.forEach(point => {

            ctx.beginPath();

            ctx.arc(
                point.x,
                point.y,
                3.5,
                0,
                Math.PI * 2
            );

            ctx.fillStyle = '#397fc7';
            ctx.fill();

        });


        // Draw X-axis labels.

        ctx.textAlign = 'center';
        ctx.fillStyle = '#899bb2';
        ctx.font = '10px Arial';

        labels.forEach((label, index) => {

            if (values.length > 8 && index % 2 !== 0) {
                return;
            }

            ctx.fillText(
                label,
                points[index].x,
                height - 10
            );

        });

    }


    // ==========================================
    // 9. TRAFFIC DENSITY
    // ==========================================

    function updateDensity() {

        const density = analyticsData.density || {};

        const low = Number(density.low) || 0;
        const medium = Number(density.medium) || 0;
        const high = Number(density.high) || 0;

        setText('low-density-value', low + '%');
        setText('medium-density-value', medium + '%');
        setText('high-density-value', high + '%');

        getElement('low-density-bar').style.width =
            low + '%';

        getElement('medium-density-bar').style.width =
            medium + '%';

        getElement('high-density-bar').style.width =
            high + '%';

    }


    // ==========================================
    // 10. PEAK TRAFFIC
    // ==========================================

    function updatePeakTraffic() {

        const peak = analyticsData.peak_traffic || {};

        if (peak.interval === null || peak.interval === undefined) {

            setText('peak-hour', 'No data');

            setText(
                'peak-vehicles',
                '0 vehicles detected'
            );

            return;

        }

        setText(
            'peak-hour',
            `${peak.start_seconds}-${peak.end_seconds} seconds`
        );

        setText(
            'peak-vehicles',
            `${peak.vehicles} vehicles detected`
        );

    }


    // ==========================================
    // 11. UPDATE DASHBOARD
    // ==========================================

    function updateDashboard() {

        if (!analyticsData) return;

        updateSessionStatus();

        updateOverview();

        drawDistributionChart();

        drawTrafficFlowChart();

        updateDensity();

        updatePeakTraffic();

    }


    // ==========================================
    // 12. RESPONSIVE CHARTS
    // ==========================================

    window.addEventListener('resize', function () {

        clearTimeout(resizeTimer);

        resizeTimer = setTimeout(function () {

            if (!analyticsData) return;

            drawDistributionChart();

            drawTrafficFlowChart();

        }, 150);

    });


    // ==========================================
    // 13. INITIALIZATION
    // ==========================================

    async function initAnalytics() {

        await fetchAnalytics();

        setInterval(
            fetchAnalytics,
            REFRESH_INTERVAL
        );

    }


    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initAnalytics
        );

    } else {

        initAnalytics();

    }

})();