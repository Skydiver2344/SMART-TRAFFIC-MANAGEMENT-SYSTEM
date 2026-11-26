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
    // 3. BACKEND TRAFFIC SIGNAL CONTROLLER
    // ==========================================

    const signalElements = {
        L1: document.querySelector('.signal-top-left'),
        L2: document.querySelector('.signal-top-right'),
        L3: document.querySelector('.signal-bottom-left'),
        L4: document.querySelector('.signal-bottom-right')
    };

    const headerSignalLights = document.querySelectorAll(
        '.header-signal .signal-light'
    );

    function setSignalState(signalElement, color) {
        if (!signalElement) return;

        const lights = signalElement.querySelectorAll('.light');

        lights.forEach(light => {
            light.classList.toggle(
                'active',
                light.classList.contains(color.toLowerCase())
            );
        });
    }

    function updateTrafficSignals(signalStates) {
        if (!signalStates) return;

        Object.entries(signalElements).forEach(([lane, element]) => {
            const state = signalStates[lane];

            if (state) {
                setSignalState(element, state);
            }
        });

        if (headerSignalLights.length === 3) {
            const states = Object.values(signalStates);

            let activeIndex = 0;

            if (states.includes('GREEN')) {
                activeIndex = 2;
            } else if (states.includes('YELLOW')) {
                activeIndex = 1;
            }

            headerSignalLights.forEach((light, index) => {
                light.style.opacity = index === activeIndex ? '1' : '0.4';
            });
        }
    }

    // ==========================================
    // 4. FETCH LIVE BACKEND SIGNAL STATES
    // ==========================================

    const STATUS_API = '/api/status';

    async function fetchTrafficSignals() {
        try {
            const response = await fetch(STATUS_API, {
                cache: 'no-store'
            });

            if (!response.ok) {
                throw new Error('Unable to fetch traffic status.');
            }

            const data = await response.json();

            if (data.traffic && data.traffic.signal_states) {
                updateTrafficSignals(data.traffic.signal_states);
            }

        } catch (error) {
            console.warn('Traffic signal update failed:', error.message);
        }
    }

    function initTrafficSignals() {
        const dashboardExists = Object.values(signalElements).some(
            element => element !== null
        );

        if (!dashboardExists) return;

        fetchTrafficSignals();

        setInterval(fetchTrafficSignals, 1000);
    }

    // ==========================================
    // 5. INITIALIZATION
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