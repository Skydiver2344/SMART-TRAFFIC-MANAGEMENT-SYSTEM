/**
 * Smart Traffic Management System
 * Main Dashboard Controller
 */

(function () {
    'use strict';

    // ==========================================
    // 1. REAL-TIME DATE AND TIME
    // ==========================================

    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');

    function updateDateTime() {
        const now = new Date();

        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString('en-US', {
                month: 'short',
                day: '2-digit',
                year: 'numeric'
            });
        }

        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });
        }
    }

    // ==========================================
    // 2. MOBILE SIDEBAR NAVIGATION
    // ==========================================

    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');

    function initSidebar() {

        if (!menuToggle || !sidebar) return;

        menuToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            sidebar.classList.toggle('sidebar-open');
        });

        document.addEventListener('click', function (e) {

            if (
                sidebar.classList.contains('sidebar-open') &&
                !sidebar.contains(e.target) &&
                !menuToggle.contains(e.target)
            ) {
                sidebar.classList.remove('sidebar-open');
            }

        });

        const navItems = document.querySelectorAll(
            '.sidebar-navigation .nav-item'
        );

        navItems.forEach(item => {

            item.addEventListener('click', function () {

                navItems.forEach(nav => nav.classList.remove('active'));

                this.classList.add('active');

                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('sidebar-open');
                }

            });

        });

    }

    // ==========================================
    // 3. TRAFFIC SIGNAL CONTROLLER
    // ==========================================

    const signalTopLeft = document.querySelector('.signal-top-left');
    const signalTopRight = document.querySelector('.signal-top-right');
    const signalBottomLeft = document.querySelector('.signal-bottom-left');
    const signalBottomRight = document.querySelector('.signal-bottom-right');

    const headerSignalLights = document.querySelectorAll(
        '.header-signal .signal-light'
    );

    function setSignalState(signalElement, color) {

        if (!signalElement) return;

        const lights = signalElement.querySelectorAll('.light');

        lights.forEach(light => {

            if (light.classList.contains(color)) {
                light.classList.add('active');
            } else {
                light.classList.remove('active');
            }

        });

    }

    // Traffic signal phases

    const phases = [
        { ns: 'green', ew: 'red', duration: 6000 },
        { ns: 'yellow', ew: 'red', duration: 2000 },
        { ns: 'red', ew: 'green', duration: 6000 },
        { ns: 'red', ew: 'yellow', duration: 2000 }
    ];

    let currentPhaseIndex = 0;

    function applyTrafficPhase() {

        const currentPhase = phases[currentPhaseIndex];

        // North-South direction

        setSignalState(signalTopLeft, currentPhase.ns);
        setSignalState(signalBottomRight, currentPhase.ns);

        // East-West direction

        setSignalState(signalTopRight, currentPhase.ew);
        setSignalState(signalBottomLeft, currentPhase.ew);

        currentPhaseIndex = (currentPhaseIndex + 1) % phases.length;

        setTimeout(applyTrafficPhase, currentPhase.duration);

    }

    function initTrafficSignals() {

        if (
            signalTopLeft &&
            signalTopRight &&
            signalBottomLeft &&
            signalBottomRight
        ) {
            applyTrafficPhase();
        }

        // Header signal indicator

        if (headerSignalLights.length === 3) {

            headerSignalLights.forEach((light, index) => {
                light.style.opacity = index === 2 ? '1' : '0.4';
            });

        }

    }

    // ==========================================
    // 4. INITIALIZATION
    // ==========================================

    function init() {

        updateDateTime();

        setInterval(updateDateTime, 1000);

        initSidebar();

        initTrafficSignals();

    }

    if (document.readyState === 'loading') {

        document.addEventListener('DOMContentLoaded', init);

    } else {

        init();

    }

})();