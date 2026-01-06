/**
 * EMR Cost Optimizer - Frontend Application
 */

// Global state
let clustersData = null;
let analysisModal = null;
let totalPotentialSavings = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    analysisModal = new bootstrap.Modal(document.getElementById('analysisModal'));
    refreshClusters();
});

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

    // Update badges
    document.getElementById('transient-badge').textContent = clustersData.transient_count;
    document.getElementById('long-running-badge').textContent = clustersData.long_running_count;

    // Show container
    document.getElementById('loading-state').classList.add('d-none');
    document.getElementById('clusters-container').classList.remove('d-none');
}

/**
 * Create cluster card HTML
 */
function createClusterCard(cluster) {
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
            return `
                <span class="instance-group-tag ${g.type.toLowerCase()}">
                    ${g.type}: ${g.running_count}x ${g.instance_type}
                </span>
            `;
        }).join('');

    const runtimeFormatted = formatRuntime(cluster.runtime_hours);
    const statusClass = cluster.state.toLowerCase();
    const fleetBadge = cluster.uses_fleets ? '<span class="badge bg-secondary ms-2">Fleet</span>' : '';

    return `
        <div class="cluster-item" data-cluster-id="${cluster.id}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2">
                        <span class="cluster-name">${escapeHtml(cluster.name)}</span>
                        <span class="status-badge ${statusClass}">${cluster.state}</span>
                        ${fleetBadge}
                    </div>
                    <div class="cluster-id">${cluster.id}</div>
                    <div class="cluster-meta">
                        <span class="cluster-meta-item">
                            <i class="bi bi-clock"></i>
                            ${runtimeFormatted}
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
                    <div class="mt-2">
                        ${instanceGroups}
                    </div>
                </div>
                <div class="cluster-actions">
                    <button class="btn btn-primary btn-analyze" onclick="analyzeCluster('${cluster.id}')">
                        <i class="bi bi-graph-up me-1"></i>
                        Analyze Utilization
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Analyze a cluster
 */
async function analyzeCluster(clusterId) {
    const button = document.querySelector(`[data-cluster-id="${clusterId}"] .btn-analyze`);
    const originalContent = button.innerHTML;

    // Update button state
    button.classList.add('analyzing');
    button.innerHTML = '<span class="analysis-spinner me-1"></span>Analyzing...';

    // Show modal with loading state
    showAnalysisLoading(clusterId);
    analysisModal.show();

    try {
        const response = await fetch(`/api/clusters/${clusterId}/analyze`, {
            method: 'POST'
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
function showAnalysisLoading(clusterId) {
    const cluster = findCluster(clusterId);
    document.getElementById('analysisModalLabel').innerHTML = `
        <i class="bi bi-graph-up me-2"></i>
        Analyzing: ${cluster ? escapeHtml(cluster.name) : clusterId}
    `;

    document.getElementById('analysis-content').innerHTML = `
        <div class="analysis-loading">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Fetching CloudWatch metrics and analyzing utilization...</p>
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
 * Render metrics display
 */
function renderMetricsDisplay(metrics) {
    return `
        <div class="row g-2">
            <div class="col-6">
                <div class="metric-card">
                    <div class="text-muted small mb-2">CPU Utilization</div>
                    ${renderUtilizationBar('Average', metrics.cpu.average, 'cpu')}
                    ${renderUtilizationBar('Peak (P95)', metrics.cpu.p95, 'cpu')}
                </div>
            </div>
            <div class="col-6">
                <div class="metric-card">
                    <div class="text-muted small mb-2">Memory Utilization</div>
                    ${metrics.memory.available ? `
                        ${renderUtilizationBar('Average', metrics.memory.average, 'mem')}
                        ${renderUtilizationBar('Peak (P95)', metrics.memory.p95, 'mem')}
                    ` : `
                        <div class="text-muted small">Memory metrics not available</div>
                    `}
                </div>
            </div>
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

    let html = '<div class="row g-3">';

    // Same family recommendation
    if (recommendations.same_family) {
        const rec = recommendations.same_family;
        const isBest = recommendations.best_recommendation === rec;
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

    // Cross family recommendation
    if (recommendations.cross_family) {
        const rec = recommendations.cross_family;
        const isBest = recommendations.best_recommendation === rec && !recommendations.same_family;
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

    // Category optimized recommendation (if different from cross_family)
    if (recommendations.category_optimized &&
        recommendations.category_optimized.instance_type !== recommendations.cross_family?.instance_type) {
        const rec = recommendations.category_optimized;
        html += `
            <div class="col-md-6">
                <div class="recommendation-card">
                    <div class="recommendation-header">
                        <span class="recommendation-type">
                            Optimized for ${formatWorkloadProfile(rec.workload_profile)}
                        </span>
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

    // Requirements info
    if (recommendations.required_vcpus && recommendations.required_memory_gb) {
        html += `
            <div class="mt-3 small text-muted">
                <i class="bi bi-calculator me-1"></i>
                Calculated requirements with 20% headroom: ${recommendations.required_vcpus} vCPUs, ${recommendations.required_memory_gb} GB RAM
            </div>
        `;
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
    const all = [...clustersData.transient, ...clustersData.long_running];
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
