/**
 * Smart Traffic Management System
 * Backend Video Monitoring Controller
 */

(function () {
    'use strict';

    const startButton = document.getElementById('start-monitoring-btn');
    const stopButton = document.getElementById('stop-monitoring-btn');
    const instruction = document.getElementById('monitoring-instruction');
    const stream = document.getElementById('backend-stream');

    const monitoringIndicator = document.querySelector(
        '.monitoring-status .status-indicator'
    );

    const monitoringText = document.querySelector(
        '.monitoring-status span:last-child'
    );

    const START_API = '/api/start-monitoring';
    const STOP_API = '/api/stop-monitoring';
    const STATUS_API = '/api/status';
    const VIDEO_API = '/api/video-feed';

    let statusTimer = null;
    let monitoring = false;
    let requestInProgress = false;

    if (!startButton || !stopButton || !instruction || !stream) {
        console.error('Monitoring elements not found.');
        return;
    }

    function setMonitoringStatus(isActive) {
        const container = document.querySelector('.monitoring-status');

        if (container) {
            container.classList.toggle('monitoring-inactive', !isActive);
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

    function stopStatusPolling() {
        if (statusTimer !== null) {
            clearInterval(statusTimer);
            statusTimer = null;
        }
    }

    function showActiveMonitoring(message = 'Vehicle detection is running...') {
        monitoring = true;

        startButton.hidden = true;
        startButton.disabled = false;

        stopButton.hidden = false;
        stopButton.disabled = false;

        stream.hidden = false;

        stream.src = VIDEO_API + '?session=' + Date.now();

        setMonitoringStatus(true);
        instruction.textContent = message;

        startStatusPolling();
    }

    function resetMonitoring(message = 'Click to start monitoring') {
        monitoring = false;

        stopStatusPolling();

        stream.removeAttribute('src');
        stream.hidden = true;

        startButton.hidden = false;
        startButton.disabled = false;

        stopButton.hidden = true;
        stopButton.disabled = false;

        setMonitoringStatus(false);

        instruction.textContent = message;
    }

    function startStatusPolling() {
        stopStatusPolling();

        statusTimer = setInterval(checkBackendStatus, 1000);
    }

    async function checkBackendStatus() {
        try {
            const response = await fetch(STATUS_API, {
                cache: 'no-store'
            });

            if (!response.ok) {
                throw new Error('Unable to fetch backend status.');
            }

            const data = await response.json();

            switch (data.status) {
                case 'starting':
                    monitoring = true;
                    setMonitoringStatus(true);
                    instruction.textContent = 'Initializing traffic detection...';
                    break;

                case 'running':
                    monitoring = true;
                    setMonitoringStatus(true);
                    instruction.textContent = 'Vehicle detection is running...';
                    break;

                case 'stopping':
                    monitoring = true;
                    instruction.textContent = 'Stopping monitoring...';
                    break;

                case 'completed':
                    resetMonitoring('Video processing completed.');
                    break;

                case 'stopped':
                    resetMonitoring();
                    break;

                case 'error':
                    console.error('Backend error:', data.error);

                    resetMonitoring(
                        'Monitoring failed: ' +
                        (data.error || 'Unknown error')
                    );
                    break;
            }

        } catch (error) {
            console.error('Status check failed:', error);
        }
    }

    async function synchronizeWithBackend() {
        try {
            const response = await fetch(STATUS_API, {
                cache: 'no-store'
            });

            if (!response.ok) {
                throw new Error('Unable to connect to backend.');
            }

            const data = await response.json();

            if (
                data.status === 'starting' ||
                data.status === 'running' ||
                data.status === 'stopping'
            ) {
                showActiveMonitoring(
                    data.status === 'starting'
                        ? 'Initializing traffic detection...'
                        : data.status === 'stopping'
                            ? 'Stopping monitoring...'
                            : 'Vehicle detection is running...'
                );

                if (data.status === 'stopping') {
                    stopButton.disabled = true;
                }
            } else if (data.status === 'completed') {
                resetMonitoring('Video processing completed.');
            } else if (data.status === 'error') {
                resetMonitoring(
                    'Monitoring failed: ' +
                    (data.error || 'Unknown error')
                );
            } else {
                resetMonitoring();
            }

        } catch (error) {
            console.error('Backend synchronization failed:', error);
            resetMonitoring('Unable to connect to monitoring backend.');
        }
    }

    async function startMonitoring() {
        if (monitoring || requestInProgress) return;

        requestInProgress = true;

        startButton.disabled = true;
        instruction.textContent = 'Starting vehicle detection...';

        try {
            const response = await fetch(START_API, {
                method: 'POST'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || 'Unable to start monitoring.'
                );
            }

            showActiveMonitoring('Loading traffic video...');

        } catch (error) {
            console.error('Monitoring error:', error);

            await synchronizeWithBackend();

            if (!monitoring) {
                instruction.textContent =
                    'Unable to start monitoring: ' + error.message;
            }

        } finally {
            requestInProgress = false;
        }
    }

    async function stopMonitoring() {
        if (requestInProgress) return;

        requestInProgress = true;

        stopButton.disabled = true;
        instruction.textContent = 'Stopping monitoring...';

        try {
            const response = await fetch(STOP_API, {
                method: 'POST'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || 'Unable to stop monitoring.'
                );
            }

            if (data.status === 'completed') {
                resetMonitoring('Video processing completed.');
            } else {
                resetMonitoring();
            }

        } catch (error) {
            console.error('Stop error:', error);

            stopButton.disabled = false;

            instruction.textContent =
                'Unable to stop monitoring. Please try again.';

        } finally {
            requestInProgress = false;
        }
    }

    startButton.addEventListener('click', startMonitoring);
    stopButton.addEventListener('click', stopMonitoring);

    // Synchronize frontend with backend whenever dashboard loads.
    synchronizeWithBackend();

})();