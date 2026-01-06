/**
 * EMR Cost Optimizer - Frontend Application
 */

// Global state
let clustersData = null;
let analysisModal = null;
let totalPotentialSavings = 0;
let lookbackOptions = [];
let defaultLookbackHours = 72;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    analysisModal = new bootstrap.Modal(document.getElementById('analysisModal'));

    // Load lookback options
    await loadLookbackOptions();

    // Load clusters
    refreshClusters();
});

/**
 * Load lookback period options from API
 */
async function loadLookbackOptions() {
    try {
        const response = await fetch('/api/config/lookback-options');
        const result = await response.json();
        if (result.success) {
            lookbackOptions = result.data.options;
            defaultLookbackHours = result.data.default_hours;
        }
    } catch (error) {
        console.error('Failed to load lookback options:', error);
        // Use defaults
        lookbackOptions = [
            { label: 'Last 1 hour', hours: 1 },
            { label: 'Last 3 hours', hours: 3 },
            { label: 'Last 6 hours', hours: 6 },
            { label: 'Last 12 hours', hours: 12 },
            { label: 'Last 24 hours', hours: 24 },
            { label: 'Last 3 days', hours: 72 },
            { label: 'Last 7 days', hours: 168 },
        ];
        defaultLookbackHours = 72;
    }
}

/**
 * Refresh clusters list
 */
async function refreshClusters() {
    showLoading();
    hideError();

    try {
        const response = await fetch('/api/clusters');
        const result = await response.json();

        if (result.success) {
            clustersData = result.data;
            renderClusters();
            updateSummary();
        } else {
            showError(result.error || 'Failed to load clusters');
        }
    } catch (error) {
        showError('Failed to connect to server: ' + error.message);
    }
}

/**
 * Render clusters in their respective sections
 */
function renderClusters() {
    const transientList = document.getElementById('transient-clusters-list');
    const longRunningList = document.getElementById('long-running-clusters-list');
    const terminatedList = document.getElementById('terminated-clusters-list');

    // Render transient clusters
    if (clustersData.transient.length > 0) {
        transientList.innerHTML = clustersData.transient.map(cluster => createClusterCard(cluster)).join('');
    } else {
        transientList.innerHTML = createEmptyState('No transient clusters running');
    }

    // Render long-running clusters
    if (clustersData.long_running.length > 0) {
        longRunningList.innerHTML = clustersData.long_running.map(cluster => createClusterCard(cluster)).join('');
    } else {
        longRunningList.innerHTML = createEmptyState('No long running clusters');
    }

    // Render terminated clusters
    if (clustersData.terminated && clustersData.terminated.length > 0) {
        terminatedList.innerHTML = clustersData.terminated.map(cluster => createClusterCard(cluster, true)).join('');
    } else {
        terminatedList.innerHTML = createEmptyState('No recently terminated clusters');
    }

    // Update badges
    document.getElementById('transient-badge').textContent = clustersData.transient_count;
    document.getElementById('long-running-badge').textContent = clustersData.long_running_count;
    document.getElementById('terminated-badge').textContent = clustersData.terminated_count || 0;

    // Show container
    document.getElementById('loading-state').classList.add('d-none');
    document.getElementById('clusters-container').classList.remove('d-none');
}

/**
 * Create cluster card HTML
 */
function createClusterCard(cluster, isTerminated = false) {
    const instanceGroups = cluster.instance_groups
        .filter(g => g.type !== 'MASTER')
        .map(g => {
            // Handle instance fleets with multiple instance types
            if (g.is_fleet && g.instance_type_counts && Object.keys(g.instance_type_counts).length > 0) {
                const typeBreakdown = Object.entries(g.instance_type_counts)
                    .map(([type, count]) => `${count}x ${type}`)
                    .join(', ');
                return `
                    <span class="instance-group-tag ${g.type.toLowerCase()}">
                        ${g.type}: ${typeBreakdown}
                        <i class="bi bi-layers ms-1" title="Instance Fleet"></i>
                    </span>
                `;
            }
            // For terminated clusters, use requested_count if running_count is 0
            const instanceCount = g.running_count || g.requested_count || 0;
            return `
                <span class="instance-group-tag ${g.type.toLowerCase()}">
                    ${g.type}: ${instanceCount}x ${g.instance_type}
                </span>
            `;
        }).join('');

    const runtimeFormatted = formatRuntime(cluster.runtime_hours);
    const statusClass = cluster.state.toLowerCase().replace('_', '-');
    const fleetBadge = cluster.uses_fleets ? '<span class="badge bg-secondary ms-2">Fleet</span>' : '';

    // For terminated clusters, show termination info
    let terminationInfo = '';
    if (isTerminated && cluster.termination_reason) {
        const reasonCode = cluster.termination_reason.code || 'UNKNOWN';
        const reasonBadgeClass = reasonCode === 'ALL_STEPS_COMPLETED' ? 'bg-success' :
                                 reasonCode === 'USER_REQUEST' ? 'bg-info' : 'bg-warning';
        terminationInfo = `
            <div class="mt-2 small">
                <span class="badge ${reasonBadgeClass}">${reasonCode.replace(/_/g, ' ')}</span>
                ${cluster.end_time ? `<span class="text-muted ms-2">Ended: ${formatDateTime(cluster.end_time)}</span>` : ''}
            </div>
        `;
    }

    // Generate lookback options dropdown
    const lookbackOptionsHtml = lookbackOptions.map(opt =>
        `<option value="${opt.hours}" ${opt.hours === defaultLookbackHours ? 'selected' : ''}>${opt.label}</option>`
    ).join('');

    // For terminated clusters, suggest analyzing the full runtime or last 3 hours
    const defaultLookback = isTerminated ? Math.min(cluster.runtime_hours, 72) : defaultLookbackHours;
    const lookbackOptionsHtmlForCluster = lookbackOptions.map(opt => {
        const selected = isTerminated
            ? (opt.hours <= cluster.runtime_hours && opt.hours === Math.max(...lookbackOptions.filter(o => o.hours <= cluster.runtime_hours).map(o => o.hours)))
            : (opt.hours === defaultLookbackHours);
        return `<option value="${opt.hours}" ${selected ? 'selected' : ''}>${opt.label}</option>`;
    }).join('');

    return `
        <div class="cluster-item ${isTerminated ? 'terminated' : ''}" data-cluster-id="${cluster.id}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2">
                        <span class="cluster-name">${escapeHtml(cluster.name)}</span>
                        <span class="status-badge ${statusClass}">${cluster.state.replace('_', ' ')}</span>
                        ${fleetBadge}
                        ${cluster.cluster_type ? `<span class="badge bg-light text-dark">${cluster.cluster_type}</span>` : ''}
                    </div>
                    <div class="cluster-id">${cluster.id}</div>
                    <div class="cluster-meta">
                        <span class="cluster-meta-item">
                            <i class="bi bi-clock"></i>
                            ${runtimeFormatted}${isTerminated ? ' (total)' : ''}
                        </span>
                        <span class="cluster-meta-item">
                            <i class="bi bi-tag"></i>
                            ${cluster.release_label}
                        </span>
                        <span class="cluster-meta-item">
                            <i class="bi bi-app"></i>
                            ${cluster.applications.join(', ') || 'N/A'}
                        </span>
                    </div>
                    ${terminationInfo}
                    <div class="mt-2">
                        ${instanceGroups}
                    </div>
                </div>
                <div class="cluster-actions d-flex flex-column gap-2 align-items-end">
                    <div class="d-flex align-items-center gap-2">
                        <select class="form-select form-select-sm lookback-select" id="lookback-${cluster.id}" style="width: auto;">
                            ${lookbackOptionsHtmlForCluster}
                        </select>
                        <button class="btn ${isTerminated ? 'btn-outline-primary' : 'btn-primary'} btn-analyze" onclick="analyzeCluster('${cluster.id}')">
                            <i class="bi bi-graph-up me-1"></i>
                            Analyze
                        </button>
                    </div>
                    <small class="text-muted">${isTerminated ? 'Historical analysis' : 'Analysis period'}</small>
                </div>
            </div>
        </div>
    `;
}

/**
 * Format datetime for display
 */
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

/**
 * Analyze a cluster
 */
async function analyzeCluster(clusterId) {
    const button = document.querySelector(`[data-cluster-id="${clusterId}"] .btn-analyze`);
    const originalContent = button.innerHTML;

    // Get selected lookback hours
    const lookbackSelect = document.getElementById(`lookback-${clusterId}`);
    const lookbackHours = lookbackSelect ? parseInt(lookbackSelect.value) : defaultLookbackHours;

    // Update button state
    button.classList.add('analyzing');
    button.innerHTML = '<span class="analysis-spinner me-1"></span>Analyzing...';

    // Show modal with loading state
    showAnalysisLoading(clusterId, lookbackHours);
    analysisModal.show();

    try {
        const response = await fetch(`/api/clusters/${clusterId}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ lookback_hours: lookbackHours })
        });
        const result = await response.json();

        if (result.success) {
            renderAnalysisResults(result.data);
            updatePotentialSavings(result.data);
        } else {
            showAnalysisError(result.error || 'Analysis failed');
        }
    } catch (error) {
        showAnalysisError('Failed to analyze cluster: ' + error.message);
    } finally {
        // Reset button
        button.classList.remove('analyzing');
        button.innerHTML = originalContent;
    }
}

/**
 * Show analysis loading state in modal
 */
function showAnalysisLoading(clusterId, lookbackHours) {
    const cluster = findCluster(clusterId);
    const lookbackLabel = lookbackOptions.find(o => o.hours === lookbackHours)?.label || `Last ${lookbackHours} hours`;

    document.getElementById('analysisModalLabel').innerHTML = `
        <i class="bi bi-graph-up me-2"></i>
        Analyzing: ${cluster ? escapeHtml(cluster.name) : clusterId}
    `;

    document.getElementById('analysis-content').innerHTML = `
        <div class="analysis-loading">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Fetching CloudWatch metrics for <strong>${lookbackLabel}</strong>...</p>
            <p class="small text-muted">This may take a moment for clusters with many nodes.</p>
        </div>
    `;
}

/**
 * Render analysis results in modal
 */
function renderAnalysisResults(analysis) {
    document.getElementById('analysisModalLabel').innerHTML = `
        <i class="bi bi-graph-up me-2"></i>
        Analysis: ${escapeHtml(analysis.cluster_name)}
    `;

    const nodeTypes = Object.keys(analysis.node_analyses);
    let html = '';

    // Summary section
    html += `
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="analysis-section">
                    <div class="analysis-section-title">
                        <i class="bi bi-info-circle"></i>
                        Cluster Information
                    </div>
                    <table class="specs-table w-100">
                        <tr>
                            <td class="text-muted">Cluster ID</td>
                            <td class="text-end"><code>${analysis.cluster_id}</code></td>
                        </tr>
                        <tr>
                            <td class="text-muted">Type</td>
                            <td class="text-end">
                                <span class="badge ${analysis.cluster_type === 'TRANSIENT' ? 'bg-info' : 'bg-success'}">
                                    ${analysis.cluster_type}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td class="text-muted">Runtime</td>
                            <td class="text-end">${formatRuntime(analysis.runtime_hours)}</td>
                        </tr>
                        <tr>
                            <td class="text-muted">Analysis Period</td>
                            <td class="text-end">${formatAnalysisPeriod(analysis.analysis_period)}</td>
                        </tr>
                    </table>
                </div>
            </div>
            <div class="col-md-6">
                <div class="savings-summary h-100 d-flex flex-column justify-content-center">
                    <div class="savings-summary-title">Total Potential Monthly Savings</div>
                    <div class="savings-summary-value">$${analysis.total_potential_monthly_savings.toLocaleString()}</div>
                    <div class="savings-summary-detail">
                        $${analysis.total_potential_hourly_savings.toFixed(4)}/hour across all nodes
                    </div>
                </div>
            </div>
        </div>
    `;

    // Node analyses
    nodeTypes.forEach(nodeType => {
        const nodeAnalysis = analysis.node_analyses[nodeType];
        html += renderNodeAnalysis(nodeType, nodeAnalysis);
    });

    document.getElementById('analysis-content').innerHTML = html;
}

/**
 * Render single node analysis
 */
function renderNodeAnalysis(nodeType, analysis) {
    let html = `
        <div class="analysis-section">
            <div class="analysis-section-title">
                <i class="bi bi-hdd-stack"></i>
                ${nodeType} Nodes Analysis
                <span class="ms-2 badge bg-secondary">${analysis.instance_count} instances</span>
            </div>
    `;

    // Warning if metrics not available
    if (analysis.metrics_warning) {
        html += `
            <div class="warning-box mb-3">
                <i class="bi bi-exclamation-triangle me-2"></i>
                ${analysis.metrics_warning}
            </div>
        `;
    }

    // Current configuration and metrics
    html += `
        <div class="row mb-3">
            <div class="col-md-4">
                <div class="metric-card">
                    <div class="current-cost">$${analysis.current_hourly_cost.toFixed(4)}</div>
                    <div class="cost-period">per hour</div>
                    <div class="mt-2 small text-muted">
                        ${analysis.instance_count}x ${analysis.instance_type}
                    </div>
                    ${analysis.instance_specs ? `
                        <div class="small text-muted">
                            ${analysis.instance_specs.vcpus} vCPU, ${analysis.instance_specs.memory_gb} GB RAM
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="col-md-8">
                ${analysis.metrics_available ? renderMetricsDisplay(analysis.metrics) : `
                    <div class="info-box">
                        <i class="bi bi-info-circle me-2"></i>
                        No metrics available for analysis. Nodes may have recently started or scaled.
                    </div>
                `}
            </div>
        </div>
    `;

    // Status and recommendations (only if metrics available)
    if (analysis.metrics_available && analysis.sizing_status) {
        html += `
            <div class="row mb-3">
                <div class="col-md-6">
                    <div class="d-flex align-items-center gap-3 mb-2">
                        <span class="sizing-status ${analysis.sizing_status.status}">
                            ${analysis.sizing_status.label}
                        </span>
                        ${analysis.workload_profile ? `
                            <span class="workload-badge ${analysis.workload_profile}">
                                <i class="bi bi-${getWorkloadIcon(analysis.workload_profile)}"></i>
                                ${formatWorkloadProfile(analysis.workload_profile)}
                            </span>
                        ` : ''}
                    </div>
                    <p class="text-muted small mb-0">${analysis.sizing_status.description}</p>
                </div>
                <div class="col-md-6 text-md-end">
                    ${analysis.confidence ? `
                        <span class="confidence-indicator ${analysis.confidence.level}">
                            <i class="bi bi-shield-check"></i>
                            Confidence: ${analysis.confidence.level.toUpperCase()}
                        </span>
                        <div class="small text-muted mt-1">${analysis.confidence.reasons.join(', ')}</div>
                    ` : ''}
                </div>
            </div>
        `;

        // Recommendations
        if (analysis.recommendations) {
            html += renderRecommendations(analysis.recommendations);
        }
    }

    html += '</div>';
    return html;
}

/**
 * Render metrics display with sustained peak analysis
 */
function renderMetricsDisplay(metrics) {
    return `
        <div class="row g-2">
            <div class="col-6">
                <div class="metric-card">
                    <div class="text-muted small mb-2">CPU Utilization</div>
                    ${renderUtilizationBar('Average', metrics.cpu.average, 'cpu')}
                    ${renderUtilizationBarWithPeakInfo(metrics.cpu)}
                </div>
            </div>
            <div class="col-6">
                <div class="metric-card">
                    <div class="text-muted small mb-2">Memory Utilization</div>
                    ${metrics.memory.available ? `
                        ${renderUtilizationBar('Average', metrics.memory.average, 'mem')}
                        ${renderUtilizationBarWithPeakInfo(metrics.memory)}
                    ` : `
                        <div class="text-muted small">Memory metrics not available</div>
                    `}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render utilization bar with peak analysis info
 */
function renderUtilizationBarWithPeakInfo(metricData) {
    if (!metricData || !metricData.available) {
        return renderUtilizationBar('Peak', null, 'generic');
    }

    const p95 = metricData.p95;
    const effectivePeak = metricData.effective_peak || p95;
    const peakType = metricData.peak_type || 'sustained';
    const percentileUsed = metricData.effective_peak_percentile || 'P95';
    const isSpike = metricData.is_spike || false;
    const durationAtP95 = metricData.duration_at_p95_minutes || 0;

    // Determine the label and indicator based on peak type
    let peakLabel = `Peak (${percentileUsed})`;
    let peakIndicator = '';
    let peakNote = '';

    if (peakType === 'momentary') {
        peakIndicator = '<span class="badge bg-warning text-dark ms-1" title="Peak was momentary (<10 min)">Momentary</span>';
        peakNote = `<div class="small text-warning mt-1"><i class="bi bi-lightning"></i> P95 (${p95?.toFixed(1)}%) lasted only ${durationAtP95.toFixed(0)} min - using ${percentileUsed} for sizing</div>`;
    } else if (peakType === 'moderate') {
        peakIndicator = '<span class="badge bg-info text-dark ms-1" title="Peak was moderately sustained">Moderate</span>';
        peakNote = `<div class="small text-info mt-1"><i class="bi bi-clock"></i> Using ${percentileUsed} (${effectivePeak?.toFixed(1)}%) for sizing</div>`;
    } else if (isSpike) {
        peakIndicator = '<span class="badge bg-secondary ms-1" title="Spike detected between P90 and P95">Spike</span>';
    }

    // Show P95 value if different from effective peak
    let p95Info = '';
    if (effectivePeak !== p95 && p95 !== null) {
        p95Info = `<div class="small text-muted">Raw P95: ${p95.toFixed(1)}%</div>`;
    }

    let barClass = 'low';
    if (effectivePeak >= 60) barClass = 'optimal';
    else if (effectivePeak >= 40) barClass = 'medium';
    else if (effectivePeak >= 70) barClass = 'high';

    return `
        <div class="utilization-bar-container">
            <div class="utilization-bar-label">
                <span>${peakLabel}${peakIndicator}</span>
                <span>${effectivePeak?.toFixed(1) || 'N/A'}%</span>
            </div>
            <div class="utilization-bar">
                <div class="utilization-bar-fill ${barClass}" style="width: ${Math.min(effectivePeak || 0, 100)}%"></div>
            </div>
            ${p95Info}
            ${peakNote}
        </div>
    `;
}

/**
 * Render utilization bar
 */
function renderUtilizationBar(label, value, type) {
    if (value === null || value === undefined) {
        return `
            <div class="utilization-bar-container">
                <div class="utilization-bar-label">
                    <span>${label}</span>
                    <span>N/A</span>
                </div>
                <div class="utilization-bar">
                    <div class="utilization-bar-fill" style="width: 0%"></div>
                </div>
            </div>
        `;
    }

    let barClass = 'low';
    if (value >= 60) barClass = 'optimal';
    else if (value >= 40) barClass = 'medium';
    else if (value >= 70) barClass = 'high';

    return `
        <div class="utilization-bar-container">
            <div class="utilization-bar-label">
                <span>${label}</span>
                <span>${value.toFixed(1)}%</span>
            </div>
            <div class="utilization-bar">
                <div class="utilization-bar-fill ${barClass}" style="width: ${Math.min(value, 100)}%"></div>
            </div>
        </div>
    `;
}

/**
 * Render recommendations
 */
function renderRecommendations(recommendations) {
    if (recommendations.action === 'none') {
        return `
            <div class="info-box">
                <i class="bi bi-check-circle me-2"></i>
                <strong>No action needed.</strong> ${recommendations.reason}
            </div>
        `;
    }

    if (recommendations.action === 'consider_upsizing') {
        return `
            <div class="warning-box">
                <i class="bi bi-arrow-up-circle me-2"></i>
                <strong>Consider upsizing.</strong> ${recommendations.reason}
            </div>
        `;
    }

    if (recommendations.action === 'optimal_for_workload') {
        return `
            <div class="info-box">
                <i class="bi bi-info-circle me-2"></i>
                <strong>Optimal for workload.</strong> ${recommendations.reason}
            </div>
            ${recommendations.required_vcpus && recommendations.required_memory_gb ? `
                <div class="mt-3 small text-muted">
                    <i class="bi bi-calculator me-1"></i>
                    Calculated requirements with 20% headroom: ${recommendations.required_vcpus} vCPUs, ${recommendations.required_memory_gb} GB RAM
                </div>
            ` : ''}
        `;
    }

    let html = '';

    // Show same-family note if no smaller option available
    if (recommendations.same_family_note && !recommendations.same_family) {
        html += `
            <div class="info-box mb-3">
                <i class="bi bi-info-circle me-2"></i>
                <strong>Same Family:</strong> ${recommendations.same_family_note}
            </div>
        `;
    }

    html += '<div class="row g-3">';

    // Same family recommendation
    if (recommendations.same_family) {
        const rec = recommendations.same_family;
        const isBest = recommendations.best_recommendation?.instance_type === rec.instance_type;
        html += `
            <div class="col-md-6">
                <div class="recommendation-card ${isBest ? 'best' : ''}">
                    <div class="recommendation-header">
                        <span class="recommendation-type">Same Family</span>
                        ${isBest ? '<span class="recommendation-badge">Best Option</span>' : ''}
                    </div>
                    <div class="recommendation-instance">${rec.instance_type}</div>
                    <div class="recommendation-specs">
                        ${rec.vcpus} vCPU, ${rec.memory_gb} GB RAM
                        <br>$${rec.price_per_hour.toFixed(4)}/hr per instance
                    </div>
                    ${rec.savings ? `
                        <div class="recommendation-savings">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="savings-value">-$${rec.savings.monthly_savings.toLocaleString()}/mo</div>
                                    <div class="small text-muted">$${rec.savings.hourly_savings.toFixed(4)}/hr</div>
                                </div>
                                <div class="savings-percent">${rec.savings.savings_percent}% savings</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Cheaper alternative (same size, different family - e.g., r6g.4xlarge vs r7g.4xlarge)
    if (recommendations.cheaper_alternative) {
        const rec = recommendations.cheaper_alternative;
        const isBest = recommendations.best_recommendation?.instance_type === rec.instance_type;
        html += `
            <div class="col-md-6">
                <div class="recommendation-card ${isBest ? 'best' : ''}">
                    <div class="recommendation-header">
                        <span class="recommendation-type">Cheaper Alternative (${rec.family})</span>
                        ${isBest ? '<span class="recommendation-badge">Best Option</span>' : ''}
                    </div>
                    <div class="recommendation-instance">${rec.instance_type}</div>
                    <div class="recommendation-specs">
                        ${rec.vcpus} vCPU, ${rec.memory_gb} GB RAM
                        <br>$${rec.price_per_hour.toFixed(4)}/hr per instance
                        <br><span class="badge bg-light text-dark">${rec.category}</span>
                        ${rec.note ? `<br><small class="text-muted">${rec.note}</small>` : ''}
                    </div>
                    ${rec.savings ? `
                        <div class="recommendation-savings">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="savings-value">-$${rec.savings.monthly_savings.toLocaleString()}/mo</div>
                                    <div class="small text-muted">$${rec.savings.hourly_savings.toFixed(4)}/hr</div>
                                </div>
                                <div class="savings-percent">${rec.savings.savings_percent}% savings</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Cross family recommendation
    if (recommendations.cross_family &&
        recommendations.cross_family.instance_type !== recommendations.cheaper_alternative?.instance_type) {
        const rec = recommendations.cross_family;
        const isBest = recommendations.best_recommendation?.instance_type === rec.instance_type;
        html += `
            <div class="col-md-6">
                <div class="recommendation-card ${isBest ? 'best' : ''}">
                    <div class="recommendation-header">
                        <span class="recommendation-type">Cross Family (${rec.family})</span>
                        ${isBest ? '<span class="recommendation-badge">Best Option</span>' : ''}
                    </div>
                    <div class="recommendation-instance">${rec.instance_type}</div>
                    <div class="recommendation-specs">
                        ${rec.vcpus} vCPU, ${rec.memory_gb} GB RAM
                        <br>$${rec.price_per_hour.toFixed(4)}/hr per instance
                        <br><span class="badge bg-light text-dark">${rec.category}</span>
                    </div>
                    ${rec.savings ? `
                        <div class="recommendation-savings">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="savings-value">-$${rec.savings.monthly_savings.toLocaleString()}/mo</div>
                                    <div class="small text-muted">$${rec.savings.hourly_savings.toFixed(4)}/hr</div>
                                </div>
                                <div class="savings-percent">${rec.savings.savings_percent}% savings</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Category optimized recommendation (if different from others)
    if (recommendations.category_optimized &&
        recommendations.category_optimized.instance_type !== recommendations.cross_family?.instance_type &&
        recommendations.category_optimized.instance_type !== recommendations.cheaper_alternative?.instance_type) {
        const rec = recommendations.category_optimized;
        const isBest = recommendations.best_recommendation?.instance_type === rec.instance_type;
        html += `
            <div class="col-md-6">
                <div class="recommendation-card ${isBest ? 'best' : ''}">
                    <div class="recommendation-header">
                        <span class="recommendation-type">
                            Optimized for ${formatWorkloadProfile(rec.workload_profile)}
                        </span>
                        ${isBest ? '<span class="recommendation-badge">Best Option</span>' : ''}
                    </div>
                    <div class="recommendation-instance">${rec.instance_type}</div>
                    <div class="recommendation-specs">
                        ${rec.vcpus} vCPU, ${rec.memory_gb} GB RAM
                        <br>$${rec.price_per_hour.toFixed(4)}/hr per instance
                        <br><span class="badge bg-light text-dark">${rec.category}</span>
                    </div>
                    ${rec.savings ? `
                        <div class="recommendation-savings">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="savings-value">-$${rec.savings.monthly_savings.toLocaleString()}/mo</div>
                                    <div class="small text-muted">$${rec.savings.hourly_savings.toFixed(4)}/hr</div>
                                </div>
                                <div class="savings-percent">${rec.savings.savings_percent}% savings</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    html += '</div>';

    // Requirements info with peak analysis
    if (recommendations.required_vcpus && recommendations.required_memory_gb) {
        html += `
            <div class="mt-3 small text-muted">
                <i class="bi bi-calculator me-1"></i>
                Calculated requirements with 20% headroom: ${recommendations.required_vcpus} vCPUs, ${recommendations.required_memory_gb} GB RAM
            </div>
        `;
    }

    // Peak analysis summary
    if (recommendations.peak_analysis) {
        const cpuPeak = recommendations.peak_analysis.cpu;
        const memPeak = recommendations.peak_analysis.memory;

        let peakNotes = [];
        if (cpuPeak && cpuPeak.peak_type !== 'sustained') {
            peakNotes.push(`CPU: Using ${cpuPeak.percentile_used} (${cpuPeak.effective_peak?.toFixed(1)}%) instead of P95 (${cpuPeak.p95?.toFixed(1)}%) - peak was ${cpuPeak.peak_type}`);
        }
        if (memPeak && memPeak.peak_type !== 'sustained') {
            peakNotes.push(`Memory: Using ${memPeak.percentile_used} (${memPeak.effective_peak?.toFixed(1)}%) instead of P95 (${memPeak.p95?.toFixed(1)}%) - peak was ${memPeak.peak_type}`);
        }

        if (peakNotes.length > 0) {
            html += `
                <div class="mt-2 p-2 bg-light rounded">
                    <div class="small">
                        <i class="bi bi-info-circle text-info me-1"></i>
                        <strong>Peak Analysis Adjustment:</strong>
                    </div>
                    ${peakNotes.map(note => `<div class="small text-muted ms-3">• ${note}</div>`).join('')}
                </div>
            `;
        }
    }

    return html;
}

/**
 * Show analysis error
 */
function showAnalysisError(message) {
    document.getElementById('analysis-content').innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${escapeHtml(message)}
        </div>
    `;
}

/**
 * Update summary cards
 */
function updateSummary() {
    document.getElementById('total-clusters').textContent = clustersData.total_count;
    document.getElementById('transient-clusters').textContent = clustersData.transient_count;
    document.getElementById('long-running-clusters').textContent = clustersData.long_running_count;
}

/**
 * Update potential savings display
 */
function updatePotentialSavings(analysis) {
    totalPotentialSavings += analysis.total_potential_monthly_savings || 0;
    document.getElementById('potential-savings').textContent = `$${totalPotentialSavings.toLocaleString()}`;
}

/**
 * Helper: Find cluster by ID
 */
function findCluster(clusterId) {
    if (!clustersData) return null;
    const all = [
        ...clustersData.transient,
        ...clustersData.long_running,
        ...(clustersData.terminated || [])
    ];
    return all.find(c => c.id === clusterId);
}

/**
 * Helper: Format runtime
 */
function formatRuntime(hours) {
    if (hours < 1) {
        return `${Math.round(hours * 60)} minutes`;
    } else if (hours < 24) {
        return `${hours.toFixed(1)} hours`;
    } else {
        const days = Math.floor(hours / 24);
        const remainingHours = hours % 24;
        return `${days}d ${remainingHours.toFixed(0)}h`;
    }
}

/**
 * Helper: Format analysis period
 */
function formatAnalysisPeriod(period) {
    const start = new Date(period.start);
    const end = new Date(period.end);
    const hours = Math.round((end - start) / (1000 * 60 * 60));
    return `Last ${hours} hours`;
}

/**
 * Helper: Format workload profile
 */
function formatWorkloadProfile(profile) {
    const profiles = {
        'cpu_heavy': 'CPU Heavy',
        'memory_heavy': 'Memory Heavy',
        'balanced': 'Balanced',
        'unknown': 'Unknown'
    };
    return profiles[profile] || profile;
}

/**
 * Helper: Get workload icon
 */
function getWorkloadIcon(profile) {
    const icons = {
        'cpu_heavy': 'cpu',
        'memory_heavy': 'memory',
        'balanced': 'symmetry-horizontal',
        'unknown': 'question-circle'
    };
    return icons[profile] || 'question-circle';
}

/**
 * Helper: Create empty state HTML
 */
function createEmptyState(message) {
    return `
        <div class="empty-state text-center py-5">
            <i class="bi bi-inbox text-muted" style="font-size: 2rem;"></i>
            <p class="text-muted mt-2">${message}</p>
        </div>
    `;
}

/**
 * Helper: Show loading state
 */
function showLoading() {
    document.getElementById('loading-state').classList.remove('d-none');
    document.getElementById('clusters-container').classList.add('d-none');
}

/**
 * Helper: Show error
 */
function showError(message) {
    document.getElementById('loading-state').classList.add('d-none');
    document.getElementById('error-state').classList.remove('d-none');
    document.getElementById('error-message').textContent = message;
}

/**
 * Helper: Hide error
 */
function hideError() {
    document.getElementById('error-state').classList.add('d-none');
}

/**
 * Helper: Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
