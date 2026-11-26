/**
 * Smart Traffic Management System
 * Backend Video Monitoring Controller
 */

(function () {
    'use strict';

    const startButton = document.getElementById('start-monitoring-btn');
    const stopButton = document.getElementById('stop-monitoring-btn');
    const instruction = document.getElementById('monitoring-instruction');
    const video = document.getElementById('backend-video');

    const monitoringIndicator = document.querySelector(
        '.monitoring-status .status-indicator'
    );

    const monitoringText = document.querySelector(
        '.monitoring-status span:last-child'
    );

    const START_API = '/api/start-monitoring';
    const STOP_API = '/api/stop-monitoring';
    const VIDEO_API = '/api/video-feed';

    if (!startButton || !stopButton || !instruction || !video) return;

    function setMonitoringStatus(isActive) {
        const statusContainer = document.querySelector('.monitoring-status');

        if (statusContainer) {
            statusContainer.classList.toggle(
                'monitoring-inactive',
                !isActive
            );
        }

        if (monitoringIndicator) {
            monitoringIndicator.classList.toggle('inactive', !isActive);
        }

        if (monitoringText) {
            monitoringText.textContent = isActive
                ? 'Live Monitoring'
                : 'Monitoring Stopped';
        }
    }

    function resetMonitoring() {
        video.pause();
        video.removeAttribute('src');
        video.load();

        video.hidden = true;
        startButton.hidden = false;
        stopButton.hidden = true;

        setMonitoringStatus(false);

        instruction.textContent = 'Click to start monitoring';
    }

    async function startMonitoring() {
        startButton.hidden = true;
        instruction.textContent = 'Starting vehicle detection...';

        try {
            const response = await fetch(START_API, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Unable to start monitoring.');
            }

            setMonitoringStatus(true);

            stopButton.hidden = false;

            video.src = VIDEO_API;
            video.hidden = false;

            instruction.textContent = 'Vehicle detection is running...';

            await video.play();

        } catch (error) {
            console.error('Monitoring error:', error);

            resetMonitoring();

            instruction.textContent =
                'Unable to connect to the backend. Please try again.';
        }
    }

    async function stopMonitoring() {
        stopButton.disabled = true;
        instruction.textContent = 'Stopping monitoring...';

        try {
            await fetch(STOP_API, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error stopping backend:', error);
        }

        resetMonitoring();
        stopButton.disabled = false;
    }

    startButton.addEventListener('click', startMonitoring);
    stopButton.addEventListener('click', stopMonitoring);

    video.addEventListener('ended', resetMonitoring);
    video.addEventListener('error', resetMonitoring);

    setMonitoringStatus(false);

})();